from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.commit.commit import Commit


class Lane(ORMModel):
    """Lane is a pointer to commit with specific hash (projection_hash)."""

    # Relationships
    commits: list[Commit] = Field(default_factory=list)
    head_commit: Commit | None = Field(default=None)

    # Attributes
    lane_hash: str

    # Foreign Keys
    branch_id: UUID = Field(description="Foreign key for Branch.lanes")
    head_commit_id: UUID | None = Field(default=None, description="Foreign key for Lane.head_commit")
