from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology Orm Models
from aware_network_ontology_orm_models.network.network_enums import NetworkNodeStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.actor.actor import Actor
    from aware_network_ontology_orm_models.network.network_node_config import NetworkNodeConfig
    from aware_network_ontology_orm_models.network.network_node_environment import NetworkNodeEnvironment
    from aware_network_ontology_orm_models.network.network_node_member import NetworkNodeMember
    from aware_network_ontology_orm_models.network.network_node_service import NetworkNodeService


class NetworkNode(ORMModel):
    # Relationships
    config: NetworkNodeConfig | None = Field(default=None, exclude=True)
    environments: list[NetworkNodeEnvironment] = Field(default_factory=list)
    members: list[NetworkNodeMember] = Field(default_factory=list, exclude=True)
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

    # Foreign Keys
    config_id: UUID | None = Field(default=None, description="Foreign key for NetworkNode.config")
    system_actor_id: UUID | None = Field(default=None, description="Foreign key for NetworkNode.system_actor")
