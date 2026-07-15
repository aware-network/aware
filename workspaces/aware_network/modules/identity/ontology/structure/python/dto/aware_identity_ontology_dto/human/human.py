from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.actor.actor import Actor


class Human(BaseModel):
    # Relationships
    actor: Actor | None = Field(default=None)
