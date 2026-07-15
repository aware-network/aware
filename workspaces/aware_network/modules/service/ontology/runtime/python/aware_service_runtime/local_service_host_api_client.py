from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any, cast
from uuid import UUID, uuid4

from aware_api.invocation import LoadedApiInvocationManifest, ApiInvocationIndex
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    ApiEndpointStream,
    ApiEndpointTransport,
    AwareApiEndpointInvoker,
)
from aware_code.types import JsonObject
from aware_comms import DuplexIpcEndpoint
from aware_api_service_dto.comms.models.api import (
    ApiOperation,
    ApiRequestStatus,
    ApiStreamLifecycle,
    InvokeApiEndpointRequest,
    InvokeApiEndpointResponse,
    StreamApiEndpointRequest,
)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequest,
    NetworkRequestStatus,
)
from aware_network_service_dto.comms.models.network_node import (
    CloseStreamRequest,
    NetworkNodeOperation,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    StreamLifecycle,
)
from aware_service_runtime.contracts import (
    ServiceHostApiIngressRequest,
    ServiceStreamEventKind,
)
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)
from aware_service_runtime.api_endpoint_duplex import ApiEndpointDuplexClient
from aware_service_runtime.duplex import (
    ServiceDuplexStreamEventEnvelope,
    ServiceDuplexStreamEventKind,
)
from aware_service_runtime.duplex_client import ServiceHostDuplexClient
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
)
from pydantic import BaseModel
from pydantic import PrivateAttr
from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType


@dataclass(frozen=True, slots=True)
class LocalServiceHostApiConfig:
    actor_id: UUID | None
    endpoint: str
    request_timeout: float
    invocation_context: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class RemoteNodeApiEndpointConfig:
    actor_id: UUID | None
    endpoint: str
    consumer_node_id: UUID
    provider_node_id: UUID
    connection_id: UUID
    request_timeout: float
    invocation_context: JsonObject | None = None


@dataclass(frozen=True, slots=True)
class _LocalServiceHostApiEndpointTransport(ApiEndpointTransport):
    actor_id: UUID | None
    client_factory: Callable[[], ServiceHostDuplexClient]
    invocation_context: JsonObject | None = None

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        operation_started_at = perf_counter()
        phase_started_at = perf_counter()
        request_payload = cast(JsonObject, dict(invocation.request_payload))
        phase_timings_s = {
            "api_transport.request_payload_copy_s": _elapsed_seconds(phase_started_at),
        }
        phase_started_at = perf_counter()
        ingress_request = _build_ingress_request(
            actor_id=_resolve_invocation_actor_id(
                configured_actor_id=self.actor_id,
                request_payload=request_payload,
            ),
            endpoint_ref=invocation.endpoint_ref,
            discriminant=invocation.discriminant,
            request_payload=request_payload,
            stream_requested=False,
            invocation_context=self.invocation_context,
        )
        phase_timings_s["api_transport.build_ingress_request_s"] = _elapsed_seconds(
            phase_started_at
        )
        phase_started_at = perf_counter()
        service_host_client = self.client_factory()
        response = await service_host_client.send_api_ingress_request(
            request=ingress_request,
            timeout_s=timeout_s,
        )
        phase_timings_s["api_transport.send_api_ingress_request_s"] = _elapsed_seconds(
            phase_started_at
        )
        phase_started_at = perf_counter()
        endpoint_response = _api_endpoint_response_from_service_response(response)
        phase_timings_s["api_transport.service_response_adapt_s"] = _elapsed_seconds(
            phase_started_at
        )
        phase_timings_s["api_transport.total_s"] = _elapsed_seconds(
            operation_started_at
        )
        return _api_endpoint_response_with_transport_timings(
            response=endpoint_response,
            phase_timings_s=phase_timings_s,
            transport_kind="local_service_host_ipc",
            endpoint_ref=invocation.endpoint_ref,
            servicehost_duplex_client_timings_s=getattr(
                service_host_client,
                "last_request_timings_s",
                {},
            ),
            servicehost_transport_diagnostics=getattr(
                service_host_client,
                "last_response_transport_diagnostics",
                {},
            ),
        )

    async def open_stream(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointStream:
        request_payload = cast(JsonObject, dict(invocation.request_payload))
        handle = self.client_factory().open_api_ingress_stream(
            request=_build_ingress_request(
                actor_id=_resolve_invocation_actor_id(
                    configured_actor_id=self.actor_id,
                    request_payload=request_payload,
                ),
                endpoint_ref=invocation.endpoint_ref,
                discriminant=invocation.discriminant,
                request_payload=request_payload,
                stream_requested=True,
                invocation_context=self.invocation_context,
            ),
            timeout_s=timeout_s,
        )

        async def _events() -> AsyncIterator[ApiEndpointResponse]:
            try:
                async for event in handle.events:
                    if (
                        event.kind is not ServiceDuplexStreamEventKind.RESPONSE
                        or event.response is None
                    ):
                        continue
                    response = event.response.to_contract()
                    if response.stream_lifecycle is not StreamLifecycle.started:
                        continue
                    response_payload = response.response_payload
                    if response_payload is None:
                        continue
                    envelope = ServiceDuplexStreamEventEnvelope.model_validate(
                        response_payload
                    ).to_contract()
                    if envelope.kind is ServiceStreamEventKind.EVENT_ERROR:
                        yield ApiEndpointResponse(
                            status="failed",
                            error=(
                                "Service host API stream failed for "
                                f"{invocation.endpoint_ref!r}."
                            ),
                            stream_lifecycle=response.stream_lifecycle.value,
                        ),
                        continue
                    if envelope.payload is None:
                        continue
                    yield ApiEndpointResponse(
                        status=response.status.value,
                        response_payload=envelope.payload,
                        error=response.error,
                        receipt=response.receipt,
                        stream_lifecycle=response.stream_lifecycle.value,
                    )
                terminal_response = await handle.response
                if terminal_response.status is not RequestStatus.succeeded:
                    yield _api_endpoint_response_from_service_response(
                        terminal_response
                    )
            finally:
                await handle.close()
                if handle.response.done():
                    await asyncio.gather(handle.response, return_exceptions=True)

        return ApiEndpointStream(
            events=_events(),
            close=handle.close,
            response=None,
        )


@dataclass(slots=True)
class _RemoteNodeApiEndpointTransport(ApiEndpointTransport):
    config: RemoteNodeApiEndpointConfig
    _duplex: ApiEndpointDuplexClient | None = None

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        request_payload = cast(JsonObject, dict(invocation.request_payload))
        actor_id = _resolve_invocation_actor_id(
            configured_actor_id=self.config.actor_id,
            request_payload=request_payload,
        )
        network_request = NetworkRequest(
            id=uuid4(),
            requester_id=actor_id,
        )
        network_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.api,
            network_request=network_request,
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=self.config.consumer_node_id,
                    target_app_type=NetworkAppType.network_node,
                    target_node_id=self.config.provider_node_id,
                )
            ],
            api_operation=ApiOperation(
                request=InvokeApiEndpointRequest(
                    actor_id=actor_id,
                    endpoint_ref=invocation.endpoint_ref,
                    discriminant=invocation.discriminant,
                    request_payload=request_payload,
                    invocation_context=cast(Any, self.config.invocation_context),
                )
            ),
        )
        raw_response = await (await self._ensure_duplex()).send_request(
            connection_id=self.config.connection_id,
            data_serialized=network_op.model_dump_json(),
            timeout_s=timeout_s or self.config.request_timeout,
        )
        response_op = _parse_network_operation_response(raw_response)
        network_response = response_op.network_response
        if network_response is None:
            return ApiEndpointResponse(
                status="failed",
                error="Remote Node API endpoint response missing network_response.",
            )
        if network_response.status is NetworkRequestStatus.failed:
            return ApiEndpointResponse(
                status="failed",
                error=network_response.error or "Remote Node API endpoint failed.",
            )
        api_response = (
            response_op.api_operation.response
            if response_op.api_operation is not None
            else None
        )
        if not isinstance(api_response, InvokeApiEndpointResponse):
            return ApiEndpointResponse(
                status="failed",
                error="Remote Node API endpoint response missing API payload.",
            )
        return _api_endpoint_response_from_api_response(api_response)

    async def open_stream(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointStream:
        request_payload = cast(JsonObject, dict(invocation.request_payload))
        actor_id = _resolve_invocation_actor_id(
            configured_actor_id=self.config.actor_id,
            request_payload=request_payload,
        )
        network_request = NetworkRequest(
            id=uuid4(),
            requester_id=actor_id,
        )
        network_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.api,
            network_request=network_request,
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=self.config.consumer_node_id,
                    target_app_type=NetworkAppType.network_node,
                    target_node_id=self.config.provider_node_id,
                )
            ],
            api_operation=ApiOperation(
                request=StreamApiEndpointRequest(
                    actor_id=actor_id,
                    endpoint_ref=invocation.endpoint_ref,
                    discriminant=invocation.discriminant,
                    request_payload=request_payload,
                    invocation_context=cast(Any, self.config.invocation_context),
                )
            ),
        )
        duplex = await self._ensure_duplex()
        open_api_endpoint_stream = getattr(duplex, "open_api_endpoint_stream", None)
        if not callable(open_api_endpoint_stream):
            raise RuntimeError(
                "Remote Node API endpoint transport does not support streaming."
            )
        raw_handle = await open_api_endpoint_stream(
            connection_id=self.config.connection_id,
            operation=network_op,
            actor_id=actor_id,
            timeout_s=timeout_s or self.config.request_timeout,
        )

        async def _events() -> AsyncIterator[ApiEndpointResponse]:
            try:
                async for event in raw_handle.events:
                    yield _api_endpoint_response_from_api_response(event)
            finally:
                await raw_handle.close()

        return ApiEndpointStream(
            events=_events(),
            close=raw_handle.close,
            response=None,
        )

    async def _ensure_duplex(self) -> ApiEndpointDuplexClient:
        if self._duplex is not None:
            return self._duplex
        duplex = _RemoteApiEndpointStreamDuplexClient(
            client_type=NetworkAppType.network_node.value,
            server_type=NetworkAppType.network_node.value,
            endpoint=self.config.endpoint,
            request_timeout=self.config.request_timeout,
        )
        await duplex.ensure_connection(
            self.config.connection_id,
            external_url=self.config.endpoint,
        )
        self._duplex = duplex
        return duplex


@dataclass(slots=True)
class _RemoteApiEndpointStreamState:
    request_id: UUID
    connection_id: UUID
    actor_id: UUID | None
    operation: NetworkOperation
    queue: asyncio.Queue[InvokeApiEndpointResponse | None]
    terminal_task: asyncio.Task[InvokeApiEndpointResponse]


@dataclass(frozen=True, slots=True)
class _RemoteApiEndpointStreamHandle:
    events: AsyncIterator[InvokeApiEndpointResponse]
    close: Callable[[], Awaitable[None]]
    response: Awaitable[InvokeApiEndpointResponse]


class _RemoteApiEndpointStreamDuplexClient(ApiEndpointDuplexClient):
    """Remote Node API duplex client with API stream notification fan-in."""

    _api_endpoint_streams: dict[UUID, _RemoteApiEndpointStreamState] = PrivateAttr(
        default_factory=dict
    )

    async def open_api_endpoint_stream(
        self,
        *,
        connection_id: UUID,
        operation: NetworkOperation,
        actor_id: UUID | None,
        timeout_s: float | None = None,
    ) -> _RemoteApiEndpointStreamHandle:
        request_id = uuid4()
        frame = self._build_message(
            message_type=WsMessageFrameType.REQUEST,
            data_serialized=operation.model_dump_json(),
            request_id=request_id,
        )
        queue: asyncio.Queue[InvokeApiEndpointResponse | None] = asyncio.Queue()
        terminal_task = asyncio.create_task(
            self._run_api_endpoint_stream_terminal(
                connection_id=connection_id,
                request_id=request_id,
                request_data=frame.model_dump_json(),
                actor_id=actor_id,
                timeout_s=timeout_s,
            )
        )
        state = _RemoteApiEndpointStreamState(
            request_id=request_id,
            connection_id=connection_id,
            actor_id=actor_id,
            operation=operation,
            queue=queue,
            terminal_task=terminal_task,
        )
        self._api_endpoint_streams[operation.id] = state
        terminal_task.add_done_callback(
            lambda task: self._complete_api_endpoint_stream(operation.id, task)
        )

        async def _events() -> AsyncIterator[InvokeApiEndpointResponse]:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event

        async def _close() -> None:
            await self.close_api_endpoint_stream(operation.id)

        return _RemoteApiEndpointStreamHandle(
            events=_events(),
            close=_close,
            response=terminal_task,
        )

    async def close_api_endpoint_stream(self, operation_id: UUID) -> None:
        state = self._api_endpoint_streams.pop(operation_id, None)
        if state is None:
            return
        with contextlib.suppress(Exception):
            await self._send_close_api_endpoint_stream_request(
                operation_id=operation_id,
                state=state,
            )
        self.messenger.pending_futures.pop(state.request_id, None)
        if not state.terminal_task.done():
            state.terminal_task.cancel()
        state.queue.put_nowait(None)
        await asyncio.gather(state.terminal_task, return_exceptions=True)

    async def _send_close_api_endpoint_stream_request(
        self,
        *,
        operation_id: UUID,
        state: _RemoteApiEndpointStreamState,
    ) -> None:
        hop = state.operation.network_operation_hop_list[0]
        close_operation = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.notification,
            type=NetworkOperationType.network_node,
            network_node_operation=NetworkNodeOperation(
                request=CloseStreamRequest(
                    actor_id=state.actor_id,
                    node_id=hop.target_node_id,
                    network_operation_id=operation_id,
                )
            ),
            network_operation_hop_list=[
                NetworkOperationHop(
                    source_app_type=NetworkAppType.network_node,
                    source_node_id=hop.source_node_id,
                    target_app_type=NetworkAppType.network_node,
                    target_node_id=hop.target_node_id,
                )
            ],
        )
        await self.send_notification(
            connection_id=state.connection_id,
            data_serialized=close_operation.model_dump_json(),
        )

    async def _run_api_endpoint_stream_terminal(
        self,
        *,
        connection_id: UUID,
        request_id: UUID,
        request_data: str,
        actor_id: UUID | None,
        timeout_s: float | None,
    ) -> InvokeApiEndpointResponse:
        try:
            raw_response = await self.messenger.send_request(
                request_id=request_id,
                request_data=request_data,
                connection_id=connection_id,
                timeout_s=timeout_s,
            )
            response_op = _parse_network_operation_response(raw_response)
            network_response = response_op.network_response
            if (
                network_response is not None
                and network_response.status is NetworkRequestStatus.failed
            ):
                raise RuntimeError(
                    network_response.error or "Remote Node API endpoint failed."
                )
            api_response = (
                response_op.api_operation.response
                if response_op.api_operation is not None
                else None
            )
            if isinstance(api_response, InvokeApiEndpointResponse):
                return api_response
            raise RuntimeError(
                "Remote Node API endpoint did not return an API stream terminal payload."
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            return InvokeApiEndpointResponse(
                actor_id=actor_id,
                status=ApiRequestStatus.failed,
                error=str(exc),
                stream_lifecycle=ApiStreamLifecycle.closed,
            )

    def _complete_api_endpoint_stream(
        self,
        operation_id: UUID,
        task: asyncio.Task[InvokeApiEndpointResponse],
    ) -> None:
        state = self._api_endpoint_streams.get(operation_id)
        if state is None:
            return
        if not task.cancelled():
            with contextlib.suppress(Exception):
                terminal = task.result()
                if (
                    terminal.status is not ApiRequestStatus.failed
                    and terminal.stream_lifecycle is ApiStreamLifecycle.started
                ):
                    return
                self._api_endpoint_streams.pop(operation_id, None)
                if terminal.status is ApiRequestStatus.failed:
                    state.queue.put_nowait(terminal)
        else:
            self._api_endpoint_streams.pop(operation_id, None)
        state.queue.put_nowait(None)

    async def handle_data(self, connection_id: UUID, data: dict) -> None:
        try:
            frame = WsMessageFrame.model_validate(data)
        except Exception:
            await super().handle_data(connection_id, data)
            return
        if frame.type is not WsMessageFrameType.NOTIFICATION:
            await super().handle_data(connection_id, data)
            return
        await self._handle_notification_frame(frame)

    async def _handle_notification_frame(self, frame: WsMessageFrame) -> None:
        payload: object = frame.data
        try:
            if isinstance(payload, str):
                network_op = NetworkOperation.model_validate_json(payload)
            elif isinstance(payload, dict):
                network_op = NetworkOperation.model_validate(payload)
            else:
                return
        except Exception:
            return
        if network_op.message_type is not NetworkOperationMessageType.stream:
            return
        state = self._api_endpoint_streams.get(network_op.id)
        if state is None:
            return
        api_response = (
            network_op.api_operation.response
            if network_op.api_operation is not None
            else None
        )
        if not isinstance(api_response, InvokeApiEndpointResponse):
            return
        await state.queue.put(api_response)
        if api_response.stream_lifecycle is not ApiStreamLifecycle.started:
            self._api_endpoint_streams.pop(network_op.id, None)
            await state.queue.put(None)


def build_local_service_host_duplex_client_factory_for_route(
    route: ServiceApiDependencyRouteDescriptor,
) -> Callable[[], ServiceHostDuplexClient]:
    if route.route_kind is not ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC:
        raise RuntimeError(
            "Local ServiceHost API client requires a local IPC route "
            f"(actual={route.route_kind.value!r})."
        )
    if route.socket_path is None:
        raise RuntimeError("Local ServiceHost API client route is missing socket_path.")
    socket_path = str(route.socket_path)

    def _factory() -> ServiceHostDuplexClient:
        return ServiceHostDuplexClient(
            endpoint=DuplexIpcEndpoint.unix_socket(socket_path=socket_path)
        )

    return _factory


def build_local_service_host_api_client_for_route(
    route: ServiceApiDependencyRouteDescriptor,
    *,
    actor_id: UUID | None = None,
    invocation_context: JsonObject | None = None,
) -> "LocalServiceHostAwareApiClient":
    return LocalServiceHostAwareApiClient(
        actor_id=actor_id,
        client_factory=build_local_service_host_duplex_client_factory_for_route(route),
        endpoint=f"aware-service-host://{route.host_id}",
        request_timeout_s=route.request_timeout_s,
        invocation_context=invocation_context,
    )


def build_remote_node_api_client_for_route(
    route: ServiceApiDependencyRouteDescriptor,
    *,
    actor_id: UUID | None = None,
    invocation_context: JsonObject | None = None,
) -> "RemoteNodeAwareApiClient":
    if route.route_kind is not ServiceApiDependencyRouteKind.REMOTE_NODE_API_ENDPOINT:
        raise RuntimeError(
            "Remote Node API client requires a remote Node API endpoint route "
            f"(actual={route.route_kind.value!r})."
        )
    if route.consumer_node_id is None:
        raise RuntimeError("Remote Node API route is missing consumer_node_id.")
    if route.provider_node_id is None:
        raise RuntimeError("Remote Node API route is missing provider_node_id.")
    endpoint = (route.provider_node_base_url or "").strip()
    if not endpoint:
        raise RuntimeError("Remote Node API route is missing provider_node_base_url.")
    return RemoteNodeAwareApiClient(
        actor_id=actor_id,
        endpoint=endpoint,
        consumer_node_id=route.consumer_node_id,
        provider_node_id=route.provider_node_id,
        connection_id=route.route_connection_id or route.provider_node_id,
        request_timeout_s=route.request_timeout_s,
        invocation_context=invocation_context,
    )


def build_service_api_client_for_route(
    route: ServiceApiDependencyRouteDescriptor,
    *,
    actor_id: UUID | None = None,
    invocation_context: JsonObject | None = None,
) -> AwareApiEndpointInvoker:
    if route.route_kind is ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC:
        return build_local_service_host_api_client_for_route(
            route,
            actor_id=actor_id,
            invocation_context=invocation_context,
        )
    if route.route_kind is ServiceApiDependencyRouteKind.REMOTE_NODE_API_ENDPOINT:
        return build_remote_node_api_client_for_route(
            route,
            actor_id=actor_id,
            invocation_context=invocation_context,
        )
    raise RuntimeError(
        f"Unsupported Service API dependency route kind: {route.route_kind.value!r}."
    )


def _current_consumer_service_package_context() -> tuple[UUID | None, str | None]:
    host_context = current_service_api_host_context()
    if host_context is None:
        return None, None
    return host_context.service_package_id, _clean_optional_text(
        host_context.service_package_name
    )


def _route_matches_consumer_service_package(
    route: ServiceApiDependencyRouteDescriptor,
    *,
    consumer_service_package_id: UUID | None,
    consumer_service_package_name: str | None,
) -> bool:
    if (
        consumer_service_package_id is not None
        and route.consumer_service_package_id != consumer_service_package_id
    ):
        return False
    normalized_consumer_name = _clean_optional_text(consumer_service_package_name)
    if normalized_consumer_name is not None:
        route_consumer_name = route.consumer_service_package_name.strip().casefold()
        if route_consumer_name != normalized_consumer_name.casefold():
            return False
    return True


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def select_service_api_dependency_route_for_api_package(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    api_package_name: str,
    consumer_service_package_id: UUID | None = None,
    consumer_service_package_name: str | None = None,
) -> ServiceApiDependencyRouteDescriptor | None:
    normalized_api_package_name = api_package_name.strip().casefold()
    if not normalized_api_package_name:
        raise ValueError(
            "Service API dependency route selection requires api_package_name."
        )
    if consumer_service_package_id is None and not _clean_optional_text(
        consumer_service_package_name
    ):
        (
            consumer_service_package_id,
            consumer_service_package_name,
        ) = _current_consumer_service_package_context()
    matches: list[ServiceApiDependencyRouteDescriptor] = []
    for route in routes:
        route_api_package_name = (route.api_package_name or "").strip().casefold()
        if route_api_package_name == normalized_api_package_name:
            matches.append(route)
    if matches and (
        consumer_service_package_id is not None
        or _clean_optional_text(consumer_service_package_name)
    ):
        matches = [
            route
            for route in matches
            if _route_matches_consumer_service_package(
                route,
                consumer_service_package_id=consumer_service_package_id,
                consumer_service_package_name=consumer_service_package_name,
            )
        ]
    if not matches:
        return None
    if len(matches) > 1:
        route_labels = ", ".join(
            f"{route.provider_service_package_name}@{route.host_id}"
            for route in matches
        )
        raise RuntimeError(
            "Resolved multiple Service API dependency routes for API package "
            f"{api_package_name!r}: {route_labels}."
        )
    return matches[0]


def build_local_service_host_api_client_for_api_package(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    api_package_name: str,
    consumer_service_package_id: UUID | None = None,
    consumer_service_package_name: str | None = None,
    actor_id: UUID | None = None,
    invocation_context: JsonObject | None = None,
) -> LocalServiceHostAwareApiClient | None:
    route = select_service_api_dependency_route_for_api_package(
        routes,
        api_package_name=api_package_name,
        consumer_service_package_id=consumer_service_package_id,
        consumer_service_package_name=consumer_service_package_name,
    )
    if route is None:
        return None
    return build_local_service_host_api_client_for_route(
        route,
        actor_id=actor_id,
        invocation_context=invocation_context,
    )


def build_service_api_client_for_api_package(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    api_package_name: str,
    consumer_service_package_id: UUID | None = None,
    consumer_service_package_name: str | None = None,
    actor_id: UUID | None = None,
    invocation_context: JsonObject | None = None,
) -> AwareApiEndpointInvoker | None:
    route = select_service_api_dependency_route_for_api_package(
        routes,
        api_package_name=api_package_name,
        consumer_service_package_id=consumer_service_package_id,
        consumer_service_package_name=consumer_service_package_name,
    )
    if route is None:
        return None
    return build_service_api_client_for_route(
        route,
        actor_id=actor_id,
        invocation_context=invocation_context,
    )


def _api_endpoint_response_from_service_response(
    response: Any,
) -> ApiEndpointResponse:
    return ApiEndpointResponse(
        status=getattr(response.status, "value", str(response.status)),
        response_payload=response.response_payload,
        error=response.error,
        receipt=getattr(response, "receipt", None),
        stream_lifecycle=(
            getattr(response.stream_lifecycle, "value", None) or "auto_close"
        ),
    )


def _api_endpoint_response_from_api_response(
    response: InvokeApiEndpointResponse,
) -> ApiEndpointResponse:
    return ApiEndpointResponse(
        status=getattr(response.status, "value", str(response.status)),
        response_payload=response.response_payload,
        error=response.error,
        receipt=getattr(response, "receipt", None),
        stream_lifecycle=getattr(
            response.stream_lifecycle,
            "value",
            str(response.stream_lifecycle),
        ),
    )


def _api_endpoint_response_with_transport_timings(
    *,
    response: ApiEndpointResponse,
    phase_timings_s: Mapping[str, float],
    transport_kind: str,
    endpoint_ref: str,
    servicehost_duplex_client_timings_s: Mapping[str, float] | None = None,
    servicehost_transport_diagnostics: Mapping[str, object] | None = None,
) -> ApiEndpointResponse:
    raw_receipt = response.receipt
    transport_receipt = _api_endpoint_transport_receipt_payload(raw_receipt)
    transport_receipt["api_transport_kind"] = transport_kind
    transport_receipt["api_transport_endpoint_ref"] = endpoint_ref
    transport_receipt["api_transport_timings_s"] = {
        key: round(float(value), 6) for key, value in phase_timings_s.items()
    }
    if servicehost_duplex_client_timings_s:
        transport_receipt["servicehost_duplex_client_timings_s"] = {
            key: round(float(value), 6)
            for key, value in servicehost_duplex_client_timings_s.items()
        }
    if servicehost_transport_diagnostics:
        for key in (
            "servicehost_duplex_server_timings_s",
            "service_api_ingress_timings_s",
            "workspace_runtime_handler_timings_s",
            "workspace_runtime_execution_timings_s",
        ):
            value = servicehost_transport_diagnostics.get(key)
            if isinstance(value, Mapping):
                transport_receipt[key] = {
                    str(timing_key): round(float(timing_value), 6)
                    for timing_key, timing_value in value.items()
                    if isinstance(timing_value, int | float)
                }
    return ApiEndpointResponse(
        status=response.status,
        response_payload=response.response_payload,
        error=response.error,
        receipt=response.receipt,
        transport_receipt=JsonObject(cast(dict[str, Any], transport_receipt)),
        stream_lifecycle=response.stream_lifecycle,
    )


def _api_endpoint_transport_receipt_payload(
    raw_receipt: object,
) -> dict[str, object]:
    if raw_receipt is None:
        return {}
    if isinstance(raw_receipt, Mapping):
        return dict(cast(Mapping[str, object], raw_receipt))
    if isinstance(raw_receipt, BaseModel):
        return cast(dict[str, object], raw_receipt.model_dump(mode="json"))
    return {}


def _elapsed_seconds(started_at: float) -> float:
    return round(max(perf_counter() - started_at, 0.0), 6)


def _parse_network_operation_response(raw_response: object) -> NetworkOperation:
    if isinstance(raw_response, NetworkOperation):
        return raw_response
    if isinstance(raw_response, str):
        return NetworkOperation.model_validate_json(raw_response)
    if isinstance(raw_response, dict):
        return NetworkOperation.model_validate(raw_response)
    raise TypeError(
        "Remote Node API endpoint returned unsupported NetworkOperation payload "
        f"type: {type(raw_response)}"
    )


def _build_ingress_request(
    *,
    actor_id: UUID | None,
    endpoint_ref: str,
    discriminant: str,
    request_payload: JsonObject,
    stream_requested: bool,
    invocation_context: JsonObject | None = None,
) -> ServiceHostApiIngressRequest:
    return ServiceHostApiIngressRequest(
        actor_id=actor_id,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
        request_payload=request_payload,
        invocation_context=invocation_context,
        network_request_id=uuid4(),
        stream_requested=stream_requested,
    )


def _resolve_invocation_actor_id(
    *,
    configured_actor_id: UUID | None,
    request_payload: Mapping[str, Any],
) -> UUID | None:
    if configured_actor_id is not None:
        return configured_actor_id
    raw_actor_id = request_payload.get("actor_id")
    if raw_actor_id is None or raw_actor_id == "":
        return None
    if isinstance(raw_actor_id, UUID):
        return raw_actor_id
    return UUID(str(raw_actor_id))


class LocalServiceHostAwareApiClient(AwareApiEndpointInvoker):
    """Generated API invoker backed by local ServiceHost API ingress over IPC."""

    def __init__(
        self,
        *,
        actor_id: UUID | None,
        client_factory: Callable[[], ServiceHostDuplexClient],
        endpoint: str = "aware-service-host://local",
        request_timeout_s: float = 10.0,
        invocation_context: JsonObject | None = None,
    ) -> None:
        self._config = LocalServiceHostApiConfig(
            actor_id=actor_id,
            endpoint=endpoint,
            request_timeout=request_timeout_s,
            invocation_context=invocation_context,
        )
        self._client_factory = client_factory
        super().__init__(
            _LocalServiceHostApiEndpointTransport(
                actor_id=actor_id,
                client_factory=client_factory,
                invocation_context=invocation_context,
            )
        )

    @property
    def config(self) -> LocalServiceHostApiConfig:
        return self._config

    async def invoke_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> Any:
        return await super().invoke_api_endpoint(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
            timeout_s=timeout_s or self.config.request_timeout,
        )

    async def stream_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> AsyncIterator[Any]:
        async for event in super().stream_api_endpoint(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
            timeout_s=timeout_s or self.config.request_timeout,
        ):
            yield event

    def _build_ingress_request(
        self,
        *,
        endpoint_ref: str,
        discriminant: str,
        request_payload: JsonObject,
        stream_requested: bool,
        invocation_context: JsonObject | None = None,
    ) -> ServiceHostApiIngressRequest:
        return _build_ingress_request(
            actor_id=self.config.actor_id,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
            stream_requested=stream_requested,
            invocation_context=invocation_context or self.config.invocation_context,
        )

    @staticmethod
    def _raise_for_terminal_failure(
        *,
        endpoint_ref: str,
        status: RequestStatus,
        error: str | None,
    ) -> None:
        if status == RequestStatus.succeeded:
            return
        raise RuntimeError(
            error
            or f"Local ServiceHost API ingress failed for endpoint {endpoint_ref!r}."
        )


class RemoteNodeAwareApiClient(AwareApiEndpointInvoker):
    """Generated API invoker backed by a remote Node API endpoint route."""

    def __init__(
        self,
        *,
        actor_id: UUID | None,
        endpoint: str,
        consumer_node_id: UUID,
        provider_node_id: UUID,
        connection_id: UUID,
        request_timeout_s: float = 10.0,
        invocation_context: JsonObject | None = None,
    ) -> None:
        self._config = RemoteNodeApiEndpointConfig(
            actor_id=actor_id,
            endpoint=endpoint,
            consumer_node_id=consumer_node_id,
            provider_node_id=provider_node_id,
            connection_id=connection_id,
            request_timeout=request_timeout_s,
            invocation_context=invocation_context,
        )
        super().__init__(_RemoteNodeApiEndpointTransport(config=self._config))

    @property
    def config(self) -> RemoteNodeApiEndpointConfig:
        return self._config

    async def invoke_api_endpoint(
        self,
        *,
        manifest: LoadedApiInvocationManifest | ApiInvocationIndex,
        request_payload: BaseModel | Mapping[str, Any],
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        api_name: str | None = None,
        capability_name: str | None = None,
        endpoint_name: str | None = None,
        timeout_s: float | None = None,
    ) -> Any:
        return await super().invoke_api_endpoint(
            manifest=manifest,
            request_payload=request_payload,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            api_name=api_name,
            capability_name=capability_name,
            endpoint_name=endpoint_name,
            timeout_s=timeout_s or self.config.request_timeout,
        )


__all__ = [
    "LocalServiceHostApiConfig",
    "LocalServiceHostAwareApiClient",
    "RemoteNodeApiEndpointConfig",
    "RemoteNodeAwareApiClient",
    "build_local_service_host_api_client_for_api_package",
    "build_local_service_host_api_client_for_route",
    "build_local_service_host_duplex_client_factory_for_route",
    "build_remote_node_api_client_for_route",
    "build_service_api_client_for_api_package",
    "build_service_api_client_for_route",
    "select_service_api_dependency_route_for_api_package",
]
