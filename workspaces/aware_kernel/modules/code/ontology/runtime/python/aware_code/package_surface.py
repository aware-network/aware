from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleSemanticManifestResolutionDescriptor,
)


def normalize_code_package_surface(value: object | None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def code_package_surface_from_metadata(
    metadata: dict[str, object] | None,
) -> str | None:
    if metadata is None:
        return None
    return normalize_code_package_surface(metadata.get("code_package_surface"))


def code_package_surface_from_package_kind(package_kind: str | None) -> str | None:
    return normalize_code_package_surface(package_kind)


def code_package_surface_from_semantic_manifest_descriptor(
    descriptor: ModuleSemanticManifestResolutionDescriptor,
    *,
    package_kind: str | None = None,
) -> str | None:
    direct_surface = normalize_code_package_surface(descriptor.code_package_surface)
    if direct_surface is not None:
        return direct_surface
    if package_kind is None:
        return None
    surface_by_package_kind = descriptor.code_package_surface_by_package_kind
    if surface_by_package_kind is None:
        return None
    return normalize_code_package_surface(surface_by_package_kind.get(package_kind))


__all__ = [
    "code_package_surface_from_metadata",
    "code_package_surface_from_package_kind",
    "code_package_surface_from_semantic_manifest_descriptor",
    "normalize_code_package_surface",
]
