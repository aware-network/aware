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
    from aware_history_ontology_dto.migration.migration import Migration


class Version(BaseModel):
    # Relationships
    head_commit: Commit | None = Field(
        default=None,
        description="Optional for initial versions created before commits exist.\nThe lockfile / commit pipeline will later make this concrete.",
    )
    migrations: list[Migration] = Field(default_factory=list)
    parents: list[Version] = Field(default_factory=list)

    # Attributes
    version_number: int
