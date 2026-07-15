from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest

from aware_types import JsonObject, JsonValue
from aware_comms import (
    DuplexIpcEndpoint,
    DuplexIpcFrameCodec,
    DuplexMessageFrame,
    DuplexMessageFrameType,
)
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_service_runtime import (
    RequestStatus,
    ServiceDuplexLaneCommitReceiptNotification,
    ServiceDuplexOperationRequest,
    ServiceDuplexOperationResponse,
    ServiceDuplexStreamEvent,
    ServiceHostDuplexClient,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    StreamLifecycle,
)
from aware_service_runtime.contracts import ServiceHostApiIngressRequest
from aware_service_runtime.contracts import ServiceApiDispatchReceipt
from aware_service_runtime.duplex import ServiceDuplexApiIngressRequest
from aware_service_runtime.duplex import service_duplex_model_from_frame
from aware_service_runtime.duplex import (
    service_duplex_operation_response_payload_from_contract,
)
from aware_service_runtime.duplex import service_duplex_payload_from_model
from aware_service_runtime.duplex import service_duplex_trusted_json_payload


async def _start_fake_server(
    *,
    socket_path: Path,
    handler: Callable[
        [asyncio.StreamReader, asyncio.StreamWriter],
        Awaitable[None],
    ],
) -> asyncio.AbstractServer:
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()
    return await asyncio.start_unix_server(handler, path=str(socket_path))


def _request() -> ServiceOperationRequest:
    return ServiceOperationRequest(
        context=ServiceOperationContext(
            actor_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="service.host.client.test",
        ),
        service="workflow_issue",
        operation={"operation": "create_issue"},
    )


def test_service_duplex_operation_response_fast_payload_round_trips() -> None:
    api_call_id = uuid4()
    response_payload = {"accepted": True}
    diagnostics = cast(
        JsonObject,
        {
            "servicehost_duplex_server_timings_s": {
                "duplex_server.response_model_dump_s": 0.001,
            },
        },
    )
    response = ServiceOperationResponse(
        status=RequestStatus.succeeded,
        response_payload=cast(JsonValue, response_payload),
        receipt=ServiceApiDispatchReceipt(
            endpoint_ref="workspace.delta_preview.preview",
            discriminant="workspace.delta_preview.preview",
            api_call_id=api_call_id,
        ),
        stream_lifecycle=StreamLifecycle.closed,
    )
    payload = service_duplex_operation_response_payload_from_contract(
        response,
        transport_diagnostics=diagnostics,
    )

    assert isinstance(payload, dict)
    assert payload["response_payload"] is response.response_payload
    assert payload["transport_diagnostics"] is diagnostics

    duplex_response = ServiceDuplexOperationResponse.model_validate(payload)
    round_tripped = duplex_response.to_contract()

    assert round_tripped.status is RequestStatus.succeeded
    assert round_tripped.response_payload == {"accepted": True}
    assert round_tripped.stream_lifecycle is StreamLifecycle.closed
    assert round_tripped.receipt is not None
    assert round_tripped.receipt.api_call_id == api_call_id
    assert duplex_response.transport_diagnostics == diagnostics


def test_service_duplex_trusted_json_payload_skips_recursive_copy() -> None:
    payload = {"items": [{"accepted": True}], "count": 1}

    trusted = service_duplex_trusted_json_payload(cast(JsonValue, payload))

    assert trusted is payload


def test_service_duplex_trusted_json_payload_rejects_non_json_contracts() -> None:
    receipt = ServiceApiDispatchReceipt(
        endpoint_ref="workspace.delta_preview.preview",
        discriminant="workspace.delta_preview.preview",
    )

    with pytest.raises(TypeError, match="already be a JSON value"):
        service_duplex_trusted_json_payload(cast(JsonValue, cast(object, receipt)))


@pytest.mark.asyncio
async def test_service_host_duplex_client_sends_unary_requests(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "aware-service-client.sock"

    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            line = await reader.readline()
            frame = DuplexIpcFrameCodec.decode_frame(line)
            assert frame.payload is not None
            request = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexOperationRequest,
            )
            assert request.service == "workflow_issue"
            writer.write(
                DuplexIpcFrameCodec.encode_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.RESPONSE,
                        request_id=frame.id,
                        payload=service_duplex_payload_from_model(
                            ServiceDuplexOperationResponse.from_contract(
                                ServiceOperationResponse(
                                    status=RequestStatus.succeeded,
                                    response_payload={"accepted": True},
                                )
                            )
                        ),
                    )
                )
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await _start_fake_server(socket_path=socket_path, handler=_handle)
    client = ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    )
    try:
        response = await client.send_request(request=_request(), timeout_s=2.0)
    finally:
        server.close()
        await server.wait_closed()

    assert response.status is RequestStatus.succeeded
    assert response.response_payload == {"accepted": True}
    timings = client.last_request_timings_s
    assert "duplex_client.request_model_dump_s" in timings
    assert "duplex_client.socket_connect_s" in timings
    assert "duplex_client.frame_write_s" in timings
    assert "duplex_client.response_read_s" in timings
    assert "duplex_client.response_decode_s" in timings
    assert "duplex_client.socket_close_s" in timings
    assert "duplex_client.total_s" in timings


@pytest.mark.asyncio
async def test_service_host_duplex_client_accepts_legacy_data_responses(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "aware-service-client-legacy-response.sock"

    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            line = await reader.readline()
            frame = DuplexIpcFrameCodec.decode_frame(line)
            _ = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexOperationRequest,
            )
            writer.write(
                DuplexIpcFrameCodec.encode_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.RESPONSE,
                        request_id=frame.id,
                        data=ServiceDuplexOperationResponse.from_contract(
                            ServiceOperationResponse(
                                status=RequestStatus.succeeded,
                                response_payload={"legacy": True},
                            )
                        ).model_dump_json(),
                    )
                )
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await _start_fake_server(socket_path=socket_path, handler=_handle)
    client = ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    )
    try:
        response = await client.send_request(request=_request(), timeout_s=2.0)
    finally:
        server.close()
        await server.wait_closed()

    assert response.status is RequestStatus.succeeded
    assert response.response_payload == {"legacy": True}


@pytest.mark.asyncio
async def test_service_host_duplex_client_preserves_api_ingress_invocation_context(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "aware-service-client-api-ingress.sock"
    target_branch_id = uuid4()
    api_call_id = uuid4()

    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            line = await reader.readline()
            frame = DuplexIpcFrameCodec.decode_frame(line)
            assert frame.payload is not None
            request = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexApiIngressRequest,
            )
            assert request.invocation_context == {
                "service_host_api_ingress": {
                    "commit_operation_receipts": False,
                },
            }
            assert request.target_branch_id == target_branch_id
            assert request.target_projection_hash == "workspace-status"
            writer.write(
                DuplexIpcFrameCodec.encode_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.RESPONSE,
                        request_id=frame.id,
                        payload=service_duplex_payload_from_model(
                            ServiceDuplexOperationResponse.from_contract(
                                ServiceOperationResponse(
                                    status=RequestStatus.succeeded,
                                    response_payload={"accepted": True},
                                    receipt=ServiceApiDispatchReceipt(
                                        endpoint_ref="meta.graph.resolve_projection",
                                        discriminant="meta.graph.resolve_projection",
                                        api_call_id=api_call_id,
                                    ),
                                ),
                            )
                        ),
                    )
                )
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await _start_fake_server(socket_path=socket_path, handler=_handle)
    client = ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    )
    try:
        response = await client.send_api_ingress_request(
            request=ServiceHostApiIngressRequest(
                actor_id=uuid4(),
                endpoint_ref="workspace.status.status",
                discriminant="workspace.status.status",
                request_payload=cast(JsonObject, {"operation": "status"}),
                invocation_context=cast(
                    JsonObject,
                    {
                        "service_host_api_ingress": {
                            "commit_operation_receipts": False,
                        },
                    },
                ),
                target_branch_id=target_branch_id,
                target_projection_hash="workspace-status",
            ),
            timeout_s=2.0,
        )
    finally:
        server.close()
        await server.wait_closed()

    assert response.status is RequestStatus.succeeded
    assert response.response_payload == {"accepted": True}
    assert response.receipt is not None
    assert response.receipt.api_call_id == api_call_id
    assert response.receipt.endpoint_ref == "meta.graph.resolve_projection"


@pytest.mark.asyncio
async def test_service_host_duplex_client_api_ingress_timeout_is_actionable(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "aware-service-client-api-timeout.sock"

    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            line = await reader.readline()
            frame = DuplexIpcFrameCodec.decode_frame(line)
            _ = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexApiIngressRequest,
            )
            await asyncio.sleep(1.0)
        finally:
            writer.close()
            await writer.wait_closed()

    server = await _start_fake_server(socket_path=socket_path, handler=_handle)
    client = ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    )
    try:
        with pytest.raises(TimeoutError) as exc_info:
            await client.send_api_ingress_request(
                request=ServiceHostApiIngressRequest(
                    actor_id=uuid4(),
                    endpoint_ref="workspace.status.status",
                    discriminant="workspace.status.status",
                    request_payload=cast(JsonObject, {"operation": "status"}),
                ),
                timeout_s=0.01,
            )
    finally:
        server.close()
        await server.wait_closed()

    error = str(exc_info.value)
    assert "ServiceHost request timed out" in error
    assert "operation_kind='api_ingress'" in error
    assert "endpoint_ref='workspace.status.status'" in error
    assert "discriminant='workspace.status.status'" in error
    assert "timeout_s=0.01" in error
    assert socket_path.as_posix() in error


@pytest.mark.asyncio
async def test_service_host_duplex_client_sends_lane_commit_receipt_notifications(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "aware-service-client-receipt.sock"
    receipt = LaneCommitReceiptNotification(
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="sha256:attention.focus",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        graph_hash_post="a" * 64,
        object_instance_graph_id=uuid4(),
        root_object_id=uuid4(),
    )
    seen: list[LaneCommitReceiptNotification] = []

    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            line = await reader.readline()
            frame = DuplexIpcFrameCodec.decode_frame(line)
            assert frame.type is DuplexMessageFrameType.NOTIFICATION
            assert frame.payload is not None
            payload = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexLaneCommitReceiptNotification,
            )
            seen.append(payload.to_contract())
        finally:
            writer.close()
            await writer.wait_closed()

    server = await _start_fake_server(socket_path=socket_path, handler=_handle)
    client = ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    )
    try:
        await client.send_lane_commit_receipt_notification(receipt=receipt)
        await asyncio.sleep(0)
    finally:
        server.close()
        await server.wait_closed()

    assert seen == [receipt]


@pytest.mark.asyncio
async def test_service_host_duplex_client_handles_stream_notifications(
    tmp_path: Path,
) -> None:
    socket_path = tmp_path / "aware-service-client-stream.sock"

    async def _handle(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            line = await reader.readline()
            frame = DuplexIpcFrameCodec.decode_frame(line)
            assert frame.payload is not None
            _ = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexOperationRequest,
            )
            for event in (
                ServiceDuplexStreamEvent.response_event(
                    ServiceOperationResponse(
                        status=RequestStatus.pending,
                        response_payload={"phase": "booting"},
                        stream_lifecycle=StreamLifecycle.started,
                    )
                ),
                ServiceDuplexStreamEvent.close_event(),
            ):
                writer.write(
                    DuplexIpcFrameCodec.encode_frame(
                        DuplexMessageFrame(
                            type=DuplexMessageFrameType.NOTIFICATION,
                            request_id=frame.id,
                            payload=service_duplex_payload_from_model(event),
                        )
                    )
                )
                await writer.drain()
            writer.write(
                DuplexIpcFrameCodec.encode_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.RESPONSE,
                        request_id=frame.id,
                        payload=service_duplex_payload_from_model(
                            ServiceDuplexOperationResponse.from_contract(
                                ServiceOperationResponse(
                                    status=RequestStatus.succeeded,
                                    response_payload={"accepted": True},
                                    stream_lifecycle=StreamLifecycle.started,
                                )
                            )
                        ),
                    )
                )
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await _start_fake_server(socket_path=socket_path, handler=_handle)
    client = ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    )
    handle = client.open_request_stream(request=_request(), timeout_s=2.0)
    try:
        events = [event async for event in handle.events]
        response = await handle.response
    finally:
        await handle.close()
        server.close()
        await server.wait_closed()

    assert [event.kind.value for event in events] == ["response", "close"]
    assert events[0].response is not None
    assert events[0].response.response_payload == {"phase": "booting"}
    assert response.status is RequestStatus.succeeded
    assert response.response_payload == {"accepted": True}
