from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology Orm Models
from aware_network_ontology_orm_models.network.network_enums import NetworkRequestStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_network_ontology_orm_models.network.network_node import NetworkNode
    from aware_network_ontology_orm_models.network.network_node_peer_fanout_rule import NetworkNodePeerFanoutRule


class NetworkNodePeer(ORMModel):
    # Relationships
    source_peer_node: NetworkNode | None = Field(default=None, exclude=True)
    target_peer_node: NetworkNode | None = Field(default=None, exclude=True)
    fanout_rules: list[NetworkNodePeerFanoutRule] = Field(default_factory=list, exclude=True)

    # Attributes
    status: NetworkRequestStatus = Field(default=NetworkRequestStatus.pending)
    peer_http_base_url: str | None = Field(default=None)
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    failed_interactions: int = Field(default=0)
    last_ping_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: int | None = Field(default=None)
    successful_interactions: int = Field(default=0)
    trust_score: float = Field(default=50)

    # Foreign Keys
    source_peer_node_id: UUID = Field(description="Foreign key for NetworkNodePeer.source_peer_node")
    target_peer_node_id: UUID = Field(description="Foreign key for NetworkNodePeer.target_peer_node")
