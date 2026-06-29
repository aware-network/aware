from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_history_ontology.commit.commit import Commit


class CommitParent(ORMModel):
    # Relationships
    parent_commit: Commit | None = Field(default=None, exclude=True)

    # Foreign Keys
    commit_id: UUID = Field(description="Foreign key for Commit.commit_parents")
    parent_commit_id: UUID = Field(description="Foreign key for CommitParent.parent_commit")

    @classmethod
    async def create_via_commit(cls, commit_id: UUID, parent_commit_id: UUID) -> CommitParent:
        """
        Creates a new CommitParent in the current Commit.

        Contract:
        - Owner `commit_id` is supplied by the `Commit -> commit_parents` traversal path.
        - Explicit constructor input is limited to the referenced `parent_commit_id`.
        """

        payload = {"commit_id": commit_id, "parent_commit_id": parent_commit_id}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_commit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CommitParent):
            return value
        return CommitParent.validate_invocation_value(value)


class CommitParentCreateViaCommitInput(BaseModel):
    commit_id: UUID = Field(description="Foreign key for Commit.commit_parents")
    parent_commit_id: UUID


class CommitParentCreateViaCommitOutput(BaseModel):
    value: CommitParent


FUNCTIONS = {
    "CommitParent": {
        "create_via_commit": {
            "canonical": {
                "name": "create_via_commit",
                "description": "Creates a new CommitParent in the current Commit.\n\nContract:\n- Owner `commit_id` is supplied by the `Commit -> commit_parents` traversal path.\n- Explicit constructor input is limited to the referenced `parent_commit_id`.",
                "is_constructor": True,
            },
            "input": CommitParentCreateViaCommitInput,
            "output": CommitParentCreateViaCommitOutput,
        },
    },
}

__all__ = [
    "CommitParent",
    "CommitParentCreateViaCommitInput",
    "CommitParentCreateViaCommitOutput",
    "FUNCTIONS",
]
