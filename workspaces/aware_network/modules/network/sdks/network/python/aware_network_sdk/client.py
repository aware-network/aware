from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

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
    NetworkEnvironmentDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkExperienceTerritoryEntry,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkHostedServiceDescriptor,
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
from aware_network_service_dto.comms.models.network_service import NetworkPeerDescriptor
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodePublicationIntent,
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
    NetworkResolvedHostedServiceRoute,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkTerritoryNodeDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkUpsertPeerRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkUpsertPeerResponse,
)


class _NetworkPublicationCapabilityClient(Protocol):
    async def reconcile_node_publication(
        self,
        request: NetworkReconcileNodePublicationRequest,
    ) -> NetworkReconcileNodePublicationResponse: ...


class _NetworkDiscoveryCapabilityClient(Protocol):
    async def discover_experience_territory(
        self,
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> NetworkDiscoverExperienceTerritoryResponse: ...

    async def discover_territory(
        self,
        request: NetworkDiscoverTerritoryRequest,
    ) -> NetworkDiscoverTerritoryResponse: ...


class _NetworkEnvironmentCapabilityClient(Protocol):
    async def list(
        self,
        request: NetworkListEnvironmentsRequest,
    ) -> NetworkListEnvironmentsResponse: ...


class _NetworkPeerCapabilityClient(Protocol):
    async def list(
        self,
        request: NetworkListPeersRequest,
    ) -> NetworkListPeersResponse: ...

    async def upsert(
        self,
        request: NetworkUpsertPeerRequest,
    ) -> NetworkUpsertPeerResponse: ...


class _NetworkHostedServiceCapabilityClient(Protocol):
    async def list(
        self,
        request: NetworkListHostedServicesRequest,
    ) -> NetworkListHostedServicesResponse: ...


class _NetworkRouteCapabilityClient(Protocol):
    async def resolve_hosted_service_routes(
        self,
        request: NetworkResolveHostedServiceRoutesRequest,
    ) -> NetworkResolveHostedServiceRoutesResponse: ...


class _NetworkApiNamespaceClient(Protocol):
    @property
    def discovery(self) -> _NetworkDiscoveryCapabilityClient: ...

    @property
    def environment(self) -> _NetworkEnvironmentCapabilityClient: ...

    @property
    def peer(self) -> _NetworkPeerCapabilityClient: ...

    @property
    def hosted_service(self) -> _NetworkHostedServiceCapabilityClient: ...

    @property
    def publication(self) -> _NetworkPublicationCapabilityClient: ...

    @property
    def route(self) -> _NetworkRouteCapabilityClient: ...


class NetworkGeneratedApiClient(Protocol):
    @property
    def network(self) -> _NetworkApiNamespaceClient: ...


class NetworkSdkError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class NetworkRouteQuery:
    consumer_node_id: UUID
    service_name: str | None = None
    endpoint_ref: str | None = None
    accepted_peers_only: bool = True


@dataclass(frozen=True, slots=True)
class NetworkTerritoryQuery:
    node_id: UUID | None = None
    include_peers: bool = True
    include_hosted_services: bool = True
    include_environments: bool = True
    active_environments_only: bool = True
    accepted_peers_only: bool = True
    limit_nodes: int | None = 200


@dataclass(frozen=True, slots=True)
class NetworkExperienceTerritoryQuery:
    experience_name: str
    required_service_package_names: tuple[str, ...] = ()
    required_endpoint_refs: tuple[str, ...] = ()
    consumer_node_id: UUID | None = None
    active_environments_only: bool = True
    accepted_peers_only: bool = True
    include_route_hints: bool = True
    require_access_evidence: bool = False
    access_evidence_refs: tuple[str, ...] = ()
    limit_entries: int | None = 200


@dataclass(slots=True)
class NetworkSdkCache:
    peers_by_node: dict[UUID, tuple[NetworkPeerDescriptor, ...]] = field(
        default_factory=dict
    )
    environments_by_node: dict[
        UUID,
        tuple[NetworkEnvironmentDescriptor, ...],
    ] = field(default_factory=dict)
    hosted_services_by_node: dict[
        UUID,
        tuple[NetworkHostedServiceDescriptor, ...],
    ] = field(default_factory=dict)
    routes_by_query: dict[
        NetworkRouteQuery,
        tuple[NetworkResolvedHostedServiceRoute, ...],
    ] = field(default_factory=dict)
    territory_by_query: dict[
        NetworkTerritoryQuery,
        tuple[NetworkTerritoryNodeDescriptor, ...],
    ] = field(default_factory=dict)
    experience_territory_by_query: dict[
        NetworkExperienceTerritoryQuery,
        tuple[NetworkExperienceTerritoryEntry, ...],
    ] = field(default_factory=dict)

    def record_peers(
        self,
        *,
        node_id: UUID,
        peers: tuple[NetworkPeerDescriptor, ...],
    ) -> None:
        self.peers_by_node[node_id] = peers

    def record_hosted_services(
        self,
        *,
        node_id: UUID,
        hosted_services: tuple[NetworkHostedServiceDescriptor, ...],
    ) -> None:
        self.hosted_services_by_node[node_id] = hosted_services

    def record_environments(
        self,
        *,
        node_id: UUID,
        environments: tuple[NetworkEnvironmentDescriptor, ...],
    ) -> None:
        self.environments_by_node[node_id] = environments

    def record_routes(
        self,
        *,
        query: NetworkRouteQuery,
        routes: tuple[NetworkResolvedHostedServiceRoute, ...],
    ) -> None:
        self.routes_by_query[query] = routes

    def record_territory(
        self,
        *,
        query: NetworkTerritoryQuery,
        nodes: tuple[NetworkTerritoryNodeDescriptor, ...],
    ) -> None:
        self.territory_by_query[query] = nodes

    def record_experience_territory(
        self,
        *,
        query: NetworkExperienceTerritoryQuery,
        entries: tuple[NetworkExperienceTerritoryEntry, ...],
    ) -> None:
        self.experience_territory_by_query[query] = entries


@dataclass(slots=True)
class NetworkSdkClient:
    api_client: NetworkGeneratedApiClient
    cache: NetworkSdkCache | None = None

    async def reconcile_node_publication(
        self,
        *,
        intent: NetworkNodePublicationIntent,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> NetworkReconcileNodePublicationResponse:
        response = await self.api_client.network.publication.reconcile_node_publication(
            NetworkReconcileNodePublicationRequest(
                actor_id=actor_id,
                request_id=request_id,
                intent=intent,
            )
        )
        _raise_if_failed(response, operation="reconcile_node_publication")
        if response.status not in {"converged", "progressed"}:
            raise NetworkSdkError(
                "Network SDK reconciliation returned an invalid publication status."
            )
        return response

    async def upsert_peer(
        self,
        *,
        source_node_id: UUID,
        target_node_id: UUID,
        target_base_url: str,
        status: str = "accepted",
        trust_score: float = 0.0,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> NetworkPeerDescriptor:
        response = await self.api_client.network.peer.upsert(
            NetworkUpsertPeerRequest(
                actor_id=actor_id,
                request_id=request_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                target_base_url=target_base_url,
                status=status,
                trust_score=trust_score,
            )
        )
        _raise_if_failed(response, operation="upsert_peer")
        if response.peer is None:
            raise NetworkSdkError("Network SDK upsert_peer returned no peer.")
        return response.peer

    async def list_peers(
        self,
        *,
        node_id: UUID,
        include_incoming: bool = True,
        include_outgoing: bool = True,
        accepted_only: bool = True,
        limit_results: int | None = 200,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> tuple[NetworkPeerDescriptor, ...]:
        response = await self.api_client.network.peer.list(
            NetworkListPeersRequest(
                actor_id=actor_id,
                request_id=request_id,
                node_id=node_id,
                include_incoming=include_incoming,
                include_outgoing=include_outgoing,
                accepted_only=accepted_only,
                limit_results=limit_results,
            )
        )
        _raise_if_failed(response, operation="list_peers")
        peers = tuple(response.peers)
        if self.cache is not None:
            self.cache.record_peers(node_id=node_id, peers=peers)
        return peers

    async def list_hosted_services(
        self,
        *,
        node_id: UUID,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> tuple[NetworkHostedServiceDescriptor, ...]:
        response = await self.api_client.network.hosted_service.list(
            NetworkListHostedServicesRequest(
                actor_id=actor_id,
                request_id=request_id,
                node_id=node_id,
            )
        )
        _raise_if_failed(response, operation="list_hosted_services")
        hosted_services = tuple(response.hosted_services)
        if self.cache is not None:
            self.cache.record_hosted_services(
                node_id=node_id,
                hosted_services=hosted_services,
            )
        return hosted_services

    async def list_environments(
        self,
        *,
        node_id: UUID | None = None,
        active_only: bool = True,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> tuple[NetworkEnvironmentDescriptor, ...]:
        response = await self.api_client.network.environment.list(
            NetworkListEnvironmentsRequest(
                actor_id=actor_id,
                request_id=request_id,
                node_id=node_id,
                active_only=active_only,
            )
        )
        _raise_if_failed(response, operation="list_environments")
        environments = tuple(response.environments)
        if self.cache is not None:
            for cache_node_id in {
                environment.node_id
                for environment in environments
                if environment.node_id is not None
            }:
                self.cache.record_environments(
                    node_id=cache_node_id,
                    environments=tuple(
                        environment
                        for environment in environments
                        if environment.node_id == cache_node_id
                    ),
                )
        return environments

    async def discover_territory(
        self,
        *,
        node_id: UUID | None = None,
        include_peers: bool = True,
        include_hosted_services: bool = True,
        include_environments: bool = True,
        active_environments_only: bool = True,
        accepted_peers_only: bool = True,
        limit_nodes: int | None = 200,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> NetworkDiscoverTerritoryResponse:
        query = NetworkTerritoryQuery(
            node_id=node_id,
            include_peers=include_peers,
            include_hosted_services=include_hosted_services,
            include_environments=include_environments,
            active_environments_only=active_environments_only,
            accepted_peers_only=accepted_peers_only,
            limit_nodes=limit_nodes,
        )
        response = await self.api_client.network.discovery.discover_territory(
            NetworkDiscoverTerritoryRequest(
                actor_id=actor_id,
                request_id=request_id,
                node_id=node_id,
                include_peers=include_peers,
                include_hosted_services=include_hosted_services,
                include_environments=include_environments,
                active_environments_only=active_environments_only,
                accepted_peers_only=accepted_peers_only,
                limit_nodes=limit_nodes,
            )
        )
        _raise_if_failed(response, operation="discover_territory")
        if self.cache is not None:
            self.cache.record_territory(
                query=query,
                nodes=tuple(response.nodes),
            )
        return response

    async def discover_experience_territory(
        self,
        *,
        experience_name: str,
        required_service_package_names: tuple[str, ...] = (),
        required_endpoint_refs: tuple[str, ...] = (),
        consumer_node_id: UUID | None = None,
        active_environments_only: bool = True,
        accepted_peers_only: bool = True,
        include_route_hints: bool = True,
        require_access_evidence: bool = False,
        access_evidence_refs: tuple[str, ...] = (),
        limit_entries: int | None = 200,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> NetworkDiscoverExperienceTerritoryResponse:
        query = NetworkExperienceTerritoryQuery(
            experience_name=experience_name,
            required_service_package_names=required_service_package_names,
            required_endpoint_refs=required_endpoint_refs,
            consumer_node_id=consumer_node_id,
            active_environments_only=active_environments_only,
            accepted_peers_only=accepted_peers_only,
            include_route_hints=include_route_hints,
            require_access_evidence=require_access_evidence,
            access_evidence_refs=access_evidence_refs,
            limit_entries=limit_entries,
        )
        response = (
            await self.api_client.network.discovery.discover_experience_territory(
                NetworkDiscoverExperienceTerritoryRequest(
                    actor_id=actor_id,
                    request_id=request_id,
                    experience_name=experience_name,
                    required_service_package_names=list(required_service_package_names),
                    required_endpoint_refs=list(required_endpoint_refs),
                    consumer_node_id=consumer_node_id,
                    active_environments_only=active_environments_only,
                    accepted_peers_only=accepted_peers_only,
                    include_route_hints=include_route_hints,
                    require_access_evidence=require_access_evidence,
                    access_evidence_refs=list(access_evidence_refs),
                    limit_entries=limit_entries,
                )
            )
        )
        _raise_if_failed(response, operation="discover_experience_territory")
        if self.cache is not None:
            self.cache.record_experience_territory(
                query=query,
                entries=tuple(response.entries),
            )
        return response

    async def resolve_hosted_service_routes(
        self,
        *,
        consumer_node_id: UUID,
        service_name: str | None = None,
        endpoint_ref: str | None = None,
        accepted_peers_only: bool = True,
        actor_id: UUID | None = None,
        request_id: UUID | None = None,
    ) -> tuple[NetworkResolvedHostedServiceRoute, ...]:
        query = NetworkRouteQuery(
            consumer_node_id=consumer_node_id,
            service_name=service_name,
            endpoint_ref=endpoint_ref,
            accepted_peers_only=accepted_peers_only,
        )
        response = await self.api_client.network.route.resolve_hosted_service_routes(
            NetworkResolveHostedServiceRoutesRequest(
                actor_id=actor_id,
                request_id=request_id,
                consumer_node_id=consumer_node_id,
                service_name=service_name,
                endpoint_ref=endpoint_ref,
                accepted_peers_only=accepted_peers_only,
            )
        )
        _raise_if_failed(response, operation="resolve_hosted_service_routes")
        routes = tuple(response.routes)
        if self.cache is not None:
            self.cache.record_routes(query=query, routes=routes)
        return routes


class AwareNetworkSdk:
    def __init__(
        self,
        api_client: NetworkGeneratedApiClient,
        *,
        cache: NetworkSdkCache | None = None,
    ) -> None:
        self.api_client = api_client
        self.network = NetworkSdkClient(api_client=api_client, cache=cache)


def _raise_if_failed(response: object, *, operation: str) -> None:
    success = bool(getattr(response, "success", False))
    if success:
        return
    error = getattr(response, "error", None) or "unknown error"
    raise NetworkSdkError(f"Network SDK {operation} failed: {error}")


__all__ = [
    "AwareNetworkSdk",
    "NetworkExperienceTerritoryQuery",
    "NetworkGeneratedApiClient",
    "NetworkRouteQuery",
    "NetworkSdkCache",
    "NetworkSdkClient",
    "NetworkSdkError",
    "NetworkTerritoryQuery",
]
