from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticPackageRoleDescriptor,
)
from aware_code.semantic_capability import SEMANTIC_ANALYSIS_CAPABILITY
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor
from aware_node.semantic_scope import NODE_SEMANTIC_SCOPE_KEY


NODE_PROVIDER_OWNER = "aware_node.provider"
NODE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE = (NODE_PROVIDER_OWNER,)
NODE_MATERIALIZATION_OWNER_SEQUENCE = (NODE_PROVIDER_OWNER,)
NODE_SEMANTIC_SCOPE_KEYS = (NODE_SEMANTIC_SCOPE_KEY,)
NODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("node-ontology",)
NODE_RUNTIME_CLOSURE_PRODUCER_KEY = "aware_node.node.runtime_closure"
NODE_RUNTIME_CLOSURE_OUTPUT_KEY = "node_runtime_closure"
NODE_RUNTIME_CLOSURE_ARTIFACT_FAMILY = "node_runtime_closure"
NODE_RUNTIME_CLOSURE_ARTIFACT_ROLE = "deployment_runtime_closure"
NODE_RUNTIME_CLOSURE_CONTRACT_VERSION = "aware.node.runtime_closure.v1"
NODE_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "NodePackage",
    "NodeConfig",
    "CodePackage",
)

NODE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in NODE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

NODE_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in NODE_MATERIALIZATION_OWNER_SEQUENCE
)

NODE_CAPABILITY_PARTICIPATION = (
    *NODE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION,
    *NODE_MATERIALIZATION_CAPABILITY_PARTICIPATION,
)

NODE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_name="_node_semantic_analysis_provider",
        priority=700,
    )
    for semantic_owner in NODE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

NODE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_node.materialization.workspace_provider",
        callable_name="materialize",
        priority=700,
    )
    for semantic_owner in NODE_MATERIALIZATION_OWNER_SEQUENCE
)

NODE_CAPABILITY_EXECUTION_POLICY = (
    *NODE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY,
    *NODE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
)

NODE_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role="aware_node.provider",
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            SEMANTIC_ANALYSIS_CAPABILITY,
            SEMANTIC_MATERIALIZATION_CAPABILITY,
        ),
        owns_manifest_kinds=("aware_node_toml",),
    ),
)

NODE_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=NODE_PROVIDER_OWNER,
        manifest_kind="aware_node_toml",
        filename="aware.node.toml",
        contract="aware.node",
        loader_module="aware_node.manifest.loader",
        loader_name="load_aware_node_toml_spec",
        workspace_manifest_kind="node",
        package_role=NODE_PROVIDER_OWNER,
        semantic_package_family="node",
        semantic_package_kind="node_package",
        semantic_projection_name="NodePackage",
        semantic_root_kind="node_config",
        code_package_surface="runtime",
        workspace_materialization_order=700,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        semantic_package_metadata={
            "dependency_attribute_name": "dependencies",
        },
        priority=700,
    ),
)

NODE_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=NODE_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            NODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="NodePackage",
        required_projection_names=NODE_MATERIALIZATION_REQUIRED_PROJECTIONS,
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=700,
    ),
)

_NODE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT = (
    "Meta-owned Node Workspace semantic materialization runtime context"
)

NODE_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=NODE_PROVIDER_OWNER,
        callable_module="aware_meta.runtime.graph_context",
        callable_name="build_meta_workspace_materialization_runtime_context",
        required=True,
        priority=700,
        provider_payload={
            "contract": _NODE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT,
            "runtime_ontology_package_names": (
                NODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

NODE_MATERIALIZATION_ARTIFACT_OUTPUTS = (
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=NODE_PROVIDER_OWNER,
        producer_provider_key="aware_node",
        producer_key=NODE_RUNTIME_CLOSURE_PRODUCER_KEY,
        output_key=NODE_RUNTIME_CLOSURE_OUTPUT_KEY,
        artifact_family=NODE_RUNTIME_CLOSURE_ARTIFACT_FAMILY,
        artifact_role=NODE_RUNTIME_CLOSURE_ARTIFACT_ROLE,
        output_kind="materialization_detail",
        media_type="application/json",
        runtime_contract_version=NODE_RUNTIME_CLOSURE_CONTRACT_VERSION,
        required_for=(
            "workspace_revision",
            "deployment",
            "node_run_manifest",
        ),
        provider_payload={
            "contract": (
                "Node-owned runtime closure emitted from committed NodePackage/"
                "NodeConfig semantic materialization truth."
            ),
        },
    ),
)

AWARE_NODE_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_node",
    semantic_scope_keys=NODE_SEMANTIC_SCOPE_KEYS,
    capability_participation=NODE_CAPABILITY_PARTICIPATION,
    capability_execution_policy=NODE_CAPABILITY_EXECUTION_POLICY,
    package_roles=NODE_PACKAGE_ROLES,
    manifest_resolution=NODE_MANIFEST_RESOLUTION,
    materialization_artifact_outputs=NODE_MATERIALIZATION_ARTIFACT_OUTPUTS,
    materialization_runtime=NODE_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=NODE_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_NODE_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "AWARE_NODE_SEMANTIC_CONTRACT",
    "NODE_CAPABILITY_EXECUTION_POLICY",
    "NODE_CAPABILITY_PARTICIPATION",
    "NODE_MANIFEST_RESOLUTION",
    "NODE_MATERIALIZATION_ARTIFACT_OUTPUTS",
    "NODE_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "NODE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "NODE_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "NODE_MATERIALIZATION_RUNTIME",
    "NODE_MATERIALIZATION_RUNTIME_CONTEXT",
    "NODE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "NODE_MATERIALIZATION_OWNER_SEQUENCE",
    "NODE_PACKAGE_ROLES",
    "NODE_PROVIDER_OWNER",
    "NODE_RUNTIME_CLOSURE_ARTIFACT_FAMILY",
    "NODE_RUNTIME_CLOSURE_ARTIFACT_ROLE",
    "NODE_RUNTIME_CLOSURE_CONTRACT_VERSION",
    "NODE_RUNTIME_CLOSURE_OUTPUT_KEY",
    "NODE_RUNTIME_CLOSURE_PRODUCER_KEY",
    "NODE_SEMANTIC_SCOPE_KEYS",
    "NODE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY",
    "NODE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION",
    "NODE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE",
]
