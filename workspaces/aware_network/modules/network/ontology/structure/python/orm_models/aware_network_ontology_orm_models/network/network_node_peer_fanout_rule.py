from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology Orm Models
from aware_network_ontology_orm_models.network.network_enums import NetworkFanoutMode

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class NetworkNodePeerFanoutRule(ORMModel):
    # Relationships
    lane_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    lane_projection_hash: str
    enabled: bool = Field(default=True)
    mode: NetworkFanoutMode = Field(default=NetworkFanoutMode.notify_pull)

    # Foreign Keys
    network_node_peer_id: UUID = Field(description="Foreign key for NetworkNodePeer.fanout_rules")
    lane_branch_id: UUID = Field(description="Foreign key for NetworkNodePeerFanoutRule.lane_branch")
