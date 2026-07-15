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


class CommitParent(ORMModel):
    # Relationships
    parent_commit: Commit | None = Field(default=None, exclude=True)

    # Foreign Keys
    commit_id: UUID = Field(description="Foreign key for Commit.commit_parents")
    parent_commit_id: UUID = Field(description="Foreign key for CommitParent.parent_commit")
