from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# History Ontology Dto
from aware_history_ontology_dto.commit.commit_enums import CommitStatus

if TYPE_CHECKING:
    from aware_history_ontology_dto.commit.commit_parent import CommitParent


class Commit(BaseModel):
    # Relationships
    commit_parents: list[CommitParent] = Field(default_factory=list)

    # Attributes
    author_id: UUID
    key: str
    created_at: datetime
    status: CommitStatus = Field(default=CommitStatus.local)
