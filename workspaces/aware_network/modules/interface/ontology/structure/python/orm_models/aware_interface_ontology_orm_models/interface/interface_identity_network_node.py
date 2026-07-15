from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_network_ontology_orm_models.network.network_node import NetworkNode


class InterfaceIdentityNetworkNode(ORMModel):
    # Relationships
    network_node: NetworkNode | None = Field(default=None, exclude=True)

    # Attributes
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_ack_at: datetime | None = Field(default=None)
    disconnected_at: datetime | None = Field(default=None)
    last_delivery_offset: int = Field(default=0)

    # Foreign Keys
    interface_identity_id: UUID = Field(
        description="Foreign key for InterfaceIdentity.interface_identity_network_nodes"
    )
    network_node_id: UUID = Field(description="Foreign key for InterfaceIdentityNetworkNode.network_node")
