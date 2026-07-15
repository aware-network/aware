from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

import pytest

from aware_api_service_dto.comms.models.api import (
    ApiRequestStatus,
    ApiStreamLifecycle,
    InvokeApiEndpointResponse,
    StreamApiEndpointRequest,
)
from aware_network_service_dto.comms.models.network import (
    NetworkOperation,
    NetworkOperationType,
)
from aware_api.invoker import AwareApiEndpointInvoker
from aware_sdk_network.transport.provider_refs import (
    RemoteNodeAwareApiClient,
    build_api_client_for_api_package,
    endpoint_refs_for_api_package,
    routes_from_provider_refs_payload,
    select_route_for_api_package,
)


CONSUMER_NODE_ID = UUID("019e9c01-01ad-7b61-a5ee-1ea536cbb642")
CONSUMER_SERVICE_PACKAGE_ID = UUID("f8a7cd53-f724-5d14-9b6e-6a55daefffe1")
PROVIDER_NODE_ID = UUID("d2928ba5-691c-57b3-8d19-01a93c27e1c6")
PROVIDER_SERVICE_PACKAGE_ID = UUID("9ecda6a6-0995-5821-8199-c2d767b52f2c")
API_PACKAGE_ID = UUID("eb9822cb-6313-56b0-ae6f-d3e871875555")
ROUTE_CONNECTION_ID = UUID("ae2f3c2e-0c84-521e-9b4e-7cc680960d54")


class _FakeRemoteApiStreamHandle:
    def __init__(self, *, events: list[InvokeApiEndpointResponse]) -> None:
        self._events = events
        self.closed = False

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


def _provider_refs_payload() -> list[dict[str, object]]:
    return [
        {
            "provider_node_id": str(PROVIDER_NODE_ID),
            "provider_node_base_url": "ws://127.0.0.1:8971",
            "route_connection_id": str(ROUTE_CONNECTION_ID),
            "request_timeout_s": 42.0,
            "service_package_ref": {
                "service_package_id": str(PROVIDER_SERVICE_PACKAGE_ID),
                "package_name": "aware_ontology",
                "provided_api_packages": [
                    {
                        "api_package_id": str(API_PACKAGE_ID),
                        "api_package_name": "ontology-service-api",
                    }
                ],
            },
            "hosted_service_advertisement": {
                "host_id": "ontology-node",
                "service_name": "aware_ontology",
                "protocol_version": "1",
                "endpoint_refs": [
                    "ontology.graph.resolve_projection",
                    "ontology.runtime.resolve_runtime_artifact_set",
                ],
                "stream_endpoint_refs": ["ontology.commit.subscribe"],
            },
        }
    ]


def test_routes_from_provider_refs_payload_is_sdk_network_owned() -> None:
    routes = routes_from_provider_refs_payload(
        _provider_refs_payload(),
        consumer_node_id=CONSUMER_NODE_ID,
        consumer_service_package_id=CONSUMER_SERVICE_PACKAGE_ID,
        consumer_service_package_name="sdk-live-integration-proof",
    )

    assert len(routes) == 1
    route = routes[0]
    assert route.consumer_node_id == CONSUMER_NODE_ID
    assert route.consumer_service_package_id == CONSUMER_SERVICE_PACKAGE_ID
    assert route.provider_node_id == PROVIDER_NODE_ID
    assert route.provider_service_package_id == PROVIDER_SERVICE_PACKAGE_ID
    assert route.provider_node_base_url == "ws://127.0.0.1:8971"
    assert route.route_connection_id == ROUTE_CONNECTION_ID
    assert route.request_timeout_s == 42.0
    assert endpoint_refs_for_api_package(
        routes,
        api_package_name="ontology-service-api",
    ) == {
        "ontology.graph.resolve_projection",
        "ontology.runtime.resolve_runtime_artifact_set",
    }


def test_build_api_client_for_api_package_returns_remote_node_invoker() -> None:
    routes = routes_from_provider_refs_payload(
        _provider_refs_payload(),
        consumer_node_id=CONSUMER_NODE_ID,
        consumer_service_package_id=CONSUMER_SERVICE_PACKAGE_ID,
        consumer_service_package_name="sdk-live-integration-proof",
        request_timeout_s=180.0,
    )

    route = select_route_for_api_package(
        routes,
        api_package_name="ontology-service-api",
    )
    assert route is not None
    assert route.request_timeout_s == 180.0

    client = build_api_client_for_api_package(
        routes,
        api_package_name="ontology-service-api",
        actor_id=CONSUMER_SERVICE_PACKAGE_ID,
    )

    assert isinstance(client, AwareApiEndpointInvoker)
    assert isinstance(client, RemoteNodeAwareApiClient)
    assert client.config.actor_id == CONSUMER_SERVICE_PACKAGE_ID
    assert client.config.endpoint == "ws://127.0.0.1:8971"
    assert client.config.consumer_node_id == CONSUMER_NODE_ID
    assert client.config.provider_node_id == PROVIDER_NODE_ID
    assert client.config.connection_id == ROUTE_CONNECTION_ID
    assert client.config.request_timeout == 180.0


@pytest.mark.asyncio
async def test_remote_node_api_client_streams_with_explicit_api_stream_request() -> (
    None
):
    actor_id = CONSUMER_SERVICE_PACKAGE_ID
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
        endpoint="ws://127.0.0.1:8971",
        consumer_node_id=CONSUMER_NODE_ID,
        provider_node_id=PROVIDER_NODE_ID,
        connection_id=ROUTE_CONNECTION_ID,
        request_timeout_s=11.0,
    )
    api_client.transport._duplex = fake_duplex  # type: ignore[attr-defined]

    stream = await api_client.open_api_endpoint_stream_raw(
        endpoint_ref="ontology.commit.subscribe",
        discriminant="ontology.commit.subscribe",
        request_payload={"subscriber_id": "sdk-core-proof"},
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
    assert request.endpoint_ref == "ontology.commit.subscribe"
    assert request.operation == "stream_api_endpoint"
