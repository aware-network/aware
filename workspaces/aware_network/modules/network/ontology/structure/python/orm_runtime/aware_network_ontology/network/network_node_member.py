from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class NetworkNodeMember(ORMModel):
    # Attributes
    identity_id: UUID
    is_primary: bool = Field(default=True)
    last_sync_at: datetime = Field(default_factory=datetime.utcnow)
    managed_since: datetime = Field(default_factory=datetime.utcnow)

    # Foreign Keys
    network_node_id: UUID = Field(description="Foreign key for NetworkNode.members")


FUNCTIONS = {
    "NetworkNodeMember": {},
}

__all__ = [
    "NetworkNodeMember",
    "FUNCTIONS",
]
