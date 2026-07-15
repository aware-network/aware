from __future__ import annotations

from pydantic import BaseModel, Field


class CapabilityParticipationDescriptor(BaseModel):
    """Default capability-owner participation exported by a semantic package."""

    capability: str
    semantic_owner: str
    default_enabled: bool = True
    metadata: dict[str, object] = Field(default_factory=dict)


class CapabilityProfileDescriptor(BaseModel):
    """Named capability-owner bundle exported by a semantic package."""

    capability: str
    name: str
    semantic_owners: tuple[str, ...]
    default_selected: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


class CapabilityBundleDescriptor(BaseModel):
    """Higher-order capability bundle exported by a semantic package."""

    capability: str
    name: str
    profile_names: tuple[str, ...]
    metadata: dict[str, object] = Field(default_factory=dict)


class SemanticPackageDescriptor(BaseModel):
    """Shared semantic leaf provenance descriptor for a discovered code package."""

    provider_key: str
    family: str
    semantic_kind: str
    package_name: str | None = None
    manifest_relative_path: str | None = None
    provenance_field_name: str = "source_code_package"
    metadata: dict[str, object] = Field(default_factory=dict)
    semantic_scope_keys: tuple[str, ...] = ()
    capability_participation: tuple[CapabilityParticipationDescriptor, ...] = ()
    capability_profiles: tuple[CapabilityProfileDescriptor, ...] = ()
    capability_bundles: tuple[CapabilityBundleDescriptor, ...] = ()


__all__ = [
    "CapabilityBundleDescriptor",
    "CapabilityParticipationDescriptor",
    "CapabilityProfileDescriptor",
    "SemanticPackageDescriptor",
]
