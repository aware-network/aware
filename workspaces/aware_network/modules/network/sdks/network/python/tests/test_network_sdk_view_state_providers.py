from __future__ import annotations

from uuid import uuid4

import pytest

from aware_network_sdk.view_state_providers import (
    network_territory_discovery_v1_provider_input_from_client,
    network_territory_discovery_view_state,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverTerritoryResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkEnvironmentDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkHostedServiceDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodeRouteDescriptor,
)
from aware_network_service_dto.comms.models.network_service import NetworkPeerDescriptor
from aware_network_service_dto.comms.models.network_service import (
    NetworkTerritoryNodeDescriptor,
)


def test_network_territory_discovery_view_state_maps_response() -> None:
    node_id = uuid4()
    environment_id = uuid4()
    service_id = uuid4()
    receipt = NetworkDiscoverTerritoryResponse(
        success=True,
        summary="1 nodes, 1 environments, 1 hosted services",
        nodes=[
            NetworkTerritoryNodeDescriptor(
                node=NetworkNodeRouteDescriptor(
                    node_id=node_id,
                    public_key="public-key",
                    hostname="kernel",
                    port=8911,
                    base_url="ws://kernel:8911",
                ),
                environments=[
                    NetworkEnvironmentDescriptor(
                        node_id=node_id,
                        environment_id=environment_id,
                        environment_key="kernel",
                        environment_title="Kernel Network",
                        role="primary",
                        experience_names=["aware-network"],
                    )
                ],
                hosted_services=[
                    NetworkHostedServiceDescriptor(
                        service_id=service_id,
                        service_name="experience",
                        service_package_names=["aware-experience-service"],
                        endpoint_refs=["experience.resolve"],
                        host_id="service-host",
                        protocol_version="1",
                    )
                ],
                peers=[
                    NetworkPeerDescriptor(
                        source_node_id=node_id,
                        target_node_id=uuid4(),
                        peer_node_id=uuid4(),
                        peer_base_url="ws://peer:8912",
                    )
                ],
            )
        ],
    )

    state = network_territory_discovery_view_state(
        provider_input={
            "receipt": receipt,
            "authority_source_url": "http://network.local",
        }
    )

    assert state.status == "live"
    assert state.summary == "1 nodes, 1 environments, 1 hosted services"
    assert state.authority_source_url == "http://network.local"
    assert state.nodes[0].node is not None
    assert state.nodes[0].node.node_id == str(node_id)
    assert state.nodes[0].environments[0].environment_key == "kernel"
    assert state.nodes[0].hosted_services[0].service_name == "experience"
    assert state.provenance["view_ref"] == "network.territory_discovery"
    assert state.provenance["projection_view_key"] == "territory.discovery.v1"
    assert state.provenance["node_count"] == 1
    assert state.provenance["environment_count"] == 1
    assert state.provenance["hosted_service_count"] == 1


@pytest.mark.asyncio
async def test_network_territory_provider_input_from_client() -> None:
    node_id = uuid4()
    receipt = NetworkDiscoverTerritoryResponse(
        success=True,
        summary="1 nodes, 0 environments, 0 hosted services",
        nodes=[
            NetworkTerritoryNodeDescriptor(
                node=NetworkNodeRouteDescriptor(
                    node_id=node_id,
                    hostname="kernel",
                    port=8911,
                )
            )
        ],
    )

    class _Client:
        def __init__(self) -> None:
            self.calls = []

        async def discover_territory(self, **kwargs):  # noqa: ANN001, ANN201
            self.calls.append(kwargs)
            return receipt

    client = _Client()

    provider_input = await network_territory_discovery_v1_provider_input_from_client(
        client=client,
        limit_nodes=10,
        authority_source_url="http://network.local",
    )
    state = network_territory_discovery_view_state(provider_input=provider_input)

    assert client.calls[0]["limit_nodes"] == 10
    assert provider_input.receipt == receipt
    assert state.status == "live"
    assert state.nodes[0].node is not None
    assert state.nodes[0].node.hostname == "kernel"
