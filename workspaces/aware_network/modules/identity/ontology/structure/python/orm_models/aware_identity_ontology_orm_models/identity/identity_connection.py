from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Identity Ontology Orm Models
from aware_identity_ontology_orm_models.identity.identity_connection_enums import ConnectionRequestStatus

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology_orm_models.identity.identity import Identity


class IdentityConnection(ORMModel):
    # Relationships
    requester_identity: Identity | None = Field(default=None, exclude=True)
    recipient_identity: Identity | None = Field(default=None, exclude=True)

    # Attributes
    connection_type: str = Field(default="connect")
    metadata: JsonObject | None = Field(default=None)
    status: ConnectionRequestStatus = Field(default=ConnectionRequestStatus.pending)

    # Foreign Keys
    requester_identity_id: UUID = Field(description="Foreign key for IdentityConnection.requester_identity")
    recipient_identity_id: UUID = Field(description="Foreign key for IdentityConnection.recipient_identity")
