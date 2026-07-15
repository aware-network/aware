from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import (
    NetworkFanoutMode,
    NetworkRequestStatus,
)


class NetworkNodePeerListItem(BaseModel):
    # Attributes
    edge_id: UUID
    peer_node_id: UUID
    direction: str
    status: NetworkRequestStatus
    peer_http_base_url: str | None = Field(default=None)
    fanout_rules: list[NetworkNodePeerFanoutRuleListItem] = Field(default_factory=list)
    trust_score: float
    connected_at: datetime
    last_ping_at: datetime


class NetworkNodePeerFanoutRuleListItem(BaseModel):
    # Attributes
    id: UUID
    lane_branch_id: UUID
    lane_projection_hash: str
    enabled: bool
    mode: NetworkFanoutMode


class NetworkNodePeerListResponse(BaseModel):
    # Attributes
    results: list[NetworkNodePeerListItem] = Field(default_factory=list)
