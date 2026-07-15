"""Top-level manifest schema combining OCG, overlays, OPG, and GraphSQL metadata."""

# @doc-ref: ../../../docs/manifest.md
# @test-ref: ../../../tests/test_manifest_schema.py

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .graphsql_manifest import GraphSQLManifest
from .ocg_manifest import OCGSnapshotManifest
from .opg_manifest import OPGIndexManifest
from .overlay_manifest import OverlayManifest
from .program_registry import ProgramRegistryEntry


class ManifestArtifact(BaseModel):
    file: str
    hash: str


__all__ = [
    "EnvironmentManifest",
    "EnvironmentDescriptor",
    "EnvironmentServiceProviderPackageRef",
    "FunctionImplPolicyManifest",
    "ManifestArtifact",
]


class EnvironmentDescriptor(BaseModel):
    """Environment descriptor stored in the manifest."""

    id: str = Field(..., description="Environment UUID")
    title: str | None = Field(default=None, description="Human readable title")
    canonical_language: str = Field(
        ..., description="Canonical language for the environment"
    )


class FunctionImplPolicyManifest(BaseModel):
    """FunctionImpl runtime authority policy emitted into runtime manifests."""

    ownership: str = Field(
        default="authored",
        description=(
            "FunctionImpl authority owner for this module bundle. "
            "`compiler` means .aware FunctionImpl is runtime authority; "
            "`authored` means rendered Python handlers remain authority."
        ),
    )
    parity_policy: str = Field(
        default="off",
        description="FunctionImpl parity gate emitted at compile/materialization time.",
    )

    @field_validator("ownership")
    @classmethod
    def _validate_ownership(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"authored", "compiler"}:
            raise ValueError(
                "function_impl_policy.ownership must be one of: authored, compiler"
            )
        return normalized

    @field_validator("parity_policy")
    @classmethod
    def _validate_parity_policy(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"off", "warn", "error"}:
            raise ValueError(
                "function_impl_policy.parity_policy must be one of: off, warn, error"
            )
        return normalized


class EnvironmentServiceProviderPackageRef(BaseModel):
    """Deployable language package satisfying one service provider import."""

    provider_module: str = Field(
        ...,
        description="Python module import path that exposes provider registrations.",
    )
    surface: str = Field(
        default="environment",
        description="Service surface the provider belongs to.",
    )
    language: str = Field(
        default="python",
        description="Language runtime that owns this provider package.",
    )
    package_name: str = Field(
        ...,
        description="Language package/distribution name to install in execution closure.",
    )
    import_root: str | None = Field(
        default=None,
        description="Top-level import root for the provider package.",
    )
    package_root: str = Field(
        ...,
        description="WorkspaceRevision-relative package root containing the language package.",
    )
    manifest_path: str = Field(
        ...,
        description="WorkspaceRevision-relative language package manifest path.",
    )
    authority: str = Field(
        default="compatibility_module_environment_service",
        description=(
            "Authority for this package ref. Compatibility module services are "
            "transitional until ServicePackage/CodePackage artifact refs own this."
        ),
    )
    module_id: str | None = Field(
        default=None,
        description="Module id that declared this provider, for audit/debugging.",
    )
    service_package_id: str | None = Field(
        default=None,
        description="Committed ServicePackage id when this ref is ServicePackage-backed.",
    )
    source_code_package_id: str | None = Field(
        default=None,
        description="Committed source CodePackage id when available.",
    )
    source_commit_id: str | None = Field(
        default=None,
        description="Pinned source package commit id when available.",
    )


class EnvironmentManifest(BaseModel):
    """Complete environment manifest definition."""

    version: str = Field(..., description="Manifest schema version")
    built_at: datetime = Field(..., description="Timestamp when manifest was generated")
    environment: EnvironmentDescriptor = Field(
        ..., description="Environment descriptor"
    )
    ocg: OCGSnapshotManifest = Field(..., description="OCG snapshot metadata")
    ocg_binding_snapshot: ManifestArtifact = Field(
        ...,
        description="ClassConfig-only binding snapshot (msgpack) used for OCG→ORM binding",
    )
    overlays: dict[str, OverlayManifest] = Field(
        default_factory=dict, description="Overlay payloads"
    )
    opg_index: OPGIndexManifest = Field(..., description="OPG index metadata")
    graphsql: GraphSQLManifest | None = Field(
        default=None, description="GraphSQL plan metadata"
    )
    projection_plans: ManifestArtifact | None = Field(
        default=None,
        description="ProjectionPlan bundle metadata (OIG → SQL index materialization plans)",
    )
    bindings: ManifestArtifact | None = Field(
        default=None, description="Canonical-to-runtime binding manifest metadata"
    )
    handlers: ManifestArtifact | None = Field(
        default=None,
        description="Runtime handler manifest metadata (FunctionConfig → handler callable mapping)",
    )
    relationship_strategies: ManifestArtifact | None = Field(
        default=None, description="Relationship strategy manifest metadata"
    )
    plan_registry: ManifestArtifact | None = Field(
        default=None, description="GraphSQL plan descriptor registry metadata"
    )
    fixtures: dict[str, list[str]] | None = Field(
        default=None,
        description="Optional bootstrap fixtures grouped by type",
    )
    loader: dict[str, object] | None = Field(
        default=None,
        description="Loader hints (skip_database, hydrate caches, fallback paths)",
    )
    environment_service_provider_modules: list[str] | None = Field(
        default=None,
        description=(
            "Optional environment-service provider module import paths. "
            "Used by the ENVIRONMENT app surface to mount module-owned service adapters."
        ),
    )
    environment_service_provider_package_refs: (
        list[EnvironmentServiceProviderPackageRef] | None
    ) = Field(
        default=None,
        description=(
            "Optional deployable package refs satisfying environment-service "
            "provider imports. Deployment closures consume this artifact instead "
            "of rediscovering source layout."
        ),
    )
    function_impl_policy: FunctionImplPolicyManifest | None = Field(
        default=None,
        description=(
            "Optional module FunctionImpl runtime authority policy. "
            "When omitted, consumers must treat the module as authored/handler-first."
        ),
    )
    program_registry: list[ProgramRegistryEntry] | None = Field(
        default=None,
        description="Optional program-ref registry for deterministic `apply_program_ref` resolution.",
    )
    program_identity_registry: ManifestArtifact | None = Field(
        default=None,
        description=(
            "Optional program identity-contract artifact metadata "
            "(constructor identity keys and projection-branch identity contracts)."
        ),
    )
