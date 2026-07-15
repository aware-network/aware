from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
)
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor


ECONOMY_PROVIDER_OWNER = "aware_economy.provider"
ECONOMY_MATERIALIZATION_OWNER_SEQUENCE = (ECONOMY_PROVIDER_OWNER,)
ECONOMY_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("economy-ontology",)
ECONOMY_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "EconomyPackage",
    "CodePackage",
    "Price",
    "PricingPolicy",
)

ECONOMY_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in ECONOMY_MATERIALIZATION_OWNER_SEQUENCE
)

ECONOMY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_economy.materialization.workspace_provider",
        callable_name="materialize",
        priority=800,
    )
    for semantic_owner in ECONOMY_MATERIALIZATION_OWNER_SEQUENCE
)

ECONOMY_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role="aware_economy.provider",
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(SEMANTIC_MATERIALIZATION_CAPABILITY,),
        owns_manifest_kinds=("aware_economy_toml",),
    ),
)

ECONOMY_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=ECONOMY_PROVIDER_OWNER,
        manifest_kind="aware_economy_toml",
        filename="aware.economy.toml",
        contract="aware.economy",
        loader_module="aware_economy.manifest.loader",
        loader_name="load_aware_economy_toml_spec",
        workspace_manifest_kind="economy",
        package_role=ECONOMY_PROVIDER_OWNER,
        semantic_package_family="economy",
        semantic_package_kind="economy_package",
        semantic_projection_name="EconomyPackage",
        semantic_root_kind="economy_package",
        code_package_surface="economy",
        workspace_materialization_order=800,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        priority=800,
    ),
)

ECONOMY_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=ECONOMY_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            ECONOMY_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="EconomyPackage",
        required_projection_names=ECONOMY_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="economy-ontology",
                projection_names=(
                    "EconomyPackage",
                    "Price",
                    "PricingPolicy",
                ),
            ),
        ),
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=800,
    ),
)

ECONOMY_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=ECONOMY_PROVIDER_OWNER,
        callable_module="aware_meta.runtime.graph_context",
        callable_name="build_meta_workspace_materialization_runtime_context",
        required=True,
        priority=800,
        provider_payload={
            "contract": (
                "Economy-owned Workspace semantic materialization runtime context"
            ),
            "runtime_ontology_package_names": (
                ECONOMY_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

AWARE_ECONOMY_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_economy",
    capability_participation=ECONOMY_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    capability_execution_policy=ECONOMY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    package_roles=ECONOMY_PACKAGE_ROLES,
    manifest_resolution=ECONOMY_MANIFEST_RESOLUTION,
    materialization_runtime=ECONOMY_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=ECONOMY_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_ECONOMY_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_ECONOMY_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "ECONOMY_MANIFEST_RESOLUTION",
    "ECONOMY_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "ECONOMY_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "ECONOMY_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "ECONOMY_MATERIALIZATION_RUNTIME",
    "ECONOMY_MATERIALIZATION_RUNTIME_CONTEXT",
    "ECONOMY_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "ECONOMY_MATERIALIZATION_OWNER_SEQUENCE",
    "ECONOMY_PACKAGE_ROLES",
    "ECONOMY_PROVIDER_OWNER",
]
