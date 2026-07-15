from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.identity.identity import Identity
    from aware_interface_ontology_dto.interface.interface_identity_network_node import InterfaceIdentityNetworkNode


class InterfaceIdentity(BaseModel):
    # Relationships
    identity: Identity | None = Field(default=None)
    interface_identity_network_nodes: list[InterfaceIdentityNetworkNode] = Field(default_factory=list)

    # Attributes
    linked_at: datetime = Field(default_factory=datetime.utcnow)
    last_confirmed_at: datetime | None = Field(default=None)
