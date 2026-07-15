from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID, uuid4

from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    ApiEndpointStream,
    ApiEndpointTransport,
    AwareApiEndpointInvoker,
)
from aware_comms.duplex.client import DuplexClient
from aware_api_service_dto.comms.models.api import (
    ApiRequestStatus,
    ApiOperation,
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
from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType
from aware_types import JsonObject
from pydantic import PrivateAttr


@dataclass(frozen=True, slots=True)
class SdkServiceApiProviderRoute:
    consumer_service_package_id: UUID
    consumer_service_package_name: str
    provider_service_package_id: UUID
    provider_service_package_name: str
    api_package_id: UUID
    api_package_name: str
    host_id: str
    protocol_version: str
    request_timeout_s: float
    service_names: tuple[str, ...]
    consumer_node_id: UUID
    provider_node_id: UUID
    provider_node_base_url: str
    route_connection_id: UUID
    endpoint_refs_by_service: Mapping[str, tuple[str, ...]]
    stream_endpoint_refs_by_service: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class RemoteNodeApiEndpointConfig:
    actor_id: UUID | None
    endpoint: str
    consumer_node_id: UUID
    provider_node_id: UUID
    connection_id: UUID
    request_timeout: float
    invocation_context: JsonObject | None = None


@dataclass(slots=True)
class _RemoteNodeApiEndpointTransport(ApiEndpointTransport):
    config: RemoteNodeApiEndpointConfig
    _duplex: "_RemoteApiEndpointStreamDuplexClient | None" = None

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
        network_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.api,
            network_request=NetworkRequest(
                id=uuid4(),
                requester_id=actor_id,
            ),
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
        network_op = NetworkOperation(
            id=uuid4(),
            message_type=NetworkOperationMessageType.request,
            type=NetworkOperationType.api,
            network_request=NetworkRequest(
                id=uuid4(),
                requester_id=actor_id,
            ),
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
        raw_handle = await (await self._ensure_duplex()).open_api_endpoint_stream(
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

    async def _ensure_duplex(self) -> "_RemoteApiEndpointStreamDuplexClient":
        if self._duplex is not None:
            return self._duplex
        duplex = _RemoteApiEndpointStreamDuplexClient(
            client_type=NetworkAppType.network_node.value,
            server_type=NetworkAppType.network_node.value,
        )
        await duplex.ensure_connection(
            self.config.connection_id,
            external_url=self.config.endpoint,
        )
        self._duplex = duplex
        return duplex


class RemoteNodeAwareApiClient(AwareApiEndpointInvoker):
    """Generated API invoker backed by a live remote Node API endpoint route."""

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


class _RemoteApiEndpointStreamDuplexClient(DuplexClient):
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


def routes_from_provider_refs_payload(
    payload: object,
    *,
    consumer_node_id: UUID,
    consumer_service_package_id: UUID,
    consumer_service_package_name: str,
    request_timeout_s: float | None = None,
) -> tuple[SdkServiceApiProviderRoute, ...]:
    if not isinstance(payload, list):
        raise RuntimeError("Service API provider refs payload must be a list.")
    routes: list[SdkServiceApiProviderRoute] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError("Service API provider ref entries must be objects.")
        routes.extend(
            _routes_from_provider_ref(
                item,
                consumer_node_id=consumer_node_id,
                consumer_service_package_id=consumer_service_package_id,
                consumer_service_package_name=consumer_service_package_name,
                request_timeout_s=request_timeout_s,
            )
        )
    return tuple(routes)


def endpoint_refs_for_api_package(
    routes: Sequence[SdkServiceApiProviderRoute],
    *,
    api_package_name: str,
) -> set[str]:
    refs: set[str] = set()
    for route in routes:
        if route.api_package_name != api_package_name:
            continue
        for endpoint_refs in route.endpoint_refs_by_service.values():
            refs.update(endpoint_refs)
    return refs


def select_route_for_api_package(
    routes: Sequence[SdkServiceApiProviderRoute],
    *,
    api_package_name: str,
    consumer_service_package_id: UUID | None = None,
    consumer_service_package_name: str | None = None,
) -> SdkServiceApiProviderRoute | None:
    normalized_api_package_name = api_package_name.strip().casefold()
    if not normalized_api_package_name:
        raise ValueError("API package route selection requires api_package_name.")
    matches = [
        route
        for route in routes
        if route.api_package_name.strip().casefold() == normalized_api_package_name
    ]
    if consumer_service_package_id is not None:
        matches = [
            route
            for route in matches
            if route.consumer_service_package_id == consumer_service_package_id
        ]
    normalized_consumer_name = _clean_optional_text(consumer_service_package_name)
    if normalized_consumer_name is not None:
        matches = [
            route
            for route in matches
            if route.consumer_service_package_name.strip().casefold()
            == normalized_consumer_name.casefold()
        ]
    if not matches:
        return None
    if len(matches) > 1:
        route_labels = ", ".join(
            f"{route.provider_service_package_name}@{route.host_id}"
            for route in matches
        )
        raise RuntimeError(
            f"Resolved multiple routes for API package {api_package_name!r}: "
            f"{route_labels}."
        )
    return matches[0]


def build_api_client_for_api_package(
    routes: Sequence[SdkServiceApiProviderRoute],
    *,
    api_package_name: str,
    actor_id: UUID | None = None,
    invocation_context: JsonObject | None = None,
) -> AwareApiEndpointInvoker | None:
    route = select_route_for_api_package(
        routes,
        api_package_name=api_package_name,
    )
    if route is None:
        return None
    return build_remote_node_api_client_for_route(
        route,
        actor_id=actor_id,
        invocation_context=invocation_context,
    )


def build_remote_node_api_client_for_route(
    route: SdkServiceApiProviderRoute,
    *,
    actor_id: UUID | None = None,
    invocation_context: JsonObject | None = None,
) -> RemoteNodeAwareApiClient:
    endpoint = route.provider_node_base_url.strip()
    if not endpoint:
        raise RuntimeError("Remote Node API route is missing provider_node_base_url.")
    return RemoteNodeAwareApiClient(
        actor_id=actor_id,
        endpoint=endpoint,
        consumer_node_id=route.consumer_node_id,
        provider_node_id=route.provider_node_id,
        connection_id=route.route_connection_id,
        request_timeout_s=route.request_timeout_s,
        invocation_context=invocation_context,
    )


def _routes_from_provider_ref(
    ref: Mapping[str, object],
    *,
    consumer_node_id: UUID,
    consumer_service_package_id: UUID,
    consumer_service_package_name: str,
    request_timeout_s: float | None,
) -> tuple[SdkServiceApiProviderRoute, ...]:
    service_package_ref = _mapping(ref, "service_package_ref")
    advertisement = _mapping(ref, "hosted_service_advertisement")
    provided_api_packages = service_package_ref.get("provided_api_packages")
    if not isinstance(provided_api_packages, list):
        raise RuntimeError("Service API provider ref requires provided_api_packages.")
    service_name = _required_str(advertisement, "service_name")
    endpoint_refs = tuple(_string_list(advertisement.get("endpoint_refs")))
    stream_endpoint_refs = tuple(
        _string_list(advertisement.get("stream_endpoint_refs"))
    )
    routes: list[SdkServiceApiProviderRoute] = []
    for api_package in provided_api_packages:
        if not isinstance(api_package, Mapping):
            raise RuntimeError("provided_api_packages entries must be objects.")
        routes.append(
            SdkServiceApiProviderRoute(
                consumer_service_package_id=consumer_service_package_id,
                consumer_service_package_name=consumer_service_package_name,
                provider_service_package_id=_required_uuid(
                    service_package_ref,
                    "service_package_id",
                ),
                provider_service_package_name=_required_str(
                    service_package_ref,
                    "package_name",
                ),
                api_package_id=_required_uuid(api_package, "api_package_id"),
                api_package_name=_required_str(api_package, "api_package_name"),
                host_id=_required_str(advertisement, "host_id"),
                protocol_version=str(advertisement.get("protocol_version") or "1"),
                request_timeout_s=_route_request_timeout_s(
                    ref,
                    override=request_timeout_s,
                ),
                service_names=(service_name,),
                consumer_node_id=consumer_node_id,
                provider_node_id=_required_uuid(ref, "provider_node_id"),
                provider_node_base_url=_required_str(ref, "provider_node_base_url"),
                route_connection_id=_optional_uuid(ref, "route_connection_id")
                or uuid4(),
                endpoint_refs_by_service={service_name: endpoint_refs},
                stream_endpoint_refs_by_service={service_name: stream_endpoint_refs},
            )
        )
    return tuple(routes)


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


def _mapping(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise RuntimeError(f"Provider ref field {key!r} must be an object.")
    return value


def _required_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"Provider ref field {key!r} must be a non-empty string.")
    return value.strip()


def _required_uuid(payload: Mapping[str, object], key: str) -> UUID:
    return UUID(_required_str(payload, key))


def _optional_uuid(payload: Mapping[str, object], key: str) -> UUID | None:
    value = payload.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise RuntimeError(f"Provider ref field {key!r} must be a UUID string.")
    return UUID(value)


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RuntimeError("Provider ref endpoint fields must be lists.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise RuntimeError("Provider ref endpoint fields must contain strings.")
        result.append(item)
    return result


def _route_request_timeout_s(
    ref: Mapping[str, object],
    *,
    override: float | None,
) -> float:
    raw_value = override or ref.get("request_timeout_s") or 60.0
    timeout_s = float(raw_value)
    if timeout_s <= 0:
        raise RuntimeError("SDK provider-ref route request timeout must be positive.")
    return timeout_s


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
