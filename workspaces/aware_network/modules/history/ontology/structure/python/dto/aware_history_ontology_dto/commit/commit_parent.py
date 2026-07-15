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


class CommitParent(BaseModel):
    # Relationships
    parent_commit: Commit | None = Field(default=None)
