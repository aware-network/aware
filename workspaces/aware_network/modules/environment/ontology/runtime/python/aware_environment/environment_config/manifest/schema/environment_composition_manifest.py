"""Environment composition manifest schema (v1 direction).

This manifest declares an EnvironmentConfig as a composition of semantic package
bundles. `modules` remains a compatibility mirror while producers migrate to
package/ontology selectors.

The ENVIRONMENT service/runtime uses it to:
- load multiple module `environment.manifest.json` files,
- build a composite runtime index (OCG/OPG/handlers),
- boot a union DB schema (when enabled).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .environment_manifest import (
    EnvironmentDescriptor,
    EnvironmentServiceProviderPackageRef,
    FunctionImplPolicyManifest,
    ManifestArtifact,
)
from .program_registry import ProgramRegistryEntry


class EnvironmentCompositionModule(BaseModel):
    """Single module bundle entry inside a composed EnvironmentConfig."""

    module_id: str | None = Field(
        default=None,
        description="Optional module identifier (for debugging/audit only).",
    )
    manifest_path: str = Field(
        ...,
        description=(
            "Path to the module bundle manifest (environment.manifest.json). "
            "Relative paths are resolved against the bundle root (parent of the nearest `.aware` directory)."
        ),
    )
    package_name: str | None = Field(
        default=None,
        description="Canonical semantic package name for the package bundle.",
    )
    fqn_prefix: str | None = Field(
        default=None,
        description="Canonical FQN prefix owned by the package bundle.",
    )
    package_root: str | None = Field(
        default=None,
        description="Workspace-relative package root for this composition entry.",
    )
    source_manifest_path: str | None = Field(
        default=None,
        description="Workspace-relative package aware.toml used as source manifest.",
    )
    ontology_manifest_path: str | None = Field(
        default=None,
        description=(
            "Workspace-relative aware.ontology.toml selector that owns this package, "
            "when one can be resolved."
        ),
    )
    environment_service_provider_modules: list[str] | None = Field(
        default=None,
        description=(
            "Optional environment-service provider modules for this module entry. "
            "Used by ENVIRONMENT service hosts to mount module-owned service adapters."
        ),
    )
    environment_service_provider_package_refs: (
        list[EnvironmentServiceProviderPackageRef] | None
    ) = Field(
        default=None,
        description=(
            "Optional deployable package refs satisfying this module entry's "
            "environment-service provider modules."
        ),
    )
    function_impl_policy: FunctionImplPolicyManifest | None = Field(
        default=None,
        description=(
            "FunctionImpl runtime authority policy for this module entry. "
            "Runtime bootstrap must consume manifest policy rather than rediscovering source TOML."
        ),
    )


class EnvironmentCompositionPackage(BaseModel):
    """Single semantic package bundle entry inside a composed EnvironmentConfig."""

    package_name: str = Field(
        ...,
        description="Canonical semantic package name for the package bundle.",
    )
    fqn_prefix: str = Field(
        ...,
        description="Canonical FQN prefix owned by the package bundle.",
    )
    manifest_path: str = Field(
        ...,
        description="Workspace-relative environment.manifest.json for this package.",
    )
    package_root: str = Field(
        ...,
        description="Workspace-relative package root for this composition entry.",
    )
    source_manifest_path: str = Field(
        ...,
        description="Workspace-relative package aware.toml used as source manifest.",
    )
    ontology_manifest_path: str | None = Field(
        default=None,
        description=(
            "Workspace-relative aware.ontology.toml selector that owns this package, "
            "when one can be resolved."
        ),
    )
    compatibility_module_id: str | None = Field(
        default=None,
        description="Optional compatibility module identifier for older module consumers.",
    )
    environment_service_provider_modules: list[str] | None = Field(
        default=None,
        description="Compatibility environment-service provider modules for this package.",
    )
    environment_service_provider_package_refs: (
        list[EnvironmentServiceProviderPackageRef] | None
    ) = Field(
        default=None,
        description="Deployable package refs satisfying this package's providers.",
    )
    function_impl_policy: FunctionImplPolicyManifest | None = Field(
        default=None,
        description="FunctionImpl runtime authority policy for this package.",
    )


class EnvironmentCompositionManifest(BaseModel):
    """Top-level composition manifest definition."""

    version: str = Field(..., description="Manifest schema version")
    built_at: datetime = Field(
        ..., description="Timestamp when the manifest was generated"
    )
    environment: EnvironmentDescriptor = Field(
        ..., description="Composed environment descriptor"
    )
    ocg_hash: str = Field(
        ...,
        description=(
            "Pinned hash for this composed environment config (used for DB boot fail-fast). "
            "This is the environment-config version hash (e.g. `sha256:<...>`)."
        ),
    )
    db_schema_hash: str | None = Field(
        default=None,
        description=(
            "Optional DB schema hash for migration/install gating. "
            "When present, runtime DB boot policy should compare marker state against this value "
            "instead of `ocg_hash`."
        ),
    )
    modules: list[EnvironmentCompositionModule] = Field(
        default_factory=list,
        description="Compatibility ordered list of module manifests to load.",
    )
    packages: list[EnvironmentCompositionPackage] = Field(
        default_factory=list,
        description="Canonical ordered list of semantic package manifests to load.",
    )
    base_environment_manifest_paths: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of base EnvironmentConfig composition manifests to layer below "
            "this consumer environment. Runtime resolves base modules first, then this "
            "environment's modules. Minimal base-kernel trimming is a producer artifact "
            "boundary, not implied by this field."
        ),
    )
    environment_service_provider_modules: list[str] | None = Field(
        default=None,
        description=(
            "Optional aggregated environment-service provider modules for the composed "
            "environment (deduplicated union of module entries)."
        ),
    )
    environment_service_provider_package_refs: (
        list[EnvironmentServiceProviderPackageRef] | None
    ) = Field(
        default=None,
        description=(
            "Optional aggregated deployable package refs satisfying the composed "
            "environment-service providers. Deployment closures consume these "
            "refs as runtime artifact truth."
        ),
    )

    loader: dict[str, object] | None = Field(
        default=None,
        description="Optional loader hints (rare; module manifests usually own loader imports).",
    )
    program_registry: list[ProgramRegistryEntry] | None = Field(
        default=None,
        description=(
            "Optional aggregated program registry for deterministic `apply_program_ref` "
            "resolution without runtime filesystem scans."
        ),
    )
    program_identity_registry: ManifestArtifact | None = Field(
        default=None,
        description=(
            "Optional aggregated program identity-contract artifact metadata "
            "used for deterministic Type.id and bind identity resolution."
        ),
    )


__all__ = [
    "EnvironmentCompositionManifest",
    "EnvironmentCompositionModule",
    "EnvironmentCompositionPackage",
]
