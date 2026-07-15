from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class NetworkNodeRouteDescriptor(BaseModel):
    """
    Public Network Service DTOs for topology, hosted-service discovery, and route resolution.
    These are graph/ORM agnostic API contracts. The Network Service implementation may
    back them with local cache during bootstrap, but durable truth belongs to committed
    Network ontology objects (`NetworkNode`, `NetworkNodePeer`, `NetworkNodeService`).
    """

    # Attributes
    node_id: UUID
    public_key: str | None = Field(default=None)
    hostname: str
    port: int
    base_url: str | None = Field(default=None)
    status: str = Field(default="active")
    last_seen_at: str | None = Field(default=None)


class NetworkPeerFanoutRuleDescriptor(BaseModel):
    # Attributes
    id: UUID | None = Field(default=None)
    lane_branch_id: UUID
    lane_projection_hash: str
    enabled: bool = Field(default=True)
    mode: str = Field(default="notify_pull")


class NetworkPeerDescriptor(BaseModel):
    # Attributes
    edge_id: UUID | None = Field(default=None)
    source_node_id: UUID
    target_node_id: UUID
    peer_node_id: UUID
    peer_base_url: str
    direction: str = Field(default="outgoing")
    status: str = Field(default="accepted")
    trust_score: float = Field(default=0.0)
    fanout_rules: list[NetworkPeerFanoutRuleDescriptor] = Field(default_factory=list)
    connected_at: str | None = Field(default=None)
    last_ping_at: str | None = Field(default=None)


class NetworkHostedServiceDescriptor(BaseModel):
    # Attributes
    service_package_id: UUID | None = Field(default=None)
    service_id: UUID
    service_name: str
    service_package_names: list[str] = Field(default_factory=list)
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    supports_stream_events: bool = Field(default=False)


class NetworkEnvironmentDescriptor(BaseModel):
    # Attributes
    node_id: UUID | None = Field(default=None)
    environment_id: UUID
    environment_key: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    role: str = Field(default="replica")
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)
    status: str = Field(default="active")
    experience_names: list[str] = Field(default_factory=list)
    environment_config_id: UUID | None = Field(default=None)
    environment_config_key: str | None = Field(default=None)


class NetworkResolvedHostedServiceRoute(BaseModel):
    # Attributes
    provider_node_id: UUID
    provider_node_base_url: str
    route_connection_id: UUID | None = Field(default=None)
    hosted_service: NetworkHostedServiceDescriptor


class NetworkTerritoryNodeDescriptor(BaseModel):
    # Attributes
    node: NetworkNodeRouteDescriptor
    environments: list[NetworkEnvironmentDescriptor] = Field(default_factory=list)
    hosted_services: list[NetworkHostedServiceDescriptor] = Field(default_factory=list)
    peers: list[NetworkPeerDescriptor] = Field(default_factory=list)


class NetworkExperienceServiceCandidate(BaseModel):
    # Attributes
    hosted_service: NetworkHostedServiceDescriptor
    provider_node_id: UUID
    provider_node_base_url: str | None = Field(default=None)
    route_connection_id: UUID | None = Field(default=None)
    route_status: str = Field(default="reachable")
    matched_service_package_names: list[str] = Field(default_factory=list)
    matched_endpoint_refs: list[str] = Field(default_factory=list)
    missing_service_package_names: list[str] = Field(default_factory=list)
    missing_endpoint_refs: list[str] = Field(default_factory=list)


class NetworkExperienceTerritoryEntry(BaseModel):
    # Attributes
    experience_name: str
    node: NetworkNodeRouteDescriptor
    environment: NetworkEnvironmentDescriptor
    service_candidates: list[NetworkExperienceServiceCandidate] = Field(default_factory=list)
    route_status: str = Field(default="unavailable")
    missing_service_package_names: list[str] = Field(default_factory=list)
    missing_endpoint_refs: list[str] = Field(default_factory=list)


class NetworkNodePublicationNode(BaseModel):
    """
    Non-authoritative Node runtime observation submitted for Network
    reconciliation.
    """

    # Attributes
    node_id: UUID
    public_key: str
    hostname: str
    port: int
    base_url: str | None = Field(default=None)
    status: str = Field(default="active")


class NetworkNodePublicationEnvironment(BaseModel):
    """One Environment association requested by a Node publication intent."""

    # Attributes
    environment_id: UUID
    environment_key: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    role: str = Field(default="replica")
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)
    status: str = Field(default="active")
    experience_names: list[str] = Field(default_factory=list)
    environment_config_id: UUID | None = Field(default=None)
    environment_config_key: str | None = Field(default=None)


class NetworkNodePublicationHostedService(BaseModel):
    """One complete hosted-Service observation in a Node publication intent."""

    # Attributes
    service_package_id: UUID
    service_id: UUID
    service_name: str
    service_package_names: list[str] = Field(default_factory=list)
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    supports_stream_events: bool = Field(default=False)


class NetworkNodePublicationIntent(BaseModel):
    """
    Desired runtime publication submitted by a Node through Network SDK.
    This value is evidence, not Network discovery truth. Network Service owns
    validation, committed-state comparison, mutation, and coverage verification.
    """

    # Attributes
    publication_digest: str
    node: NetworkNodePublicationNode
    environment: NetworkNodePublicationEnvironment
    hosted_services: list[NetworkNodePublicationHostedService] = Field(default_factory=list)
    source_workspace_revision_id: UUID | None = Field(default=None)
    source_node_config_id: UUID | None = Field(default=None)


class NetworkNodePublicationCommitReceipt(BaseModel):
    """One commit produced while Network Service reconciles publication intent."""

    # Attributes
    operation: str
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    root_object_id: UUID | None = Field(default=None)


class NetworkNodePublicationCoverage(BaseModel):
    """Committed coverage observed after Network Service reconciliation."""

    # Attributes
    node_registered: bool = Field(default=False)
    environment_published: bool = Field(default=False)
    hosted_service_package_ids: list[UUID] = Field(default_factory=list)
    missing_hosted_service_package_ids: list[UUID] = Field(default_factory=list)
    unexpected_hosted_service_package_ids: list[UUID] = Field(default_factory=list)


class NetworkReconcileNodePublicationRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    intent: NetworkNodePublicationIntent


class NetworkReconcileNodePublicationResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    status: str = Field(default="converged")
    error: str | None = Field(default=None)
    publication_digest: str | None = Field(default=None)
    node: NetworkNodeRouteDescriptor | None = Field(default=None)
    environment: NetworkEnvironmentDescriptor | None = Field(default=None)
    hosted_services: list[NetworkHostedServiceDescriptor] = Field(default_factory=list)
    coverage: NetworkNodePublicationCoverage | None = Field(default=None)
    commit_receipts: list[NetworkNodePublicationCommitReceipt] = Field(default_factory=list)


class NetworkRegisterNodeRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    node_id: UUID | None = Field(default=None)
    public_key: str
    hostname: str
    port: int
    base_url: str | None = Field(default=None)
    status: str = Field(default="active")


class NetworkRegisterNodeResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    node: NetworkNodeRouteDescriptor | None = Field(default=None)


class NetworkUpsertPeerRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    source_node_id: UUID
    target_node_id: UUID
    target_base_url: str
    status: str = Field(default="accepted")
    trust_score: float = Field(default=0.0)


class NetworkUpsertPeerResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    peer: NetworkPeerDescriptor | None = Field(default=None)


class NetworkListPeersRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    node_id: UUID
    include_incoming: bool = Field(default=True)
    include_outgoing: bool = Field(default=True)
    accepted_only: bool = Field(default=True)
    limit_results: int | None = Field(default=200)


class NetworkListPeersResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    peers: list[NetworkPeerDescriptor] = Field(default_factory=list)


class NetworkPublishHostedServiceRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    node_id: UUID
    service_package_id: UUID | None = Field(default=None)
    service_id: UUID
    service_name: str
    service_package_names: list[str] = Field(default_factory=list)
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    supports_stream_events: bool = Field(default=False)


class NetworkPublishHostedServiceResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    hosted_service: NetworkHostedServiceDescriptor | None = Field(default=None)


class NetworkListHostedServicesRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    node_id: UUID


class NetworkListHostedServicesResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    hosted_services: list[NetworkHostedServiceDescriptor] = Field(default_factory=list)


class NetworkPublishEnvironmentRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    node_id: UUID
    environment_id: UUID
    environment_key: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    role: str = Field(default="replica")
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)
    status: str = Field(default="active")
    experience_names: list[str] = Field(default_factory=list)
    environment_config_id: UUID | None = Field(default=None)
    environment_config_key: str | None = Field(default=None)


class NetworkPublishEnvironmentResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    environment: NetworkEnvironmentDescriptor | None = Field(default=None)


class NetworkListEnvironmentsRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    node_id: UUID | None = Field(default=None)
    active_only: bool = Field(default=True)


class NetworkListEnvironmentsResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    environments: list[NetworkEnvironmentDescriptor] = Field(default_factory=list)


class NetworkResolveHostedServiceRoutesRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    consumer_node_id: UUID
    service_name: str | None = Field(default=None)
    endpoint_ref: str | None = Field(default=None)
    accepted_peers_only: bool = Field(default=True)


class NetworkResolveHostedServiceRoutesResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    routes: list[NetworkResolvedHostedServiceRoute] = Field(default_factory=list)


class NetworkDiscoverTerritoryRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    node_id: UUID | None = Field(default=None)
    include_peers: bool = Field(default=True)
    include_hosted_services: bool = Field(default=True)
    include_environments: bool = Field(default=True)
    active_environments_only: bool = Field(default=True)
    accepted_peers_only: bool = Field(default=True)
    limit_nodes: int | None = Field(default=200)


class NetworkDiscoverTerritoryResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    nodes: list[NetworkTerritoryNodeDescriptor] = Field(default_factory=list)
    summary: str | None = Field(default=None)


class NetworkDiscoverExperienceTerritoryRequest(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    request_id: UUID | None = Field(default=None)
    experience_name: str
    required_service_package_names: list[str] = Field(default_factory=list)
    required_endpoint_refs: list[str] = Field(default_factory=list)
    consumer_node_id: UUID | None = Field(default=None)
    active_environments_only: bool = Field(default=True)
    accepted_peers_only: bool = Field(default=True)
    include_route_hints: bool = Field(default=True)
    require_access_evidence: bool = Field(default=False)
    access_evidence_refs: list[str] = Field(default_factory=list)
    limit_entries: int | None = Field(default=200)


class NetworkDiscoverExperienceTerritoryResponse(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    entries: list[NetworkExperienceTerritoryEntry] = Field(default_factory=list)
    summary: str | None = Field(default=None)
