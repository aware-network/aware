from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID, uuid4

from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceHostApiIngressRequest,
    ServiceOperationRequest,
    ServiceOperationResponse,
    ServiceStreamEventEnvelope,
    ServiceStreamEventKind,
    ServiceStreamSession,
    StreamLifecycle,
)
from aware_service_runtime.duplex import (
    ServiceDuplexStreamEvent,
    ServiceDuplexStreamEventEnvelope,
)


StreamEventEmitter = Callable[[ServiceDuplexStreamEvent], Awaitable[None]]


@dataclass(slots=True)
class ActiveDuplexStream:
    emit_event: StreamEventEmitter
    session_id: UUID
    next_sequence: int = 1


_active_duplex_stream: ContextVar[ActiveDuplexStream | None] = ContextVar(
    "aware_service_service_active_duplex_stream",
    default=None,
)


@contextmanager
def duplex_stream_context(
    *,
    emit_event: StreamEventEmitter,
    session_id: UUID,
) -> Iterator[ActiveDuplexStream]:
    stream = ActiveDuplexStream(
        emit_event=emit_event,
        session_id=session_id,
    )
    token = _active_duplex_stream.set(stream)
    try:
        yield stream
    finally:
        _active_duplex_stream.reset(token)


def active_duplex_stream_session_id() -> UUID | None:
    stream = _active_duplex_stream.get()
    if stream is None:
        return None
    return stream.session_id


async def run_duplex_service_request(
    *,
    request: ServiceOperationRequest,
    emit_event: StreamEventEmitter,
    handle_request: Callable[..., Awaitable[ServiceOperationResponse]],
) -> ServiceOperationResponse:
    with duplex_stream_context(
        emit_event=emit_event,
        session_id=service_operation_duplex_session_id(request=request),
    ):
        return await handle_request(request=request)


async def run_duplex_service_notification(
    *,
    request: ServiceOperationRequest,
    emit_event: StreamEventEmitter,
    handle_notification: Callable[..., Awaitable[None]],
) -> None:
    with duplex_stream_context(
        emit_event=emit_event,
        session_id=service_operation_duplex_session_id(request=request),
    ):
        await handle_notification(request=request)


async def run_duplex_api_ingress_request(
    *,
    request: ServiceHostApiIngressRequest,
    emit_event: StreamEventEmitter,
    handle_api_ingress_request: Callable[..., Awaitable[ServiceOperationResponse]],
) -> ServiceOperationResponse:
    if not request.stream_requested:
        return await handle_api_ingress_request(request=request)
    with duplex_stream_context(
        emit_event=emit_event,
        session_id=api_ingress_duplex_session_id(request=request),
    ):
        return await handle_api_ingress_request(request=request)


def service_operation_duplex_session_id(
    *,
    request: ServiceOperationRequest,
) -> UUID:
    return request.stream_correlation_id or request.stream_target_id or uuid4()


def api_ingress_duplex_session_id(
    *,
    request: ServiceHostApiIngressRequest,
) -> UUID:
    return request.network_request_id or uuid4()


async def send_duplex_service_response(
    *,
    request: ServiceOperationRequest,
    response: ServiceOperationResponse,
) -> None:
    duplex_response = response
    if should_wrap_stream_response(response=response):
        envelope = build_stream_event_envelope(
            request=request,
            response=response,
        )
        duplex_response = ServiceOperationResponse(
            status=response.status,
            error=response.error,
            response_payload=ServiceDuplexStreamEventEnvelope.from_contract(
                envelope
            ).model_dump(mode="json"),
            stream_lifecycle=response.stream_lifecycle,
        )
    await emit_duplex_stream_event(
        ServiceDuplexStreamEvent.response_event(duplex_response)
    )


async def close_duplex_service_stream() -> None:
    await emit_duplex_stream_event(ServiceDuplexStreamEvent.close_event())


async def emit_duplex_stream_event(event: ServiceDuplexStreamEvent) -> None:
    stream = _active_duplex_stream.get()
    if stream is None:
        raise RuntimeError(
            "Standalone Service host stream transport requires an active "
            "duplex IPC session."
        )
    await stream.emit_event(event)


def should_wrap_stream_response(*, response: ServiceOperationResponse) -> bool:
    return (
        _active_duplex_stream.get() is not None
        and response.stream_lifecycle is StreamLifecycle.started
    )


def build_stream_event_envelope(
    *,
    request: ServiceOperationRequest,
    response: ServiceOperationResponse,
) -> ServiceStreamEventEnvelope:
    stream = _active_duplex_stream.get()
    if stream is None:
        raise RuntimeError(
            "Service stream event envelope requires an active duplex stream context."
        )
    envelope = ServiceStreamEventEnvelope(
        session=ServiceStreamSession(
            session_id=stream.session_id,
            request=request,
            publisher_id=request.service,
            subscriber_id=(
                str(request.context.actor_id)
                if request.context.actor_id is not None
                else None
            ),
        ),
        sequence=stream.next_sequence,
        kind=(
            ServiceStreamEventKind.EVENT_ERROR
            if response.status is RequestStatus.failed
            else ServiceStreamEventKind.NOTICE
        ),
        item_key=(
            request.api_dispatch.operation_key
            if request.api_dispatch is not None
            else str(request.stream_target_id or stream.session_id)
        ),
        payload=response.response_payload,
    )
    stream.next_sequence += 1
    return envelope


__all__ = [
    "ActiveDuplexStream",
    "StreamEventEmitter",
    "active_duplex_stream_session_id",
    "api_ingress_duplex_session_id",
    "build_stream_event_envelope",
    "close_duplex_service_stream",
    "duplex_stream_context",
    "emit_duplex_stream_event",
    "run_duplex_api_ingress_request",
    "run_duplex_service_notification",
    "run_duplex_service_request",
    "send_duplex_service_response",
    "service_operation_duplex_session_id",
    "should_wrap_stream_response",
]
