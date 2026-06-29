from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_history_ontology_dto.commit.commit import Commit


class Lane(BaseModel):
    """Lane is a pointer to commit with specific hash (projection_hash)."""

    # Relationships
    commits: list[Commit] = Field(default_factory=list)
    head_commit: Commit | None = Field(default=None)

    # Attributes
    lane_hash: str
