from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aware_code.module_semantic_contract import ModuleSemanticManifestResolutionDescriptor
from aware_meta.manifest.loader import (
    load_aware_toml_spec,
    load_aware_toml_spec_from_text,
)
from aware_meta.manifest.spec import AwareTomlSpec
from aware_meta.semantic_contract import (
    AWARE_META_SEMANTIC_CONTRACT,
    META_MANIFEST_RESOLUTION,
)


@dataclass(frozen=True, slots=True)
class ObjectConfigGraphPackageManifestContract:
    """Meta-owned public contract for ObjectConfigGraphPackage manifests."""

    provider_key: str
    semantic_owner: str
    manifest_kind: str
    filename: str
    contract: str
    loader_module: str
    loader_name: str
    workspace_manifest_kind: str | None
    package_role: str | None
    semantic_package_family: str
    semantic_package_kind: str
    semantic_projection_name: str
    semantic_root_kind: str
    code_package_surface_by_package_kind: tuple[tuple[str, str], ...]

    def code_package_surface_for_package_kind(self, package_kind: str) -> str | None:
        normalized = package_kind.strip()
        if not normalized:
            return None
        return dict(self.code_package_surface_by_package_kind).get(normalized)


def object_config_graph_package_manifest_contract() -> (
    ObjectConfigGraphPackageManifestContract
):
    """Return the Meta-owned OCG package manifest contract.

    API, Ontology, and future semantic packages consume this facade when they need
    the raw ObjectConfigGraphPackage manifest boundary. They should not claim
    ownership of `aware_toml` themselves.
    """

    descriptor = object_config_graph_package_manifest_resolution_descriptor()
    surface_by_kind = descriptor.code_package_surface_by_package_kind or {}
    return ObjectConfigGraphPackageManifestContract(
        provider_key=AWARE_META_SEMANTIC_CONTRACT.provider_key,
        semantic_owner=_required_text(descriptor.semantic_owner, "semantic_owner"),
        manifest_kind=_required_text(descriptor.manifest_kind, "manifest_kind"),
        filename=_required_text(descriptor.filename, "filename"),
        contract=_required_text(descriptor.contract, "contract"),
        loader_module=_required_text(descriptor.loader_module, "loader_module"),
        loader_name=_required_text(descriptor.loader_name, "loader_name"),
        workspace_manifest_kind=descriptor.workspace_manifest_kind,
        package_role=descriptor.package_role,
        semantic_package_family=_required_text(
            descriptor.semantic_package_family,
            "semantic_package_family",
        ),
        semantic_package_kind=_required_text(
            descriptor.semantic_package_kind,
            "semantic_package_kind",
        ),
        semantic_projection_name=_required_text(
            descriptor.semantic_projection_name,
            "semantic_projection_name",
        ),
        semantic_root_kind=_required_text(
            descriptor.semantic_root_kind,
            "semantic_root_kind",
        ),
        code_package_surface_by_package_kind=tuple(sorted(surface_by_kind.items())),
    )


def object_config_graph_package_manifest_resolution_descriptor() -> (
    ModuleSemanticManifestResolutionDescriptor
):
    matches = tuple(
        descriptor
        for descriptor in META_MANIFEST_RESOLUTION
        if descriptor.manifest_kind == "aware_toml"
        and descriptor.semantic_package_kind == "object_config_graph_package"
        and descriptor.semantic_projection_name == "ObjectConfigGraphPackage"
    )
    if len(matches) != 1:
        raise RuntimeError(
            "Meta semantic contract must declare exactly one "
            "ObjectConfigGraphPackage aware_toml manifest-resolution descriptor"
        )
    return matches[0]


def load_object_config_graph_package_manifest(*, toml_path: str | Path) -> AwareTomlSpec:
    return load_aware_toml_spec(toml_path=toml_path)


def load_object_config_graph_package_manifest_from_text(
    *,
    toml_text: str,
    toml_path: str | Path | None = None,
) -> AwareTomlSpec:
    return load_aware_toml_spec_from_text(toml_text=toml_text, toml_path=toml_path)


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Meta OCG manifest contract is missing {field_name}")
    return value.strip()


OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_CONTRACT = (
    object_config_graph_package_manifest_contract()
)
OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND = (
    OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_CONTRACT.manifest_kind
)
OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_FILENAME = (
    OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_CONTRACT.filename
)
OBJECT_CONFIG_GRAPH_PACKAGE_SEMANTIC_KIND = (
    OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_CONTRACT.semantic_package_kind
)
OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME = (
    OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_CONTRACT.semantic_projection_name
)


__all__ = [
    "OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_CONTRACT",
    "OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_FILENAME",
    "OBJECT_CONFIG_GRAPH_PACKAGE_MANIFEST_KIND",
    "OBJECT_CONFIG_GRAPH_PACKAGE_PROJECTION_NAME",
    "OBJECT_CONFIG_GRAPH_PACKAGE_SEMANTIC_KIND",
    "ObjectConfigGraphPackageManifestContract",
    "load_object_config_graph_package_manifest",
    "load_object_config_graph_package_manifest_from_text",
    "object_config_graph_package_manifest_contract",
    "object_config_graph_package_manifest_resolution_descriptor",
]
