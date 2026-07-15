from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
)


@dataclass(frozen=True, slots=True)
class SemanticManifestResolution:
    """One semantic-contract-owned manifest resolution."""

    manifest_path: Path
    descriptor: ModuleSemanticManifestResolutionDescriptor
    manifest: object


def matching_manifest_resolution_descriptors(
    *,
    manifest_path: Path,
    contracts: Iterable[ModuleSemanticContract],
    manifest_kind: str | None = None,
    workspace_manifest_kind: str | None = None,
) -> tuple[ModuleSemanticManifestResolutionDescriptor, ...]:
    """Return semantic-contract descriptors that can resolve a manifest path."""

    filename = manifest_path.name
    descriptors: list[ModuleSemanticManifestResolutionDescriptor] = []
    for contract in contracts:
        descriptors.extend(
            contract.manifest_resolution_for(
                manifest_kind=manifest_kind,
                filename=filename,
                workspace_manifest_kind=workspace_manifest_kind,
            )
        )
    return tuple(
        sorted(
            descriptors,
            key=lambda item: (
                item.priority,
                item.semantic_owner,
                item.manifest_kind,
                item.filename,
            ),
        )
    )


def load_semantic_manifest(
    *,
    manifest_path: Path,
    descriptor: ModuleSemanticManifestResolutionDescriptor,
) -> object:
    """Load a manifest through the owning semantic package facade."""

    module = import_module(descriptor.loader_module)
    loader = getattr(module, descriptor.loader_name)
    return loader(toml_path=manifest_path)


def resolve_semantic_manifest(
    *,
    manifest_path: Path,
    contracts: Iterable[ModuleSemanticContract],
    manifest_kind: str | None = None,
    workspace_manifest_kind: str | None = None,
) -> SemanticManifestResolution:
    """Resolve and load a manifest through semantic contract ownership."""

    descriptors = matching_manifest_resolution_descriptors(
        manifest_path=manifest_path,
        contracts=contracts,
        manifest_kind=manifest_kind,
        workspace_manifest_kind=workspace_manifest_kind,
    )
    if not descriptors:
        raise LookupError(
            "No semantic contract manifest resolver matched "
            f"{manifest_path.as_posix()!r}"
        )
    descriptor = descriptors[0]
    return SemanticManifestResolution(
        manifest_path=manifest_path,
        descriptor=descriptor,
        manifest=load_semantic_manifest(
            manifest_path=manifest_path,
            descriptor=descriptor,
        ),
    )


__all__ = [
    "SemanticManifestResolution",
    "load_semantic_manifest",
    "matching_manifest_resolution_descriptors",
    "resolve_semantic_manifest",
]
