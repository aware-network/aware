from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology
from aware_network_ontology.network.network_enums import NetworkFanoutMode

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


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

    @classmethod
    async def create_via_network_node_peer(
        cls,
        network_node_peer_id: UUID,
        lane_branch_id: UUID,
        lane_projection_hash: str,
        enabled: bool = True,
        mode: NetworkFanoutMode = NetworkFanoutMode.notify_pull,
    ) -> NetworkNodePeerFanoutRule:
        """
        Create a peer fan-out rule (v0).

        Contract:
        - Deterministic id by (network_node_peer_id, lane key) where `network_node_peer_id` is
        parent-propagated.
        - Requires invocation branch_id to match network_node_peer_id (rule lives in the peer lane).
        """

        payload = {
            "network_node_peer_id": network_node_peer_id,
            "lane_branch_id": lane_branch_id,
            "lane_projection_hash": lane_projection_hash,
            "enabled": enabled,
            "mode": mode,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_network_node_peer", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodePeerFanoutRule):
            return value
        return NetworkNodePeerFanoutRule.validate_invocation_value(value)


class NetworkNodePeerFanoutRuleCreateViaNetworkNodePeerInput(BaseModel):
    network_node_peer_id: UUID = Field(description="Foreign key for NetworkNodePeer.fanout_rules")
    lane_branch_id: UUID
    lane_projection_hash: str
    enabled: bool = Field(default=True)
    mode: NetworkFanoutMode = Field(default=NetworkFanoutMode.notify_pull)


class NetworkNodePeerFanoutRuleCreateViaNetworkNodePeerOutput(BaseModel):
    value: NetworkNodePeerFanoutRule


FUNCTIONS = {
    "NetworkNodePeerFanoutRule": {
        "create_via_network_node_peer": {
            "canonical": {
                "name": "create_via_network_node_peer",
                "description": "Create a peer fan-out rule (v0).\n\nContract:\n- Deterministic id by (network_node_peer_id, lane key) where `network_node_peer_id` is parent-propagated.\n- Requires invocation branch_id to match network_node_peer_id (rule lives in the peer lane).",
                "is_constructor": True,
            },
            "input": NetworkNodePeerFanoutRuleCreateViaNetworkNodePeerInput,
            "output": NetworkNodePeerFanoutRuleCreateViaNetworkNodePeerOutput,
        },
    },
}

__all__ = [
    "NetworkNodePeerFanoutRule",
    "NetworkNodePeerFanoutRuleCreateViaNetworkNodePeerInput",
    "NetworkNodePeerFanoutRuleCreateViaNetworkNodePeerOutput",
    "FUNCTIONS",
]
