from __future__ import annotations

import asyncio
import os
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import cast

from aware_code.types import JsonValue
from aware_comms import (
    DuplexIpcEndpoint,
    DuplexMessageFrame,
    DuplexMessageFrameType,
    UnixSocketDuplexClient,
)
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)

from aware_service_runtime.contracts import (
    ServiceHostApiIngressRequest,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
    ServiceHostHandshakeRequest,
    ServiceHostHandshakeResponse,
    ServiceOperationRequest,
    ServiceOperationResponse,
)
from aware_service_runtime.duplex import (
    ServiceDuplexApiIngressRequest,
    ServiceDuplexHandshakeRequest,
    ServiceDuplexHandshakeResponse,
    ServiceDuplexHostControlRequest,
    ServiceDuplexHostControlResponse,
    ServiceDuplexLaneCommitReceiptNotification,
    ServiceDuplexOperationRequest,
    ServiceDuplexOperationResponse,
    ServiceDuplexStreamEvent,
    service_duplex_model_from_frame,
    service_duplex_payload_from_model,
)


@dataclass(frozen=True, slots=True)
class ServiceHostDuplexRequestHandle:
    events: AsyncIterator[ServiceDuplexStreamEvent]
    response: asyncio.Future[ServiceOperationResponse]
    close: Callable[[], Awaitable[None]]


class ServiceHostDuplexClient:
    """Generic Python client for the standalone Service host duplex IPC rail."""

    def __init__(self, *, endpoint: DuplexIpcEndpoint) -> None:
        self._endpoint = endpoint
        self._last_request_timings_s: dict[str, float] = {}
        self._last_response_transport_diagnostics: dict[str, object] = {}

    @property
    def last_request_timings_s(self) -> dict[str, float]:
        return dict(self._last_request_timings_s)

    @property
    def last_response_transport_diagnostics(self) -> dict[str, object]:
        return dict(self._last_response_transport_diagnostics)

    async def send_request(
        self,
        *,
        request: ServiceOperationRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceOperationResponse:
        operation_started_at = time.perf_counter()
        timings_s: dict[str, float] = {}
        self._last_response_transport_diagnostics = {}
        client = self._new_transport_client()
        phase_started_at = time.perf_counter()
        frame_payload = service_duplex_payload_from_model(
            ServiceDuplexOperationRequest.from_contract(request)
        )
        timings_s["duplex_client.request_model_dump_s"] = _duration_since(
            phase_started_at
        )
        phase_started_at = time.perf_counter()
        frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.REQUEST,
            payload=frame_payload,
        )
        timings_s["duplex_client.frame_build_s"] = _duration_since(phase_started_at)
        started = time.perf_counter()
        try:
            response_frame = await self._send_and_receive_frame_with_timings(
                client=client,
                frame=frame,
                timeout_s=timeout_s,
                timings_s=timings_s,
            )
        except asyncio.TimeoutError as exc:
            timings_s["duplex_client.total_s"] = _duration_since(operation_started_at)
            self._last_request_timings_s = timings_s
            raise _service_host_timeout_error(
                operation_kind="service_operation",
                request_id=str(frame.id),
                timeout_s=timeout_s,
                elapsed_s=_duration_since(started),
                socket_path=self._endpoint.socket_path,
                service=request.service,
                operation=_operation_name(request.operation),
            ) from exc
        phase_started_at = time.perf_counter()
        response = self._decode_terminal_response(
            frame=response_frame,
            request_id=frame.id,
        )
        timings_s["duplex_client.response_decode_s"] = _duration_since(phase_started_at)
        timings_s["duplex_client.total_s"] = _duration_since(operation_started_at)
        self._last_request_timings_s = timings_s
        return response

    async def send_api_ingress_request(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceOperationResponse:
        operation_started_at = time.perf_counter()
        timings_s: dict[str, float] = {}
        self._last_response_transport_diagnostics = {}
        client = self._new_transport_client()
        phase_started_at = time.perf_counter()
        frame_payload = service_duplex_payload_from_model(
            ServiceDuplexApiIngressRequest.from_contract(
                ServiceHostApiIngressRequest(
                    actor_id=request.actor_id,
                    endpoint_ref=request.endpoint_ref,
                    discriminant=request.discriminant,
                    request_payload=request.request_payload,
                    invocation_context=request.invocation_context,
                    network_request_id=request.network_request_id,
                    stream_requested=False,
                    target_branch_id=request.target_branch_id,
                    target_projection_hash=request.target_projection_hash,
                )
            )
        )
        timings_s["duplex_client.request_model_dump_s"] = _duration_since(
            phase_started_at
        )
        phase_started_at = time.perf_counter()
        frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.REQUEST,
            payload=frame_payload,
        )
        timings_s["duplex_client.frame_build_s"] = _duration_since(phase_started_at)
        started = time.perf_counter()
        try:
            response_frame = await self._send_and_receive_frame_with_timings(
                client=client,
                frame=frame,
                timeout_s=timeout_s,
                timings_s=timings_s,
            )
        except asyncio.TimeoutError as exc:
            timings_s["duplex_client.total_s"] = _duration_since(operation_started_at)
            self._last_request_timings_s = timings_s
            raise _service_host_timeout_error(
                operation_kind="api_ingress",
                request_id=str(frame.id),
                timeout_s=timeout_s,
                elapsed_s=_duration_since(started),
                socket_path=self._endpoint.socket_path,
                endpoint_ref=request.endpoint_ref,
                discriminant=request.discriminant,
            ) from exc
        phase_started_at = time.perf_counter()
        response = self._decode_terminal_response(
            frame=response_frame,
            request_id=frame.id,
        )
        timings_s["duplex_client.response_decode_s"] = _duration_since(phase_started_at)
        timings_s["duplex_client.total_s"] = _duration_since(operation_started_at)
        self._last_request_timings_s = timings_s
        return response

    def open_api_ingress_stream(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostDuplexRequestHandle:
        return self._open_stream(
            payload=service_duplex_payload_from_model(
                ServiceDuplexApiIngressRequest.from_contract(
                    ServiceHostApiIngressRequest(
                        actor_id=request.actor_id,
                        endpoint_ref=request.endpoint_ref,
                        discriminant=request.discriminant,
                        request_payload=request.request_payload,
                        invocation_context=request.invocation_context,
                        network_request_id=request.network_request_id,
                        stream_requested=True,
                        target_branch_id=request.target_branch_id,
                        target_projection_hash=request.target_projection_hash,
                    )
                )
            ),
            timeout_s=timeout_s,
        )

    async def send_handshake(
        self,
        *,
        request: ServiceHostHandshakeRequest | None = None,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostHandshakeResponse:
        client = self._new_transport_client()
        frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.REQUEST,
            payload=service_duplex_payload_from_model(
                ServiceDuplexHandshakeRequest.from_contract(
                    request or ServiceHostHandshakeRequest()
                )
            ),
        )
        started = time.perf_counter()
        try:
            response_frame = await client.send_and_receive(frame, timeout_s=timeout_s)
        except asyncio.TimeoutError as exc:
            raise _service_host_timeout_error(
                operation_kind="handshake",
                request_id=str(frame.id),
                timeout_s=timeout_s,
                elapsed_s=_duration_since(started),
                socket_path=self._endpoint.socket_path,
            ) from exc
        finally:
            await client.close()
        return self._decode_handshake_response(
            frame=response_frame,
            request_id=frame.id,
        )

    async def send_host_control_request(
        self,
        *,
        request: ServiceHostControlRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostControlResponse:
        client = self._new_transport_client()
        frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.REQUEST,
            payload=service_duplex_payload_from_model(
                ServiceDuplexHostControlRequest.from_contract(request)
            ),
        )
        started = time.perf_counter()
        try:
            response_frame = await client.send_and_receive(frame, timeout_s=timeout_s)
        except asyncio.TimeoutError as exc:
            raise _service_host_timeout_error(
                operation_kind="host_control",
                request_id=str(frame.id),
                timeout_s=timeout_s,
                elapsed_s=_duration_since(started),
                socket_path=self._endpoint.socket_path,
                control_type=type(request).__name__,
            ) from exc
        finally:
            await client.close()
        return self._decode_host_control_response(
            frame=response_frame,
            request_id=frame.id,
        )

    async def send_lane_commit_receipt_notification(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
    ) -> None:
        client = self._new_transport_client()
        frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.NOTIFICATION,
            payload=service_duplex_payload_from_model(
                ServiceDuplexLaneCommitReceiptNotification.from_contract(receipt)
            ),
        )
        try:
            await client.send_frame(frame)
        finally:
            await client.close()

    def open_request_stream(
        self,
        *,
        request: ServiceOperationRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostDuplexRequestHandle:
        return self._open_stream(
            payload=service_duplex_payload_from_model(
                ServiceDuplexOperationRequest.from_contract(request)
            ),
            timeout_s=timeout_s,
        )

    def _open_stream(
        self,
        *,
        payload: JsonValue,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostDuplexRequestHandle:
        client = self._new_transport_client()
        frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.REQUEST,
            payload=payload,
        )
        loop = asyncio.get_running_loop()
        response_future: asyncio.Future[ServiceOperationResponse] = loop.create_future()
        queue: asyncio.Queue[ServiceDuplexStreamEvent | None] = asyncio.Queue()

        async def _event_stream() -> AsyncIterator[ServiceDuplexStreamEvent]:
            while True:
                event = await queue.get()
                if event is None:
                    return
                yield event

        async def _pump() -> None:
            started = time.perf_counter()
            try:
                await client.send_frame(frame)
                while True:
                    try:
                        next_frame = await client.read_frame(timeout_s=timeout_s)
                    except asyncio.TimeoutError as exc:
                        raise _service_host_timeout_error(
                            operation_kind="stream",
                            request_id=str(frame.id),
                            timeout_s=timeout_s,
                            elapsed_s=_duration_since(started),
                            socket_path=self._endpoint.socket_path,
                        ) from exc
                    if next_frame.request_id != frame.id:
                        raise RuntimeError(
                            "service host stream received mismatched request_id "
                            f"(expected={frame.id} actual={next_frame.request_id})"
                        )
                    if next_frame.type is DuplexMessageFrameType.NOTIFICATION:
                        await queue.put(
                            service_duplex_model_from_frame(
                                frame=next_frame,
                                model_type=ServiceDuplexStreamEvent,
                            )
                        )
                        continue
                    terminal = self._decode_terminal_response(
                        frame=next_frame,
                        request_id=frame.id,
                    )
                    if not response_future.done():
                        response_future.set_result(terminal)
                    break
            except Exception as exc:
                if not response_future.done():
                    response_future.set_exception(exc)
            finally:
                await client.close()
                await queue.put(None)

        task = loop.create_task(_pump())

        async def _close() -> None:
            if task.done():
                await asyncio.gather(task, return_exceptions=True)
                return
            task.cancel()
            await client.close()
            try:
                await task
            except asyncio.CancelledError:
                pass
            if not response_future.done():
                response_future.set_exception(
                    RuntimeError("service host stream closed before terminal response")
                )

        return ServiceHostDuplexRequestHandle(
            events=_event_stream(),
            response=response_future,
            close=_close,
        )

    def _new_transport_client(self) -> UnixSocketDuplexClient:
        return UnixSocketDuplexClient(endpoint=self._endpoint)

    async def _send_and_receive_frame_with_timings(
        self,
        *,
        client: UnixSocketDuplexClient,
        frame: DuplexMessageFrame,
        timeout_s: float | None,
        timings_s: dict[str, float],
    ) -> DuplexMessageFrame:
        try:
            phase_started_at = time.perf_counter()
            await client.connect()
            timings_s["duplex_client.socket_connect_s"] = _duration_since(
                phase_started_at
            )
            phase_started_at = time.perf_counter()
            await client.send_frame(frame)
            timings_s["duplex_client.frame_write_s"] = _duration_since(phase_started_at)
            phase_started_at = time.perf_counter()
            response_frame = await client.read_frame(timeout_s=timeout_s)
            timings_s["duplex_client.response_read_s"] = _duration_since(
                phase_started_at
            )
            return response_frame
        finally:
            phase_started_at = time.perf_counter()
            await client.close()
            timings_s["duplex_client.socket_close_s"] = _duration_since(
                phase_started_at
            )

    def _decode_terminal_response(
        self,
        *,
        frame: DuplexMessageFrame,
        request_id,
    ) -> ServiceOperationResponse:  # type: ignore[no-untyped-def]
        if frame.request_id != request_id:
            raise RuntimeError(
                "service host response request_id mismatch "
                f"(expected={request_id} actual={frame.request_id})"
            )
        if frame.type is DuplexMessageFrameType.RESPONSE:
            response = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexOperationResponse,
            )
            self._last_response_transport_diagnostics = dict(
                response.transport_diagnostics or {}
            )
            return response.to_contract()
        if frame.type is DuplexMessageFrameType.ERROR:
            raise RuntimeError(frame.data)
        raise RuntimeError(
            "unexpected terminal frame type from service host: "
            f"{cast(object, frame.type)}"
        )

    def _decode_host_control_response(
        self,
        *,
        frame: DuplexMessageFrame,
        request_id,
    ) -> ServiceHostControlResponse:  # type: ignore[no-untyped-def]
        if frame.request_id != request_id:
            raise RuntimeError(
                "service host control response request_id mismatch "
                f"(expected={request_id} actual={frame.request_id})"
            )
        if frame.type is DuplexMessageFrameType.ERROR:
            raise RuntimeError(frame.data)
        if frame.type is not DuplexMessageFrameType.RESPONSE:
            raise RuntimeError(
                "service host control expected response frame, got "
                f"{frame.type.value}"
            )
        return service_duplex_model_from_frame(
            frame=frame,
            model_type=ServiceDuplexHostControlResponse,
        ).to_contract()

    def _decode_handshake_response(
        self,
        *,
        frame: DuplexMessageFrame,
        request_id,
    ) -> ServiceHostHandshakeResponse:  # type: ignore[no-untyped-def]
        if frame.request_id != request_id:
            raise RuntimeError(
                "service host handshake response request_id mismatch "
                f"(expected={request_id} actual={frame.request_id})"
            )
        if frame.type is DuplexMessageFrameType.RESPONSE:
            return service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexHandshakeResponse,
            ).to_contract()
        if frame.type is DuplexMessageFrameType.ERROR:
            raise RuntimeError(frame.data)
        raise RuntimeError(
            "unexpected terminal frame type from service host handshake: "
            f"{cast(object, frame.type)}"
        )


def build_service_host_duplex_client_from_env(
    *socket_path_env_vars: str,
) -> ServiceHostDuplexClient:
    keys = tuple(key for key in socket_path_env_vars if str(key or "").strip()) or (
        "AWARE_SERVICE_HOST_SOCKET_PATH",
    )
    socket_path = ""
    for key in keys:
        raw = (os.environ.get(key) or "").strip()
        if raw:
            socket_path = raw
            break
    if not socket_path:
        joined = ", ".join(keys)
        raise RuntimeError(
            "Service host socket path is required " f"(set one of: {joined})"
        )
    return ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=socket_path)
    )


def _duration_since(started: float) -> float:
    return round(time.perf_counter() - started, 6)


def _service_host_timeout_error(
    *,
    operation_kind: str,
    request_id: str,
    timeout_s: float | None,
    elapsed_s: float,
    socket_path: str | None,
    service: str | None = None,
    operation: str | None = None,
    endpoint_ref: str | None = None,
    discriminant: str | None = None,
    control_type: str | None = None,
) -> TimeoutError:
    details = {
        "operation_kind": operation_kind,
        "request_id": request_id,
        "timeout_s": timeout_s,
        "elapsed_s": elapsed_s,
        "socket_path": socket_path,
        "service": service,
        "operation": operation,
        "endpoint_ref": endpoint_ref,
        "discriminant": discriminant,
        "control_type": control_type,
    }
    detail_text = " ".join(
        f"{key}={value!r}" for key, value in details.items() if value is not None
    )
    return TimeoutError(f"ServiceHost request timed out: {detail_text}")


def _operation_name(operation: object) -> str | None:
    if isinstance(operation, dict):
        value = operation.get("operation")
        return str(value) if value is not None else None
    value = getattr(operation, "operation", None)
    return str(value) if value is not None else None


__all__ = [
    "build_service_host_duplex_client_from_env",
    "ServiceHostDuplexClient",
    "ServiceHostDuplexRequestHandle",
]
