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
    from aware_identity_ontology_orm_models.identity.identity import Identity
    from aware_interface_ontology_orm_models.interface.interface_identity_network_node import (
        InterfaceIdentityNetworkNode,
    )


class InterfaceIdentity(ORMModel):
    # Relationships
    identity: Identity | None = Field(default=None, exclude=True)
    interface_identity_network_nodes: list[InterfaceIdentityNetworkNode] = Field(default_factory=list, exclude=True)

    # Attributes
    linked_at: datetime = Field(default_factory=datetime.utcnow)
    last_confirmed_at: datetime | None = Field(default=None)

    # Foreign Keys
    interface_id: UUID = Field(description="Foreign key for Interface.interface_identities")
    identity_id: UUID = Field(description="Foreign key for InterfaceIdentity.identity")
