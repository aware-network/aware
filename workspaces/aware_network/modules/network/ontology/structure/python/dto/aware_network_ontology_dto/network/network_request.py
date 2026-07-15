from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Network Ontology Dto
from aware_network_ontology_dto.network.network_enums import NetworkRequestStatus

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor import Actor


class NetworkRequest(BaseModel):
    # Relationships
    requester: Actor | None = Field(default=None)

    # Attributes
    status: NetworkRequestStatus = Field(default=NetworkRequestStatus.pending)
