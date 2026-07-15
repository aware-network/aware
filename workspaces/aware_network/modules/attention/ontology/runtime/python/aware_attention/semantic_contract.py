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


ATTENTION_PROVIDER_OWNER = "aware_attention.provider"
ATTENTION_MATERIALIZATION_OWNER_SEQUENCE = (ATTENTION_PROVIDER_OWNER,)
ATTENTION_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("attention-ontology",)
ATTENTION_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "AttentionPackage",
    "LayoutConfig",
    "Layout",
    "LayoutSection",
    "Section",
    "CodePackage",
)

ATTENTION_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in ATTENTION_MATERIALIZATION_OWNER_SEQUENCE
)

ATTENTION_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_attention.materialization.workspace_provider",
        callable_name="materialize",
        priority=400,
    )
    for semantic_owner in ATTENTION_MATERIALIZATION_OWNER_SEQUENCE
)

ATTENTION_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role="aware_attention.provider",
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(SEMANTIC_MATERIALIZATION_CAPABILITY,),
        owns_manifest_kinds=("aware_attention_toml",),
    ),
)

ATTENTION_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=ATTENTION_PROVIDER_OWNER,
        manifest_kind="aware_attention_toml",
        filename="aware.attention.toml",
        contract="aware.attention",
        loader_module="aware_attention.manifest.loader",
        loader_name="load_aware_attention_toml_spec",
        workspace_manifest_kind="attention",
        package_role=ATTENTION_PROVIDER_OWNER,
        semantic_package_family="attention",
        semantic_package_kind="attention_package",
        semantic_projection_name="AttentionPackage",
        semantic_root_kind="attention_package",
        code_package_surface="runtime",
        workspace_materialization_order=400,
        workspace_materialization_branch="none",
        workspace_materialization_commit=False,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        priority=400,
    ),
)

ATTENTION_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=ATTENTION_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            ATTENTION_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="AttentionPackage",
        required_projection_names=ATTENTION_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="attention-ontology",
                projection_names=(
                    "AttentionPackage",
                    "LayoutConfig",
                    "Layout",
                    "LayoutSection",
                    "Section",
                ),
            ),
        ),
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=400,
    ),
)

ATTENTION_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=ATTENTION_PROVIDER_OWNER,
        callable_module="aware_meta.runtime.graph_context",
        callable_name="build_meta_workspace_materialization_runtime_context",
        required=True,
        priority=400,
        provider_payload={
            "contract": "Attention-owned Workspace semantic materialization runtime context",
            "runtime_ontology_package_names": (
                ATTENTION_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

AWARE_ATTENTION_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_attention",
    capability_participation=ATTENTION_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    capability_execution_policy=ATTENTION_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    package_roles=ATTENTION_PACKAGE_ROLES,
    manifest_resolution=ATTENTION_MANIFEST_RESOLUTION,
    materialization_runtime=ATTENTION_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=ATTENTION_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_ATTENTION_SEMANTIC_CONTRACT


__all__ = [
    "ATTENTION_PACKAGE_ROLES",
    "AWARE_ATTENTION_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "ATTENTION_MANIFEST_RESOLUTION",
    "ATTENTION_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "ATTENTION_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "ATTENTION_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "ATTENTION_MATERIALIZATION_RUNTIME",
    "ATTENTION_MATERIALIZATION_RUNTIME_CONTEXT",
    "ATTENTION_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "ATTENTION_MATERIALIZATION_OWNER_SEQUENCE",
    "ATTENTION_PROVIDER_OWNER",
]
