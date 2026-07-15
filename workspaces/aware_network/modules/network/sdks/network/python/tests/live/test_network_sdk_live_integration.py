from __future__ import annotations

from dataclasses import dataclass
import os
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
import pytest_asyncio

from aware_network_sdk import AwareNetworkSdk
from aware_network_sdk.view_state_providers import (
    network_territory_discovery_v1_provider_input_from_client,
    network_territory_discovery_view_state,
)
from aware_network_service_api import AwareNetworkServiceApiClient
from aware_network_service_api._bindings import ENDPOINT_REF_BY_NAME
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodePublicationEnvironment,
    NetworkNodePublicationHostedService,
    NetworkNodePublicationIntent,
    NetworkNodePublicationNode,
)
from aware_sdk_network.testing.live import (
    LiveSdkEndpointProofRow,
    build_live_api_client_for_package,
    close_live_api_client,
    endpoint_refs_for_api_package,
)


pytest_plugins = ("aware_sdk_network.testing.pytest_plugin",)


NETWORK_API_PACKAGE_NAME = "network-service-api"
_FIXTURE_NAMESPACE = uuid5(NAMESPACE_URL, "aware.network.sdk.live.territory.v1")
_FIXTURE_EXPERIENCE_NAME = "network.sdk.live.territory"
_FIXTURE_SERVICE_PACKAGE_NAME = "aware-network-sdk-live-service"
_FIXTURE_ENDPOINT_REF = "network.sdk.live.endpoint"


@dataclass(frozen=True, slots=True)
class NetworkLiveSdk:
    api: AwareNetworkServiceApiClient
    sdk: AwareNetworkSdk
    actor_id: UUID | None


NETWORK_ENDPOINT_MATRIX: tuple[LiveSdkEndpointProofRow, ...] = (
    LiveSdkEndpointProofRow(
        "network.discovery.discover_experience_territory",
        "AwareNetworkSdk.network.discover_experience_territory",
        1,
        "green",
        "read-back of fixture environment/service territory candidates",
    ),
    LiveSdkEndpointProofRow(
        "network.discovery.discover_territory",
        "AwareNetworkSdk.network.discover_territory",
        1,
        "green",
        "read-back of fixture nodes, peer, environment, and hosted service",
    ),
    LiveSdkEndpointProofRow(
        "network.environment.list",
        "AwareNetworkSdk.network.list_environments",
        1,
        "green",
        "read-back of the published fixture Environment descriptor",
    ),
    LiveSdkEndpointProofRow(
        "network.hosted_service.list",
        "AwareNetworkSdk.network.list_hosted_services",
        1,
        "green",
        "read-back of the published fixture hosted service descriptor",
    ),
    LiveSdkEndpointProofRow(
        "network.publication.reconcile_node_publication",
        "AwareNetworkSdk.network.reconcile_node_publication",
        3,
        "green",
        "composite node, Environment, and hosted-Service publication",
    ),
    LiveSdkEndpointProofRow(
        "network.peer.list",
        "AwareNetworkSdk.network.list_peers",
        1,
        "green",
        "read-back of the fixture accepted peer edge",
    ),
    LiveSdkEndpointProofRow(
        "network.peer.upsert",
        "AwareNetworkSdk.network.upsert_peer",
        3,
        "green",
        "isolated fixture peer edge upsert with SDK read-back",
    ),
    LiveSdkEndpointProofRow(
        "network.route.resolve_hosted_service_routes",
        "AwareNetworkSdk.network.resolve_hosted_service_routes",
        1,
        "green",
        "route resolution from fixture consumer node to provider hosted service",
    ),
)


def test_network_endpoint_matrix_accounts_for_generated_sdk_surface() -> None:
    generated_endpoint_refs = set(ENDPOINT_REF_BY_NAME.values())
    matrix_endpoint_refs = {row.endpoint_ref for row in NETWORK_ENDPOINT_MATRIX}
    assert matrix_endpoint_refs == generated_endpoint_refs
    assert len(NETWORK_ENDPOINT_MATRIX) == 8
    assert {row.status for row in NETWORK_ENDPOINT_MATRIX} == {"green"}


def test_live_services_advertise_generated_network_endpoint_surface(
    live_sdk_api_dependency_routes,
) -> None:
    advertised_refs = endpoint_refs_for_api_package(
        live_sdk_api_dependency_routes,
        api_package_name=NETWORK_API_PACKAGE_NAME,
    )
    assert advertised_refs == set(ENDPOINT_REF_BY_NAME.values())


@pytest_asyncio.fixture()
async def network_sdk(
    live_sdk_api_dependency_routes,
    live_sdk_actor_id,
):
    api_invoker = build_live_api_client_for_package(
        live_sdk_api_dependency_routes,
        api_package_name=NETWORK_API_PACKAGE_NAME,
        actor_id=live_sdk_actor_id,
    )
    api_client = AwareNetworkServiceApiClient(api_invoker)
    try:
        yield NetworkLiveSdk(
            api=api_client,
            sdk=AwareNetworkSdk(api_client=api_client),
            actor_id=live_sdk_actor_id,
        )
    finally:
        await close_live_api_client(api_invoker)


@pytest.mark.asyncio
async def test_network_topology_round_trip_live_sdk(
    network_sdk: NetworkLiveSdk,
) -> None:
    environment_id = UUID(os.environ["AWARE_SDK_LIVE_ENVIRONMENT_ID"])
    consumer_node_id = _fixture_uuid("consumer-node")
    provider_node_id = _fixture_uuid("provider-node")
    service_package_id = _fixture_uuid("service-package")
    service_id = _fixture_uuid("service")
    consumer_publication = await network_sdk.sdk.network.reconcile_node_publication(
        intent=_intent(
            node_id=consumer_node_id,
            public_key=_fixture_public_key("consumer"),
            port=19631,
            environment_id=environment_id,
        ),
        actor_id=network_sdk.actor_id,
    )
    provider_publication = await network_sdk.sdk.network.reconcile_node_publication(
        intent=_intent(
            node_id=provider_node_id,
            public_key=_fixture_public_key("provider"),
            port=19632,
            environment_id=environment_id,
            service_package_id=service_package_id,
            service_id=service_id,
        ),
        actor_id=network_sdk.actor_id,
    )
    assert consumer_publication.node is not None
    assert provider_publication.node is not None
    consumer = consumer_publication.node
    provider = provider_publication.node

    peer = await network_sdk.sdk.network.upsert_peer(
        source_node_id=consumer.node_id,
        target_node_id=provider.node_id,
        target_base_url=provider.base_url or "ws://127.0.0.1:19632",
        actor_id=network_sdk.actor_id,
    )
    assert peer.source_node_id == consumer.node_id
    assert peer.target_node_id == provider.node_id

    environment = provider_publication.environment
    assert environment is not None
    assert environment.node_id == provider.node_id
    assert environment.environment_id == environment_id
    assert _FIXTURE_EXPERIENCE_NAME in environment.experience_names

    hosted_service = provider_publication.hosted_services[0]
    assert hosted_service.service_package_id == service_package_id
    assert hosted_service.service_id == service_id
    assert _FIXTURE_ENDPOINT_REF in hosted_service.endpoint_refs

    peers = await network_sdk.sdk.network.list_peers(
        node_id=consumer.node_id,
        actor_id=network_sdk.actor_id,
    )
    assert any(item.target_node_id == provider.node_id for item in peers)

    environments = await network_sdk.sdk.network.list_environments(
        node_id=provider.node_id,
        actor_id=network_sdk.actor_id,
    )
    assert any(item.environment_id == environment_id for item in environments)

    hosted_services = await network_sdk.sdk.network.list_hosted_services(
        node_id=provider.node_id,
        actor_id=network_sdk.actor_id,
    )
    assert any(
        item.service_package_id == service_package_id for item in hosted_services
    )

    routes = await network_sdk.sdk.network.resolve_hosted_service_routes(
        consumer_node_id=consumer.node_id,
        endpoint_ref=_FIXTURE_ENDPOINT_REF,
        actor_id=network_sdk.actor_id,
    )
    assert len(routes) == 1
    assert routes[0].provider_node_id == provider.node_id
    assert routes[0].hosted_service.service_package_id == service_package_id
    assert routes[0].route_connection_id == peer.edge_id

    territory = await network_sdk.sdk.network.discover_territory(
        node_id=provider.node_id,
        actor_id=network_sdk.actor_id,
        limit_nodes=10,
    )
    assert territory.success is True
    assert territory.nodes
    provider_territory = next(
        item for item in territory.nodes if item.node.node_id == provider.node_id
    )
    assert any(
        item.environment_id == environment_id
        for item in provider_territory.environments
    )
    assert any(
        item.service_package_id == service_package_id
        for item in provider_territory.hosted_services
    )

    experience = await network_sdk.sdk.network.discover_experience_territory(
        experience_name=_FIXTURE_EXPERIENCE_NAME,
        required_service_package_names=(_FIXTURE_SERVICE_PACKAGE_NAME,),
        required_endpoint_refs=(_FIXTURE_ENDPOINT_REF,),
        consumer_node_id=consumer.node_id,
        actor_id=network_sdk.actor_id,
        limit_entries=10,
    )
    assert experience.success is True
    assert experience.experience_name == _FIXTURE_EXPERIENCE_NAME
    matching_entry = next(
        entry
        for entry in experience.entries
        if entry.node.node_id == provider.node_id
        and entry.environment.environment_id == environment_id
    )
    assert matching_entry.route_status == "reachable"
    assert not matching_entry.missing_service_package_names
    assert not matching_entry.missing_endpoint_refs
    assert matching_entry.service_candidates
    assert (
        matching_entry.service_candidates[0].hosted_service.service_package_id
        == service_package_id
    )

    provider_input = await network_territory_discovery_v1_provider_input_from_client(
        client=network_sdk.sdk.network,
        node_id=provider.node_id,
        actor_id=network_sdk.actor_id,
        authority_source_url="live://network-service-api",
        limit_nodes=10,
        raise_errors=True,
    )
    view_state = network_territory_discovery_view_state(
        provider_input=provider_input,
    )
    assert view_state.status == "live"
    assert view_state.authority_source_url == "live://network-service-api"
    assert view_state.nodes
    assert view_state.nodes[0].node is not None
    assert view_state.nodes[0].node.node_id == str(provider.node_id)


def _fixture_uuid(label: str) -> UUID:
    return uuid5(_FIXTURE_NAMESPACE, label)


def _fixture_public_key(label: str) -> str:
    return f"network-sdk-live:{label}:v1"


def _intent(
    *,
    node_id: UUID,
    public_key: str,
    port: int,
    environment_id: UUID,
    service_package_id: UUID | None = None,
    service_id: UUID | None = None,
) -> NetworkNodePublicationIntent:
    services = []
    if service_package_id is not None and service_id is not None:
        services.append(
            NetworkNodePublicationHostedService(
                service_package_id=service_package_id,
                service_id=service_id,
                service_name="network-sdk-live",
                service_package_names=[_FIXTURE_SERVICE_PACKAGE_NAME],
                endpoint_refs=[_FIXTURE_ENDPOINT_REF],
                stream_endpoint_refs=[],
                host_id="network-sdk-live-host",
                protocol_version="1",
            )
        )
    return NetworkNodePublicationIntent(
        publication_digest=f"sha256:{node_id}:{environment_id}",
        node=NetworkNodePublicationNode(
            node_id=node_id,
            public_key=public_key,
            hostname="127.0.0.1",
            port=port,
            base_url=f"ws://127.0.0.1:{port}",
        ),
        environment=NetworkNodePublicationEnvironment(
            environment_id=environment_id,
            environment_key="network-sdk-live",
            environment_title="Network SDK Live",
            role="primary",
            experience_names=[_FIXTURE_EXPERIENCE_NAME],
        ),
        hosted_services=services,
    )
