"""Python operational workspace materialization."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from aware_code.language.operational_workspace import (
    CodeLanguageOperationalPackageRef,
    CodeLanguageOperationalWorkspaceRequest,
    CodeLanguageOperationalWorkspaceResult,
)
from aware_code_ontology.code.code_enums import CodeLanguage


_PYTHON_OPERATIONAL_WORKSPACE_VERSION = (
    "aware.code.language.operational_workspace.python.v0"
)
_PYTHON_OPERATIONAL_WORKSPACE_MANIFEST = (
    Path(".aware") / "workspace" / "python-operational-workspace.manifest.json"
)


class PythonOperationalWorkspaceBuilder:
    """Materialize a UV-backed Python workspace for committed package refs."""

    def materialize_operational_workspace(
        self,
        request: CodeLanguageOperationalWorkspaceRequest,
    ) -> CodeLanguageOperationalWorkspaceResult:
        if request.language != CodeLanguage.python:
            raise ValueError(
                "Python operational workspace requires python language request: "
                f"language={request.language.value!r}"
            )

        output_root = request.output_root.expanduser().resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        packages = tuple(
            self._resolve_package(
                output_root=output_root,
                package_ref=package_ref,
            )
            for package_ref in _dedupe_packages(request.packages)
        )
        status = "ready" if packages else "empty"
        project_path = output_root / "pyproject.toml"
        manifest_path = output_root / _PYTHON_OPERATIONAL_WORKSPACE_MANIFEST

        project_path.write_text(
            _render_pyproject(
                project_name=_safe_project_name(request.workspace_key),
                packages=packages,
                output_root=output_root,
            ),
            encoding="utf-8",
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "manifest_version": _PYTHON_OPERATIONAL_WORKSPACE_VERSION,
                    "language": "python",
                    "workspace_key": request.workspace_key,
                    "status": status,
                    "output_root": ".",
                    "project_path": "pyproject.toml",
                    "package_count": len(packages),
                    "packages": [
                        _package_payload(package_ref, output_root=output_root)
                        for package_ref in packages
                    ],
                    "command_prefix": ["uv", "run", "--project", "."],
                    "metadata": dict(request.metadata),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return CodeLanguageOperationalWorkspaceResult(
            workspace_key=request.workspace_key,
            language=CodeLanguage.python,
            status=status,
            output_root=output_root,
            project_path=project_path,
            manifest_path=manifest_path,
            packages=packages,
            command_prefix=("uv", "run", "--project", "."),
            environment={
                "AWARE_WORKSPACE_PYTHON_PROJECT_PATH": ".",
                "AWARE_WORKSPACE_PYTHON_OPERATIONAL_MANIFEST_PATH": (
                    _PYTHON_OPERATIONAL_WORKSPACE_MANIFEST.as_posix()
                ),
            },
            metadata={"language": "python", **dict(request.metadata)},
        )

    def _resolve_package(
        self,
        *,
        output_root: Path,
        package_ref: CodeLanguageOperationalPackageRef,
    ) -> CodeLanguageOperationalPackageRef:
        if package_ref.language != CodeLanguage.python:
            raise ValueError(
                "Python operational workspace received non-python package ref: "
                f"{package_ref.package_name} language={package_ref.language.value!r}"
            )
        package_name = package_ref.package_name.strip()
        if not package_name:
            raise ValueError("Python operational package name is required")
        if package_ref.source_root is None:
            return replace(package_ref, package_name=package_name)

        source_root = package_ref.source_root.expanduser().resolve()
        if not _is_relative_to(source_root, output_root):
            raise ValueError(
                "Python operational workspace package roots must be under the "
                "workspace output root: "
                f"{package_name} -> {source_root}"
            )
        manifest_path = package_ref.manifest_path
        resolved_manifest_path = (
            (source_root / "pyproject.toml").resolve()
            if manifest_path is None
            else manifest_path.expanduser().resolve()
        )
        if not _is_relative_to(resolved_manifest_path, source_root):
            raise ValueError(
                "Python operational workspace rejected manifest outside package "
                f"root: {package_name} -> {resolved_manifest_path}"
            )
        if resolved_manifest_path.name != "pyproject.toml":
            raise ValueError(
                "Python operational workspace requires pyproject-backed package "
                f"refs for UV workspace membership: {package_name}"
            )
        if not resolved_manifest_path.is_file():
            raise ValueError(
                "Python operational workspace package manifest is missing: "
                f"{package_name} -> {resolved_manifest_path}"
            )
        return replace(
            package_ref,
            package_name=package_name,
            source_root=source_root,
            manifest_path=resolved_manifest_path,
        )


def _render_pyproject(
    *,
    project_name: str,
    packages: tuple[CodeLanguageOperationalPackageRef, ...],
    output_root: Path,
) -> str:
    dependency_names = tuple(
        sorted({package.package_name for package in packages if package.required})
    )
    workspace_packages = tuple(
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
        'description = "Aware WorkspaceRevision Python operational workspace"',
        'requires-python = ">=3.12"',
        "dependencies = [",
    ]
    lines.extend(f"  {_toml_string(name)}," for name in dependency_names)
    lines.extend(["]", "", "[tool.uv]", "package = false"])
    if workspace_packages:
        lines.extend(["", "[tool.uv.workspace]", "members = ["])
        for package in workspace_packages:
            assert package.source_root is not None
            lines.append(
                f"  {_toml_string(_relative_path(package.source_root, output_root))},"
            )
        lines.extend(["]", "", "[tool.uv.sources]"])
        for package in workspace_packages:
            lines.append(f"{_toml_string(package.package_name)} = {{ workspace = true }}")
    return "\n".join(lines) + "\n"


def _dedupe_packages(
    packages: tuple[CodeLanguageOperationalPackageRef, ...],
) -> tuple[CodeLanguageOperationalPackageRef, ...]:
    by_name: dict[str, CodeLanguageOperationalPackageRef] = {}
    for package in packages:
        name = package.package_name.strip()
        if not name:
            raise ValueError("Python operational package name is required")
        if name not in by_name:
            by_name[name] = package
    return tuple(by_name[name] for name in sorted(by_name))


def _package_payload(
    package_ref: CodeLanguageOperationalPackageRef,
    *,
    output_root: Path,
) -> dict[str, object]:
    source_root = (
        _relative_path(package_ref.source_root, output_root)
        if package_ref.source_root is not None
        else None
    )
    manifest_path = (
        _relative_path(package_ref.manifest_path, output_root)
        if package_ref.manifest_path is not None
        else None
    )
    return {
        "package_name": package_ref.package_name,
        "language": package_ref.language.value,
        "role": package_ref.role,
        "source_root": source_root,
        "manifest_path": manifest_path,
        "authority": package_ref.authority,
        "required": package_ref.required,
        "metadata": dict(package_ref.metadata),
    }


def _safe_project_name(raw_name: str) -> str:
    safe = "".join(
        character.lower() if character.isalnum() else "-"
        for character in raw_name.strip()
    ).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe or "aware-workspace"


def _relative_path(path: Path, output_root: Path) -> str:
    resolved_path = path.expanduser().resolve()
    try:
        return resolved_path.relative_to(output_root).as_posix()
    except ValueError as exc:
        raise ValueError(
            "Python operational workspace path is outside output root: "
            f"{resolved_path}"
        ) from exc


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
