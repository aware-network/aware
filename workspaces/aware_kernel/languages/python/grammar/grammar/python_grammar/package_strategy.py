"""Python-specific ObjectConfigGraph package strategy."""

import importlib
import json
from pathlib import Path
import shutil
import textwrap
from typing import cast

from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageSpec,
    ObjectConfigGraphPackageStrategy,
)
from typing_extensions import override

from python_grammar.package_policy import PythonPackagePolicy
from python_grammar.package_templates import render_root_init


_API_DTO_PACKAGE_KIND = "api_dto"
_API_PUBLIC_PACKAGE_KIND = "api_public_package"
_API_SERVICE_PROTOCOL_PACKAGE_KIND = "api_service_protocol"
_ONTOLOGY_DTO_PACKAGE_KIND = "ontology_dto"
_GENERATED_CONTRACT_PACKAGE_KINDS = frozenset(
    {
        _API_DTO_PACKAGE_KIND,
        _API_SERVICE_PROTOCOL_PACKAGE_KIND,
        _ONTOLOGY_DTO_PACKAGE_KIND,
    }
)
_STALE_SERVICE_PROTOCOL_RUNTIME_INDEX_ARTIFACTS = (
    "python.models.json",
    "ocg.node_paths.python.json",
)
_STALE_API_PUBLIC_PACKAGE_LOCAL_MODEL_ARTIFACTS = (
    "python.models.json",
    "ocg.node_paths.python.json",
)


class PythonPackageStrategy(ObjectConfigGraphPackageStrategy):
    """Builds Python packages (pyproject + README + import root)."""

    def _write_text_if_changed(self, path: Path, content: str) -> bool:
        path = Path(path)
        if path.suffix in {".py", ".pyi"} and path.exists():
            try:
                if path.read_text(encoding="utf-8") == content:
                    return False
            except (OSError, UnicodeDecodeError):
                pass
        return super()._write_text_if_changed(
            path,
            _canonicalize_python_package_text(path=path, content=content),
        )

    def _copy_if_changed(self, src: Path, dest: Path) -> bool:
        src = Path(src)
        dest = Path(dest)
        if dest.suffix in {".py", ".pyi"}:
            if dest.exists():
                try:
                    if src.read_bytes() == dest.read_bytes():
                        return False
                except OSError:
                    pass
            try:
                return self._write_text_if_changed(
                    dest,
                    src.read_text(encoding="utf-8"),
                )
            except UnicodeDecodeError:
                pass
        return super()._copy_if_changed(src, dest)

    @override
    def build_into(
        self,
        *,
        output_root: Path,
        rendered_files: list[Path],
        spec: ObjectConfigGraphPackageSpec,
    ) -> list[Path]:
        """
        Populate `output_root` with a full Python package.

        This includes:
        - import root package with all rendered modules
        - PEP 561 marker (`py.typed`) so type checkers treat generated packages as typed
        - README.md
        - pyproject.toml
        - optional license file
        - import-root __init__.py shim that imports generated modules and triggers model_rebuild()
        """
        package_name = spec.package_name or spec.name
        if not package_name:
            raise ValueError("Package spec must define a package_name or name")

        rendered_paths = [Path(p).resolve() for p in rendered_files]
        import_root_name = spec.import_root or package_name.replace("-", "_")
        import_root = output_root / import_root_name
        files_written: list[Path] = []

        import_root.mkdir(parents=True, exist_ok=True)
        self._remove_stale_api_service_protocol_runtime_indexes(
            import_root=import_root,
            spec=spec,
        )
        self._remove_stale_api_public_package_local_models(
            import_root=import_root,
            spec=spec,
        )
        self._remove_stale_api_dto_python_modules(
            import_root=import_root,
            rendered_paths=rendered_paths,
            spec=spec,
        )
        self._ensure_package_inits(import_root, import_root, files_written)
        py_typed_path = import_root / "py.typed"
        self._write_text_if_changed(py_typed_path, "")
        files_written.append(py_typed_path)

        # Copy rendered files into package import root
        if rendered_files:
            rendered_relative_paths = [
                self._rendered_file_relative_path(
                    src_path=src_path,
                    import_root_name=import_root_name,
                )
                for src_path in rendered_paths
            ]
            if any(
                self._rendered_file_is_import_root_prefixed(
                    src_path=src_path,
                    import_root_name=import_root_name,
                )
                for src_path in rendered_paths
            ):
                self._remove_stale_nested_import_root(
                    import_root=import_root,
                    import_root_name=import_root_name,
                )
            for src_path in rendered_paths:
                rel = rendered_relative_paths.pop(0)
                dest = import_root / rel
                self._copy_if_changed(src_path, dest)
                files_written.append(dest)
                self._ensure_package_inits(dest.parent, import_root, files_written)
        else:
            self._ensure_package_inits(import_root, import_root, files_written)

        readme_path = output_root / "README.md"
        self._write_text_if_changed(
            readme_path, self._render_readme(package_name, spec.description, spec)
        )
        files_written.append(readme_path)

        pyproject_path = output_root / "pyproject.toml"
        self._write_text_if_changed(
            pyproject_path,
            self._render_pyproject(
                package_name,
                import_root_name,
                spec,
                import_root_path=import_root,
            ),
        )
        files_written.append(pyproject_path)

        if spec.license_file:
            license_src = Path(spec.license_file)
            if license_src.exists():
                license_dest = output_root / license_src.name
                self._copy_if_changed(license_src, license_dest)
                files_written.append(license_dest)

        python_module_files = [
            p
            for p in files_written
            if p.suffix == ".py"
            and import_root in p.parents
            and p.name != "__init__.py"
        ]
        dependency_import_roots: list[str] = []
        raw_deps = (spec.metadata or {}).get("dependency_import_roots")
        if isinstance(raw_deps, list):
            for raw_dep in cast(list[object], raw_deps):
                if isinstance(raw_dep, str) and raw_dep:
                    dependency_import_roots.append(raw_dep)
        root_export_refs: list[str] = []
        raw_root_exports = (spec.metadata or {}).get("root_export_refs")
        if isinstance(raw_root_exports, list):
            for raw_export in cast(list[object], raw_root_exports):
                if isinstance(raw_export, str) and raw_export:
                    root_export_refs.append(raw_export)
        init_path = self._write_root_init(
            import_root,
            import_root_name,
            python_module_files,
            dependency_import_roots,
            root_export_refs,
        )
        files_written.append(init_path)

        return files_written

    def _rendered_file_relative_path(
        self,
        *,
        src_path: Path,
        import_root_name: str,
    ) -> Path:
        try:
            rel = src_path.relative_to(self.base_dir)
        except ValueError:
            return Path(src_path.name)
        if rel.parts and rel.parts[0] == import_root_name:
            stripped = Path(*rel.parts[1:])
            return stripped if stripped.parts else Path(src_path.name)
        return rel

    def _rendered_file_is_import_root_prefixed(
        self,
        *,
        src_path: Path,
        import_root_name: str,
    ) -> bool:
        try:
            rel = src_path.relative_to(self.base_dir)
        except ValueError:
            return False
        return bool(rel.parts and rel.parts[0] == import_root_name)

    def _remove_stale_nested_import_root(
        self,
        *,
        import_root: Path,
        import_root_name: str,
    ) -> None:
        nested_root = import_root / import_root_name
        if nested_root.is_dir():
            shutil.rmtree(nested_root)

    def _remove_stale_api_service_protocol_runtime_indexes(
        self,
        *,
        import_root: Path,
        spec: ObjectConfigGraphPackageSpec,
    ) -> None:
        metadata = cast(dict[str, object], spec.metadata or {})
        if metadata.get("aware_package_kind") != _API_SERVICE_PROTOCOL_PACKAGE_KIND:
            return
        artifacts_dir = import_root / "_aware"
        for filename in _STALE_SERVICE_PROTOCOL_RUNTIME_INDEX_ARTIFACTS:
            stale_path = artifacts_dir / filename
            if stale_path.is_file() or stale_path.is_symlink():
                stale_path.unlink()

    def _remove_stale_api_dto_python_modules(
        self,
        *,
        import_root: Path,
        rendered_paths: list[Path],
        spec: ObjectConfigGraphPackageSpec,
    ) -> None:
        metadata = cast(dict[str, object], spec.metadata or {})
        if metadata.get("aware_package_kind") != _API_DTO_PACKAGE_KIND:
            return

        expected_modules: set[Path] = set()
        expected_package_dirs: set[Path] = {Path(".")}
        for src_path in rendered_paths:
            if src_path.suffix != ".py":
                continue
            try:
                rel = src_path.relative_to(self.base_dir)
            except ValueError:
                rel = Path(src_path.name)
            expected_modules.add(rel)
            for parent in rel.parents:
                if parent == Path("."):
                    break
                expected_package_dirs.add(parent)

        if not import_root.exists():
            return

        for existing in sorted(import_root.rglob("*.py")):
            try:
                rel = existing.relative_to(import_root)
            except ValueError:
                continue
            if rel.parts and rel.parts[0] == "_aware":
                continue
            if rel in expected_modules:
                continue
            if existing.name == "__init__.py" and rel.parent in expected_package_dirs:
                continue
            existing.unlink()

        for directory in sorted(
            (
                path
                for path in import_root.rglob("*")
                if path.is_dir() and path.name != "_aware"
            ),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            if directory == import_root:
                continue
            try:
                next(directory.iterdir())
            except StopIteration:
                directory.rmdir()

    def _remove_stale_api_public_package_local_models(
        self,
        *,
        import_root: Path,
        spec: ObjectConfigGraphPackageSpec,
    ) -> None:
        metadata = cast(dict[str, object], spec.metadata or {})
        if metadata.get("aware_package_kind") != _API_PUBLIC_PACKAGE_KIND:
            return
        if metadata.get("uses_external_api_dto_types") is not True:
            return

        models_dir = import_root / "models"
        if models_dir.exists():
            for existing in sorted(
                models_dir.rglob("*"), key=lambda path: len(path.parts), reverse=True
            ):
                if existing.is_file() or existing.is_symlink():
                    existing.unlink()
                elif existing.is_dir():
                    try:
                        existing.rmdir()
                    except OSError:
                        pass
            try:
                models_dir.rmdir()
            except OSError:
                pass

        artifacts_dir = import_root / "_aware"
        for filename in _STALE_API_PUBLIC_PACKAGE_LOCAL_MODEL_ARTIFACTS:
            stale_path = artifacts_dir / filename
            if stale_path.is_file() or stale_path.is_symlink():
                stale_path.unlink()

    def _ensure_package_inits(
        self, current: Path, stop: Path, files_written: list[Path]
    ) -> None:
        current = current.resolve()
        stop = stop.resolve()
        if stop not in current.parents and current != stop:
            return
        while True:
            init_path = current / "__init__.py"
            if not init_path.exists():
                # Non-root packages get a minimal stub; the import root
                # content is populated by _write_root_init.
                self._write_text_if_changed(
                    init_path, "# Auto-generated by Aware package strategy.\n"
                )
            if init_path not in files_written:
                files_written.append(init_path)
            if current == stop:
                break
            current = current.parent

    def _write_root_init(
        self,
        import_root: Path,
        import_root_name: str,
        module_files: list[Path],
        dependency_import_roots: list[str] | None = None,
        root_export_refs: list[str] | None = None,
    ) -> Path:
        """
        Render a root __init__.py that:

        - Imports all generated modules under the import root so models are registered.
        - Rebuilds models so forward references resolve eagerly.
        """
        import_root = import_root.resolve()
        init_path = import_root / "__init__.py"

        # Derive fully qualified module names from the file layout.
        module_names: list[str] = []
        for path in module_files:
            try:
                rel = path.resolve().relative_to(import_root)
            except ValueError:
                continue
            parts = list(rel.with_suffix("").parts)
            if not parts:
                continue
            module_names.append(".".join([import_root_name, *parts]))

        # Deduplicate and sort for deterministic output
        module_names = sorted({m for m in module_names})
        policy = (
            self.policy
            if isinstance(self.policy, PythonPackagePolicy)
            else PythonPackagePolicy.orm_default()
        )
        install_runtime_artifacts = bool(policy.install_runtime_artifacts)
        self._write_text_if_changed(
            init_path,
            render_root_init(
                module_names=module_names,
                dependency_import_roots=dependency_import_roots or [],
                install_runtime_artifacts=install_runtime_artifacts,
                root_export_refs=root_export_refs or [],
            ),
        )
        return init_path

    def _render_readme(
        self,
        package_name: str,
        description: str | None,
        spec: ObjectConfigGraphPackageSpec,
    ) -> str:
        metadata = cast(dict[str, object], spec.metadata or {})
        if metadata.get("aware_package_kind") == "api_public_package":
            return self._render_api_public_package_readme(
                package_name=package_name,
                description=description,
                metadata=metadata,
            )

        content = description or f"Auto-generated package for {package_name}."
        return (
            textwrap.dedent(
                f"""\
            # {package_name}

            {content}

            ## Installation

            ```bash
            pip install .
            ```
            """
            ).strip()
            + "\n"
        )

    def _render_api_public_package_readme(
        self,
        *,
        package_name: str,
        description: str | None,
        metadata: dict[str, object],
    ) -> str:
        content = _scrub_public_api_client_text(
            description or f"Generated API client package for {package_name}."
        )
        root_client_class = _read_root_client_class(metadata=metadata)
        example = (
            f"{root_client_class}(AwareApiEndpointInvoker(...))"
            if root_client_class
            else "AwareApiEndpointInvoker(...)"
        )
        return (
            textwrap.dedent(
                f"""\
            # {package_name}

            Generated API client package.

            {content}

            ## Install

            ```bash
            pip install {package_name.replace("_", "-")}
            ```

            ## Public Boundary

            - Use this package from SDKs, tools, agents, and service consumers
              that need a public caller boundary over `aware-api-client`.
            - Generated clients accept `aware_api.invoker.AwareApiEndpointInvoker`.
            - Endpoint refs and DTOs are generated API contract surfaces.
            - This package does not deploy, provision, or host a Service.
            - This package does not expose or depend on Service internals,
              service protocol internals, local graph gateways, runtime
              indexes, or full `aware-code`.
            - This is not the public `aware hub ...` product rail.

            ## Example

            ```python
            from aware_api import AwareApiEndpointInvoker
            from {package_name} import {root_client_class or "AWARE_GENERATED_CLIENT"}

            api = {example}
            ```
            """
            ).strip()
            + "\n"
        )

    def _render_pyproject(
        self,
        package_name: str,
        import_root_name: str,
        spec: ObjectConfigGraphPackageSpec,
        *,
        import_root_path: Path,
    ) -> str:
        metadata = cast(dict[str, object], spec.metadata or {})
        raw_min_python = metadata.get("min_python")
        min_python = raw_min_python if isinstance(raw_min_python, str) else ">=3.12"
        deps = self._filter_pyproject_dependencies(
            dependencies=spec.dependencies or [],
            metadata=metadata,
            import_root_path=import_root_path,
        )
        deps_block = "[]"
        if deps:
            deps_lines = ",\n    ".join(f'"{dep}"' for dep in deps)
            deps_block = "[\n    " + deps_lines + "\n]"

        description = spec.description or f"Auto-generated package {package_name}"
        if metadata.get("aware_package_kind") == "api_public_package":
            description = _scrub_public_api_client_text(description)
        lines = [
            "[project]",
            f'name = "{package_name}"',
            f'version = "{spec.version}"',
            f'description = "{description}"',
            'authors = [{ name = "Aware Automations" }]',
            'readme = "README.md"',
        ]
        if spec.license_file:
            lines.append(f'license = {{ file = "{Path(spec.license_file).name}" }}')
        lines.append(f'requires-python = "{min_python}"')
        lines.append(f"dependencies = {deps_block}")
        if spec.optional_dependencies:
            lines.append("")
            lines.append("[project.optional-dependencies]")
            for group, group_deps in spec.optional_dependencies.items():
                if group_deps:
                    lines.append(f"{group} = [")
                    for dep in group_deps:
                        lines.append(f'    "{dep}",')
                    lines.append("]")
                else:
                    lines.append(f"{group} = []")

        lines.extend(
            [
                "",
                "[build-system]",
                'requires = ["hatchling>=1.27.0"]',
                'build-backend = "hatchling.build"',
                "",
                "[tool.hatch.build.targets.wheel]",
                f'packages = ["{import_root_name}"]',
                f'include = ["README.md", "{import_root_name}/py.typed"]',
            ]
        )
        return "\n".join(lines) + "\n"

    def _filter_pyproject_dependencies(
        self,
        *,
        dependencies: list[str],
        metadata: dict[str, object],
        import_root_path: Path,
    ) -> list[str]:
        """Keep generated pyproject deps aligned to actual bootstrap imports."""

        aware_package_kind = str(metadata.get("aware_package_kind") or "").strip()
        if aware_package_kind not in _GENERATED_CONTRACT_PACKAGE_KINDS:
            return dependencies

        bootstrap_dependency_roots = _read_bootstrap_dependency_import_roots(
            import_root_path=import_root_path,
        )
        metadata_dependency_roots = _metadata_dependency_import_roots(metadata=metadata)
        dependency_roots = bootstrap_dependency_roots or metadata_dependency_roots
        if not dependency_roots:
            return dependencies
        prunable_dependency_roots = (
            _metadata_prunable_dependency_import_roots(metadata=metadata)
            or metadata_dependency_roots
        )
        if not prunable_dependency_roots:
            return dependencies

        filtered: list[str] = []
        for dependency in dependencies:
            dependency_name = _dependency_distribution_name(dependency)
            if not dependency_name:
                filtered.append(dependency)
                continue
            dependency_import_root = dependency_name.replace("-", "_")
            if dependency_import_root in dependency_roots:
                filtered.append(dependency)
                continue
            if dependency_import_root in prunable_dependency_roots:
                continue
            filtered.append(dependency)
        return filtered


def _metadata_dependency_import_roots(*, metadata: dict[str, object]) -> frozenset[str]:
    raw_dependency_roots = metadata.get("dependency_import_roots")
    if not isinstance(raw_dependency_roots, list):
        return frozenset()
    return frozenset(
        root.strip().replace("-", "_")
        for root in raw_dependency_roots
        if isinstance(root, str) and root.strip()
    )


def _metadata_prunable_dependency_import_roots(
    *, metadata: dict[str, object]
) -> frozenset[str]:
    raw_dependency_roots = metadata.get("prunable_dependency_import_roots")
    if not isinstance(raw_dependency_roots, list):
        return frozenset()
    return frozenset(
        root.strip().replace("-", "_")
        for root in raw_dependency_roots
        if isinstance(root, str) and root.strip()
    )


def _read_bootstrap_dependency_import_roots(
    *, import_root_path: Path
) -> frozenset[str]:
    bootstrap_path = import_root_path / "_aware" / "python.bootstrap.json"
    try:
        payload = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return frozenset()
    dependency_roots = payload.get("dependency_import_roots")
    if not isinstance(dependency_roots, list):
        return frozenset()
    return frozenset(
        root.strip().replace("-", "_")
        for root in dependency_roots
        if isinstance(root, str) and root.strip()
    )


def _dependency_distribution_name(dependency: str) -> str:
    token = dependency.strip()
    if not token:
        return ""
    for separator in (";", "[", "<", ">", "=", "!", "~", " "):
        token = token.split(separator, maxsplit=1)[0].strip()
    return token.replace("_", "-")


def _read_root_client_class(*, metadata: dict[str, object]) -> str | None:
    raw_root_exports = metadata.get("root_export_refs")
    if not isinstance(raw_root_exports, list):
        return None
    for raw_export in raw_root_exports:
        if not isinstance(raw_export, str):
            continue
        module_name, _, symbol = raw_export.partition(".")
        if module_name == "client" and symbol:
            return symbol
    return None


def _canonicalize_python_package_text(*, path: Path, content: str) -> str:
    path = Path(path)
    if path.suffix not in {".py", ".pyi"} or not content.strip():
        return content
    try:
        black = importlib.import_module("black")
        mode = black.FileMode(line_length=120, is_pyi=(path.suffix == ".pyi"))
        return str(black.format_str(content, mode=mode))
    except Exception:
        return content


def _scrub_public_api_client_text(value: str) -> str:
    return (
        value.replace("Product A/Product B", "API/service")
        .replace("Generated Product A", "Generated API client")
        .replace("generated Product A", "generated API client")
        .replace("Product A consumers", "API client consumers")
        .replace("Product A", "generated API client")
        .replace("Generated Product B", "Generated service protocol")
        .replace("generated Product B", "generated service protocol")
        .replace("Product B", "service protocol")
        .replace("product A", "generated API client")
        .replace("product B", "service protocol")
    )
