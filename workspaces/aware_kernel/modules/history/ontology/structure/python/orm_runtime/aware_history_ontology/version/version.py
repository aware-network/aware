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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_history_ontology.commit.commit import Commit
    from aware_history_ontology.migration.migration import Migration


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

    async def create_migration(
        self,
        name: str,
        description: str | None = None,
        applied_at: datetime | None = None,
        status: MigrationStatus = MigrationStatus.pending,
    ) -> Migration:
        """
        Create one Migration under this Version.

        Contract:
        - Parent `version_id` is propagated by traversal lowering.
        - Stable identity is keyed by `(version_id, name)`.
        """

        payload = {"name": name, "description": description, "applied_at": applied_at, "status": status}
        result = await invoke_instance(orm_model=self, function_name="create_migration", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_history_ontology.migration.migration import Migration

        if isinstance(value, Migration):
            return value
        return Migration.validate_invocation_value(value)

    @classmethod
    async def create_via_branch(
        cls, branch_id: UUID, version_number: int, head_commit_id: UUID | None = None
    ) -> Version:
        """Create one Version under this Branch."""

        payload = {"branch_id": branch_id, "version_number": version_number, "head_commit_id": head_commit_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_branch", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Version):
            return value
        return Version.validate_invocation_value(value)


class VersionCreateMigrationInput(BaseModel):
    name: str
    description: str | None = Field(default=None)
    applied_at: datetime | None = Field(default=None)
    status: MigrationStatus = Field(default=MigrationStatus.pending)


class VersionCreateMigrationOutput(BaseModel):
    value: Migration


class VersionCreateViaBranchInput(BaseModel):
    branch_id: UUID = Field(description="Foreign key for Branch.versions")
    version_number: int
    head_commit_id: UUID | None = Field(default=None)


class VersionCreateViaBranchOutput(BaseModel):
    value: Version


FUNCTIONS = {
    "Version": {
        "create_migration": {
            "canonical": {
                "name": "create_migration",
                "description": "Create one Migration under this Version.\n\nContract:\n- Parent `version_id` is propagated by traversal lowering.\n- Stable identity is keyed by `(version_id, name)`.",
                "is_constructor": False,
            },
            "input": VersionCreateMigrationInput,
            "output": VersionCreateMigrationOutput,
        },
        "create_via_branch": {
            "canonical": {
                "name": "create_via_branch",
                "description": "Create one Version under this Branch.",
                "is_constructor": True,
            },
            "input": VersionCreateViaBranchInput,
            "output": VersionCreateViaBranchOutput,
        },
    },
}

__all__ = [
    "Version",
    "VersionCreateMigrationInput",
    "VersionCreateMigrationOutput",
    "VersionCreateViaBranchInput",
    "VersionCreateViaBranchOutput",
    "FUNCTIONS",
]
