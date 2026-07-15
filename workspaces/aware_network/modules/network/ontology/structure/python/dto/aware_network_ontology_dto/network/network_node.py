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
from aware_network_ontology_dto.network.network_enums import NetworkNodeStatus

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor import Actor
    from aware_network_ontology_dto.network.network_node_config import NetworkNodeConfig
    from aware_network_ontology_dto.network.network_node_environment import NetworkNodeEnvironment
    from aware_network_ontology_dto.network.network_node_member import NetworkNodeMember
    from aware_network_ontology_dto.network.network_node_service import NetworkNodeService


class NetworkNode(BaseModel):
    # Relationships
    config: NetworkNodeConfig | None = Field(default=None)
    environments: list[NetworkNodeEnvironment] = Field(default_factory=list)
    members: list[NetworkNodeMember] = Field(default_factory=list)
    services: list[NetworkNodeService] = Field(default_factory=list)
    system_actor: Actor | None = Field(
        default=None,
        description="Node-owned system Actor used for bootstrap and topology-publication provenance.\nContract:\n- Node bootstrap/self-registration is never actorless.\n- The Node system Actor is stable before human/operator or commercial\ncontract admission exists.\n- Future contract-gated registration still uses this Node Actor as the\nprovenance subject; commercial terms add a gate, not an actorless path.",
    )

    # Attributes
    base_url: str | None = Field(default=None)
    hostname: str
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    port: int
    public_key: str
    status: NetworkNodeStatus = Field(default=NetworkNodeStatus.inactive)
