from __future__ import annotations

from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverExperienceTerritoryRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverExperienceTerritoryResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverTerritoryRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkDiscoverTerritoryResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListEnvironmentsRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListEnvironmentsResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListHostedServicesRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListHostedServicesResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListPeersRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkListPeersResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkReconcileNodePublicationRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkReconcileNodePublicationResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkResolveHostedServiceRoutesRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkResolveHostedServiceRoutesResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkUpsertPeerRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkUpsertPeerResponse,
)
from aware_network_service_protocol.protocols import (
    AwareNetworkServiceProtocol,
    NetworkApiServiceProtocol,
    NetworkDiscoveryCapabilityServiceProtocol,
    NetworkEnvironmentCapabilityServiceProtocol,
    NetworkHostedServiceCapabilityServiceProtocol,
    NetworkPeerCapabilityServiceProtocol,
    NetworkPublicationCapabilityServiceProtocol,
    NetworkRouteCapabilityServiceProtocol,
)

from .ontology_authority import HostContextNetworkTopologyAuthority
from .topology_authority import NetworkTopologyAuthority


def build_aware_network_service_protocol_handler(
    *,
    authority: NetworkTopologyAuthority | None = None,
) -> AwareNetworkServiceProtocol:
    return _AwareNetworkServiceProtocolHandler(
        authority=authority or HostContextNetworkTopologyAuthority()
    )


class _NetworkPublicationCapabilityHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self._authority = authority

    async def reconcile_node_publication(
        self,
        request: NetworkReconcileNodePublicationRequest,
    ) -> NetworkReconcileNodePublicationResponse:
        return await self._authority.reconcile_node_publication(request)


class _NetworkPeerCapabilityHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self._authority = authority

    async def upsert(
        self,
        request: NetworkUpsertPeerRequest,
    ) -> NetworkUpsertPeerResponse:
        return await self._authority.upsert_peer(request)

    async def list(
        self,
        request: NetworkListPeersRequest,
    ) -> NetworkListPeersResponse:
        return await self._authority.list_peers(request)


class _NetworkEnvironmentCapabilityHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self._authority = authority

    async def list(
        self,
        request: NetworkListEnvironmentsRequest,
    ) -> NetworkListEnvironmentsResponse:
        return await self._authority.list_environments(request)


class _NetworkHostedServiceCapabilityHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self._authority = authority

    async def list(
        self,
        request: NetworkListHostedServicesRequest,
    ) -> NetworkListHostedServicesResponse:
        return await self._authority.list_hosted_services(request)


class _NetworkRouteCapabilityHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self._authority = authority

    async def resolve_hosted_service_routes(
        self,
        request: NetworkResolveHostedServiceRoutesRequest,
    ) -> NetworkResolveHostedServiceRoutesResponse:
        return await self._authority.resolve_hosted_service_routes(request)


class _NetworkDiscoveryCapabilityHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self._authority = authority

    async def discover_territory(
        self,
        request: NetworkDiscoverTerritoryRequest,
    ) -> NetworkDiscoverTerritoryResponse:
        return await self._authority.discover_territory(request)

    async def discover_experience_territory(
        self,
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> NetworkDiscoverExperienceTerritoryResponse:
        return await self._authority.discover_experience_territory(request)


class _NetworkApiServiceProtocolHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self.discovery: NetworkDiscoveryCapabilityServiceProtocol = (
            _NetworkDiscoveryCapabilityHandler(authority=authority)
        )
        self.environment: NetworkEnvironmentCapabilityServiceProtocol = (
            _NetworkEnvironmentCapabilityHandler(authority=authority)
        )
        self.publication: NetworkPublicationCapabilityServiceProtocol = (
            _NetworkPublicationCapabilityHandler(authority=authority)
        )
        self.peer: NetworkPeerCapabilityServiceProtocol = _NetworkPeerCapabilityHandler(
            authority=authority
        )
        self.hosted_service: NetworkHostedServiceCapabilityServiceProtocol = (
            _NetworkHostedServiceCapabilityHandler(authority=authority)
        )
        self.route: NetworkRouteCapabilityServiceProtocol = (
            _NetworkRouteCapabilityHandler(authority=authority)
        )


class _AwareNetworkServiceProtocolHandler:
    def __init__(self, *, authority: NetworkTopologyAuthority) -> None:
        self.network: NetworkApiServiceProtocol = _NetworkApiServiceProtocolHandler(
            authority=authority
        )


__all__ = [
    "build_aware_network_service_protocol_handler",
]
