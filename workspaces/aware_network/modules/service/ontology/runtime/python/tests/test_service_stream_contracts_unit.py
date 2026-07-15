from __future__ import annotations

from uuid import uuid4

from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceStreamControlKind,
    ServiceStreamControlRequest,
    ServiceStreamControlResponse,
    ServiceStreamSession,
)


def _context() -> ServiceOperationContext:
    return ServiceOperationContext(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="service.stream.contracts",
    )


def test_service_stream_session_keeps_parent_request_and_parties() -> None:
    request = ServiceOperationRequest(
        context=_context(),
        service="agent",
        operation={"prompt": "hello"},
        stream_target_id=uuid4(),
        stream_correlation_id=uuid4(),
    )

    session = ServiceStreamSession(
        session_id=uuid4(),
        request=request,
        publisher_id="service-host",
        subscriber_id="interface",
    )

    assert session.request == request
    assert session.publisher_id == "service-host"
    assert session.subscriber_id == "interface"


def test_service_stream_control_response_keeps_semantic_outcome() -> None:
    session_id = uuid4()
    request = ServiceStreamControlRequest(
        session_id=session_id,
        kind=ServiceStreamControlKind.CLOSE_SESSION,
        reason="completed",
    )
    response = ServiceStreamControlResponse(
        session_id=session_id,
        kind=request.kind,
        status=RequestStatus.succeeded,
        detail_payload={"final": True},
    )

    assert response.session_id == request.session_id
    assert response.kind is ServiceStreamControlKind.CLOSE_SESSION
    assert response.status is RequestStatus.succeeded
    assert response.detail_payload == {"final": True}
