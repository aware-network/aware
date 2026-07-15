# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_attention_service_dto.attention.section.models import AttentionRuntimeMountSnapshotEvent
from aware_attention_service_dto.attention.section.service_operation import (
    ActivateAttentionSectionObservableRequest,
    ActivateAttentionSectionObservableResponse,
    GetAttentionFocusScopeCommitsRequest,
    GetAttentionFocusScopeCommitsResponse,
    GetAttentionRuntimeMountRequest,
    GetAttentionRuntimeMountResponse,
    GetAttentionSectionStateRequest,
    GetAttentionSectionStateResponse,
    WatchAttentionRuntimeMountRequest,
    WatchAttentionRuntimeMountResponse,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTopologyTransitionRequest,
    ApplyAttentionSessionLayoutTopologyTransitionResponse,
    ApplyAttentionSessionLayoutTransitionRequest,
    ApplyAttentionSessionLayoutTransitionResponse,
    DescribeAttentionSessionRequest,
    DescribeAttentionSessionResponse,
    DescribeAttentionTransitionRequest,
    DescribeAttentionTransitionResponse,
    ListAttentionTransitionsRequest,
    ListAttentionTransitionsResponse,
    MountAttentionSessionLayoutRequest,
    MountAttentionSessionLayoutResponse,
    MountAttentionSessionSectionRequest,
    MountAttentionSessionSectionResponse,
    StartAttentionSessionRequest,
    StartAttentionSessionResponse,
    ValidateAttentionTransitionRequest,
    ValidateAttentionTransitionResponse,
)

API_PACKAGE_NAME: Final[str] = "attention-service-api"
API_FQN_PREFIX: Final[str] = "aware_attention_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_attention_service_api"


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


async def invoke_attention__activate_section_observable__activate_section_observable(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ActivateAttentionSectionObservableResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = ActivateAttentionSectionObservableRequest.model_validate(request)
    return await typed_handler.attention.activate_section_observable.activate_section_observable(typed_request)


ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF: Final[str] = (
    "attention.activate_section_observable.activate_section_observable"
)
ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF,
    api_name="attention",
    capability_name="activate_section_observable",
    endpoint_name="activate_section_observable",
    request_type_ref="aware_attention_service_dto.attention.section.ActivateAttentionSectionObservableRequest",
    response_type_ref="aware_attention_service_dto.attention.section.ActivateAttentionSectionObservableResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__activate_section_observable__activate_section_observable,
)


async def invoke_attention__apply_session_layout_topology_transition__apply_session_layout_topology_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ApplyAttentionSessionLayoutTopologyTransitionResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = ApplyAttentionSessionLayoutTopologyTransitionRequest.model_validate(request)
    return (
        await typed_handler.attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition(
            typed_request
        )
    )


ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF: Final[
    str
] = "attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition"
ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF,
    api_name="attention",
    capability_name="apply_session_layout_topology_transition",
    endpoint_name="apply_session_layout_topology_transition",
    request_type_ref="aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTopologyTransitionRequest",
    response_type_ref="aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTopologyTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__apply_session_layout_topology_transition__apply_session_layout_topology_transition,
)


async def invoke_attention__apply_session_layout_transition__apply_session_layout_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ApplyAttentionSessionLayoutTransitionResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = ApplyAttentionSessionLayoutTransitionRequest.model_validate(request)
    return await typed_handler.attention.apply_session_layout_transition.apply_session_layout_transition(typed_request)


ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF: Final[str] = (
    "attention.apply_session_layout_transition.apply_session_layout_transition"
)
ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF,
    api_name="attention",
    capability_name="apply_session_layout_transition",
    endpoint_name="apply_session_layout_transition",
    request_type_ref="aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTransitionRequest",
    response_type_ref="aware_attention_service_dto.attention.session.ApplyAttentionSessionLayoutTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__apply_session_layout_transition__apply_session_layout_transition,
)


async def invoke_attention__describe_attention_session__describe_attention_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeAttentionSessionResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = DescribeAttentionSessionRequest.model_validate(request)
    return await typed_handler.attention.describe_attention_session.describe_attention_session(typed_request)


ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF: Final[str] = (
    "attention.describe_attention_session.describe_attention_session"
)
ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF,
    api_name="attention",
    capability_name="describe_attention_session",
    endpoint_name="describe_attention_session",
    request_type_ref="aware_attention_service_dto.attention.session.DescribeAttentionSessionRequest",
    response_type_ref="aware_attention_service_dto.attention.session.DescribeAttentionSessionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__describe_attention_session__describe_attention_session,
)


async def invoke_attention__describe_attention_transition__describe_attention_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeAttentionTransitionResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = DescribeAttentionTransitionRequest.model_validate(request)
    return await typed_handler.attention.describe_attention_transition.describe_attention_transition(typed_request)


ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF: Final[str] = (
    "attention.describe_attention_transition.describe_attention_transition"
)
ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF,
    api_name="attention",
    capability_name="describe_attention_transition",
    endpoint_name="describe_attention_transition",
    request_type_ref="aware_attention_service_dto.attention.session.DescribeAttentionTransitionRequest",
    response_type_ref="aware_attention_service_dto.attention.session.DescribeAttentionTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__describe_attention_transition__describe_attention_transition,
)


async def invoke_attention__get_focus_scope_commits__get_focus_scope_commits(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetAttentionFocusScopeCommitsResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = GetAttentionFocusScopeCommitsRequest.model_validate(request)
    return await typed_handler.attention.get_focus_scope_commits.get_focus_scope_commits(typed_request)


ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF: Final[str] = (
    "attention.get_focus_scope_commits.get_focus_scope_commits"
)
ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF,
        api_name="attention",
        capability_name="get_focus_scope_commits",
        endpoint_name="get_focus_scope_commits",
        request_type_ref="aware_attention_service_dto.attention.section.GetAttentionFocusScopeCommitsRequest",
        response_type_ref="aware_attention_service_dto.attention.section.GetAttentionFocusScopeCommitsResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_attention__get_focus_scope_commits__get_focus_scope_commits,
    )
)


async def invoke_attention__get_runtime_mount__get_runtime_mount(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetAttentionRuntimeMountResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = GetAttentionRuntimeMountRequest.model_validate(request)
    return await typed_handler.attention.get_runtime_mount.get_runtime_mount(typed_request)


ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF: Final[str] = (
    "attention.get_runtime_mount.get_runtime_mount"
)
ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF,
        api_name="attention",
        capability_name="get_runtime_mount",
        endpoint_name="get_runtime_mount",
        request_type_ref="aware_attention_service_dto.attention.section.GetAttentionRuntimeMountRequest",
        response_type_ref="aware_attention_service_dto.attention.section.GetAttentionRuntimeMountResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_attention__get_runtime_mount__get_runtime_mount,
    )
)


async def invoke_attention__get_section_state__get_section_state(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> GetAttentionSectionStateResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = GetAttentionSectionStateRequest.model_validate(request)
    return await typed_handler.attention.get_section_state.get_section_state(typed_request)


ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF: Final[str] = (
    "attention.get_section_state.get_section_state"
)
ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF,
        api_name="attention",
        capability_name="get_section_state",
        endpoint_name="get_section_state",
        request_type_ref="aware_attention_service_dto.attention.section.GetAttentionSectionStateRequest",
        response_type_ref="aware_attention_service_dto.attention.section.GetAttentionSectionStateResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_attention__get_section_state__get_section_state,
    )
)


async def invoke_attention__list_attention_transitions__list_attention_transitions(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ListAttentionTransitionsResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = ListAttentionTransitionsRequest.model_validate(request)
    return await typed_handler.attention.list_attention_transitions.list_attention_transitions(typed_request)


ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF: Final[str] = (
    "attention.list_attention_transitions.list_attention_transitions"
)
ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF,
    api_name="attention",
    capability_name="list_attention_transitions",
    endpoint_name="list_attention_transitions",
    request_type_ref="aware_attention_service_dto.attention.session.ListAttentionTransitionsRequest",
    response_type_ref="aware_attention_service_dto.attention.session.ListAttentionTransitionsResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__list_attention_transitions__list_attention_transitions,
)


async def invoke_attention__mount_attention_session_layout__mount_attention_session_layout(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MountAttentionSessionLayoutResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = MountAttentionSessionLayoutRequest.model_validate(request)
    return await typed_handler.attention.mount_attention_session_layout.mount_attention_session_layout(typed_request)


ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF: Final[str] = (
    "attention.mount_attention_session_layout.mount_attention_session_layout"
)
ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF,
    api_name="attention",
    capability_name="mount_attention_session_layout",
    endpoint_name="mount_attention_session_layout",
    request_type_ref="aware_attention_service_dto.attention.session.MountAttentionSessionLayoutRequest",
    response_type_ref="aware_attention_service_dto.attention.session.MountAttentionSessionLayoutResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__mount_attention_session_layout__mount_attention_session_layout,
)


async def invoke_attention__mount_attention_session_section__mount_attention_session_section(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> MountAttentionSessionSectionResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = MountAttentionSessionSectionRequest.model_validate(request)
    return await typed_handler.attention.mount_attention_session_section.mount_attention_session_section(typed_request)


ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF: Final[str] = (
    "attention.mount_attention_session_section.mount_attention_session_section"
)
ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF,
    api_name="attention",
    capability_name="mount_attention_session_section",
    endpoint_name="mount_attention_session_section",
    request_type_ref="aware_attention_service_dto.attention.session.MountAttentionSessionSectionRequest",
    response_type_ref="aware_attention_service_dto.attention.session.MountAttentionSessionSectionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__mount_attention_session_section__mount_attention_session_section,
)


async def invoke_attention__start_attention_session__start_attention_session(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> StartAttentionSessionResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = StartAttentionSessionRequest.model_validate(request)
    return await typed_handler.attention.start_attention_session.start_attention_session(typed_request)


ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF: Final[str] = (
    "attention.start_attention_session.start_attention_session"
)
ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF,
        api_name="attention",
        capability_name="start_attention_session",
        endpoint_name="start_attention_session",
        request_type_ref="aware_attention_service_dto.attention.session.StartAttentionSessionRequest",
        response_type_ref="aware_attention_service_dto.attention.session.StartAttentionSessionResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_attention__start_attention_session__start_attention_session,
    )
)


async def invoke_attention__validate_attention_transition__validate_attention_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateAttentionTransitionResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = ValidateAttentionTransitionRequest.model_validate(request)
    return await typed_handler.attention.validate_attention_transition.validate_attention_transition(typed_request)


ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF: Final[str] = (
    "attention.validate_attention_transition.validate_attention_transition"
)
ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF,
    api_name="attention",
    capability_name="validate_attention_transition",
    endpoint_name="validate_attention_transition",
    request_type_ref="aware_attention_service_dto.attention.session.ValidateAttentionTransitionRequest",
    response_type_ref="aware_attention_service_dto.attention.session.ValidateAttentionTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_attention__validate_attention_transition__validate_attention_transition,
)

AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent: TypeAlias = AttentionRuntimeMountSnapshotEvent


async def invoke_attention__watch_runtime_mount__watch_runtime_mount(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> WatchAttentionRuntimeMountResponse:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = WatchAttentionRuntimeMountRequest.model_validate(request)
    return await typed_handler.attention.watch_runtime_mount.watch_runtime_mount(typed_request)


def stream_invoke_attention__watch_runtime_mount__watch_runtime_mount(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent]:
    typed_handler = cast(AwareAttentionServiceProtocol, handler)
    typed_request = WatchAttentionRuntimeMountRequest.model_validate(request)
    _ = execution
    return typed_handler.attention.watch_runtime_mount.stream_watch_runtime_mount(typed_request)


ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF: Final[str] = (
    "attention.watch_runtime_mount.watch_runtime_mount"
)
ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF,
        api_name="attention",
        capability_name="watch_runtime_mount",
        endpoint_name="watch_runtime_mount",
        request_type_ref="aware_attention_service_dto.attention.section.WatchAttentionRuntimeMountRequest",
        response_type_ref="aware_attention_service_dto.attention.section.WatchAttentionRuntimeMountResponse",
        stream_event_type_refs=("aware_attention_service_dto.attention.section.AttentionRuntimeMountSnapshotEvent",),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=stream_invoke_attention__watch_runtime_mount__watch_runtime_mount,
        fulfillment_bindings=(),
        invoke=invoke_attention__watch_runtime_mount__watch_runtime_mount,
    )
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF: ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_PROTOCOL_BINDING,
    ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF: ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_PROTOCOL_BINDING,
    ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF: ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_PROTOCOL_BINDING,
    ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF: ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_PROTOCOL_BINDING,
    ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF: ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_PROTOCOL_BINDING,
    ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF: ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_PROTOCOL_BINDING,
    ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF: ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_PROTOCOL_BINDING,
    ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF: ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_PROTOCOL_BINDING,
    ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF: ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_PROTOCOL_BINDING,
    ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF: ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_PROTOCOL_BINDING,
    ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF: ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_PROTOCOL_BINDING,
    ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF: ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_PROTOCOL_BINDING,
    ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF: ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_PROTOCOL_BINDING,
    ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF: ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_PROTOCOL_BINDING,
}


class AttentionActivateSectionObservableCapabilityServiceProtocol(Protocol):

    async def activate_section_observable(
        self, request: ActivateAttentionSectionObservableRequest
    ) -> ActivateAttentionSectionObservableResponse: ...


class AttentionApplySessionLayoutTopologyTransitionCapabilityServiceProtocol(Protocol):

    async def apply_session_layout_topology_transition(
        self, request: ApplyAttentionSessionLayoutTopologyTransitionRequest
    ) -> ApplyAttentionSessionLayoutTopologyTransitionResponse: ...


class AttentionApplySessionLayoutTransitionCapabilityServiceProtocol(Protocol):

    async def apply_session_layout_transition(
        self, request: ApplyAttentionSessionLayoutTransitionRequest
    ) -> ApplyAttentionSessionLayoutTransitionResponse: ...


class AttentionDescribeAttentionSessionCapabilityServiceProtocol(Protocol):

    async def describe_attention_session(
        self, request: DescribeAttentionSessionRequest
    ) -> DescribeAttentionSessionResponse: ...


class AttentionDescribeAttentionTransitionCapabilityServiceProtocol(Protocol):

    async def describe_attention_transition(
        self, request: DescribeAttentionTransitionRequest
    ) -> DescribeAttentionTransitionResponse: ...


class AttentionGetFocusScopeCommitsCapabilityServiceProtocol(Protocol):

    async def get_focus_scope_commits(
        self, request: GetAttentionFocusScopeCommitsRequest
    ) -> GetAttentionFocusScopeCommitsResponse: ...


class AttentionGetRuntimeMountCapabilityServiceProtocol(Protocol):

    async def get_runtime_mount(self, request: GetAttentionRuntimeMountRequest) -> GetAttentionRuntimeMountResponse: ...


class AttentionGetSectionStateCapabilityServiceProtocol(Protocol):

    async def get_section_state(self, request: GetAttentionSectionStateRequest) -> GetAttentionSectionStateResponse: ...


class AttentionListAttentionTransitionsCapabilityServiceProtocol(Protocol):

    async def list_attention_transitions(
        self, request: ListAttentionTransitionsRequest
    ) -> ListAttentionTransitionsResponse: ...


class AttentionMountAttentionSessionLayoutCapabilityServiceProtocol(Protocol):

    async def mount_attention_session_layout(
        self, request: MountAttentionSessionLayoutRequest
    ) -> MountAttentionSessionLayoutResponse: ...


class AttentionMountAttentionSessionSectionCapabilityServiceProtocol(Protocol):

    async def mount_attention_session_section(
        self, request: MountAttentionSessionSectionRequest
    ) -> MountAttentionSessionSectionResponse: ...


class AttentionStartAttentionSessionCapabilityServiceProtocol(Protocol):

    async def start_attention_session(self, request: StartAttentionSessionRequest) -> StartAttentionSessionResponse: ...


class AttentionValidateAttentionTransitionCapabilityServiceProtocol(Protocol):

    async def validate_attention_transition(
        self, request: ValidateAttentionTransitionRequest
    ) -> ValidateAttentionTransitionResponse: ...


class AttentionWatchRuntimeMountCapabilityServiceProtocol(Protocol):

    async def watch_runtime_mount(
        self, request: WatchAttentionRuntimeMountRequest
    ) -> WatchAttentionRuntimeMountResponse: ...

    def stream_watch_runtime_mount(
        self, request: WatchAttentionRuntimeMountRequest
    ) -> AsyncIterator[AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent]: ...


class AttentionApiServiceProtocol(Protocol):
    activate_section_observable: AttentionActivateSectionObservableCapabilityServiceProtocol
    apply_session_layout_topology_transition: AttentionApplySessionLayoutTopologyTransitionCapabilityServiceProtocol
    apply_session_layout_transition: AttentionApplySessionLayoutTransitionCapabilityServiceProtocol
    describe_attention_session: AttentionDescribeAttentionSessionCapabilityServiceProtocol
    describe_attention_transition: AttentionDescribeAttentionTransitionCapabilityServiceProtocol
    get_focus_scope_commits: AttentionGetFocusScopeCommitsCapabilityServiceProtocol
    get_runtime_mount: AttentionGetRuntimeMountCapabilityServiceProtocol
    get_section_state: AttentionGetSectionStateCapabilityServiceProtocol
    list_attention_transitions: AttentionListAttentionTransitionsCapabilityServiceProtocol
    mount_attention_session_layout: AttentionMountAttentionSessionLayoutCapabilityServiceProtocol
    mount_attention_session_section: AttentionMountAttentionSessionSectionCapabilityServiceProtocol
    start_attention_session: AttentionStartAttentionSessionCapabilityServiceProtocol
    validate_attention_transition: AttentionValidateAttentionTransitionCapabilityServiceProtocol
    watch_runtime_mount: AttentionWatchRuntimeMountCapabilityServiceProtocol


class AwareAttentionServiceProtocol(Protocol):
    attention: AttentionApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:0f7df048c4f20370d918ae1ce6d365829ecf672896e3e49bd7900b7ca10c5de3",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 62,'
    '  "sections": ['
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c39c6c6a617fc05554db9e7d388e797f29eab773717fe86a1f9aba4a07f98a1f",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:attention.activate_section_observable.activate_section_observable",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.apply_session_layout_transition.apply_session_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.describe_attention_session.describe_attention_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.describe_attention_transition.describe_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.get_focus_scope_commits.get_focus_scope_commits",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.get_runtime_mount.get_runtime_mount",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.get_section_state.get_section_state",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.list_attention_transitions.list_attention_transitions",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.mount_attention_session_layout.mount_attention_session_layout",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.mount_attention_session_section.mount_attention_session_section",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.start_attention_session.start_attention_session",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.validate_attention_transition.validate_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:attention.watch_runtime_mount.watch_runtime_mount",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:690be5153a6c92eb05fb6f0dd9d955fcb2c84bf8f236475526b8368ffdfdf8ea",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.activate_section_observable.activate_section_observable",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:fc6e1533cac605722210b054049b02743869ba4d07ecb65c16601f661d869c39",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.activate_section_observable.activate_section_observable",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:949e60ca6228b9c05d0c5107bd459d7eebadabef4f1a28723eb568fb84dec296",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0cccfd1c5ef795606d1a24244c0e09ca1ade3f89d4d8f4610168d64665655e31",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e1b5824ea092190eda8997c2d68e70edc563d8c2f9936ae6c6496d761de56bce",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.apply_session_layout_transition.apply_session_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:eed6b9eee02ac1f992eb20f5ce0fcd126f84135ec02d254b2d55d5a37a638c8e",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.apply_session_layout_transition.apply_session_layout_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:4021860231bdcdbd68d06f4c169a90aca88305d4e8ca3c8355adabf42ec1159b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.describe_attention_session.describe_attention_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:6c88846e418f1929ac53926ccaff307d3a65daaa65ce664a9022f25a078060e7",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.describe_attention_session.describe_attention_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:ae73e92e64b48e8e7151bb7e73d46a803a34a741a5ded76a53c44b4d51380274",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.describe_attention_transition.describe_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:7e931e6000b9c63b351d1da7ab1bfe2c17b11b697ba0e3d91a13008b4dbd52d7",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.describe_attention_transition.describe_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2151654dac455d8cdf25602676f9ddf230174ffbe348298ba22364802854e33d",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.get_focus_scope_commits.get_focus_scope_commits",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:c3edfb472ee46be50e833996539ceccab7f5bfd63c9b8bf791fdf35c74aa9688",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.get_focus_scope_commits.get_focus_scope_commits",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:14388e05f0aa13497597e1c2831f1c3502d906f3ce316d8e7f9fc5edc9e2b251",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.get_runtime_mount.get_runtime_mount",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e3d653d6f20269ce3c68bfd7d6cc9f3dff6f7cd5729221eb9f9a947b508c14bd",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.get_runtime_mount.get_runtime_mount",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:363f6eec86ab606a11a25cbf469cb269d2e81ae8ade5665ae507acff000adc89",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.get_section_state.get_section_state",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:96110509c6e7431e42515247d6cf3768ef5842b7e2cf62857dc41a00600914f2",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.get_section_state.get_section_state",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e48b500b07a7e5ab7e9c124496bacb2c935210962478bbcf13629e9f1af7c8ca",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.list_attention_transitions.list_attention_transitions",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:836ba3dc2f1a06726e5e033a14fd85b13c603811612d9daaf37be0325fa506f2",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.list_attention_transitions.list_attention_transitions",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:f9c94a915f5a5e0b16bc403dcae6b97b6b134f97b66e242536f3ed621dd84de1",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.mount_attention_session_layout.mount_attention_session_layout",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:039487fbe9e2d94cb6f1c265b68099f129ec40aaea323031028b654baa1c1333",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.mount_attention_session_layout.mount_attention_session_layout",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:3db7bca858af1e6f6e06b7f89a5b41d3d0e03062c75a4481068a50ba1c8d4d66",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.mount_attention_session_section.mount_attention_session_section",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:4ee7a6f3f5ec50902ce0ec9431f31c951b51d9d057258db2ff94abad98b367a7",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.mount_attention_session_section.mount_attention_session_section",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:40f25c9aae1cc011ff02a7b36bf8da781ec46570b977a898b077f9559ce55a5b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.start_attention_session.start_attention_session",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:50952518901bd99a30c5033aeb56fd4398b0990048ed7417d1ea2bb54b92a81d",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.start_attention_session.start_attention_session",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:2c937f603b91b37cf731688b6acb72954a6a95797d2185b592f522598b6fd306",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.validate_attention_transition.validate_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:10a17f665c4c09390022db5a541926d57469c2c10e72c80385e2d46daf89f4e2",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.validate_attention_transition.validate_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:236ec07aee8976f7b92d5c6b63d07aadb9c07dc9fb0a5beaafeeda3b5a69ad41",'
    '      "section_key": "api.service_protocol.endpoint_invoker:attention.watch_runtime_mount.watch_runtime_mount",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:0ee03a5d81d6ce5ca9de0780b6981856d970b6c57e34b453e9020f624324317a",'
    '      "section_key": "api.service_protocol.endpoint_binding:attention.watch_runtime_mount.watch_runtime_mount",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 17,'
    '      "rendered_text_digest": "sha256:e83b1555897ca7de63dbe884994d39c34de9188b27177450956a0d607c503433",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:5531e78860c17feeebf271b36a8f708b328ac4a61a7e7d174add6bbd0a00f283",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.activate_section_observable",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:4733a2510ed372d6101056039f75198a636dc6df2e64f2b393af249de6fb5c55",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.apply_session_layout_topology_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:1265df8ebbee65c8cfeccd6470219b853d63f49d844a5f5d2742b6e484e35c6f",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.apply_session_layout_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:47bccec744141721186cb2ec8b2c9afaefbaf6cfcaf766b378da556f456d487d",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.describe_attention_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:ef04a22b2a2d0ce9d1267d3f1d67cbf2615886293c03df0f7ee42db1b789d7cf",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.describe_attention_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6c1b5422fee3712713ad1448d17654c8cd539077d95c9142858214ad668b2f13",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.get_focus_scope_commits",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:3df72ef7a4ec5a451cc4ca982033f97f54535e5acf74f32d0fdd0151f92b9c1d",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.get_runtime_mount",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:a8bdeca2c59069660805bca012e45cd5accea9f0f8b213006d4e3166d0e6613d",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.get_section_state",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:41d0d3adc38c92e54fe6b93f8f2da9a0c8e0f0485c968fb677ff76aa90399a82",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.list_attention_transitions",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:1ebca6bbc1ed36109412a989ea3aadd76bc6e9ec2f902b3237a18323594e6f84",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.mount_attention_session_layout",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:e6a716173407f87bf581ecd9b6b67b4b7663b45c3498412f4df8af52e5656c66",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.mount_attention_session_section",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:c8c49410689a71ce54a9e0981d9f066fd30641d6ba0af0bfb8fee5eb15073a69",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.start_attention_session",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:7ff54abb18f90570aa0dc59105f53d111ba535750b1454c725ffcad154d5a2ff",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.validate_attention_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 57'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:889461846164a60242a9e845f6c0916d57ae49bf8f8522d157f85bc61d1f2aaa",'
    '      "section_key": "api.service_protocol.capability_protocol:attention.watch_runtime_mount",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 58'
    "    },"
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:61263996e14721364d8e0dcb92b16a4c8947a5df756863a6255a052642c18f15",'
    '      "section_key": "api.service_protocol.api_protocol:attention",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 59'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:99188093ca9bf6c22bd841832bd8d7f9d2a4d418e6a5d9c03fc441bfcf7c6afa",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 60'
    "    },"
    "    {"
    '      "line_count": 74,'
    '      "rendered_text_digest": "sha256:0bee01a1e747ceb2b23893edd2205b5aaa6911b0e917d04621dd840f5a8f9444",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 61'
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
    "AwareAttentionServiceProtocol",
    "AttentionApiServiceProtocol",
    "AttentionActivateSectionObservableCapabilityServiceProtocol",
    "AttentionApplySessionLayoutTopologyTransitionCapabilityServiceProtocol",
    "AttentionApplySessionLayoutTransitionCapabilityServiceProtocol",
    "AttentionDescribeAttentionSessionCapabilityServiceProtocol",
    "AttentionDescribeAttentionTransitionCapabilityServiceProtocol",
    "AttentionGetFocusScopeCommitsCapabilityServiceProtocol",
    "AttentionGetRuntimeMountCapabilityServiceProtocol",
    "AttentionGetSectionStateCapabilityServiceProtocol",
    "AttentionListAttentionTransitionsCapabilityServiceProtocol",
    "AttentionMountAttentionSessionLayoutCapabilityServiceProtocol",
    "AttentionMountAttentionSessionSectionCapabilityServiceProtocol",
    "AttentionStartAttentionSessionCapabilityServiceProtocol",
    "AttentionValidateAttentionTransitionCapabilityServiceProtocol",
    "AttentionWatchRuntimeMountCapabilityServiceProtocol",
    "AttentionWatchRuntimeMountWatchRuntimeMountStreamEvent",
    "ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_ENDPOINT_REF",
    "ATTENTION__ACTIVATE_SECTION_OBSERVABLE__ACTIVATE_SECTION_OBSERVABLE_PROTOCOL_BINDING",
    "invoke_attention__activate_section_observable__activate_section_observable",
    "ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_ENDPOINT_REF",
    "ATTENTION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION__APPLY_SESSION_LAYOUT_TOPOLOGY_TRANSITION_PROTOCOL_BINDING",
    "invoke_attention__apply_session_layout_topology_transition__apply_session_layout_topology_transition",
    "ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_ENDPOINT_REF",
    "ATTENTION__APPLY_SESSION_LAYOUT_TRANSITION__APPLY_SESSION_LAYOUT_TRANSITION_PROTOCOL_BINDING",
    "invoke_attention__apply_session_layout_transition__apply_session_layout_transition",
    "ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_ENDPOINT_REF",
    "ATTENTION__DESCRIBE_ATTENTION_SESSION__DESCRIBE_ATTENTION_SESSION_PROTOCOL_BINDING",
    "invoke_attention__describe_attention_session__describe_attention_session",
    "ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_ENDPOINT_REF",
    "ATTENTION__DESCRIBE_ATTENTION_TRANSITION__DESCRIBE_ATTENTION_TRANSITION_PROTOCOL_BINDING",
    "invoke_attention__describe_attention_transition__describe_attention_transition",
    "ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_ENDPOINT_REF",
    "ATTENTION__GET_FOCUS_SCOPE_COMMITS__GET_FOCUS_SCOPE_COMMITS_PROTOCOL_BINDING",
    "invoke_attention__get_focus_scope_commits__get_focus_scope_commits",
    "ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_ENDPOINT_REF",
    "ATTENTION__GET_RUNTIME_MOUNT__GET_RUNTIME_MOUNT_PROTOCOL_BINDING",
    "invoke_attention__get_runtime_mount__get_runtime_mount",
    "ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_ENDPOINT_REF",
    "ATTENTION__GET_SECTION_STATE__GET_SECTION_STATE_PROTOCOL_BINDING",
    "invoke_attention__get_section_state__get_section_state",
    "ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_ENDPOINT_REF",
    "ATTENTION__LIST_ATTENTION_TRANSITIONS__LIST_ATTENTION_TRANSITIONS_PROTOCOL_BINDING",
    "invoke_attention__list_attention_transitions__list_attention_transitions",
    "ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_ENDPOINT_REF",
    "ATTENTION__MOUNT_ATTENTION_SESSION_LAYOUT__MOUNT_ATTENTION_SESSION_LAYOUT_PROTOCOL_BINDING",
    "invoke_attention__mount_attention_session_layout__mount_attention_session_layout",
    "ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_ENDPOINT_REF",
    "ATTENTION__MOUNT_ATTENTION_SESSION_SECTION__MOUNT_ATTENTION_SESSION_SECTION_PROTOCOL_BINDING",
    "invoke_attention__mount_attention_session_section__mount_attention_session_section",
    "ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_ENDPOINT_REF",
    "ATTENTION__START_ATTENTION_SESSION__START_ATTENTION_SESSION_PROTOCOL_BINDING",
    "invoke_attention__start_attention_session__start_attention_session",
    "ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_ENDPOINT_REF",
    "ATTENTION__VALIDATE_ATTENTION_TRANSITION__VALIDATE_ATTENTION_TRANSITION_PROTOCOL_BINDING",
    "invoke_attention__validate_attention_transition__validate_attention_transition",
    "ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_ENDPOINT_REF",
    "ATTENTION__WATCH_RUNTIME_MOUNT__WATCH_RUNTIME_MOUNT_PROTOCOL_BINDING",
    "invoke_attention__watch_runtime_mount__watch_runtime_mount",
    "stream_invoke_attention__watch_runtime_mount__watch_runtime_mount",
]
