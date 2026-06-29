"""Dart-specific ObjectConfigGraph package strategy."""

import os
from pathlib import Path
import textwrap
from typing_extensions import override

from aware_meta.graph.config.package_strategy import (
    ObjectConfigGraphPackageSpec,
    ObjectConfigGraphPackageStrategy,
)


_AWARE_REPO_ROOT_ENV = "AWARE_REPO_ROOT"


class DartPackageStrategy(ObjectConfigGraphPackageStrategy):
    """Builds Dart packages (pubspec + README + lib import root)."""

    # NOTE: The generated model packages depend on `freezed`/`json_serializable` and are
    # built via `dart run build_runner build`. Keep this aligned with the toolchain
    # requirements to avoid build_runner failures during materialization.
    DEFAULT_SDK_CONSTRAINT: str = ">=3.8.0 <4.0.0"

    @staticmethod
    def _metadata_bool(value: object) -> bool | None:
        """Parse permissive bool-like metadata values."""
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return None

    @override
    def build_into(
        self,
        *,
        output_root: Path,
        rendered_files: list[Path],
        spec: ObjectConfigGraphPackageSpec,
    ) -> list[Path]:
        """Populate `output_root` with a full Dart package."""
        package_name = spec.package_name or spec.name
        if not package_name:
            raise ValueError("Package spec must define a package_name or name")

        rendered_paths = [Path(p).resolve() for p in rendered_files]

        lib_root = output_root / "lib"

        # IMPORTANT (Dart semantics):
        # `package:<name>/foo/bar.dart` resolves to `lib/foo/bar.dart`.
        #
        # Our renderer emits imports like:
        #   import 'package:<pubspec_name>/communication/...';
        #
        # Therefore, the default MUST be to place rendered sources directly under `lib/`.
        # Only nest under `lib/<import_root>/...` when the workflow explicitly asks for it.
        if spec.import_root is None or spec.import_root == "":
            import_root = lib_root
        else:
            import_root_name = spec.import_root.replace("-", "_")
            import_root = lib_root / import_root_name

        import_root.mkdir(parents=True, exist_ok=True)
        self._remove_stale_generated_package_dart_files(import_root=import_root)

        files_written: list[Path] = []

        for src_path in rendered_paths:
            try:
                rel = src_path.relative_to(self.base_dir)
            except ValueError:
                rel = Path(src_path.name)

            dest = import_root / rel
            self._copy_if_changed(src_path, dest)
            files_written.append(dest)

        readme_path = output_root / "README.md"
        self._write_text_if_changed(
            readme_path, self._render_readme(package_name, spec.description)
        )
        files_written.append(readme_path)

        pubspec_path = output_root / "pubspec.yaml"
        self._write_text_if_changed(
            pubspec_path,
            self._render_pubspec(package_name, spec, package_root=output_root),
        )
        files_written.append(pubspec_path)

        if spec.license_file:
            license_src = Path(spec.license_file)
            if license_src.exists():
                license_dest = output_root / license_src.name
                self._copy_if_changed(license_src, license_dest)
                files_written.append(license_dest)

        return files_written

    def _remove_stale_generated_package_dart_files(
        self,
        *,
        import_root: Path,
    ) -> None:
        if not import_root.exists():
            return

        for existing in sorted(
            import_root.rglob("*.dart"),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            if existing.is_file() or existing.is_symlink():
                existing.unlink()

        for existing_dir in sorted(
            (path for path in import_root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            try:
                existing_dir.rmdir()
            except OSError:
                pass

    def _render_readme(self, package_name: str, description: str | None) -> str:
        content = description or f"Auto-generated Dart package for {package_name}."
        return (
            textwrap.dedent(
                f"""\
            # {package_name}

            {content}

            ## Usage

            ```bash
            dart pub get
            ```
            """
            ).strip()
            + "\n"
        )

    def _resolve_workspace_dependency_dir(
        self,
        *,
        package_root: Path,
        repo_root: Path,
        dependency_repo_roots: tuple[Path, ...],
        rel_parts: tuple[str, ...],
        pubspec_name: str,
        dependency_name: str,
    ) -> Path:
        """Resolve a workspace dependency path with local ancestor fallback.

        Primary lookup stays `repo_root/<rel_parts>` (canonical for normal workspaces).
        Fallback supports standalone nested workspaces by walking up from `package_root`.
        """

        seen: set[Path] = set()
        candidates: list[Path] = []
        primary = repo_root.resolve()
        package_root_resolved = package_root.resolve()
        search_roots = [
            primary,
            *dependency_repo_roots,
            package_root_resolved,
            *package_root_resolved.parents,
        ]
        for base in search_roots:
            candidate = (base.joinpath(*rel_parts)).resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)
            if candidate.exists():
                return candidate

        checked = ", ".join(str(path) for path in candidates)
        msg = (
            f"Expected workspace dependency for {pubspec_name} "
            f"({dependency_name}). Checked: {checked}"
        )
        raise FileNotFoundError(msg)

    def _resolve_aware_ontology_dependency_dir(
        self,
        *,
        package_root: Path,
        repo_root: Path,
        dependency_repo_roots: tuple[Path, ...],
        dependency_import_root: str,
        pubspec_name: str,
    ) -> Path:
        normalized = dependency_import_root.strip().replace("-", "_")
        ontology_suffix = "_ontology"
        dto_suffix = "_ontology_dto"
        if normalized.endswith(dto_suffix):
            module_name = normalized.removeprefix("aware_").removesuffix(dto_suffix)
            package_kind = "ontology_dto"
        elif normalized.endswith(ontology_suffix):
            module_name = normalized.removeprefix("aware_").removesuffix(
                ontology_suffix
            )
            package_kind = "ontology"
        else:
            raise FileNotFoundError(
                f"Expected Aware ontology dependency import root for {pubspec_name}: "
                f"{dependency_import_root!r}"
            )
        if not normalized.startswith("aware_") or not module_name:
            raise FileNotFoundError(
                f"Expected Aware ontology dependency import root for {pubspec_name}: "
                f"{dependency_import_root!r}"
            )

        module_candidates = tuple(
            dict.fromkeys((module_name, module_name.replace("_", "-")))
        )
        candidates: list[Path] = []
        for candidate_root in (repo_root, *dependency_repo_roots):
            for candidate_module in module_candidates:
                candidates.append(
                    candidate_root
                    / "modules"
                    / candidate_module
                    / "structure"
                    / package_kind
                    / "dart"
                )
            workspaces_root = candidate_root / "workspaces"
            if workspaces_root.is_dir():
                for workspace_root in sorted(workspaces_root.iterdir()):
                    if not workspace_root.is_dir():
                        continue
                    for candidate_module in module_candidates:
                        candidates.append(
                            workspace_root
                            / "modules"
                            / candidate_module
                            / "structure"
                            / package_kind
                            / "dart"
                        )
            for workspace_root in candidate_root.parents:
                if not workspace_root.is_dir():
                    continue
                for candidate_module in module_candidates:
                    candidates.append(
                        workspace_root
                        / "modules"
                        / candidate_module
                        / "structure"
                        / package_kind
                        / "dart"
                    )
                parent_workspaces_root = workspace_root / "workspaces"
                if not parent_workspaces_root.is_dir():
                    continue
                for parent_workspace_root in sorted(parent_workspaces_root.iterdir()):
                    if not parent_workspace_root.is_dir():
                        continue
                    for candidate_module in module_candidates:
                        candidates.append(
                            parent_workspace_root
                            / "modules"
                            / candidate_module
                            / "structure"
                            / package_kind
                            / "dart"
                        )

        for candidate in candidates:
            if (candidate / "pubspec.yaml").is_file():
                return candidate.resolve()

        checked = ", ".join(path.as_posix() for path in candidates)
        raise FileNotFoundError(
            f"Expected Dart ontology dependency for {pubspec_name} "
            f"({dependency_import_root}). Checked: {checked}"
        )

    @staticmethod
    def _metadata_dependency_import_roots(metadata: dict[str, object]) -> list[str]:
        raw_roots = metadata.get("dependency_import_roots")
        if not isinstance(raw_roots, list):
            return []
        roots: list[str] = []
        for raw_root in raw_roots:
            if isinstance(raw_root, str) and raw_root.strip():
                roots.append(raw_root.strip().replace("-", "_"))
        return list(dict.fromkeys(roots))

    @staticmethod
    def _metadata_dependency_repo_roots(
        metadata: dict[str, object]
    ) -> tuple[Path, ...]:
        raw_roots = metadata.get("dependency_repo_roots")
        if not isinstance(raw_roots, list):
            return ()
        roots: list[Path] = []
        for raw_root in raw_roots:
            if isinstance(raw_root, str) and raw_root.strip():
                roots.append(Path(raw_root).expanduser().resolve())
        return tuple(dict.fromkeys(roots))

    @staticmethod
    def _metadata_path_dependencies(metadata: dict[str, object]) -> dict[str, str]:
        raw_deps = metadata.get("path_dependencies")
        if not isinstance(raw_deps, dict):
            return {}
        dependencies: dict[str, str] = {}
        for raw_name, raw_path in raw_deps.items():
            name = str(raw_name or "").strip().replace("-", "_")
            path_text = str(raw_path or "").strip()
            if name and path_text:
                dependencies[name] = path_text
        return dependencies

    @staticmethod
    def _resolve_declared_path_dependency_dir(
        *,
        package_root: Path,
        repo_root: Path,
        dependency_repo_roots: tuple[Path, ...],
        dependency_name: str,
        dependency_path: str,
        pubspec_name: str,
    ) -> Path:
        raw_path = Path(dependency_path).expanduser()
        if raw_path.is_absolute():
            candidates = [raw_path.resolve()]
        else:
            candidates = [
                (repo_root / raw_path).resolve(),
                *((root / raw_path).resolve() for root in dependency_repo_roots),
                (package_root / raw_path).resolve(),
            ]
        candidates = list(dict.fromkeys(candidates))
        for candidate in candidates:
            if (candidate / "pubspec.yaml").is_file():
                return candidate
        checked = ", ".join(path.as_posix() for path in candidates)
        raise FileNotFoundError(
            f"Expected declared Dart path dependency for {pubspec_name} "
            f"({dependency_name}) at {dependency_path!r}. Checked: {checked}"
        )

    @staticmethod
    def _dependency_declared(deps: list[str], dependency_name: str) -> bool:
        prefix = f"{dependency_name}:"
        return any(str(dep).strip().startswith(prefix) for dep in deps)

    @staticmethod
    def _explicit_repo_root(metadata: dict[str, object]) -> Path:
        raw_value = metadata.get("repo_root") or metadata.get("aware_repo_root")
        if raw_value is None:
            raw_value = os.environ.get(_AWARE_REPO_ROOT_ENV)
        raw_text = str(raw_value or "").strip()
        if raw_text:
            return Path(raw_text).expanduser().resolve()
        raise RuntimeError(
            "Dart package strategy requires metadata repo_root/aware_repo_root "
            f"or {_AWARE_REPO_ROOT_ENV}; public kernel runtime must not discover "
            "repository roots"
        )

    def _render_pubspec(
        self,
        package_name: str,
        spec: ObjectConfigGraphPackageSpec,
        *,
        package_root: Path,
    ) -> str:
        # Dart pubspec package names must be valid Dart identifiers:
        # - lowercase letters, digits, underscores
        # - must not contain hyphens
        #
        # We keep `package_name` as the external/workflow identity, but normalize for pubspec.
        pubspec_name = package_name.replace("-", "_")
        description = spec.description or f"Auto-generated Dart package {package_name}"
        deps = list(spec.dependencies or [])
        optional = spec.optional_dependencies or {}
        dev_deps = list(optional.get("dev", []))
        metadata = spec.metadata or {}
        dependency_repo_roots = self._metadata_dependency_repo_roots(metadata)
        pkg_kind = str(metadata.get("aware_package_kind") or "").strip().lower()
        is_api_package = pkg_kind == "api"
        is_ontology_dto_package = pkg_kind == "ontology_dto"
        has_flutter_dependency = any(
            str(dep).strip().startswith("flutter:") for dep in deps
        )
        flutter_package_flag = self._metadata_bool(metadata.get("flutter_package"))
        is_flutter_package = (
            has_flutter_dependency
            if flutter_package_flag is None
            else flutter_package_flag
        )
        uses_material_design_value = self._metadata_bool(
            metadata.get("uses_material_design")
            if metadata.get("uses_material_design") is not None
            else metadata.get("uses-material-design")
        )

        # ------------------------------------------------------------
        # Strict defaults for Aware-generated Dart API packages
        # ------------------------------------------------------------
        # 1) Codegen toolchain: we run `dart run build_runner build` as a post-step by default,
        #    and the generated code uses @freezed/@JsonSerializable.
        #
        # 2) Runtime deps: generated code imports json_annotation/freezed_annotation/uuid and
        #    also uses Aware's shared converter utilities (aware_model_helpers).
        #
        # Workflows can override any of these by explicitly setting dependencies/dev deps.

        # Runtime dependencies (inject if missing)
        if not any(str(dep).strip().startswith("freezed_annotation:") for dep in deps):
            deps.append("freezed_annotation: ^3.0.0")
        if not any(str(dep).strip().startswith("json_annotation:") for dep in deps):
            deps.append("json_annotation: ^4.9.0")
        if not any(str(dep).strip().startswith("uuid:") for dep in deps):
            deps.append("uuid: ^4.5.1")
        if is_flutter_package and not has_flutter_dependency:
            deps.insert(0, "flutter:\n  sdk: flutter")
        repo_root: Path | None = None

        def _repo_root() -> Path:
            nonlocal repo_root
            if repo_root is None:
                repo_root = self._explicit_repo_root(metadata)
            return repo_root

        for dependency_name, dependency_path in self._metadata_path_dependencies(
            metadata
        ).items():
            if dependency_name == pubspec_name or self._dependency_declared(
                deps, dependency_name
            ):
                continue
            dependency_dir = self._resolve_declared_path_dependency_dir(
                package_root=package_root,
                repo_root=_repo_root(),
                dependency_repo_roots=dependency_repo_roots,
                dependency_name=dependency_name,
                dependency_path=dependency_path,
                pubspec_name=pubspec_name,
            )
            rel = os.path.relpath(dependency_dir, start=package_root.resolve())
            deps.append(f"{dependency_name}:\n  path: {Path(rel).as_posix()}")

        for dependency_import_root in self._metadata_dependency_import_roots(metadata):
            dependency_name = dependency_import_root.replace("-", "_")
            if dependency_name == pubspec_name or self._dependency_declared(
                deps, dependency_name
            ):
                continue
            dependency_dir = self._resolve_aware_ontology_dependency_dir(
                package_root=package_root,
                repo_root=_repo_root(),
                dependency_repo_roots=dependency_repo_roots,
                dependency_import_root=dependency_import_root,
                pubspec_name=pubspec_name,
            )
            rel = os.path.relpath(dependency_dir, start=package_root.resolve())
            deps.append(f"{dependency_name}:\n  path: {Path(rel).as_posix()}")
        # Kernel-level helper package used by generated converters.
        if not any(str(dep).strip().startswith("aware_model_helpers:") for dep in deps):
            helpers_dir = self._resolve_workspace_dependency_dir(
                package_root=package_root,
                repo_root=_repo_root(),
                dependency_repo_roots=dependency_repo_roots,
                rel_parts=("libs", "model_helpers", "dart", "aware_model_helpers"),
                pubspec_name=pubspec_name,
                dependency_name="aware_model_helpers",
            )
            rel = os.path.relpath(helpers_dir, start=package_root.resolve())
            deps.append(f"aware_model_helpers:\n  path: {Path(rel).as_posix()}")
        # Aware API Dart (required by ontology model packages for function invocation helpers).
        # API packages must stay transport-only and must not depend on the Interface API package to avoid
        # pubspec cycles (Interface API depends on module APIs).
        if not (is_api_package or is_ontology_dto_package) and not any(
            str(dep).strip().startswith("aware_api:") for dep in deps
        ):
            aware_api_dir = self._resolve_workspace_dependency_dir(
                package_root=package_root,
                repo_root=_repo_root(),
                dependency_repo_roots=dependency_repo_roots,
                rel_parts=("libs", "api", "dart"),
                pubspec_name=pubspec_name,
                dependency_name="aware_api",
            )
            rel = os.path.relpath(aware_api_dir, start=package_root.resolve())
            deps.append(f"aware_api:\n  path: {Path(rel).as_posix()}")

        # Dev dependencies (inject if missing)
        if not any(str(dep).strip().startswith("build_runner:") for dep in dev_deps):
            dev_deps = [*dev_deps, "build_runner: ^2.4.11"]
        if not any(str(dep).strip().startswith("freezed:") for dep in dev_deps):
            dev_deps = [*dev_deps, "freezed: ^3.0.0"]
        if not any(
            str(dep).strip().startswith("json_serializable:") for dep in dev_deps
        ):
            dev_deps = [*dev_deps, "json_serializable: ^6.8.0"]

        def _indent_yaml_block(block: str, *, indent: str) -> str:
            lines = block.splitlines() or [block]
            return "\n".join(
                f"{indent}{line}" if line.strip() else line for line in lines
            )

        deps_lines = "\n".join(
            _indent_yaml_block(str(dep), indent="  ") for dep in deps
        )
        dev_lines = "\n".join(
            _indent_yaml_block(str(dep), indent="  ") for dep in dev_deps
        )

        sdk_constraint = str(
            spec.metadata.get("sdk_constraint")
            or spec.metadata.get("dart_sdk_constraint")
            or self.DEFAULT_SDK_CONSTRAINT
        ).strip()
        if not sdk_constraint:
            sdk_constraint = self.DEFAULT_SDK_CONSTRAINT

        lines = [
            f"name: {pubspec_name}",
            f"description: {description}",
            f"version: {spec.version}",
            "publish_to: none",
            "",
            "environment:",
            f'  sdk: "{sdk_constraint}"',
            "",
            "dependencies:",
        ]
        if deps_lines:
            lines.append(deps_lines)
        else:
            lines.append("  # Add dependencies here")

        lines.append("")
        lines.append("dev_dependencies:")
        if dev_lines:
            lines.append(dev_lines)
        else:
            lines.append("  # Add dev dependencies here")

        if is_flutter_package:
            if uses_material_design_value is None:
                uses_material_design_value = True
            lines.extend(
                [
                    "",
                    "flutter:",
                    f"  uses-material-design: {'true' if uses_material_design_value else 'false'}",
                ]
            )

        return "\n".join(lines) + "\n"
