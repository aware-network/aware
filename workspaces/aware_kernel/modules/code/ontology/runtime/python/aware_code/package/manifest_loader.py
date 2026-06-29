from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib

PACKAGE_MANAGER_NAME_KEY_METADATA_KEY = "package_manager_name_key"
PACKAGE_DEPENDENCY_NAMES_METADATA_KEY = "package_dependency_names"
PACKAGE_DEPENDENCY_KEYS_METADATA_KEY = "package_dependency_keys"
_PYTHON_REQUIREMENT_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


@dataclass(frozen=True, slots=True)
class CodeRuntimePackageManifest:
    """Code-owned runtime package manifest summary."""

    package_name: str
    manifest_kind: str
    manifest_path: Path
    package_manager_name_key: str | None = None
    package_dependency_names: tuple[str, ...] = ()
    package_dependency_keys: tuple[str, ...] = ()


def load_pyproject_toml_package_manifest(
    *,
    toml_path: Path,
) -> CodeRuntimePackageManifest:
    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    project = data.get("project")
    tool = data.get("tool")
    package_name = _optional_mapping_text(project, "name")
    if package_name is None and isinstance(tool, dict):
        poetry = tool.get("poetry")
        package_name = _optional_mapping_text(poetry, "name")
    resolved_package_name = package_name or toml_path.parent.name
    package_metadata = pyproject_package_manager_metadata(
        payload=data,
        package_name=resolved_package_name,
    )
    return CodeRuntimePackageManifest(
        package_name=resolved_package_name,
        manifest_kind="pyproject_toml",
        manifest_path=toml_path,
        package_manager_name_key=_metadata_text(
            package_metadata,
            PACKAGE_MANAGER_NAME_KEY_METADATA_KEY,
        ),
        package_dependency_names=tuple(
            _metadata_text_tuple(
                package_metadata,
                PACKAGE_DEPENDENCY_NAMES_METADATA_KEY,
            )
        ),
        package_dependency_keys=tuple(
            _metadata_text_tuple(
                package_metadata,
                PACKAGE_DEPENDENCY_KEYS_METADATA_KEY,
            )
        ),
    )


def load_setup_py_package_manifest(
    *,
    toml_path: Path,
) -> CodeRuntimePackageManifest:
    text = toml_path.read_text(encoding="utf-8")
    package_name = None
    match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", text)
    if match is not None:
        package_name = _optional_text(match.group(1))
    resolved_package_name = package_name or toml_path.parent.name
    return CodeRuntimePackageManifest(
        package_name=resolved_package_name,
        manifest_kind="setup_py",
        manifest_path=toml_path,
        package_manager_name_key=_canonical_python_package_name(
            resolved_package_name
        ),
    )


def load_pubspec_yaml_package_manifest(
    *,
    toml_path: Path,
) -> CodeRuntimePackageManifest:
    text = toml_path.read_text(encoding="utf-8")
    package_name = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("name:"):
            continue
        package_name = _optional_text(stripped.removeprefix("name:"))
        break
    return CodeRuntimePackageManifest(
        package_name=package_name or toml_path.parent.name,
        manifest_kind="pubspec_yaml",
        manifest_path=toml_path,
    )


def pyproject_package_manager_metadata(
    *,
    payload: dict[str, object],
    package_name: str,
) -> dict[str, object]:
    dependency_names = _pyproject_dependency_names(payload)
    return {
        PACKAGE_MANAGER_NAME_KEY_METADATA_KEY: _canonical_python_package_name(
            package_name
        ),
        PACKAGE_DEPENDENCY_NAMES_METADATA_KEY: list(dependency_names),
        PACKAGE_DEPENDENCY_KEYS_METADATA_KEY: [
            _canonical_python_package_name(name) for name in dependency_names
        ],
    }


def load_pyproject_package_manager_metadata(
    *,
    toml_path: Path,
    package_name: str | None = None,
) -> dict[str, object]:
    payload = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    project = payload.get("project")
    resolved_package_name = package_name or _optional_mapping_text(project, "name")
    if resolved_package_name is None:
        tool = payload.get("tool")
        if isinstance(tool, dict):
            resolved_package_name = _optional_mapping_text(tool.get("poetry"), "name")
    return pyproject_package_manager_metadata(
        payload=payload,
        package_name=resolved_package_name or toml_path.parent.name,
    )


def _optional_mapping_text(value: object, key: str) -> str | None:
    if not isinstance(value, dict):
        return None
    return _optional_text(value.get(key))


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().strip("\"'")
    return normalized or None


def _pyproject_dependency_names(payload: dict[str, object]) -> tuple[str, ...]:
    project = payload.get("project")
    if not isinstance(project, dict):
        return ()
    raw_dependency_values: list[object] = []
    raw_dependency_values.extend(
        _dependency_values_from_object(project.get("dependencies"))
    )
    optional_dependencies = project.get("optional-dependencies")
    if isinstance(optional_dependencies, dict):
        for raw_optional_values in optional_dependencies.values():
            raw_dependency_values.extend(
                _dependency_values_from_object(raw_optional_values)
            )
    dependency_groups = payload.get("dependency-groups")
    if isinstance(dependency_groups, dict):
        for raw_group_values in dependency_groups.values():
            raw_dependency_values.extend(
                _dependency_values_from_object(raw_group_values)
            )
    dependency_names: list[str] = []
    seen: set[str] = set()
    for raw_dependency in raw_dependency_values:
        if not isinstance(raw_dependency, str):
            continue
        dependency_name = _dependency_name_from_requirement(raw_dependency)
        if dependency_name is None:
            continue
        dependency_key = _canonical_python_package_name(dependency_name)
        if dependency_key in seen:
            continue
        seen.add(dependency_key)
        dependency_names.append(dependency_name)
    return tuple(dependency_names)


def _dependency_values_from_object(value: object) -> list[object]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list | tuple):
        return []
    values: list[object] = []
    for item in value:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            values.extend(_dependency_values_from_object(item.get("dependencies")))
    return values


def _dependency_name_from_requirement(requirement: str) -> str | None:
    match = _PYTHON_REQUIREMENT_NAME_RE.match(requirement)
    if match is None:
        return None
    return match.group(1).strip() or None


def _canonical_python_package_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _metadata_text(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _metadata_text_tuple(payload: dict[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


__all__ = [
    "CodeRuntimePackageManifest",
    "PACKAGE_DEPENDENCY_KEYS_METADATA_KEY",
    "PACKAGE_DEPENDENCY_NAMES_METADATA_KEY",
    "PACKAGE_MANAGER_NAME_KEY_METADATA_KEY",
    "load_pyproject_package_manager_metadata",
    "load_pubspec_yaml_package_manifest",
    "load_pyproject_toml_package_manifest",
    "load_setup_py_package_manifest",
    "pyproject_package_manager_metadata",
]
