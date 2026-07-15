from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleCapabilityExecutionPolicyDescriptor,
    ModuleSemanticContract,
    ModuleSemanticGrammarRuleDescriptor,
    ModuleSemanticGrammarRuleFieldDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationPackageOutputDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
    ModuleSemanticSyntaxLaneDescriptor,
)
from aware_code.semantic_source_meaning import (
    CodeSemanticSourceMeaningBinding,
    CodeSemanticSourceMeaningContract,
    CodeSemanticSourceMeaningTypedOperationBinding,
)
from aware_code.source_index import (
    CodeGrammarGraphSelector,
    CodeGrammarTemplateValueBinding,
)
from aware_code.semantic_capability import SEMANTIC_ANALYSIS_CAPABILITY
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
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
from aware_experience.semantic_scope import EXPERIENCE_SEMANTIC_SCOPE_KEY
from aware_experience.profile.semantic_function_refs import (
    EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF,
)
from aware_experience.profile.semantic_operation_resolution import (
    EXPERIENCE_PROFILE_TITLE_UPDATE_BINDING_KEY,
    EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,
    EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY,
    EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION,
)
from aware_experience.profile.source_projection_contract import (
    EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY,
    EXPERIENCE_PROFILE_SOURCE_PROJECTION_CONTRACT_VERSION,
)
from aware_experience.semantic_registry import (
    EXPERIENCE_MANIFEST_RESOLUTION,
    EXPERIENCE_PACKAGE_LAYOUT,
    EXPERIENCE_PACKAGE_ROLES,
    EXPERIENCE_PROVIDER_OWNER,
    EXPERIENCE_RUNTIME_PROJECTION_PACKAGES,
)


EXPERIENCE_PROJECTION_OWNER = "aware_experience.projection"
EXPERIENCE_GRAPH_OWNER = "aware_experience.graph"
EXPERIENCE_ROLE_OWNER = "aware_experience.role"
EXPERIENCE_ACTOR_OWNER = "aware_experience.actor"
EXPERIENCE_ENVIRONMENT_OWNER = "aware_experience.environment"
EXPERIENCE_PROGRAM_OWNER = "aware_experience.program"
EXPERIENCE_ACTION_OWNER = "aware_experience.action"
EXPERIENCE_EVENT_OWNER = "aware_experience.event"
EXPERIENCE_CONNECTOR_OWNER = "aware_experience.connector"
EXPERIENCE_PROFILE_OWNER = "aware_experience.profile"

EXPERIENCE_SEMANTIC_SCOPE_KEYS = (EXPERIENCE_SEMANTIC_SCOPE_KEY,)

EXPERIENCE_DIAGNOSTICS_OWNER_SEQUENCE = (
    EXPERIENCE_PROJECTION_OWNER,
    EXPERIENCE_GRAPH_OWNER,
    EXPERIENCE_ROLE_OWNER,
    EXPERIENCE_ACTOR_OWNER,
    EXPERIENCE_ENVIRONMENT_OWNER,
    EXPERIENCE_PROGRAM_OWNER,
)

EXPERIENCE_SEMANTIC_TOKENS_OWNER_SEQUENCE = (
    EXPERIENCE_PROJECTION_OWNER,
    EXPERIENCE_GRAPH_OWNER,
    EXPERIENCE_PROGRAM_OWNER,
    EXPERIENCE_ENVIRONMENT_OWNER,
    EXPERIENCE_ROLE_OWNER,
    EXPERIENCE_ACTOR_OWNER,
    EXPERIENCE_ACTION_OWNER,
    EXPERIENCE_EVENT_OWNER,
)

EXPERIENCE_MATERIALIZATION_OWNER_SEQUENCE = (EXPERIENCE_PROVIDER_OWNER,)
EXPERIENCE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE = (EXPERIENCE_PROVIDER_OWNER,)

EXPERIENCE_MATERIALIZATION_CAPABILITY_METADATA: dict[str, object] = {
    SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_METADATA_KEY: {
        "callable_module": "aware_experience.materialization.currentness_replay",
        "callable_name": (
            SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_ADAPTER_ENTRYPOINT
        ),
        "contract_version": (
            SEMANTIC_MATERIALIZATION_CURRENTNESS_REPLAY_CONTRACT_VERSION
        ),
    },
}

EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT = CodeSemanticSourceMeaningContract(
    provider_key="aware_experience",
    semantic_owner=EXPERIENCE_PROFILE_OWNER,
    grammar_profile_key="code.grammar_profile.aware_kernel",
    bindings=(
        CodeSemanticSourceMeaningBinding(
            binding_key="aware_experience.profile.title",
            grammar_rule_name="experience_profile_title_stmt",
            anchor_field_path="title",
            graph_selector=CodeGrammarGraphSelector(
                provider_key="aware_experience",
                semantic_owner=EXPERIENCE_PROFILE_OWNER,
                subject_type=("aware_experience.EnvironmentExperienceProfileConfig"),
                field_name="title",
            ),
            semantic_subject_type=(
                "aware_experience.EnvironmentExperienceProfileConfig"
            ),
            semantic_key_template=(
                "experience.profile:{experience_name}:{profile_key}"
            ),
            semantic_field="title",
            anchor_role="experience_profile_title",
            value_domain="aware_string_literal",
            event_type="semantic_change",
            condition_keys=("aware_experience.profile.title.changed",),
            template_value_bindings=(
                CodeGrammarTemplateValueBinding(
                    value_key="experience_name",
                    grammar_rule_name="experience_profile_scope_def",
                    field_path="name",
                ),
                CodeGrammarTemplateValueBinding(
                    value_key="profile_key",
                    grammar_rule_name="experience_profile_def",
                    field_path="key",
                ),
            ),
            typed_operation_bindings=(
                CodeSemanticSourceMeaningTypedOperationBinding(
                    operation_key_template=(
                        "aware_experience.profile.title:"
                        "{experience_name}:{profile_key}:update"
                    ),
                    event_verbs=("update", "delete"),
                    semantic_operation_type=(EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION),
                    semantic_subject_type=(
                        "aware_experience.EnvironmentExperienceProfileConfig"
                    ),
                    field_path="title",
                    requires_baseline_object_identity=True,
                    contract_source="aware_experience.semantic_contract",
                    semantic_apply_boundary="ontology_function_call",
                ),
            ),
            required=False,
        ),
    ),
)

EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_METADATA: dict[str, object] = {
    "source_meaning_contract": (
        EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT.evidence_payload()
    ),
    "coverage": "profile_title_update",
}

EXPERIENCE_VIEW_API_PRODUCER_KEY = "aware_experience.view_api"
EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY = "experience.view_api.api_compile_plan"
EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY = "experience.view_api.generated_api_package"
EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY = "aware_api"
EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER = "aware_api.provider"
EXPERIENCE_VIEW_API_TARGET_INPUT_KEY = "aware_api.compile_plan"
EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION = "aware.api.compile_plan.v1"

EXPERIENCE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
    )
    for semantic_owner in EXPERIENCE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

EXPERIENCE_MATERIALIZATION_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        metadata=EXPERIENCE_MATERIALIZATION_CAPABILITY_METADATA,
    )
    for semantic_owner in EXPERIENCE_MATERIALIZATION_OWNER_SEQUENCE
)

EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability="semantic_source_meaning",
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        metadata=EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_METADATA,
    ),
)

EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA: dict[
    str,
    object,
] = {
    "contract_version": (
        EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CONTRACT_VERSION
    ),
    "callable_module": ("aware_experience.profile.semantic_operation_resolution"),
    "callable_name": (
        "resolve_experience_semantic_operation_function_call_plan_previews"
    ),
    "supported_semantic_operation_types": (EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,),
    "semantic_operation_type_refs": (EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,),
    "function_call_binding_refs": (EXPERIENCE_PROFILE_TITLE_UPDATE_BINDING_KEY,),
    "ontology_function_refs": (EXPERIENCE_PROFILE_UPDATE_TITLE_FUNCTION_REF,),
    "semantic_apply_boundary": "ontology_function_call",
    "mutates": False,
    "execution_status": "not_requested",
    "provider_contract": (
        "Experience owns profile operation vocabulary and FunctionCall bindings; "
        "Workspace discovers this resolver generically and Meta executes the "
        "ontology FunctionCall."
    ),
}

EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability=(EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY),
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        metadata=(
            EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA
        ),
    ),
)

EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_PARTICIPATION = (
    CapabilityParticipationDescriptor(
        capability=EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY,
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        metadata={
            "contract_version": EXPERIENCE_PROFILE_SOURCE_PROJECTION_CONTRACT_VERSION,
            "supported_semantic_operation_types": (
                EXPERIENCE_PROFILE_TITLE_UPDATE_OPERATION,
            ),
            "source_meaning_binding_refs": ("aware_experience.profile.title",),
        },
    ),
)

EXPERIENCE_DIAGNOSTICS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in EXPERIENCE_DIAGNOSTICS_OWNER_SEQUENCE
)

EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION = tuple(
    CapabilityParticipationDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
    )
    for semantic_owner in EXPERIENCE_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

EXPERIENCE_CAPABILITY_PARTICIPATION = (
    *EXPERIENCE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION,
    *EXPERIENCE_MATERIALIZATION_CAPABILITY_PARTICIPATION,
    *EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_PARTICIPATION,
    *EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION,
    *EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_PARTICIPATION,
    *EXPERIENCE_DIAGNOSTICS_CAPABILITY_PARTICIPATION,
    *EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION,
)

_EXPERIENCE_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER = {
    EXPERIENCE_PROVIDER_OWNER: 35,
}

_EXPERIENCE_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER = {
    EXPERIENCE_PROVIDER_OWNER: "_experience_semantic_analysis_provider",
}

_EXPERIENCE_DIAGNOSTICS_PRIORITY_BY_OWNER = {
    EXPERIENCE_PROJECTION_OWNER: 40,
    EXPERIENCE_GRAPH_OWNER: 50,
    EXPERIENCE_ROLE_OWNER: 60,
    EXPERIENCE_ACTOR_OWNER: 70,
    EXPERIENCE_ENVIRONMENT_OWNER: 80,
    EXPERIENCE_PROGRAM_OWNER: 110,
}

_EXPERIENCE_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER = {
    EXPERIENCE_PROJECTION_OWNER: "_experience_projection_provider",
    EXPERIENCE_GRAPH_OWNER: "_experience_graph_provider",
    EXPERIENCE_ROLE_OWNER: "_experience_role_provider",
    EXPERIENCE_ACTOR_OWNER: "_experience_actor_provider",
    EXPERIENCE_ENVIRONMENT_OWNER: "_environment_provider",
    EXPERIENCE_PROGRAM_OWNER: "_program_provider",
}

_EXPERIENCE_SEMANTIC_TOKENS_PRIORITY_BY_OWNER = {
    EXPERIENCE_PROJECTION_OWNER: 30,
    EXPERIENCE_GRAPH_OWNER: 40,
    EXPERIENCE_PROGRAM_OWNER: 60,
    EXPERIENCE_ENVIRONMENT_OWNER: 70,
    EXPERIENCE_ROLE_OWNER: 80,
    EXPERIENCE_ACTOR_OWNER: 90,
    EXPERIENCE_ACTION_OWNER: 100,
    EXPERIENCE_EVENT_OWNER: 110,
}

_EXPERIENCE_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER = {
    EXPERIENCE_PROJECTION_OWNER: "_experience_projection_tokens_provider",
    EXPERIENCE_GRAPH_OWNER: "_experience_graph_tokens_provider",
    EXPERIENCE_PROGRAM_OWNER: "_experience_program_tokens_provider",
    EXPERIENCE_ENVIRONMENT_OWNER: "_experience_environment_tokens_provider",
    EXPERIENCE_ROLE_OWNER: "_experience_role_tokens_provider",
    EXPERIENCE_ACTOR_OWNER: "_experience_actor_tokens_provider",
    EXPERIENCE_ACTION_OWNER: "_experience_action_tokens_provider",
    EXPERIENCE_EVENT_OWNER: "_experience_event_tokens_provider",
}

EXPERIENCE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="diagnostics",
        semantic_owner=semantic_owner,
        callable_name=_EXPERIENCE_DIAGNOSTICS_CALLABLE_NAME_BY_OWNER[semantic_owner],
        required_semantic_scope_keys=EXPERIENCE_SEMANTIC_SCOPE_KEYS,
        priority=_EXPERIENCE_DIAGNOSTICS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in EXPERIENCE_DIAGNOSTICS_OWNER_SEQUENCE
)

EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability="semantic_tokens",
        semantic_owner=semantic_owner,
        callable_name=_EXPERIENCE_SEMANTIC_TOKENS_CALLABLE_NAME_BY_OWNER[
            semantic_owner
        ],
        priority=_EXPERIENCE_SEMANTIC_TOKENS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in EXPERIENCE_SEMANTIC_TOKENS_OWNER_SEQUENCE
)

EXPERIENCE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_name=_EXPERIENCE_SEMANTIC_ANALYSIS_CALLABLE_NAME_BY_OWNER[
            semantic_owner
        ],
        required_semantic_scope_keys=EXPERIENCE_SEMANTIC_SCOPE_KEYS,
        priority=_EXPERIENCE_SEMANTIC_ANALYSIS_PRIORITY_BY_OWNER[semantic_owner],
    )
    for semantic_owner in EXPERIENCE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE
)

EXPERIENCE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY = tuple(
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
        semantic_owner=semantic_owner,
        callable_module="aware_experience.materialization.workspace_provider",
        callable_name="materialize",
        priority=200,
    )
    for semantic_owner in EXPERIENCE_MATERIALIZATION_OWNER_SEQUENCE
)

EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_EXECUTION_POLICY = (
    ModuleCapabilityExecutionPolicyDescriptor(
        capability=EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY,
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        callable_module="aware_experience.profile.source_projection",
        callable_name="resolve_experience_profile_source_projection",
        priority=100,
    ),
)

EXPERIENCE_CAPABILITY_EXECUTION_POLICY = (
    *EXPERIENCE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY,
    *EXPERIENCE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY,
    *EXPERIENCE_PROFILE_SOURCE_PROJECTION_CAPABILITY_EXECUTION_POLICY,
    *EXPERIENCE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY,
    *EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY,
)

_EXPERIENCE_DIAGNOSTICS_PROFILE_OWNERS = (
    ("module.aware_experience.actor", (EXPERIENCE_ACTOR_OWNER,)),
    ("module.aware_experience.environment", (EXPERIENCE_ENVIRONMENT_OWNER,)),
    ("module.aware_experience.graph", (EXPERIENCE_GRAPH_OWNER,)),
    ("module.aware_experience.program", (EXPERIENCE_PROGRAM_OWNER,)),
    ("module.aware_experience.projection", (EXPERIENCE_PROJECTION_OWNER,)),
    ("module.aware_experience.role", (EXPERIENCE_ROLE_OWNER,)),
)

_EXPERIENCE_SEMANTIC_TOKENS_PROFILE_OWNERS = (
    ("module.aware_experience.action", (EXPERIENCE_ACTION_OWNER,)),
    ("module.aware_experience.actor", (EXPERIENCE_ACTOR_OWNER,)),
    ("module.aware_experience.environment", (EXPERIENCE_ENVIRONMENT_OWNER,)),
    ("module.aware_experience.event", (EXPERIENCE_EVENT_OWNER,)),
    ("module.aware_experience.graph", (EXPERIENCE_GRAPH_OWNER,)),
    ("module.aware_experience.program", (EXPERIENCE_PROGRAM_OWNER,)),
    ("module.aware_experience.projection", (EXPERIENCE_PROJECTION_OWNER,)),
    ("module.aware_experience.role", (EXPERIENCE_ROLE_OWNER,)),
)

EXPERIENCE_DIAGNOSTICS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _EXPERIENCE_DIAGNOSTICS_PROFILE_OWNERS
)

EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PROFILES = tuple(
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name=name,
        semantic_owners=semantic_owners,
    )
    for name, semantic_owners in _EXPERIENCE_SEMANTIC_TOKENS_PROFILE_OWNERS
)

EXPERIENCE_CAPABILITY_PROFILES = (
    CapabilityProfileDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        name="module.aware_experience.semantic_analysis",
        semantic_owners=EXPERIENCE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE,
        default_selected=True,
    ),
    CapabilityProfileDescriptor(
        capability="diagnostics",
        name="module.aware_experience",
        semantic_owners=(
            EXPERIENCE_ACTOR_OWNER,
            EXPERIENCE_ENVIRONMENT_OWNER,
            EXPERIENCE_GRAPH_OWNER,
            EXPERIENCE_PROGRAM_OWNER,
            EXPERIENCE_PROJECTION_OWNER,
            EXPERIENCE_ROLE_OWNER,
        ),
        default_selected=True,
    ),
    *EXPERIENCE_DIAGNOSTICS_CAPABILITY_PROFILES,
    CapabilityProfileDescriptor(
        capability="semantic_tokens",
        name="module.aware_experience",
        semantic_owners=(
            EXPERIENCE_ACTION_OWNER,
            EXPERIENCE_ACTOR_OWNER,
            EXPERIENCE_ENVIRONMENT_OWNER,
            EXPERIENCE_EVENT_OWNER,
            EXPERIENCE_GRAPH_OWNER,
            EXPERIENCE_PROGRAM_OWNER,
            EXPERIENCE_PROJECTION_OWNER,
            EXPERIENCE_ROLE_OWNER,
        ),
        default_selected=True,
    ),
    *EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PROFILES,
)

EXPERIENCE_CAPABILITY_BUNDLES = (
    CapabilityBundleDescriptor(
        capability=SEMANTIC_ANALYSIS_CAPABILITY,
        name="bundle.authoring",
        profile_names=("module.aware_experience.semantic_analysis",),
    ),
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.authoring",
        profile_names=("module.aware_experience",),
    ),
    CapabilityBundleDescriptor(
        capability="diagnostics",
        name="bundle.projection",
        profile_names=("module.aware_experience.projection",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.authoring",
        profile_names=("module.aware_experience",),
    ),
    CapabilityBundleDescriptor(
        capability="semantic_tokens",
        name="bundle.projection",
        profile_names=("module.aware_experience.projection",),
    ),
)

EXPERIENCE_SYNTAX_LANES = (
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.profile",
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        compiler_owner=EXPERIENCE_PROFILE_OWNER,
        grammar_rules=(
            "experience_profile_scope_def",
            "experience_profile_def",
            "experience_profile_title_stmt",
            "experience_profile_description_stmt",
            "experience_profile_narrative_stmt",
        ),
        semantic_token_types=("namespace", "class", "property", "string"),
        semantic_token_modifiers=("experience", "profile"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.projection",
        semantic_owner=EXPERIENCE_PROJECTION_OWNER,
        compiler_owner=EXPERIENCE_PROJECTION_OWNER,
        grammar_rules=(
            "experience_def",
            "experience_observable_group",
            "experience_view_def",
            "experience_node_def",
            "experience_node_identity_def",
        ),
        semantic_token_types=("class", "type", "property", "parameter", "keyword"),
        semantic_token_modifiers=("experience", "identity"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.graph",
        semantic_owner=EXPERIENCE_GRAPH_OWNER,
        compiler_owner=EXPERIENCE_GRAPH_OWNER,
        grammar_rules=("graph_def", "graph_root_stmt", "graph_edge_stmt"),
        semantic_token_types=("class", "parameter", "property", "keyword"),
        semantic_token_modifiers=("experience",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.role",
        semantic_owner=EXPERIENCE_ROLE_OWNER,
        compiler_owner=EXPERIENCE_ROLE_OWNER,
        grammar_rules=("role_def", "role_capability_stmt"),
        semantic_token_types=("class", "type", "function"),
        semantic_token_modifiers=("role",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.actor",
        semantic_owner=EXPERIENCE_ACTOR_OWNER,
        compiler_owner=EXPERIENCE_ACTOR_OWNER,
        grammar_rules=(
            "actor_def",
            "actor_role_stmt",
            "environment_actor_stmt",
            "environment_actor_role_stmt",
        ),
        semantic_token_types=("class", "type"),
        semantic_token_modifiers=("actor", "role"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.environment",
        semantic_owner=EXPERIENCE_ENVIRONMENT_OWNER,
        compiler_owner=EXPERIENCE_ENVIRONMENT_OWNER,
        grammar_rules=(
            "environment_def",
            "environment_experience_stmt",
            "environment_program_stmt",
            "environment_event_stmt",
            "environment_event_action_stmt",
        ),
        semantic_token_types=("namespace", "type"),
        semantic_token_modifiers=("environment", "experience", "program"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.program",
        semantic_owner=EXPERIENCE_PROGRAM_OWNER,
        compiler_owner=EXPERIENCE_PROGRAM_OWNER,
        grammar_rules=(
            "program_def",
            "actor_decl_stmt",
            "port_decl_stmt",
            "port_decl_node_stmt",
            "bind_stmt",
            "call_stmt",
            "program_call",
            "input_stmt",
            "expect_stmt",
            "intent_stmt",
        ),
        semantic_token_types=("function", "type", "parameter", "property", "keyword"),
        semantic_token_modifiers=("program", "actor", "portNode", "intrinsic"),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.action",
        semantic_owner=EXPERIENCE_ACTION_OWNER,
        compiler_owner=EXPERIENCE_ACTION_OWNER,
        grammar_rules=("action_def", "action_program_stmt"),
        semantic_token_types=("keyword", "function", "type"),
        semantic_token_modifiers=("action",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.event",
        semantic_owner=EXPERIENCE_EVENT_OWNER,
        compiler_owner=EXPERIENCE_EVENT_OWNER,
        grammar_rules=("event_def", "event_binding"),
        semantic_token_types=("keyword", "class", "type", "property"),
        semantic_token_modifiers=("event",),
    ),
    ModuleSemanticSyntaxLaneDescriptor(
        lane_key="aware_experience.connector",
        semantic_owner=EXPERIENCE_CONNECTOR_OWNER,
        compiler_owner=EXPERIENCE_CONNECTOR_OWNER,
        grammar_rules=(
            "connector_def",
            "connector_provider_def",
            "connector_sensor_def",
            "connector_actuator_def",
            "connector_invocation_def",
        ),
        semantic_token_types=("class", "function", "type", "property", "keyword"),
        semantic_token_modifiers=("connector", "sensor", "actuator", "invocation"),
    ),
)

EXPERIENCE_GRAMMAR_RULE_DECLARATIONS = (
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        rule_name="experience_profile_scope_def",
        top_level=True,
        section_type="experience_profile_scope",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="name",
                field_role="experience_identity",
                value_kind="identifier",
                required=True,
            ),
        ),
        child_rule_refs=("experience_profile_def",),
        source_anchor_fields=("name",),
    ),
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        rule_name="experience_profile_def",
        section_type="experience_profile",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="key",
                field_role="profile_identity",
                value_kind="view_path",
                required=True,
            ),
        ),
        child_rule_refs=(
            "experience_profile_title_stmt",
            "experience_profile_description_stmt",
            "experience_profile_narrative_stmt",
        ),
        source_anchor_fields=("key",),
    ),
    ModuleSemanticGrammarRuleDescriptor(
        semantic_owner=EXPERIENCE_PROFILE_OWNER,
        rule_name="experience_profile_title_stmt",
        section_type="experience_profile_title",
        fields=(
            ModuleSemanticGrammarRuleFieldDescriptor(
                field_path="title",
                field_role="profile_title",
                value_kind="string_literal",
                required=True,
            ),
        ),
        source_anchor_fields=("title",),
    ),
)

EXPERIENCE_MATERIALIZATION_ARTIFACT_OUTPUTS = (
    ModuleSemanticMaterializationArtifactOutputDescriptor(
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        producer_key=EXPERIENCE_VIEW_API_PRODUCER_KEY,
        output_key=EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY,
        artifact_family="api_compile_plan",
        artifact_role="compile_plan",
        output_kind="compile_plan",
        artifact_path_pattern=".aware/api/runtime/{package_key}/api.compile_plan.json",
        media_type="application/vnd.aware.api.compile-plan+json",
        runtime_contract_version=EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION,
        required_for=("workspace.semantic_materialization",),
        required=False,
        priority=100,
        provider_payload={
            "target_provider_key": EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY,
            "target_semantic_owner": EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER,
            "target_input_key": EXPERIENCE_VIEW_API_TARGET_INPUT_KEY,
            "schema_version": 10,
        },
    ),
)

EXPERIENCE_MATERIALIZATION_PACKAGE_OUTPUTS = (
    ModuleSemanticMaterializationPackageOutputDescriptor(
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        producer_key=EXPERIENCE_VIEW_API_PRODUCER_KEY,
        output_key=EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY,
        target_provider_key=EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY,
        target_semantic_owner=EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER,
        target_input_key=EXPERIENCE_VIEW_API_TARGET_INPUT_KEY,
        target_package_family="api",
        target_semantic_kind="api_package",
        input_artifact_producer_key=EXPERIENCE_VIEW_API_PRODUCER_KEY,
        input_artifact_output_key=EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY,
        input_artifact_family="api_compile_plan",
        runtime_contract_version=EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION,
        required_for=("workspace.semantic_materialization",),
        required=False,
        priority=100,
        provider_payload={
            "source": "experience projection views",
            "schema_version": 10,
        },
    ),
)

EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES = (
    "experience-ontology",
    "api-ontology",
)

EXPERIENCE_MATERIALIZATION_REQUIRED_PROJECTIONS = (
    "ActionExperience",
    "ActuatorConfig",
    "ActuatorInvocationActionConfig",
    "Api",
    "ApiPackage",
    "ActorConfig",
    "CodePackage",
    "ConnectorConfig",
    "ConnectorProvider",
    "EnvironmentExperience",
    "EnvironmentExperienceProfileConfig",
    "EnvironmentExperienceProfile",
    "EnvironmentTopologySeed",
    "ExperienceInvocationActionConfig",
    "ObjectInstanceGraphIdentity",
    "ProgramConfig",
    "ProgramConfigGraph",
    "ProgramImpl",
    "ProjectionExperience",
    "ProjectionExperienceGraph",
    "ProjectionExperienceOIGI",
    "ProjectionExperienceSectionGraphBinding",
    "RoleConfig",
    "SensorConfig",
    "SensorInvocationActionConfig",
    "ThreadConfig",
)

EXPERIENCE_MATERIALIZATION_RUNTIME = (
    ModuleSemanticMaterializationRuntimeDescriptor(
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        runtime_ontology_package_names=(
            EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        lane_projection_name="ExperiencePackage",
        required_projection_names=EXPERIENCE_MATERIALIZATION_REQUIRED_PROJECTIONS,
        runtime_projection_packages=EXPERIENCE_RUNTIME_PROJECTION_PACKAGES,
        environment_handle="workspace-semantic-materialization",
        include_package_dependency_closure=True,
        priority=200,
    ),
)

_EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT = (
    "Experience-owned Workspace semantic materialization runtime context"
)

EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT = (
    ModuleSemanticMaterializationRuntimeContextDescriptor(
        semantic_owner=EXPERIENCE_PROVIDER_OWNER,
        callable_module="aware_experience.materialization.runtime_context",
        callable_name="build_experience_workspace_materialization_runtime_context",
        required=True,
        priority=200,
        provider_payload={
            "contract": _EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT_CONTRACT,
            "runtime_ontology_package_names": (
                EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES
            ),
        },
    ),
)

AWARE_EXPERIENCE_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key="aware_experience",
    semantic_scope_keys=EXPERIENCE_SEMANTIC_SCOPE_KEYS,
    capability_participation=EXPERIENCE_CAPABILITY_PARTICIPATION,
    capability_execution_policy=EXPERIENCE_CAPABILITY_EXECUTION_POLICY,
    capability_profiles=EXPERIENCE_CAPABILITY_PROFILES,
    capability_bundles=EXPERIENCE_CAPABILITY_BUNDLES,
    syntax_lanes=EXPERIENCE_SYNTAX_LANES,
    grammar_rule_declarations=EXPERIENCE_GRAMMAR_RULE_DECLARATIONS,
    package_roles=EXPERIENCE_PACKAGE_ROLES,
    manifest_resolution=EXPERIENCE_MANIFEST_RESOLUTION,
    package_layout=EXPERIENCE_PACKAGE_LAYOUT,
    materialization_artifact_outputs=EXPERIENCE_MATERIALIZATION_ARTIFACT_OUTPUTS,
    materialization_package_outputs=EXPERIENCE_MATERIALIZATION_PACKAGE_OUTPUTS,
    materialization_runtime=EXPERIENCE_MATERIALIZATION_RUNTIME,
    materialization_runtime_context=EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT,
)
AWARE_MODULE_SEMANTIC_CONTRACT = AWARE_EXPERIENCE_SEMANTIC_CONTRACT


__all__ = [
    "AWARE_EXPERIENCE_SEMANTIC_CONTRACT",
    "AWARE_MODULE_SEMANTIC_CONTRACT",
    "EXPERIENCE_ACTION_OWNER",
    "EXPERIENCE_ACTOR_OWNER",
    "EXPERIENCE_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_CAPABILITY_BUNDLES",
    "EXPERIENCE_CAPABILITY_EXECUTION_POLICY",
    "EXPERIENCE_CAPABILITY_PROFILES",
    "EXPERIENCE_CONNECTOR_OWNER",
    "EXPERIENCE_GRAMMAR_RULE_DECLARATIONS",
    "EXPERIENCE_DIAGNOSTICS_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_DIAGNOSTICS_CAPABILITY_EXECUTION_POLICY",
    "EXPERIENCE_DIAGNOSTICS_CAPABILITY_PROFILES",
    "EXPERIENCE_DIAGNOSTICS_OWNER_SEQUENCE",
    "EXPERIENCE_ENVIRONMENT_OWNER",
    "EXPERIENCE_EVENT_OWNER",
    "EXPERIENCE_GRAPH_OWNER",
    "EXPERIENCE_MANIFEST_RESOLUTION",
    "EXPERIENCE_MATERIALIZATION_ARTIFACT_OUTPUTS",
    "EXPERIENCE_MATERIALIZATION_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_MATERIALIZATION_CAPABILITY_EXECUTION_POLICY",
    "EXPERIENCE_MATERIALIZATION_PACKAGE_OUTPUTS",
    "EXPERIENCE_MATERIALIZATION_RUNTIME",
    "EXPERIENCE_MATERIALIZATION_RUNTIME_CONTEXT",
    "EXPERIENCE_MATERIALIZATION_RUNTIME_ONTOLOGY_PACKAGE_NAMES",
    "EXPERIENCE_MATERIALIZATION_REQUIRED_PROJECTIONS",
    "EXPERIENCE_MATERIALIZATION_OWNER_SEQUENCE",
    "EXPERIENCE_PACKAGE_LAYOUT",
    "EXPERIENCE_SEMANTIC_ANALYSIS_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_SEMANTIC_ANALYSIS_CAPABILITY_EXECUTION_POLICY",
    "EXPERIENCE_SEMANTIC_ANALYSIS_OWNER_SEQUENCE",
    "EXPERIENCE_PACKAGE_ROLES",
    "EXPERIENCE_PROGRAM_OWNER",
    "EXPERIENCE_PROFILE_OWNER",
    "EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_METADATA",
    "EXPERIENCE_PROFILE_SOURCE_MEANING_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_PROFILE_SOURCE_MEANING_CONTRACT",
    "EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_METADATA",
    "EXPERIENCE_SEMANTIC_OPERATION_FUNCTION_CALL_RESOLUTION_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_PROJECTION_OWNER",
    "EXPERIENCE_PROVIDER_OWNER",
    "EXPERIENCE_ROLE_OWNER",
    "EXPERIENCE_SEMANTIC_SCOPE_KEYS",
    "EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PARTICIPATION",
    "EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_EXECUTION_POLICY",
    "EXPERIENCE_SEMANTIC_TOKENS_CAPABILITY_PROFILES",
    "EXPERIENCE_SEMANTIC_TOKENS_OWNER_SEQUENCE",
    "EXPERIENCE_SYNTAX_LANES",
    "EXPERIENCE_VIEW_API_COMPILE_PLAN_OUTPUT_KEY",
    "EXPERIENCE_VIEW_API_PACKAGE_OUTPUT_KEY",
    "EXPERIENCE_VIEW_API_PRODUCER_KEY",
    "EXPERIENCE_VIEW_API_RUNTIME_CONTRACT_VERSION",
    "EXPERIENCE_VIEW_API_TARGET_INPUT_KEY",
    "EXPERIENCE_VIEW_API_TARGET_PROVIDER_KEY",
    "EXPERIENCE_VIEW_API_TARGET_SEMANTIC_OWNER",
]
