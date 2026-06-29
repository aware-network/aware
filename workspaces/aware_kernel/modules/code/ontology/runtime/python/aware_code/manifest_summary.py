from __future__ import annotations

from pathlib import Path
from typing import Mapping

from aware_code.manifest_resolution import SemanticManifestResolution
from aware_code.module_semantic_contract import (
    ModuleSemanticManifestResolutionDescriptor,
)
from aware_code.package.schemas import CodePackageInfo
from aware_code.package_surface import (
    code_package_surface_from_semantic_manifest_descriptor,
)
from aware_code_ontology.code.code_enums import CodeLanguage


def code_package_info_from_semantic_manifest_resolution(
    *,
    resolution: SemanticManifestResolution,
    workspace_root: Path | None = None,
    manifest_relative_path: str | None = None,
) -> CodePackageInfo | None:
    """Build CodePackageInfo from semantic-contract-owned manifest resolution."""

    descriptor = resolution.descriptor
    manifest_path = resolution.manifest_path
    relative_manifest_path = _relative_manifest_path(
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        manifest_relative_path=manifest_relative_path,
    )
    package_section = _semantic_manifest_package_section(
        manifest=resolution.manifest,
        descriptor=descriptor,
    )
    if package_section is None:
        return None
    package_name = _semantic_manifest_package_name(
        package_section=package_section,
        descriptor=descriptor,
    )
    if package_name is None:
        return None

    relative_package_root = relative_manifest_path.parent
    absolute_package_root = manifest_path.parent.resolve()
    metadata = _semantic_manifest_code_package_metadata(
        descriptor=descriptor,
        manifest=resolution.manifest,
        package_section=package_section,
        workspace_root=workspace_root,
        absolute_package_root=absolute_package_root,
        relative_package_root=relative_package_root,
        relative_manifest_path=relative_manifest_path,
    )
    return CodePackageInfo(
        name=package_name,
        root_path=relative_package_root,
        manifest_path=relative_manifest_path,
        language=CodeLanguage.aware,
        metadata=metadata,
    )


def _relative_manifest_path(
    *,
    manifest_path: Path,
    workspace_root: Path | None,
    manifest_relative_path: str | None,
) -> Path:
    if manifest_relative_path is not None and manifest_relative_path.strip():
        return Path(manifest_relative_path.strip())
    if workspace_root is None:
        return manifest_path
    return Path(
        _relative_to_root(
            path=manifest_path.resolve(),
            root=workspace_root.resolve(),
        )
    )


def _semantic_manifest_package_section(
    *,
    manifest: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> object | None:
    explicit_name = _metadata_string(
        descriptor.semantic_package_metadata,
        "package_section_name",
    )
    if explicit_name is not None:
        return getattr(manifest, explicit_name, None)
    if descriptor.workspace_manifest_kind is not None:
        section = getattr(manifest, descriptor.workspace_manifest_kind, None)
        if section is not None:
            return section
    if descriptor.semantic_package_family is not None:
        section = getattr(manifest, descriptor.semantic_package_family, None)
        if section is not None:
            return section
    return getattr(manifest, "package", None)


def _semantic_manifest_package_name(
    *,
    package_section: object,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> str | None:
    package_name = _string_attribute(package_section, "package_name")
    if package_name is not None:
        return package_name
    package_name_attr = _metadata_string(
        descriptor.semantic_package_metadata,
        "package_name_attribute",
    )
    package_name_template = _metadata_string(
        descriptor.semantic_package_metadata,
        "package_name_template",
    )
    if package_name_attr is not None:
        raw_value = _string_attribute(package_section, package_name_attr)
        if raw_value is None:
            return None
        if package_name_template is not None:
            return package_name_template.format(value=_slugify(raw_value))
        return raw_value
    return None


def _semantic_manifest_code_package_metadata(
    *,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    manifest: object,
    package_section: object,
    workspace_root: Path | None,
    absolute_package_root: Path,
    relative_package_root: Path,
    relative_manifest_path: Path,
) -> dict[str, object]:
    build_section = getattr(manifest, "build", None)
    sources_dir = _string_attribute(build_section, "sources_dir") or "."
    manifest_package_kind = _string_attribute(package_section, "kind")
    absolute_source_root = (absolute_package_root / sources_dir).resolve()
    source_root = _relative_metadata_path(
        path=absolute_source_root,
        workspace_root=workspace_root,
        fallback=relative_package_root / sources_dir,
    )
    metadata: dict[str, object] = {
        "manifest_kind": descriptor.manifest_kind,
        "authored_manifest_kind": descriptor.manifest_kind,
        "package_root": relative_package_root.as_posix(),
        "package_kind": manifest_package_kind
        or descriptor.workspace_manifest_kind
        or descriptor.semantic_package_family
        or descriptor.semantic_package_kind
        or descriptor.manifest_kind,
        "source_root": source_root,
        "include_paths": _string_tuple_attribute(build_section, "include_paths"),
        "exclude_paths": _string_tuple_attribute(build_section, "exclude_paths"),
        "owned_file_paths": [],
        _manifest_path_metadata_key(descriptor.manifest_kind): (
            relative_manifest_path.as_posix()
        ),
        "semantic_manifest_kind": descriptor.manifest_kind,
        "semantic_owner": descriptor.semantic_owner,
    }
    code_package_surface = code_package_surface_from_semantic_manifest_descriptor(
        descriptor,
        package_kind=manifest_package_kind,
    )
    if code_package_surface is None:
        raise ValueError(
            "Semantic manifest descriptor must declare code_package_surface: "
            f"{descriptor.semantic_owner}/{descriptor.manifest_kind}"
        )
    if descriptor.semantic_package_metadata is not None:
        metadata.update(
            {
                key: value
                for key, value in dict(descriptor.semantic_package_metadata).items()
                if key != "code_package_surface"
            }
        )
    metadata["code_package_surface"] = code_package_surface
    if descriptor.semantic_package_family is not None:
        metadata["semantic_package_family"] = descriptor.semantic_package_family
    if descriptor.semantic_package_kind is not None:
        metadata["semantic_package_kind"] = descriptor.semantic_package_kind
    _copy_descriptor_metadata_keys(
        metadata=metadata,
        keys=descriptor.copy_code_package_metadata_keys,
        manifest=manifest,
        package_section=package_section,
        absolute_package_root=absolute_package_root,
        workspace_root=workspace_root,
    )
    metadata["code_package_surface"] = code_package_surface
    return metadata


def _copy_descriptor_metadata_keys(
    *,
    metadata: dict[str, object],
    keys: tuple[str, ...],
    manifest: object,
    package_section: object,
    absolute_package_root: Path,
    workspace_root: Path | None,
) -> None:
    for key in keys:
        value = _metadata_value_for_key(
            key=key,
            manifest=manifest,
            package_section=package_section,
            absolute_package_root=absolute_package_root,
            workspace_root=workspace_root,
        )
        if value is not None:
            metadata[key] = value


def _metadata_value_for_key(
    *,
    key: str,
    manifest: object,
    package_section: object,
    absolute_package_root: Path,
    workspace_root: Path | None,
) -> object | None:
    if key == "package_kind":
        return None
    if key == "environment_handle":
        return _string_attribute(getattr(manifest, "build", None), key) or (
            _string_attribute(package_section, "handle")
        )
    if key == "package_root":
        return _package_relative_metadata_path(
            package_section=package_section,
            attribute_name=key,
            absolute_package_root=absolute_package_root,
            workspace_root=workspace_root,
        )
    if key == "sources_root":
        return _package_relative_metadata_path(
            package_section=package_section,
            attribute_name=key,
            absolute_package_root=absolute_package_root,
            workspace_root=workspace_root,
        )
    if key == "semantic_runtime_manifest_path":
        return _package_relative_metadata_path(
            package_section=package_section,
            attribute_name="source_manifest",
            absolute_package_root=absolute_package_root,
            workspace_root=workspace_root,
        )
    if key == "runtime_manifest":
        return _string_attribute(getattr(manifest, "runtime", None), "manifest")
    if key == "runtime_project_name":
        return _string_attribute(getattr(manifest, "runtime", None), "project_name")
    if key == "runtime_import_root":
        return _string_attribute(getattr(manifest, "runtime", None), "import_root")
    if key == "layout_output_dirs":
        value = getattr(getattr(manifest, "layout", None), "output_dirs", None)
        return value if isinstance(value, dict) else None
    if key == "language_materialization_targets":
        return _language_materialization_targets_payload(
            getattr(manifest, "language_materialization_targets", None)
        )
    if key == "dependency_package_names":
        return tuple(
            dependency_name
            for dependency in tuple(getattr(manifest, "dependencies", ()) or ())
            for dependency_name in (_string_attribute(dependency, "package_name"),)
            if dependency_name
        )
    if key.startswith("layout_"):
        return _string_attribute(
            getattr(manifest, "layout", None),
            key.removeprefix("layout_"),
        )
    if key == "declared_semantic_contract_provider_key":
        return _string_attribute(
            getattr(manifest, "semantic_contract", None),
            "provider_key",
        )
    if key == "declared_semantic_contract_role":
        return _string_attribute(getattr(manifest, "semantic_contract", None), "role")
    if key == "declared_semantic_contract_module":
        return _string_attribute(
            getattr(manifest, "semantic_contract", None),
            "module",
        )
    if key == "declared_semantic_contract_owns_manifest_kinds":
        return _string_tuple_attribute(
            getattr(manifest, "semantic_contract", None),
            "owns_manifest_kinds",
        )
    if key == "declared_semantic_contract_capabilities":
        return _string_tuple_attribute(
            getattr(manifest, "semantic_contract", None),
            "capabilities",
        )
    return _string_attribute(package_section, key) or _string_attribute(
        getattr(manifest, "build", None),
        key,
    )


def _language_materialization_targets_payload(value: object) -> list[dict[str, object]]:
    if not isinstance(value, (tuple, list)):
        return []
    targets: list[dict[str, object]] = []
    for item in value:
        target = _language_materialization_target_payload(item)
        if target:
            targets.append(target)
    return targets


def _language_materialization_target_payload(value: object) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key in (
        "role",
        "language",
        "output_dir",
        "import_root",
        "package_name",
        "materialization_source",
        "code_package_surface",
        "renderer_profile",
        "renderer_kind",
        "stable_ids_import_root",
        "stable_ids_ownership",
        "stable_ids_resolution_policy",
    ):
        raw_value = getattr(value, key, None)
        if isinstance(raw_value, str) and raw_value.strip():
            payload[key] = raw_value.strip()
    if getattr(value, "source_is_runtime", False) is True:
        payload["source_is_runtime"] = True
    return payload


def _package_relative_metadata_path(
    *,
    package_section: object,
    attribute_name: str,
    absolute_package_root: Path,
    workspace_root: Path | None,
) -> str | None:
    raw_value = _string_attribute(package_section, attribute_name)
    if raw_value is None:
        return None
    return _relative_metadata_path(
        path=(absolute_package_root / raw_value).resolve(),
        workspace_root=workspace_root,
        fallback=Path(raw_value),
    )


def _relative_metadata_path(
    *,
    path: Path,
    workspace_root: Path | None,
    fallback: Path,
) -> str:
    if workspace_root is None:
        return fallback.as_posix()
    return _relative_to_root(path=path, root=workspace_root.resolve())


def _manifest_path_metadata_key(manifest_kind: str) -> str:
    return f"{manifest_kind}_path"


def _string_attribute(target: object, attribute_name: str) -> str | None:
    value = getattr(target, attribute_name, None)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _string_tuple_attribute(target: object, attribute_name: str) -> tuple[str, ...]:
    value = getattr(target, attribute_name, None)
    if not isinstance(value, tuple):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _metadata_string(
    metadata: Mapping[str, object] | None,
    key: str,
) -> str | None:
    if metadata is None:
        return None
    value = metadata.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _relative_to_root(*, path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _slugify(value: str) -> str:
    slug_chars: list[str] = []
    previous_was_separator = False
    for char in value.strip().casefold():
        if char.isalnum():
            slug_chars.append(char)
            previous_was_separator = False
            continue
        if previous_was_separator:
            continue
        slug_chars.append("-")
        previous_was_separator = True
    return "".join(slug_chars).strip("-")


__all__ = [
    "code_package_info_from_semantic_manifest_resolution",
]
