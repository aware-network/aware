# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionRequest,
    InterfaceActionResponse,
    InterfaceActivateRuntimeFocusRequest,
    InterfaceActivateRuntimeFocusResponse,
    InterfaceAdmitEnvironmentActorRequest,
    InterfaceAdmitEnvironmentActorResponse,
    InterfaceApiEventNotification,
    InterfaceApiStreamClosedNotification,
    InterfaceApplyAttentionLayoutTopologyTransitionRequest,
    InterfaceApplyAttentionLayoutTopologyTransitionResponse,
    InterfaceApplyAttentionLayoutTransitionRequest,
    InterfaceApplyAttentionLayoutTransitionResponse,
    InterfaceEnterAppScreenRequest,
    InterfaceEnterAppScreenResponse,
    InterfaceEnterEnvironmentRequest,
    InterfaceEnterEnvironmentResponse,
    InterfaceExperienceSessionMountRequest,
    InterfaceExperienceSessionMountResponse,
    InterfaceFollowRequest,
    InterfaceFollowResponse,
    InterfaceInvokeApiRequest,
    InterfaceInvokeApiResponse,
    InterfaceJoinEnvironmentSessionRequest,
    InterfaceJoinEnvironmentSessionResponse,
    InterfaceReportRendererCapabilitiesRequest,
    InterfaceReportRendererCapabilitiesResponse,
    InterfaceRequestWindowLayoutRequest,
    InterfaceRequestWindowLayoutResponse,
    InterfaceResolveExperienceLensRequest,
    InterfaceResolveExperienceLensResponse,
    InterfaceSelectEnvironmentNavigationTargetRequest,
    InterfaceSelectEnvironmentNavigationTargetResponse,
    InterfaceSelectProfileRequest,
    InterfaceSelectProfileResponse,
    InterfaceSelectRuntimeLayoutRequest,
    InterfaceSelectRuntimeLayoutResponse,
    InterfaceSelectStepRequest,
    InterfaceSelectStepResponse,
    InterfaceSessionDescribeRequest,
    InterfaceSessionDescribeResponse,
    InterfaceSessionStartRequest,
    InterfaceSessionStartResponse,
    InterfaceStateNotification,
    InterfaceStatusRequest,
    InterfaceStatusResponse,
    InterfaceStopRequest,
    InterfaceStopResponse,
    InterfaceStreamApiRequest,
    InterfaceStreamApiResponse,
    InterfaceSyncViewStateCursorRequest,
    InterfaceSyncViewStateCursorResponse,
    NamespaceEnsureRequest,
    NamespaceEnsureResponse,
    NamespaceListRequest,
    NamespaceListResponse,
    PingRequest,
    PingResponse,
)

API_PACKAGE_NAME: Final[str] = "interface-service-api"
API_FQN_PREFIX: Final[str] = "aware_interface_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_interface_service_api"


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


async def invoke_interface__activate_interface_runtime_focus__activate_interface_runtime_focus(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceActivateRuntimeFocusResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceActivateRuntimeFocusRequest.model_validate(request)
    return await typed_handler.interface.activate_interface_runtime_focus.activate_interface_runtime_focus(
        typed_request
    )


INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF: Final[str] = (
    "interface.activate_interface_runtime_focus.activate_interface_runtime_focus"
)
INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF,
    api_name="interface",
    capability_name="activate_interface_runtime_focus",
    endpoint_name="activate_interface_runtime_focus",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceActivateRuntimeFocusResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__activate_interface_runtime_focus__activate_interface_runtime_focus,
)


async def invoke_interface__admit_environment_actor__admit_environment_actor(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceAdmitEnvironmentActorResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceAdmitEnvironmentActorRequest.model_validate(request)
    return await typed_handler.interface.admit_environment_actor.admit_environment_actor(typed_request)


INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF: Final[str] = (
    "interface.admit_environment_actor.admit_environment_actor"
)
INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF,
        api_name="interface",
        capability_name="admit_environment_actor",
        endpoint_name="admit_environment_actor",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceAdmitEnvironmentActorResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__admit_environment_actor__admit_environment_actor,
    )
)


async def invoke_interface__admit_interface__admit_interface(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NamespaceEnsureResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = NamespaceEnsureRequest.model_validate(request)
    return await typed_handler.interface.admit_interface.admit_interface(typed_request)


INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF: Final[str] = "interface.admit_interface.admit_interface"
INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF,
        api_name="interface",
        capability_name="admit_interface",
        endpoint_name="admit_interface",
        request_type_ref="aware_interface_service_dto.comms.models.NamespaceEnsureRequest",
        response_type_ref="aware_interface_service_dto.comms.models.NamespaceEnsureResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__admit_interface__admit_interface,
    )
)


async def invoke_interface__apply_attention_layout_topology_transition__apply_attention_layout_topology_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceApplyAttentionLayoutTopologyTransitionResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceApplyAttentionLayoutTopologyTransitionRequest.model_validate(request)
    return await typed_handler.interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition(
        typed_request
    )


INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF: Final[
    str
] = "interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition"
INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_PROTOCOL_BINDING: (
    Final[ServiceProtocolEndpointBinding]
) = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
    api_name="interface",
    capability_name="apply_attention_layout_topology_transition",
    endpoint_name="apply_attention_layout_topology_transition",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTopologyTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__apply_attention_layout_topology_transition__apply_attention_layout_topology_transition,
)


async def invoke_interface__apply_attention_layout_transition__apply_attention_layout_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceApplyAttentionLayoutTransitionResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceApplyAttentionLayoutTransitionRequest.model_validate(request)
    return await typed_handler.interface.apply_attention_layout_transition.apply_attention_layout_transition(
        typed_request
    )


INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "interface.apply_attention_layout_transition.apply_attention_layout_transition"
)
INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF,
    api_name="interface",
    capability_name="apply_attention_layout_transition",
    endpoint_name="apply_attention_layout_transition",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceApplyAttentionLayoutTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__apply_attention_layout_transition__apply_attention_layout_transition,
)


async def invoke_interface__describe_interface_session__describe_interface_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceSessionDescribeResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceSessionDescribeRequest.model_validate(request)
    return await typed_handler.interface.describe_interface_session.describe_interface_session(typed_request)


INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.describe_interface_session.describe_interface_session"
)
INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF,
    api_name="interface",
    capability_name="describe_interface_session",
    endpoint_name="describe_interface_session",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceSessionDescribeRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceSessionDescribeResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__describe_interface_session__describe_interface_session,
)


async def invoke_interface__enter_app_screen__enter_app_screen(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceEnterAppScreenResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceEnterAppScreenRequest.model_validate(request)
    return await typed_handler.interface.enter_app_screen.enter_app_screen(typed_request)


INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF: Final[str] = "interface.enter_app_screen.enter_app_screen"
INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF,
        api_name="interface",
        capability_name="enter_app_screen",
        endpoint_name="enter_app_screen",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceEnterAppScreenRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceEnterAppScreenResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__enter_app_screen__enter_app_screen,
    )
)


async def invoke_interface__enter_environment__enter_environment(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceEnterEnvironmentResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceEnterEnvironmentRequest.model_validate(request)
    return await typed_handler.interface.enter_environment.enter_environment(typed_request)


INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF: Final[str] = (
    "interface.enter_environment.enter_environment"
)
INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF,
        api_name="interface",
        capability_name="enter_environment",
        endpoint_name="enter_environment",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceEnterEnvironmentResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__enter_environment__enter_environment,
    )
)


async def invoke_interface__get_interface_state__get_interface_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceStatusResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceStatusRequest.model_validate(request)
    return await typed_handler.interface.get_interface_state.get_interface_state(typed_request)


INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF: Final[str] = (
    "interface.get_interface_state.get_interface_state"
)
INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF,
        api_name="interface",
        capability_name="get_interface_state",
        endpoint_name="get_interface_state",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceStatusRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceStatusResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__get_interface_state__get_interface_state,
    )
)


async def invoke_interface__invoke_interface_api__invoke_interface_api(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceInvokeApiResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceInvokeApiRequest.model_validate(request)
    return await typed_handler.interface.invoke_interface_api.invoke_interface_api(typed_request)


INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF: Final[str] = (
    "interface.invoke_interface_api.invoke_interface_api"
)
INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF,
        api_name="interface",
        capability_name="invoke_interface_api",
        endpoint_name="invoke_interface_api",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceInvokeApiRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceInvokeApiResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__invoke_interface_api__invoke_interface_api,
    )
)


async def invoke_interface__join_environment_session__join_environment_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceJoinEnvironmentSessionResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceJoinEnvironmentSessionRequest.model_validate(request)
    return await typed_handler.interface.join_environment_session.join_environment_session(typed_request)


INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.join_environment_session.join_environment_session"
)
INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF,
    api_name="interface",
    capability_name="join_environment_session",
    endpoint_name="join_environment_session",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceJoinEnvironmentSessionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__join_environment_session__join_environment_session,
)


async def invoke_interface__list_interface_namespaces__list_interface_namespaces(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> NamespaceListResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = NamespaceListRequest.model_validate(request)
    return await typed_handler.interface.list_interface_namespaces.list_interface_namespaces(typed_request)


INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF: Final[str] = (
    "interface.list_interface_namespaces.list_interface_namespaces"
)
INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF,
    api_name="interface",
    capability_name="list_interface_namespaces",
    endpoint_name="list_interface_namespaces",
    request_type_ref="aware_interface_service_dto.comms.models.NamespaceListRequest",
    response_type_ref="aware_interface_service_dto.comms.models.NamespaceListResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__list_interface_namespaces__list_interface_namespaces,
)


async def invoke_interface__mount_interface_experience_session__mount_interface_experience_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceExperienceSessionMountResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceExperienceSessionMountRequest.model_validate(request)
    return await typed_handler.interface.mount_interface_experience_session.mount_interface_experience_session(
        typed_request
    )


INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.mount_interface_experience_session.mount_interface_experience_session"
)
INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF,
    api_name="interface",
    capability_name="mount_interface_experience_session",
    endpoint_name="mount_interface_experience_session",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceExperienceSessionMountResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__mount_interface_experience_session__mount_interface_experience_session,
)


async def invoke_interface__perform_interface_action__perform_interface_action(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceActionResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceActionRequest.model_validate(request)
    return await typed_handler.interface.perform_interface_action.perform_interface_action(typed_request)


INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF: Final[str] = (
    "interface.perform_interface_action.perform_interface_action"
)
INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF,
    api_name="interface",
    capability_name="perform_interface_action",
    endpoint_name="perform_interface_action",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceActionRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceActionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__perform_interface_action__perform_interface_action,
)


async def invoke_interface__ping_interface_host__ping_interface_host(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> PingResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = PingRequest.model_validate(request)
    return await typed_handler.interface.ping_interface_host.ping_interface_host(typed_request)


INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF: Final[str] = (
    "interface.ping_interface_host.ping_interface_host"
)
INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF,
        api_name="interface",
        capability_name="ping_interface_host",
        endpoint_name="ping_interface_host",
        request_type_ref="aware_interface_service_dto.comms.models.PingRequest",
        response_type_ref="aware_interface_service_dto.comms.models.PingResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__ping_interface_host__ping_interface_host,
    )
)


async def invoke_interface__report_renderer_capabilities__report_renderer_capabilities(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceReportRendererCapabilitiesResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceReportRendererCapabilitiesRequest.model_validate(request)
    return await typed_handler.interface.report_renderer_capabilities.report_renderer_capabilities(typed_request)


INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF: Final[str] = (
    "interface.report_renderer_capabilities.report_renderer_capabilities"
)
INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF,
    api_name="interface",
    capability_name="report_renderer_capabilities",
    endpoint_name="report_renderer_capabilities",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceReportRendererCapabilitiesResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__report_renderer_capabilities__report_renderer_capabilities,
)


async def invoke_interface__request_interface_window_layout__request_interface_window_layout(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceRequestWindowLayoutResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceRequestWindowLayoutRequest.model_validate(request)
    return await typed_handler.interface.request_interface_window_layout.request_interface_window_layout(typed_request)


INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF: Final[str] = (
    "interface.request_interface_window_layout.request_interface_window_layout"
)
INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF,
    api_name="interface",
    capability_name="request_interface_window_layout",
    endpoint_name="request_interface_window_layout",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceRequestWindowLayoutResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__request_interface_window_layout__request_interface_window_layout,
)


async def invoke_interface__resolve_experience_lens__resolve_experience_lens(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceResolveExperienceLensResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceResolveExperienceLensRequest.model_validate(request)
    return await typed_handler.interface.resolve_experience_lens.resolve_experience_lens(typed_request)


INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF: Final[str] = (
    "interface.resolve_experience_lens.resolve_experience_lens"
)
INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF,
        api_name="interface",
        capability_name="resolve_experience_lens",
        endpoint_name="resolve_experience_lens",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceResolveExperienceLensResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__resolve_experience_lens__resolve_experience_lens,
    )
)


async def invoke_interface__select_environment_navigation_target__select_environment_navigation_target(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceSelectEnvironmentNavigationTargetResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceSelectEnvironmentNavigationTargetRequest.model_validate(request)
    return await typed_handler.interface.select_environment_navigation_target.select_environment_navigation_target(
        typed_request
    )


INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF: Final[str] = (
    "interface.select_environment_navigation_target.select_environment_navigation_target"
)
INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF,
    api_name="interface",
    capability_name="select_environment_navigation_target",
    endpoint_name="select_environment_navigation_target",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectEnvironmentNavigationTargetResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__select_environment_navigation_target__select_environment_navigation_target,
)


async def invoke_interface__select_interface_profile__select_interface_profile(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceSelectProfileResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceSelectProfileRequest.model_validate(request)
    return await typed_handler.interface.select_interface_profile.select_interface_profile(typed_request)


INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF: Final[str] = (
    "interface.select_interface_profile.select_interface_profile"
)
INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF,
    api_name="interface",
    capability_name="select_interface_profile",
    endpoint_name="select_interface_profile",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectProfileRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectProfileResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__select_interface_profile__select_interface_profile,
)


async def invoke_interface__select_interface_runtime_layout__select_interface_runtime_layout(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceSelectRuntimeLayoutResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceSelectRuntimeLayoutRequest.model_validate(request)
    return await typed_handler.interface.select_interface_runtime_layout.select_interface_runtime_layout(typed_request)


INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF: Final[str] = (
    "interface.select_interface_runtime_layout.select_interface_runtime_layout"
)
INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF,
    api_name="interface",
    capability_name="select_interface_runtime_layout",
    endpoint_name="select_interface_runtime_layout",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectRuntimeLayoutResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__select_interface_runtime_layout__select_interface_runtime_layout,
)


async def invoke_interface__select_interface_step__select_interface_step(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceSelectStepResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceSelectStepRequest.model_validate(request)
    return await typed_handler.interface.select_interface_step.select_interface_step(typed_request)


INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF: Final[str] = (
    "interface.select_interface_step.select_interface_step"
)
INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF,
        api_name="interface",
        capability_name="select_interface_step",
        endpoint_name="select_interface_step",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectStepRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceSelectStepResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__select_interface_step__select_interface_step,
    )
)


async def invoke_interface__start_interface_session__start_interface_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceSessionStartResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceSessionStartRequest.model_validate(request)
    return await typed_handler.interface.start_interface_session.start_interface_session(typed_request)


INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF: Final[str] = (
    "interface.start_interface_session.start_interface_session"
)
INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF,
        api_name="interface",
        capability_name="start_interface_session",
        endpoint_name="start_interface_session",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceSessionStartRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceSessionStartResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__start_interface_session__start_interface_session,
    )
)


async def invoke_interface__stop_interface_namespace__stop_interface_namespace(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceStopResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceStopRequest.model_validate(request)
    return await typed_handler.interface.stop_interface_namespace.stop_interface_namespace(typed_request)


INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF: Final[str] = (
    "interface.stop_interface_namespace.stop_interface_namespace"
)
INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF,
    api_name="interface",
    capability_name="stop_interface_namespace",
    endpoint_name="stop_interface_namespace",
    request_type_ref="aware_interface_service_dto.comms.models.InterfaceStopRequest",
    response_type_ref="aware_interface_service_dto.comms.models.InterfaceStopResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_interface__stop_interface_namespace__stop_interface_namespace,
)

InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent: TypeAlias = (
    InterfaceApiStreamClosedNotification | InterfaceApiEventNotification
)


async def invoke_interface__stream_interface_api__stream_interface_api(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceStreamApiResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceStreamApiRequest.model_validate(request)
    return await typed_handler.interface.stream_interface_api.stream_interface_api(typed_request)


def stream_invoke_interface__stream_interface_api__stream_interface_api(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent]:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceStreamApiRequest.model_validate(request)
    _ = execution
    return typed_handler.interface.stream_interface_api.stream_stream_interface_api(typed_request)


INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF: Final[str] = (
    "interface.stream_interface_api.stream_interface_api"
)
INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF,
        api_name="interface",
        capability_name="stream_interface_api",
        endpoint_name="stream_interface_api",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceStreamApiRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceStreamApiResponse",
        stream_event_type_refs=(
            "aware_interface_service_dto.comms.models.InterfaceApiStreamClosedNotification",
            "aware_interface_service_dto.comms.models.InterfaceApiEventNotification",
        ),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=stream_invoke_interface__stream_interface_api__stream_interface_api,
        fulfillment_bindings=(),
        invoke=invoke_interface__stream_interface_api__stream_interface_api,
    )
)


async def invoke_interface__sync_view_state_cursor__sync_view_state_cursor(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceSyncViewStateCursorResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceSyncViewStateCursorRequest.model_validate(request)
    return await typed_handler.interface.sync_view_state_cursor.sync_view_state_cursor(typed_request)


INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF: Final[str] = (
    "interface.sync_view_state_cursor.sync_view_state_cursor"
)
INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF,
        api_name="interface",
        capability_name="sync_view_state_cursor",
        endpoint_name="sync_view_state_cursor",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceSyncViewStateCursorResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_interface__sync_view_state_cursor__sync_view_state_cursor,
    )
)

InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent: TypeAlias = InterfaceStateNotification


async def invoke_interface__watch_interface_state__watch_interface_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> InterfaceFollowResponse:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceFollowRequest.model_validate(request)
    return await typed_handler.interface.watch_interface_state.watch_interface_state(typed_request)


def stream_invoke_interface__watch_interface_state__watch_interface_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent]:
    typed_handler = cast(AwareInterfaceServiceProtocol, handler)
    typed_request = InterfaceFollowRequest.model_validate(request)
    _ = execution
    return typed_handler.interface.watch_interface_state.stream_watch_interface_state(typed_request)


INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF: Final[str] = (
    "interface.watch_interface_state.watch_interface_state"
)
INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF,
        api_name="interface",
        capability_name="watch_interface_state",
        endpoint_name="watch_interface_state",
        request_type_ref="aware_interface_service_dto.comms.models.InterfaceFollowRequest",
        response_type_ref="aware_interface_service_dto.comms.models.InterfaceFollowResponse",
        stream_event_type_refs=("aware_interface_service_dto.comms.models.InterfaceStateNotification",),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=stream_invoke_interface__watch_interface_state__watch_interface_state,
        fulfillment_bindings=(),
        invoke=invoke_interface__watch_interface_state__watch_interface_state,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF: INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_PROTOCOL_BINDING,
    INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF: INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_PROTOCOL_BINDING,
    INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF: INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_PROTOCOL_BINDING,
    INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF: INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_PROTOCOL_BINDING,
    INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF: INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_PROTOCOL_BINDING,
    INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF: INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_PROTOCOL_BINDING,
    INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF: INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_PROTOCOL_BINDING,
    INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF: INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_PROTOCOL_BINDING,
    INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF: INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_PROTOCOL_BINDING,
    INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF: INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_PROTOCOL_BINDING,
    INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF: INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_PROTOCOL_BINDING,
    INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF: INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_PROTOCOL_BINDING,
    INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF: INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_PROTOCOL_BINDING,
    INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF: INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_PROTOCOL_BINDING,
    INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF: INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_PROTOCOL_BINDING,
    INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF: INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_PROTOCOL_BINDING,
    INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF: INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_PROTOCOL_BINDING,
    INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF: INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_PROTOCOL_BINDING,
    INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF: INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_PROTOCOL_BINDING,
    INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF: INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_PROTOCOL_BINDING,
    INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF: INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_PROTOCOL_BINDING,
    INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF: INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_PROTOCOL_BINDING,
    INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF: INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_PROTOCOL_BINDING,
    INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF: INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_PROTOCOL_BINDING,
    INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF: INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_PROTOCOL_BINDING,
    INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF: INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_PROTOCOL_BINDING,
    INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF: INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_PROTOCOL_BINDING,
}


class InterfaceActivateInterfaceRuntimeFocusCapabilityServiceProtocol(Protocol):

    async def activate_interface_runtime_focus(
        self, request: InterfaceActivateRuntimeFocusRequest
    ) -> InterfaceActivateRuntimeFocusResponse: ...


class InterfaceAdmitEnvironmentActorCapabilityServiceProtocol(Protocol):

    async def admit_environment_actor(
        self, request: InterfaceAdmitEnvironmentActorRequest
    ) -> InterfaceAdmitEnvironmentActorResponse: ...


class InterfaceAdmitInterfaceCapabilityServiceProtocol(Protocol):

    async def admit_interface(self, request: NamespaceEnsureRequest) -> NamespaceEnsureResponse: ...


class InterfaceApplyAttentionLayoutTopologyTransitionCapabilityServiceProtocol(Protocol):

    async def apply_attention_layout_topology_transition(
        self, request: InterfaceApplyAttentionLayoutTopologyTransitionRequest
    ) -> InterfaceApplyAttentionLayoutTopologyTransitionResponse: ...


class InterfaceApplyAttentionLayoutTransitionCapabilityServiceProtocol(Protocol):

    async def apply_attention_layout_transition(
        self, request: InterfaceApplyAttentionLayoutTransitionRequest
    ) -> InterfaceApplyAttentionLayoutTransitionResponse: ...


class InterfaceDescribeInterfaceSessionCapabilityServiceProtocol(Protocol):

    async def describe_interface_session(
        self, request: InterfaceSessionDescribeRequest
    ) -> InterfaceSessionDescribeResponse: ...


class InterfaceEnterAppScreenCapabilityServiceProtocol(Protocol):

    async def enter_app_screen(self, request: InterfaceEnterAppScreenRequest) -> InterfaceEnterAppScreenResponse: ...


class InterfaceEnterEnvironmentCapabilityServiceProtocol(Protocol):

    async def enter_environment(
        self, request: InterfaceEnterEnvironmentRequest
    ) -> InterfaceEnterEnvironmentResponse: ...


class InterfaceGetInterfaceStateCapabilityServiceProtocol(Protocol):

    async def get_interface_state(self, request: InterfaceStatusRequest) -> InterfaceStatusResponse: ...


class InterfaceInvokeInterfaceApiCapabilityServiceProtocol(Protocol):

    async def invoke_interface_api(self, request: InterfaceInvokeApiRequest) -> InterfaceInvokeApiResponse: ...


class InterfaceJoinEnvironmentSessionCapabilityServiceProtocol(Protocol):

    async def join_environment_session(
        self, request: InterfaceJoinEnvironmentSessionRequest
    ) -> InterfaceJoinEnvironmentSessionResponse: ...


class InterfaceListInterfaceNamespacesCapabilityServiceProtocol(Protocol):

    async def list_interface_namespaces(self, request: NamespaceListRequest) -> NamespaceListResponse: ...


class InterfaceMountInterfaceExperienceSessionCapabilityServiceProtocol(Protocol):

    async def mount_interface_experience_session(
        self, request: InterfaceExperienceSessionMountRequest
    ) -> InterfaceExperienceSessionMountResponse: ...


class InterfacePerformInterfaceActionCapabilityServiceProtocol(Protocol):

    async def perform_interface_action(self, request: InterfaceActionRequest) -> InterfaceActionResponse: ...


class InterfacePingInterfaceHostCapabilityServiceProtocol(Protocol):

    async def ping_interface_host(self, request: PingRequest) -> PingResponse: ...


class InterfaceReportRendererCapabilitiesCapabilityServiceProtocol(Protocol):

    async def report_renderer_capabilities(
        self, request: InterfaceReportRendererCapabilitiesRequest
    ) -> InterfaceReportRendererCapabilitiesResponse: ...


class InterfaceRequestInterfaceWindowLayoutCapabilityServiceProtocol(Protocol):

    async def request_interface_window_layout(
        self, request: InterfaceRequestWindowLayoutRequest
    ) -> InterfaceRequestWindowLayoutResponse: ...


class InterfaceResolveExperienceLensCapabilityServiceProtocol(Protocol):

    async def resolve_experience_lens(
        self, request: InterfaceResolveExperienceLensRequest
    ) -> InterfaceResolveExperienceLensResponse: ...


class InterfaceSelectEnvironmentNavigationTargetCapabilityServiceProtocol(Protocol):

    async def select_environment_navigation_target(
        self, request: InterfaceSelectEnvironmentNavigationTargetRequest
    ) -> InterfaceSelectEnvironmentNavigationTargetResponse: ...


class InterfaceSelectInterfaceProfileCapabilityServiceProtocol(Protocol):

    async def select_interface_profile(
        self, request: InterfaceSelectProfileRequest
    ) -> InterfaceSelectProfileResponse: ...


class InterfaceSelectInterfaceRuntimeLayoutCapabilityServiceProtocol(Protocol):

    async def select_interface_runtime_layout(
        self, request: InterfaceSelectRuntimeLayoutRequest
    ) -> InterfaceSelectRuntimeLayoutResponse: ...


class InterfaceSelectInterfaceStepCapabilityServiceProtocol(Protocol):

    async def select_interface_step(self, request: InterfaceSelectStepRequest) -> InterfaceSelectStepResponse: ...


class InterfaceStartInterfaceSessionCapabilityServiceProtocol(Protocol):

    async def start_interface_session(self, request: InterfaceSessionStartRequest) -> InterfaceSessionStartResponse: ...


class InterfaceStopInterfaceNamespaceCapabilityServiceProtocol(Protocol):

    async def stop_interface_namespace(self, request: InterfaceStopRequest) -> InterfaceStopResponse: ...


class InterfaceStreamInterfaceApiCapabilityServiceProtocol(Protocol):

    async def stream_interface_api(self, request: InterfaceStreamApiRequest) -> InterfaceStreamApiResponse: ...

    def stream_stream_interface_api(
        self, request: InterfaceStreamApiRequest
    ) -> AsyncIterator[InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent]: ...


class InterfaceSyncViewStateCursorCapabilityServiceProtocol(Protocol):

    async def sync_view_state_cursor(
        self, request: InterfaceSyncViewStateCursorRequest
    ) -> InterfaceSyncViewStateCursorResponse: ...


class InterfaceWatchInterfaceStateCapabilityServiceProtocol(Protocol):

    async def watch_interface_state(self, request: InterfaceFollowRequest) -> InterfaceFollowResponse: ...

    def stream_watch_interface_state(
        self, request: InterfaceFollowRequest
    ) -> AsyncIterator[InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent]: ...


class InterfaceApiServiceProtocol(Protocol):
    activate_interface_runtime_focus: InterfaceActivateInterfaceRuntimeFocusCapabilityServiceProtocol
    admit_environment_actor: InterfaceAdmitEnvironmentActorCapabilityServiceProtocol
    admit_interface: InterfaceAdmitInterfaceCapabilityServiceProtocol
    apply_attention_layout_topology_transition: InterfaceApplyAttentionLayoutTopologyTransitionCapabilityServiceProtocol
    apply_attention_layout_transition: InterfaceApplyAttentionLayoutTransitionCapabilityServiceProtocol
    describe_interface_session: InterfaceDescribeInterfaceSessionCapabilityServiceProtocol
    enter_app_screen: InterfaceEnterAppScreenCapabilityServiceProtocol
    enter_environment: InterfaceEnterEnvironmentCapabilityServiceProtocol
    get_interface_state: InterfaceGetInterfaceStateCapabilityServiceProtocol
    invoke_interface_api: InterfaceInvokeInterfaceApiCapabilityServiceProtocol
    join_environment_session: InterfaceJoinEnvironmentSessionCapabilityServiceProtocol
    list_interface_namespaces: InterfaceListInterfaceNamespacesCapabilityServiceProtocol
    mount_interface_experience_session: InterfaceMountInterfaceExperienceSessionCapabilityServiceProtocol
    perform_interface_action: InterfacePerformInterfaceActionCapabilityServiceProtocol
    ping_interface_host: InterfacePingInterfaceHostCapabilityServiceProtocol
    report_renderer_capabilities: InterfaceReportRendererCapabilitiesCapabilityServiceProtocol
    request_interface_window_layout: InterfaceRequestInterfaceWindowLayoutCapabilityServiceProtocol
    resolve_experience_lens: InterfaceResolveExperienceLensCapabilityServiceProtocol
    select_environment_navigation_target: InterfaceSelectEnvironmentNavigationTargetCapabilityServiceProtocol
    select_interface_profile: InterfaceSelectInterfaceProfileCapabilityServiceProtocol
    select_interface_runtime_layout: InterfaceSelectInterfaceRuntimeLayoutCapabilityServiceProtocol
    select_interface_step: InterfaceSelectInterfaceStepCapabilityServiceProtocol
    start_interface_session: InterfaceStartInterfaceSessionCapabilityServiceProtocol
    stop_interface_namespace: InterfaceStopInterfaceNamespaceCapabilityServiceProtocol
    stream_interface_api: InterfaceStreamInterfaceApiCapabilityServiceProtocol
    sync_view_state_cursor: InterfaceSyncViewStateCursorCapabilityServiceProtocol
    watch_interface_state: InterfaceWatchInterfaceStateCapabilityServiceProtocol


class AwareInterfaceServiceProtocol(Protocol):
    interface: InterfaceApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:8f10bec2ffdc72c2d6fcdcdad611aaa0fdff570f84c2d6d5e8a0285384a5099f",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 114,'
    '  "sections": ['
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:7c0f7bd5e2ee51f8e3bb05dd54ade843f6d5581d5ca3724fe7e08aced34a0f59",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:interface.activate_interface_runtime_focus.activate_interface_runtime_focus",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.admit_environment_actor.admit_environment_actor",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.admit_interface.admit_interface",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.apply_attention_layout_transition.apply_attention_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.describe_interface_session.describe_interface_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.enter_app_screen.enter_app_screen",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.enter_environment.enter_environment",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.get_interface_state.get_interface_state",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.invoke_interface_api.invoke_interface_api",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.join_environment_session.join_environment_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.list_interface_namespaces.list_interface_namespaces",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.mount_interface_experience_session.mount_interface_experience_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.perform_interface_action.perform_interface_action",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.ping_interface_host.ping_interface_host",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.report_renderer_capabilities.report_renderer_capabilities",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.request_interface_window_layout.request_interface_window_layout",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.resolve_experience_lens.resolve_experience_lens",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.select_environment_navigation_target.select_environment_navigation_target",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.select_interface_profile.select_interface_profile",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.select_interface_runtime_layout.select_interface_runtime_layout",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.select_interface_step.select_interface_step",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.start_interface_session.start_interface_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.stop_interface_namespace.stop_interface_namespace",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.stream_interface_api.stream_interface_api",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.sync_view_state_cursor.sync_view_state_cursor",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:interface.watch_interface_state.watch_interface_state",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:fb5725c10ec77f7ddeaf559b26690d0e45288c3a6e030548ee00a8e7457ced94",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.activate_interface_runtime_focus.activate_interface_runtime_focus",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:429794b5b2288bf4e4e3fb87c14913908755277f6aff709664445f63f167f76d",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.activate_interface_runtime_focus.activate_interface_runtime_focus",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1f1fa09c4ed19652c7faf96c673a2927af8784c39c9d08925cd67e22ead1246e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.admit_environment_actor.admit_environment_actor",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c6b6b523ad4f6aa61c1acc3032dc1487c0303f67204914a9d596ada2a13f13ed",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.admit_environment_actor.admit_environment_actor",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:5b5f740a813f630187ff38f49acbf90b2e8dfb64f269c67809775f70db55053c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.admit_interface.admit_interface",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0aaf0f1f740bdcad2948246cb06c80628447a8ebf424675b67c2807e0142d3f2",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.admit_interface.admit_interface",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:faa79050012aff9c2632ddf82f30baf7aa0b534c46a6ad3cee7651d8de4db83f",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:bbe1f4c16d82390bd04c4b17d61c0f452537f5571c4e68d04ce544db92a3f3ca",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.apply_attention_layout_topology_transition.apply_attention_layout_topology_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2cacf39c9271162ae50fd4048610a74391e043a4d8e87a198a821eb051bb9970",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.apply_attention_layout_transition.apply_attention_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7d4ad1579598e2b4f6027a180260d5a8580e0593874b52ce55c6f673c05e9377",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.apply_attention_layout_transition.apply_attention_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:cea76c11141d07ae94e44eb74f4f78e64ce3d877338955794dd5f69a66c84045",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.describe_interface_session.describe_interface_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e929fbaeeee7415ca53d7da92d4eb30b24026d7b50c324416e38f855dbcfb337",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.describe_interface_session.describe_interface_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:a87846d2a30e7cc8d2393581b9f4d78ed9d802989ec9783b7f3b3b032711f6d7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.enter_app_screen.enter_app_screen",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:90a6a8bc998b42dff1aa085ff6ccb498dc64dcaff18ab8b13ffdf5f247394226",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.enter_app_screen.enter_app_screen",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:23d9398b0630615776abb99536d7f1731892246547df19edd1eac9055125f7cb",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.enter_environment.enter_environment",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:2e3c05da9a162d9181344525f00309a77d9f275458a40dd58c1a24f0549c136f",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.enter_environment.enter_environment",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b2c4c57f2e2a2cb4ffa5c26736d70b41c23c8fc6a53260032b1692c141f7704e",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.get_interface_state.get_interface_state",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:dc292b96346a63861cea17fbc88b49c0e648cc3bdb30ed0ed9184c9201426467",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.get_interface_state.get_interface_state",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:133018adb088399b34352ba20e913f6e0180f916dfde839fc8cbee49e51d1981",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.invoke_interface_api.invoke_interface_api",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6272bf3c6cc3278d4d43465502bd1f90ee7daac79ed1771b9b2de4e0a8d274a2",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.invoke_interface_api.invoke_interface_api",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:fb94ca9f75abd6c3e9f013224f7f12868a6b7f169634cd58042db882ff8a9483",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.join_environment_session.join_environment_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:2df53761618f03299241a814704e677cb4474f94624b90c3149d47f82d0a0991",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.join_environment_session.join_environment_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:b55aec6357d3954322a3f525754b0f8149a24aad4acaa6ca37c3ea76ad757e60",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.list_interface_namespaces.list_interface_namespaces",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:04d69ad5a7379a8662b2f3bcd7cc3ffc9711951822cfae613dbb84b923942d8e",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.list_interface_namespaces.list_interface_namespaces",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:71d4ec1d2a9c5098af24df9b524956ee2a3c782b6f549696ed20e33be7bb4f45",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.mount_interface_experience_session.mount_interface_experience_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:928586e521bc0f0fc46acb7f5da6f73343f36cada2c11c64f25084f37cbc4ed2",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.mount_interface_experience_session.mount_interface_experience_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:51c94cba52de096baf8c1ef528011b08cef95512cd972010e9abb49bfed02dc5",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.perform_interface_action.perform_interface_action",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:67945bdf87e3b28ea60634f593952f74d7d03b143f2508c04520965dc8960a27",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.perform_interface_action.perform_interface_action",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2075d46cef2b828607fdd4a513b0e914c694073ebee14aa52fd73116f9719fc4",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.ping_interface_host.ping_interface_host",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 57'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d7f613ad88b8b21a6aa104b811fe8c6ec97fd7b7bade7227bbf86caf7f600d69",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.ping_interface_host.ping_interface_host",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 58'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ec7a4dbc8ada1384d93ac4fd803e98dd81e485b981656c118f01de2908bdb024",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.report_renderer_capabilities.report_renderer_capabilities",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 59'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:59a8536c8a036c4bb53cf3e6ab1d9da86f9c967c502bc6f93518cb0e24017333",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.report_renderer_capabilities.report_renderer_capabilities",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 60'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:73a3e6a4b8a63000354bd01fadf35785ac6cf7b29273e9737028ba7639e8c52b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.request_interface_window_layout.request_interface_window_layout",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 61'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a52fbe319c9a81798ca02afa0bb323ebf6d395c189aef59ecf87d6a445c62993",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.request_interface_window_layout.request_interface_window_layout",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 62'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:008ce5aa544a800fed5e486586814637fb73db46730a5e740aa80393aeeb4490",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.resolve_experience_lens.resolve_experience_lens",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 63'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:1bec4ca57862c87a75c28ddf98a6f3a3a263bc71077e5453588827928f3cd86a",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.resolve_experience_lens.resolve_experience_lens",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 64'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:6d4377d96051b75058ef3036348dd30fbbaf7699ffe5fbcf6568fe25a1095049",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.select_environment_navigation_target.select_environment_navigation_target",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 65'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:a39811bc2b75bf9c906bc1c4cd86ea28396ae85bcd80229543287a2950764b62",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.select_environment_navigation_target.select_environment_navigation_target",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 66'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:76b3088fb5b192596dd263ab58853a984ff57743ba14f5b4e82128b2290005b6",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.select_interface_profile.select_interface_profile",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 67'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:73e7d2825831c70923c9da047183efc6c41593f8e7dca4e952f8433cf479119d",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.select_interface_profile.select_interface_profile",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 68'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:79a305c400f6a1375764e6ba9b0c1f2705570a201ef82fd33b9c2afc38a165e7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.select_interface_runtime_layout.select_interface_runtime_layout",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 69'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:987df9064e6e98f594fd9063ead8a9270af1c90ce7bb7247413d6ee3def60a4e",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.select_interface_runtime_layout.select_interface_runtime_layout",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 70'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:20d701f76bf940e5f0fdf4243fc2bea7e35b398a24194729353a4c818cc7d2cf",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.select_interface_step.select_interface_step",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 71'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:480ecebc0f8733c41ea4785aa729ce51e8a533bc3221edddd51492613481053d",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.select_interface_step.select_interface_step",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 72'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:9072d2c8beca74037296873a8ecc59f5e62ea0fa75962ac26830032564a65f53",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.start_interface_session.start_interface_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 73'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5a3cd300404d83bfdab993b126580cfd0beef6dccde67ea2e267043de5318504",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.start_interface_session.start_interface_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 74'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e35b7486a6030bdbe077e09f538a54f346390faa5f733697abbacad57a96f298",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.stop_interface_namespace.stop_interface_namespace",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 75'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7a83804926c2f8bf6ad4206f36cde59db6b6aa71d33462bb06c2d3c7f9dfcb22",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.stop_interface_namespace.stop_interface_namespace",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 76'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:e71474232e277bbc49902b82b1d380ffe8d927a9eaf31978cedd94259f5ab6e7",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.stream_interface_api.stream_interface_api",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 77'
    "    },"
    "    {"
    '      "line_count": 20,'
    '      "rendered_text_digest": "sha256:5f5d969234e6802e4c8aca57dc8413d71da261cb0400d83b69a999a9e78199f9",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.stream_interface_api.stream_interface_api",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 78'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:158f6daacb3669ba82e6a60a81873da85a6d34052bd6c324320876d203713521",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.sync_view_state_cursor.sync_view_state_cursor",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 79'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5fee1f73da6a34f74eaecca06e36c35e28ff9e5397f0dfa5bb96e1a016eb906c",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.sync_view_state_cursor.sync_view_state_cursor",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 80'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:9e80c83cc4473f23003730247ca507b9a4f33aa5efd693d7659ab036e8c2f29d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:interface.watch_interface_state.watch_interface_state",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 81'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:b3d9e73a5cfdaa747acc8ad28ffdad96a6f0e710a15cd50a68a7c0f55e83709e",'
    '      "section_key": "api.service_protocol.endpoint_binding:interface.watch_interface_state.watch_interface_state",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 82'
    "    },"
    "    {"
    '      "line_count": 30,'
    '      "rendered_text_digest": "sha256:5fa161e50d0d2ece5fd60d1885003a0a94bea391d7445cc341f6e025df257b1e",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 83'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ad30b05af03a7bd8b997724da597766add6d83021b20a34949be6541b0e57f42",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.activate_interface_runtime_focus",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 84'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:5c31b1b42ae071401e3a431a32da5f953e01d9c4053b050a20baf12e3a334f1e",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.admit_environment_actor",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 85'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d7756e689b0edbb0e36cc1bb9a89c968b4ccafa3d4bbde14aca98c158df2f26c",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.admit_interface",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 86'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:797744a5fe8a65c319b53c90f1f50851004a273b0cc2ce25790fa0ad11fd78e7",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.apply_attention_layout_topology_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 87'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:28ae45310c1b5922b19ab5c9bb0dd9ae8d959c332f55891f084b3e42d956c4b2",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.apply_attention_layout_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 88'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:b2af448420fd0efd436d28cb73a6da68d21a6dfd62d07397797e9d88467c3dc2",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.describe_interface_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 89'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d59e4827107a04d9156c1ba5fb141d6ea76d8b014a6b52bc564821ea71b5ed15",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.enter_app_screen",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 90'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:48788206c411ae4be54536791588c461f25d2b041b03e1d97f3e658e7a4de48f",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.enter_environment",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 91'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:af7488ce8cdd53c655636e7109ce455da5dfd176424e79cb1be6c9fda7f36779",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.get_interface_state",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 92'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:9a77cf46979ee0ebf38f53871789edc93f0892152550766a173a4e7ed2fe847c",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.invoke_interface_api",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 93'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e15f39823d9fc689e7e1082357fabe506cc27ebd1071098c0c52ab481b1a62c4",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.join_environment_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 94'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:38a33a5bca2e9822ae6ea1ea71671270bc602fd64245272d6cc0b3bd62ce8394",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.list_interface_namespaces",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 95'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d7698b76de49b703706267c12f9fc1b210ecc9a3875ed9e6e9b62e6eab25ce9a",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.mount_interface_experience_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 96'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6a2d767cd6a648c96633a5e60acdc29e038744066cc07b9c822e8c1197d35601",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.perform_interface_action",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 97'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:01d64024767cd54ac2e2ca43b5b2f83154a2c1e4bdee2c0c4a9c726b97e443f1",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.ping_interface_host",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 98'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:41149f26b9e36d2b68cb31a52c43e14708d298cec081dc57a52e23260f41724c",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.report_renderer_capabilities",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 99'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e45239dd3eab43f311cafd634fa7a6d3ea808c321c638c2b3645b43bda93ccd9",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.request_interface_window_layout",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 100'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:421f821bcd769fcfe73f63ba05a9eca93e5ce733a9f26b9dadc12ee92994294e",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.resolve_experience_lens",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 101'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:f4e18647d466fdc760200240e93b7d94ec85fde32b10d8c18e041e43356b9fb6",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.select_environment_navigation_target",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 102'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:2e84331136daca69b23676ad1e8d6f0655eca4366a3c6df9f63a7cbdc406dc6d",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.select_interface_profile",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 103'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:67b006f40d3c25be5d213f179268e224371448bad5e062fb5cc939eeb9f72807",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.select_interface_runtime_layout",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 104'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:23c72fb327a65cde0bc5af1f0eec20fac4f18376854e03b46071ef6d949da698",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.select_interface_step",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 105'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:f9cde4f16676842e995f4014d6b49188664306f152713caf29c61493ead0cc0a",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.start_interface_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 106'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:57cf9157686cfa3d380bc969da0896179fec2a45d03e68f67193834e74dc954d",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.stop_interface_namespace",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 107'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:38645550f6eb2ffe381c099a08a9143cc296a0ad78c80f73b8b4e4ca4bfcf051",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.stream_interface_api",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 108'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:92442801faf56b73524eb28403a06c107ba1fec78d8fb800d235cd29c4386944",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.sync_view_state_cursor",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 109'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:0264178966a6136eb6268bcb5eef0ffcefbf3552064dd753be7cd9243bb23ab7",'
    '      "section_key": "api.service_protocol.capability_protocol:interface.watch_interface_state",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 110'
    "    },"
    "    {"
    '      "line_count": 29,'
    '      "rendered_text_digest": "sha256:25cca5408a695ab646709a4f29962fd4c24cb15be483d0d5013c63074c69dcdf",'
    '      "section_key": "api.service_protocol.api_protocol:interface",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 111'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:eefde8f4da8cf62d8295deb40f9340baea23acbcd30d0d7342b7d66c7ffb760d",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 112'
    "    },"
    "    {"
    '      "line_count": 128,'
    '      "rendered_text_digest": "sha256:9b00aca8c1a4c745e8464c8ecdae512e103ed185c1224255eb1bbedaf1cd2a61",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 113'
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
    "AwareInterfaceServiceProtocol",
    "InterfaceApiServiceProtocol",
    "InterfaceActivateInterfaceRuntimeFocusCapabilityServiceProtocol",
    "InterfaceAdmitEnvironmentActorCapabilityServiceProtocol",
    "InterfaceAdmitInterfaceCapabilityServiceProtocol",
    "InterfaceApplyAttentionLayoutTopologyTransitionCapabilityServiceProtocol",
    "InterfaceApplyAttentionLayoutTransitionCapabilityServiceProtocol",
    "InterfaceDescribeInterfaceSessionCapabilityServiceProtocol",
    "InterfaceEnterAppScreenCapabilityServiceProtocol",
    "InterfaceEnterEnvironmentCapabilityServiceProtocol",
    "InterfaceGetInterfaceStateCapabilityServiceProtocol",
    "InterfaceInvokeInterfaceApiCapabilityServiceProtocol",
    "InterfaceJoinEnvironmentSessionCapabilityServiceProtocol",
    "InterfaceListInterfaceNamespacesCapabilityServiceProtocol",
    "InterfaceMountInterfaceExperienceSessionCapabilityServiceProtocol",
    "InterfacePerformInterfaceActionCapabilityServiceProtocol",
    "InterfacePingInterfaceHostCapabilityServiceProtocol",
    "InterfaceReportRendererCapabilitiesCapabilityServiceProtocol",
    "InterfaceRequestInterfaceWindowLayoutCapabilityServiceProtocol",
    "InterfaceResolveExperienceLensCapabilityServiceProtocol",
    "InterfaceSelectEnvironmentNavigationTargetCapabilityServiceProtocol",
    "InterfaceSelectInterfaceProfileCapabilityServiceProtocol",
    "InterfaceSelectInterfaceRuntimeLayoutCapabilityServiceProtocol",
    "InterfaceSelectInterfaceStepCapabilityServiceProtocol",
    "InterfaceStartInterfaceSessionCapabilityServiceProtocol",
    "InterfaceStopInterfaceNamespaceCapabilityServiceProtocol",
    "InterfaceStreamInterfaceApiCapabilityServiceProtocol",
    "InterfaceSyncViewStateCursorCapabilityServiceProtocol",
    "InterfaceWatchInterfaceStateCapabilityServiceProtocol",
    "InterfaceStreamInterfaceApiStreamInterfaceApiStreamEvent",
    "InterfaceWatchInterfaceStateWatchInterfaceStateStreamEvent",
    "INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_ENDPOINT_REF",
    "INTERFACE__ACTIVATE_INTERFACE_RUNTIME_FOCUS__ACTIVATE_INTERFACE_RUNTIME_FOCUS_PROTOCOL_BINDING",
    "invoke_interface__activate_interface_runtime_focus__activate_interface_runtime_focus",
    "INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_ENDPOINT_REF",
    "INTERFACE__ADMIT_ENVIRONMENT_ACTOR__ADMIT_ENVIRONMENT_ACTOR_PROTOCOL_BINDING",
    "invoke_interface__admit_environment_actor__admit_environment_actor",
    "INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_ENDPOINT_REF",
    "INTERFACE__ADMIT_INTERFACE__ADMIT_INTERFACE_PROTOCOL_BINDING",
    "invoke_interface__admit_interface__admit_interface",
    "INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF",
    "INTERFACE__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_ATTENTION_LAYOUT_TOPOLOGY_TRANSITION_PROTOCOL_BINDING",
    "invoke_interface__apply_attention_layout_topology_transition__apply_attention_layout_topology_transition",
    "INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_ENDPOINT_REF",
    "INTERFACE__APPLY_ATTENTION_LAYOUT_TRANSITION__APPLY_ATTENTION_LAYOUT_TRANSITION_PROTOCOL_BINDING",
    "invoke_interface__apply_attention_layout_transition__apply_attention_layout_transition",
    "INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_ENDPOINT_REF",
    "INTERFACE__DESCRIBE_INTERFACE_SESSION__DESCRIBE_INTERFACE_SESSION_PROTOCOL_BINDING",
    "invoke_interface__describe_interface_session__describe_interface_session",
    "INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_ENDPOINT_REF",
    "INTERFACE__ENTER_APP_SCREEN__ENTER_APP_SCREEN_PROTOCOL_BINDING",
    "invoke_interface__enter_app_screen__enter_app_screen",
    "INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_ENDPOINT_REF",
    "INTERFACE__ENTER_ENVIRONMENT__ENTER_ENVIRONMENT_PROTOCOL_BINDING",
    "invoke_interface__enter_environment__enter_environment",
    "INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_ENDPOINT_REF",
    "INTERFACE__GET_INTERFACE_STATE__GET_INTERFACE_STATE_PROTOCOL_BINDING",
    "invoke_interface__get_interface_state__get_interface_state",
    "INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_ENDPOINT_REF",
    "INTERFACE__INVOKE_INTERFACE_API__INVOKE_INTERFACE_API_PROTOCOL_BINDING",
    "invoke_interface__invoke_interface_api__invoke_interface_api",
    "INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_ENDPOINT_REF",
    "INTERFACE__JOIN_ENVIRONMENT_SESSION__JOIN_ENVIRONMENT_SESSION_PROTOCOL_BINDING",
    "invoke_interface__join_environment_session__join_environment_session",
    "INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_ENDPOINT_REF",
    "INTERFACE__LIST_INTERFACE_NAMESPACES__LIST_INTERFACE_NAMESPACES_PROTOCOL_BINDING",
    "invoke_interface__list_interface_namespaces__list_interface_namespaces",
    "INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_ENDPOINT_REF",
    "INTERFACE__MOUNT_INTERFACE_EXPERIENCE_SESSION__MOUNT_INTERFACE_EXPERIENCE_SESSION_PROTOCOL_BINDING",
    "invoke_interface__mount_interface_experience_session__mount_interface_experience_session",
    "INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_ENDPOINT_REF",
    "INTERFACE__PERFORM_INTERFACE_ACTION__PERFORM_INTERFACE_ACTION_PROTOCOL_BINDING",
    "invoke_interface__perform_interface_action__perform_interface_action",
    "INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_ENDPOINT_REF",
    "INTERFACE__PING_INTERFACE_HOST__PING_INTERFACE_HOST_PROTOCOL_BINDING",
    "invoke_interface__ping_interface_host__ping_interface_host",
    "INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_ENDPOINT_REF",
    "INTERFACE__REPORT_RENDERER_CAPABILITIES__REPORT_RENDERER_CAPABILITIES_PROTOCOL_BINDING",
    "invoke_interface__report_renderer_capabilities__report_renderer_capabilities",
    "INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_ENDPOINT_REF",
    "INTERFACE__REQUEST_INTERFACE_WINDOW_LAYOUT__REQUEST_INTERFACE_WINDOW_LAYOUT_PROTOCOL_BINDING",
    "invoke_interface__request_interface_window_layout__request_interface_window_layout",
    "INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_ENDPOINT_REF",
    "INTERFACE__RESOLVE_EXPERIENCE_LENS__RESOLVE_EXPERIENCE_LENS_PROTOCOL_BINDING",
    "invoke_interface__resolve_experience_lens__resolve_experience_lens",
    "INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_ENDPOINT_REF",
    "INTERFACE__SELECT_ENVIRONMENT_NAVIGATION_TARGET__SELECT_ENVIRONMENT_NAVIGATION_TARGET_PROTOCOL_BINDING",
    "invoke_interface__select_environment_navigation_target__select_environment_navigation_target",
    "INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_ENDPOINT_REF",
    "INTERFACE__SELECT_INTERFACE_PROFILE__SELECT_INTERFACE_PROFILE_PROTOCOL_BINDING",
    "invoke_interface__select_interface_profile__select_interface_profile",
    "INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_ENDPOINT_REF",
    "INTERFACE__SELECT_INTERFACE_RUNTIME_LAYOUT__SELECT_INTERFACE_RUNTIME_LAYOUT_PROTOCOL_BINDING",
    "invoke_interface__select_interface_runtime_layout__select_interface_runtime_layout",
    "INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_ENDPOINT_REF",
    "INTERFACE__SELECT_INTERFACE_STEP__SELECT_INTERFACE_STEP_PROTOCOL_BINDING",
    "invoke_interface__select_interface_step__select_interface_step",
    "INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_ENDPOINT_REF",
    "INTERFACE__START_INTERFACE_SESSION__START_INTERFACE_SESSION_PROTOCOL_BINDING",
    "invoke_interface__start_interface_session__start_interface_session",
    "INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_ENDPOINT_REF",
    "INTERFACE__STOP_INTERFACE_NAMESPACE__STOP_INTERFACE_NAMESPACE_PROTOCOL_BINDING",
    "invoke_interface__stop_interface_namespace__stop_interface_namespace",
    "INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_ENDPOINT_REF",
    "INTERFACE__STREAM_INTERFACE_API__STREAM_INTERFACE_API_PROTOCOL_BINDING",
    "invoke_interface__stream_interface_api__stream_interface_api",
    "stream_invoke_interface__stream_interface_api__stream_interface_api",
    "INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_ENDPOINT_REF",
    "INTERFACE__SYNC_VIEW_STATE_CURSOR__SYNC_VIEW_STATE_CURSOR_PROTOCOL_BINDING",
    "invoke_interface__sync_view_state_cursor__sync_view_state_cursor",
    "INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_ENDPOINT_REF",
    "INTERFACE__WATCH_INTERFACE_STATE__WATCH_INTERFACE_STATE_PROTOCOL_BINDING",
    "invoke_interface__watch_interface_state__watch_interface_state",
    "stream_invoke_interface__watch_interface_state__watch_interface_state",
]
