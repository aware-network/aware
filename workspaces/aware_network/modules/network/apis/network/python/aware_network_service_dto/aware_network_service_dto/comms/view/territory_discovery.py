from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class NetworkTerritoryNodeRouteViewStateV1(BaseModel):
    """
    View-state contract for public Network territory discovery.
    Public API view key: network.territory_discovery
    """

    # Attributes
    node_id: str | None = Field(default=None)
    public_key: str | None = Field(default=None)
    hostname: str | None = Field(default=None)
    port: int | None = Field(default=None)
    base_url: str | None = Field(default=None)
    status: str = Field(default="active")
    last_seen_at: str | None = Field(default=None)


class NetworkTerritoryEnvironmentViewStateV1(BaseModel):
    # Attributes
    node_id: str | None = Field(default=None)
    environment_id: str | None = Field(default=None)
    environment_key: str | None = Field(default=None)
    environment_title: str | None = Field(default=None)
    role: str = Field(default="replica")
    is_active: bool = Field(default=True)
    priority: int = Field(default=0)
    status: str = Field(default="active")
    experience_names: list[str] = Field(default_factory=list)
    environment_config_id: str | None = Field(default=None)
    environment_config_key: str | None = Field(default=None)


class NetworkTerritoryHostedServiceViewStateV1(BaseModel):
    # Attributes
    service_id: str | None = Field(default=None)
    service_name: str | None = Field(default=None)
    service_package_names: list[str] = Field(default_factory=list)
    endpoint_refs: list[str] = Field(default_factory=list)
    stream_endpoint_refs: list[str] = Field(default_factory=list)
    host_id: str | None = Field(default=None)
    host_version: str | None = Field(default=None)
    protocol_version: str | None = Field(default=None)
    supports_stream_events: bool = Field(default=False)


class NetworkTerritoryPeerViewStateV1(BaseModel):
    # Attributes
    edge_id: str | None = Field(default=None)
    source_node_id: str | None = Field(default=None)
    target_node_id: str | None = Field(default=None)
    peer_node_id: str | None = Field(default=None)
    peer_base_url: str | None = Field(default=None)
    direction: str = Field(default="outgoing")
    status: str = Field(default="accepted")
    trust_score: float = Field(default=0.0)
    connected_at: str | None = Field(default=None)
    last_ping_at: str | None = Field(default=None)


class NetworkTerritoryNodeViewStateV1(BaseModel):
    # Attributes
    node: NetworkTerritoryNodeRouteViewStateV1 | None = Field(default=None)
    environments: list[NetworkTerritoryEnvironmentViewStateV1] = Field(default_factory=list)
    hosted_services: list[NetworkTerritoryHostedServiceViewStateV1] = Field(default_factory=list)
    peers: list[NetworkTerritoryPeerViewStateV1] = Field(default_factory=list)


class NetworkTerritoryDiscoveryViewStateV1(BaseModel):
    # Attributes
    status: str = Field(default="waiting")
    authority_source_url: str | None = Field(default=None)
    nodes: list[NetworkTerritoryNodeViewStateV1] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    empty_message: str = Field(default="No Network territory has been published yet")
    error: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)
