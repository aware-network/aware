from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import replace
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceApiDispatchReceipt,
    ServiceHostApiIngressRequest,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
    ServiceStreamEventEnvelope,
    ServiceStreamEventKind,
    ServiceStreamSession,
    StreamLifecycle,
)
from aware_service_runtime.duplex import (
    ServiceDuplexOperationResponse,
    ServiceDuplexStreamEvent,
    ServiceDuplexStreamEventEnvelope,
    ServiceDuplexStreamEventKind,
)
from aware_service_runtime.duplex_client import ServiceHostDuplexClient
from aware_service_runtime.api_ingress.host_context import service_api_host_context
import aware_service_runtime.local_service_host_api_client as client_mod
from aware_service_runtime.local_service_host_api_client import (
    LocalServiceHostAwareApiClient,
    RemoteNodeAwareApiClient,
    build_local_service_host_api_client_for_api_package,
    build_local_service_host_api_client_for_route,
    build_service_api_client_for_api_package,
    select_service_api_dependency_route_for_api_package,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
    service_api_dependency_routes_from_payload,
    service_api_dependency_routes_to_payload,
)
from aware_api_service_dto.comms.models.api import (
    ApiOperation,
    ApiRequestStatus,
    ApiStreamLifecycle,
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
    NetworkResponse,
)
from aware_network_service_dto.comms.models.network_node import CloseStreamRequest


class _FakeUnaryServiceHostClient:
    def __init__(
        self,
        *,
        response: ServiceOperationResponse,
        response_transport_diagnostics: dict[str, object] | None = None,
    ) -> None:
        self.response = response
        self._response_transport_diagnostics = response_transport_diagnostics or {}
        self.requests: list[ServiceHostApiIngressRequest] = []

    @property
    def last_request_timings_s(self) -> dict[str, float]:
        return {"duplex_client.total_s": 0.02}

    @property
    def last_response_transport_diagnostics(self) -> dict[str, object]:
        return dict(self._response_transport_diagnostics)

    async def send_api_ingress_request(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceOperationResponse:
        _ = timeout_s
        self.requests.append(request)
        return self.response


class _FakeStreamHandle:
    def __init__(
        self,
        *,
        events: list[ServiceDuplexStreamEvent],
        response: ServiceOperationResponse,
    ) -> None:
        self._events = events
        self.closed = False
        loop = asyncio.get_running_loop()
        self.response: asyncio.Future[ServiceOperationResponse] = loop.create_future()
        self.response.set_result(response)

    @property
    def events(self) -> AsyncIterator[ServiceDuplexStreamEvent]:
        async def _iterate() -> AsyncIterator[ServiceDuplexStreamEvent]:
            for event in self._events:
                yield event

        return _iterate()

    async def close(self) -> None:
        self.closed = True


class _FakeClosingStreamHandle(_FakeStreamHandle):
    def __init__(
        self,
        *,
        events: list[ServiceDuplexStreamEvent],
    ) -> None:
        self._events = events
        self.closed = False
        loop = asyncio.get_running_loop()
        self.response: asyncio.Future[ServiceOperationResponse] = loop.create_future()

    async def close(self) -> None:
        self.closed = True
        if not self.response.done():
            self.response.set_exception(
                RuntimeError("service host stream closed before terminal response")
            )


class _FakeStreamingServiceHostClient:
    def __init__(self, *, handle: _FakeStreamHandle) -> None:
        self.handle = handle
        self.requests: list[ServiceHostApiIngressRequest] = []

    def open_api_ingress_stream(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        timeout_s: float | None = 5.0,
    ) -> _FakeStreamHandle:
        _ = timeout_s
        self.requests.append(request)
        return self.handle


class _FakeRemoteApiStreamHandle:
    def __init__(self, *, events: list[InvokeApiEndpointResponse]) -> None:
        self._events = events
        self.closed = False
        loop = asyncio.get_running_loop()
        self.response: asyncio.Future[InvokeApiEndpointResponse] = loop.create_future()
        self.response.set_result(
            InvokeApiEndpointResponse(
                status=ApiRequestStatus.succeeded,
                stream_lifecycle=ApiStreamLifecycle.started,
            )
        )

    @property
    def events(self) -> AsyncIterator[InvokeApiEndpointResponse]:
        async def _iterate() -> AsyncIterator[InvokeApiEndpointResponse]:
            for event in self._events:
                yield event

        return _iterate()

    async def close(self) -> None:
        self.closed = True


class _FakeRemoteApiStreamDuplex:
    def __init__(self, *, handle: _FakeRemoteApiStreamHandle) -> None:
        self.handle = handle
        self.operations: list[NetworkOperation] = []

    async def open_api_endpoint_stream(self, **kwargs):  # type: ignore[no-untyped-def]
        self.operations.append(kwargs["operation"])
        return self.handle


def _route(tmp_path: Path) -> ServiceApiDependencyRouteDescriptor:
    return ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware-environment-service",
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware-meta-service",
        api_package_id=uuid4(),
        api_package_name="meta-service-api",
        route_kind=ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC,
        host_id="aware-meta-service-host",
        host_version="1.0.0",
        protocol_version="1",
        socket_path=tmp_path / "meta-service.sock",
        request_timeout_s=7.5,
        service_names=("aware_meta",),
        endpoint_refs_by_service={
            "aware_meta": ("meta.graph.resolve_projection",),
        },
        stream_endpoint_refs_by_service={
            "aware_meta": ("meta.commit.subscribe",),
        },
    )


def _remote_route() -> ServiceApiDependencyRouteDescriptor:
    return ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware-environment-service",
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware-experience-service",
        api_package_id=uuid4(),
        api_package_name="experience-service-api",
        route_kind=ServiceApiDependencyRouteKind.REMOTE_NODE_API_ENDPOINT,
        host_id="aware-experience-service-host",
        host_version="1.0.0",
        protocol_version="1",
        socket_path=None,
        consumer_node_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        provider_node_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        provider_node_base_url="ws://kernel-services.example.test/network_node/network_node",
        route_connection_id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        request_timeout_s=11.0,
        service_names=("aware_experience",),
        endpoint_refs_by_service={
            "aware_experience": (
                "experience.activate_experience_section_graph_binding",
            ),
        },
    )


def test_service_api_dependency_route_descriptor_roundtrips_payload(
    tmp_path: Path,
) -> None:
    route = _route(tmp_path)

    payload = service_api_dependency_routes_to_payload((route,))
    restored = service_api_dependency_routes_from_payload(payload)

    assert len(restored) == 1
    assert restored[0] == route
    assert restored[0].to_payload()["socket_path"] == str(route.socket_path)


def test_remote_service_api_dependency_route_descriptor_roundtrips_without_socket_path() -> (
    None
):
    route = _remote_route()

    payload = service_api_dependency_routes_to_payload((route,))
    restored = service_api_dependency_routes_from_payload(payload)

    assert len(restored) == 1
    assert restored[0] == route
    restored_payload = restored[0].to_payload()
    assert "socket_path" not in restored_payload
    assert restored_payload["route_kind"] == "remote_node_api_endpoint"
    assert restored_payload["consumer_node_id"] == str(route.consumer_node_id)
    assert restored_payload["provider_node_id"] == str(route.provider_node_id)


@pytest.mark.asyncio
async def test_local_service_host_api_client_invokes_unary_api_ingress() -> None:
    invocation_context = {"surface": {"section_key": "primary"}}
    api_call_id = uuid4()
    service_host_client = _FakeUnaryServiceHostClient(
        response=ServiceOperationResponse(
            status=RequestStatus.succeeded,
            response_payload={"ok": True},
            receipt=ServiceApiDispatchReceipt(
                endpoint_ref="meta.graph.resolve_projection",
                discriminant="meta.graph.resolve_projection",
                api_call_id=api_call_id,
            ),
        )
    )
    api_client = LocalServiceHostAwareApiClient(
        actor_id=None,
        client_factory=cast(
            Callable[[], ServiceHostDuplexClient],
            lambda: service_host_client,
        ),
        request_timeout_s=2.0,
        invocation_context=invocation_context,
    )

    response = await api_client.invoke_api_endpoint_raw(
        endpoint_ref="meta.graph.resolve_projection",
        discriminant="meta.graph.resolve_projection",
        request_payload={"projection_name": "Environment"},
    )

    assert response.status == "succeeded"
    assert response.response_payload == {"ok": True}
    assert response.receipt is not None
    assert response.receipt.api_call_id == api_call_id
    assert len(service_host_client.requests) == 1
    request = service_host_client.requests[0]
    assert request.actor_id is None
    assert request.endpoint_ref == "meta.graph.resolve_projection"
    assert request.discriminant == "meta.graph.resolve_projection"
    assert request.stream_requested is False
    assert request.invocation_context == invocation_context
    assert request.request_payload == {"projection_name": "Environment"}


@pytest.mark.asyncio
async def test_local_service_host_api_client_attaches_transport_timings() -> None:
    service_host_client = _FakeUnaryServiceHostClient(
        response=ServiceOperationResponse(
            status=RequestStatus.succeeded,
            response_payload={"ok": True},
            receipt=ServiceApiDispatchReceipt(
                endpoint_ref="meta.graph.resolve_projection",
                discriminant="meta.graph.resolve_projection",
            ),
        ),
        response_transport_diagnostics={
            "servicehost_duplex_server_timings_s": {
                "duplex_server.app_dispatch_s": 0.03,
            },
            "service_api_ingress_timings_s": {
                "service_host.api_ingress.execute_dispatch_s": 0.04,
            },
        },
    )
    api_client = LocalServiceHostAwareApiClient(
        actor_id=None,
        client_factory=cast(
            Callable[[], ServiceHostDuplexClient],
            lambda: service_host_client,
        ),
        request_timeout_s=2.0,
    )

    response = await api_client.invoke_api_endpoint_raw(
        endpoint_ref="meta.graph.resolve_projection",
        discriminant="meta.graph.resolve_projection",
        request_payload={"projection_name": "Environment"},
    )

    assert response.status == "succeeded"
    receipt = cast(dict[str, object], response.transport_receipt)
    assert receipt["api_transport_kind"] == "local_service_host_ipc"
    timings = cast(dict[str, object], receipt["api_transport_timings_s"])
    assert "api_transport.build_ingress_request_s" in timings
    assert "api_transport.send_api_ingress_request_s" in timings
    assert "api_transport.service_response_adapt_s" in timings
    assert "api_transport.total_s" in timings
    duplex_client_timings = cast(
        dict[str, object],
        receipt["servicehost_duplex_client_timings_s"],
    )
    assert duplex_client_timings["duplex_client.total_s"] == 0.02
    duplex_server_timings = cast(
        dict[str, object],
        receipt["servicehost_duplex_server_timings_s"],
    )
    assert duplex_server_timings["duplex_server.app_dispatch_s"] == 0.03
    api_ingress_timings = cast(
        dict[str, object],
        receipt["service_api_ingress_timings_s"],
    )
    assert api_ingress_timings["service_host.api_ingress.execute_dispatch_s"] == 0.04


@pytest.mark.asyncio
async def test_local_service_host_api_client_uses_request_payload_actor_id() -> None:
    actor_id = uuid4()
    service_host_client = _FakeUnaryServiceHostClient(
        response=ServiceOperationResponse(
            status=RequestStatus.succeeded,
            response_payload={"ok": True},
        )
    )
    api_client = LocalServiceHostAwareApiClient(
        actor_id=None,
        client_factory=cast(
            Callable[[], ServiceHostDuplexClient],
            lambda: service_host_client,
        ),
        request_timeout_s=2.0,
    )

    response = await api_client.invoke_api_endpoint_raw(
        endpoint_ref="meta.graph.invoke_function",
        discriminant="meta.graph.invoke_function",
        request_payload={
            "actor_id": str(actor_id),
            "domain_branch_id": str(uuid4()),
        },
    )

    assert response.status == "succeeded"
    assert len(service_host_client.requests) == 1
    request = service_host_client.requests[0]
    assert request.actor_id == actor_id


@pytest.mark.asyncio
async def test_local_service_host_api_client_streams_api_ingress_events() -> None:
    actor_id = uuid4()
    stream_envelope = ServiceDuplexStreamEventEnvelope.from_contract(
        ServiceStreamEventEnvelope(
            session=ServiceStreamSession(
                session_id=uuid4(),
                request=ServiceOperationRequest(
                    context=ServiceOperationContext(
                        actor_id=None,
                        environment_id=uuid4(),
                        process_id=uuid4(),
                        thread_id=uuid4(),
                        branch_id=uuid4(),
                        projection_hash="service.api_ingress",
                    ),
                    service="aware-meta-service",
                    operation={"kind": "api_ingress_stream"},
                ),
            ),
            sequence=1,
            kind=ServiceStreamEventKind.NOTICE,
            item_key="commit:1",
            payload={"commit_id": str(UUID(int=1))},
        )
    )
    handle = _FakeStreamHandle(
        events=[
            ServiceDuplexStreamEvent(
                kind=ServiceDuplexStreamEventKind.RESPONSE,
                response=ServiceDuplexOperationResponse(
                    status=RequestStatus.pending,
                    response_payload=stream_envelope.model_dump(mode="json"),
                    stream_lifecycle=StreamLifecycle.started,
                ),
            ),
            ServiceDuplexStreamEvent(kind=ServiceDuplexStreamEventKind.CLOSE),
        ],
        response=ServiceOperationResponse(
            status=RequestStatus.succeeded,
            stream_lifecycle=StreamLifecycle.started,
        ),
    )
    service_host_client = _FakeStreamingServiceHostClient(handle=handle)
    api_client = LocalServiceHostAwareApiClient(
        actor_id=actor_id,
        client_factory=cast(
            Callable[[], ServiceHostDuplexClient],
            lambda: service_host_client,
        ),
    )

    stream = await api_client.open_api_endpoint_stream_raw(
        endpoint_ref="meta.commit.subscribe",
        discriminant="meta.commit.subscribe",
        request_payload={"subscriber_id": "aware_environment.topology"},
    )
    events = [event async for event in stream.events]
    await stream.close()

    assert len(events) == 1
    assert events[0].status == "pending"
    assert events[0].response_payload == {"commit_id": str(UUID(int=1))}
    assert handle.closed is True
    assert len(service_host_client.requests) == 1
    request = service_host_client.requests[0]
    assert request.actor_id == actor_id
    assert request.endpoint_ref == "meta.commit.subscribe"
    assert request.stream_requested is True


@pytest.mark.asyncio
async def test_local_service_host_api_client_consumes_response_future_on_early_stream_close() -> (
    None
):
    actor_id = uuid4()
    stream_envelope = ServiceDuplexStreamEventEnvelope.from_contract(
        ServiceStreamEventEnvelope(
            session=ServiceStreamSession(
                session_id=uuid4(),
                request=ServiceOperationRequest(
                    context=ServiceOperationContext(
                        actor_id=None,
                        environment_id=uuid4(),
                        process_id=uuid4(),
                        thread_id=uuid4(),
                        branch_id=uuid4(),
                        projection_hash="service.api_ingress",
                    ),
                    service="aware-meta-service",
                    operation={"kind": "api_ingress_stream"},
                ),
            ),
            sequence=1,
            kind=ServiceStreamEventKind.NOTICE,
            item_key="commit:1",
            payload={"commit_id": str(UUID(int=1))},
        )
    )
    handle = _FakeClosingStreamHandle(
        events=[
            ServiceDuplexStreamEvent(
                kind=ServiceDuplexStreamEventKind.RESPONSE,
                response=ServiceDuplexOperationResponse(
                    status=RequestStatus.pending,
                    response_payload=stream_envelope.model_dump(mode="json"),
                    stream_lifecycle=StreamLifecycle.started,
                ),
            ),
        ],
    )
    service_host_client = _FakeStreamingServiceHostClient(handle=handle)
    api_client = LocalServiceHostAwareApiClient(
        actor_id=actor_id,
        client_factory=cast(
            Callable[[], ServiceHostDuplexClient],
            lambda: service_host_client,
        ),
    )

    stream = await api_client.open_api_endpoint_stream_raw(
        endpoint_ref="meta.commit.subscribe",
        discriminant="meta.commit.subscribe",
        request_payload={"subscriber_id": "aware_environment.topology"},
    )
    iterator = stream.events.__aiter__()
    event = await anext(iterator)
    await iterator.aclose()

    assert event.response_payload == {"commit_id": str(UUID(int=1))}
    assert handle.closed is True
    assert handle.response.done() is True


@pytest.mark.asyncio
async def test_remote_node_api_client_streams_with_explicit_api_stream_request() -> (
    None
):
    actor_id = uuid4()
    handle = _FakeRemoteApiStreamHandle(
        events=[
            InvokeApiEndpointResponse(
                actor_id=actor_id,
                status=ApiRequestStatus.pending,
                response_payload={"event_id": "evt-1"},
                stream_lifecycle=ApiStreamLifecycle.started,
            )
        ]
    )
    fake_duplex = _FakeRemoteApiStreamDuplex(handle=handle)
    api_client = RemoteNodeAwareApiClient(
        actor_id=actor_id,
        endpoint="ws://kernel-services.example.test",
        consumer_node_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        provider_node_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        connection_id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        request_timeout_s=11.0,
    )
    transport = cast(client_mod._RemoteNodeApiEndpointTransport, api_client.transport)  # type: ignore[attr-defined]
    transport._duplex = cast(client_mod.ApiEndpointDuplexClient, fake_duplex)  # type: ignore[attr-defined]

    stream = await api_client.open_api_endpoint_stream_raw(
        endpoint_ref="reactivity.event.subscribe_events",
        discriminant="reactivity.event.subscribe_events",
        request_payload={"subscriber_ref": "dogfood"},
    )
    events = [event async for event in stream.events]

    assert events[0].status == "pending"
    assert events[0].response_payload == {"event_id": "evt-1"}
    assert handle.closed is True
    assert len(fake_duplex.operations) == 1
    operation = fake_duplex.operations[0]
    assert operation.type is NetworkOperationType.api
    assert operation.api_operation is not None
    request = operation.api_operation.request
    assert isinstance(request, StreamApiEndpointRequest)
    assert request.endpoint_ref == "reactivity.event.subscribe_events"
    assert request.operation == "stream_api_endpoint"


@pytest.mark.asyncio
async def test_remote_api_endpoint_stream_close_sends_node_close_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor_id = uuid4()
    consumer_node_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    provider_node_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    connection_id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    terminal_started = asyncio.Event()
    captured: dict[str, object] = {}

    async def _fake_terminal(
        self: object,
        *,
        connection_id: UUID,
        request_id: UUID,
        request_data: str,
        actor_id: UUID | None,
        timeout_s: float | None,
    ) -> InvokeApiEndpointResponse:
        _ = (self, connection_id, request_id, request_data, actor_id, timeout_s)
        terminal_started.set()
        await asyncio.Event().wait()
        raise AssertionError("terminal task should be cancelled by close")

    async def _fake_send_notification(
        self: object,
        connection_id: UUID,
        data_serialized: str,
    ) -> bool:
        _ = self
        captured["connection_id"] = connection_id
        captured["operation"] = NetworkOperation.model_validate_json(data_serialized)
        return True

    monkeypatch.setattr(
        client_mod._RemoteApiEndpointStreamDuplexClient,
        "_run_api_endpoint_stream_terminal",
        _fake_terminal,
    )
    monkeypatch.setattr(
        client_mod._RemoteApiEndpointStreamDuplexClient,
        "send_notification",
        _fake_send_notification,
    )
    duplex = client_mod._RemoteApiEndpointStreamDuplexClient(
        client_type=NetworkAppType.network_node.value,
        server_type=NetworkAppType.network_node.value,
        endpoint="ws://kernel-services.example.test/network_node/network_node",
        request_timeout=11.0,
    )
    stream_operation = NetworkOperation(
        id=uuid4(),
        message_type=NetworkOperationMessageType.request,
        type=NetworkOperationType.api,
        network_request=NetworkRequest(id=uuid4(), requester_id=actor_id),
        network_operation_hop_list=[
            NetworkOperationHop(
                source_app_type=NetworkAppType.network_node,
                source_node_id=consumer_node_id,
                target_app_type=NetworkAppType.network_node,
                target_node_id=provider_node_id,
            )
        ],
        api_operation=ApiOperation(
            request=StreamApiEndpointRequest(
                actor_id=actor_id,
                endpoint_ref="reactivity.event.subscribe_events",
                discriminant="reactivity.event.subscribe_events",
                request_payload={"subscriber_ref": "dogfood"},
            )
        ),
    )

    handle = await duplex.open_api_endpoint_stream(
        connection_id=connection_id,
        operation=stream_operation,
        actor_id=actor_id,
        timeout_s=11.0,
    )
    await terminal_started.wait()
    await handle.close()

    assert captured["connection_id"] == connection_id
    close_operation = captured["operation"]
    assert isinstance(close_operation, NetworkOperation)
    assert close_operation.message_type is NetworkOperationMessageType.notification
    assert close_operation.type is NetworkOperationType.network_node
    close_hop = close_operation.network_operation_hop_list[0]
    assert close_hop.source_node_id == consumer_node_id
    assert close_hop.target_node_id == provider_node_id
    assert close_operation.network_node_operation is not None
    close_request = close_operation.network_node_operation.request
    assert isinstance(close_request, CloseStreamRequest)
    assert close_request.actor_id == actor_id
    assert close_request.node_id == provider_node_id
    assert close_request.network_operation_id == stream_operation.id
    assert duplex._api_endpoint_streams == {}


@pytest.mark.asyncio
async def test_local_service_host_api_client_configured_actor_overrides_payload_actor() -> (
    None
):
    configured_actor_id = uuid4()
    payload_actor_id = uuid4()
    service_host_client = _FakeUnaryServiceHostClient(
        response=ServiceOperationResponse(
            status=RequestStatus.succeeded,
            response_payload={"ok": True},
        )
    )
    api_client = LocalServiceHostAwareApiClient(
        actor_id=configured_actor_id,
        client_factory=cast(
            Callable[[], ServiceHostDuplexClient],
            lambda: service_host_client,
        ),
        request_timeout_s=2.0,
    )

    await api_client.invoke_api_endpoint_raw(
        endpoint_ref="meta.graph.invoke_function",
        discriminant="meta.graph.invoke_function",
        request_payload={"actor_id": str(payload_actor_id)},
    )

    assert service_host_client.requests[0].actor_id == configured_actor_id


def test_build_local_service_host_api_client_for_route_uses_route_config(
    tmp_path: Path,
) -> None:
    api_client = build_local_service_host_api_client_for_route(_route(tmp_path))

    assert api_client.config.endpoint == "aware-service-host://aware-meta-service-host"
    assert api_client.config.request_timeout == 7.5


def test_select_service_api_dependency_route_for_api_package(tmp_path: Path) -> None:
    route = _route(tmp_path)

    selected = select_service_api_dependency_route_for_api_package(
        (route,),
        api_package_name="meta-service-api",
    )

    assert selected == route
    assert (
        select_service_api_dependency_route_for_api_package(
            (route,),
            api_package_name="experience-service-api",
        )
        is None
    )


def test_select_service_api_dependency_route_filters_by_consumer_package(
    tmp_path: Path,
) -> None:
    identity_consumer_id = uuid4()
    experience_consumer_id = uuid4()
    route = replace(
        _route(tmp_path),
        api_package_name="reactivity-service-api",
        consumer_service_package_id=identity_consumer_id,
        consumer_service_package_name="aware-identity-service",
    )
    other_consumer_route = replace(
        route,
        consumer_service_package_id=experience_consumer_id,
        consumer_service_package_name="aware-experience-service",
    )

    selected = select_service_api_dependency_route_for_api_package(
        (route, other_consumer_route),
        api_package_name="reactivity-service-api",
        consumer_service_package_id=identity_consumer_id,
        consumer_service_package_name="aware-identity-service",
    )

    assert selected == route


def test_select_service_api_dependency_route_still_rejects_ambiguous_provider(
    tmp_path: Path,
) -> None:
    consumer_id = uuid4()
    route = replace(
        _route(tmp_path),
        api_package_name="reactivity-service-api",
        consumer_service_package_id=consumer_id,
        consumer_service_package_name="aware-identity-service",
    )
    competing_provider_route = replace(
        route,
        provider_service_package_id=uuid4(),
        provider_service_package_name="aware-other-reactivity-service",
        host_id="aware-other-service-host",
        socket_path=tmp_path / "other-service.sock",
    )

    with pytest.raises(RuntimeError, match="Resolved multiple Service API"):
        select_service_api_dependency_route_for_api_package(
            (route, competing_provider_route),
            api_package_name="reactivity-service-api",
            consumer_service_package_id=consumer_id,
            consumer_service_package_name="aware-identity-service",
        )


def test_build_local_service_host_api_client_for_api_package_preserves_context(
    tmp_path: Path,
) -> None:
    invocation_context = {"surface": {"section_key": "primary"}}
    api_client = build_local_service_host_api_client_for_api_package(
        (_route(tmp_path),),
        api_package_name="meta-service-api",
        actor_id=UUID(int=7),
        invocation_context=invocation_context,
    )

    assert api_client is not None
    assert api_client.config.actor_id == UUID(int=7)
    assert api_client.config.invocation_context == invocation_context


def test_build_service_api_client_for_api_package_uses_current_host_consumer(
    tmp_path: Path,
) -> None:
    route = replace(
        _route(tmp_path),
        api_package_name="reactivity-service-api",
        consumer_service_package_name="aware-identity-service",
        socket_path=tmp_path / "identity-route.sock",
        request_timeout_s=3.0,
    )
    other_consumer_route = replace(
        route,
        consumer_service_package_id=uuid4(),
        consumer_service_package_name="aware-experience-service",
        socket_path=tmp_path / "experience-route.sock",
        request_timeout_s=9.0,
    )

    with service_api_host_context(
        operation_context=ServiceOperationContext(
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="service.api_ingress",
        ),
        graph_gateway=None,
        service_name="aware_identity",
        service_package_id=route.consumer_service_package_id,
        service_package_name="aware-identity-service",
    ):
        api_client = build_service_api_client_for_api_package(
            (route, other_consumer_route),
            api_package_name="reactivity-service-api",
        )

    assert isinstance(api_client, LocalServiceHostAwareApiClient)
    assert api_client.config.request_timeout == 3.0


@pytest.mark.asyncio
async def test_remote_node_api_client_invokes_network_api_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = _remote_route()
    captured: dict[str, object] = {}

    class _FakeApiEndpointDuplexClient:
        def __init__(self, **kwargs: object) -> None:
            captured["client_kwargs"] = kwargs

        async def ensure_connection(
            self,
            connection_id: UUID,
            *,
            external_url: str,
        ) -> None:
            captured["ensure_connection_id"] = connection_id
            captured["external_url"] = external_url

        async def send_request(
            self,
            *,
            connection_id: UUID,
            data_serialized: str,
            timeout_s: float | None = None,
        ) -> str:
            captured["send_connection_id"] = connection_id
            captured["timeout_s"] = timeout_s
            forwarded = NetworkOperation.model_validate_json(data_serialized)
            captured["forwarded"] = forwarded
            response = NetworkOperation(
                id=forwarded.id,
                message_type=NetworkOperationMessageType.response,
                type=NetworkOperationType.api,
                network_response=NetworkResponse(
                    network_request_id=(
                        forwarded.network_request.id
                        if forwarded.network_request is not None
                        else None
                    ),
                    status=NetworkRequestStatus.succeeded,
                ),
                api_operation=ApiOperation(
                    response=InvokeApiEndpointResponse(
                        actor_id=UUID(int=7),
                        status=ApiRequestStatus.succeeded,
                        response_payload={"activated": True},
                    )
                ),
            )
            return response.model_dump_json()

    monkeypatch.setattr(
        client_mod,
        "_RemoteApiEndpointStreamDuplexClient",
        _FakeApiEndpointDuplexClient,
    )
    api_client = build_service_api_client_for_api_package(
        (route,),
        api_package_name="experience-service-api",
        actor_id=UUID(int=7),
        invocation_context={"surface": {"section_key": "primary"}},
    )

    assert isinstance(api_client, RemoteNodeAwareApiClient)
    response = await api_client.invoke_api_endpoint_raw(
        endpoint_ref="experience.activate_experience_section_graph_binding",
        discriminant="experience.activate_experience_section_graph_binding",
        request_payload={"binding_key": "identity.admission"},
    )

    assert response.status == "succeeded"
    assert response.response_payload == {"activated": True}
    assert captured["external_url"] == route.provider_node_base_url
    assert captured["ensure_connection_id"] == route.route_connection_id
    assert captured["send_connection_id"] == route.route_connection_id
    assert captured["timeout_s"] == route.request_timeout_s
    forwarded = captured["forwarded"]
    assert isinstance(forwarded, NetworkOperation)
    assert forwarded.type is NetworkOperationType.api
    hop = forwarded.network_operation_hop_list[0]
    assert hop.source_node_id == route.consumer_node_id
    assert hop.target_node_id == route.provider_node_id
    assert forwarded.api_operation is not None
    request = forwarded.api_operation.request
    assert request is not None
    assert request.actor_id == UUID(int=7)
    assert forwarded.network_request is not None
    assert forwarded.network_request.requester_id == UUID(int=7)
    assert (
        request.endpoint_ref == "experience.activate_experience_section_graph_binding"
    )
    assert request.request_payload == {"binding_key": "identity.admission"}
    assert request.invocation_context is not None
    assert request.invocation_context.surface is not None
    assert request.invocation_context.surface.section_key == "primary"


@pytest.mark.asyncio
async def test_remote_node_api_client_uses_request_payload_actor_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    route = _remote_route()
    actor_id = uuid4()
    captured: dict[str, object] = {}

    class _FakeApiEndpointDuplexClient:
        def __init__(self, **kwargs: object) -> None:
            captured["client_kwargs"] = kwargs

        async def ensure_connection(
            self,
            connection_id: UUID,
            *,
            external_url: str,
        ) -> None:
            captured["ensure_connection_id"] = connection_id
            captured["external_url"] = external_url

        async def send_request(
            self,
            *,
            connection_id: UUID,
            data_serialized: str,
            timeout_s: float | None = None,
        ) -> str:
            captured["send_connection_id"] = connection_id
            captured["timeout_s"] = timeout_s
            forwarded = NetworkOperation.model_validate_json(data_serialized)
            captured["forwarded"] = forwarded
            response = NetworkOperation(
                id=forwarded.id,
                message_type=NetworkOperationMessageType.response,
                type=NetworkOperationType.api,
                network_response=NetworkResponse(
                    network_request_id=(
                        forwarded.network_request.id
                        if forwarded.network_request is not None
                        else None
                    ),
                    status=NetworkRequestStatus.succeeded,
                ),
                api_operation=ApiOperation(
                    response=InvokeApiEndpointResponse(
                        actor_id=actor_id,
                        status=ApiRequestStatus.succeeded,
                        response_payload={"activated": True},
                    )
                ),
            )
            return response.model_dump_json()

    monkeypatch.setattr(
        client_mod,
        "_RemoteApiEndpointStreamDuplexClient",
        _FakeApiEndpointDuplexClient,
    )
    api_client = build_service_api_client_for_api_package(
        (route,),
        api_package_name="experience-service-api",
        actor_id=None,
    )

    assert isinstance(api_client, RemoteNodeAwareApiClient)
    response = await api_client.invoke_api_endpoint_raw(
        endpoint_ref="experience.activate_experience_section_graph_binding",
        discriminant="experience.activate_experience_section_graph_binding",
        request_payload={
            "actor_id": str(actor_id),
            "binding_key": "identity.admission",
        },
    )

    assert response.status == "succeeded"
    forwarded = captured["forwarded"]
    assert isinstance(forwarded, NetworkOperation)
    assert forwarded.network_request is not None
    assert forwarded.network_request.requester_id == actor_id
    assert forwarded.api_operation is not None
    request = forwarded.api_operation.request
    assert request is not None
    assert request.actor_id == actor_id
