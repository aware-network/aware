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
    from aware_history_ontology_orm_models.migration.migration import Migration


class Version(ORMModel):
    # Relationships
    head_commit: Commit | None = Field(
        default=None,
        description="Optional for initial versions created before commits exist.\nThe lockfile / commit pipeline will later make this concrete.",
    )
    migrations: list[Migration] = Field(default_factory=list, exclude=True)
    parents: list[Version] = Field(default_factory=list, exclude=True)

    # Attributes
    version_number: int

    # Foreign Keys
    branch_id: UUID = Field(description="Foreign key for Branch.versions")
    version_id: UUID | None = Field(default=None, description="Foreign key for Version.parents")
    head_commit_id: UUID | None = Field(default=None, description="Foreign key for Version.head_commit")
