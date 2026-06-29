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

# History Ontology
from aware_history_ontology.migration.migration_enums import MigrationStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_code_ontology.code.code import Code


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

    @classmethod
    async def create_via_version(
        cls,
        version_id: UUID,
        name: str,
        description: str | None = None,
        applied_at: datetime | None = None,
        status: MigrationStatus = MigrationStatus.pending,
    ) -> Migration:
        """Create one Migration under this Version."""

        payload = {
            "version_id": version_id,
            "name": name,
            "description": description,
            "applied_at": applied_at,
            "status": status,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_version", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Migration):
            return value
        return Migration.validate_invocation_value(value)


class MigrationCreateViaVersionInput(BaseModel):
    version_id: UUID = Field(description="Foreign key for Version.migrations")
    name: str
    description: str | None = Field(default=None)
    applied_at: datetime | None = Field(default=None)
    status: MigrationStatus = Field(default=MigrationStatus.pending)


class MigrationCreateViaVersionOutput(BaseModel):
    value: Migration


FUNCTIONS = {
    "Migration": {
        "create_via_version": {
            "canonical": {
                "name": "create_via_version",
                "description": "Create one Migration under this Version.",
                "is_constructor": True,
            },
            "input": MigrationCreateViaVersionInput,
            "output": MigrationCreateViaVersionOutput,
        },
    },
}

__all__ = [
    "Migration",
    "MigrationCreateViaVersionInput",
    "MigrationCreateViaVersionOutput",
    "FUNCTIONS",
]
