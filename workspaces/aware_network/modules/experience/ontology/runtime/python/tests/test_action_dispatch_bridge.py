from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_api_runtime.invocation import (
    ApiInvocationIR,
    ApiInvocationSourceCommit,
    MaterializedApiCallBinding,
)
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_api_ontology.api.api_call_stream_event import ApiCallStreamEvent
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_capability_endpoint_response_config import (
    ApiCapabilityEndpointResponseConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_config import (
    ApiCapabilityEndpointStreamConfig,
)
from aware_api_ontology.api.api_capability_endpoint_stream_enums import (
    ApiCapabilityEndpointStreamEventKind,
    ApiCapabilityEndpointStreamMode,
)
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
    ApiCapabilityEndpointStreamEventConfig,
)
from aware_api_ontology.stable_ids import stable_api_call_id
from aware_experience.action_dispatch.bridge import (
    ACTION_DISPATCH_PUBLISHER_ID,
    ACTION_DISPATCH_ACCEPTED_REASON,
    AD_HOC_REQUEST_PAYLOAD_REJECTED_REASON,
    AMBIGUOUS_BINDING_REASON,
    ENDPOINT_MISMATCH_REASON,
    DENIED_ROLE_EVIDENCE_REASON,
    MISSING_ACTION_CONFIG_ANCHOR_REASON,
    MISSING_BINDING_REASON,
    MISSING_ROLE_EVIDENCE_REASON,
    NON_API_BINDING_REASON,
    ActionDispatchBinding,
    ActionDispatchRoleEvidence,
    derive_action_dispatch_action_execution_id,
    derive_action_dispatch_api_call_key,
    dispatch_action_api_call,
    dispatch_requested_action_intent,
    publish_action_dispatch_execution_start,
    publish_action_dispatch_stream_feedback,
    resolve_action_dispatch_binding_from_environment_profile,
)
from aware_experience.environment.event_node_scope import (
    EnvironmentEventNodeScopeLoweringError,
    lower_environment_event_node_scope,
)
from aware_experience.program.action_continuation import (
    ProgramActionContinuationResult,
)
from aware_experience.program.action_continuation_activation import (
    ProgramActionContinuationActivationError,
)
from aware_experience_ontology.action.action_experience import ActionExperience
from aware_experience_ontology.action.action_experience_invocation import (
    ActionExperienceInvocation,
)
from aware_experience_ontology.action.action_experience_invocation_request_field import (
    ActionExperienceInvocationRequestField,
)
from aware_experience_ontology.environment.environment_experience_event import (
    EnvironmentExperienceEvent,
)
from aware_experience_ontology.environment.environment_experience_event_action import (
    EnvironmentExperienceEventAction,
)
from aware_experience_ontology.environment.environment_experience_event_node_scope import (
    EnvironmentExperienceEventNodeScope,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.environment.environment_experience_projection import (
    EnvironmentExperienceProjection,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.invocation.role_config_invocation_action_config import (
    RoleConfigInvocationActionConfig,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_node import (
    ProjectionExperienceNode,
)
from aware_experience_ontology.projection.projection_experience_node_class_identity import (
    ProjectionExperienceNodeClassIdentity,
)
from aware_experience_ontology.projection.projection_experience_node_identity import (
    ProjectionExperienceNodeIdentity,
)
from aware_experience_ontology.projection.projection_experience_oigi import (
    ProjectionExperienceOIGI,
)
from aware_reactivity_service_dto.reactivity.action_feedback_enums import (
    ActionExecutionClaimStatus,
    ActionExecutionStatus,
    ActionFeedbackStage,
    ActionFeedbackStatus,
    ActionIntentStatus,
    ActionTerminalStatus,
)
from aware_reactivity.stable_ids import (
    stable_action_config_id,
    stable_action_intent_id,
    stable_event_config_id,
    stable_event_id,
)
from aware_reactivity_service_dto.reactivity.action_execution import (
    ActionExecution,
    ReactivityActionExecutionClaimResponse,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
    ReactivityActionLifecyclePublishResponse,
)
from aware_reactivity.stable_ids import stable_action_execution_id
from aware_reactivity_ontology.action.action_config import ActionConfig
from aware_reactivity_ontology.event.event_config_condition_config_scope import (
    EventConfigConditionConfigScope,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance

from ._experience_runtime_test_paths import REPO_ROOT


class _ReactivityLifecycleSdk:
    def __init__(self) -> None:
        self.requests: list[ReactivityActionLifecyclePublishRequest] = []
        self.execution_id = uuid4()
        self.feedback_id = uuid4()

    async def publish_action_lifecycle(
        self,
        request: ReactivityActionLifecyclePublishRequest,
    ) -> ReactivityActionLifecyclePublishResponse:
        self.requests.append(request)
        action_execution_id = None
        if request.execution is not None:
            action_execution_id = (
                request.execution.action_execution_id or self.execution_id
            )
        if request.terminal is not None:
            action_execution_id = request.terminal.action_execution_id
        return ReactivityActionLifecyclePublishResponse(
            request_id=request.request_id,
            accepted=True,
            published_count=1,
            action_execution_id=action_execution_id,
            action_feedback_id=(
                self.feedback_id if request.feedback is not None else None
            ),
        )


def _experience_meta_package_manifest_paths() -> tuple[Path, ...]:
    return (
        REPO_ROOT
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        REPO_ROOT / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        REPO_ROOT / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        REPO_ROOT
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
    )


def _build_experience_meta_runtime(*, aware_root: Path) -> MetaGraphRuntime:
    from aware_experience.handlers._generated import (  # noqa: WPS433
        meta_handlers as experience_meta_handlers,
    )
    from aware_meta.handlers._generated import (  # noqa: WPS433
        meta_handlers as meta_meta_handlers,
    )
    from aware_reactivity.handlers._generated import (  # noqa: WPS433
        meta_handlers as reactivity_meta_handlers,
    )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_meta_package_manifest_paths(),
        workspace_root=REPO_ROOT,
        aware_root=aware_root,
        handler_modules=(
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, meta_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
        bootstrap_modules=(
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, meta_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
    )
    assert runtime.context is not None
    return runtime


def _intent(*, status: ActionIntentStatus = ActionIntentStatus.requested):
    event_config_id = stable_event_config_id(name="home.door.lock.requested")
    activation_id = uuid4()
    event_id = stable_event_id(
        config_id=event_config_id,
        activation_id=activation_id,
    )
    action_config_id = stable_action_config_id(name="home.door.lock")
    intent_key = "subscription:door.lock"
    return ReactivityActionIntent(
        action_intent_id=stable_action_intent_id(
            event_id=event_id,
            config_id=action_config_id,
            intent_key=intent_key,
        ),
        intent_key=intent_key,
        event_id=event_id,
        event_config_id=event_config_id,
        activation_id=activation_id,
        event_type="home.door.lock.requested",
        source="reactivity.test",
        branch_id=uuid4(),
        projection_hash="projection:home-door",
        commit_id=uuid4(),
        event_config_condition_config_scope_id=uuid4(),
        event_config_condition_config_id=uuid4(),
        event_config_action_config_id=uuid4(),
        action_config_id=action_config_id,
        action_type="home.door.lock",
        status=status,
        root_object_id=uuid4(),
        object_instance_graph_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_branch_id=uuid4(),
        graph_hash_post="sha256:test",
    )


def _binding(*, request_class_config_id: UUID | None = None) -> ActionDispatchBinding:
    endpoint_id = uuid4()
    return ActionDispatchBinding(
        action_binding_id=uuid4(),
        experience_invocation_action_config_id=uuid4(),
        api_capability_endpoint_id=endpoint_id,
        action_config_api_capability_endpoint_id=endpoint_id,
        request_class_config_id=request_class_config_id,
    )


def _primitive_attribute(
    *,
    owner_key: str,
    name: str,
    is_required: bool = True,
) -> AttributeConfig:
    descriptor = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    return AttributeConfig(
        owner_key=owner_key,
        name=name,
        is_required=is_required,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _request_class(
    *attribute_names: str,
    optional_attribute_names: tuple[str, ...] = (),
) -> tuple[ClassConfig, dict[str, AttributeConfig]]:
    class_config = ClassConfig(
        name="RememberEventRequest",
        class_fqn="aware_test.memory.RememberEventRequest",
        value_mode=ClassValueMode.inline_value,
    )
    attributes: dict[str, AttributeConfig] = {}
    for position, name in enumerate(attribute_names):
        attribute = _primitive_attribute(
            owner_key=class_config.class_fqn,
            name=name,
            is_required=name not in optional_attribute_names,
        )
        attributes[name] = attribute
        class_config.class_config_attribute_configs.append(
            ClassConfigAttributeConfig(
                class_config_id=class_config.id,
                attribute_config=attribute,
                attribute_config_id=attribute.id,
                position=position,
            )
        )
    return class_config, attributes


def _request_field(
    *,
    invocation_id: UUID,
    attribute: AttributeConfig,
    source_ref: str,
    position: int = 0,
) -> ActionExperienceInvocationRequestField:
    return ActionExperienceInvocationRequestField(
        id=uuid4(),
        action_experience_invocation_id=invocation_id,
        attribute_config_id=attribute.id,
        attribute_config=attribute,
        source_ref=source_ref,
        required=True,
        position=position,
    )


def _program_continuation_result(
    *,
    target_action_config_id: UUID,
    target_endpoint_id: UUID,
    target_request_class_config_id: UUID,
    target_attribute_config_id: UUID,
    value: object,
) -> ProgramActionContinuationResult:
    return ProgramActionContinuationResult(
        source_program_impl_instruction_intent_id=uuid4(),
        target_program_impl_instruction_intent_id=uuid4(),
        source_action_config_id=uuid4(),
        target_action_config_id=target_action_config_id,
        source_api_capability_endpoint_id=uuid4(),
        target_api_capability_endpoint_id=target_endpoint_id,
        source_response_class_config_id=uuid4(),
        target_request_class_config_id=target_request_class_config_id,
        source_api_call_id=uuid4(),
        source_api_call_key=uuid4(),
        source_api_call_outcome_id=uuid4(),
        source_response_model_id=uuid4(),
        source_receipt_class_config_id=None,
        request_payload={"remembered_item_id": value},
        target_values_by_attribute_config_id={
            target_attribute_config_id: value,
        },
    )


def _ir(
    *,
    endpoint_id: UUID,
    request_class_config_id: UUID | None,
    request_payload: dict[str, object] | None = None,
) -> ApiInvocationIR:
    return ApiInvocationIR(
        api_name="memory",
        capability_name="remember_event",
        endpoint_name="remember_event",
        endpoint_ref="memory.remember_event.remember_event",
        discriminant="memory.remember_event.remember_event",
        source_path="runtime-proof",
        request_payload=request_payload or {},
        request_class_ref="aware_memory_api.memory.RememberEventRequest",
        request_class_config_id=request_class_config_id,
        request_source_path="runtime-proof",
        response_class_ref="aware_memory_api.memory.RememberEventResponse",
        response_source_path="runtime-proof",
        stream=None,
        fulfillment_bindings=(),
        description="Remember one event.",
        api_capability_endpoint_id=endpoint_id,
    )


def _typed_api_invocation_config(
    *,
    endpoint_id: UUID | None = None,
    request_class_config: ClassConfig | None = None,
    request_class_config_id: UUID | None = None,
    response_class_config_id: UUID | None = None,
    stream_event_class_config_id: UUID | None = None,
    role_config_id: UUID | None = None,
    role_policy_key: str = "invoke",
) -> ExperienceInvocationActionConfig:
    endpoint_id = endpoint_id or uuid4()
    invocation_config_id = uuid4()
    request_config_id = uuid4()
    stream_config_id = uuid4()
    effective_request_class_config_id = request_class_config_id or (
        request_class_config.id if request_class_config is not None else uuid4()
    )
    request_config = ApiCapabilityEndpointRequestConfig(
        id=request_config_id,
        api_capability_endpoint_id=endpoint_id,
        class_config_id=effective_request_class_config_id,
        class_config=request_class_config,
        response_config=ApiCapabilityEndpointResponseConfig(
            id=uuid4(),
            api_capability_endpoint_request_config_id=request_config_id,
            class_config_id=response_class_config_id or uuid4(),
        ),
        stream_config=ApiCapabilityEndpointStreamConfig(
            id=stream_config_id,
            api_capability_endpoint_request_config_id=request_config_id,
            stream_mode=ApiCapabilityEndpointStreamMode.server,
            api_capability_endpoint_stream_event_configs=[
                ApiCapabilityEndpointStreamEventConfig(
                    id=uuid4(),
                    api_capability_endpoint_stream_config_id=stream_config_id,
                    kind=ApiCapabilityEndpointStreamEventKind.notice,
                    class_config_id=stream_event_class_config_id or uuid4(),
                )
            ],
        ),
    )
    endpoint = ApiCapabilityEndpoint(
        id=endpoint_id,
        api_capability_id=uuid4(),
        name="lock_door",
        request_config=request_config,
    )
    return ExperienceInvocationActionConfig(
        id=invocation_config_id,
        projection_experience_id=uuid4(),
        target_kind=ExperienceInvocationActionTargetKind.api,
        api_capability_endpoint_id=endpoint_id,
        api_capability_endpoint=endpoint,
        role_policies=(
            [
                RoleConfigInvocationActionConfig(
                    id=uuid4(),
                    experience_invocation_action_config_id=invocation_config_id,
                    role_config_id=role_config_id,
                    policy_key=role_policy_key,
                    requirement_kind="admitted_actor_role",
                    description=None,
                )
            ]
            if role_config_id is not None
            else []
        ),
    )


def _profile_with_action_invocations(
    *,
    action_config_id: UUID,
    invocation_configs: list[ExperienceInvocationActionConfig],
    anchor_endpoint_id: UUID | None = None,
    include_action_config: bool = True,
    request_field_specs: list[tuple[AttributeConfig, str]] | None = None,
    projection_experience: ProjectionExperience | None = None,
) -> EnvironmentExperienceProfileConfig:
    profile_id = uuid4()
    event_id = uuid4()
    action_experience_id = uuid4()
    if anchor_endpoint_id is None:
        for config in invocation_configs:
            if config.api_capability_endpoint_id is not None:
                anchor_endpoint_id = config.api_capability_endpoint_id
                break
    anchor_endpoint_id = anchor_endpoint_id or uuid4()
    action_config = (
        ActionConfig(
            id=action_config_id,
            api_capability_endpoint_id=anchor_endpoint_id,
            name="door.lock",
            description="Door lock action",
            action_type="home.door.lock",
        )
        if include_action_config
        else None
    )
    action_experience = ActionExperience(
        id=action_experience_id,
        action_config_id=action_config_id,
        action_config=action_config,
        action_experience_invocations=[],
    )
    for config in invocation_configs:
        invocation_id = uuid4()
        action_experience.action_experience_invocations.append(
            ActionExperienceInvocation(
                id=invocation_id,
                action_experience_id=action_experience_id,
                experience_invocation_action_config_id=config.id,
                experience_invocation_action_config=config,
                request_fields=[
                    _request_field(
                        invocation_id=invocation_id,
                        attribute=attribute,
                        source_ref=source_ref,
                        position=position,
                    )
                    for position, (attribute, source_ref) in enumerate(
                        request_field_specs or []
                    )
                ],
            )
        )
    event = EnvironmentExperienceEvent(
        id=event_id,
        environment_experience_profile_config_id=profile_id,
        event_config_id=uuid4(),
        actions=[
            EnvironmentExperienceEventAction(
                id=uuid4(),
                environment_experience_event_id=event_id,
                action_experience_id=action_experience_id,
                action_experience=action_experience,
            )
        ],
    )
    return EnvironmentExperienceProfileConfig(
        id=profile_id,
        environment_experience_id=uuid4(),
        environment_profile_config_id=uuid4(),
        key="home.default",
        experiences=(
            [
                EnvironmentExperienceProjection(
                    id=uuid4(),
                    environment_experience_profile_config_id=profile_id,
                    projection_experience_id=projection_experience.id,
                    projection_experience=projection_experience,
                )
            ]
            if projection_experience is not None
            and projection_experience.id is not None
            else []
        ),
        events=[event],
    )


def _projection_experience_with_binding_node(
    *,
    projection_experience_id: UUID,
    alias: str,
    class_config_id: UUID,
    class_instance_identity_id: UUID,
) -> ProjectionExperience:
    node_id = uuid4()
    node_identity_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_instance = ClassInstance(
        id=uuid4(),
        object_instance_graph_id=uuid4(),
        class_config_id=class_config_id,
        source_object_id=uuid4(),
    )
    class_instance_identity = ClassInstanceIdentity(
        id=class_instance_identity_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        class_instance_id=class_instance.id,
        class_instance=class_instance,
        label=alias,
    )
    node_identity = ProjectionExperienceNodeIdentity(
        id=node_identity_id,
        projection_experience_node_id=node_id,
        key=alias,
    )
    node = ProjectionExperienceNode(
        id=node_id,
        projection_experience_id=projection_experience_id,
        object_projection_graph_node_id=uuid4(),
        key=alias,
        projection_experience_node_identities=[node_identity],
    )
    oigi_id = uuid4()
    node_class_identity = ProjectionExperienceNodeClassIdentity(
        id=uuid4(),
        projection_experience_oigi_id=oigi_id,
        projection_experience_node_identity_id=node_identity_id,
        projection_experience_node_identity=node_identity,
        class_instance_identity_id=class_instance_identity_id,
        class_instance_identity=class_instance_identity,
        key=alias,
    )
    return ProjectionExperience(
        id=projection_experience_id,
        object_projection_graph_identity_id=uuid4(),
        name="home_story",
        projection_experience_nodes=[node],
        projection_experience_oigis=[
            ProjectionExperienceOIGI(
                id=oigi_id,
                projection_experience_id=projection_experience_id,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                key="home_default",
                node_class_identities=[node_class_identity],
            )
        ],
    )


def _profile_config_for_projection(
    projection_experience: ProjectionExperience,
) -> EnvironmentExperienceProfileConfig:
    profile_id = uuid4()
    return EnvironmentExperienceProfileConfig(
        id=profile_id,
        environment_experience_id=uuid4(),
        environment_profile_config_id=uuid4(),
        key="home.default",
        experiences=[
            EnvironmentExperienceProjection(
                id=uuid4(),
                environment_experience_profile_config_id=profile_id,
                projection_experience_id=projection_experience.id,
                projection_experience=projection_experience,
            )
        ],
    )


def _sdk_invocation_config() -> ExperienceInvocationActionConfig:
    return ExperienceInvocationActionConfig(
        id=uuid4(),
        projection_experience_id=uuid4(),
        target_kind=ExperienceInvocationActionTargetKind.sdk,
        sdk_operation_id=uuid4(),
    )


def test_action_dispatch_execution_id_matches_reactivity_stable_id() -> None:
    intent = _intent()

    derived = derive_action_dispatch_action_execution_id(
        action_intent_id=intent.action_intent_id,
    )

    assert derived == stable_action_execution_id(
        action_intent_id=intent.action_intent_id,
        execution_key="primary",
    )


def test_environment_event_node_scope_lowers_declared_binding_node() -> None:
    class_config_id = uuid4()
    class_instance_identity_id = uuid4()
    projection = _projection_experience_with_binding_node(
        projection_experience_id=uuid4(),
        alias="front_door",
        class_config_id=class_config_id,
        class_instance_identity_id=class_instance_identity_id,
    )
    profile_config = _profile_config_for_projection(projection)
    node_identity = projection.projection_experience_nodes[
        0
    ].projection_experience_node_identities[0]
    projection_oigi = projection.projection_experience_oigis[0]
    node_scope = EnvironmentExperienceEventNodeScope(
        id=uuid4(),
        environment_experience_event_id=uuid4(),
        event_config_condition_config_id=uuid4(),
        projection_experience_node_identity_id=node_identity.id,
        projection_experience_node_identity=node_identity,
    )

    lowered = lower_environment_event_node_scope(
        profile_config=profile_config,
        node_scope=node_scope,
    )

    assert lowered.projection_experience_node_identity_id == node_identity.id
    assert lowered.object_instance_graph_identity_id == (
        projection_oigi.object_instance_graph_identity_id
    )
    assert lowered.class_instance_identity_id == class_instance_identity_id
    assert lowered.scope_key == (
        f"branch:all|class_instance:{class_instance_identity_id}"
    )


def test_environment_event_node_scope_rejects_undeclared_alias() -> None:
    projection = _projection_experience_with_binding_node(
        projection_experience_id=uuid4(),
        alias="front_door",
        class_config_id=uuid4(),
        class_instance_identity_id=uuid4(),
    )
    profile_config = _profile_config_for_projection(projection)
    node_scope = EnvironmentExperienceEventNodeScope(
        id=uuid4(),
        environment_experience_event_id=uuid4(),
        event_config_condition_config_id=uuid4(),
        projection_experience_node_identity_id=uuid4(),
    )

    with pytest.raises(EnvironmentEventNodeScopeLoweringError) as exc:
        lower_environment_event_node_scope(
            profile_config=profile_config,
            node_scope=node_scope,
        )

    assert str(exc.value) == "environment_event_node_scope_alias_not_declared"


def test_environment_event_node_scope_rejects_cross_lane_existing_scope() -> None:
    class_instance_identity_id = uuid4()
    projection = _projection_experience_with_binding_node(
        projection_experience_id=uuid4(),
        alias="front_door",
        class_config_id=uuid4(),
        class_instance_identity_id=class_instance_identity_id,
    )
    profile_config = _profile_config_for_projection(projection)
    node_identity = projection.projection_experience_nodes[
        0
    ].projection_experience_node_identities[0]
    event_condition_id = uuid4()
    existing_scope = EventConfigConditionConfigScope(
        id=uuid4(),
        event_config_condition_config_id=event_condition_id,
        object_instance_graph_identity_id=uuid4(),
        scope_key="branch:all|class_instance:mismatch",
        class_instance_identity_id=class_instance_identity_id,
    )
    node_scope = EnvironmentExperienceEventNodeScope(
        id=uuid4(),
        environment_experience_event_id=uuid4(),
        event_config_condition_config_id=event_condition_id,
        projection_experience_node_identity_id=node_identity.id,
        projection_experience_node_identity=node_identity,
        event_config_condition_config_scope_id=existing_scope.id,
        event_config_condition_config_scope=existing_scope,
    )

    with pytest.raises(EnvironmentEventNodeScopeLoweringError) as exc:
        lower_environment_event_node_scope(
            profile_config=profile_config,
            node_scope=node_scope,
        )

    assert str(exc.value) in {
        "environment_event_node_scope_existing_scope_id_mismatch",
        "environment_event_node_scope_existing_scope_oigi_mismatch",
    }


@pytest.mark.asyncio
async def test_environment_profile_projection_hydrates_event_node_scope_portals(
    tmp_path: Path,
) -> None:
    runtime = _build_experience_meta_runtime(aware_root=tmp_path / "aware_root")
    assert runtime.context is not None
    idx = runtime.context.index

    profile_opg = next(
        opg
        for opg in idx.ocg.object_projection_graphs
        if opg.name == "EnvironmentExperienceProfileConfig"
    )
    event_config_opg = next(
        opg for opg in idx.ocg.object_projection_graphs if opg.name == "EventConfig"
    )
    projection_experience_opg = next(
        opg
        for opg in idx.ocg.object_projection_graphs
        if opg.name == "ProjectionExperience"
    )
    reactivity_scope_opg = next(
        opg
        for opg in idx.ocg.object_projection_graphs
        if opg.name == "EventConfigConditionConfigScope"
    )
    profile_node_class_names = {
        idx.class_configs_by_id[node.class_config_id].name
        for node in profile_opg.object_projection_graph_nodes
        if node.class_config_id in idx.class_configs_by_id
    }
    profile_portals = [
        portal
        for portal in idx.portal_index.portals
        if portal.source_projection_hash == profile_opg.projection_hash
    ]

    assert "EnvironmentExperienceEventNodeScope" in profile_node_class_names
    assert any(
        portal.reference_field_name == "event_config_condition_config"
        and portal.target_projection_hash == event_config_opg.projection_hash
        for portal in profile_portals
    )
    assert any(
        portal.reference_field_name == "projection_experience_node_identity"
        and portal.target_projection_hash == projection_experience_opg.projection_hash
        for portal in profile_portals
    )
    assert any(
        portal.reference_field_name == "event_config_condition_config_scope"
        and portal.target_projection_hash == reactivity_scope_opg.projection_hash
        for portal in profile_portals
    )


@pytest.mark.asyncio
async def test_action_dispatch_execution_start_publishes_accepted_lifecycle_and_call_key() -> (
    None
):
    reactivity = _ReactivityLifecycleSdk()
    intent = _intent()
    binding = _binding(request_class_config_id=uuid4())
    request_id = uuid4()
    api_call_id = uuid4()
    action_execution_id = derive_action_dispatch_action_execution_id(
        action_intent_id=intent.action_intent_id,
    )

    result = await publish_action_dispatch_execution_start(
        reactivity=reactivity,
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        api_call_id=api_call_id,
        request_id=request_id,
        created_at_unix_ms=1_775_923_201_000,
    )

    assert result.status == "accepted"
    assert result.reason == ACTION_DISPATCH_ACCEPTED_REASON
    assert result.action_execution_id == action_execution_id
    assert result.action_feedback_id == reactivity.feedback_id
    assert result.api_call_key == derive_action_dispatch_api_call_key(
        action_execution_id=action_execution_id
    )
    assert len(reactivity.requests) == 2

    execution_request = reactivity.requests[0]
    assert execution_request.publisher_id == ACTION_DISPATCH_PUBLISHER_ID
    assert execution_request.request_id == request_id
    assert execution_request.execution is not None
    execution = execution_request.execution
    assert execution.action_execution_id == action_execution_id
    assert execution.action_intent_id == intent.action_intent_id
    assert execution.action_binding_id == binding.action_binding_id
    assert execution.api_call_id == api_call_id
    assert execution.status is ActionExecutionStatus.accepted
    assert execution.result_info == ACTION_DISPATCH_ACCEPTED_REASON

    feedback_request = reactivity.requests[1]
    assert feedback_request.feedback is not None
    feedback = feedback_request.feedback
    assert feedback.action_execution_id == action_execution_id
    assert feedback.stage is ActionFeedbackStage.dispatch
    assert feedback.status is ActionFeedbackStatus.accepted
    assert feedback.message == ACTION_DISPATCH_ACCEPTED_REASON
    assert feedback.payload is None


def test_action_dispatch_call_key_is_deterministic_from_action_execution_id() -> None:
    action_execution_id = uuid4()

    first = derive_action_dispatch_api_call_key(
        action_execution_id=action_execution_id,
    )
    second = derive_action_dispatch_api_call_key(
        action_execution_id=action_execution_id,
    )

    assert first == second
    assert first != action_execution_id


@pytest.mark.asyncio
async def test_action_dispatch_execution_start_skips_non_requested_intent() -> None:
    reactivity = _ReactivityLifecycleSdk()

    result = await publish_action_dispatch_execution_start(
        reactivity=reactivity,
        intent=_intent(status=ActionIntentStatus.skipped),
        binding=_binding(request_class_config_id=uuid4()),
    )

    assert result.status == "skipped"
    assert result.reason == "action_intent_not_requested"
    assert reactivity.requests == []


def test_resolve_action_dispatch_binding_from_environment_profile_single_api_binding() -> (
    None
):
    intent = _intent()
    assert intent.action_config_id is not None
    request_class_config_id = uuid4()
    response_class_config_id = uuid4()
    stream_event_class_config_id = uuid4()
    invocation_config = _typed_api_invocation_config(
        request_class_config_id=request_class_config_id,
        response_class_config_id=response_class_config_id,
        stream_event_class_config_id=stream_event_class_config_id,
    )
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[invocation_config],
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile,
        intent=intent,
    )

    assert resolution.status == "resolved"
    assert resolution.reason is None
    assert resolution.candidate_count == 1
    assert resolution.binding is not None
    binding = resolution.binding
    assert binding.experience_invocation_action_config_id == invocation_config.id
    assert binding.api_capability_endpoint_id == (
        invocation_config.api_capability_endpoint_id
    )
    assert binding.action_config_api_capability_endpoint_id == (
        invocation_config.api_capability_endpoint_id
    )
    assert binding.request_class_config_id == request_class_config_id
    assert binding.response_class_config_id == response_class_config_id
    assert binding.stream_event_class_config_ids == {
        "notice": stream_event_class_config_id,
    }
    assert binding.environment_experience_profile_config_id == profile.id
    assert (
        binding.environment_profile_config_id == profile.environment_profile_config_id
    )
    assert binding.environment_profile_key == "home.default"
    assert binding.environment_experience_event_id == profile.events[0].id
    assert binding.action_experience_id == (
        profile.events[0].actions[0].action_experience_id
    )


def test_resolve_action_dispatch_binding_carries_projection_node_sources() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    target_class_config_id = uuid4()
    target_class_instance_identity_id = uuid4()
    invocation_config = _typed_api_invocation_config()
    projection_experience = _projection_experience_with_binding_node(
        projection_experience_id=invocation_config.projection_experience_id,
        alias="front_door",
        class_config_id=target_class_config_id,
        class_instance_identity_id=target_class_instance_identity_id,
    )
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[invocation_config],
        projection_experience=projection_experience,
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile,
        intent=intent,
    )

    assert resolution.status == "resolved"
    assert resolution.binding is not None
    node_source = resolution.binding.binding_node_sources["front_door"]
    assert node_source.alias == "front_door"
    assert node_source.class_instance_identity_id == target_class_instance_identity_id
    assert node_source.class_config_id == target_class_config_id


def test_resolve_action_dispatch_binding_fails_closed_on_missing_anchor() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[_typed_api_invocation_config()],
        include_action_config=False,
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile,
        intent=intent,
    )

    assert resolution.status == "failed"
    assert resolution.reason == MISSING_ACTION_CONFIG_ANCHOR_REASON
    assert resolution.binding is None


def test_resolve_action_dispatch_binding_fails_closed_on_endpoint_mismatch() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[_typed_api_invocation_config(endpoint_id=uuid4())],
        anchor_endpoint_id=uuid4(),
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile,
        intent=intent,
    )

    assert resolution.status == "failed"
    assert resolution.reason == ENDPOINT_MISMATCH_REASON
    assert resolution.binding is None


def test_resolve_action_dispatch_binding_fails_closed_on_missing_binding() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    profile = _profile_with_action_invocations(
        action_config_id=uuid4(),
        invocation_configs=[_typed_api_invocation_config()],
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile,
        intent=intent,
    )

    assert resolution.status == "failed"
    assert resolution.reason == MISSING_BINDING_REASON
    assert resolution.binding is None
    assert resolution.candidate_count == 0


def test_resolve_action_dispatch_binding_fails_closed_on_ambiguous_bindings() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(endpoint_id=endpoint_id),
            _typed_api_invocation_config(endpoint_id=endpoint_id),
        ],
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile,
        intent=intent,
    )

    assert resolution.status == "failed"
    assert resolution.reason == AMBIGUOUS_BINDING_REASON
    assert resolution.binding is None
    assert resolution.candidate_count == 2


def test_resolve_action_dispatch_binding_fails_closed_on_non_api_target() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[_sdk_invocation_config()],
    )

    resolution = resolve_action_dispatch_binding_from_environment_profile(
        profile_config=profile,
        intent=intent,
    )

    assert resolution.status == "failed"
    assert resolution.reason == NON_API_BINDING_REASON
    assert resolution.binding is None
    assert resolution.candidate_count == 1


@pytest.mark.asyncio
async def test_dispatch_requested_action_intent_fails_binding_before_lifecycle_and_api() -> (
    None
):
    intent = _intent()
    assert intent.action_config_id is not None
    endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(endpoint_id=endpoint_id),
            _typed_api_invocation_config(endpoint_id=endpoint_id),
        ],
    )
    reactivity = _ReactivityLifecycleSdk()
    api_calls: list[dict[str, Any]] = []

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        api_calls.append(kwargs)
        return SimpleNamespace(materialized_call=SimpleNamespace())

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=cast(ApiInvocationIR, object()),
        api_dispatcher=_fake_api_dispatcher,
    )

    assert result.status == "binding_failed"
    assert result.reason == AMBIGUOUS_BINDING_REASON
    assert result.binding_resolution is not None
    assert result.binding_resolution.candidate_count == 2
    assert result.rejection is None
    assert result.execution_start is None
    assert result.api_call is None
    assert reactivity.requests == []
    assert api_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("evidence_granted", "expected_reason"),
    (
        (None, MISSING_ROLE_EVIDENCE_REASON),
        (False, DENIED_ROLE_EVIDENCE_REASON),
    ),
)
async def test_dispatch_requested_action_intent_fails_role_preflight_before_lifecycle_and_api(
    evidence_granted: bool | None,
    expected_reason: str,
) -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    role_config_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(role_config_id=role_config_id)
        ],
    )
    role_evidence = (
        ()
        if evidence_granted is None
        else (
            ActionDispatchRoleEvidence(
                role_config_id=role_config_id,
                policy_key="invoke",
                granted=evidence_granted,
            ),
        )
    )
    reactivity = _ReactivityLifecycleSdk()
    api_calls: list[dict[str, Any]] = []

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        api_calls.append(kwargs)
        return SimpleNamespace(materialized_call=SimpleNamespace())

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=cast(ApiInvocationIR, object()),
        role_evidence=role_evidence,
        api_dispatcher=_fake_api_dispatcher,
    )

    assert result.status == "role_denied"
    assert result.reason == expected_reason
    assert result.role_preflight is not None
    assert result.role_preflight.required_policies[0].role_config_id == role_config_id
    assert result.execution_start is None
    assert result.api_call is None
    assert reactivity.requests == []
    assert api_calls == []


@pytest.mark.asyncio
async def test_dispatch_requested_action_intent_materializes_api_then_publishes_lifecycle() -> (
    None
):
    intent = _intent()
    assert intent.action_config_id is not None
    request_class_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=api_capability_endpoint_id,
                request_class_config_id=request_class_config_id,
            )
        ],
    )
    reactivity = _ReactivityLifecycleSdk()
    request_model_id = uuid4()
    api_call_id = uuid4()
    captured: dict[str, Any] = {}

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        captured.update(kwargs)
        binding = MaterializedApiCallBinding(
            api_call_id=api_call_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=kwargs["call_key"],
            request_hash="sha256:action-dispatch-coordinator",
            request_model_id=request_model_id,
            request_class_config_id=request_class_config_id,
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="sha256:api-call",
        )
        return SimpleNamespace(
            materialized_call=SimpleNamespace(binding=binding),
        )

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=cast(ApiInvocationIR, object()),
        source_commit=cast(Any, object()),
        commit=True,
        publish=False,
        receipt_projection_backend="db",
        api_dispatcher=_fake_api_dispatcher,
    )

    assert result.status == "dispatched"
    assert result.reason == ACTION_DISPATCH_ACCEPTED_REASON
    assert result.binding_resolution is not None
    assert result.binding_resolution.status == "resolved"
    assert result.rejection is None
    assert result.execution_start is not None
    assert result.api_call is not None
    expected_action_execution_id = derive_action_dispatch_action_execution_id(
        action_intent_id=intent.action_intent_id,
    )
    assert result.execution_start.action_execution_id == expected_action_execution_id
    assert captured["call_key"] == derive_action_dispatch_api_call_key(
        action_execution_id=expected_action_execution_id,
    )
    assert captured["receipt_projection_backend"] == "db"
    assert result.api_call.api_call_id == api_call_id
    assert result.api_call.api_capability_endpoint_id == api_capability_endpoint_id
    assert result.api_call.request_model_id == request_model_id
    assert result.api_call.request_class_config_id == request_class_config_id
    assert len(reactivity.requests) == 2
    execution = reactivity.requests[0].execution
    assert execution is not None
    assert execution.action_execution_id == expected_action_execution_id
    assert execution.api_call_id == api_call_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "outcome_status",
        "expected_bridge_status",
        "expected_feedback_status",
        "expected_terminal_status",
        "continuation_error",
    ),
    [
        (
            "succeeded",
            "fulfilled",
            ActionFeedbackStatus.succeeded,
            ActionTerminalStatus.succeeded,
            False,
        ),
        (
            "succeeded",
            "continuation_failed",
            ActionFeedbackStatus.succeeded,
            ActionTerminalStatus.succeeded,
            True,
        ),
        (
            "failed",
            "fulfillment_failed",
            ActionFeedbackStatus.failed,
            ActionTerminalStatus.failed,
            False,
        ),
    ],
)
async def test_dispatch_requested_action_intent_publishes_terminal_service_outcome(
    outcome_status: str,
    expected_bridge_status: str,
    expected_feedback_status: ActionFeedbackStatus,
    expected_terminal_status: ActionTerminalStatus,
    continuation_error: bool,
) -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    request_class_config_id = uuid4()
    response_class_config_id = uuid4()
    endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=endpoint_id,
                request_class_config_id=request_class_config_id,
                response_class_config_id=response_class_config_id,
            )
        ],
    )
    reactivity = _ReactivityLifecycleSdk()
    request_model_id = uuid4()
    outcome_id = uuid4()
    response_model_id = uuid4()
    service_operation_id = uuid4()
    captured: dict[str, object] = {}
    continuation_calls: list[dict[str, object]] = []
    effect_order: list[str] = []

    class _ExecutionClaimer:
        async def claim_action_execution(self, request):  # noqa: ANN001, ANN201
            effect_order.append("claim")
            return ReactivityActionExecutionClaimResponse(
                request_id=request.request_id,
                accepted=True,
                claim_status=ActionExecutionClaimStatus.claimed,
                action_execution=ActionExecution(
                    action_execution_id=derive_action_dispatch_action_execution_id(
                        action_intent_id=intent.action_intent_id,
                    ),
                    action_intent_id=intent.action_intent_id,
                    event_id=intent.event_id,
                    event_type=intent.event_type,
                    source=intent.source,
                    branch_id=intent.branch_id,
                    projection_hash=intent.projection_hash,
                    commit_id=intent.commit_id,
                    execution_key="primary",
                ),
            )

    class _ContinuationRuntime:
        async def activate(self, **kwargs: object) -> None:
            continuation_calls.append(dict(kwargs))
            if continuation_error:
                raise ProgramActionContinuationActivationError(
                    "program_action_continuation_test_failure"
                )

    class _TerminalInvoker:
        async def invoke_action_endpoint(self, **kwargs: object) -> object:
            effect_order.append("provider")
            captured.update(kwargs)
            call_key = cast(UUID, kwargs["api_call_key"])
            api_call_id = stable_api_call_id(
                api_capability_endpoint_id=endpoint_id,
                call_key=call_key,
            )
            return SimpleNamespace(
                status=outcome_status,
                error=None if outcome_status == "succeeded" else "provider_failed",
                response_payload=(
                    {"remembered": True} if outcome_status == "succeeded" else None
                ),
                receipt=SimpleNamespace(
                    endpoint_ref="memory.remember_event.remember_event",
                    discriminant="memory.remember_event.remember_event",
                    status=outcome_status,
                    api_call_id=api_call_id,
                    api_capability_endpoint_id=endpoint_id,
                    call_key=call_key,
                    request_model_id=request_model_id,
                    api_call_outcome_id=outcome_id,
                    response_model_id=(
                        response_model_id if outcome_status == "succeeded" else None
                    ),
                    service_operation_id=service_operation_id,
                    service_operation_config_id=uuid4(),
                    service_operation_commit_id=uuid4(),
                    service_operation_head_commit_id=uuid4(),
                    service_operation_branch_id=uuid4(),
                    service_operation_projection_hash="sha256:service",
                    api_call_outcome_commit_id=uuid4(),
                    api_call_outcome_head_commit_id=uuid4(),
                    api_call_outcome_branch_id=uuid4(),
                    api_call_outcome_projection_hash="sha256:api-call",
                ),
            )

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_ir(
            endpoint_id=endpoint_id,
            request_class_config_id=request_class_config_id,
        ),
        terminal_fulfillment_invoker=_TerminalInvoker(),
        execution_claimer=_ExecutionClaimer(),
        program_continuation_activation_runtime=_ContinuationRuntime(),
    )

    assert result.status == expected_bridge_status
    assert result.api_call is not None
    assert result.terminal_outcome is not None
    assert result.terminal is not None
    assert result.execution_claim is not None
    assert effect_order == ["claim", "provider"]
    assert result.terminal_outcome.api_call_outcome_id == outcome_id
    assert result.terminal_outcome.response_model_id == (
        response_model_id if outcome_status == "succeeded" else None
    )
    assert result.terminal_outcome.service_operation_id == service_operation_id
    assert result.terminal_outcome.response_payload == (
        {"remembered": True} if outcome_status == "succeeded" else None
    )
    assert result.terminal.action_terminal_status is expected_terminal_status
    assert len(continuation_calls) == (1 if outcome_status == "succeeded" else 0)
    if continuation_error:
        assert result.reason == "program_action_continuation_test_failure"
    assert captured["endpoint_ref"] == "memory.remember_event.remember_event"
    assert captured["request_values"] == {}
    assert result.api_call.call_key == captured["api_call_key"]
    assert len(reactivity.requests) == 4
    assert reactivity.requests[0].execution is not None
    assert reactivity.requests[1].feedback is not None
    assert reactivity.requests[2].feedback is not None
    assert reactivity.requests[2].feedback.stage is ActionFeedbackStage.terminal
    assert reactivity.requests[2].feedback.status is expected_feedback_status
    assert reactivity.requests[3].terminal is not None
    assert reactivity.requests[3].terminal.terminal_status is expected_terminal_status


@pytest.mark.asyncio
async def test_dispatch_requested_action_intent_replay_never_invokes_provider() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    request_class_config_id = uuid4()
    endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=endpoint_id,
                request_class_config_id=request_class_config_id,
            )
        ],
    )

    class _ReplayClaimer:
        async def claim_action_execution(self, request):  # noqa: ANN001, ANN201
            return ReactivityActionExecutionClaimResponse(
                request_id=request.request_id,
                accepted=True,
                claim_status=ActionExecutionClaimStatus.already_running,
                action_execution=ActionExecution(
                    action_execution_id=derive_action_dispatch_action_execution_id(
                        action_intent_id=intent.action_intent_id,
                    ),
                    action_intent_id=intent.action_intent_id,
                    event_id=intent.event_id,
                    event_type=intent.event_type,
                    source=intent.source,
                    branch_id=intent.branch_id,
                    projection_hash=intent.projection_hash,
                    commit_id=intent.commit_id,
                    execution_key="primary",
                ),
            )

    class _ForbiddenInvoker:
        async def invoke_action_endpoint(self, **kwargs: object) -> object:
            raise AssertionError(f"replay invoked provider: {kwargs!r}")

    reactivity = _ReactivityLifecycleSdk()
    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_ir(
            endpoint_id=endpoint_id,
            request_class_config_id=request_class_config_id,
        ),
        terminal_fulfillment_invoker=_ForbiddenInvoker(),
        execution_claimer=_ReplayClaimer(),
    )

    assert result.status == "claim_replay_skipped"
    assert result.reason == "already_running"
    assert result.execution_claim is not None
    assert result.execution_start is None
    assert result.api_call is None
    assert reactivity.requests == []


@pytest.mark.asyncio
async def test_dispatch_requested_action_intent_composes_declared_request_payload() -> (
    None
):
    intent = _intent()
    assert intent.action_config_id is not None
    request_class, attributes = _request_class(
        "event_id",
        "commit_id",
        "intent_key",
        "transaction_intent_id",
        "transaction_intent_commit_id",
        "action_execution_id",
        "api_call_key",
        "subscription_id",
        "target_class_instance_identity_id",
        "target_class_config_id",
    )
    api_capability_endpoint_id = uuid4()
    invocation_config = _typed_api_invocation_config(
        endpoint_id=api_capability_endpoint_id,
        request_class_config=request_class,
    )
    target_class_instance_identity_id = uuid4()
    target_class_config_id = uuid4()
    projection_experience = _projection_experience_with_binding_node(
        projection_experience_id=invocation_config.projection_experience_id,
        alias="front_door",
        class_config_id=target_class_config_id,
        class_instance_identity_id=target_class_instance_identity_id,
    )
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[invocation_config],
        projection_experience=projection_experience,
        request_field_specs=[
            (attributes["event_id"], "event.id"),
            (attributes["commit_id"], "commit.commit_id"),
            (attributes["intent_key"], "intent.intent_key"),
            (attributes["transaction_intent_id"], "commit.branch_id"),
            (attributes["transaction_intent_commit_id"], "commit.commit_id"),
            (attributes["action_execution_id"], "execution.id"),
            (attributes["api_call_key"], "api_call.key"),
            (attributes["subscription_id"], "subscription.id"),
            (
                attributes["target_class_instance_identity_id"],
                "binding.node.front_door.class_instance_identity_id",
            ),
            (
                attributes["target_class_config_id"],
                "binding.node.front_door.class_config_id",
            ),
        ],
    )
    reactivity = _ReactivityLifecycleSdk()
    request_model_id = uuid4()
    api_call_id = uuid4()
    subscription_id = uuid4()
    source_commit = ApiInvocationSourceCommit(
        branch_id=uuid4(),
        projection_hash="sha256:memory-event",
        commit_id=uuid4(),
        object_instance_graph_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    captured: dict[str, Any] = {}

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        captured.update(kwargs)
        binding = MaterializedApiCallBinding(
            api_call_id=api_call_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=kwargs["call_key"],
            request_hash="sha256:declared-composition",
            request_model_id=request_model_id,
            request_class_config_id=request_class.id,
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="sha256:api-call",
        )
        return SimpleNamespace(materialized_call=SimpleNamespace(binding=binding))

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_ir(
            endpoint_id=api_capability_endpoint_id,
            request_class_config_id=request_class.id,
        ),
        source_commit=source_commit,
        subscription_id=subscription_id,
        api_dispatcher=_fake_api_dispatcher,
    )

    assert result.status == "dispatched"
    expected_action_execution_id = derive_action_dispatch_action_execution_id(
        action_intent_id=intent.action_intent_id,
    )
    expected_api_call_key = derive_action_dispatch_api_call_key(
        action_execution_id=expected_action_execution_id,
    )
    resolved_ir = captured["ir"]
    assert isinstance(resolved_ir, ApiInvocationIR)
    assert resolved_ir.request_payload == {
        "event_id": intent.event_id,
        "commit_id": source_commit.commit_id,
        "intent_key": intent.intent_key,
        "transaction_intent_id": source_commit.branch_id,
        "transaction_intent_commit_id": source_commit.commit_id,
        "action_execution_id": expected_action_execution_id,
        "api_call_key": expected_api_call_key,
        "subscription_id": subscription_id,
        "target_class_instance_identity_id": target_class_instance_identity_id,
        "target_class_config_id": target_class_config_id,
    }
    assert result.api_call is not None
    assert result.api_call.request_class_config_id == request_class.id


@pytest.mark.asyncio
async def test_dispatch_requested_action_intent_composes_program_continuation() -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    request_class, attributes = _request_class("event_id", "remembered_item_id")
    endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=endpoint_id,
                request_class_config=request_class,
            )
        ],
        request_field_specs=[(attributes["event_id"], "event.id")],
    )
    remembered_item_id = uuid4()
    continuation = _program_continuation_result(
        target_action_config_id=intent.action_config_id,
        target_endpoint_id=endpoint_id,
        target_request_class_config_id=request_class.id,
        target_attribute_config_id=attributes["remembered_item_id"].id,
        value=remembered_item_id,
    )
    captured: dict[str, Any] = {}

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        captured.update(kwargs)
        return SimpleNamespace(
            materialized_call=SimpleNamespace(
                binding=MaterializedApiCallBinding(
                    api_call_id=uuid4(),
                    api_capability_endpoint_id=endpoint_id,
                    call_key=kwargs["call_key"],
                    request_hash="sha256:program-continuation",
                    request_model_id=uuid4(),
                    request_class_config_id=request_class.id,
                    commit_id=uuid4(),
                    head_commit_id=uuid4(),
                    branch_id=uuid4(),
                    projection_hash="sha256:api-call",
                )
            )
        )

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=_ReactivityLifecycleSdk(),
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_ir(
            endpoint_id=endpoint_id,
            request_class_config_id=request_class.id,
        ),
        api_dispatcher=_fake_api_dispatcher,
        program_continuation=continuation,
    )

    assert result.status == "dispatched"
    resolved_ir = captured["ir"]
    assert isinstance(resolved_ir, ApiInvocationIR)
    assert resolved_ir.request_payload == {
        "event_id": intent.event_id,
        "remembered_item_id": remembered_item_id,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("continuation_update", "expected_reason"),
    [
        (
            {"target_action_config_id": uuid4()},
            "action_request_composition_continuation_action_config_mismatch",
        ),
        (
            {"target_api_capability_endpoint_id": uuid4()},
            "action_request_composition_continuation_endpoint_mismatch",
        ),
        (
            {"target_request_class_config_id": uuid4()},
            "action_request_composition_continuation_request_class_mismatch",
        ),
    ],
)
async def test_dispatch_requested_action_intent_rejects_mismatched_continuation_target(
    continuation_update: dict[str, object],
    expected_reason: str,
) -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    request_class, attributes = _request_class("event_id", "remembered_item_id")
    endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=endpoint_id,
                request_class_config=request_class,
            )
        ],
        request_field_specs=[(attributes["event_id"], "event.id")],
    )
    continuation = _program_continuation_result(
        target_action_config_id=intent.action_config_id,
        target_endpoint_id=endpoint_id,
        target_request_class_config_id=request_class.id,
        target_attribute_config_id=attributes["remembered_item_id"].id,
        value=uuid4(),
    )

    async def _unexpected_api_dispatcher(**kwargs: Any) -> object:
        raise AssertionError(f"continuation mismatch reached API dispatch: {kwargs}")

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=_ReactivityLifecycleSdk(),
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_ir(
            endpoint_id=endpoint_id,
            request_class_config_id=request_class.id,
        ),
        api_dispatcher=_unexpected_api_dispatcher,
        program_continuation=replace(continuation, **continuation_update),
    )

    assert result.status == "composition_rejected"
    assert result.reason == expected_reason


@pytest.mark.asyncio
async def test_dispatch_requested_action_intent_rejects_ad_hoc_payload_when_composed() -> (
    None
):
    intent = _intent()
    assert intent.action_config_id is not None
    request_class, attributes = _request_class("event_id")
    api_capability_endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=api_capability_endpoint_id,
                request_class_config=request_class,
            )
        ],
        request_field_specs=[(attributes["event_id"], "event.id")],
    )
    reactivity = _ReactivityLifecycleSdk()
    api_calls: list[dict[str, Any]] = []

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        api_calls.append(kwargs)
        return SimpleNamespace(materialized_call=SimpleNamespace())

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_ir(
            endpoint_id=api_capability_endpoint_id,
            request_class_config_id=request_class.id,
            request_payload={"event_id": "manual"},
        ),
        api_dispatcher=_fake_api_dispatcher,
    )

    assert result.status == "composition_rejected"
    assert result.reason == AD_HOC_REQUEST_PAYLOAD_REJECTED_REASON
    assert result.rejection is not None
    assert result.rejection.status == ActionFeedbackStatus.rejected.value
    assert result.execution_start is None
    assert result.api_call is None
    assert api_calls == []
    assert len(reactivity.requests) == 2
    execution = reactivity.requests[0].execution
    feedback = reactivity.requests[1].feedback
    assert execution is not None
    assert execution.status is ActionExecutionStatus.rejected
    assert execution.api_call_id is None
    assert feedback is not None
    assert feedback.status is ActionFeedbackStatus.rejected
    assert feedback.message == AD_HOC_REQUEST_PAYLOAD_REJECTED_REASON


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    (
        "unmapped_required",
        "absent_source",
        "attribute_outside_request",
        "undeclared_binding_node_alias",
    ),
)
async def test_dispatch_requested_action_intent_rejects_invalid_composition(
    case: str,
) -> None:
    intent = _intent()
    assert intent.action_config_id is not None
    api_capability_endpoint_id = uuid4()
    request_class, attributes = _request_class(
        "event_id",
        (
            "commit_id"
            if case == "unmapped_required"
            else (
                "target_class_instance_identity_id"
                if case == "undeclared_binding_node_alias"
                else "event_status"
            )
        ),
    )
    request_field_specs: list[tuple[AttributeConfig, str]]
    expected_reason_fragment: str
    if case == "unmapped_required":
        request_field_specs = [(attributes["event_id"], "event.id")]
        expected_reason_fragment = "required_attribute_unmapped:commit_id"
    elif case == "absent_source":
        request_field_specs = [(attributes["event_status"], "event.status")]
        expected_reason_fragment = "source_absent:event.status->event_status"
    elif case == "undeclared_binding_node_alias":
        request_field_specs = [
            (
                attributes["target_class_instance_identity_id"],
                "binding.node.front_door.class_instance_identity_id",
            )
        ]
        expected_reason_fragment = "binding_node_alias_not_declared:front_door"
    else:
        _, foreign_attributes = _request_class("foreign_id")
        request_field_specs = [(foreign_attributes["foreign_id"], "event.id")]
        expected_reason_fragment = "attribute_not_in_request_class"
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=api_capability_endpoint_id,
                request_class_config=request_class,
            )
        ],
        request_field_specs=request_field_specs,
    )
    reactivity = _ReactivityLifecycleSdk()
    api_calls: list[dict[str, Any]] = []

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        api_calls.append(kwargs)
        return SimpleNamespace(materialized_call=SimpleNamespace())

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=None,
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=_ir(
            endpoint_id=api_capability_endpoint_id,
            request_class_config_id=request_class.id,
        ),
        api_dispatcher=_fake_api_dispatcher,
    )

    assert result.status == "composition_rejected"
    assert result.reason is not None
    assert expected_reason_fragment in result.reason
    assert result.execution_start is None
    assert result.api_call is None
    assert api_calls == []
    assert len(reactivity.requests) == 2
    execution = reactivity.requests[0].execution
    feedback = reactivity.requests[1].feedback
    assert execution is not None
    assert execution.status is ActionExecutionStatus.rejected
    assert execution.api_call_id is None
    assert feedback is not None
    assert feedback.status is ActionFeedbackStatus.rejected
    assert feedback.message == result.reason


@pytest.mark.asyncio
async def test_dispatch_requested_action_intent_accepts_matching_role_evidence() -> (
    None
):
    intent = _intent()
    assert intent.action_config_id is not None
    role_config_id = uuid4()
    request_class_config_id = uuid4()
    api_capability_endpoint_id = uuid4()
    profile = _profile_with_action_invocations(
        action_config_id=intent.action_config_id,
        invocation_configs=[
            _typed_api_invocation_config(
                endpoint_id=api_capability_endpoint_id,
                request_class_config_id=request_class_config_id,
                role_config_id=role_config_id,
            )
        ],
    )
    reactivity = _ReactivityLifecycleSdk()
    request_model_id = uuid4()
    api_call_id = uuid4()
    actor_id = uuid4()
    role_assignment_binding_id = uuid4()

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        binding = MaterializedApiCallBinding(
            api_call_id=api_call_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            call_key=kwargs["call_key"],
            request_hash="sha256:action-dispatch-coordinator",
            request_model_id=request_model_id,
            request_class_config_id=request_class_config_id,
            commit_id=uuid4(),
            head_commit_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="sha256:api-call",
        )
        return SimpleNamespace(
            materialized_call=SimpleNamespace(binding=binding),
        )

    result = await dispatch_requested_action_intent(
        profile_config=profile,
        intent=intent,
        reactivity=reactivity,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=actor_id,
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=cast(ApiInvocationIR, object()),
        role_evidence=(
            ActionDispatchRoleEvidence(
                role_config_id=role_config_id,
                policy_key="invoke",
                actor_id=actor_id,
                role_assignment_binding_id=role_assignment_binding_id,
                granted=True,
            ),
        ),
        api_dispatcher=_fake_api_dispatcher,
    )

    assert result.status == "dispatched"
    assert result.role_preflight is not None
    assert result.role_preflight.status == "allowed"
    assert result.role_preflight.required_policies[0].role_config_id == role_config_id
    assert result.role_preflight.accepted_evidence[0].role_assignment_binding_id == (
        role_assignment_binding_id
    )
    assert result.api_call is not None
    assert len(reactivity.requests) == 2


@pytest.mark.asyncio
async def test_dispatch_action_api_call_uses_api_runtime_with_derived_call_key() -> (
    None
):
    action_execution_id = uuid4()
    api_call_key = derive_action_dispatch_api_call_key(
        action_execution_id=action_execution_id,
    )
    binding = MaterializedApiCallBinding(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=api_call_key,
        request_hash="sha256:action-dispatch",
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
        commit_id=uuid4(),
        head_commit_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:api-call",
    )
    captured: dict[str, Any] = {}

    async def _fake_api_dispatcher(**kwargs: Any) -> object:
        captured.update(kwargs)
        return SimpleNamespace(
            materialized_call=SimpleNamespace(binding=binding),
        )

    result = await dispatch_action_api_call(
        action_execution_id=action_execution_id,
        api_call_key=api_call_key,
        runtime=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        source_lane=cast(Any, object()),
        target_lane=cast(Any, object()),
        ir=cast(ApiInvocationIR, object()),
        source_commit=cast(Any, object()),
        commit=True,
        publish=False,
        receipt_projection_backend="db",
        api_dispatcher=_fake_api_dispatcher,
    )

    assert captured["call_key"] == api_call_key
    assert captured["commit"] is True
    assert captured["publish"] is False
    assert captured["receipt_projection_backend"] == "db"
    assert result.status == "materialized"
    assert result.action_execution_id == action_execution_id
    assert result.api_call_id == binding.api_call_id
    assert result.api_capability_endpoint_id == binding.api_capability_endpoint_id
    assert result.call_key == api_call_key
    assert result.request_model_id == binding.request_model_id
    assert result.request_class_config_id == binding.request_class_config_id
    assert result.commit_id == binding.commit_id
    assert result.head_commit_id == binding.head_commit_id
    assert result.branch_id == binding.branch_id
    assert result.projection_hash == binding.projection_hash


@pytest.mark.asyncio
async def test_dispatch_action_api_call_rejects_mismatched_api_call_key() -> None:
    action_execution_id = uuid4()
    api_call_key = derive_action_dispatch_api_call_key(
        action_execution_id=action_execution_id,
    )
    binding = MaterializedApiCallBinding(
        api_call_id=uuid4(),
        api_capability_endpoint_id=uuid4(),
        call_key=uuid4(),
        request_hash="sha256:wrong-key",
        request_model_id=uuid4(),
        request_class_config_id=uuid4(),
    )

    async def _fake_api_dispatcher(**_: Any) -> object:
        return SimpleNamespace(
            materialized_call=SimpleNamespace(binding=binding),
        )

    with pytest.raises(RuntimeError, match="mismatched call_key"):
        await dispatch_action_api_call(
            action_execution_id=action_execution_id,
            api_call_key=api_call_key,
            runtime=cast(Any, object()),
            index=cast(Any, object()),
            actor_id=None,
            source_lane=cast(Any, object()),
            target_lane=cast(Any, object()),
            ir=cast(ApiInvocationIR, object()),
            api_dispatcher=_fake_api_dispatcher,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "kind",
        "expected_stage",
        "expected_status",
        "expected_terminal_status",
    ),
    [
        (
            ApiCapabilityEndpointStreamEventKind.notice,
            ActionFeedbackStage.execute,
            ActionFeedbackStatus.running,
            None,
        ),
        (
            ApiCapabilityEndpointStreamEventKind.delta,
            ActionFeedbackStage.execute,
            ActionFeedbackStatus.running,
            None,
        ),
        (
            ApiCapabilityEndpointStreamEventKind.complete,
            ActionFeedbackStage.terminal,
            ActionFeedbackStatus.succeeded,
            ActionTerminalStatus.succeeded,
        ),
        (
            ApiCapabilityEndpointStreamEventKind.error,
            ActionFeedbackStage.terminal,
            ActionFeedbackStatus.failed,
            ActionTerminalStatus.failed,
        ),
    ],
)
async def test_publish_action_dispatch_stream_feedback_links_api_stream_event(
    kind: ApiCapabilityEndpointStreamEventKind,
    expected_stage: ActionFeedbackStage,
    expected_status: ActionFeedbackStatus,
    expected_terminal_status: ActionTerminalStatus | None,
) -> None:
    reactivity = _ReactivityLifecycleSdk()
    intent = _intent()
    binding = _binding(request_class_config_id=uuid4())
    action_execution_id = derive_action_dispatch_action_execution_id(
        action_intent_id=intent.action_intent_id,
    )
    stream_event_id = uuid4()
    stream_event_config = ApiCapabilityEndpointStreamEventConfig(
        id=uuid4(),
        api_capability_endpoint_stream_config_id=uuid4(),
        kind=kind,
        class_config_id=uuid4(),
    )
    stream_event = ApiCallStreamEvent(
        id=stream_event_id,
        api_call_id=uuid4(),
        sequence=2,
        api_capability_endpoint_stream_event_config_id=stream_event_config.id,
        api_capability_endpoint_stream_event_config=stream_event_config,
        event_model_id=uuid4(),
        event_model=InlineValueInstance(
            id=uuid4(),
            owner_key=stream_event_id,
            class_config_id=stream_event_config.class_config_id,
        ),
    )

    result = await publish_action_dispatch_stream_feedback(
        reactivity=reactivity,
        intent=intent,
        binding=binding,
        action_execution_id=action_execution_id,
        api_call_stream_event=stream_event,
        created_at_unix_ms=1_775_923_202_000,
    )

    assert result.status == expected_status.value
    assert result.action_execution_id == action_execution_id
    assert result.action_feedback_id == reactivity.feedback_id
    assert result.action_terminal_status is expected_terminal_status
    expected_request_count = 2 if expected_terminal_status is not None else 1
    assert len(reactivity.requests) == expected_request_count
    request = reactivity.requests[0]
    assert request.feedback is not None
    feedback = request.feedback
    assert feedback.action_execution_id == action_execution_id
    assert feedback.api_call_stream_event_id == stream_event_id
    assert feedback.sequence == stream_event.sequence
    assert feedback.stage is expected_stage
    assert feedback.status is expected_status
    assert feedback.payload is None
    assert "payload_model_id" not in type(feedback).model_fields
    assert "payload_model" not in type(feedback).model_fields
    if expected_terminal_status is None:
        return

    terminal_request = reactivity.requests[1]
    assert terminal_request.terminal is not None
    terminal = terminal_request.terminal
    assert terminal.action_execution_id == action_execution_id
    assert terminal.event_id == intent.event_id
    assert terminal.action_binding_id == binding.action_binding_id
    assert terminal.action_config_id == intent.action_config_id
    assert terminal.action_type == intent.action_type
    assert terminal.terminal_status is expected_terminal_status
    assert terminal.handled is (
        expected_terminal_status is ActionTerminalStatus.succeeded
    )
    if expected_terminal_status is ActionTerminalStatus.failed:
        assert terminal.error == f"api_stream_event:{kind.value}"
        assert terminal.info is None
    else:
        assert terminal.info == f"api_stream_event:{kind.value}"
        assert terminal.error is None


def test_action_dispatch_bridge_uses_reactivity_sdk_boundary() -> None:
    source = Path(
        "workspaces/aware_network/modules/experience/ontology/runtime/python/"
        "aware_experience/action_dispatch/bridge.py"
    ).read_text(encoding="utf-8")

    assert "publish_action_lifecycle" in source
    assert "derive_action_dispatch_api_call_key" in source
    assert "dispatch_api_invocation" in source
    assert "EnvironmentExperienceProfileConfig" in source
    forbidden = (
        "aware_reactivity_ontology",
        ".start_execution(",
        ".add_feedback(",
        "intent.actor_id",
        "intent.target_actor_id",
        "actor_subscription_id",
        "subscription_filter_config",
        "payload_model",
        "payload_model_id",
        "getattr(",
    )
    for token in forbidden:
        assert token not in source
    assert "intent_action_payload" not in source
