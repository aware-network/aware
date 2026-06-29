from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# History Ontology Dto
from aware_history_ontology_dto.migration.migration_enums import MigrationStatus

if TYPE_CHECKING:
    from aware_code_ontology_dto.code.code import Code


class Migration(BaseModel):
    # Relationships
    codes: list[Code] = Field(default_factory=list)

    # Attributes
    applied_at: datetime | None = Field(default=None)
    description: str | None = Field(default=None)
    name: str
    status: MigrationStatus = Field(default=MigrationStatus.pending)
