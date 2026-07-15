from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import NetworkRequestStatus

if TYPE_CHECKING:
    from aware_network_ontology_dto.network.network_node import NetworkNode
    from aware_network_ontology_dto.network.network_node_peer_fanout_rule import NetworkNodePeerFanoutRule


class NetworkNodePeer(BaseModel):
    # Relationships
    source_peer_node: NetworkNode | None = Field(default=None)
    target_peer_node: NetworkNode | None = Field(default=None)
    fanout_rules: list[NetworkNodePeerFanoutRule] = Field(default_factory=list)

    # Attributes
    status: NetworkRequestStatus = Field(default=NetworkRequestStatus.pending)
    peer_http_base_url: str | None = Field(default=None)
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    failed_interactions: int = Field(default=0)
    last_ping_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: int | None = Field(default=None)
    successful_interactions: int = Field(default=0)
    trust_score: float = Field(default=50)
