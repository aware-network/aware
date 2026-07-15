from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Network Ontology
from aware_network_ontology.network.network_enums import NetworkRequestStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor import Actor


class NetworkRequest(ORMModel):
    # Relationships
    requester: Actor | None = Field(default=None, exclude=True)

    # Attributes
    status: NetworkRequestStatus = Field(default=NetworkRequestStatus.pending)

    # Foreign Keys
    requester_id: UUID = Field(description="Foreign key for NetworkRequest.requester")


FUNCTIONS = {
    "NetworkRequest": {},
}

__all__ = [
    "NetworkRequest",
    "FUNCTIONS",
]
