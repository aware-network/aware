from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class NetworkDirectoryNodeRouteItem(BaseModel):
    # Attributes
    node_id: UUID
    public_key: str | None = Field(default=None)
    hostname: str
    port: int
    base_url: str | None = Field(default=None)
    status: str = Field(default="active")
    last_seen_at: str | None = Field(default=None)


class NetworkDirectoryPeerItem(BaseModel):
    # Attributes
    edge_id: UUID | None = Field(default=None)
    source_node_id: UUID
    target_node_id: UUID
    peer_node_id: UUID
    peer_base_url: str
    direction: str = Field(default="outgoing")
    status: str = Field(default="accepted")
    trust_score: float = Field(default=0.0)
    connected_at: str | None = Field(default=None)
    last_ping_at: str | None = Field(default=None)


class NetworkDirectoryHostedServiceItem(BaseModel):
    # Attributes
    service_id: UUID
    service_name: str
    service_package_names: list[str] = Field(default_factory=list)
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str
    host_version: str | None = Field(default=None)
    protocol_version: str
    supports_stream_events: bool = Field(default=False)


class NetworkDirectoryEnvironmentItem(BaseModel):
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


class NetworkDirectoryTerritoryNodeItem(BaseModel):
    # Attributes
    node: NetworkDirectoryNodeRouteItem
    environments: list[NetworkDirectoryEnvironmentItem] = Field(default_factory=list)
    hosted_services: list[NetworkDirectoryHostedServiceItem] = Field(default_factory=list)
    peers: list[NetworkDirectoryPeerItem] = Field(default_factory=list)


class NetworkDirectoryTerritoryResponse(BaseModel):
    # Attributes
    nodes: list[NetworkDirectoryTerritoryNodeItem] = Field(default_factory=list)
    summary: str | None = Field(default=None)


class NetworkDirectoryExperienceServiceCandidate(BaseModel):
    # Attributes
    hosted_service: NetworkDirectoryHostedServiceItem
    provider_node_id: UUID
    provider_node_base_url: str | None = Field(default=None)
    route_connection_id: UUID | None = Field(default=None)
    route_status: str = Field(default="reachable")
    matched_service_package_names: list[str] = Field(default_factory=list)
    matched_endpoint_refs: list[str] = Field(default_factory=list)
    missing_service_package_names: list[str] = Field(default_factory=list)
    missing_endpoint_refs: list[str] = Field(default_factory=list)


class NetworkDirectoryExperienceTerritoryEntry(BaseModel):
    # Attributes
    experience_name: str
    node: NetworkDirectoryNodeRouteItem
    environment: NetworkDirectoryEnvironmentItem
    service_candidates: list[NetworkDirectoryExperienceServiceCandidate] = Field(default_factory=list)
    route_status: str = Field(default="unavailable")
    missing_service_package_names: list[str] = Field(default_factory=list)
    missing_endpoint_refs: list[str] = Field(default_factory=list)


class NetworkDirectoryExperienceTerritoryResponse(BaseModel):
    # Attributes
    experience_name: str | None = Field(default=None)
    entries: list[NetworkDirectoryExperienceTerritoryEntry] = Field(default_factory=list)
    summary: str | None = Field(default=None)
