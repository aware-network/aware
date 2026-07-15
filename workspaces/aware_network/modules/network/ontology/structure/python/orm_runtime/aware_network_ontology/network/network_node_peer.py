from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology
from aware_network_ontology.network.network_enums import (
    NetworkFanoutMode,
    NetworkRequestStatus,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_network_ontology.network.network_node import NetworkNode
    from aware_network_ontology.network.network_node_peer_fanout_rule import NetworkNodePeerFanoutRule


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

    @classmethod
    async def create(
        cls, network_node_id: UUID, peer_node_id: UUID, peer_http_base_url: str | None = None
    ) -> NetworkNodePeer:
        """
        Creates an accepted peer link between two NetworkNodes (v0 bootstrap).

        Contract:
        - Deterministic NetworkNodePeer.id (stable by (network_node_id, peer_node_id)).
        - Idempotent: repeated calls yield the same NetworkNodePeer.id.
        - Sets status=`accepted`.
        """

        payload = {
            "network_node_id": network_node_id,
            "peer_node_id": peer_node_id,
            "peer_http_base_url": peer_http_base_url,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodePeer):
            return value
        return NetworkNodePeer.validate_invocation_value(value)

    @classmethod
    async def request(
        cls, network_node_id: UUID, peer_node_id: UUID, peer_http_base_url: str | None = None
    ) -> NetworkNodePeer:
        """
        Creates a pending peer request between two NetworkNodes (v0).

        Contract:
        - Deterministic NetworkNodePeer.id (stable by (network_node_id, peer_node_id)).
        - Idempotent: repeated calls yield the same NetworkNodePeer.id.
        - Sets status=`pending`.
        """

        payload = {
            "network_node_id": network_node_id,
            "peer_node_id": peer_node_id,
            "peer_http_base_url": peer_http_base_url,
        }
        result = await invoke_constructor(orm_class=cls, function_name="request", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodePeer):
            return value
        return NetworkNodePeer.validate_invocation_value(value)

    async def respond(self, status: NetworkRequestStatus) -> NetworkNodePeer:
        """
        Accept or reject a pending NetworkNodePeer request (v0).

        Canonical contract:
        - Allowed transitions: pending -> accepted|rejected (idempotent).
        """

        payload = {"status": status}
        result = await invoke_instance(orm_model=self, function_name="respond", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodePeer):
            return value
        return NetworkNodePeer.validate_invocation_value(value)

    async def upsert_fanout_rule(
        self,
        lane_branch_id: UUID,
        lane_projection_hash: str,
        enabled: bool = True,
        mode: NetworkFanoutMode = NetworkFanoutMode.notify_pull,
    ) -> NetworkNodePeer:
        """
        Upsert a fan-out rule for this peer (v0).

        Contract:
        - Targets a lane key (`lane_branch_id`, `lane_projection_hash`).
        - Idempotent by (peer.id, lane key).
        """

        payload = {
            "lane_branch_id": lane_branch_id,
            "lane_projection_hash": lane_projection_hash,
            "enabled": enabled,
            "mode": mode,
        }
        result = await invoke_instance(orm_model=self, function_name="upsert_fanout_rule", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodePeer):
            return value
        return NetworkNodePeer.validate_invocation_value(value)

    async def remove_fanout_rule(self, lane_branch_id: UUID, lane_projection_hash: str) -> NetworkNodePeer:
        """
        Remove a fan-out rule for this peer (v0).

        Contract:
        - Idempotent: removing a missing rule is a no-op.
        """

        payload = {"lane_branch_id": lane_branch_id, "lane_projection_hash": lane_projection_hash}
        result = await invoke_instance(orm_model=self, function_name="remove_fanout_rule", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, NetworkNodePeer):
            return value
        return NetworkNodePeer.validate_invocation_value(value)


class NetworkNodePeerCreateInput(BaseModel):
    network_node_id: UUID
    peer_node_id: UUID
    peer_http_base_url: str | None = Field(default=None)


class NetworkNodePeerCreateOutput(BaseModel):
    value: NetworkNodePeer


class NetworkNodePeerRequestInput(BaseModel):
    network_node_id: UUID
    peer_node_id: UUID
    peer_http_base_url: str | None = Field(default=None)


class NetworkNodePeerRequestOutput(BaseModel):
    value: NetworkNodePeer


class NetworkNodePeerRespondInput(BaseModel):
    status: NetworkRequestStatus


class NetworkNodePeerRespondOutput(BaseModel):
    value: NetworkNodePeer


class NetworkNodePeerUpsertFanoutRuleInput(BaseModel):
    lane_branch_id: UUID
    lane_projection_hash: str
    enabled: bool = Field(default=True)
    mode: NetworkFanoutMode = Field(default=NetworkFanoutMode.notify_pull)


class NetworkNodePeerUpsertFanoutRuleOutput(BaseModel):
    value: NetworkNodePeer


class NetworkNodePeerRemoveFanoutRuleInput(BaseModel):
    lane_branch_id: UUID
    lane_projection_hash: str


class NetworkNodePeerRemoveFanoutRuleOutput(BaseModel):
    value: NetworkNodePeer


FUNCTIONS = {
    "NetworkNodePeer": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Creates an accepted peer link between two NetworkNodes (v0 bootstrap).\n\nContract:\n- Deterministic NetworkNodePeer.id (stable by (network_node_id, peer_node_id)).\n- Idempotent: repeated calls yield the same NetworkNodePeer.id.\n- Sets status=`accepted`.",
                "is_constructor": True,
            },
            "input": NetworkNodePeerCreateInput,
            "output": NetworkNodePeerCreateOutput,
        },
        "request": {
            "canonical": {
                "name": "request",
                "description": "Creates a pending peer request between two NetworkNodes (v0).\n\nContract:\n- Deterministic NetworkNodePeer.id (stable by (network_node_id, peer_node_id)).\n- Idempotent: repeated calls yield the same NetworkNodePeer.id.\n- Sets status=`pending`.",
                "is_constructor": True,
            },
            "input": NetworkNodePeerRequestInput,
            "output": NetworkNodePeerRequestOutput,
        },
        "respond": {
            "canonical": {
                "name": "respond",
                "description": "Accept or reject a pending NetworkNodePeer request (v0).\n\nCanonical contract:\n- Allowed transitions: pending -> accepted|rejected (idempotent).",
                "is_constructor": False,
            },
            "input": NetworkNodePeerRespondInput,
            "output": NetworkNodePeerRespondOutput,
        },
        "upsert_fanout_rule": {
            "canonical": {
                "name": "upsert_fanout_rule",
                "description": "Upsert a fan-out rule for this peer (v0).\n\nContract:\n- Targets a lane key (`lane_branch_id`, `lane_projection_hash`).\n- Idempotent by (peer.id, lane key).",
                "is_constructor": False,
            },
            "input": NetworkNodePeerUpsertFanoutRuleInput,
            "output": NetworkNodePeerUpsertFanoutRuleOutput,
        },
        "remove_fanout_rule": {
            "canonical": {
                "name": "remove_fanout_rule",
                "description": "Remove a fan-out rule for this peer (v0).\n\nContract:\n- Idempotent: removing a missing rule is a no-op.",
                "is_constructor": False,
            },
            "input": NetworkNodePeerRemoveFanoutRuleInput,
            "output": NetworkNodePeerRemoveFanoutRuleOutput,
        },
    },
}

__all__ = [
    "NetworkNodePeer",
    "NetworkNodePeerCreateInput",
    "NetworkNodePeerCreateOutput",
    "NetworkNodePeerRequestInput",
    "NetworkNodePeerRequestOutput",
    "NetworkNodePeerRespondInput",
    "NetworkNodePeerRespondOutput",
    "NetworkNodePeerUpsertFanoutRuleInput",
    "NetworkNodePeerUpsertFanoutRuleOutput",
    "NetworkNodePeerRemoveFanoutRuleInput",
    "NetworkNodePeerRemoveFanoutRuleOutput",
    "FUNCTIONS",
]
