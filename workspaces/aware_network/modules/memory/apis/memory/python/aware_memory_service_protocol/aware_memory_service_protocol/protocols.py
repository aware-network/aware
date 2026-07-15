# GENERATED CODE - DO NOT MODIFY BY HAND
# Compiled API service protocol package.
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Final, Protocol, TypeAlias, cast

from pydantic import BaseModel

from aware_memory_service_dto.memory.working.models import MemoryActorContextEvent, MemoryActorContextFrameEvent
from aware_memory_service_dto.memory.working.service_operation import (
    DescribeMemoryWorkingRequest,
    DescribeMemoryWorkingResponse,
    EnsureMemoryWorkingRequest,
    EnsureMemoryWorkingResponse,
    ListMemoryWorkingItemsRequest,
    ListMemoryWorkingItemsResponse,
    RecordResolvedEventMeaningRequest,
    RecordResolvedEventMeaningResponse,
    RememberAttentionTransitionRequest,
    RememberAttentionTransitionResponse,
    RememberContentRequest,
    RememberContentResponse,
    RememberEventRequest,
    RememberEventResponse,
    ResolveActorMemoryContextFrameRequest,
    ResolveActorMemoryContextFrameResponse,
    ResolveActorMemoryContextRequest,
    ResolveActorMemoryContextResponse,
    ResolveMemoryContextRequest,
    ResolveMemoryContextResponse,
    ValidateMemoryWorkingItemRequest,
    ValidateMemoryWorkingItemResponse,
    WatchActorMemoryContextFrameRequest,
    WatchActorMemoryContextFrameResponse,
    WatchActorMemoryContextRequest,
    WatchActorMemoryContextResponse,
)

API_PACKAGE_NAME: Final[str] = "memory-service-api"
API_FQN_PREFIX: Final[str] = "aware_memory_service_api"
PUBLIC_PACKAGE_IMPORT_ROOT: Final[str] = "aware_memory_service_api"


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


async def invoke_memory__describe_memory_working__describe_memory_working(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> DescribeMemoryWorkingResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = DescribeMemoryWorkingRequest.model_validate(request)
    return await typed_handler.memory.describe_memory_working.describe_memory_working(typed_request)


MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF: Final[str] = (
    "memory.describe_memory_working.describe_memory_working"
)
MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF,
        api_name="memory",
        capability_name="describe_memory_working",
        endpoint_name="describe_memory_working",
        request_type_ref="aware_memory_service_dto.memory.working.DescribeMemoryWorkingRequest",
        response_type_ref="aware_memory_service_dto.memory.working.DescribeMemoryWorkingResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_memory__describe_memory_working__describe_memory_working,
    )
)


async def invoke_memory__ensure_memory_working__ensure_memory_working(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> EnsureMemoryWorkingResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = EnsureMemoryWorkingRequest.model_validate(request)
    return await typed_handler.memory.ensure_memory_working.ensure_memory_working(typed_request)


MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF: Final[str] = (
    "memory.ensure_memory_working.ensure_memory_working"
)
MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF,
        api_name="memory",
        capability_name="ensure_memory_working",
        endpoint_name="ensure_memory_working",
        request_type_ref="aware_memory_service_dto.memory.working.EnsureMemoryWorkingRequest",
        response_type_ref="aware_memory_service_dto.memory.working.EnsureMemoryWorkingResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_memory__ensure_memory_working__ensure_memory_working,
    )
)


async def invoke_memory__list_memory_working_items__list_memory_working_items(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ListMemoryWorkingItemsResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = ListMemoryWorkingItemsRequest.model_validate(request)
    return await typed_handler.memory.list_memory_working_items.list_memory_working_items(typed_request)


MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF: Final[str] = (
    "memory.list_memory_working_items.list_memory_working_items"
)
MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF,
        api_name="memory",
        capability_name="list_memory_working_items",
        endpoint_name="list_memory_working_items",
        request_type_ref="aware_memory_service_dto.memory.working.ListMemoryWorkingItemsRequest",
        response_type_ref="aware_memory_service_dto.memory.working.ListMemoryWorkingItemsResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_memory__list_memory_working_items__list_memory_working_items,
    )
)


async def invoke_memory__record_resolved_event_meaning__record_resolved_event_meaning(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RecordResolvedEventMeaningResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = RecordResolvedEventMeaningRequest.model_validate(request)
    return await typed_handler.memory.record_resolved_event_meaning.record_resolved_event_meaning(typed_request)


MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF: Final[str] = (
    "memory.record_resolved_event_meaning.record_resolved_event_meaning"
)
MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF,
    api_name="memory",
    capability_name="record_resolved_event_meaning",
    endpoint_name="record_resolved_event_meaning",
    request_type_ref="aware_memory_service_dto.memory.working.RecordResolvedEventMeaningRequest",
    response_type_ref="aware_memory_service_dto.memory.working.RecordResolvedEventMeaningResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_memory__record_resolved_event_meaning__record_resolved_event_meaning,
)


async def invoke_memory__remember_attention_transition__remember_attention_transition(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RememberAttentionTransitionResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = RememberAttentionTransitionRequest.model_validate(request)
    return await typed_handler.memory.remember_attention_transition.remember_attention_transition(typed_request)


MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF: Final[str] = (
    "memory.remember_attention_transition.remember_attention_transition"
)
MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF,
    api_name="memory",
    capability_name="remember_attention_transition",
    endpoint_name="remember_attention_transition",
    request_type_ref="aware_memory_service_dto.memory.working.RememberAttentionTransitionRequest",
    response_type_ref="aware_memory_service_dto.memory.working.RememberAttentionTransitionResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_memory__remember_attention_transition__remember_attention_transition,
)


async def invoke_memory__remember_content__remember_content(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RememberContentResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = RememberContentRequest.model_validate(request)
    return await typed_handler.memory.remember_content.remember_content(typed_request)


MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF: Final[str] = "memory.remember_content.remember_content"
MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF,
        api_name="memory",
        capability_name="remember_content",
        endpoint_name="remember_content",
        request_type_ref="aware_memory_service_dto.memory.working.RememberContentRequest",
        response_type_ref="aware_memory_service_dto.memory.working.RememberContentResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_memory__remember_content__remember_content,
    )
)


async def invoke_memory__remember_event__remember_event(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> RememberEventResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = RememberEventRequest.model_validate(request)
    return await typed_handler.memory.remember_event.remember_event(typed_request)


MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF: Final[str] = "memory.remember_event.remember_event"
MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF,
        api_name="memory",
        capability_name="remember_event",
        endpoint_name="remember_event",
        request_type_ref="aware_memory_service_dto.memory.working.RememberEventRequest",
        response_type_ref="aware_memory_service_dto.memory.working.RememberEventResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_memory__remember_event__remember_event,
    )
)


async def invoke_memory__resolve_actor_memory_context__resolve_actor_memory_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveActorMemoryContextResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = ResolveActorMemoryContextRequest.model_validate(request)
    return await typed_handler.memory.resolve_actor_memory_context.resolve_actor_memory_context(typed_request)


MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF: Final[str] = (
    "memory.resolve_actor_memory_context.resolve_actor_memory_context"
)
MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
    api_name="memory",
    capability_name="resolve_actor_memory_context",
    endpoint_name="resolve_actor_memory_context",
    request_type_ref="aware_memory_service_dto.memory.working.ResolveActorMemoryContextRequest",
    response_type_ref="aware_memory_service_dto.memory.working.ResolveActorMemoryContextResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_memory__resolve_actor_memory_context__resolve_actor_memory_context,
)


async def invoke_memory__resolve_actor_memory_context_frame__resolve_actor_memory_context_frame(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveActorMemoryContextFrameResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = ResolveActorMemoryContextFrameRequest.model_validate(request)
    return await typed_handler.memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame(
        typed_request
    )


MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF: Final[str] = (
    "memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame"
)
MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
    api_name="memory",
    capability_name="resolve_actor_memory_context_frame",
    endpoint_name="resolve_actor_memory_context_frame",
    request_type_ref="aware_memory_service_dto.memory.working.ResolveActorMemoryContextFrameRequest",
    response_type_ref="aware_memory_service_dto.memory.working.ResolveActorMemoryContextFrameResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_memory__resolve_actor_memory_context_frame__resolve_actor_memory_context_frame,
)


async def invoke_memory__resolve_memory_context__resolve_memory_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ResolveMemoryContextResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = ResolveMemoryContextRequest.model_validate(request)
    return await typed_handler.memory.resolve_memory_context.resolve_memory_context(typed_request)


MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF: Final[str] = (
    "memory.resolve_memory_context.resolve_memory_context"
)
MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_PROTOCOL_BINDING: Final[ServiceProtocolEndpointBinding] = (
    ServiceProtocolEndpointBinding(
        endpoint_ref=MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF,
        api_name="memory",
        capability_name="resolve_memory_context",
        endpoint_name="resolve_memory_context",
        request_type_ref="aware_memory_service_dto.memory.working.ResolveMemoryContextRequest",
        response_type_ref="aware_memory_service_dto.memory.working.ResolveMemoryContextResponse",
        stream_event_type_refs=(),
        execution_protocol_ref=None,
        build_execution=None,
        stream_invoke=None,
        fulfillment_bindings=(),
        invoke=invoke_memory__resolve_memory_context__resolve_memory_context,
    )
)


async def invoke_memory__validate_memory_working_item__validate_memory_working_item(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> ValidateMemoryWorkingItemResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = ValidateMemoryWorkingItemRequest.model_validate(request)
    return await typed_handler.memory.validate_memory_working_item.validate_memory_working_item(typed_request)


MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF: Final[str] = (
    "memory.validate_memory_working_item.validate_memory_working_item"
)
MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF,
    api_name="memory",
    capability_name="validate_memory_working_item",
    endpoint_name="validate_memory_working_item",
    request_type_ref="aware_memory_service_dto.memory.working.ValidateMemoryWorkingItemRequest",
    response_type_ref="aware_memory_service_dto.memory.working.ValidateMemoryWorkingItemResponse",
    stream_event_type_refs=(),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=None,
    fulfillment_bindings=(),
    invoke=invoke_memory__validate_memory_working_item__validate_memory_working_item,
)

MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent: TypeAlias = MemoryActorContextEvent


async def invoke_memory__watch_actor_memory_context__watch_actor_memory_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> WatchActorMemoryContextResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = WatchActorMemoryContextRequest.model_validate(request)
    return await typed_handler.memory.watch_actor_memory_context.watch_actor_memory_context(typed_request)


def stream_invoke_memory__watch_actor_memory_context__watch_actor_memory_context(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent]:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = WatchActorMemoryContextRequest.model_validate(request)
    _ = execution
    return typed_handler.memory.watch_actor_memory_context.stream_watch_actor_memory_context(typed_request)


MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF: Final[str] = (
    "memory.watch_actor_memory_context.watch_actor_memory_context"
)
MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
    api_name="memory",
    capability_name="watch_actor_memory_context",
    endpoint_name="watch_actor_memory_context",
    request_type_ref="aware_memory_service_dto.memory.working.WatchActorMemoryContextRequest",
    response_type_ref="aware_memory_service_dto.memory.working.WatchActorMemoryContextResponse",
    stream_event_type_refs=("aware_memory_service_dto.memory.working.MemoryActorContextEvent",),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=stream_invoke_memory__watch_actor_memory_context__watch_actor_memory_context,
    fulfillment_bindings=(),
    invoke=invoke_memory__watch_actor_memory_context__watch_actor_memory_context,
)

MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent: TypeAlias = MemoryActorContextFrameEvent


async def invoke_memory__watch_actor_memory_context_frame__watch_actor_memory_context_frame(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> WatchActorMemoryContextFrameResponse:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = WatchActorMemoryContextFrameRequest.model_validate(request)
    return await typed_handler.memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame(typed_request)


def stream_invoke_memory__watch_actor_memory_context_frame__watch_actor_memory_context_frame(
    handler: object, request: BaseModel, execution: ServiceProtocolExecution | None = None
) -> AsyncIterator[MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent]:
    typed_handler = cast(AwareMemoryServiceProtocol, handler)
    typed_request = WatchActorMemoryContextFrameRequest.model_validate(request)
    _ = execution
    return typed_handler.memory.watch_actor_memory_context_frame.stream_watch_actor_memory_context_frame(typed_request)


MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF: Final[str] = (
    "memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame"
)
MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_PROTOCOL_BINDING: Final[
    ServiceProtocolEndpointBinding
] = ServiceProtocolEndpointBinding(
    endpoint_ref=MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
    api_name="memory",
    capability_name="watch_actor_memory_context_frame",
    endpoint_name="watch_actor_memory_context_frame",
    request_type_ref="aware_memory_service_dto.memory.working.WatchActorMemoryContextFrameRequest",
    response_type_ref="aware_memory_service_dto.memory.working.WatchActorMemoryContextFrameResponse",
    stream_event_type_refs=("aware_memory_service_dto.memory.working.MemoryActorContextFrameEvent",),
    execution_protocol_ref=None,
    build_execution=None,
    stream_invoke=stream_invoke_memory__watch_actor_memory_context_frame__watch_actor_memory_context_frame,
    fulfillment_bindings=(),
    invoke=invoke_memory__watch_actor_memory_context_frame__watch_actor_memory_context_frame,
)

ENDPOINT_BINDINGS: Final[dict[str, ServiceProtocolEndpointBinding]] = {
    MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF: MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_PROTOCOL_BINDING,
    MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF: MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_PROTOCOL_BINDING,
    MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF: MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_PROTOCOL_BINDING,
    MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF: MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_PROTOCOL_BINDING,
    MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF: MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_PROTOCOL_BINDING,
    MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF: MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_PROTOCOL_BINDING,
    MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF: MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_PROTOCOL_BINDING,
    MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF: MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_PROTOCOL_BINDING,
    MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF: MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_PROTOCOL_BINDING,
    MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF: MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_PROTOCOL_BINDING,
    MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF: MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_PROTOCOL_BINDING,
    MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF: MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_PROTOCOL_BINDING,
    MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF: MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_PROTOCOL_BINDING,
}


class MemoryDescribeMemoryWorkingCapabilityServiceProtocol(Protocol):

    async def describe_memory_working(self, request: DescribeMemoryWorkingRequest) -> DescribeMemoryWorkingResponse: ...


class MemoryEnsureMemoryWorkingCapabilityServiceProtocol(Protocol):

    async def ensure_memory_working(self, request: EnsureMemoryWorkingRequest) -> EnsureMemoryWorkingResponse: ...


class MemoryListMemoryWorkingItemsCapabilityServiceProtocol(Protocol):

    async def list_memory_working_items(
        self, request: ListMemoryWorkingItemsRequest
    ) -> ListMemoryWorkingItemsResponse: ...


class MemoryRecordResolvedEventMeaningCapabilityServiceProtocol(Protocol):

    async def record_resolved_event_meaning(
        self, request: RecordResolvedEventMeaningRequest
    ) -> RecordResolvedEventMeaningResponse: ...


class MemoryRememberAttentionTransitionCapabilityServiceProtocol(Protocol):

    async def remember_attention_transition(
        self, request: RememberAttentionTransitionRequest
    ) -> RememberAttentionTransitionResponse: ...


class MemoryRememberContentCapabilityServiceProtocol(Protocol):

    async def remember_content(self, request: RememberContentRequest) -> RememberContentResponse: ...


class MemoryRememberEventCapabilityServiceProtocol(Protocol):

    async def remember_event(self, request: RememberEventRequest) -> RememberEventResponse: ...


class MemoryResolveActorMemoryContextCapabilityServiceProtocol(Protocol):

    async def resolve_actor_memory_context(
        self, request: ResolveActorMemoryContextRequest
    ) -> ResolveActorMemoryContextResponse: ...


class MemoryResolveActorMemoryContextFrameCapabilityServiceProtocol(Protocol):

    async def resolve_actor_memory_context_frame(
        self, request: ResolveActorMemoryContextFrameRequest
    ) -> ResolveActorMemoryContextFrameResponse: ...


class MemoryResolveMemoryContextCapabilityServiceProtocol(Protocol):

    async def resolve_memory_context(self, request: ResolveMemoryContextRequest) -> ResolveMemoryContextResponse: ...


class MemoryValidateMemoryWorkingItemCapabilityServiceProtocol(Protocol):

    async def validate_memory_working_item(
        self, request: ValidateMemoryWorkingItemRequest
    ) -> ValidateMemoryWorkingItemResponse: ...


class MemoryWatchActorMemoryContextCapabilityServiceProtocol(Protocol):

    async def watch_actor_memory_context(
        self, request: WatchActorMemoryContextRequest
    ) -> WatchActorMemoryContextResponse: ...

    def stream_watch_actor_memory_context(
        self, request: WatchActorMemoryContextRequest
    ) -> AsyncIterator[MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent]: ...


class MemoryWatchActorMemoryContextFrameCapabilityServiceProtocol(Protocol):

    async def watch_actor_memory_context_frame(
        self, request: WatchActorMemoryContextFrameRequest
    ) -> WatchActorMemoryContextFrameResponse: ...

    def stream_watch_actor_memory_context_frame(
        self, request: WatchActorMemoryContextFrameRequest
    ) -> AsyncIterator[MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent]: ...


class MemoryApiServiceProtocol(Protocol):
    describe_memory_working: MemoryDescribeMemoryWorkingCapabilityServiceProtocol
    ensure_memory_working: MemoryEnsureMemoryWorkingCapabilityServiceProtocol
    list_memory_working_items: MemoryListMemoryWorkingItemsCapabilityServiceProtocol
    record_resolved_event_meaning: MemoryRecordResolvedEventMeaningCapabilityServiceProtocol
    remember_attention_transition: MemoryRememberAttentionTransitionCapabilityServiceProtocol
    remember_content: MemoryRememberContentCapabilityServiceProtocol
    remember_event: MemoryRememberEventCapabilityServiceProtocol
    resolve_actor_memory_context: MemoryResolveActorMemoryContextCapabilityServiceProtocol
    resolve_actor_memory_context_frame: MemoryResolveActorMemoryContextFrameCapabilityServiceProtocol
    resolve_memory_context: MemoryResolveMemoryContextCapabilityServiceProtocol
    validate_memory_working_item: MemoryValidateMemoryWorkingItemCapabilityServiceProtocol
    watch_actor_memory_context: MemoryWatchActorMemoryContextCapabilityServiceProtocol
    watch_actor_memory_context_frame: MemoryWatchActorMemoryContextFrameCapabilityServiceProtocol


class AwareMemoryServiceProtocol(Protocol):
    memory: MemoryApiServiceProtocol


SERVICE_PROTOCOL_RENDER_SECTION_MANIFEST_JSON: Final[str] = (
    "{"
    '  "contract_version": "aware.api.service-protocol-section-text-manifest.v1",'
    '  "described_sections_text_digest": "sha256:a0049baa0b902b018d4e16d4f8f10d792798a2ddfeb0028efdaceb445db2e8cf",'
    '  "manifest_digests_cover_manifest_section": false,'
    '  "manifest_kind": "api_service_protocol_section_text_manifest",'
    '  "renderer_key": "PythonApiServiceProtocolRendererLanguage",'
    '  "section_count": 58,'
    '  "sections": ['
    "    {"
    '      "line_count": 17,'
    '      "rendered_text_digest": "sha256:4a674ff96a4d4bc9612783cce02b7298d6e2bb9844ad1504509adca1ec032c37",'
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
    '      "section_key": "api.service_protocol.endpoint_execution:memory.describe_memory_working.describe_memory_working",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 2'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.ensure_memory_working.ensure_memory_working",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 3'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.list_memory_working_items.list_memory_working_items",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 4'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.record_resolved_event_meaning.record_resolved_event_meaning",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 5'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.remember_attention_transition.remember_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 6'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.remember_content.remember_content",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 7'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.remember_event.remember_event",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 8'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.resolve_actor_memory_context.resolve_actor_memory_context",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 9'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 10'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.resolve_memory_context.resolve_memory_context",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 11'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.validate_memory_working_item.validate_memory_working_item",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 12'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.watch_actor_memory_context.watch_actor_memory_context",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 13'
    "    },"
    "    {"
    '      "line_count": 0,'
    '      "rendered_text_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",'
    '      "section_key": "api.service_protocol.endpoint_execution:memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_endpoint_execution",'
    '      "section_order": 14'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:e65b85e9627198ac85828cbb324d2b7742a9aaf42a47a975d00f0e42e8255884",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.describe_memory_working.describe_memory_working",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 15'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:4839f2ec846283fb1d2721e7f3e2732609dfdc36fe6e5c4fa1bf1a9c6613922c",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.describe_memory_working.describe_memory_working",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 16'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:9f7ff9b2f508f4c7b510f589dbf386baa51555e5e71b52599b907d5eae777164",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.ensure_memory_working.ensure_memory_working",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 17'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:703f41209d6c0c161cd0947799e5d20755c1c0d54795e71942ebc3e111f78951",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.ensure_memory_working.ensure_memory_working",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 18'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:86889dc3400bf049ada3121f0c4ff8f8a831dae723bf83be3e4bf3525e8fe35b",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.list_memory_working_items.list_memory_working_items",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 19'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:f7bb29645846ed7430fb3eeff133a0c6f6c607350487241d302a68e4e3c35cb1",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.list_memory_working_items.list_memory_working_items",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 20'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:05d6028e69bf6d3fa882351ac1eb91b02454e4b71c8711cf6c37cd2545b75990",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.record_resolved_event_meaning.record_resolved_event_meaning",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 21'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:5a0b189efe70b1bcc08c091dff244435191e111f8ed0a1891317df39acf63ca3",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.record_resolved_event_meaning.record_resolved_event_meaning",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 22'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:68c550fbfd3915604a96ff6292ce76e46d8641c1513fe722c5e87e0c74d4d373",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.remember_attention_transition.remember_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 23'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0d706b2432620957c07236d0f59da0c9e12c49cd275206759c32d293d157b6da",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.remember_attention_transition.remember_attention_transition",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 24'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:1624c45cdbaa50f8c95bf1914d019a30fe1c27c00e18b2cbb9dd7bbb7243c555",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.remember_content.remember_content",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 25'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:67197028f3f7b33cf5b5bdb950a494dc2bae4b4ead38c76d9f91e7b18c69547b",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.remember_content.remember_content",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 26'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:d82cd6fe51d92f8f6f54f02bca7fb507df22e754c59cf34061a007c61c196d80",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.remember_event.remember_event",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 27'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:d0756bffc6090fe9a1399a18905b275318607f5be616e3dcc5efb106fe385dfc",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.remember_event.remember_event",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 28'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:0111f234078cd231217c583ec45d4e0c17ffac6038da79484b53bd86f64884df",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.resolve_actor_memory_context.resolve_actor_memory_context",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 29'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:0ff9812822d6aa81566595fb8d3325cb95d9658ba99ad5baef1a4189328ce3b8",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.resolve_actor_memory_context.resolve_actor_memory_context",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 30'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:9693d91ec7b2344db87b02d878334d4af50b6d8a2a73ef57bd69d926f2db3006",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 31'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:53e7942460c6f3c01c17812153daa5debc0948cca0f7ccca36686f92a3420b31",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.resolve_actor_memory_context_frame.resolve_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 32'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:61ecc827d93ff25b236e4484130a61c765f74b9ea75704b133f320f1155e1f6a",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.resolve_memory_context.resolve_memory_context",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 33'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:e84e1cf76fb5ee5bd0aaa1f9d5401bbf7b93ba6ad4daf101ff24a62e85b413f6",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.resolve_memory_context.resolve_memory_context",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 34'
    "    },"
    "    {"
    '      "line_count": 5,'
    '      "rendered_text_digest": "sha256:64e2b3f7df3e694a67c3069e4761c96183ea4c5e66a4097291d1147a225b1aab",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.validate_memory_working_item.validate_memory_working_item",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 35'
    "    },"
    "    {"
    '      "line_count": 18,'
    '      "rendered_text_digest": "sha256:2e94ea7ad07baa5436e35e599e6dacdc76a68d56ae47ed1986a9e893c50f42fa",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.validate_memory_working_item.validate_memory_working_item",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 36'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:ec80b6faf83eacfdac8809c9954154c5e64bbc13febd5e1c4b744958d88ac544",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.watch_actor_memory_context.watch_actor_memory_context",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 37'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:16f7b32855bf92e7c65582c7739ad508a80618398ece13be474fcc92c8a06cb7",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.watch_actor_memory_context.watch_actor_memory_context",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 38'
    "    },"
    "    {"
    '      "line_count": 12,'
    '      "rendered_text_digest": "sha256:13246f7037764b8cd41310c0bf62180dde634768962410fcb8cc9d277857cc4c",'
    '      "section_key": "api.service_protocol.endpoint_invoker:memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_endpoint_invoker",'
    '      "section_order": 39'
    "    },"
    "    {"
    '      "line_count": 19,'
    '      "rendered_text_digest": "sha256:df68d19ef12f5c8913a904fa6d1512d643825af7384569b949f0829931b8a8ca",'
    '      "section_key": "api.service_protocol.endpoint_binding:memory.watch_actor_memory_context_frame.watch_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_endpoint_binding",'
    '      "section_order": 40'
    "    },"
    "    {"
    '      "line_count": 16,'
    '      "rendered_text_digest": "sha256:c06930b58f6aa3f59e1953e2b5678de4b16a7451abc4ab8bed71b7ca778cda3b",'
    '      "section_key": "api.service_protocol.endpoint_bindings_index",'
    '      "section_kind": "service_protocol_endpoint_binding_index",'
    '      "section_order": 41'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:2e5024a36b25e298c02ca2329e18469f06ef4c6ac423dec3d1eb8365ed8b80eb",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.describe_memory_working",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 42'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:eef15b2ead429d70f2511ca2825bd291dd5e79c53713ad1e7e19020e68afcf79",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.ensure_memory_working",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 43'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:4337ca6cbe9c66a63fa9b31e5f2ba54904bc2cac457bd2492054828a07e1f0f2",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.list_memory_working_items",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 44'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:dd6abcb1661df4800f1781db6ae9a4f2892efafb8797e680cdf6b39dfed0405e",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.record_resolved_event_meaning",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 45'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:b8bf80631d657ad5b15d90899503bb56d8f7e5ad983135e409877677244ff149",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.remember_attention_transition",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 46'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:8e400c673b6f4c9b0d94eccbbb9cac67786ba6943b7cbb799c10b212ac0a7f64",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.remember_content",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 47'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:f5c997dea2b31fb14f4111f5c44f1d45adeb86889c313720ea4a7e96dc869d23",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.remember_event",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 48'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:d27bd61cc8fc8daa4bb303123ffd11994371f5df505ce1145035cb436c6d17d0",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.resolve_actor_memory_context",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 49'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:b63bffc0c0f47cfddc6f87935d287403c0401e3722f4c9b9c18558560971b157",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.resolve_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 50'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:6be5e9c74b23c3f1bb317b992cd5064963692bf993539439dbddcd9bb377599f",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.resolve_memory_context",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 51'
    "    },"
    "    {"
    '      "line_count": 4,'
    '      "rendered_text_digest": "sha256:fd3eb968b4a2d0e204ec23c1b5acde506ae58776bacc2b3c3cb6a30577f0e108",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.validate_memory_working_item",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 52'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:f109deefc485074c212626afb2ee7758b3e54577f3cc3505ec252ab6a1101807",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.watch_actor_memory_context",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 53'
    "    },"
    "    {"
    '      "line_count": 6,'
    '      "rendered_text_digest": "sha256:0913e265df6bb02804a063db196dc0ed41137c3c86b3fd6765520b921f83a2ca",'
    '      "section_key": "api.service_protocol.capability_protocol:memory.watch_actor_memory_context_frame",'
    '      "section_kind": "service_protocol_capability_protocol",'
    '      "section_order": 54'
    "    },"
    "    {"
    '      "line_count": 15,'
    '      "rendered_text_digest": "sha256:93b18ff155df56707a9a352ccce91523b3780fa145ab237e088d541c600d708e",'
    '      "section_key": "api.service_protocol.api_protocol:memory",'
    '      "section_kind": "service_protocol_api_protocol",'
    '      "section_order": 55'
    "    },"
    "    {"
    '      "line_count": 3,'
    '      "rendered_text_digest": "sha256:4d44292b2d1df92a9e8eeb69cb46daa6334ce76e205d720975dea6ef18f2d918",'
    '      "section_key": "api.service_protocol.root_protocol",'
    '      "section_kind": "service_protocol_root_protocol",'
    '      "section_order": 56'
    "    },"
    "    {"
    '      "line_count": 72,'
    '      "rendered_text_digest": "sha256:82ac9ad85b4efa139ea1380373d5609f43af4e38dd0a2d554f8d183235c48af8",'
    '      "section_key": "api.service_protocol.__all__",'
    '      "section_kind": "service_protocol_module_exports",'
    '      "section_order": 57'
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
    "AwareMemoryServiceProtocol",
    "MemoryApiServiceProtocol",
    "MemoryDescribeMemoryWorkingCapabilityServiceProtocol",
    "MemoryEnsureMemoryWorkingCapabilityServiceProtocol",
    "MemoryListMemoryWorkingItemsCapabilityServiceProtocol",
    "MemoryRecordResolvedEventMeaningCapabilityServiceProtocol",
    "MemoryRememberAttentionTransitionCapabilityServiceProtocol",
    "MemoryRememberContentCapabilityServiceProtocol",
    "MemoryRememberEventCapabilityServiceProtocol",
    "MemoryResolveActorMemoryContextCapabilityServiceProtocol",
    "MemoryResolveActorMemoryContextFrameCapabilityServiceProtocol",
    "MemoryResolveMemoryContextCapabilityServiceProtocol",
    "MemoryValidateMemoryWorkingItemCapabilityServiceProtocol",
    "MemoryWatchActorMemoryContextCapabilityServiceProtocol",
    "MemoryWatchActorMemoryContextFrameCapabilityServiceProtocol",
    "MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent",
    "MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent",
    "MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF",
    "MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_PROTOCOL_BINDING",
    "invoke_memory__describe_memory_working__describe_memory_working",
    "MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF",
    "MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_PROTOCOL_BINDING",
    "invoke_memory__ensure_memory_working__ensure_memory_working",
    "MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF",
    "MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_PROTOCOL_BINDING",
    "invoke_memory__list_memory_working_items__list_memory_working_items",
    "MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF",
    "MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_PROTOCOL_BINDING",
    "invoke_memory__record_resolved_event_meaning__record_resolved_event_meaning",
    "MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF",
    "MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_PROTOCOL_BINDING",
    "invoke_memory__remember_attention_transition__remember_attention_transition",
    "MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF",
    "MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_PROTOCOL_BINDING",
    "invoke_memory__remember_content__remember_content",
    "MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF",
    "MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_PROTOCOL_BINDING",
    "invoke_memory__remember_event__remember_event",
    "MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF",
    "MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_PROTOCOL_BINDING",
    "invoke_memory__resolve_actor_memory_context__resolve_actor_memory_context",
    "MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF",
    "MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_PROTOCOL_BINDING",
    "invoke_memory__resolve_actor_memory_context_frame__resolve_actor_memory_context_frame",
    "MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF",
    "MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_PROTOCOL_BINDING",
    "invoke_memory__resolve_memory_context__resolve_memory_context",
    "MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF",
    "MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_PROTOCOL_BINDING",
    "invoke_memory__validate_memory_working_item__validate_memory_working_item",
    "MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF",
    "MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_PROTOCOL_BINDING",
    "invoke_memory__watch_actor_memory_context__watch_actor_memory_context",
    "stream_invoke_memory__watch_actor_memory_context__watch_actor_memory_context",
    "MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF",
    "MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_PROTOCOL_BINDING",
    "invoke_memory__watch_actor_memory_context_frame__watch_actor_memory_context_frame",
    "stream_invoke_memory__watch_actor_memory_context_frame__watch_actor_memory_context_frame",
]
