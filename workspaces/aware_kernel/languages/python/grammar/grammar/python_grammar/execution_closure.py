"""Python execution closure materialization."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil

from aware_code.language.execution_closure import (
    CodeLanguageExecutionClosureRequest,
    CodeLanguageExecutionClosureResult,
    CodeLanguageExecutionPackageRef,
)


_COPY_IGNORE_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "sample",
    "samples",
    "test",
    "tests",
}


class PythonExecutionClosureBuilder:
    """Materialize a replayable Python project for selected package refs."""

    def materialize_execution_closure(
        self,
        request: CodeLanguageExecutionClosureRequest,
    ) -> CodeLanguageExecutionClosureResult:
        output_root = request.output_root.expanduser().resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        project_path = output_root / "pyproject.toml"
        manifest_path = output_root / "execution-closure.manifest.json"
        portable_root = _portable_root_for_output(output_root)

        packages = tuple(
            self._resolve_package_source(
                output_root=output_root,
                portable_root=portable_root,
                package_ref=package_ref,
            )
            for package_ref in _dedupe_packages(request.packages)
        )
        project_path.write_text(
            _render_pyproject(
                project_name=_safe_project_name(request.closure_key),
                packages=packages,
                output_root=output_root,
            ),
            encoding="utf-8",
        )
        manifest_payload = {
            "version": "aware.code.language.execution_closure.python.v0",
            "language": "python",
            "closure_key": request.closure_key,
            "output_root": output_root.as_posix(),
            "project_path": project_path.as_posix(),
            "packages": [_package_payload(package_ref) for package_ref in packages],
            "launchers": [
                {
                    "launcher_key": launcher.launcher_key,
                    "module": launcher.module,
                    "package_name": launcher.package_name,
                    "description": launcher.description,
                }
                for launcher in request.launchers
            ],
            "metadata": dict(request.metadata),
        }
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return CodeLanguageExecutionClosureResult(
            closure_key=request.closure_key,
            output_root=output_root,
            project_path=project_path,
            manifest_path=manifest_path,
            packages=packages,
            launchers=request.launchers,
            command_prefix=("uv", "run", "--project", project_path.parent.as_posix()),
            environment={
                "AWARE_DEPLOY_PYTHON_PROJECT_PATH": project_path.parent.as_posix(),
                "AWARE_DEPLOY_PYTHON_EXECUTION_CLOSURE_MANIFEST_PATH": (
                    manifest_path.as_posix()
                ),
            },
            metadata={"language": "python", **dict(request.metadata)},
        )

    def _resolve_package_source(
        self,
        *,
        output_root: Path,
        portable_root: Path,
        package_ref: CodeLanguageExecutionPackageRef,
    ) -> CodeLanguageExecutionPackageRef:
        alias_for = package_ref.metadata.get("python_dependency_alias_for")
        if isinstance(alias_for, str) and alias_for.strip():
            alias_root = (
                output_root
                / "sources"
                / package_ref.role
                / _safe_path_name(package_ref.package_name)
            )
            _write_dependency_alias_package(
                alias_root=alias_root,
                alias_name=package_ref.package_name,
                target_name=alias_for.strip(),
            )
            return replace(
                package_ref,
                source_root=alias_root.resolve(),
                manifest_path=(alias_root / "pyproject.toml").resolve(),
            )

        source_root = package_ref.source_root
        if source_root is None:
            return package_ref

        resolved_source_root = source_root.expanduser().resolve()
        if package_ref.copy_to_closure:
            copied_root = (
                output_root
                / "sources"
                / package_ref.role
                / _safe_path_name(package_ref.package_name)
            )
            if copied_root.exists():
                shutil.rmtree(copied_root)
            shutil.copytree(
                resolved_source_root,
                copied_root,
                ignore=_copy_ignore,
            )
            _sanitize_copied_pyproject(copied_root / "pyproject.toml")
            copied_manifest_path = None
            if package_ref.manifest_path is not None:
                resolved_manifest_path = package_ref.manifest_path.expanduser().resolve()
                if _is_relative_to(resolved_manifest_path, resolved_source_root):
                    copied_manifest_path = (
                        copied_root
                        / resolved_manifest_path.relative_to(resolved_source_root)
                    ).resolve()
            return replace(
                package_ref,
                source_root=copied_root.resolve(),
                manifest_path=copied_manifest_path,
            )

        if not _is_relative_to(resolved_source_root, portable_root):
            raise ValueError(
                "Python execution closure source roots must be under the run "
                "directory or copied into the closure: "
                f"{package_ref.package_name} -> {resolved_source_root}"
            )
        return replace(package_ref, source_root=resolved_source_root)


def _render_pyproject(
    *,
    project_name: str,
    packages: tuple[CodeLanguageExecutionPackageRef, ...],
    output_root: Path,
) -> str:
    dependency_names = tuple(
        sorted({package.package_name for package in packages if package.required})
    )
    source_packages = tuple(
        sorted(
            (
                package
                for package in packages
                if package.source_root is not None
            ),
            key=lambda package: package.package_name,
        )
    )
    lines = [
        "[project]",
        f"name = {_toml_string(project_name)}",
        'version = "0.0.0"',
        'description = "Aware WorkspaceRevision Python execution closure"',
        'requires-python = ">=3.12"',
        "dependencies = [",
    ]
    lines.extend(f"  {_toml_string(name)}," for name in dependency_names)
    lines.extend(
        [
            "]",
            "",
            "[tool.uv]",
            "package = false",
        ]
    )
    if source_packages:
        lines.extend(["", "[tool.uv.sources]"])
        for package in source_packages:
            assert package.source_root is not None
            relative_path = _relative_path(package.source_root, output_root)
            lines.append(
                f"{_toml_string(package.package_name)} = "
                f"{{ path = {_toml_string(relative_path)} }}"
            )
    return "\n".join(lines) + "\n"


def _dedupe_packages(
    packages: tuple[CodeLanguageExecutionPackageRef, ...],
) -> tuple[CodeLanguageExecutionPackageRef, ...]:
    by_name: dict[str, CodeLanguageExecutionPackageRef] = {}
    for package in packages:
        name = package.package_name.strip()
        if not name:
            raise ValueError("Python execution package name is required")
        if name not in by_name:
            by_name[name] = package
    return tuple(by_name[name] for name in sorted(by_name))


def _package_payload(package_ref: CodeLanguageExecutionPackageRef) -> dict[str, object]:
    return {
        "package_name": package_ref.package_name,
        "role": package_ref.role,
        "source_root": (
            package_ref.source_root.as_posix()
            if package_ref.source_root is not None
            else None
        ),
        "manifest_path": (
            package_ref.manifest_path.as_posix()
            if package_ref.manifest_path is not None
            else None
        ),
        "authority": package_ref.authority,
        "copy_to_closure": package_ref.copy_to_closure,
        "required": package_ref.required,
        "metadata": dict(package_ref.metadata),
    }


def _write_dependency_alias_package(
    *,
    alias_root: Path,
    alias_name: str,
    target_name: str,
) -> None:
    if alias_root.exists():
        shutil.rmtree(alias_root)
    package_dir = alias_root / "aware_python_dependency_alias"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text(
        '"""Dependency-only distribution alias generated by Aware deployment."""\n',
        encoding="utf-8",
    )
    (alias_root / "pyproject.toml").write_text(
        "\n".join(
            (
                "[project]",
                f"name = {_toml_string(alias_name)}",
                'version = "0.0.0"',
                'description = "Aware deployment dependency alias"',
                'requires-python = ">=3.12"',
                "dependencies = [",
                f"  {_toml_string(target_name)},",
                "]",
                "",
                "[build-system]",
                'requires = ["hatchling>=1.27.0"]',
                'build-backend = "hatchling.build"',
                "",
                "[tool.hatch.build.targets.wheel]",
                'packages = ["aware_python_dependency_alias"]',
                "",
            )
        ),
        encoding="utf-8",
    )


def _sanitize_copied_pyproject(path: Path) -> None:
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    sanitized_lines: list[str] = []
    skipping_tool_uv_workspace_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            skipping_tool_uv_workspace_block = stripped in {
                "[tool.uv.sources]",
                "[tool.uv.workspace]",
            }
            if skipping_tool_uv_workspace_block:
                continue
        if skipping_tool_uv_workspace_block:
            continue
        sanitized_lines.append(line)
    path.write_text("\n".join(sanitized_lines).rstrip() + "\n", encoding="utf-8")


def _portable_root_for_output(output_root: Path) -> Path:
    # output_root is <run_dir>/runtime/python in Workspace deployment prepare.
    try:
        return output_root.parents[1]
    except IndexError:
        return output_root


def _relative_path(path: Path, base: Path) -> str:
    if _is_relative_to(path, base):
        return path.relative_to(base).as_posix()
    portable_root = _portable_root_for_output(base)
    if _is_relative_to(path, portable_root):
        return Path("..", "..", path.relative_to(portable_root)).as_posix()
    return path.as_posix()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _copy_ignore(directory: str, names: list[str]) -> set[str]:
    _ = directory
    ignored = {name for name in names if name in _COPY_IGNORE_NAMES}
    ignored.update(name for name in names if name.endswith((".pyc", ".pyo")))
    return ignored


def _safe_project_name(value: str) -> str:
    normalized = _safe_path_name(value).replace("_", "-")
    return normalized or "aware-workspace-execution-closure"


def _safe_path_name(value: str) -> str:
    return "".join(
        character if character.isalnum() or character in "._-" else "-"
        for character in value.strip().lower()
    ).strip(".-")


def _toml_string(value: str) -> str:
    return json.dumps(value)


__all__ = ["PythonExecutionClosureBuilder"]
