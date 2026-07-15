from __future__ import annotations

from aware_api_runtime.semantic_scope import API_SEMANTIC_SCOPE_KEY
from aware_code.module_semantic_contract import (
    ModuleSemanticArtifactLeafOwnershipDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationInputDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticMaterializationToolingDescriptor,
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticSyntaxLaneDescriptor,
    ModuleSemanticWorkflowDescriptor,
    ModuleSemanticWorkflowInstructionDescriptor,
)
from aware_code.semantic_capability import SEMANTIC_ANALYSIS_CAPABILITY
from aware_code.semantic_materialization import (
    SEMANTIC_FUNCTION_CALL_CONTEXT_KEY,
    SEMANTIC_MATERIALIZATION_CAPABILITY,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY,
    SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY,
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY,
    SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY,
    SEMANTIC_PROVIDER_DELTA_PREVIOUS_EVIDENCE_RESOLVER_KEY,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY,
)
from aware_code.semantic_currentness import (
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_ENTRYPOINT,
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY,
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION,
)
from aware_code.semantic_package.schemas import (
    CapabilityBundleDescriptor,
    CapabilityParticipationDescriptor,
    CapabilityProfileDescriptor,
)
from aware_api_runtime.semantic_function_refs import (
    API_SEMANTIC_FUNCTION_CALL_BINDING_REFS,
    API_SEMANTIC_FUNCTION_REFS,
    API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
    API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION,
    API_SEMANTIC_OPERATION_TYPES,
)
from aware_api_runtime.semantic_registry import (
    API_MANIFEST_RESOLUTION,
    API_PACKAGE_ROLES,
    API_PROVIDER_OWNER,
    API_RUNTIME_PROJECTION_PACKAGES,
)


API_API_OWNER = "aware_api.api"
API_CAPABILITY_OWNER = "aware_api.capability"
API_GRAPH_OWNER = "aware_api.graph"
API_PROJECTION_OWNER = "aware_api.projection"

API_SEMANTIC_SCOPE_KEYS = (API_SEMANTIC_SCOPE_KEY,)

API_DIAGNOSTICS_OWNER_SEQUENCE = (
    API_API_OWNER,
    API_PROJECTION_OWNER,
)

API_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    API_API_OWNER,
    API_CAPABILITY_OWNER,
    API_GRAPH_OWNER,
    API_PROJECTION_OWNER,
)

API_SEMANTIC_ANALYSIS_OWNER_SEQUENCE = (API_API_OWNER,)
API_MATERIALIZATION_OWNER_SEQUENCE = (API_PROVIDER_OWNER,)

API_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in API_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

API_PROVIDER_DELTA_READY_OPERATIONS: tuple[dict[str, object], ...] = tuple(
    {
        "case_key": case_key,
        "provider_operation_type": provider_operation_type,
        "ontology_subject_kind": ontology_subject_kind,
        "operation_family": operation_family,
        "mutable_fields": mutable_fields,
        "source_projection_policy": "public_graph_only_ready",
        "workspace_delta_first_mode": "public_graph_only_ready",
        "workspace_delta_first_ready": True,
    }
    for (
        case_key,
        provider_operation_type,
        ontology_subject_kind,
        operation_family,
        mutable_fields,
    ) in (
        (
            "aware_api.api.create",
            "aware_api.api.create",
            "api",
            "create",
            (),
        ),
        (
            "aware_api.api_capability.create",
            "aware_api.api_capability.create",
            "api_capability",
            "create",
            (),
        ),
        (
            "aware_api.api_capability_endpoint.create",
            "aware_api.api_capability_endpoint.create",
            "api_capability_endpoint",
            "create",
            (),
        ),
        (
            "aware_api.api_capability_endpoint.description.update",
            "aware_api.api_capability_endpoint.update",
            "api_capability_endpoint",
            "update",
            ("description",),
        ),
    )
)
API_PROVIDER_DELTA_BLOCKED_OPERATIONS: tuple[dict[str, object], ...] = (
    {
        "case_key": "aware_api.api.update",
        "provider_operation_type": "aware_api.api.update",
        "ontology_subject_kind": "api",
        "operation_family": "update",
        "workspace_delta_first_ready": False,
        "blocked_reason": "api_update_executor_not_ready",
    },
    {
        "case_key": "aware_api.api_capability.update",
        "provider_operation_type": "aware_api.api_capability.update",
        "ontology_subject_kind": "api_capability",
        "operation_family": "update",
        "workspace_delta_first_ready": False,
        "blocked_reason": "api_capability_update_executor_not_ready",
    },
    {
        "case_key": "aware_api.api_capability_endpoint.identity_or_request_contract.update",
        "provider_operation_type": "aware_api.api_capability_endpoint.update",
        "ontology_subject_kind": "api_capability_endpoint",
        "operation_family": "update",
        "blocked_fields": ("name", "request_class_config_id"),
        "workspace_delta_first_ready": False,
        "blocked_reason": "api_endpoint_non_description_update_executor_not_ready",
    },
    {
        "case_key": "aware_api.api_semantic_object.delete",
        "provider_operation_type": "aware_api.api_semantic_object.delete",
        "ontology_subject_kind": "api_semantic_object",
        "operation_family": "delete",
        "source_projection_policy": "explicit_fallback_required",
        "workspace_delta_first_mode": "explicit_fallback_required",
        "workspace_delta_first_ready": False,
        "blocked_reason": "api_provider_delta_delete_executor_not_ready",
    },
)
API_PROVIDER_DELTA_PRODUCT_READINESS: dict[str, object] = {
    "readiness_kind": "aware_api.api_provider_delta_product_readiness",
    "contract_version": SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_CONTRACT_VERSION,
    "provider_contract_version": "aware.api.provider-delta.typed-operation.v1",
    "provider_key": "aware_api",
    "status": "ready",
    "reason": "api_provider_delta_create_and_endpoint_description_update_ready",
    "default_policy": "ready_operations_only",
    "fallback_policy": "explicit_fallback_required",
    "operation_count": (
        len(API_PROVIDER_DELTA_READY_OPERATIONS)
        + len(API_PROVIDER_DELTA_BLOCKED_OPERATIONS)
    ),
    "ready_operation_count": len(API_PROVIDER_DELTA_READY_OPERATIONS),
    "render_all_required_operation_count": 0,
    "blocked_operation_count": len(API_PROVIDER_DELTA_BLOCKED_OPERATIONS),
    "workspace_delta_first_default_policy": ("public_lifecycle_ready_operations_only"),
    "workspace_delta_first_ready_operation_count": len(
        API_PROVIDER_DELTA_READY_OPERATIONS
    ),
    "workspace_delta_first_mode_counts": {"public_graph_only_ready": 4},
    "workspace_delta_first_ready_operations": API_PROVIDER_DELTA_READY_OPERATIONS,
    "ready_operations": API_PROVIDER_DELTA_READY_OPERATIONS,
    "render_all_required_operations": (),
    "blocked_operations": API_PROVIDER_DELTA_BLOCKED_OPERATIONS,
}

API_MATERIALIZATION_DELTA_ADAPTER_METADATA: dict[str, object] = {
    "callable_module": "aware_api_runtime.workspace_provider",
    "callable_name": SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_ENTRYPOINT,
    "request_contract_version": (
        "aware.workspace.semantic-materialization.provider-delta-request.v1"
    ),
    "result_contract_version": (
        "aware.workspace.semantic-materialization.provider-delta-result.v1"
    ),
    SEMANTIC_PROVIDER_DELTA_FUNCTIONAL_MATERIALIZATION_KEY: True,
    SEMANTIC_PROVIDER_DELTA_PRODUCT_READINESS_KEY: (
        API_PROVIDER_DELTA_PRODUCT_READINESS
    ),
    SEMANTIC_PROVIDER_DELTA_OPERATION_EXECUTION_PROJECTION_NAME_KEY: "Api",
    SEMANTIC_PROVIDER_DELTA_PREVIOUS_EVIDENCE_RESOLVER_KEY: {
        "callable_module": "aware_api_runtime.workspace_provider",
        "callable_name": (
            "resolve_api_provider_delta_previous_materialization_evidence"
        ),
        "request_type": "SemanticProviderDeltaPreviousEvidenceResolverRequest",
        "result_type": "SemanticProviderDeltaPreviousEvidenceResolverResult",
        "required": False,
        "provider_payload": {
            "contract": (
                "API provider-delta previous full-rebuild receipt evidence " "resolver"
            ),
            "source": "aware_api.semantic_contract",
        },
    },
    SEMANTIC_PROVIDER_DELTA_EXECUTION_CONTEXT_RESOLVERS_KEY: (
        {
            "context_key": SEMANTIC_FUNCTION_CALL_CONTEXT_KEY,
            "callable_module": ("aware_api_runtime.workspace_provider"),
            "callable_name": ("build_api_provider_delta_function_call_context"),
            "required": False,
            "provider_payload": {
                "contract": (
                    "API provider-delta function-call argument resolution " "context"
                ),
            },
        },
    ),
}
API_MATERIALIZATION_CAPABILITY_METADATA: dict[str, object] = {
    SEMANTIC_MATERIALIZATION_DELTA_ADAPTER_METADATA_KEY: (
        API_MATERIALIZATION_DELTA_ADAPTER_METADATA
    ),
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY: {
        "callable_module": "aware_api_runtime.workspace_provider",
        "callable_name": (
            SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_ENTRYPOINT
        ),
        "contract_version": (
            SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION
        ),
    },
}

API_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        metadata=API_MATERIALIZATION_CAPABILITY_METADATA,
    )
    for semantic_owner in API_MATERIALIZATION_OWNER_SEQUENCE
)

API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA: dict[
    str,
    object,
] = {
    "contract_version": (
        API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
    ),
    "callable_module": "aware_api_runtime.semantic_functions.resolution",
    "callable_name": "resolve_api_semantic_function_call_plan_previews",
    "supported_semantic_operation_types": API_SEMANTIC_OPERATION_TYPES,
    "semantic_operation_type_refs": API_SEMANTIC_OPERATION_TYPES,
    "function_call_binding_refs": API_SEMANTIC_FUNCTION_CALL_BINDING_REFS,
    "ontology_function_refs": tuple(sorted(API_SEMANTIC_FUNCTION_REFS)),
    "semantic_apply_boundary": "ontology_function_call",
    "mutates": False,
    "execution_status": "not_requested",
    "provider_contract": (
        "API owns API-domain semantic operation vocabulary and FunctionCall "
        "bindings. Code owns source/grammar evidence; Meta owns the ontology "
        "FunctionCall execution boundary consumed by Workspace."
    ),
}
API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability=API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
        semantic_owner=API_PROVIDER_OWNER,
        metadata=(API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA),
    ),
)

API_DIAGNOSTICS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in API_DIAGNOSTICS_OWNER_SEQUENCE
)

API_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in API_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

API_CAPABILITY_PARTICIPATION = (
    *API_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION,
    *API_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    *API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
    *API_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    *API_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)

_API_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER = {
    API_API_OWNER: 20,
}

_API_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER = {
    API_API_OWNER: "_api_semantic_analysis_provider",
}

_API_DIAGNOSTICS_PRIORITY_BY_OWNER = {
    API_API_OWNER: 30,
    API_PROJECTION_OWNER: 35,
}

_API_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER = {
    API_API_OWNER: "_api_root_diagnostics_provider",
    API_PROJECTION_OWNER: "_api_projection_diagnostics_provider",
}

_API_SEMANTIC_TOKENS_PRIORITY_BY_OWNER = {
    API_API_OWNER: 50,
    API_CAPABILITY_OWNER: 51,
    API_GRAPH_OWNER: 52,
    API_PROJECTION_OWNER: 53,
}

_API_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER = {
    API_API_OWNER: "_api_tokens_provider",
    API_CAPABILITY_OWNER: "_api_capability_tokens_provider",
    API_GRAPH_OWNER: "_api_graph_tokens_provider",
    API_PROJECTION_OWNER: "_api_projection_tokens_provider",
}

API_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
        callable_name=_API_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=API_SEMANTIC_SCOPE_KEYS,
        priority=_API_DIAGNOSTICS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in API_DIAGNOSTICS_OWNER_SEQUENCE
)

API_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
        callable_name=_API_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        priority=_API_SEMANTIC_TOKENS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in API_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

API_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_name=_API_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=API_SEMANTIC_SCOPE_KEYS,
        priority=_API_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in API_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

API_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_api_runtime.workspace_provider",
        callable_name="materialize",
        priority=100,
    )
    for semantic_owner in API_MATERIALIZATION_OWNER_SEQUENCE
)

API_CAPABILITY_EXECUTION_POLICY = (
    *API_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY,
    *API_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    *API_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY,
    *API_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY,
)

API_SEMANTIC_ANALYSIS_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        name="module.aware_api.surface",
        semantic_owners=(API_API_OWNER,),
    ),
)

API_DIAGNOSTICS_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_api.surface",
        semantic_owners=(API_API_OWNER,),
    ),
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_api.contracts",
        semantic_owners=(API_PROJECTION_OWNER,),
    ),
)

API_SEMANTIC_TOKENS_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_api.surface",
        semantic_owners=(
            API_API_OWNER,
            API_CAPABILITY_OWNER,
            API_GRAPH_OWNER,
        ),
    ),
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_api.contracts",
        semantic_owners=(API_PROJECTION_OWNER,),
    ),
)

API_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        name="module.aware_api",
        semantic_owners=(API_API_OWNER,),
        default_selected=True,
    ),
    *API_SEMANTIC_ANALYSIS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_api",
        semantic_owners=(
            API_API_OWNER,
            API_PROJECTION_OWNER,
        ),
        default_selected=True,
    ),
    *API_DIAGNOSTICS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_api",
        semantic_owners=(
            API_API_OWNER,
            API_CAPABILITY_OWNER,
            API_GRAPH_OWNER,
            API_PROJECTION_OWNER,
        ),
        default_selected=True,
    ),
    *API_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

API_CAPABILITY_BUNDLES = (
    CapabilityBundleDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        name="bundle.authoring",
        profile_names=("module.aware_api",),
    ),
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.authoring",
        profile_names=("module.aware_api",),
    ),
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.projection",
        profile_names=("module.aware_api.contracts",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.authoring",
        profile_names=("module.aware_api",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.projection",
        profile_names=("module.aware_api.contracts",),
    ),
)

API_SYNTAX_LANES = (
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_api.api",
        semantic_owner=API_API_OWNER,
        compiler_owner=API_API_OWNER,
        grammar_rules=("api_def",),
        semantic_token_types=("keyword", "class"),
        semantic_token_modifiers=("api",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_api.capability",
        semantic_owner=API_CAPABILITY_OWNER,
        compiler_owner=API_CAPABILITY_OWNER,
        grammar_rules=(
            "api_capability_def",
            "api_capability_endpoint_def",
            "api_capability_endpoint_response_def",
            "api_capability_endpoint_stream_def",
            "api_capability_endpoint_stream_event_def",
        ),
        semantic_token_types=(
            "keyword",
            "class",
            "function",
            "type",
            "enumMember",
        ),
        semantic_token_modifiers=("api",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_api.graph",
        semantic_owner=API_GRAPH_OWNER,
        compiler_owner=API_GRAPH_OWNER,
        grammar_rules=(
            "api_graph_def",
            "api_graph_capability_def",
            "api_graph_capability_function_def",
        ),
        semantic_token_types=("keyword", "type", "class", "function"),
        semantic_token_modifiers=("api",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_api.projection",
        semantic_owner=API_PROJECTION_OWNER,
        compiler_owner=API_PROJECTION_OWNER,
        grammar_rules=(
            "api_graph_projection_def",
            "api_graph_projection_binding_def",
            "api_projection_anchor",
        ),
        semantic_token_types=("keyword", "type", "property"),
        semantic_token_modifiers=("api",),
    ),
)

API_ARTIFACT_LEAF_OWNERSHIP = (
    ModuleSemanticArtifactLeafOwnershipDescriptor(
        semantic_owner=API_PROVIDER_OWNER,
        owner_manifest_kinds=("aware_api_toml",),
        artifact_manifest_kinds=("pyproject_toml", "setup_py", "pubspec_yaml"),
        callable_module="aware_api_runtime.semantic_artifact_ownership",
        callable_name="resolve_workspace_semantic_artifact_leaf_ownership",
        priority=100,
    ),
)

API_MATERIALIZATION_ARTIFACT_OUTPUTS = (
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=API_PROVIDER_OWNER,
        producer_key="aware_api.product_runtime",
        output_key="api.product_runtime_file",
        artifact_family="api_product_runtime",
        artifact_role="runtime_file",
        output_kind="file",
        runtime_contract_version="aware.api.product_runtime.v1",
        artifact_scope_policy="replace_missing",
        required_for=("workspace_revision", "api_service_protocol"),
        media_type="application/octet-stream",
        provider_payload={
            "contract": "api product runtime files required by service protocol activation"
        },
    ),
)

API_MATERIALIZATION_TOOLING = (
    ModuleSemanticMaterializationToolingDescriptor(
        semantic_owner=API_PROVIDER_OWNER,
        tooling_key="api.dart_target",
        languages=("dart",),
        required_for=("workspace.semantic_materialization",),
        manifest_presence_path=("targets", "dart"),
        provider_payload={
            "contract": (
                "API manifests with a Dart target require Dart tooling context."
            ),
        },
        priority=100,
    ),
)

API_MATERIALIZATION_INPUTS = (
    ModuleSemanticMaterializationInputDescriptor(
        semantic_owner=API_PROVIDER_OWNER,
        input_key="aware_api.compile_plan",
        input_kind="compile_plan",
        artifact_family="api_compile_plan",
        artifact_role="compile_plan",
        package_family="api",
        semantic_kind="api_package",
        runtime_contract_version="aware.api.compile_plan.v1",
        callable_module="aware_api_runtime.workspace_provider",
        callable_name="materialize",
        required=True,
        priority=100,
        provider_payload={
            "schema_version": 9,
            "contract": "API compile-plan input accepted for generated API packages",
        },
    ),
)

API_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = ("api-ontology",)

API_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "Api",
    "ApiCall",
    "ApiPackage",
    "CodePackage",
    "CodePackageConfig",
)

API_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=API_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            API_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="ApiPackage",
        required_projection_names=API_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=API_RUNTIME_PROJECTION_PACKAGES,
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=100,
    ),
)

_API_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT = (
    "API-owned Workspace semantic materialization runtime context"
)

API_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=API_PROVIDER_OWNER,
        callable_module=("aware_api_runtime.runtime_context.workspace_materialization"),
        callable_name="build_api_workspace_materialization_runtime_context",
        required=True,
        priority=100,
        provider_payload={
            "contract": _API_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT,
            "runtime_ontology_package_names": (
                API_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

API_SEMANTIC_WORKFLOWS = (
    ModuleSemanticWorkflowDescriptor(
        workflow_key="external-api-service.api",
        semantic_owner=API_PROVIDER_OWNER,
        description=("API package side of external API-Service Workspace genesis."),
        stage_keys=(
            "workspace.genesis.understand",
            "workspace.genesis.plan",
            "semantic.api.materialize",
            "semantic.api.verify",
        ),
        instructions=(
            ModuleSemanticWorkflowInstructionDescriptor(
                instruction_key="external-api-service.api.authoring",
                title="Author API semantic source",
                body=(
                    "Use the API semantic contract to author API source first, "
                    "preserving grammar lanes and graph-binding expectations "
                    "before Service consumes the protocol artifact."
                ),
                stage_keys=(
                    "workspace.genesis.understand",
                    "workspace.genesis.plan",
                    "semantic.api.materialize",
                ),
                source_refs=(
                    "workspaces/aware_kernel/modules/api/ontology/runtime/python/aware_api_runtime/semantic_contract.py",
                    "aware.api.toml",
                ),
            ),
        ),
        capability_refs=(
            SEMANTIC_ANALYSIS_CAPABILITY,
            SEMANTIC_MATERIALIZATION_CAPABILITY,
            API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
            "diagnostics",
            "semantic_tokens",
        ),
        capability_profile_refs=(
            "module.aware_api",
            "module.aware_api.contracts",
        ),
        grammar_profile_refs=("workspace.code.grammar_profile.semantic_contracts",),
        source_meaning_refs=("aware_api.semantic_source_meaning",),
        ontology_feature_refs=(
            "aware_api.Api",
            "aware_api.ApiCapability",
            "aware_api.ApiCapabilityEndpoint",
        ),
        graph_binding_refs=(
            "aware_api.api_def",
            "aware_api.api_capability_def",
            "aware_api.api_capability_endpoint_def",
        ),
        expected_artifact_refs=(
            "aware.api.toml",
            "api_service_protocol",
        ),
        expected_proof_refs=(
            "api_service_protocol.hash",
            "api.semantic_function_call.plan_preview",
            "workspace.semantic_materialization.receipt",
        ),
        expected_receipt_refs=(
            "workspace.semantic_materialization",
            "code.semantic_contract.describe",
            "api.semantic_operation_function_call_resolution",
        ),
        diagnostic_refs=(
            "code.grammar_profile.resolve",
            "meta.semantic_diagnostics",
        ),
        priority=100,
    ),
)

AWARE_API_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_api",
    semantic_scope_keys=API_SEMANTIC_SCOPE_KEYS,
    capability_participation=API_CAPABILITY_PARTICIPATION,
    capability_execution_policy=API_CAPABILITY_EXECUTION_POLICY,
    capability_profiles=API_CAPABILITY_PROFILES,
    capability_bundles=API_CAPABILITY_BUNDLES,
    syntax_lanes=API_SYNTAX_LANES,
    package_roles=API_PACKAGE_ROLES,
    semantic_workflows=API_SEMANTIC_WORKFLOWS,
    manifest_resolution=API_MANIFEST_RESOLUTION,
    artifact_leaf_ownership=API_ARTIFACT_LEAF_OWNERSHIP,
    materialization_artifact_outputs=API_MATERIALIZATION_ARTIFACT_OUTPUTS,
    materialization_inputs=API_MATERIALIZATION_INPUTS,
    materialization_runtime=API_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=API_MATERIALIZATION_RUNTIME_CONTEXT,
    materialization_tooling=API_MATERIALIZATION_TOOLING,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_API_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_API_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "API_ARTIFACT_LEAF_OWNERSHIP",
    "API_API_OWNER",
    "API_CAPABILITY_OWNER",
    "API_CAPABILITY_PARTICIPATION",
    "API_CAPABILITY_BUNDLES",
    "API_CAPABILITY_EXECUTION_POLICY",
    "API_CAPABILITY_PROFILES",
    "API_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "API_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY",
    "API_DIAGNOSTICS_CAPABILITY_PROFILES",
    "API_DIAGNOSTICS_OWNER_SEQUENCE",
    "API_GRAPH_OWNER",
    "API_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "API_MATERIALIZATION_CAPABILITY_METADATA",
    "API_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "API_MATERIALIZATION_DELTA_ADAPTER_METADATA",
    "API_MATERIALIZATION_INPUTS",
    "API_MANIFEST_RESOLUTION",
    "API_MATERIALIZATION_OWNER_SEQUENCE",
    "API_MATERIALIZATION_ARTIFACT_OUTPUTS",
    "API_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "API_MATERIALIZATION_RUNTIME",
    "API_MATERIALIZATION_RUNTIME_CONTEXT",
    "API_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "API_MATERIALIZATION_TOOLING",
    "API_PROJECTION_OWNER",
    "API_PROVIDER_DELTA_BLOCKED_OPERATIONS",
    "API_PROVIDER_DELTA_PRODUCT_READINESS",
    "API_PROVIDER_DELTA_READY_OPERATIONS",
    "API_PROVIDER_OWNER",
    "API_PACKAGE_ROLES",
    "API_SEMANTIC_SCOPE_KEYS",
    "API_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION",
    "API_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY",
    "API_SEMANTIC_ANALYSIS_CAPABILITY_PROFILES",
    "API_SEMANTIC_ANALYSIS_OWNER_SEQUENCE",
    "API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA",
    "API_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION",
    "API_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "API_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY",
    "API_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "API_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "API_SEMANTIC_WORKFLOWS",
    "API_SYNTAX_LANES",
]
