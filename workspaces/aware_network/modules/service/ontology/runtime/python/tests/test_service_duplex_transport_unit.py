from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest
from pydantic import BaseModel
from aware_code.types import JsonObject
from aware_code.types import JsonValue
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationContext,
)

from aware_service_runtime.adapters.environment import (
    build_environment_service_operation_request,
    build_service_operation_result_from_response,
)
from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceHostApiIngressRequest,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    ServiceStreamControlKind,
    ServiceStreamControlRequest,
    ServiceStreamControlResponse,
    ServiceStreamSession,
    StreamLifecycle,
)
from aware_service_runtime.duplex import (
    ServiceDuplexApiIngressRequest,
    ServiceDuplexOperationRequest,
    ServiceDuplexOperationResponse,
    ServiceDuplexStreamControlRequest,
    ServiceDuplexStreamControlResponse,
    ServiceDuplexStreamEvent,
    ServiceDuplexStreamEventKind,
    ServiceDuplexStreamSession,
    dump_service_duplex_payload,
)


class _PayloadModel(BaseModel):
    value: int
    label: str


def _context() -> ServiceOperationContext:
    return ServiceOperationContext(
        actor_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="service.duplex.test",
    )


def test_service_duplex_request_roundtrips_json_payloads() -> None:
    request = ServiceOperationRequest(
        context=_context(),
        service="workspace",
        operation=_PayloadModel(value=7, label="ok").model_dump(mode="json"),
        stream_target_id=uuid4(),
        stream_correlation_id=uuid4(),
        network_request_id=uuid4(),
    )

    model = ServiceDuplexOperationRequest.from_contract(request)
    restored = model.to_contract()

    assert model.operation == {"value": 7, "label": "ok"}
    assert restored.context == request.context
    assert restored.service == request.service
    assert restored.operation == {"value": 7, "label": "ok"}
    assert restored.stream_target_id == request.stream_target_id
    assert restored.stream_correlation_id == request.stream_correlation_id
    assert restored.network_request_id == request.network_request_id


def test_service_duplex_api_ingress_request_roundtrips_target_lane() -> None:
    target_branch_id = uuid4()
    request = ServiceHostApiIngressRequest(
        actor_id=uuid4(),
        endpoint_ref="home_devices.open_door.open_door",
        discriminant="home_devices.open_door.open_door",
        request_payload=cast(JsonObject, {"label": "Front Door"}),
        network_request_id=uuid4(),
        target_branch_id=target_branch_id,
        target_projection_hash="home-projection",
    )

    model = ServiceDuplexApiIngressRequest.from_contract(request)
    restored = model.to_contract()

    assert model.target_branch_id == target_branch_id
    assert model.target_projection_hash == "home-projection"
    assert restored == request


def test_service_duplex_api_ingress_request_roundtrips_invocation_context() -> None:
    focus_scope_id = uuid4()
    layout_section_id = uuid4()
    request = ServiceHostApiIngressRequest(
        actor_id=uuid4(),
        endpoint_ref="conversation.add_message.add_message",
        discriminant="conversation.add_message.add_message",
        request_payload=cast(JsonObject, {"text": "hello"}),
        invocation_context=cast(
            JsonObject,
            {
                "surface": {
                    "window_key": "main",
                    "layout_key": "control",
                    "section_key": "conversation",
                },
                "attention": {
                    "layout_section_id": layout_section_id,
                    "focus_scope_id": focus_scope_id,
                },
            },
        ),
        network_request_id=uuid4(),
    )

    model = ServiceDuplexApiIngressRequest.from_contract(request)
    restored = model.to_contract()

    expected_context = {
        "surface": {
            "window_key": "main",
            "layout_key": "control",
            "section_key": "conversation",
        },
        "attention": {
            "layout_section_id": str(layout_section_id),
            "focus_scope_id": str(focus_scope_id),
        },
    }
    assert model.invocation_context == expected_context
    assert restored.invocation_context == expected_context


def test_service_duplex_response_roundtrips_environment_payload_mappings() -> None:
    payload: JsonValue = {
        "service": "custom_service",
        "operation": "status_get",
        "kwargs": {"phase": "boot"},
    }
    response = ServiceOperationResponse(
        status=RequestStatus.succeeded,
        response_payload=payload,
        stream_lifecycle=StreamLifecycle.started,
    )

    model = ServiceDuplexOperationResponse.from_contract(response)
    result = build_service_operation_result_from_response(response=model.to_contract())

    assert model.response_payload == {
        "service": "custom_service",
        "operation": "status_get",
        "kwargs": {"phase": "boot"},
    }
    assert result.response_service_operation is not None
    assert result.response_service_operation.model_dump() == {
        "service": "custom_service",
        "operation": "status_get",
        "kwargs": {"phase": "boot"},
    }
    assert result.stream_lifecycle is StreamLifecycle.started


def test_environment_adapter_accepts_mapping_payloads_after_duplex_decode() -> None:
    request = ServiceDuplexOperationRequest(
        context=ServiceDuplexOperationRequest.from_contract(
            ServiceOperationRequest(
                context=_context(),
                service="custom_service",
                operation={
                    "service": "custom_service",
                    "operation": "create_issue",
                },
            )
        ).context,
        service="custom_service",
        operation={
            "service": "custom_service",
            "operation": "create_issue",
            "args": [],
            "kwargs": {"title": "test"},
        },
    ).to_contract()

    env_req = build_environment_service_operation_request(
        request=request,
        environment_context=EnvironmentOperationContext(
            actor_id=request.context.actor_id,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=request.context.branch_id,
            projection_hash=request.context.projection_hash,
        ),
    )

    assert env_req.service_operation.model_dump() == {
        "service": "custom_service",
        "operation": "create_issue",
        "args": [],
        "kwargs": {"title": "test"},
    }


def test_service_duplex_stream_event_validates_shape() -> None:
    response = ServiceOperationResponse(
        status=RequestStatus.pending,
        response_payload={"phase": "boot"},
        stream_lifecycle=StreamLifecycle.started,
    )

    event = ServiceDuplexStreamEvent.response_event(response)

    assert event.kind is ServiceDuplexStreamEventKind.RESPONSE
    assert event.response is not None
    assert event.response.response_payload == {"phase": "boot"}

    close_event = ServiceDuplexStreamEvent.close_event()
    assert close_event.kind is ServiceDuplexStreamEventKind.CLOSE
    assert close_event.response is None

    with pytest.raises(ValueError):
        ServiceDuplexStreamEvent(kind=ServiceDuplexStreamEventKind.RESPONSE)

    with pytest.raises(ValueError):
        ServiceDuplexStreamEvent(
            kind=ServiceDuplexStreamEventKind.CLOSE,
            response=ServiceDuplexOperationResponse.from_contract(response),
        )


def test_service_duplex_stream_session_roundtrips() -> None:
    request = ServiceOperationRequest(
        context=_context(),
        service="agent",
        operation={"mode": "stream"},
        stream_correlation_id=uuid4(),
    )
    session = ServiceStreamSession(
        session_id=uuid4(),
        request=request,
        publisher_id="service-host",
        subscriber_id="cli",
    )

    model = ServiceDuplexStreamSession.from_contract(session)
    restored = model.to_contract()

    assert restored == session
    assert model.request.service == "agent"
    assert model.request.operation == {"mode": "stream"}


def test_service_duplex_stream_control_roundtrips() -> None:
    request = ServiceStreamControlRequest(
        session_id=uuid4(),
        kind=ServiceStreamControlKind.OPEN_SESSION,
        reason="bootstrap",
        detail_payload={"budget": {"max_ms": 5000}},
    )
    response = ServiceStreamControlResponse(
        session_id=request.session_id,
        kind=request.kind,
        status=RequestStatus.succeeded,
        detail_payload={"accepted": True},
    )

    request_model = ServiceDuplexStreamControlRequest.from_contract(request)
    response_model = ServiceDuplexStreamControlResponse.from_contract(response)

    assert request_model.to_contract() == request
    assert response_model.to_contract() == response
    assert request_model.detail_payload == {"budget": {"max_ms": 5000}}
    assert response_model.detail_payload == {"accepted": True}


def test_dump_service_duplex_payload_rejects_non_serializable_values() -> None:
    with pytest.raises(TypeError):
        dump_service_duplex_payload(object())
