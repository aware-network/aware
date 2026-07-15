# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF,
    NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF,
    NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF,
    NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF,
    NETWORK__PEER__LIST_ENDPOINT_REF,
    NETWORK__PEER__UPSERT_ENDPOINT_REF,
    NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF,
    NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverExperienceTerritoryRequest,
    NetworkDiscoverExperienceTerritoryResponse,
    NetworkDiscoverTerritoryRequest,
    NetworkDiscoverTerritoryResponse,
    NetworkListEnvironmentsRequest,
    NetworkListEnvironmentsResponse,
    NetworkListHostedServicesRequest,
    NetworkListHostedServicesResponse,
    NetworkListPeersRequest,
    NetworkListPeersResponse,
    NetworkReconcileNodePublicationRequest,
    NetworkReconcileNodePublicationResponse,
    NetworkResolveHostedServiceRoutesRequest,
    NetworkResolveHostedServiceRoutesResponse,
    NetworkUpsertPeerRequest,
    NetworkUpsertPeerResponse,
)


class NetworkDiscoveryCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def discover_experience_territory(
        self, request: NetworkDiscoverExperienceTerritoryRequest
    ) -> NetworkDiscoverExperienceTerritoryResponse:
        """Resolve an experience-first Network territory read model from environment and hosted-service advertisements."""
        return cast(
            NetworkDiscoverExperienceTerritoryResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__DISCOVERY__DISCOVER_EXPERIENCE_TERRITORY_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def discover_territory(self, request: NetworkDiscoverTerritoryRequest) -> NetworkDiscoverTerritoryResponse:
        """Resolve the Control territory read model: nodes, environments, hosted services, and peers."""
        return cast(
            NetworkDiscoverTerritoryResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__DISCOVERY__DISCOVER_TERRITORY_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class NetworkEnvironmentCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list(self, request: NetworkListEnvironmentsRequest) -> NetworkListEnvironmentsResponse:
        """List Environment advertisements known to Network Service topology truth."""
        return cast(
            NetworkListEnvironmentsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__ENVIRONMENT__LIST_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class NetworkHostedServiceCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list(self, request: NetworkListHostedServicesRequest) -> NetworkListHostedServicesResponse:
        """List hosted Service advertisements for one NetworkNode."""
        return cast(
            NetworkListHostedServicesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__HOSTED_SERVICE__LIST_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class NetworkPeerCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list(self, request: NetworkListPeersRequest) -> NetworkListPeersResponse:
        """List peer edges for one NetworkNode from Network Service topology truth."""
        return cast(
            NetworkListPeersResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__PEER__LIST_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def upsert(self, request: NetworkUpsertPeerRequest) -> NetworkUpsertPeerResponse:
        """Upsert one canonical NetworkNodePeer edge used for node-to-node routing."""
        return cast(
            NetworkUpsertPeerResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__PEER__UPSERT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class NetworkPublicationCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def reconcile_node_publication(
        self, request: NetworkReconcileNodePublicationRequest
    ) -> NetworkReconcileNodePublicationResponse:
        """Reconcile one complete Node runtime publication through canonical Network Service authority."""
        return cast(
            NetworkReconcileNodePublicationResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__PUBLICATION__RECONCILE_NODE_PUBLICATION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class NetworkRouteCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_hosted_service_routes(
        self, request: NetworkResolveHostedServiceRoutesRequest
    ) -> NetworkResolveHostedServiceRoutesResponse:
        """Resolve remote hosted-Service routes for a consumer NetworkNode."""
        return cast(
            NetworkResolveHostedServiceRoutesResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=NETWORK__ROUTE__RESOLVE_HOSTED_SERVICE_ROUTES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class NetworkApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.discovery = NetworkDiscoveryCapabilityClient(client)
        self.environment = NetworkEnvironmentCapabilityClient(client)
        self.hosted_service = NetworkHostedServiceCapabilityClient(client)
        self.peer = NetworkPeerCapabilityClient(client)
        self.publication = NetworkPublicationCapabilityClient(client)
        self.route = NetworkRouteCapabilityClient(client)


class AwareNetworkServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.network = NetworkApiClient(client)


__all__ = [
    "AwareNetworkServiceApiClient",
    "NetworkApiClient",
    "NetworkDiscoveryCapabilityClient",
    "NetworkEnvironmentCapabilityClient",
    "NetworkHostedServiceCapabilityClient",
    "NetworkPeerCapabilityClient",
    "NetworkPublicationCapabilityClient",
    "NetworkRouteCapabilityClient",
]
