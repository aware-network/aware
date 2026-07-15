# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_experience_service_dto.experience.actor_admission.service_operation import (
    AdmitExperienceActorConfigRequest,
    AdmitExperienceActorConfigResponse,
)
from aware_experience_service_dto.experience.environment_profile.service_operation import (
    ApplyExperienceEnvironmentProfileProgramsRequest,
    ApplyExperienceEnvironmentProfileProgramsResponse,
    ProvisionExperienceEnvironmentProfileRequest,
    ProvisionExperienceEnvironmentProfileResponse,
    UpsertExperienceEnvironmentProfileRequest,
    UpsertExperienceEnvironmentProfileResponse,
)
from aware_experience_service_dto.experience.layout_transition.service_operation import (
    RequestExperienceLayoutTransitionRequest,
    RequestExperienceLayoutTransitionResponse,
)
from aware_experience_service_dto.experience.package_materialization.service_operation import (
    ResolveExperiencePackageProjectionOwnershipRequest,
    ResolveExperiencePackageProjectionOwnershipResponse,
)
from aware_experience_service_dto.experience.program.service_operation import (
    ApplyProgramRefRequest,
    ApplyProgramRefResponse,
    GetTurnExecutionRequest,
    GetTurnExecutionResponse,
    RunProgramRequest,
    RunProgramResponse,
    SubmitProgramTurnRequest,
    SubmitProgramTurnResponse,
)
from aware_experience_service_dto.experience.section_graph_binding.models import ExperienceSectionGraphBindingStateEvent
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceLayoutGraphBindingRequest,
    ActivateExperienceLayoutGraphBindingResponse,
    ActivateExperienceSectionGraphBindingRequest,
    ActivateExperienceSectionGraphBindingResponse,
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
    GetExperienceLayoutGraphBindingCatalogRequest,
    GetExperienceLayoutGraphBindingCatalogResponse,
    GetExperienceLayoutGraphBindingStateRequest,
    GetExperienceLayoutGraphBindingStateResponse,
    GetExperienceSectionGraphBindingCatalogRequest,
    GetExperienceSectionGraphBindingCatalogResponse,
    GetExperienceSectionGraphBindingStateRequest,
    GetExperienceSectionGraphBindingStateResponse,
    InvokeExperienceViewInvocationActionRequest,
    InvokeExperienceViewInvocationActionResponse,
    RecordExperienceViewInvocationActionRequest,
    RecordExperienceViewInvocationActionResponse,
    ResolveExperienceInvocationActionRolePolicyRequest,
    ResolveExperienceInvocationActionRolePolicyResponse,
    WatchExperienceSectionGraphBindingsRequest,
    WatchExperienceSectionGraphBindingsResponse,
)
from aware_experience_service_dto.experience.session_commit.service_operation import (
    DescribeExperienceSessionRequest,
    DescribeExperienceSessionResponse,
    MountExperienceSessionProfileRequest,
    MountExperienceSessionProfileResponse,
    StartExperienceSessionRequest,
    StartExperienceSessionResponse,
)
from aware_experience_service_dto.experience.session_context.service_operation import (
    ResolveExperienceSessionContextRequest,
    ResolveExperienceSessionContextResponse,
)
from aware_experience_service_dto.experience.session_handoff.service_operation import (
    EnsureExperienceSessionHandoffRequest,
    EnsureExperienceSessionHandoffResponse,
    GetExperienceSessionHandoffStatusRequest,
    GetExperienceSessionHandoffStatusResponse,
)
from aware_experience_service_dto.experience.session_view_frame.service_operation import (
    ResolveExperienceSessionViewFrameRequest,
    ResolveExperienceSessionViewFrameResponse,
)
from aware_experience_service_dto.experience.thread_layout_resolution.service_operation import (
    ResolveExperienceThreadLayoutIntentRequest,
    ResolveExperienceThreadLayoutIntentResponse,
)
from aware_experience_service_dto.experience.view_state.models import ExperienceViewStateEvent
from aware_experience_service_dto.experience.view_state.service_operation import (
    WatchExperienceViewStateRequest,
    WatchExperienceViewStateResponse,
)

API_PACKAGE_NAME: Final[str] = "experience-service-api"
API_FQN_PREFIX: Final[str] = "aware_experience_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_experience_service_api"


@dataclass(frozen=True, slots=True)
class ServiceProtocolFulfillmentBinding:
    name: str
    graph_target: str
    graph_capability_function_name: str
    graph_function_python_ref: str
    method_name: str
    request_type_ref: str
    response_type_ref: str


class ServiceProtocolExecutionBackend(Protocol):
    async def invoke_fulfillment(
        self,
        *,
        fulfillment_name: str,
        request: BaseModel,
    ) -> object | None: ...


class ServiceProtocolExecution(Protocol):
    pass


ServiceProtocolExecutionFactory: TypeAlias = Callable[[ServiceProtocolExecutionBackend], ServiceProtocolExecution]

ServiceProtocolInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], Awaitable[object | None]
]

ServiceProtocolStreamInvoker: TypeAlias = Callable[
    [object, BaseModel, ServiceProtocolExecution | None], AsyncIterator[object]
]


def _coerce_model_payload(value: object, *, model_cls: type[BaseModel]) -> object:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    required_fields = [name for name, field in model_cls.model_fields.items() if field.is_required()]
    if len(required_fields) == 1:
        field_name = required_fields[0]
        if isinstance(payload, dict) and field_name in payload:
            return payload
        return {field_name: payload}
    return payload


@dataclass(frozen=True, slots=True)
class ServiceProtocolEndpointBinding:
    endpoint_ref: str
    api_name: str
    capability_name: str
    endpoint_name: str
    request_type_ref: str
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    build_execution: ServiceProtocolExecutionFactory | None
    stream_invoke: ServiceProtocolStreamInvoker | None
    fulfillment_bindings: tuple[ServiceProtocolFulfillmentBinding, ...]
    invoke: ServiceProtocolInvoker


async def invoke_experience__activate_experience_layout_graph_binding__activate_experience_layout_graph_binding(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActivateExperienceLayoutGraphBindingResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ActivateExperienceLayoutGraphBindingRequest.model_validate(request)
    return await typed_handler.experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding(
        typed_request
    )


EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF: Final[
    str
] = "experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding"
EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF,
    api_name="experience",
    capability_name="activate_experience_layout_graph_binding",
    endpoint_name="activate_experience_layout_graph_binding",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceLayoutGraphBindingRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceLayoutGraphBindingResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__activate_experience_layout_graph_binding__activate_experience_layout_graph_binding,
)


async def invoke_experience__activate_experience_section_graph_binding__activate_experience_section_graph_binding(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActivateExperienceSectionGraphBindingResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ActivateExperienceSectionGraphBindingRequest.model_validate(request)
    return await typed_handler.experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding(
        typed_request
    )


EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF: Final[
    str
] = "experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding"
EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_PROTOCOL_BINDING: (
    Final[ServiceProtocolEndpointBinding]
) = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF,
    api_name="experience",
    capability_name="activate_experience_section_graph_binding",
    endpoint_name="activate_experience_section_graph_binding",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceSectionGraphBindingRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.ActivateExperienceSectionGraphBindingResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__activate_experience_section_graph_binding__activate_experience_section_graph_binding,
)


async def invoke_experience__actor_admission__admit_experience_actor_config(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AdmitExperienceActorConfigResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = AdmitExperienceActorConfigRequest.model_validate(request)
    return await typed_handler.experience.actor_admission.admit_experience_actor_config(typed_request)


EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF: Final[str] = (
    "experience.actor_admission.admit_experience_actor_config"
)
EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF,
        api_name="experience",
        capability_name="actor_admission",
        endpoint_name="admit_experience_actor_config",
        request_type_ref="aware_experience_service_dto.experience.actor_admission.AdmitExperienceActorConfigRequest",
        response_type_ref="aware_experience_service_dto.experience.actor_admission.AdmitExperienceActorConfigResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_experience__actor_admission__admit_experience_actor_config,
    )
)


async def invoke_experience__apply_experience_view_event_transition__apply_experience_view_event_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ApplyExperienceViewEventTransitionResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ApplyExperienceViewEventTransitionRequest.model_validate(request)
    return await typed_handler.experience.apply_experience_view_event_transition.apply_experience_view_event_transition(
        typed_request
    )


EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "experience.apply_experience_view_event_transition.apply_experience_view_event_transition"
)
EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF,
    api_name="experience",
    capability_name="apply_experience_view_event_transition",
    endpoint_name="apply_experience_view_event_transition",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.ApplyExperienceViewEventTransitionRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.ApplyExperienceViewEventTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__apply_experience_view_event_transition__apply_experience_view_event_transition,
)


async def invoke_experience__describe_experience_session__describe_experience_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeExperienceSessionResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = DescribeExperienceSessionRequest.model_validate(request)
    return await typed_handler.experience.describe_experience_session.describe_experience_session(typed_request)


EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF: Final[str] = (
    "experience.describe_experience_session.describe_experience_session"
)
EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF,
    api_name="experience",
    capability_name="describe_experience_session",
    endpoint_name="describe_experience_session",
    request_type_ref="aware_experience_service_dto.experience.session_commit.DescribeExperienceSessionRequest",
    response_type_ref="aware_experience_service_dto.experience.session_commit.DescribeExperienceSessionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__describe_experience_session__describe_experience_session,
)


async def invoke_experience__environment_profile__apply_experience_environment_profile_programs(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ApplyExperienceEnvironmentProfileProgramsResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ApplyExperienceEnvironmentProfileProgramsRequest.model_validate(request)
    return await typed_handler.experience.environment_profile.apply_experience_environment_profile_programs(
        typed_request
    )


EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF: Final[str] = (
    "experience.environment_profile.apply_experience_environment_profile_programs"
)
EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF,
    api_name="experience",
    capability_name="environment_profile",
    endpoint_name="apply_experience_environment_profile_programs",
    request_type_ref="aware_experience_service_dto.experience.environment_profile.ApplyExperienceEnvironmentProfileProgramsRequest",
    response_type_ref="aware_experience_service_dto.experience.environment_profile.ApplyExperienceEnvironmentProfileProgramsResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__environment_profile__apply_experience_environment_profile_programs,
)


async def invoke_experience__environment_profile__provision_experience_environment_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ProvisionExperienceEnvironmentProfileResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ProvisionExperienceEnvironmentProfileRequest.model_validate(request)
    return await typed_handler.experience.environment_profile.provision_experience_environment_profile(typed_request)


EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "experience.environment_profile.provision_experience_environment_profile"
)
EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    api_name="experience",
    capability_name="environment_profile",
    endpoint_name="provision_experience_environment_profile",
    request_type_ref="aware_experience_service_dto.experience.environment_profile.ProvisionExperienceEnvironmentProfileRequest",
    response_type_ref="aware_experience_service_dto.experience.environment_profile.ProvisionExperienceEnvironmentProfileResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__environment_profile__provision_experience_environment_profile,
)


async def invoke_experience__environment_profile__upsert_experience_environment_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> UpsertExperienceEnvironmentProfileResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = UpsertExperienceEnvironmentProfileRequest.model_validate(request)
    return await typed_handler.experience.environment_profile.upsert_experience_environment_profile(typed_request)


EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF: Final[str] = (
    "experience.environment_profile.upsert_experience_environment_profile"
)
EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF,
    api_name="experience",
    capability_name="environment_profile",
    endpoint_name="upsert_experience_environment_profile",
    request_type_ref="aware_experience_service_dto.experience.environment_profile.UpsertExperienceEnvironmentProfileRequest",
    response_type_ref="aware_experience_service_dto.experience.environment_profile.UpsertExperienceEnvironmentProfileResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__environment_profile__upsert_experience_environment_profile,
)


async def invoke_experience__get_experience_layout_graph_binding_catalog__get_experience_layout_graph_binding_catalog(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetExperienceLayoutGraphBindingCatalogResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = GetExperienceLayoutGraphBindingCatalogRequest.model_validate(request)
    return await typed_handler.experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog(
        typed_request
    )


EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF: (
    Final[str]
) = ("experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog")
EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_PROTOCOL_BINDING: (
    Final[ServiceProtocolEndpointBinding]
) = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    api_name="experience",
    capability_name="get_experience_layout_graph_binding_catalog",
    endpoint_name="get_experience_layout_graph_binding_catalog",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingCatalogRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingCatalogResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__get_experience_layout_graph_binding_catalog__get_experience_layout_graph_binding_catalog,
)


async def invoke_experience__get_experience_layout_graph_binding_state__get_experience_layout_graph_binding_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetExperienceLayoutGraphBindingStateResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = GetExperienceLayoutGraphBindingStateRequest.model_validate(request)
    return await typed_handler.experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state(
        typed_request
    )


EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF: Final[
    str
] = "experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state"
EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_PROTOCOL_BINDING: (
    Final[ServiceProtocolEndpointBinding]
) = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF,
    api_name="experience",
    capability_name="get_experience_layout_graph_binding_state",
    endpoint_name="get_experience_layout_graph_binding_state",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingStateRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceLayoutGraphBindingStateResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__get_experience_layout_graph_binding_state__get_experience_layout_graph_binding_state,
)


async def invoke_experience__get_experience_section_graph_binding_catalog__get_experience_section_graph_binding_catalog(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetExperienceSectionGraphBindingCatalogResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = GetExperienceSectionGraphBindingCatalogRequest.model_validate(request)
    return await typed_handler.experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog(
        typed_request
    )


EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF: (
    Final[str]
) = ("experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog")
EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    api_name="experience",
    capability_name="get_experience_section_graph_binding_catalog",
    endpoint_name="get_experience_section_graph_binding_catalog",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingCatalogRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingCatalogResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__get_experience_section_graph_binding_catalog__get_experience_section_graph_binding_catalog,
)


async def invoke_experience__get_experience_section_graph_binding_state__get_experience_section_graph_binding_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetExperienceSectionGraphBindingStateResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = GetExperienceSectionGraphBindingStateRequest.model_validate(request)
    return await typed_handler.experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state(
        typed_request
    )


EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF: Final[
    str
] = "experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state"
EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_PROTOCOL_BINDING: (
    Final[ServiceProtocolEndpointBinding]
) = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF,
    api_name="experience",
    capability_name="get_experience_section_graph_binding_state",
    endpoint_name="get_experience_section_graph_binding_state",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingStateRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.GetExperienceSectionGraphBindingStateResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__get_experience_section_graph_binding_state__get_experience_section_graph_binding_state,
)


async def invoke_experience__invoke_experience_view_invocation_action__invoke_experience_view_invocation_action(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InvokeExperienceViewInvocationActionResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = InvokeExperienceViewInvocationActionRequest.model_validate(request)
    return await typed_handler.experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action(
        typed_request
    )


EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF: Final[
    str
] = "experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action"
EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
    api_name="experience",
    capability_name="invoke_experience_view_invocation_action",
    endpoint_name="invoke_experience_view_invocation_action",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.InvokeExperienceViewInvocationActionRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.InvokeExperienceViewInvocationActionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__invoke_experience_view_invocation_action__invoke_experience_view_invocation_action,
)


async def invoke_experience__mount_experience_session_profile__mount_experience_session_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MountExperienceSessionProfileResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = MountExperienceSessionProfileRequest.model_validate(request)
    return await typed_handler.experience.mount_experience_session_profile.mount_experience_session_profile(
        typed_request
    )


EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF: Final[str] = (
    "experience.mount_experience_session_profile.mount_experience_session_profile"
)
EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF,
    api_name="experience",
    capability_name="mount_experience_session_profile",
    endpoint_name="mount_experience_session_profile",
    request_type_ref="aware_experience_service_dto.experience.session_commit.MountExperienceSessionProfileRequest",
    response_type_ref="aware_experience_service_dto.experience.session_commit.MountExperienceSessionProfileResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__mount_experience_session_profile__mount_experience_session_profile,
)


async def invoke_experience__package_materialization__resolve_experience_package_projection_ownership(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveExperiencePackageProjectionOwnershipResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ResolveExperiencePackageProjectionOwnershipRequest.model_validate(request)
    return await typed_handler.experience.package_materialization.resolve_experience_package_projection_ownership(
        typed_request
    )


EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF: Final[str] = (
    "experience.package_materialization.resolve_experience_package_projection_ownership"
)
EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF,
    api_name="experience",
    capability_name="package_materialization",
    endpoint_name="resolve_experience_package_projection_ownership",
    request_type_ref="aware_experience_service_dto.experience.package_materialization.ResolveExperiencePackageProjectionOwnershipRequest",
    response_type_ref="aware_experience_service_dto.experience.package_materialization.ResolveExperiencePackageProjectionOwnershipResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__package_materialization__resolve_experience_package_projection_ownership,
)


async def invoke_experience__program__apply_program_ref(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ApplyProgramRefResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ApplyProgramRefRequest.model_validate(request)
    return await typed_handler.experience.program.apply_program_ref(typed_request)


EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF: Final[str] = "experience.program.apply_program_ref"
EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF,
        api_name="experience",
        capability_name="program",
        endpoint_name="apply_program_ref",
        request_type_ref="aware_experience_service_dto.experience.program.ApplyProgramRefRequest",
        response_type_ref="aware_experience_service_dto.experience.program.ApplyProgramRefResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_experience__program__apply_program_ref,
    )
)


async def invoke_experience__program__get_turn_execution(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetTurnExecutionResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = GetTurnExecutionRequest.model_validate(request)
    return await typed_handler.experience.program.get_turn_execution(typed_request)


EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF: Final[str] = "experience.program.get_turn_execution"
EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF,
        api_name="experience",
        capability_name="program",
        endpoint_name="get_turn_execution",
        request_type_ref="aware_experience_service_dto.experience.program.GetTurnExecutionRequest",
        response_type_ref="aware_experience_service_dto.experience.program.GetTurnExecutionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_experience__program__get_turn_execution,
    )
)


async def invoke_experience__program__run_program(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RunProgramResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = RunProgramRequest.model_validate(request)
    return await typed_handler.experience.program.run_program(typed_request)


EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF: Final[str] = "experience.program.run_program"
EXPERIENCE__PROGRAM__RUN_PROGRAM_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF,
        api_name="experience",
        capability_name="program",
        endpoint_name="run_program",
        request_type_ref="aware_experience_service_dto.experience.program.RunProgramRequest",
        response_type_ref="aware_experience_service_dto.experience.program.RunProgramResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_experience__program__run_program,
    )
)


async def invoke_experience__program__submit_program_turn(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> SubmitProgramTurnResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = SubmitProgramTurnRequest.model_validate(request)
    return await typed_handler.experience.program.submit_program_turn(typed_request)


EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF: Final[str] = "experience.program.submit_program_turn"
EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF,
        api_name="experience",
        capability_name="program",
        endpoint_name="submit_program_turn",
        request_type_ref="aware_experience_service_dto.experience.program.SubmitProgramTurnRequest",
        response_type_ref="aware_experience_service_dto.experience.program.SubmitProgramTurnResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_experience__program__submit_program_turn,
    )
)


async def invoke_experience__record_experience_view_invocation_action__record_experience_view_invocation_action(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RecordExperienceViewInvocationActionResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = RecordExperienceViewInvocationActionRequest.model_validate(request)
    return await typed_handler.experience.record_experience_view_invocation_action.record_experience_view_invocation_action(
        typed_request
    )


EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF: Final[
    str
] = "experience.record_experience_view_invocation_action.record_experience_view_invocation_action"
EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
    api_name="experience",
    capability_name="record_experience_view_invocation_action",
    endpoint_name="record_experience_view_invocation_action",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.RecordExperienceViewInvocationActionRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.RecordExperienceViewInvocationActionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__record_experience_view_invocation_action__record_experience_view_invocation_action,
)


async def invoke_experience__request_experience_layout_transition__request_experience_layout_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RequestExperienceLayoutTransitionResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = RequestExperienceLayoutTransitionRequest.model_validate(request)
    return await typed_handler.experience.request_experience_layout_transition.request_experience_layout_transition(
        typed_request
    )


EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "experience.request_experience_layout_transition.request_experience_layout_transition"
)
EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF,
    api_name="experience",
    capability_name="request_experience_layout_transition",
    endpoint_name="request_experience_layout_transition",
    request_type_ref="aware_experience_service_dto.experience.layout_transition.RequestExperienceLayoutTransitionRequest",
    response_type_ref="aware_experience_service_dto.experience.layout_transition.RequestExperienceLayoutTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__request_experience_layout_transition__request_experience_layout_transition,
)


async def invoke_experience__resolve_experience_invocation_action_role_policy__resolve_experience_invocation_action_role_policy(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveExperienceInvocationActionRolePolicyResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ResolveExperienceInvocationActionRolePolicyRequest.model_validate(request)
    return await typed_handler.experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy(
        typed_request
    )


EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF: Final[
    str
] = "experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy"
EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF,
    api_name="experience",
    capability_name="resolve_experience_invocation_action_role_policy",
    endpoint_name="resolve_experience_invocation_action_role_policy",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.ResolveExperienceInvocationActionRolePolicyRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.ResolveExperienceInvocationActionRolePolicyResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__resolve_experience_invocation_action_role_policy__resolve_experience_invocation_action_role_policy,
)


async def invoke_experience__resolve_experience_thread_layout_intent__resolve_experience_thread_layout_intent(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveExperienceThreadLayoutIntentResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ResolveExperienceThreadLayoutIntentRequest.model_validate(request)
    return (
        await typed_handler.experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent(
            typed_request
        )
    )


EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF: Final[
    str
] = "experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent"
EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF,
    api_name="experience",
    capability_name="resolve_experience_thread_layout_intent",
    endpoint_name="resolve_experience_thread_layout_intent",
    request_type_ref="aware_experience_service_dto.experience.thread_layout_resolution.ResolveExperienceThreadLayoutIntentRequest",
    response_type_ref="aware_experience_service_dto.experience.thread_layout_resolution.ResolveExperienceThreadLayoutIntentResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__resolve_experience_thread_layout_intent__resolve_experience_thread_layout_intent,
)


async def invoke_experience__session_context__resolve_experience_session_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveExperienceSessionContextResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ResolveExperienceSessionContextRequest.model_validate(request)
    return await typed_handler.experience.session_context.resolve_experience_session_context(typed_request)


EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF: Final[str] = (
    "experience.session_context.resolve_experience_session_context"
)
EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF,
    api_name="experience",
    capability_name="session_context",
    endpoint_name="resolve_experience_session_context",
    request_type_ref="aware_experience_service_dto.experience.session_context.ResolveExperienceSessionContextRequest",
    response_type_ref="aware_experience_service_dto.experience.session_context.ResolveExperienceSessionContextResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__session_context__resolve_experience_session_context,
)


async def invoke_experience__session_handoff__ensure_experience_session_handoff(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EnsureExperienceSessionHandoffResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = EnsureExperienceSessionHandoffRequest.model_validate(request)
    return await typed_handler.experience.session_handoff.ensure_experience_session_handoff(typed_request)


EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF: Final[str] = (
    "experience.session_handoff.ensure_experience_session_handoff"
)
EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF,
    api_name="experience",
    capability_name="session_handoff",
    endpoint_name="ensure_experience_session_handoff",
    request_type_ref="aware_experience_service_dto.experience.session_handoff.EnsureExperienceSessionHandoffRequest",
    response_type_ref="aware_experience_service_dto.experience.session_handoff.EnsureExperienceSessionHandoffResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__session_handoff__ensure_experience_session_handoff,
)


async def invoke_experience__session_handoff__get_experience_session_handoff_status(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetExperienceSessionHandoffStatusResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = GetExperienceSessionHandoffStatusRequest.model_validate(request)
    return await typed_handler.experience.session_handoff.get_experience_session_handoff_status(typed_request)


EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF: Final[str] = (
    "experience.session_handoff.get_experience_session_handoff_status"
)
EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF,
    api_name="experience",
    capability_name="session_handoff",
    endpoint_name="get_experience_session_handoff_status",
    request_type_ref="aware_experience_service_dto.experience.session_handoff.GetExperienceSessionHandoffStatusRequest",
    response_type_ref="aware_experience_service_dto.experience.session_handoff.GetExperienceSessionHandoffStatusResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__session_handoff__get_experience_session_handoff_status,
)


async def invoke_experience__session_view_frame__resolve_experience_session_view_frame(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveExperienceSessionViewFrameResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = ResolveExperienceSessionViewFrameRequest.model_validate(request)
    return await typed_handler.experience.session_view_frame.resolve_experience_session_view_frame(typed_request)


EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF: Final[str] = (
    "experience.session_view_frame.resolve_experience_session_view_frame"
)
EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF,
    api_name="experience",
    capability_name="session_view_frame",
    endpoint_name="resolve_experience_session_view_frame",
    request_type_ref="aware_experience_service_dto.experience.session_view_frame.ResolveExperienceSessionViewFrameRequest",
    response_type_ref="aware_experience_service_dto.experience.session_view_frame.ResolveExperienceSessionViewFrameResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__session_view_frame__resolve_experience_session_view_frame,
)


async def invoke_experience__start_experience_session__start_experience_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> StartExperienceSessionResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = StartExperienceSessionRequest.model_validate(request)
    return await typed_handler.experience.start_experience_session.start_experience_session(typed_request)


EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF: Final[str] = (
    "experience.start_experience_session.start_experience_session"
)
EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF,
    api_name="experience",
    capability_name="start_experience_session",
    endpoint_name="start_experience_session",
    request_type_ref="aware_experience_service_dto.experience.session_commit.StartExperienceSessionRequest",
    response_type_ref="aware_experience_service_dto.experience.session_commit.StartExperienceSessionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_experience__start_experience_session__start_experience_session,
)

ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent: TypeAlias = (
    ExperienceSectionGraphBindingStateEvent
)


async def invoke_experience__watch_experience_section_graph_bindings__watch_experience_section_graph_bindings(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> WatchExperienceSectionGraphBindingsResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = WatchExperienceSectionGraphBindingsRequest.model_validate(request)
    return (
        await typed_handler.experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings(
            typed_request
        )
    )


def stream_invoke_experience__watch_experience_section_graph_bindings__watch_experience_section_graph_bindings(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent]:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = WatchExperienceSectionGraphBindingsRequest.model_validate(request)
    _ = execution
    return (
        typed_handler.experience.watch_experience_section_graph_bindings.stream_watch_experience_section_graph_bindings(
            typed_request
        )
    )


EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF: Final[
    str
] = "experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings"
EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF,
    api_name="experience",
    capability_name="watch_experience_section_graph_bindings",
    endpoint_name="watch_experience_section_graph_bindings",
    request_type_ref="aware_experience_service_dto.experience.section_graph_binding.WatchExperienceSectionGraphBindingsRequest",
    response_type_ref="aware_experience_service_dto.experience.section_graph_binding.WatchExperienceSectionGraphBindingsResponse",
    stream_event_type_refs=(
        "aware_experience_service_dto.experience.section_graph_binding.ExperienceSectionGraphBindingStateEvent",
    ),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=stream_invoke_experience__watch_experience_section_graph_bindings__watch_experience_section_graph_bindings,
    fulfillment_bindings=(),
    invoke=invoke_experience__watch_experience_section_graph_bindings__watch_experience_section_graph_bindings,
)

ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent: TypeAlias = ExperienceViewStateEvent


async def invoke_experience__watch_experience_view_state__watch_experience_view_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> WatchExperienceViewStateResponse:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = WatchExperienceViewStateRequest.model_validate(request)
    return await typed_handler.experience.watch_experience_view_state.watch_experience_view_state(typed_request)


def stream_invoke_experience__watch_experience_view_state__watch_experience_view_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent]:
    typed_handler = cast(AwareExperienceServiceProtocol, handler)
    typed_request = WatchExperienceViewStateRequest.model_validate(request)
    _ = execution
    return typed_handler.experience.watch_experience_view_state.stream_watch_experience_view_state(typed_request)


EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF: Final[str] = (
    "experience.watch_experience_view_state.watch_experience_view_state"
)
EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF,
    api_name="experience",
    capability_name="watch_experience_view_state",
    endpoint_name="watch_experience_view_state",
    request_type_ref="aware_experience_service_dto.experience.view_state.WatchExperienceViewStateRequest",
    response_type_ref="aware_experience_service_dto.experience.view_state.WatchExperienceViewStateResponse",
    stream_event_type_refs=("aware_experience_service_dto.experience.view_state.ExperienceViewStateEvent",),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=stream_invoke_experience__watch_experience_view_state__watch_experience_view_state,
    fulfillment_bindings=(),
    invoke=invoke_experience__watch_experience_view_state__watch_experience_view_state,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF: EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_PROTOCOL_BINDING,
    EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF: EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_PROTOCOL_BINDING,
    EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF: EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_PROTOCOL_BINDING,
    EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF: EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_PROTOCOL_BINDING,
    EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF: EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_PROTOCOL_BINDING,
    EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF: EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_PROTOCOL_BINDING,
    EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF: EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_PROTOCOL_BINDING,
    EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF: EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_PROTOCOL_BINDING,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF: EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_PROTOCOL_BINDING,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF: EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_PROTOCOL_BINDING,
    EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF: EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_PROTOCOL_BINDING,
    EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF: EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_PROTOCOL_BINDING,
    EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF: EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_PROTOCOL_BINDING,
    EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF: EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_PROTOCOL_BINDING,
    EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF: EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_PROTOCOL_BINDING,
    EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF: EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_PROTOCOL_BINDING,
    EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF: EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_PROTOCOL_BINDING,
    EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF: EXPERIENCE__PROGRAM__RUN_PROGRAM_PROTOCOL_BINDING,
    EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF: EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_PROTOCOL_BINDING,
    EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF: EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_PROTOCOL_BINDING,
    EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF: EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_PROTOCOL_BINDING,
    EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF: EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_PROTOCOL_BINDING,
    EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF: EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_PROTOCOL_BINDING,
    EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF: EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_PROTOCOL_BINDING,
    EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF: EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_PROTOCOL_BINDING,
    EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF: EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_PROTOCOL_BINDING,
    EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF: EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_PROTOCOL_BINDING,
    EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF: EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_PROTOCOL_BINDING,
    EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF: EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_PROTOCOL_BINDING,
    EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF: EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_PROTOCOL_BINDING,
}


class ExperienceActivateExperienceLayoutGraphBindingCapabilityServiceProtocol(Protocol):

    async def activate_experience_layout_graph_binding(
        self, request: ActivateExperienceLayoutGraphBindingRequest
    ) -> ActivateExperienceLayoutGraphBindingResponse: ...


class ExperienceActivateExperienceSectionGraphBindingCapabilityServiceProtocol(Protocol):

    async def activate_experience_section_graph_binding(
        self, request: ActivateExperienceSectionGraphBindingRequest
    ) -> ActivateExperienceSectionGraphBindingResponse: ...


class ExperienceActorAdmissionCapabilityServiceProtocol(Protocol):

    async def admit_experience_actor_config(
        self, request: AdmitExperienceActorConfigRequest
    ) -> AdmitExperienceActorConfigResponse: ...


class ExperienceApplyExperienceViewEventTransitionCapabilityServiceProtocol(Protocol):

    async def apply_experience_view_event_transition(
        self, request: ApplyExperienceViewEventTransitionRequest
    ) -> ApplyExperienceViewEventTransitionResponse: ...


class ExperienceDescribeExperienceSessionCapabilityServiceProtocol(Protocol):

    async def describe_experience_session(
        self, request: DescribeExperienceSessionRequest
    ) -> DescribeExperienceSessionResponse: ...


class ExperienceEnvironmentProfileCapabilityServiceProtocol(Protocol):

    async def apply_experience_environment_profile_programs(
        self, request: ApplyExperienceEnvironmentProfileProgramsRequest
    ) -> ApplyExperienceEnvironmentProfileProgramsResponse: ...

    async def provision_experience_environment_profile(
        self, request: ProvisionExperienceEnvironmentProfileRequest
    ) -> ProvisionExperienceEnvironmentProfileResponse: ...

    async def upsert_experience_environment_profile(
        self, request: UpsertExperienceEnvironmentProfileRequest
    ) -> UpsertExperienceEnvironmentProfileResponse: ...


class ExperienceGetExperienceLayoutGraphBindingCatalogCapabilityServiceProtocol(Protocol):

    async def get_experience_layout_graph_binding_catalog(
        self, request: GetExperienceLayoutGraphBindingCatalogRequest
    ) -> GetExperienceLayoutGraphBindingCatalogResponse: ...


class ExperienceGetExperienceLayoutGraphBindingStateCapabilityServiceProtocol(Protocol):

    async def get_experience_layout_graph_binding_state(
        self, request: GetExperienceLayoutGraphBindingStateRequest
    ) -> GetExperienceLayoutGraphBindingStateResponse: ...


class ExperienceGetExperienceSectionGraphBindingCatalogCapabilityServiceProtocol(Protocol):

    async def get_experience_section_graph_binding_catalog(
        self, request: GetExperienceSectionGraphBindingCatalogRequest
    ) -> GetExperienceSectionGraphBindingCatalogResponse: ...


class ExperienceGetExperienceSectionGraphBindingStateCapabilityServiceProtocol(Protocol):

    async def get_experience_section_graph_binding_state(
        self, request: GetExperienceSectionGraphBindingStateRequest
    ) -> GetExperienceSectionGraphBindingStateResponse: ...


class ExperienceInvokeExperienceViewInvocationActionCapabilityServiceProtocol(Protocol):

    async def invoke_experience_view_invocation_action(
        self, request: InvokeExperienceViewInvocationActionRequest
    ) -> InvokeExperienceViewInvocationActionResponse: ...


class ExperienceMountExperienceSessionProfileCapabilityServiceProtocol(Protocol):

    async def mount_experience_session_profile(
        self, request: MountExperienceSessionProfileRequest
    ) -> MountExperienceSessionProfileResponse: ...


class ExperiencePackageMaterializationCapabilityServiceProtocol(Protocol):

    async def resolve_experience_package_projection_ownership(
        self, request: ResolveExperiencePackageProjectionOwnershipRequest
    ) -> ResolveExperiencePackageProjectionOwnershipResponse: ...


class ExperienceProgramCapabilityServiceProtocol(Protocol):

    async def apply_program_ref(self, request: ApplyProgramRefRequest) -> ApplyProgramRefResponse: ...

    async def get_turn_execution(self, request: GetTurnExecutionRequest) -> GetTurnExecutionResponse: ...

    async def run_program(self, request: RunProgramRequest) -> RunProgramResponse: ...

    async def submit_program_turn(self, request: SubmitProgramTurnRequest) -> SubmitProgramTurnResponse: ...


class ExperienceRecordExperienceViewInvocationActionCapabilityServiceProtocol(Protocol):

    async def record_experience_view_invocation_action(
        self, request: RecordExperienceViewInvocationActionRequest
    ) -> RecordExperienceViewInvocationActionResponse: ...


class ExperienceRequestExperienceLayoutTransitionCapabilityServiceProtocol(Protocol):

    async def request_experience_layout_transition(
        self, request: RequestExperienceLayoutTransitionRequest
    ) -> RequestExperienceLayoutTransitionResponse: ...


class ExperienceResolveExperienceInvocationActionRolePolicyCapabilityServiceProtocol(Protocol):

    async def resolve_experience_invocation_action_role_policy(
        self, request: ResolveExperienceInvocationActionRolePolicyRequest
    ) -> ResolveExperienceInvocationActionRolePolicyResponse: ...


class ExperienceResolveExperienceThreadLayoutIntentCapabilityServiceProtocol(Protocol):

    async def resolve_experience_thread_layout_intent(
        self, request: ResolveExperienceThreadLayoutIntentRequest
    ) -> ResolveExperienceThreadLayoutIntentResponse: ...


class ExperienceSessionContextCapabilityServiceProtocol(Protocol):

    async def resolve_experience_session_context(
        self, request: ResolveExperienceSessionContextRequest
    ) -> ResolveExperienceSessionContextResponse: ...


class ExperienceSessionHandoffCapabilityServiceProtocol(Protocol):

    async def ensure_experience_session_handoff(
        self, request: EnsureExperienceSessionHandoffRequest
    ) -> EnsureExperienceSessionHandoffResponse: ...

    async def get_experience_session_handoff_status(
        self, request: GetExperienceSessionHandoffStatusRequest
    ) -> GetExperienceSessionHandoffStatusResponse: ...


class ExperienceSessionViewFrameCapabilityServiceProtocol(Protocol):

    async def resolve_experience_session_view_frame(
        self, request: ResolveExperienceSessionViewFrameRequest
    ) -> ResolveExperienceSessionViewFrameResponse: ...


class ExperienceStartExperienceSessionCapabilityServiceProtocol(Protocol):

    async def start_experience_session(
        self, request: StartExperienceSessionRequest
    ) -> StartExperienceSessionResponse: ...


class ExperienceWatchExperienceSectionGraphBindingsCapabilityServiceProtocol(Protocol):

    async def watch_experience_section_graph_bindings(
        self, request: WatchExperienceSectionGraphBindingsRequest
    ) -> WatchExperienceSectionGraphBindingsResponse: ...

    def stream_watch_experience_section_graph_bindings(
        self, request: WatchExperienceSectionGraphBindingsRequest
    ) -> AsyncIterator[ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent]: ...


class ExperienceWatchExperienceViewStateCapabilityServiceProtocol(Protocol):

    async def watch_experience_view_state(
        self, request: WatchExperienceViewStateRequest
    ) -> WatchExperienceViewStateResponse: ...

    def stream_watch_experience_view_state(
        self, request: WatchExperienceViewStateRequest
    ) -> AsyncIterator[ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent]: ...


class ExperienceApiServiceProtocol(Protocol):
    activate_experience_layout_graph_binding: ExperienceActivateExperienceLayoutGraphBindingCapabilityServiceProtocol
    activate_experience_section_graph_binding: ExperienceActivateExperienceSectionGraphBindingCapabilityServiceProtocol
    actor_admission: ExperienceActorAdmissionCapabilityServiceProtocol
    apply_experience_view_event_transition: ExperienceApplyExperienceViewEventTransitionCapabilityServiceProtocol
    describe_experience_session: ExperienceDescribeExperienceSessionCapabilityServiceProtocol
    environment_profile: ExperienceEnvironmentProfileCapabilityServiceProtocol
    get_experience_layout_graph_binding_catalog: (
        ExperienceGetExperienceLayoutGraphBindingCatalogCapabilityServiceProtocol
    )
    get_experience_layout_graph_binding_state: ExperienceGetExperienceLayoutGraphBindingStateCapabilityServiceProtocol
    get_experience_section_graph_binding_catalog: (
        ExperienceGetExperienceSectionGraphBindingCatalogCapabilityServiceProtocol
    )
    get_experience_section_graph_binding_state: ExperienceGetExperienceSectionGraphBindingStateCapabilityServiceProtocol
    invoke_experience_view_invocation_action: ExperienceInvokeExperienceViewInvocationActionCapabilityServiceProtocol
    mount_experience_session_profile: ExperienceMountExperienceSessionProfileCapabilityServiceProtocol
    package_materialization: ExperiencePackageMaterializationCapabilityServiceProtocol
    program: ExperienceProgramCapabilityServiceProtocol
    record_experience_view_invocation_action: ExperienceRecordExperienceViewInvocationActionCapabilityServiceProtocol
    request_experience_layout_transition: ExperienceRequestExperienceLayoutTransitionCapabilityServiceProtocol
    resolve_experience_invocation_action_role_policy: (
        ExperienceResolveExperienceInvocationActionRolePolicyCapabilityServiceProtocol
    )
    resolve_experience_thread_layout_intent: ExperienceResolveExperienceThreadLayoutIntentCapabilityServiceProtocol
    session_context: ExperienceSessionContextCapabilityServiceProtocol
    session_handoff: ExperienceSessionHandoffCapabilityServiceProtocol
    session_view_frame: ExperienceSessionViewFrameCapabilityServiceProtocol
    start_experience_session: ExperienceStartExperienceSessionCapabilityServiceProtocol
    watch_experience_section_graph_bindings: ExperienceWatchExperienceSectionGraphBindingsCapabilityServiceProtocol
    watch_experience_view_state: ExperienceWatchExperienceViewStateCapabilityServiceProtocol


class AwareExperienceServiceProtocol(Protocol):
    experience: ExperienceApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:9af519c3ab11870bab318e192e1e780b38419b0270dfa2b5f84f954bb5136f92",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 120,'
    '  "sections": ['
    "    {"
    '      "line_count": 29,'
    '      "rendered_text_digest": "sha256:a390df67ce3204162f2badb440409cd9a805b933e8f8bd7e21ce5ad0faa30831",'
    '      "section_key": "api.service_protocol.module_prelude",'
    '      "section_kind": "service_protocol_module_prelude",'
    '      "section_order": 0'
    "    },"
    "    {"
    '      "line_count": 59,'
    '      "rendered_text_digest": "sha256:4b2f83676760964f04df5a2dfd6a8153e0c286051f2d85dd83b8e2e933b411d7",'
    '      "section_key": "api.service_protocol.runtime_support",'
    '      "section_kind": "service_protocol_runtime_support",'
    '      "section_order": 1'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.actor_admission.admit_experience_actor_config",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.apply_experience_view_event_transition.apply_experience_view_event_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.describe_experience_session.describe_experience_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.environment_profile.apply_experience_environment_profile_programs",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.environment_profile.provision_experience_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.environment_profile.upsert_experience_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.mount_experience_session_profile.mount_experience_session_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.package_materialization.resolve_experience_package_projection_ownership",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.program.apply_program_ref",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.program.get_turn_execution",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.program.run_program",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.program.submit_program_turn",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.record_experience_view_invocation_action.record_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.request_experience_layout_transition.request_experience_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.session_context.resolve_experience_session_context",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.session_handoff.ensure_experience_session_handoff",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.session_handoff.get_experience_session_handoff_status",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.session_view_frame.resolve_experience_session_view_frame",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.start_experience_session.start_experience_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:experience.watch_experience_view_state.watch_experience_view_state",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:920595aecb0450f271f431818c642a51991115ceab3fabd70c1b30b889988d10",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a6c458c7d2d8ca6dcb03527e456c1e2c8352314dfb10ece250c0ef293ae98dd8",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.activate_experience_layout_graph_binding.activate_experience_layout_graph_binding",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:94ccb248417ee840ea62d5d1ae7081d6a74bda262dc7a625b08fe1367c269de8",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:8e28d345a4e23dde89cb66338657aae46e4881f61f894bd52a53efedcf8f96f1",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.activate_experience_section_graph_binding.activate_experience_section_graph_binding",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1b668ffb661a79eb97183112ef0b842023f32afa9858cd5755f8a82d01fa96ed",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.actor_admission.admit_experience_actor_config",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5b73761b34c24b930d776fa76caab9ffbbad803d54ced48b18bc673507018013",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.actor_admission.admit_experience_actor_config",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:7728d9cbad1554c92b5af53d0b960ba54f5b634c0b658e0c2bc2cbc6dfe67af9",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.apply_experience_view_event_transition.apply_experience_view_event_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a5e8c552f5aae4be6bce2204138967eb491a38a992bed225efe407fb46f47ff9",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.apply_experience_view_event_transition.apply_experience_view_event_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:68e6a78156a0389707ab3e0b0a2fdf4ceec40b8312039ba96d7de6845e9d5406",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.describe_experience_session.describe_experience_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e0ad1a3c1355ff4dc379883232a8b1c3fe6ee7a53c2a9a9bb3e2e08278ad329f",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.describe_experience_session.describe_experience_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:dff66b3cb8a34917add67729894dba22ba0525a63fef107bf788ee11f1575987",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.environment_profile.apply_experience_environment_profile_programs",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6434b0d378948de0cc22efb5c148c2d212563e405926b2235c7c9e68f02a0ba5",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.environment_profile.apply_experience_environment_profile_programs",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:fe72ee18917d7cf395fb905bd9d487c756eb482670c183cf7003fcb6f9398ada",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.environment_profile.provision_experience_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:92305f55f7b93a336ab2461e877d1d751ab80f80598999101c305e4eeb7f6298",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.environment_profile.provision_experience_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a68ff8a410f001dc8fc95e6ca97e9026dce0db4fec6107927930cce74cebc1a6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.environment_profile.upsert_experience_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:4bdd96c196ad664a284af8e9b8d9de5add5185f522a6341ac0ef7f9ffc61e61f",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.environment_profile.upsert_experience_environment_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4f47c71651037dd719e0f8abda13da529f1a7c838ee829174ae5e46672b02884",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:90fa5b53af426ff68000344847faedce7cb7363e0aaec6aa2bf4c4eaeb9bb4c8",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.get_experience_layout_graph_binding_catalog.get_experience_layout_graph_binding_catalog",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:79b48a71b10aa2f537159566ba22cf3505f3027b437795d505ba324afa7349c2",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:374ffe3382b37693f8d78451a6ddaa8add11aefbac5b96ffa438a4206080aaec",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.get_experience_layout_graph_binding_state.get_experience_layout_graph_binding_state",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:07403bc5b7bbcb18039874493d3409e37c6a9647885abcaba45888f85c5030a6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:30807f78e83e58696aa69af45dd4538eddaef611247eb4fe3c0a6b54979a490c",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.get_experience_section_graph_binding_catalog.get_experience_section_graph_binding_catalog",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a15afc14c37ba785ac5b2a2b34e7901243b3f68a9d301a0402d29c98012a9088",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b3d922c2dc20128839f8f33ac9ecef9739ac31855f039b19d31782a096da9677",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.get_experience_section_graph_binding_state.get_experience_section_graph_binding_state",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:19df5a17c2bee6df80e142d70811e3c5eaaa21f539594ea4caa5a20c0c4401fc",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:46c717e9433389724395ba72f9686bcbcfed0723e09559fff004a5e894bd8fe8",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.invoke_experience_view_invocation_action.invoke_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 57'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ff26bec4f128c53e05686a16446579b7185233ce214039f1ca54fd0e40e7920d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.mount_experience_session_profile.mount_experience_session_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 58'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:b499ccba0811ac43f02398817f2f311e55ba2098b5f662656956720ca423d01e",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.mount_experience_session_profile.mount_experience_session_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 59'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4cccefe94ede2efa2b9a16a3b51b3a52707f7127e948a1b149405fb192a6594e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.package_materialization.resolve_experience_package_projection_ownership",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 60'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:8fdbd7bc22012a8d49cab656e733cb78c9c6837e62fd627d6f5a8c966a2c5eea",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.package_materialization.resolve_experience_package_projection_ownership",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 61'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:06ba5c4ace33d0a5dee060b409802ff96f22c6852785e283885b0b18ee31e3f1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.program.apply_program_ref",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 62'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5bab11dca9738f9c21c8a1641cac2881abc288fb5444d9a9d575eef948dea01f",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.program.apply_program_ref",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 63'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4493421147095e71e0ae0eb0431c8193a4f2fe8a0da6f5b362ad4849d39f921c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.program.get_turn_execution",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 64'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d42632825bdd467c290ff633564572561bf8a5f0f7ea150c9d2e7c94ff1e3d8d",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.program.get_turn_execution",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 65'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a90071290b41322bd08574b71f706733ed9dfe1d70835b1e79a066e6020cf835",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.program.run_program",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 66'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6b1aebcb43a5ce1e5eebefcb645b9d59c6b31c3a41aae1544af553bda7fc542d",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.program.run_program",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 67'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:43103503b05c23179befc3e7bfd502b52841090e7c6cb17bf1c1369206bab85b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.program.submit_program_turn",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 68'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c8ec4c9e10c46a58a9cde3e112d1361192d34f5a377ce5768ffe1f295ea6d72a",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.program.submit_program_turn",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 69'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d6959c0b9dbe2fb8914e636e4a435c3656ae45bcd4725379055ac0f520b0d08d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.record_experience_view_invocation_action.record_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 70'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:626561f5b1a13aefa2d175963e6a8247ed19268634f392cf428f98368a979140",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.record_experience_view_invocation_action.record_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 71'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:cab91a8be4d5eb719089e9f532965ff4a0861003a5c1734b296e325082656242",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.request_experience_layout_transition.request_experience_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 72'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:28a7c805459a46c27bb230c1aa34dd79e19a5a9f6e615c244d663e2b710b214a",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.request_experience_layout_transition.request_experience_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 73'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4720f1c6a4ab2be359b421f67e9f377761f69bd88b6035fa9298e2dd91eea51b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 74'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:cf8bc164904ed8f3ec23fe3e76d0ba722318baa1296fa0c49bcc76d3c46fa19b",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.resolve_experience_invocation_action_role_policy.resolve_experience_invocation_action_role_policy",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 75'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:0acbc85858f1a3a629ad308e2fc1610ff5b4939b7161f47c35d909a0ec8d27f4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 76'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:1c8e354757dc71f2a33798a36c870f997c79a4a24f7c54fb0e06150b9e8157b5",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.resolve_experience_thread_layout_intent.resolve_experience_thread_layout_intent",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 77'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:bc2410453b787f58a48578d9f4ca45b5f645223643764888f87b09680b19a79c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.session_context.resolve_experience_session_context",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 78'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:8f1fb1eba65c1f9e3ae592cde163f56c7b4f90d9860fff8c4d9c709b07442706",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.session_context.resolve_experience_session_context",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 79'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:3b1343018b02fc747bf9e4c30f616e558b520b1e6d5e3ccdbc6eb7d3faecfd87",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.session_handoff.ensure_experience_session_handoff",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 80'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:53c624ab5a946cd60bc4dd0e5abe440f5c33306174d985a13a8055db0661fff4",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.session_handoff.ensure_experience_session_handoff",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 81'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:7d9523d557f25f705f59393e3a177b06ee84cd8bdde07138349f71be28110ad7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.session_handoff.get_experience_session_handoff_status",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 82'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5678eb576a5252c4b67061006b346963fae6ef4f4d3816bb8e7afc1d142b96e8",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.session_handoff.get_experience_session_handoff_status",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 83'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e2902bb1d86b784f12e170207ca160e86cefecef8c9ce1f17e84a5501755f285",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.session_view_frame.resolve_experience_session_view_frame",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 84'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:dd7e3d808f8a974682e7781f11d8149c3b8155da3959248727233f28e34d0833",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.session_view_frame.resolve_experience_session_view_frame",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 85'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:16ee59eb38d06539c0a77d8edde4c3d80566746de9b2967e6d14606b93284932",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.start_experience_session.start_experience_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 86'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:62419b287ac14df6e2cd49cd9f28bc2571d68aba4b362eace4a88025ba4d8099",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.start_experience_session.start_experience_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 87'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:485faff71cc694da99c3e803ce5791d2993717028c78b522eb8f54d46b751f0b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 88'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:3931e97ba61a73d247620ae7026b99fe56b708ca8dbef4d5ff660fe107174d54",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.watch_experience_section_graph_bindings.watch_experience_section_graph_bindings",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 89'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:287e7f956472cf9ca2b23b4a96934ed0be89495431868f8c5d99c2b02e99d18e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:experience.watch_experience_view_state.watch_experience_view_state",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 90'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:b67939988f6b39a4b0cb53ca2e110b8bc13e075353ae6d31d7ba8acedbf5d01b",'
    '      "section_key": "api.service_protocol.endpoint_binding:experience.watch_experience_view_state.watch_experience_view_state",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 91'
    "    },"
    "    {"
    '      "line_count": 33,'
    '      "rendered_text_digest": "sha256:b523eba9d589bdc71732dd2cdb63acaec5e018be423cc4d4b01724d74c985ae6",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 92'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:a5d0bb73fa2e3782b19e3960594bb26c16d031b23b29370f3b53d5278d462eb0",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.activate_experience_layout_graph_binding",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 93'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:394cac983a8378f307125c7905dfaebe08423f522b7236c3df700b1db7eaf307",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.activate_experience_section_graph_binding",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 94'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:c59d545721b98501e727fa8105c5288428ab24af653504f917992a8f4ebf10f0",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.actor_admission",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 95'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:1801afb128342cf51a93747c89cc054b8a4bc25da58b41f69c2741a56d724907",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.apply_experience_view_event_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 96'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:b2b0e21ed9c068d21dcae6ad58552c6d9e11bcd90407f0a0b9f87790c131ec04",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.describe_experience_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 97'
    "    },"
    "    {"
    '      "line_count": 8,'
    '      "rendered_text_digest": "sha256:6a687cc082f1cb5b1d5b9a93d5d1487d9bb1b85736e235454a28702e800a5537",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.environment_profile",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 98'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ea10ff9f5ac59a8528542cbbb6f13557607dde74b8061f97bed4759ca4a386af",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.get_experience_layout_graph_binding_catalog",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 99'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:83d267dec14146b3d8a0121b5c0827acc2b992a8a3b9beeb27e562bf35b2b8c6",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.get_experience_layout_graph_binding_state",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 100'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:674a6db54cec78eeef97d9a8b4eefbb69ac9c8f006dd52366d7754607d23470f",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.get_experience_section_graph_binding_catalog",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 101'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:2f6c307b932b5bfc58774c5c942a2343c874d0b7503f1e7e935d16d19f945092",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.get_experience_section_graph_binding_state",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 102'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:a33d6e2b4faf6c71dc081e53496917e5e21c93067c6e3c7c45e31dd2c1ecd28d",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.invoke_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 103'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:a15a9dd08c9cf5afe9fdcb72fc347fefbff9f9bc619944d1cf224f02612eec67",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.mount_experience_session_profile",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 104'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e7424ea71fa8e233c3d97205eb6d1ca40c832efde66ac2de161b7d804cba1318",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.package_materialization",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 105'
    "    },"
    "    {"
    '      "line_count": 10,'
    '      "rendered_text_digest": "sha256:35e3272a80017d7de3b12e43625341a318553147966c64f707db78d25d69bd51",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.program",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 106'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:78799e3ef51d6fb2d24cac8977c38289701f918f11e5875741857256b158a15c",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.record_experience_view_invocation_action",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 107'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:2af4df6ca799159d5b8977feda59c14095a3cd7930bb1898148345bd907e6b52",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.request_experience_layout_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 108'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:b5d272cf6a1752fdc1f6bc476e30354418079658c56430837e85063fd328883e",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.resolve_experience_invocation_action_role_policy",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 109'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:872af987db49bedeeea53d761997d46d1c62c20beedd9701a47877359fc98729",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.resolve_experience_thread_layout_intent",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 110'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:8d2b211c3b54ac330c73bbb8763d14311c02df6d33654e36295aa959c63a236e",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.session_context",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 111'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:45ce197a55e5944f0b389bdebf9ddb6f237ae47f42193262aa6c9e9e11dd88ef",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.session_handoff",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 112'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:003434c4e7d21d9b03b23b5bf4570abc81844aad585d3ef9f69da15958540666",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.session_view_frame",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 113'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:c57e1acedf1a852eaa66bba56f163170bead6025d36782fb05f343aeb00610a5",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.start_experience_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 114'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:a6fd8566add9cbdcabddf7804ca89bae165b169629f6817f98c8151d26bcfeba",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.watch_experience_section_graph_bindings",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 115'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:db73d3d986139007a8934a144e0e646ece7ea7f55130a966c0fa3932824a2253",'
    '      "section_key": "api.service_protocol.capability_protocol:experience.watch_experience_view_state",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 116'
    "    },"
    "    {"
    '      "line_count": 26,'
    '      "rendered_text_digest": "sha256:011286714d4352dabdaf994e65c8779e39bd33eec93ad2d159a3a2a3cee3c695",'
    '      "section_key": "api.service_protocol.api_protocol:experience",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 117'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:da7e370a10852cc6ea309feb3df227c29a8c9f0d87cfe0a853ae76a20978d1bf",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 118'
    "    },"
    "    {"
    '      "line_count": 134,'
    '      "rendered_text_digest": "sha256:15805f0ded28fd4737a5c8f51cc7ba234fa881e1f62b865cf12bbb368898c6a2",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 119'
    "    }"
    "  ],"
    '  "target_relpath": "protocols.py",'
    '  "text_digest_algorithm": "sha256"'
    "}"
)

__all__ = [
    "API_FQN_PREFIX",
    "API_PACKAGE_NAME",
    "ENDPOINT_BINDINGS",
    "PUBLIC_PACKAGE_IMPORT_ROOT",
    "SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON",
    "ServiceProtocolExecutionBackend",
    "ServiceProtocolExecutionFactory",
    "ServiceProtocolEndpointBinding",
    "ServiceProtocolFulfillmentBinding",
    "ServiceProtocolInvoker",
    "ServiceProtocolStreamInvoker",
    "AwareExperienceServiceProtocol",
    "ExperienceApiServiceProtocol",
    "ExperienceActivateExperienceLayoutGraphBindingCapabilityServiceProtocol",
    "ExperienceActivateExperienceSectionGraphBindingCapabilityServiceProtocol",
    "ExperienceActorAdmissionCapabilityServiceProtocol",
    "ExperienceApplyExperienceViewEventTransitionCapabilityServiceProtocol",
    "ExperienceDescribeExperienceSessionCapabilityServiceProtocol",
    "ExperienceEnvironmentProfileCapabilityServiceProtocol",
    "ExperienceGetExperienceLayoutGraphBindingCatalogCapabilityServiceProtocol",
    "ExperienceGetExperienceLayoutGraphBindingStateCapabilityServiceProtocol",
    "ExperienceGetExperienceSectionGraphBindingCatalogCapabilityServiceProtocol",
    "ExperienceGetExperienceSectionGraphBindingStateCapabilityServiceProtocol",
    "ExperienceInvokeExperienceViewInvocationActionCapabilityServiceProtocol",
    "ExperienceMountExperienceSessionProfileCapabilityServiceProtocol",
    "ExperiencePackageMaterializationCapabilityServiceProtocol",
    "ExperienceProgramCapabilityServiceProtocol",
    "ExperienceRecordExperienceViewInvocationActionCapabilityServiceProtocol",
    "ExperienceRequestExperienceLayoutTransitionCapabilityServiceProtocol",
    "ExperienceResolveExperienceInvocationActionRolePolicyCapabilityServiceProtocol",
    "ExperienceResolveExperienceThreadLayoutIntentCapabilityServiceProtocol",
    "ExperienceSessionContextCapabilityServiceProtocol",
    "ExperienceSessionHandoffCapabilityServiceProtocol",
    "ExperienceSessionViewFrameCapabilityServiceProtocol",
    "ExperienceStartExperienceSessionCapabilityServiceProtocol",
    "ExperienceWatchExperienceSectionGraphBindingsCapabilityServiceProtocol",
    "ExperienceWatchExperienceViewStateCapabilityServiceProtocol",
    "ExperienceWatchExperienceSectionGraphBindingsWatchExperienceSectionGraphBindingsStreamEvent",
    "ExperienceWatchExperienceViewStateWatchExperienceViewStateStreamEvent",
    "EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF",
    "EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_PROTOCOL_BINDING",
    "invoke_experience__activate_experience_layout_graph_binding__activate_experience_layout_graph_binding",
    "EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_ENDPOINT_REF",
    "EXPERIENCE__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING__ACTIVATE_EXPERIENCE_SECTION_GRAPH_BINDING_PROTOCOL_BINDING",
    "invoke_experience__activate_experience_section_graph_binding__activate_experience_section_graph_binding",
    "EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_ENDPOINT_REF",
    "EXPERIENCE__ACTOR_ADMISSION__ADMIT_EXPERIENCE_ACTOR_CONFIG_PROTOCOL_BINDING",
    "invoke_experience__actor_admission__admit_experience_actor_config",
    "EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF",
    "EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_PROTOCOL_BINDING",
    "invoke_experience__apply_experience_view_event_transition__apply_experience_view_event_transition",
    "EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_ENDPOINT_REF",
    "EXPERIENCE__DESCRIBE_EXPERIENCE_SESSION__DESCRIBE_EXPERIENCE_SESSION_PROTOCOL_BINDING",
    "invoke_experience__describe_experience_session__describe_experience_session",
    "EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_ENDPOINT_REF",
    "EXPERIENCE__ENVIRONMENT_PROFILE__APPLY_EXPERIENCE_ENVIRONMENT_PROFILE_PROGRAMS_PROTOCOL_BINDING",
    "invoke_experience__environment_profile__apply_experience_environment_profile_programs",
    "EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "EXPERIENCE__ENVIRONMENT_PROFILE__PROVISION_EXPERIENCE_ENVIRONMENT_PROFILE_PROTOCOL_BINDING",
    "invoke_experience__environment_profile__provision_experience_environment_profile",
    "EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_ENDPOINT_REF",
    "EXPERIENCE__ENVIRONMENT_PROFILE__UPSERT_EXPERIENCE_ENVIRONMENT_PROFILE_PROTOCOL_BINDING",
    "invoke_experience__environment_profile__upsert_experience_environment_profile",
    "EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_PROTOCOL_BINDING",
    "invoke_experience__get_experience_layout_graph_binding_catalog__get_experience_layout_graph_binding_catalog",
    "EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_PROTOCOL_BINDING",
    "invoke_experience__get_experience_layout_graph_binding_state__get_experience_layout_graph_binding_state",
    "EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_PROTOCOL_BINDING",
    "invoke_experience__get_experience_section_graph_binding_catalog__get_experience_section_graph_binding_catalog",
    "EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_ENDPOINT_REF",
    "EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_STATE_PROTOCOL_BINDING",
    "invoke_experience__get_experience_section_graph_binding_state__get_experience_section_graph_binding_state",
    "EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF",
    "EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_PROTOCOL_BINDING",
    "invoke_experience__invoke_experience_view_invocation_action__invoke_experience_view_invocation_action",
    "EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_ENDPOINT_REF",
    "EXPERIENCE__MOUNT_EXPERIENCE_SESSION_PROFILE__MOUNT_EXPERIENCE_SESSION_PROFILE_PROTOCOL_BINDING",
    "invoke_experience__mount_experience_session_profile__mount_experience_session_profile",
    "EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_ENDPOINT_REF",
    "EXPERIENCE__PACKAGE_MATERIALIZATION__RESOLVE_EXPERIENCE_PACKAGE_PROJECTION_OWNERSHIP_PROTOCOL_BINDING",
    "invoke_experience__package_materialization__resolve_experience_package_projection_ownership",
    "EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__APPLY_PROGRAM_REF_PROTOCOL_BINDING",
    "invoke_experience__program__apply_program_ref",
    "EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__GET_TURN_EXECUTION_PROTOCOL_BINDING",
    "invoke_experience__program__get_turn_execution",
    "EXPERIENCE__PROGRAM__RUN_PROGRAM_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__RUN_PROGRAM_PROTOCOL_BINDING",
    "invoke_experience__program__run_program",
    "EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_ENDPOINT_REF",
    "EXPERIENCE__PROGRAM__SUBMIT_PROGRAM_TURN_PROTOCOL_BINDING",
    "invoke_experience__program__submit_program_turn",
    "EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF",
    "EXPERIENCE__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION__RECORD_EXPERIENCE_VIEW_INVOCATION_ACTION_PROTOCOL_BINDING",
    "invoke_experience__record_experience_view_invocation_action__record_experience_view_invocation_action",
    "EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_ENDPOINT_REF",
    "EXPERIENCE__REQUEST_EXPERIENCE_LAYOUT_TRANSITION__REQUEST_EXPERIENCE_LAYOUT_TRANSITION_PROTOCOL_BINDING",
    "invoke_experience__request_experience_layout_transition__request_experience_layout_transition",
    "EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_ENDPOINT_REF",
    "EXPERIENCE__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY__RESOLVE_EXPERIENCE_INVOCATION_ACTION_ROLE_POLICY_PROTOCOL_BINDING",
    "invoke_experience__resolve_experience_invocation_action_role_policy__resolve_experience_invocation_action_role_policy",
    "EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_ENDPOINT_REF",
    "EXPERIENCE__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT__RESOLVE_EXPERIENCE_THREAD_LAYOUT_INTENT_PROTOCOL_BINDING",
    "invoke_experience__resolve_experience_thread_layout_intent__resolve_experience_thread_layout_intent",
    "EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF",
    "EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_PROTOCOL_BINDING",
    "invoke_experience__session_context__resolve_experience_session_context",
    "EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF",
    "EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_PROTOCOL_BINDING",
    "invoke_experience__session_handoff__ensure_experience_session_handoff",
    "EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF",
    "EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_PROTOCOL_BINDING",
    "invoke_experience__session_handoff__get_experience_session_handoff_status",
    "EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF",
    "EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_PROTOCOL_BINDING",
    "invoke_experience__session_view_frame__resolve_experience_session_view_frame",
    "EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_ENDPOINT_REF",
    "EXPERIENCE__START_EXPERIENCE_SESSION__START_EXPERIENCE_SESSION_PROTOCOL_BINDING",
    "invoke_experience__start_experience_session__start_experience_session",
    "EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_ENDPOINT_REF",
    "EXPERIENCE__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS__WATCH_EXPERIENCE_SECTION_GRAPH_BINDINGS_PROTOCOL_BINDING",
    "invoke_experience__watch_experience_section_graph_bindings__watch_experience_section_graph_bindings",
    "stream_invoke_experience__watch_experience_section_graph_bindings__watch_experience_section_graph_bindings",
    "EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_ENDPOINT_REF",
    "EXPERIENCE__WATCH_EXPERIENCE_VIEW_STATE__WATCH_EXPERIENCE_VIEW_STATE_PROTOCOL_BINDING",
    "invoke_experience__watch_experience_view_state__watch_experience_view_state",
    "stream_invoke_experience__watch_experience_view_state__watch_experience_view_state",
]
