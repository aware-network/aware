from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# History Ontology Orm Models
from aware_history_ontology_orm_models.commit.commit_enums import CommitStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_history_ontology_orm_models.commit.commit_parent import CommitParent


class Commit(ORMModel):
    # Relationships
    commit_parents: list[CommitParent] = Field(default_factory=list)

    # Attributes
    author_id: UUID
    key: str
    created_at: datetime
    status: CommitStatus = Field(default=CommitStatus.local)

    # Foreign Keys
    lane_id: UUID = Field(description="Foreign key for Lane.commits")
