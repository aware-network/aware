from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from aware_network_ontology.stable_ids import (
    stable_network_node_id,
    stable_network_node_peer_id,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkHostedServiceDescriptor,
)
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
    NetworkExperienceServiceCandidate,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkExperienceTerritoryEntry,
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
    NetworkNodeRouteDescriptor,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkNodePublicationCoverage,
)
from aware_network_service_dto.comms.models.network_service import NetworkPeerDescriptor
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishEnvironmentRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishEnvironmentResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishHostedServiceRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkPublishHostedServiceResponse,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkRegisterNodeRequest,
)
from aware_network_service_dto.comms.models.network_service import (
    NetworkRegisterNodeResponse,
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


class NetworkTopologyAuthority(Protocol):
    async def reconcile_node_publication(
        self,
        request: NetworkReconcileNodePublicationRequest,
    ) -> NetworkReconcileNodePublicationResponse: ...

    async def register_node(
        self,
        request: NetworkRegisterNodeRequest,
    ) -> NetworkRegisterNodeResponse: ...

    async def upsert_peer(
        self,
        request: NetworkUpsertPeerRequest,
    ) -> NetworkUpsertPeerResponse: ...

    async def list_peers(
        self,
        request: NetworkListPeersRequest,
    ) -> NetworkListPeersResponse: ...

    async def publish_hosted_service(
        self,
        request: NetworkPublishHostedServiceRequest,
    ) -> NetworkPublishHostedServiceResponse: ...

    async def list_hosted_services(
        self,
        request: NetworkListHostedServicesRequest,
    ) -> NetworkListHostedServicesResponse: ...

    async def publish_environment(
        self,
        request: NetworkPublishEnvironmentRequest,
    ) -> NetworkPublishEnvironmentResponse: ...

    async def list_environments(
        self,
        request: NetworkListEnvironmentsRequest,
    ) -> NetworkListEnvironmentsResponse: ...

    async def resolve_hosted_service_routes(
        self,
        request: NetworkResolveHostedServiceRoutesRequest,
    ) -> NetworkResolveHostedServiceRoutesResponse: ...

    async def discover_territory(
        self,
        request: NetworkDiscoverTerritoryRequest,
    ) -> NetworkDiscoverTerritoryResponse: ...

    async def discover_experience_territory(
        self,
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> NetworkDiscoverExperienceTerritoryResponse: ...


@dataclass(frozen=True, slots=True)
class _ExperienceRouteHint:
    route_status: str
    provider_node_base_url: str | None
    route_connection_id: UUID | None


@dataclass(slots=True)
class InMemoryNetworkTopologyAuthority:
    """Bootstrap authority used until the Network ontology-backed store lands.

    This class is intentionally behind `NetworkTopologyAuthority` so Node and
    future SDK consumers never depend on this storage shape.
    """

    nodes_by_id: dict[UUID, NetworkNodeRouteDescriptor] = field(default_factory=dict)
    peers_by_edge: dict[UUID, NetworkPeerDescriptor] = field(default_factory=dict)
    hosted_services_by_node: dict[
        UUID,
        dict[UUID, NetworkHostedServiceDescriptor],
    ] = field(default_factory=dict)
    environments_by_node: dict[
        UUID,
        dict[UUID, NetworkEnvironmentDescriptor],
    ] = field(default_factory=dict)

    async def reconcile_node_publication(
        self,
        request: NetworkReconcileNodePublicationRequest,
    ) -> NetworkReconcileNodePublicationResponse:
        intent = request.intent
        node_result = await self.register_node(
            NetworkRegisterNodeRequest(
                actor_id=request.actor_id,
                request_id=request.request_id,
                node_id=intent.node.node_id,
                public_key=intent.node.public_key,
                hostname=intent.node.hostname,
                port=intent.node.port,
                base_url=intent.node.base_url,
                status=intent.node.status,
            )
        )
        environment_result = await self.publish_environment(
            NetworkPublishEnvironmentRequest(
                actor_id=request.actor_id,
                request_id=request.request_id,
                node_id=intent.node.node_id,
                environment_id=intent.environment.environment_id,
                environment_key=intent.environment.environment_key,
                environment_title=intent.environment.environment_title,
                role=intent.environment.role,
                is_active=intent.environment.is_active,
                priority=intent.environment.priority,
                status=intent.environment.status,
                experience_names=intent.environment.experience_names,
                environment_config_id=intent.environment.environment_config_id,
                environment_config_key=intent.environment.environment_config_key,
            )
        )
        hosted_services: list[NetworkHostedServiceDescriptor] = []
        for service in intent.hosted_services:
            result = await self.publish_hosted_service(
                NetworkPublishHostedServiceRequest(
                    actor_id=request.actor_id,
                    request_id=request.request_id,
                    node_id=intent.node.node_id,
                    service_package_id=service.service_package_id,
                    service_id=service.service_id,
                    service_name=service.service_name,
                    service_package_names=service.service_package_names,
                    endpoint_refs=service.endpoint_refs,
                    stream_endpoint_refs=service.stream_endpoint_refs,
                    host_id=service.host_id,
                    host_version=service.host_version,
                    protocol_version=service.protocol_version,
                    supports_stream_events=service.supports_stream_events,
                )
            )
            if result.hosted_service is not None:
                hosted_services.append(result.hosted_service)

        requested_ids = {item.service_package_id for item in intent.hosted_services}
        committed_ids = {
            item.service_package_id
            for item in hosted_services
            if item.service_package_id is not None
        }
        coverage = NetworkNodePublicationCoverage(
            node_registered=node_result.node is not None,
            environment_published=environment_result.environment is not None,
            hosted_service_package_ids=sorted(committed_ids, key=str),
            missing_hosted_service_package_ids=sorted(
                requested_ids - committed_ids, key=str
            ),
            unexpected_hosted_service_package_ids=[],
        )
        converged = (
            coverage.node_registered
            and coverage.environment_published
            and not coverage.missing_hosted_service_package_ids
        )
        return NetworkReconcileNodePublicationResponse(
            request_id=request.request_id,
            success=converged,
            status="converged" if converged else "blocked",
            error=None if converged else "Network publication coverage is incomplete.",
            publication_digest=intent.publication_digest,
            node=node_result.node,
            environment=environment_result.environment,
            hosted_services=hosted_services,
            coverage=coverage,
            commit_receipts=[],
        )

    async def register_node(
        self,
        request: NetworkRegisterNodeRequest,
    ) -> NetworkRegisterNodeResponse:
        node_id = request.node_id or stable_network_node_id(
            public_key=request.public_key.strip()
        )
        node = NetworkNodeRouteDescriptor(
            node_id=node_id,
            public_key=request.public_key.strip(),
            hostname=request.hostname.strip(),
            port=request.port,
            base_url=_normalize_base_url(
                request.base_url,
                hostname=request.hostname,
                port=request.port,
            ),
            status=request.status.strip() or "active",
            last_seen_at=_utc_now(),
        )
        self.nodes_by_id[node_id] = node
        return NetworkRegisterNodeResponse(
            request_id=request.request_id,
            success=True,
            node=node,
        )

    async def upsert_peer(
        self,
        request: NetworkUpsertPeerRequest,
    ) -> NetworkUpsertPeerResponse:
        edge_id = stable_network_node_peer_id(
            source_peer_node_id=request.source_node_id,
            target_peer_node_id=request.target_node_id,
        )
        now = _utc_now()
        peer = NetworkPeerDescriptor(
            edge_id=edge_id,
            source_node_id=request.source_node_id,
            target_node_id=request.target_node_id,
            peer_node_id=request.target_node_id,
            peer_base_url=request.target_base_url.strip().rstrip("/"),
            direction="outgoing",
            status=request.status.strip() or "accepted",
            trust_score=request.trust_score,
            connected_at=now,
            last_ping_at=now,
        )
        self.peers_by_edge[edge_id] = peer
        return NetworkUpsertPeerResponse(
            request_id=request.request_id,
            success=True,
            peer=peer,
        )

    async def list_peers(
        self,
        request: NetworkListPeersRequest,
    ) -> NetworkListPeersResponse:
        limit = request.limit_results if request.limit_results is not None else 200
        if limit <= 0:
            return NetworkListPeersResponse(
                request_id=request.request_id,
                success=True,
                peers=[],
            )
        peers = tuple(
            _peer_for_node(peer=peer, node_id=request.node_id)
            for peer in self.peers_by_edge.values()
            if _peer_matches_request(peer=peer, request=request)
        )
        return NetworkListPeersResponse(
            request_id=request.request_id,
            success=True,
            peers=list(peers[:limit]),
        )

    async def publish_hosted_service(
        self,
        request: NetworkPublishHostedServiceRequest,
    ) -> NetworkPublishHostedServiceResponse:
        hosted_service = NetworkHostedServiceDescriptor(
            service_package_id=request.service_package_id,
            service_id=request.service_id,
            service_name=request.service_name.strip(),
            service_package_names=_clean_strings(request.service_package_names),
            endpoint_refs=_clean_strings(request.endpoint_refs),
            stream_endpoint_refs=_clean_strings(request.stream_endpoint_refs),
            host_id=request.host_id.strip(),
            host_version=request.host_version,
            protocol_version=request.protocol_version.strip(),
            supports_stream_events=request.supports_stream_events,
        )
        self.hosted_services_by_node.setdefault(request.node_id, {})[
            request.service_package_id or request.service_id
        ] = hosted_service
        return NetworkPublishHostedServiceResponse(
            request_id=request.request_id,
            success=True,
            hosted_service=hosted_service,
        )

    async def list_hosted_services(
        self,
        request: NetworkListHostedServicesRequest,
    ) -> NetworkListHostedServicesResponse:
        services = tuple(self.hosted_services_by_node.get(request.node_id, {}).values())
        return NetworkListHostedServicesResponse(
            request_id=request.request_id,
            success=True,
            hosted_services=list(
                sorted(services, key=lambda item: item.service_name.casefold())
            ),
        )

    async def publish_environment(
        self,
        request: NetworkPublishEnvironmentRequest,
    ) -> NetworkPublishEnvironmentResponse:
        environment = NetworkEnvironmentDescriptor(
            node_id=request.node_id,
            environment_id=request.environment_id,
            environment_key=_optional_clean_text(request.environment_key),
            environment_title=_optional_clean_text(request.environment_title),
            role=request.role.strip() or "replica",
            is_active=request.is_active,
            priority=request.priority,
            status=request.status.strip() or "active",
            experience_names=_clean_strings(request.experience_names),
            environment_config_id=request.environment_config_id,
            environment_config_key=_optional_clean_text(request.environment_config_key),
        )
        self.environments_by_node.setdefault(request.node_id, {})[
            request.environment_id
        ] = environment
        return NetworkPublishEnvironmentResponse(
            request_id=request.request_id,
            success=True,
            environment=environment,
        )

    async def list_environments(
        self,
        request: NetworkListEnvironmentsRequest,
    ) -> NetworkListEnvironmentsResponse:
        environments = self._environment_candidates(
            node_id=request.node_id,
            active_only=request.active_only,
        )
        return NetworkListEnvironmentsResponse(
            request_id=request.request_id,
            success=True,
            environments=list(environments),
        )

    async def resolve_hosted_service_routes(
        self,
        request: NetworkResolveHostedServiceRoutesRequest,
    ) -> NetworkResolveHostedServiceRoutesResponse:
        routes: list[NetworkResolvedHostedServiceRoute] = []
        for peer in self._route_candidate_peers(request):
            services = self.hosted_services_by_node.get(peer.target_node_id, {})
            for hosted_service in services.values():
                if not _hosted_service_matches(
                    hosted_service=hosted_service,
                    service_name=request.service_name,
                    endpoint_ref=request.endpoint_ref,
                ):
                    continue
                routes.append(
                    NetworkResolvedHostedServiceRoute(
                        provider_node_id=peer.target_node_id,
                        provider_node_base_url=peer.peer_base_url,
                        route_connection_id=peer.edge_id,
                        hosted_service=hosted_service,
                    )
                )
        return NetworkResolveHostedServiceRoutesResponse(
            request_id=request.request_id,
            success=True,
            routes=routes,
        )

    async def discover_territory(
        self,
        request: NetworkDiscoverTerritoryRequest,
    ) -> NetworkDiscoverTerritoryResponse:
        limit = request.limit_nodes if request.limit_nodes is not None else 200
        if limit <= 0:
            return NetworkDiscoverTerritoryResponse(
                request_id=request.request_id,
                success=True,
                nodes=[],
                summary="0 nodes, 0 environments, 0 hosted services",
            )
        nodes = self._territory_nodes(request)[:limit]
        territory_nodes: list[NetworkTerritoryNodeDescriptor] = []
        for node in nodes:
            peers: list[NetworkPeerDescriptor] = []
            if request.include_peers:
                peer_response = await self.list_peers(
                    NetworkListPeersRequest(
                        node_id=node.node_id,
                        include_incoming=True,
                        include_outgoing=True,
                        accepted_only=request.accepted_peers_only,
                        limit_results=None,
                    )
                )
                peers = peer_response.peers
            territory_nodes.append(
                NetworkTerritoryNodeDescriptor(
                    node=node,
                    environments=(
                        list(
                            self._environment_candidates(
                                node_id=node.node_id,
                                active_only=request.active_environments_only,
                            )
                        )
                        if request.include_environments
                        else []
                    ),
                    hosted_services=(
                        list(self._hosted_services_for_node(node_id=node.node_id))
                        if request.include_hosted_services
                        else []
                    ),
                    peers=peers,
                )
            )
        return NetworkDiscoverTerritoryResponse(
            request_id=request.request_id,
            success=True,
            nodes=territory_nodes,
            summary=_territory_summary(territory_nodes),
        )

    async def discover_experience_territory(
        self,
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> NetworkDiscoverExperienceTerritoryResponse:
        experience_name = request.experience_name.strip()
        if not experience_name:
            return NetworkDiscoverExperienceTerritoryResponse(
                request_id=request.request_id,
                success=False,
                error="experience_name is required.",
                experience_name=None,
                entries=[],
                summary="0 experience territory entries",
            )
        limit = request.limit_entries if request.limit_entries is not None else 200
        if limit <= 0:
            return NetworkDiscoverExperienceTerritoryResponse(
                request_id=request.request_id,
                success=True,
                experience_name=experience_name,
                entries=[],
                summary=f"0 experience territory entries for {experience_name!r}",
            )
        required_service_package_names = _clean_unique_strings(
            request.required_service_package_names
        )
        required_endpoint_refs = _clean_unique_strings(request.required_endpoint_refs)
        required_services = bool(
            required_service_package_names or required_endpoint_refs
        )
        entries: list[NetworkExperienceTerritoryEntry] = []
        territory_request = NetworkDiscoverTerritoryRequest(
            request_id=request.request_id,
            node_id=None,
            include_peers=False,
            include_hosted_services=False,
            include_environments=True,
            active_environments_only=request.active_environments_only,
            accepted_peers_only=request.accepted_peers_only,
            limit_nodes=None,
        )
        for node in self._territory_nodes(territory_request):
            if len(entries) >= limit:
                break
            environments = self._matching_experience_environments(
                node_id=node.node_id,
                active_only=request.active_environments_only,
                experience_name=experience_name,
            )
            if not environments:
                continue
            hosted_services = self._hosted_services_for_node(node_id=node.node_id)
            for environment in environments:
                if len(entries) >= limit:
                    break
                candidates = self._experience_service_candidates(
                    node=node,
                    hosted_services=hosted_services,
                    required_service_package_names=required_service_package_names,
                    required_endpoint_refs=required_endpoint_refs,
                    request=request,
                )
                missing_packages = _entry_missing_required_values(
                    required_values=required_service_package_names,
                    matched_values=(
                        matched
                        for candidate in candidates
                        for matched in candidate.matched_service_package_names
                    ),
                )
                missing_endpoints = _entry_missing_required_values(
                    required_values=required_endpoint_refs,
                    matched_values=(
                        matched
                        for candidate in candidates
                        for matched in candidate.matched_endpoint_refs
                    ),
                )
                route_status = _experience_entry_route_status(
                    route_hint=self._experience_route_hint(
                        provider_node_id=node.node_id,
                        request=request,
                    ),
                    required_services=required_services,
                    service_candidates=candidates,
                    missing_service_package_names=missing_packages,
                    missing_endpoint_refs=missing_endpoints,
                )
                entries.append(
                    NetworkExperienceTerritoryEntry(
                        experience_name=experience_name,
                        node=node,
                        environment=environment,
                        service_candidates=list(candidates),
                        route_status=route_status,
                        missing_service_package_names=missing_packages,
                        missing_endpoint_refs=missing_endpoints,
                    )
                )
        return NetworkDiscoverExperienceTerritoryResponse(
            request_id=request.request_id,
            success=True,
            experience_name=experience_name,
            entries=entries,
            summary=f"{len(entries)} experience territory entries for {experience_name!r}",
        )

    def _route_candidate_peers(
        self,
        request: NetworkResolveHostedServiceRoutesRequest,
    ) -> tuple[NetworkPeerDescriptor, ...]:
        candidates = []
        for peer in self.peers_by_edge.values():
            if peer.source_node_id != request.consumer_node_id:
                continue
            if request.accepted_peers_only and peer.status.casefold() != "accepted":
                continue
            candidates.append(peer)
        return tuple(candidates)

    def _experience_route_hint(
        self,
        *,
        provider_node_id: UUID,
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> _ExperienceRouteHint:
        provider_node = self.nodes_by_id.get(provider_node_id)
        provider_base_url = (
            provider_node.base_url if provider_node is not None else None
        )
        route_connection_id: UUID | None = None
        route_status = "reachable"
        if (
            request.consumer_node_id is not None
            and request.consumer_node_id != provider_node_id
        ):
            route_status = "peer_required"
            for peer in self.peers_by_edge.values():
                if peer.source_node_id != request.consumer_node_id:
                    continue
                if peer.target_node_id != provider_node_id:
                    continue
                if request.accepted_peers_only and peer.status.casefold() != "accepted":
                    continue
                route_status = "reachable"
                route_connection_id = peer.edge_id
                provider_base_url = peer.peer_base_url or provider_base_url
                break
        if (
            route_status == "reachable"
            and request.require_access_evidence
            and not _clean_strings(request.access_evidence_refs)
        ):
            route_status = "access_required"
        if not request.include_route_hints:
            provider_base_url = None
            route_connection_id = None
        return _ExperienceRouteHint(
            route_status=route_status,
            provider_node_base_url=provider_base_url,
            route_connection_id=route_connection_id,
        )

    def _experience_service_candidates(
        self,
        *,
        node: NetworkNodeRouteDescriptor,
        hosted_services: Iterable[NetworkHostedServiceDescriptor],
        required_service_package_names: tuple[str, ...],
        required_endpoint_refs: tuple[str, ...],
        request: NetworkDiscoverExperienceTerritoryRequest,
    ) -> tuple[NetworkExperienceServiceCandidate, ...]:
        required_services = bool(
            required_service_package_names or required_endpoint_refs
        )
        route_hint = self._experience_route_hint(
            provider_node_id=node.node_id,
            request=request,
        )
        candidates: list[NetworkExperienceServiceCandidate] = []
        for hosted_service in hosted_services:
            matched_package_names = _matched_required_values(
                required_values=required_service_package_names,
                available_values=hosted_service.service_package_names,
            )
            matched_endpoint_refs = _matched_required_values(
                required_values=required_endpoint_refs,
                available_values=(
                    *hosted_service.endpoint_refs,
                    *hosted_service.stream_endpoint_refs,
                ),
            )
            if required_services and not (
                matched_package_names or matched_endpoint_refs
            ):
                continue
            candidates.append(
                NetworkExperienceServiceCandidate(
                    hosted_service=hosted_service,
                    provider_node_id=node.node_id,
                    provider_node_base_url=route_hint.provider_node_base_url,
                    route_connection_id=route_hint.route_connection_id,
                    route_status=route_hint.route_status,
                    matched_service_package_names=list(matched_package_names),
                    matched_endpoint_refs=list(matched_endpoint_refs),
                    missing_service_package_names=_entry_missing_required_values(
                        required_values=required_service_package_names,
                        matched_values=matched_package_names,
                    ),
                    missing_endpoint_refs=_entry_missing_required_values(
                        required_values=required_endpoint_refs,
                        matched_values=matched_endpoint_refs,
                    ),
                )
            )
        return tuple(candidates)

    def _territory_nodes(
        self,
        request: NetworkDiscoverTerritoryRequest,
    ) -> tuple[NetworkNodeRouteDescriptor, ...]:
        nodes = self.nodes_by_id.values()
        if request.node_id is not None:
            nodes = [node for node in nodes if node.node_id == request.node_id]
        return tuple(
            sorted(
                nodes,
                key=lambda item: (
                    item.hostname.casefold(),
                    item.port,
                    str(item.node_id),
                ),
            )
        )

    def _hosted_services_for_node(
        self,
        *,
        node_id: UUID,
    ) -> tuple[NetworkHostedServiceDescriptor, ...]:
        services = tuple(self.hosted_services_by_node.get(node_id, {}).values())
        return tuple(sorted(services, key=lambda item: item.service_name.casefold()))

    def _matching_experience_environments(
        self,
        *,
        node_id: UUID,
        active_only: bool,
        experience_name: str,
    ) -> tuple[NetworkEnvironmentDescriptor, ...]:
        return tuple(
            environment
            for environment in self._environment_candidates(
                node_id=node_id,
                active_only=active_only,
            )
            if _experience_matches(
                environment=environment,
                experience_name=experience_name,
            )
        )

    def _environment_candidates(
        self,
        *,
        node_id: UUID | None,
        active_only: bool,
    ) -> tuple[NetworkEnvironmentDescriptor, ...]:
        if node_id is not None:
            environments = self.environments_by_node.get(node_id, {}).values()
        else:
            environments = (
                environment
                for by_environment_id in self.environments_by_node.values()
                for environment in by_environment_id.values()
            )
        return tuple(
            sorted(
                (
                    environment
                    for environment in environments
                    if not active_only
                    or (
                        environment.is_active
                        and environment.status.casefold() != "inactive"
                    )
                ),
                key=lambda item: (
                    -item.priority,
                    (item.environment_title or "").casefold(),
                    (item.environment_key or "").casefold(),
                    str(item.environment_id),
                ),
            )
        )


def _peer_matches_request(
    *,
    peer: NetworkPeerDescriptor,
    request: NetworkListPeersRequest,
) -> bool:
    if request.accepted_only and peer.status.casefold() != "accepted":
        return False
    outgoing = peer.source_node_id == request.node_id
    incoming = peer.target_node_id == request.node_id
    return (outgoing and request.include_outgoing) or (
        incoming and request.include_incoming
    )


def _peer_for_node(
    *,
    peer: NetworkPeerDescriptor,
    node_id: UUID,
) -> NetworkPeerDescriptor:
    if peer.source_node_id == node_id:
        return peer.model_copy(
            update={
                "direction": "outgoing",
                "peer_node_id": peer.target_node_id,
            }
        )
    return peer.model_copy(
        update={
            "direction": "incoming",
            "peer_node_id": peer.source_node_id,
        }
    )


def _hosted_service_matches(
    *,
    hosted_service: NetworkHostedServiceDescriptor,
    service_name: str | None,
    endpoint_ref: str | None,
) -> bool:
    normalized_service_name = (service_name or "").strip().casefold()
    if normalized_service_name:
        return hosted_service.service_name.strip().casefold() == normalized_service_name
    normalized_endpoint_ref = (endpoint_ref or "").strip().casefold()
    if normalized_endpoint_ref:
        endpoint_refs = {
            endpoint.strip().casefold()
            for endpoint in (
                *hosted_service.endpoint_refs,
                *hosted_service.stream_endpoint_refs,
            )
            if endpoint.strip()
        }
        return normalized_endpoint_ref in endpoint_refs
    return True


def _experience_matches(
    *,
    environment: NetworkEnvironmentDescriptor,
    experience_name: str,
) -> bool:
    normalized_experience_name = experience_name.strip().casefold()
    return normalized_experience_name in {
        candidate.strip().casefold()
        for candidate in environment.experience_names
        if candidate.strip()
    }


def _matched_required_values(
    *,
    required_values: Iterable[str],
    available_values: Iterable[str],
) -> tuple[str, ...]:
    available_lookup = {
        value.strip().casefold() for value in available_values if value.strip()
    }
    return tuple(
        required
        for required in required_values
        if required.strip().casefold() in available_lookup
    )


def _entry_missing_required_values(
    *,
    required_values: Iterable[str],
    matched_values: Iterable[str],
) -> list[str]:
    matched_lookup = {value.strip().casefold() for value in matched_values}
    return [
        required
        for required in required_values
        if required.strip().casefold() not in matched_lookup
    ]


def _experience_entry_route_status(
    *,
    route_hint: _ExperienceRouteHint,
    required_services: bool,
    service_candidates: Iterable[NetworkExperienceServiceCandidate],
    missing_service_package_names: Iterable[str],
    missing_endpoint_refs: Iterable[str],
) -> str:
    candidates = tuple(service_candidates)
    if required_services and (
        not candidates
        or tuple(missing_service_package_names)
        or tuple(missing_endpoint_refs)
    ):
        return "unavailable"
    if not candidates:
        return route_hint.route_status
    route_statuses = {candidate.route_status for candidate in candidates}
    if "access_required" in route_statuses:
        return "access_required"
    if "reachable" in route_statuses:
        return "reachable"
    if "peer_required" in route_statuses:
        return "peer_required"
    return "unavailable"


def _normalize_base_url(
    base_url: str | None,
    *,
    hostname: str,
    port: int,
) -> str:
    normalized = (base_url or "").strip().rstrip("/")
    if normalized:
        return normalized
    return f"http://{hostname.strip()}:{port}"


def _clean_strings(values: Iterable[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def _clean_unique_strings(values: Iterable[str]) -> tuple[str, ...]:
    cleaned_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        normalized = cleaned.casefold()
        if normalized in seen_values:
            continue
        seen_values.add(normalized)
        cleaned_values.append(cleaned)
    return tuple(cleaned_values)


def _optional_clean_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _territory_summary(nodes: Iterable[NetworkTerritoryNodeDescriptor]) -> str:
    node_list = tuple(nodes)
    environment_count = sum(len(node.environments) for node in node_list)
    hosted_service_count = sum(len(node.hosted_services) for node in node_list)
    return (
        f"{len(node_list)} nodes, "
        f"{environment_count} environments, "
        f"{hosted_service_count} hosted services"
    )


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat()


__all__ = [
    "InMemoryNetworkTopologyAuthority",
    "NetworkTopologyAuthority",
]
