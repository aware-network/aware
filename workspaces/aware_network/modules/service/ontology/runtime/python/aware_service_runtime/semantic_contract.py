from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticArtifactLeafOwnershipDescriptor,
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationExecutionContextDescriptor,
    ModuleSemanticMaterializationPackageOutputDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticPackageLayoutDescriptor,
    ModuleSemanticPackageRoleDescriptor,
    ModuleSemanticRuntimeProjectionPackageDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
    ModuleSemanticWorkflowDescriptor,
    ModuleSemanticWorkflowInstructionDescriptor,
)
from aware_code.semantic_capability import SEMANTIC_ANALYSIS_CAPABILITY
from aware_code.semantic_materialization import (
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
)
from aware_code.semantic_package.schemas import (
    CapabilityBundleDescriptor,
    CapabilityParticipationDescriptor,
    CapabilityProfileDescriptor,
)
from aware_service_runtime.semantic_constants import SERVICE_SEMANTIC_SCOPE_KEY


SERVICE_PROVIDER_OWNER = "aware_service.provider"
SERVICE_ROOT_OWNER = "aware_service.service"
SERVICE_API_OWNER = "aware_service.api"
SERVICE_EXPERIENCE_OWNER = "aware_service.experience"
SERVICE_PROJECTION_OWNER = "aware_service.projection"
SERVICE_OPERATION_OWNER = "aware_service.operation"
SERVICE_ENDPOINT_OWNER = "aware_service.endpoint"
SERVICE_OWNED_OCG_PACKAGE_PRODUCER_KEY = (
    "aware_service.owned_object_config_graph_package"
)
SERVICE_OWNED_OCG_PACKAGE_OUTPUT_KEY = "object_config_graph_package_manifest"
SERVICE_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY = (
    "aware_meta.object_config_graph_package_manifest"
)
SERVICE_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION = (
    "aware.meta.object_config_graph_package_manifest.v1"
)
SERVICE_SEMANTIC_SCOPE_KEYS = (SERVICE_SEMANTIC_SCOPE_KEY,)

SERVICE_DIAGNOSTICS_OWNER_SEQUENCE = (
    SERVICE_ROOT_OWNER,
    SERVICE_API_OWNER,
    SERVICE_EXPERIENCE_OWNER,
    SERVICE_PROJECTION_OWNER,
    SERVICE_OPERATION_OWNER,
    SERVICE_ENDPOINT_OWNER,
)

SERVICE_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    SERVICE_ROOT_OWNER,
    SERVICE_API_OWNER,
    SERVICE_EXPERIENCE_OWNER,
    SERVICE_PROJECTION_OWNER,
    SERVICE_OPERATION_OWNER,
    SERVICE_ENDPOINT_OWNER,
)

SERVICE_MATERIALIZATION_OWNER_SEQUENCE = (SERVICE_PROVIDER_OWNER,)
SERVICE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE = (SERVICE_ROOT_OWNER,)
SERVICE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("service-ontology",)
SERVICE_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "Service",
    "ServiceConfig",
    "ServicePackage",
    "ApiPackage",
    "CodePackage",
    "CodePackageConfig",
)

SERVICE_MATERIALIZATION_DELTA_ADAPTER_METADATA: dict[str, object] = {
    "callable_module": "aware_service_runtime.materialization.workspace_provider",
    "callable_name": SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    "request_contract_version": (
        "aware.workspace.semantic-materialization.provider-delta-request.v1"
    ),
    "result_contract_version": (
        "aware.workspace.semantic-materialization.provider-delta-result.v1"
    ),
}
SERVICE_MATERIALIZATION_CAPABILITY_METADATA: dict[str, object] = {
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: (
        SERVICE_MATERIALIZATION_DELTA_ADAPTER_METADATA
    ),
}

SERVICE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SERVICE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

SERVICE_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        metadata=SERVICE_MATERIALIZATION_CAPABILITY_METADATA,
    )
    for semantic_owner in SERVICE_MATERIALIZATION_OWNER_SEQUENCE
)

SERVICE_DIAGNOSTICS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SERVICE_DIAGNOSTICS_OWNER_SEQUENCE
)

SERVICE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in SERVICE_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

SERVICE_CAPABILITY_PARTICIPATION = (
    *SERVICE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION,
    *SERVICE_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    *SERVICE_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    *SERVICE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)

_SERVICE_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER = {
    SERVICE_ROOT_OWNER: 110,
}

_SERVICE_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER = {
    SERVICE_ROOT_OWNER: "_service_semantic_analysis_provider",
}

_SERVICE_DIAGNOSTICS_PRIORITY_BY_OWNER = {
    SERVICE_ROOT_OWNER: 120,
    SERVICE_API_OWNER: 121,
    SERVICE_EXPERIENCE_OWNER: 122,
    SERVICE_PROJECTION_OWNER: 123,
    SERVICE_OPERATION_OWNER: 124,
    SERVICE_ENDPOINT_OWNER: 125,
}

_SERVICE_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER = {
    SERVICE_ROOT_OWNER: "_service_root_diagnostics_provider",
    SERVICE_API_OWNER: "_service_api_diagnostics_provider",
    SERVICE_EXPERIENCE_OWNER: "_service_experience_diagnostics_provider",
    SERVICE_PROJECTION_OWNER: "_service_projection_diagnostics_provider",
    SERVICE_OPERATION_OWNER: "_service_operation_diagnostics_provider",
    SERVICE_ENDPOINT_OWNER: "_service_endpoint_diagnostics_provider",
}

_SERVICE_SEMANTIC_TOKENS_PRIORITY_BY_OWNER = {
    SERVICE_ROOT_OWNER: 150,
    SERVICE_API_OWNER: 151,
    SERVICE_EXPERIENCE_OWNER: 152,
    SERVICE_PROJECTION_OWNER: 153,
    SERVICE_OPERATION_OWNER: 154,
    SERVICE_ENDPOINT_OWNER: 155,
}

_SERVICE_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER = {
    SERVICE_ROOT_OWNER: "_service_root_tokens_provider",
    SERVICE_API_OWNER: "_service_api_tokens_provider",
    SERVICE_EXPERIENCE_OWNER: "_service_experience_tokens_provider",
    SERVICE_PROJECTION_OWNER: "_service_projection_tokens_provider",
    SERVICE_OPERATION_OWNER: "_service_operation_tokens_provider",
    SERVICE_ENDPOINT_OWNER: "_service_endpoint_tokens_provider",
}

SERVICE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
        callable_name=_SERVICE_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=SERVICE_SEMANTIC_SCOPE_KEYS,
        priority=_SERVICE_DIAGNOSTICS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in SERVICE_DIAGNOSTICS_OWNER_SEQUENCE
)

SERVICE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
        callable_name=_SERVICE_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        priority=_SERVICE_SEMANTIC_TOKENS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in SERVICE_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

SERVICE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_name=_SERVICE_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=SERVICE_SEMANTIC_SCOPE_KEYS,
        priority=_SERVICE_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in SERVICE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

SERVICE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_service_runtime.materialization.workspace_provider",
        callable_name="materialize",
        priority=300,
    )
    for semantic_owner in SERVICE_MATERIALIZATION_OWNER_SEQUENCE
)

SERVICE_CAPABILITY_EXECUTION_POLICY = (
    *SERVICE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY,
    *SERVICE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    *SERVICE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY,
    *SERVICE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY,
)

_SERVICE_PROFILE_OWNERS = (
    ("module.aware_service.service", (SERVICE_ROOT_OWNER,)),
    ("module.aware_service.api", (SERVICE_API_OWNER,)),
    ("module.aware_service.experience", (SERVICE_EXPERIENCE_OWNER,)),
    ("module.aware_service.projection", (SERVICE_PROJECTION_OWNER,)),
    ("module.aware_service.operation", (SERVICE_OPERATION_OWNER,)),
    ("module.aware_service.endpoint", (SERVICE_ENDPOINT_OWNER,)),
)

SERVICE_DIAGNOSTICS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _SERVICE_PROFILE_OWNERS
)

SERVICE_SEMANTIC_TOKENS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _SERVICE_PROFILE_OWNERS
)

SERVICE_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_service",
        semantic_owners=SERVICE_DIAGNOSTICS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *SERVICE_DIAGNOSTICS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_service",
        semantic_owners=SERVICE_SEMANTIC_TOKENS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    *SERVICE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

SERVICE_CAPABILITY_BUNDLES = (
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.authoring",
        profile_names=("module.aware_service",),
    ),
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.projection",
        profile_names=("module.aware_service.projection",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.authoring",
        profile_names=("module.aware_service",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.projection",
        profile_names=("module.aware_service.projection",),
    ),
)

SERVICE_SYNTAX_LANES = (
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_service.service",
        semantic_owner=SERVICE_ROOT_OWNER,
        compiler_owner=SERVICE_ROOT_OWNER,
        grammar_rules=("service_def",),
        semantic_token_types=("keyword", "class"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_service.api",
        semantic_owner=SERVICE_API_OWNER,
        compiler_owner=SERVICE_API_OWNER,
        grammar_rules=("service_api_decl",),
        semantic_token_types=("keyword", "type"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_service.experience",
        semantic_owner=SERVICE_EXPERIENCE_OWNER,
        compiler_owner=SERVICE_EXPERIENCE_OWNER,
        grammar_rules=("service_experience_decl",),
        semantic_token_types=("keyword", "type"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_service.projection",
        semantic_owner=SERVICE_PROJECTION_OWNER,
        compiler_owner=SERVICE_PROJECTION_OWNER,
        grammar_rules=("service_api_projection_decl",),
        semantic_token_types=("keyword", "type"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_service.operation",
        semantic_owner=SERVICE_OPERATION_OWNER,
        compiler_owner=SERVICE_OPERATION_OWNER,
        grammar_rules=(
            "service_operation_def",
            "service_operation_settlement_decl",
            "service_operation_price_def",
        ),
        semantic_token_types=("keyword", "function"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_service.endpoint",
        semantic_owner=SERVICE_ENDPOINT_OWNER,
        compiler_owner=SERVICE_ENDPOINT_OWNER,
        grammar_rules=("service_operation_endpoint_def",),
        semantic_token_types=("keyword", "type", "function"),
    ),
)

SERVICE_PACKAGE_ROLES = (
    ModuleSemanticPackageRoleDescriptor(
        role="aware_service.provider",
        contract="aware.semantic_provider",
        package_kind="runtime",
        capabilities=(
            SEMANTIC_ANALYSIS_CAPABILITY,
            "diagnostics",
            "semantic_tokens",
            SEMANTIC_MATERIALIZATION_CAPABILITY,
        ),
        owns_manifest_kinds=("aware_service_toml",),
    ),
)

SERVICE_MANIFEST_RESOLUTION = (
    ModuleSemanticManifestResolutionDescriptor(
        semantic_owner=SERVICE_PROVIDER_OWNER,
        manifest_kind="aware_service_toml",
        filename="aware.service.toml",
        contract="aware.service",
        loader_module="aware_service_runtime.manifest.loader",
        loader_name="load_aware_service_toml_spec",
        workspace_manifest_kind="service",
        package_role=SERVICE_PROVIDER_OWNER,
        semantic_package_family="service",
        semantic_package_kind="service_package",
        semantic_projection_name="ServicePackage",
        semantic_root_kind="service_config",
        code_package_surface="service",
        workspace_materialization_order=300,
        workspace_materialization_branch="semantic",
        workspace_materialization_commit=True,
        workspace_materialization_primary=True,
        copy_code_package_metadata_keys=("fqn_prefix", "package_kind"),
        semantic_package_metadata={
            "dependency_attribute_name": "dependencies",
            "metadata_resolver_module": (
                "aware_service_runtime.semantic_manifest_metadata"
            ),
            "metadata_resolver_name": (
                "resolve_service_manifest_semantic_package_metadata"
            ),
        },
        priority=300,
    ),
)

SERVICE_ARTIFACT_LEAF_OWNERSHIP = (
    ModuleSemanticArtifactLeafOwnershipDescriptor(
        semantic_owner=SERVICE_PROVIDER_OWNER,
        owner_manifest_kinds=("aware_service_toml",),
        artifact_manifest_kinds=("pyproject_toml",),
        callable_module="aware_service_runtime.semantic_artifact_ownership",
        callable_name="resolve_workspace_semantic_artifact_leaf_ownership",
        priority=100,
        ownership_role="service_implementation_package",
    ),
)

SERVICE_PACKAGE_LAYOUT = (
    ModuleSemanticPackageLayoutDescriptor(
        semantic_owner=SERVICE_PROVIDER_OWNER,
        manifest_kinds=("aware_service_toml",),
        callable_module="aware_service_runtime.semantic_package_layout",
        callable_name="resolve_service_python_package_layout",
        priority=100,
    ),
)

SERVICE_MATERIALIZATION_PACKAGE_OUTPUTS = (
    ModuleSemanticMaterializationPackageOutputDescriptor(
        semantic_owner=SERVICE_PROVIDER_OWNER,
        producer_key=SERVICE_OWNED_OCG_PACKAGE_PRODUCER_KEY,
        output_key=SERVICE_OWNED_OCG_PACKAGE_OUTPUT_KEY,
        target_provider_key="aware_meta",
        target_semantic_owner="aware_meta.object_config_graph",
        target_input_key=SERVICE_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY,
        target_package_family="meta",
        target_semantic_kind="object_config_graph_package",
        input_artifact_family="aware_toml_manifest",
        target_code_package_manifest_kind="aware_toml",
        target_code_package_surface="structure",
        runtime_contract_version=(SERVICE_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION),
        required_for=("workspace.semantic_materialization",),
        priority=300,
        provider_payload={
            "source": "service owned object_config_graph_packages",
            "schema_version": 1,
        },
    ),
)

SERVICE_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=SERVICE_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            SERVICE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="ServicePackage",
        required_projection_names=SERVICE_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=(
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="service-ontology",
                projection_names=("Service", "ServiceConfig", "ServicePackage"),
            ),
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="api-ontology",
                projection_names=("ApiPackage",),
            ),
            ModuleSemanticRuntimeProjectionPackageDescriptor(
                package_name="code-ontology",
                projection_names=("CodePackage", "CodePackageConfig"),
            ),
        ),
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=300,
    ),
)

_SERVICE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT = (
    "Meta-owned Service Workspace semantic materialization runtime context"
)

SERVICE_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=SERVICE_PROVIDER_OWNER,
        callable_module="aware_meta.runtime.graph_context",
        callable_name="build_meta_workspace_materialization_runtime_context",
        required=True,
        priority=300,
        provider_payload={
            "contract": _SERVICE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT,
            "runtime_ontology_package_names": (
                SERVICE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

SERVICE_MATERIALIZATION_EXECUTION_CONTEXT = (
    ModuleSemanticMaterializationExecutionContextDescriptor(
        semantic_owner=SERVICE_PROVIDER_OWNER,
        context_key="api_reference_branch_ids_by_api_name",
        callable_module="aware_service_runtime.workspace_context",
        callable_name="resolve_service_api_reference_branch_ids_by_api_name",
        required=False,
        priority=300,
        provider_payload={
            "dependency_workspace_manifest_kind": "api",
            "dependency_projection_name": "ApiPackage",
            "contract": (
                "Service materialization preseed for committed API reference "
                "branch ids."
            ),
        },
    ),
)

SERVICE_SEMANTIC_WORKFLOWS = (
    ModuleSemanticWorkflowDescriptor(
        workflow_key="external-api-service.service",
        semantic_owner=SERVICE_PROVIDER_OWNER,
        description=("Service package side of external API-Service Workspace genesis."),
        stage_keys=(
            "workspace.genesis.understand",
            "workspace.genesis.plan",
            "semantic.service.materialize",
            "semantic.service.verify",
        ),
        instructions=(
            ModuleSemanticWorkflowInstructionDescriptor(
                instruction_key="external-api-service.service.authoring",
                title="Bind Service operations to API protocol",
                body=(
                    "Use the Service semantic contract to author Service "
                    "operations after the API protocol artifact is present, "
                    "preserving operation-to-endpoint graph-binding evidence."
                ),
                stage_keys=(
                    "workspace.genesis.plan",
                    "semantic.service.materialize",
                    "semantic.service.verify",
                ),
                source_refs=(
                    "workspaces/aware_network/modules/service/ontology/runtime/python/aware_service_runtime/semantic_contract.py",
                    "aware.service.toml",
                ),
            ),
        ),
        capability_refs=(
            SEMANTIC_ANALYSIS_CAPABILITY,
            SEMANTIC_MATERIALIZATION_CAPABILITY,
            "diagnostics",
            "semantic_tokens",
        ),
        capability_profile_refs=(
            "module.aware_service",
            "module.aware_service.projection",
        ),
        grammar_profile_refs=("workspace.code.grammar_profile.semantic_contracts",),
        source_meaning_refs=("aware_service.semantic_source_meaning",),
        ontology_feature_refs=(
            "aware_service.ServiceConfig",
            "aware_service.ServiceOperationConfig",
            "aware_service.ServiceOperationConfigApiEndpoint",
            "aware_api.ApiCapabilityEndpoint",
        ),
        graph_binding_refs=(
            "aware_service.service_def",
            "aware_service.service_operation_def",
            "aware_service.service_operation_endpoint_def",
        ),
        expected_artifact_refs=(
            "aware.service.toml",
            "api_service_protocol",
        ),
        expected_proof_refs=(
            "api_service_protocol.hash",
            "workspace.semantic_materialization.receipt",
            "meta.function_call.proof",
        ),
        expected_receipt_refs=(
            "workspace.semantic_materialization",
            "code.semantic_contract.describe",
        ),
        diagnostic_refs=(
            "code.grammar_profile.resolve",
            "meta.semantic_diagnostics",
        ),
        priority=300,
    ),
)

AWARE_SERVICE_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_service",
    semantic_scope_keys=SERVICE_SEMANTIC_SCOPE_KEYS,
    capability_participation=SERVICE_CAPABILITY_PARTICIPATION,
    capability_execution_policy=SERVICE_CAPABILITY_EXECUTION_POLICY,
    capability_profiles=SERVICE_CAPABILITY_PROFILES,
    capability_bundles=SERVICE_CAPABILITY_BUNDLES,
    syntax_lanes=SERVICE_SYNTAX_LANES,
    package_roles=SERVICE_PACKAGE_ROLES,
    semantic_workflows=SERVICE_SEMANTIC_WORKFLOWS,
    manifest_resolution=SERVICE_MANIFEST_RESOLUTION,
    artifact_leaf_ownership=SERVICE_ARTIFACT_LEAF_OWNERSHIP,
    package_layout=SERVICE_PACKAGE_LAYOUT,
    materialization_package_outputs=SERVICE_MATERIALIZATION_PACKAGE_OUTPUTS,
    materialization_runtime=SERVICE_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=SERVICE_MATERIALIZATION_RUNTIME_CONTEXT,
    materialization_execution_context=SERVICE_MATERIALIZATION_EXECUTION_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_SERVICE_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_SERVICE_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "SERVICE_API_OWNER",
    "SERVICE_ARTIFACT_LEAF_OWNERSHIP",
    "SERVICE_CAPABILITY_PARTICIPATION",
    "SERVICE_CAPABILITY_BUNDLES",
    "SERVICE_CAPABILITY_EXECUTION_POLICY",
    "SERVICE_CAPABILITY_PROFILES",
    "SERVICE_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "SERVICE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY",
    "SERVICE_DIAGNOSTICS_CAPABILITY_PROFILES",
    "SERVICE_DIAGNOSTICS_OWNER_SEQUENCE",
    "SERVICE_ENDPOINT_OWNER",
    "SERVICE_EXPERIENCE_OWNER",
    "SERVICE_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "SERVICE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "SERVICE_MATERIALIZATION_PACKAGE_OUTPUTS",
    "SERVICE_MANIFEST_RESOLUTION",
    "SERVICE_PACKAGE_LAYOUT",
    "SERVICE_MATERIALIZATION_CAPABILITY_METADATA",
    "SERVICE_MATERIALIZATION_DELTA_ADAPTER_METADATA",
    "SERVICE_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "SERVICE_MATERIALIZATION_RUNTIME",
    "SERVICE_MATERIALIZATION_RUNTIME_CONTEXT",
    "SERVICE_MATERIALIZATION_EXECUTION_CONTEXT",
    "SERVICE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "SERVICE_MATERIALIZATION_OWNER_SEQUENCE",
    "SERVICE_OPERATION_OWNER",
    "SERVICE_PACKAGE_ROLES",
    "SERVICE_PROJECTION_OWNER",
    "SERVICE_PROVIDER_OWNER",
    "SERVICE_OWNED_OCG_PACKAGE_OUTPUT_KEY",
    "SERVICE_OWNED_OCG_PACKAGE_PRODUCER_KEY",
    "SERVICE_OWNED_OCG_PACKAGE_RUNTIME_CONTRACT_VERSION",
    "SERVICE_OWNED_OCG_PACKAGE_TARGET_INPUT_KEY",
    "SERVICE_ROOT_OWNER",
    "SERVICE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION",
    "SERVICE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY",
    "SERVICE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE",
    "SERVICE_SEMANTIC_SCOPE_KEYS",
    "SERVICE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "SERVICE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY",
    "SERVICE_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "SERVICE_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "SERVICE_SEMANTIC_WORKFLOWS",
    "SERVICE_SYNTAX_LANES",
]
