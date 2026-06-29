from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# History Ontology Orm Models
from aware_history_ontology_orm_models.migration.migration_enums import MigrationStatus

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.code.code import Code


class Migration(ORMModel):
    # Relationships
    codes: list[Code] = Field(default_factory=list, exclude=True)

    # Attributes
    applied_at: datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str
    status: MigrationStatus = Field(default=MigrationStatus.pending)

    # Foreign Keys
    version_id: UUID = Field(description="Foreign key for Version.migrations")
