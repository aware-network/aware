from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Identity Ontology Dto
from aware_identity_ontology_dto.identity.identity_connection_enums import ConnectionRequestStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_dto.identity.identity import Identity


class IdentityConnection(BaseModel):
    # Relationships
    requester_identity: Identity | None = Field(default=None)
    recipient_identity: Identity | None = Field(default=None)

    # Attributes
    connection_type: str = Field(default="connect")
    metadata: JsonObject | None = Field(default=None)
    status: ConnectionRequestStatus = Field(default=ConnectionRequestStatus.pending)
