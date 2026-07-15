from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_identity_ontology_dto.identity.identity import Identity


class MemorySemantic(BaseModel):
    # Relationships
    identity: Identity | None = Field(default=None)

    # Attributes
    key: str = Field(default="default")
