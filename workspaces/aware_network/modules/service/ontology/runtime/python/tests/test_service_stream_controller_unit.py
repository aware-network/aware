from __future__ import annotations

from uuid import uuid4

import pytest

from aware_service_runtime import (
    InMemoryServiceStreamController,
    RequestStatus,
    ServiceDuplexStreamEventEnvelope,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceStreamControlKind,
    ServiceStreamControlRequest,
    ServiceStreamEventEnvelope,
    ServiceStreamEventKind,
    ServiceStreamSession,
)


def _request() -> ServiceOperationRequest:
    return ServiceOperationRequest(
        context=ServiceOperationContext(
            actor_id=uuid4(),
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="service.stream.controller",
        ),
        service="agent",
        operation={"operation": "start"},
        stream_target_id=uuid4(),
        stream_correlation_id=uuid4(),
    )


@pytest.mark.asyncio
async def test_stream_controller_opens_and_closes_session() -> None:
    controller = InMemoryServiceStreamController()
    session = ServiceStreamSession(
        session_id=uuid4(),
        request=_request(),
        publisher_id="agent.inference",
        subscriber_id="node:test",
    )

    opened = await controller.open_stream_session(session=session)
    closed = await controller.send_stream_control(
        request=ServiceStreamControlRequest(
            session_id=session.session_id,
            kind=ServiceStreamControlKind.CLOSE_SESSION,
            reason="complete",
        )
    )

    assert opened.status is RequestStatus.succeeded
    assert closed.status is RequestStatus.succeeded
    assert controller.get_session(session_id=session.session_id) is None


@pytest.mark.asyncio
async def test_stream_controller_rejects_duplicate_open() -> None:
    controller = InMemoryServiceStreamController()
    session = ServiceStreamSession(
        session_id=uuid4(),
        request=_request(),
    )

    first = await controller.open_stream_session(session=session)
    duplicate = await controller.open_stream_session(session=session)

    assert first.status is RequestStatus.succeeded
    assert duplicate.status is RequestStatus.failed
    assert "already exists" in (duplicate.error or "")


@pytest.mark.asyncio
async def test_stream_controller_accepts_then_cancels_session() -> None:
    controller = InMemoryServiceStreamController()
    session = ServiceStreamSession(
        session_id=uuid4(),
        request=_request(),
    )
    await controller.open_stream_session(session=session)

    accepted = await controller.handle_stream_control(
        request=ServiceStreamControlRequest(
            session_id=session.session_id,
            kind=ServiceStreamControlKind.ACCEPT_SESSION,
        )
    )
    cancelled = await controller.send_stream_control(
        request=ServiceStreamControlRequest(
            session_id=session.session_id,
            kind=ServiceStreamControlKind.CANCEL_SESSION,
            reason="client-requested",
        )
    )

    assert accepted.status is RequestStatus.succeeded
    assert cancelled.status is RequestStatus.succeeded
    assert controller.get_session(session_id=session.session_id) is None


def test_service_stream_event_envelope_roundtrips_through_duplex_model() -> None:
    session = ServiceStreamSession(
        session_id=uuid4(),
        request=_request(),
        publisher_id="streaming",
        subscriber_id="node:test",
    )
    envelope = ServiceStreamEventEnvelope(
        session=session,
        sequence=1,
        kind=ServiceStreamEventKind.NOTICE,
        item_key="item-1",
        payload={"phase": "booting"},
    )

    restored = ServiceDuplexStreamEventEnvelope.from_contract(envelope).to_contract()

    assert restored.sequence == 1
    assert restored.kind is ServiceStreamEventKind.NOTICE
    assert restored.item_key == "item-1"
    assert restored.payload == {"phase": "booting"}
    assert restored.session.request.service == "agent"
