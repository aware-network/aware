from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import NetworkFanoutMode

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class NetworkNodePeerFanoutRule(BaseModel):
    # Relationships
    lane_branch: ObjectInstanceGraphBranch | None = Field(default=None)

    # Attributes
    lane_projection_hash: str
    enabled: bool = Field(default=True)
    mode: NetworkFanoutMode = Field(default=NetworkFanoutMode.notify_pull)
