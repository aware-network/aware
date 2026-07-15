from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest

from aware_network_sdk import (
    NetworkGeneratedApiClient,
    NetworkExperienceTerritoryQuery,
    NetworkSdkCache,
    NetworkSdkClient,
    NetworkSdkError,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverExperienceTerritoryResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkEnvironmentDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkExperienceServiceCandidate,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkExperienceTerritoryEntry,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkHostedServiceDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodeRouteDescriptor,
)


class _DiscoveryApi:
    def __init__(self, response: NetworkDiscoverExperienceTerritoryResponse) -> None:
        self.discover_experience_requests = []
        self._response = response

    async def discover_experience_territory(self, request):  # noqa: ANN001, ANN201
        self.discover_experience_requests.append(request)
        return self._response


class _NetworkApi:
    def __init__(self, discovery: _DiscoveryApi) -> None:
        self.discovery = discovery


class _ApiClient:
    def __init__(self, network: _NetworkApi) -> None:
        self.network = network


def _as_generated_client(client: _ApiClient) -> NetworkGeneratedApiClient:
    return cast(NetworkGeneratedApiClient, cast(object, client))


@pytest.mark.asyncio
async def test_network_sdk_discovers_experience_territory_and_records_cache() -> None:
    consumer_node_id = uuid4()
    provider_node_id = uuid4()
    environment_id = uuid4()
    service_id = uuid4()
    route_connection_id = uuid4()
    hosted_service = NetworkHostedServiceDescriptor(
        service_id=service_id,
        service_name="conversation",
        service_package_names=["aware-conversation-service"],
        endpoint_refs=["conversation.create_conversation"],
        host_id="service-host",
        protocol_version="1",
    )
    candidate = NetworkExperienceServiceCandidate(
        hosted_service=hosted_service,
        provider_node_id=provider_node_id,
        provider_node_base_url="ws://127.0.0.1:8912",
        route_connection_id=route_connection_id,
        route_status="reachable",
        matched_service_package_names=["aware-conversation-service"],
        matched_endpoint_refs=["conversation.create_conversation"],
    )
    entry = NetworkExperienceTerritoryEntry(
        experience_name="workspace.collaboration",
        node=NetworkNodeRouteDescriptor(
            node_id=provider_node_id,
            public_key="provider-key",
            hostname="127.0.0.1",
            port=8912,
            base_url="ws://127.0.0.1:8912",
        ),
        environment=NetworkEnvironmentDescriptor(
            node_id=provider_node_id,
            environment_id=environment_id,
            environment_key="workspace",
            experience_names=["workspace.collaboration"],
        ),
        service_candidates=[candidate],
        route_status="reachable",
    )
    response = NetworkDiscoverExperienceTerritoryResponse(
        success=True,
        experience_name="workspace.collaboration",
        entries=[entry],
        summary="1 experience territory entries for 'workspace.collaboration'",
    )
    discovery_api = _DiscoveryApi(response)
    cache = NetworkSdkCache()
    client = NetworkSdkClient(
        api_client=_as_generated_client(_ApiClient(_NetworkApi(discovery_api))),
        cache=cache,
    )

    resolved = await client.discover_experience_territory(
        experience_name="workspace.collaboration",
        required_service_package_names=("aware-conversation-service",),
        required_endpoint_refs=("conversation.create_conversation",),
        consumer_node_id=consumer_node_id,
        require_access_evidence=True,
        access_evidence_refs=("economy://service-access/receipt-1",),
        limit_entries=25,
    )

    assert resolved == response
    request = discovery_api.discover_experience_requests[0]
    assert request.experience_name == "workspace.collaboration"
    assert request.required_service_package_names == ["aware-conversation-service"]
    assert request.required_endpoint_refs == ["conversation.create_conversation"]
    assert request.consumer_node_id == consumer_node_id
    assert request.require_access_evidence is True
    assert request.access_evidence_refs == ["economy://service-access/receipt-1"]
    assert request.limit_entries == 25
    assert cache.experience_territory_by_query[
        NetworkExperienceTerritoryQuery(
            experience_name="workspace.collaboration",
            required_service_package_names=("aware-conversation-service",),
            required_endpoint_refs=("conversation.create_conversation",),
            consumer_node_id=consumer_node_id,
            require_access_evidence=True,
            access_evidence_refs=("economy://service-access/receipt-1",),
            limit_entries=25,
        )
    ] == (entry,)


@pytest.mark.asyncio
async def test_network_sdk_experience_territory_raises_on_error_response() -> None:
    response = NetworkDiscoverExperienceTerritoryResponse(
        success=False,
        error="network unavailable",
    )
    discovery_api = _DiscoveryApi(response)
    client = NetworkSdkClient(
        api_client=_as_generated_client(_ApiClient(_NetworkApi(discovery_api)))
    )

    with pytest.raises(NetworkSdkError, match="network unavailable"):
        await client.discover_experience_territory(
            experience_name="workspace.collaboration"
        )
