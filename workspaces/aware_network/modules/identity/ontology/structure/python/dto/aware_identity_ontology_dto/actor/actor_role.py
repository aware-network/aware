from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.role.role import Role


class ActorRole(BaseModel):
    # Relationships
    role: Role | None = Field(default=None)
