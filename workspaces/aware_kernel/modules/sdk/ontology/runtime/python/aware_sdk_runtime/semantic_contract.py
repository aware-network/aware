from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationPackageOutputDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
)
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor


SDK_ONTOLOGY_PACKAGE_ROLE = "aware_sdk.ontology"
SDK_PROVIDER_PACKAGE_ROLE = "aware_sdk.provider"
SDK_CONFIG_OWNER = "aware_sdk.sdk_config"
SDK_API_OWNER = "aware_sdk.api"
SDK_OPERATION_OWNER = "aware_sdk.operation"
SDK_ENDPOINT_OWNER = "aware_sdk.endpoint"
SDK_OWNED_OCG_PACKAGE_PRODUCER_KEY = "aware_sdk.owned_object_config_graph_package"
SDK_OWNED_OCG_PACKAGE_OUTPUT_KEY = "object_config_graph_package_manifest"
SDK_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY = (
    "aware_meta.object_config_graph_package_manifest"
)
SDK_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION = (
    "aware.meta.object_config_graph_package_manifest.v1"
)
SDK_PUBLIC_PACKAGE_TARGET_METADATA_RESOLVER = {
    "metadata_resolver_module": "aware_sdk_runtime.semantic_package",
    "metadata_resolver_name": "sdk_semantic_package_metadata",
}

SDK_MATERIALIZATION_OWNER_SEQUENCE = (SDK_PROVIDER_PACKAGE_ROLE,)

SDK_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SDK_MATERIALIZATION_OWNER_SEQUENCE
)

SDK_CAPABILITY_PARTICIPATION = (*SDK_MATERIALIZATION_CAPABILITY_PARTICIPATION,)

SDK_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_sdk_runtime.materialization.workspace_provider",
        callable_name="materialize",
        priority=250,
    )
    for semantic_owner in SDK_MATERIALIZATION_OWNER_SEQUENCE
)

SDK_CAPABILITY_EXECUTION_POLICY = (*SDK_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,)

SDK_MATERIALIZATION_PACKAGE_OUTPUTS = (
    ModuleSemanticMaterializationPackageOutputDescriptor(
        semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
        producer_key=SDK_OWNED_OCG_PACKAGE_PRODUCER_KEY,
        output_key=SDK_OWNED_OCG_PACKAGE_OUTPUT_KEY,
        target_provider_key="aware_meta",
        target_semantic_owner="aware_meta.object_config_graph",
        target_input_key=SDK_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY,
        target_package_family="meta",
        target_semantic_kind="object_config_graph_package",
        input_artifact_family="aware_toml_manifest",
        target_code_package_manifest_kind="aware_toml",
        target_code_package_surface="structure",
        runtime_contract_version=SDK_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION,
        required_for=("workspace.semantic_materialization",),
        priority=250,
        provider_payload={
            "source": "sdk owned object_config_graph_packages",
            "schema_version": 1,
        },
    ),
)

SDK_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role=SDK_ONTOLOGY_PACKAGE_ROLE,
        contract="aware.ontology",
        package_kind="ontology",
    ),
    ModuleSemanticPackageRoleDescriptor(
        role=SDK_PROVIDER_PACKAGE_ROLE,
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=("semantic_tokens", SEMANTIC_MATERIALIZATION_CAPABILITY),
        owns_manifest_kinds=("aware_sdk_toml",),
    ),
)

SDK_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
        manifest_kind="aware_sdk_toml",
        filename="aware.sdk.toml",
        contract="aware.sdk",
        loader_module="aware_sdk_runtime.manifest.loader",
        loader_name="load_aware_sdk_toml_spec",
        workspace_manifest_kind="sdk",
        package_role=SDK_PROVIDER_PACKAGE_ROLE,
        semantic_package_family="sdk",
        semantic_package_kind="sdk_package",
        semantic_projection_name="SdkPackage",
        semantic_root_kind="sdk_config",
        code_package_surface="sdk",
        workspace_materialization_order=250,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        semantic_package_metadata=SDK_PUBLIC_PACKAGE_TARGET_METADATA_RESOLVER,
        priority=250,
    ),
)

SDK_SYNTAX_LANES = (
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_sdk.sdk_config",
        semantic_owner=SDK_CONFIG_OWNER,
        compiler_owner=SDK_CONFIG_OWNER,
        grammar_rules=("sdk_def",),
        semantic_token_types=("keyword", "class"),
        semantic_token_modifiers=("sdk",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_sdk.api",
        semantic_owner=SDK_API_OWNER,
        compiler_owner=SDK_API_OWNER,
        grammar_rules=("sdk_api_decl",),
        semantic_token_types=("keyword", "namespace"),
        semantic_token_modifiers=("sdk",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_sdk.operation",
        semantic_owner=SDK_OPERATION_OWNER,
        compiler_owner=SDK_OPERATION_OWNER,
        grammar_rules=("sdk_operation_def",),
        semantic_token_types=("keyword", "function"),
        semantic_token_modifiers=("sdk",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_sdk.endpoint",
        semantic_owner=SDK_ENDPOINT_OWNER,
        compiler_owner=SDK_ENDPOINT_OWNER,
        grammar_rules=("sdk_operation_endpoint_def",),
        semantic_token_types=("keyword", "function"),
        semantic_token_modifiers=("sdk",),
    ),
)

SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("sdk-ontology",)

SDK_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "SdkPackage",
    "Api",
    "ApiPackage",
    "CodePackage",
)

SDK_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
        runtime_ontology_package_names=(
            SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="SdkPackage",
        required_projection_names=SDK_MATERIALIZATION_REQUIRED_PROJECTIONS,
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=250,
    ),
)

_SDK_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT = (
    "Meta-owned SDK Workspace semantic materialization runtime context"
)

SDK_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=SDK_PROVIDER_PACKAGE_ROLE,
        callable_module="aware_sdk_runtime.materialization.runtime_context",
        callable_name="build_sdk_workspace_materialization_runtime_context",
        required=True,
        priority=250,
        provider_payload={
            "contract": _SDK_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT,
            "runtime_ontology_package_names": (
                SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

AWARE_SDK_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_sdk",
    capability_participation=SDK_CAPABILITY_PARTICIPATION,
    capability_execution_policy=SDK_CAPABILITY_EXECUTION_POLICY,
    syntax_lanes=SDK_SYNTAX_LANES,
    package_roles=SDK_PACKAGE_ROLES,
    manifest_resolution=SDK_MANIFEST_RESOLUTION,
    materialization_package_outputs=SDK_MATERIALIZATION_PACKAGE_OUTPUTS,
    materialization_runtime=SDK_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=SDK_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_SDK_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "AWARE_SDK_SEMANTIC_CONTRACT",
    "SDK_API_OWNER",
    "SDK_CAPABILITY_EXECUTION_POLICY",
    "SDK_CAPABILITY_PARTICIPATION",
    "SDK_CONFIG_OWNER",
    "SDK_ENDPOINT_OWNER",
    "SDK_MANIFEST_RESOLUTION",
    "SDK_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "SDK_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "SDK_MATERIALIZATION_PACKAGE_OUTPUTS",
    "SDK_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "SDK_MATERIALIZATION_RUNTIME",
    "SDK_MATERIALIZATION_RUNTIME_CONTEXT",
    "SDK_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "SDK_MATERIALIZATION_OWNER_SEQUENCE",
    "SDK_ONTOLOGY_PACKAGE_ROLE",
    "SDK_OPERATION_OWNER",
    "SDK_OWNED_OCG_PACKAGE_OUTPUT_KEY",
    "SDK_OWNED_OCG_PACKAGE_PRODUCER_KEY",
    "SDK_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION",
    "SDK_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY",
    "SDK_PACKAGE_ROLES",
    "SDK_PROVIDER_PACKAGE_ROLE",
    "SDK_PUBLIC_PACKAGE_TARGET_METADATA_RESOLVER",
    "SDK_SYNTAX_LANES",
]
