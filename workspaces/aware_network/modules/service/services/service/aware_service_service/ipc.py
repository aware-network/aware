from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, Mapping, cast

from aware_code.types import JsonObject
from aware_comms import (
    DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES,
    DuplexIpcEndpoint,
    DuplexIpcFrameCodec,
    DuplexIpcTransportKind,
    DuplexMessageFrame,
    DuplexMessageFrameType,
)
from aware_service_runtime import UnsupportedServiceError
from aware_service_runtime.api_ingress.telemetry import (
    collect_service_api_trace_timings,
)
from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceOperationResponse,
    StreamLifecycle,
)
from aware_service_runtime.duplex import (
    ServiceDuplexApiIngressRequest,
    ServiceDuplexHandshakeRequest,
    ServiceDuplexHandshakeResponse,
    ServiceDuplexHostControlRequest,
    ServiceDuplexHostControlResponse,
    ServiceDuplexLaneCommitReceiptNotification,
    ServiceDuplexOperationRequest,
    ServiceDuplexStreamEvent,
    service_duplex_model_from_frame,
    service_duplex_operation_response_payload_from_contract,
    service_duplex_payload_from_model,
)
from aware_utils.logging import logger

from aware_service_service.config import ServiceHostIpcConfig

if TYPE_CHECKING:
    from aware_service_service.app import ServiceHostApp


class ServiceHostIpcServer:
    """Unix-socket IPC host over the shared duplex frame contract."""

    def __init__(
        self,
        *,
        app: ServiceHostApp,
        endpoint: DuplexIpcEndpoint,
        managed_startup: bool = False,
    ) -> None:
        if endpoint.transport is not DuplexIpcTransportKind.UNIX_SOCKET:
            raise ValueError("ServiceHostIpcServer requires a unix_socket endpoint")
        self._app = app
        self._endpoint = endpoint
        self._managed_startup = managed_startup
        self._server: asyncio.AbstractServer | None = None
        self._startup_phase_timings_s: dict[str, float] = {}

    async def start(self) -> tuple[str, ...]:
        if self._server is not None:
            return self._app.plugin_services
        started = perf_counter()
        app_start_started = perf_counter()
        if self._managed_startup:
            loaded = await self._app.prepare()
        else:
            loaded = await self._app.start()
        app_start_duration_s = _duration_since(app_start_started)
        socket_path = Path(self._endpoint.socket_path or "")
        socket_parent_started = perf_counter()
        socket_path.parent.mkdir(parents=True, exist_ok=True)
        socket_parent_duration_s = _duration_since(socket_parent_started)
        stale_socket_unlink_started = perf_counter()
        if socket_path.exists():
            socket_path.unlink()
        stale_socket_unlink_duration_s = _duration_since(stale_socket_unlink_started)
        unix_server_start_started = perf_counter()
        self._server = await asyncio.start_unix_server(
            self._handle_connection,
            path=str(socket_path),
            limit=DEFAULT_DUPLEX_IPC_FRAME_LIMIT_BYTES,
        )
        unix_server_start_duration_s = _duration_since(unix_server_start_started)
        self._startup_phase_timings_s = {
            "app_start_duration_s": app_start_duration_s,
            "socket_parent_prepare_duration_s": socket_parent_duration_s,
            "stale_socket_unlink_duration_s": stale_socket_unlink_duration_s,
            "unix_server_start_duration_s": unix_server_start_duration_s,
            "total_duration_s": _duration_since(started),
        }
        logger.info(
            "ServiceHostIpcServer listening on %s services=%s timings=%s",
            socket_path.as_posix(),
            list(loaded),
            {
                key: round(value, 3)
                for key, value in self._startup_phase_timings_s.items()
            },
        )
        return loaded

    @property
    def startup_phase_timings_s(self) -> dict[str, float]:
        return dict(self._startup_phase_timings_s)

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        socket_path = Path(self._endpoint.socket_path or "")
        if socket_path.exists():
            socket_path.unlink()
        await self._app.close()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        write_lock = asyncio.Lock()
        request_tasks: set[asyncio.Task[None]] = set()

        async def send_frame(frame: DuplexMessageFrame) -> None:
            async with write_lock:
                writer.write(DuplexIpcFrameCodec.encode_frame(frame))
                await writer.drain()

        def track_request_task(task: asyncio.Task[None]) -> None:
            request_tasks.add(task)

            def _discard(completed: asyncio.Task[None]) -> None:
                request_tasks.discard(completed)
                if completed.cancelled():
                    return
                with contextlib.suppress(Exception):
                    completed.result()

            task.add_done_callback(_discard)

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    frame = DuplexIpcFrameCodec.decode_frame(line)
                except Exception as exc:
                    await send_frame(
                        DuplexMessageFrame(
                            type=DuplexMessageFrameType.ERROR,
                            data=str(exc),
                        )
                    )
                    continue

                if frame.type is DuplexMessageFrameType.REQUEST:
                    track_request_task(
                        asyncio.create_task(
                            self._handle_request_frame(
                                frame=frame,
                                send_frame=send_frame,
                            )
                        )
                    )
                    continue
                if frame.type is DuplexMessageFrameType.NOTIFICATION:
                    await self._handle_notification_frame(
                        frame=frame,
                        send_frame=send_frame,
                    )
                    continue

                await send_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.ERROR,
                        request_id=frame.id,
                        data=(
                            "ServiceHostIpcServer only accepts request or "
                            "notification frames from clients."
                        ),
                    )
                )
        except (BrokenPipeError, ConnectionResetError):
            logger.debug("Service IPC client disconnected before response flush")
        finally:
            for task in tuple(request_tasks):
                task.cancel()
            if request_tasks:
                await asyncio.gather(*request_tasks, return_exceptions=True)
            writer.close()
            try:
                await writer.wait_closed()
            except (BrokenPipeError, ConnectionResetError):
                logger.debug("Service IPC client disconnected during close")

    async def _handle_request_frame(
        self,
        *,
        frame: DuplexMessageFrame,
        send_frame,
    ) -> None:  # type: ignore[no-untyped-def]
        operation_started_at = perf_counter()
        phase_timings_s: dict[str, float] = {}
        phase_started_at = perf_counter()
        try:
            handshake_request = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexHandshakeRequest,
            )
        except Exception:
            handshake_request = None
        phase_timings_s["duplex_server.handshake_request_probe_s"] = _duration_since(
            phase_started_at
        )
        if handshake_request is not None:
            await send_frame(
                DuplexMessageFrame(
                    type=DuplexMessageFrameType.RESPONSE,
                    request_id=frame.id,
                    payload=service_duplex_payload_from_model(
                        ServiceDuplexHandshakeResponse.from_contract(
                            await self._app.handle_handshake(
                                request=handshake_request.to_contract(),
                                endpoint=self._endpoint,
                            )
                        )
                    ),
                )
            )
            return

        phase_started_at = perf_counter()
        try:
            api_ingress_request = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexApiIngressRequest,
            )
        except Exception:
            api_ingress_request = None
        phase_timings_s["duplex_server.api_ingress_request_probe_s"] = _duration_since(
            phase_started_at
        )
        if api_ingress_request is not None:

            async def emit_event(event: ServiceDuplexStreamEvent) -> None:
                await send_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.NOTIFICATION,
                        request_id=frame.id,
                        payload=service_duplex_payload_from_model(event),
                    )
                )

            phase_started_at = perf_counter()
            contract_request = api_ingress_request.to_contract()
            phase_timings_s["duplex_server.api_ingress_to_contract_s"] = (
                _duration_since(phase_started_at)
            )
            service_api_ingress_timings_s: dict[str, float] = {}
            phase_started_at = perf_counter()
            try:
                with collect_service_api_trace_timings() as collected_timings:
                    response = await self._app.handle_duplex_api_ingress_request(
                        request=contract_request,
                        emit_event=emit_event,
                    )
                service_api_ingress_timings_s = dict(collected_timings)
            except Exception as exc:
                logger.exception("Service IPC API ingress request failed")
                response = ServiceOperationResponse(
                    status=RequestStatus.failed,
                    error=str(exc),
                    stream_lifecycle=StreamLifecycle.closed,
                )
            phase_timings_s["duplex_server.app_dispatch_s"] = _duration_since(
                phase_started_at
            )
            phase_started_at = perf_counter()
            phase_timings_s["duplex_server.total_before_response_encode_s"] = (
                _duration_since(operation_started_at)
            )
            response = _attach_workspace_delta_preview_duplex_server_timings(
                response=response,
                phase_timings_s=phase_timings_s,
                service_api_ingress_timings_s=service_api_ingress_timings_s,
            )
            phase_timings_s["duplex_server.attach_public_envelope_s"] = _duration_since(
                phase_started_at
            )
            phase_started_at = perf_counter()
            transport_diagnostics = _servicehost_transport_diagnostics(
                response=response,
                phase_timings_s=phase_timings_s,
                service_api_ingress_timings_s=service_api_ingress_timings_s,
            )
            phase_timings_s["duplex_server.transport_diagnostics_build_s"] = (
                _duration_since(phase_started_at)
            )
            phase_started_at = perf_counter()
            response_payload = service_duplex_operation_response_payload_from_contract(
                response,
                transport_diagnostics=transport_diagnostics,
            )
            phase_timings_s["duplex_server.response_model_dump_s"] = _duration_since(
                phase_started_at
            )
            phase_started_at = perf_counter()
            response_frame = DuplexMessageFrame(
                type=DuplexMessageFrameType.RESPONSE,
                request_id=frame.id,
                payload=response_payload,
            )
            phase_timings_s["duplex_server.response_frame_build_s"] = _duration_since(
                phase_started_at
            )
            phase_timings_s["duplex_server.total_before_response_write_s"] = (
                _duration_since(operation_started_at)
            )
            _attach_duplex_response_frame_server_timings(
                frame=response_frame,
                phase_timings_s=phase_timings_s,
                service_api_ingress_timings_s=service_api_ingress_timings_s,
            )
            await send_frame(response_frame)
            return

        phase_started_at = perf_counter()
        try:
            host_control_request = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexHostControlRequest,
            )
        except Exception:
            host_control_request = None
        phase_timings_s["duplex_server.host_control_request_probe_s"] = _duration_since(
            phase_started_at
        )
        if host_control_request is not None:
            try:
                response = await self._app.handle_host_control_request(
                    request=host_control_request.to_contract(),
                )
            except Exception as exc:
                logger.exception("Service IPC host-control request failed")
                await send_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.ERROR,
                        request_id=frame.id,
                        data=str(exc),
                    )
                )
                return
            await send_frame(
                DuplexMessageFrame(
                    type=DuplexMessageFrameType.RESPONSE,
                    request_id=frame.id,
                    payload=service_duplex_payload_from_model(
                        ServiceDuplexHostControlResponse.from_contract(response)
                    ),
                )
            )
            return

        phase_started_at = perf_counter()
        try:
            request = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexOperationRequest,
            )
        except Exception as exc:
            await send_frame(
                DuplexMessageFrame(
                    type=DuplexMessageFrameType.ERROR,
                    request_id=frame.id,
                    data=f"Invalid service request payload: {exc}",
                )
            )
            return
        phase_timings_s["duplex_server.operation_request_parse_s"] = _duration_since(
            phase_started_at
        )

        async def emit_event(event: ServiceDuplexStreamEvent) -> None:
            await send_frame(
                DuplexMessageFrame(
                    type=DuplexMessageFrameType.NOTIFICATION,
                    request_id=frame.id,
                    payload=service_duplex_payload_from_model(event),
                )
            )

        phase_started_at = perf_counter()
        contract_request = request.to_contract()
        phase_timings_s["duplex_server.operation_to_contract_s"] = _duration_since(
            phase_started_at
        )
        phase_started_at = perf_counter()
        try:
            response = await self._app.handle_duplex_request(
                request=contract_request,
                emit_event=emit_event,
            )
        except UnsupportedServiceError as exc:
            response = ServiceOperationResponse(
                status=RequestStatus.failed,
                error=str(exc),
                stream_lifecycle=StreamLifecycle.closed,
            )
        except Exception as exc:
            logger.exception("Service IPC request failed")
            response = ServiceOperationResponse(
                status=RequestStatus.failed,
                error=str(exc),
                stream_lifecycle=StreamLifecycle.closed,
            )
        phase_timings_s["duplex_server.app_dispatch_s"] = _duration_since(
            phase_started_at
        )

        phase_started_at = perf_counter()
        phase_timings_s["duplex_server.total_before_response_encode_s"] = (
            _duration_since(operation_started_at)
        )
        response = _attach_workspace_delta_preview_duplex_server_timings(
            response=response,
            phase_timings_s=phase_timings_s,
            service_api_ingress_timings_s=None,
        )
        phase_timings_s["duplex_server.attach_public_envelope_s"] = _duration_since(
            phase_started_at
        )
        phase_started_at = perf_counter()
        transport_diagnostics = _servicehost_transport_diagnostics(
            response=response,
            phase_timings_s=phase_timings_s,
            service_api_ingress_timings_s=None,
        )
        phase_timings_s["duplex_server.transport_diagnostics_build_s"] = (
            _duration_since(phase_started_at)
        )
        phase_started_at = perf_counter()
        response_payload = service_duplex_operation_response_payload_from_contract(
            response,
            transport_diagnostics=transport_diagnostics,
        )
        phase_timings_s["duplex_server.response_model_dump_s"] = _duration_since(
            phase_started_at
        )
        phase_started_at = perf_counter()
        response_frame = DuplexMessageFrame(
            type=DuplexMessageFrameType.RESPONSE,
            request_id=frame.id,
            payload=response_payload,
        )
        phase_timings_s["duplex_server.response_frame_build_s"] = _duration_since(
            phase_started_at
        )
        phase_timings_s["duplex_server.total_before_response_write_s"] = (
            _duration_since(operation_started_at)
        )
        _attach_duplex_response_frame_server_timings(
            frame=response_frame,
            phase_timings_s=phase_timings_s,
            service_api_ingress_timings_s=None,
        )
        await send_frame(response_frame)

    async def _handle_notification_frame(
        self,
        *,
        frame: DuplexMessageFrame,
        send_frame,
    ) -> None:  # type: ignore[no-untyped-def]
        try:
            lane_receipt_notification = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexLaneCommitReceiptNotification,
            )
        except Exception:
            lane_receipt_notification = None
        if lane_receipt_notification is not None:
            try:
                await self._app.handle_lane_commit_receipt_notification(
                    receipt=lane_receipt_notification.to_contract(),
                )
            except Exception as exc:
                await send_frame(
                    DuplexMessageFrame(
                        type=DuplexMessageFrameType.ERROR,
                        request_id=frame.id,
                        data=f"Service lane receipt notification failed: {exc}",
                    )
                )
            return

        try:
            request = service_duplex_model_from_frame(
                frame=frame,
                model_type=ServiceDuplexOperationRequest,
            )
            await self._app.handle_duplex_notification(
                request=request.to_contract(),
                emit_event=self._unsupported_notification_emit,
            )
        except Exception as exc:
            await send_frame(
                DuplexMessageFrame(
                    type=DuplexMessageFrameType.ERROR,
                    request_id=frame.id,
                    data=str(exc),
                )
            )
            return

        await send_frame(
            DuplexMessageFrame(
                type=DuplexMessageFrameType.ACK,
                request_id=frame.id,
                payload={},
            )
        )

    async def _unsupported_notification_emit(
        self,
        event: ServiceDuplexStreamEvent,
    ) -> None:
        _ = event
        raise RuntimeError(
            "ServiceHostIpcServer notifications do not support outbound "
            "stream emission."
        )


def _attach_workspace_delta_preview_duplex_server_timings(
    *,
    response: ServiceOperationResponse,
    phase_timings_s: dict[str, float],
    service_api_ingress_timings_s: dict[str, float] | None,
) -> ServiceOperationResponse:
    payload = response.response_payload
    if not isinstance(payload, dict):
        return response
    result = payload.get("result")
    if not isinstance(result, dict):
        return response
    receipt_refs = result.get("receipt_refs")
    if not isinstance(receipt_refs, dict):
        return response
    envelope_key = _workspace_public_envelope_key(receipt_refs=receipt_refs)
    if envelope_key is None:
        return response
    envelope = receipt_refs.get(envelope_key)
    if not isinstance(envelope, dict):
        return response

    next_envelope = dict(envelope)
    next_envelope["servicehost_duplex_server_timings_s"] = {
        key: round(float(value), 6) for key, value in sorted(phase_timings_s.items())
    }
    if service_api_ingress_timings_s:
        next_envelope["service_api_ingress_timings_s"] = {
            key: round(float(value), 6)
            for key, value in sorted(service_api_ingress_timings_s.items())
        }
    next_receipt_refs = dict(receipt_refs)
    next_receipt_refs[envelope_key] = next_envelope
    next_result = dict(result)
    next_result["receipt_refs"] = next_receipt_refs
    next_payload = dict(payload)
    next_payload["result"] = next_result
    return response.model_copy(update={"response_payload": next_payload})


def _servicehost_transport_diagnostics(
    *,
    response: ServiceOperationResponse,
    phase_timings_s: dict[str, float],
    service_api_ingress_timings_s: dict[str, float] | None,
) -> JsonObject:
    diagnostics: dict[str, object] = {
        "servicehost_duplex_server_timings_s": {
            key: round(float(value), 6)
            for key, value in sorted(phase_timings_s.items())
        },
    }
    if service_api_ingress_timings_s:
        diagnostics["service_api_ingress_timings_s"] = {
            key: round(float(value), 6)
            for key, value in sorted(service_api_ingress_timings_s.items())
        }
    runtime_handler_timings_s = _workspace_delta_preview_runtime_handler_timings(
        response=response,
    )
    if runtime_handler_timings_s:
        diagnostics["workspace_runtime_handler_timings_s"] = runtime_handler_timings_s
    runtime_execution_timings_s = _workspace_runtime_execution_timings(
        response=response,
    )
    if runtime_execution_timings_s:
        diagnostics["workspace_runtime_execution_timings_s"] = (
            runtime_execution_timings_s
        )
    return cast(JsonObject, diagnostics)


def _attach_duplex_response_frame_server_timings(
    *,
    frame: DuplexMessageFrame,
    phase_timings_s: dict[str, float],
    service_api_ingress_timings_s: dict[str, float] | None,
) -> None:
    payload = frame.payload
    if not isinstance(payload, dict):
        return

    server_timings = {
        key: round(float(value), 6) for key, value in sorted(phase_timings_s.items())
    }
    transport_diagnostics = payload.get("transport_diagnostics")
    if isinstance(transport_diagnostics, dict):
        transport_diagnostics["servicehost_duplex_server_timings_s"] = server_timings
        if service_api_ingress_timings_s:
            transport_diagnostics["service_api_ingress_timings_s"] = {
                key: round(float(value), 6)
                for key, value in sorted(service_api_ingress_timings_s.items())
            }

    response_payload = payload.get("response_payload")
    if not isinstance(response_payload, dict):
        return
    result = response_payload.get("result")
    if not isinstance(result, dict):
        return
    receipt_refs = result.get("receipt_refs")
    if not isinstance(receipt_refs, dict):
        return
    envelope_key = _workspace_public_envelope_key(receipt_refs=receipt_refs)
    if envelope_key is None:
        return
    envelope = receipt_refs.get(envelope_key)
    if not isinstance(envelope, dict):
        return
    envelope["servicehost_duplex_server_timings_s"] = server_timings
    if service_api_ingress_timings_s:
        envelope["service_api_ingress_timings_s"] = {
            key: round(float(value), 6)
            for key, value in sorted(service_api_ingress_timings_s.items())
        }


def _workspace_delta_preview_runtime_handler_timings(
    *,
    response: ServiceOperationResponse,
) -> dict[str, float]:
    payload = response.response_payload
    if not isinstance(payload, dict):
        return {}
    result = payload.get("result")
    if not isinstance(result, dict):
        return {}
    receipt_refs = result.get("receipt_refs")
    if not isinstance(receipt_refs, dict):
        return {}
    envelope_key = _workspace_public_envelope_key(receipt_refs=receipt_refs)
    if envelope_key is None:
        return {}
    envelope = receipt_refs.get(envelope_key)
    if not isinstance(envelope, dict):
        return {}
    raw_timings = envelope.get("workspace_runtime_handler_timings_s")
    if not isinstance(raw_timings, dict):
        return {}
    return {
        str(key): round(float(value), 6)
        for key, value in sorted(raw_timings.items())
        if isinstance(value, int | float)
    }


def _workspace_public_envelope_key(*, receipt_refs: Mapping[str, object]) -> str | None:
    for key in (
        "workspace_delta_preview_public_envelope",
        "workspace_materialize_public_envelope",
    ):
        if isinstance(receipt_refs.get(key), dict):
            return key
    return None


def _workspace_runtime_execution_timings(
    *,
    response: ServiceOperationResponse,
) -> dict[str, float]:
    payload = response.response_payload
    if not isinstance(payload, dict):
        return {}
    result = payload.get("result")
    if not isinstance(result, dict):
        return {}
    receipt_refs = result.get("receipt_refs")
    if not isinstance(receipt_refs, dict):
        return {}
    observability = receipt_refs.get(
        "workspace_service_plugin_materialize_observability"
    )
    if not isinstance(observability, dict):
        return {}
    raw_timings = observability.get("timings_s")
    if not isinstance(raw_timings, dict):
        return {}
    return {
        f"workspace_runtime_execution.{key}": round(float(value), 6)
        for key, value in sorted(raw_timings.items())
        if isinstance(value, int | float)
    }


def _duration_since(started: float) -> float:
    return perf_counter() - started


__all__ = ["ServiceHostIpcConfig", "ServiceHostIpcServer"]
