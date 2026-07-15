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
from aware_history_ontology.commit.commit_enums import CommitStatus

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_history_ontology.commit.commit_parent import CommitParent


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

    async def add_parent(self, parent_id: UUID) -> CommitParent:
        """
        Attach one parent edge under this Commit.

        Contract:
        - Owner `commit_id` is propagated from Commit via traversal lowering.
        - Only the explicit reference-side `parent_commit_id` is authored here.
        - Stable identity is keyed by `(commit_id, parent_id)`.
        """

        payload = {"parent_id": parent_id}
        result = await invoke_instance(orm_model=self, function_name="add_parent", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_history_ontology.commit.commit_parent import CommitParent

        if isinstance(value, CommitParent):
            return value
        return CommitParent.validate_invocation_value(value)

    @classmethod
    async def create_via_lane(
        cls, lane_id: UUID, key: str, author_id: UUID, created_at: datetime, status: CommitStatus = CommitStatus.local
    ) -> Commit:
        """Creates a new Commit in the current Lane."""

        payload = {"lane_id": lane_id, "key": key, "author_id": author_id, "created_at": created_at, "status": status}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_lane", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Commit):
            return value
        return Commit.validate_invocation_value(value)


class CommitAddParentInput(BaseModel):
    parent_id: UUID


class CommitAddParentOutput(BaseModel):
    value: CommitParent


class CommitCreateViaLaneInput(BaseModel):
    lane_id: UUID = Field(description="Foreign key for Lane.commits")
    key: str
    author_id: UUID
    created_at: datetime
    status: CommitStatus = Field(default=CommitStatus.local)


class CommitCreateViaLaneOutput(BaseModel):
    value: Commit


FUNCTIONS = {
    "Commit": {
        "add_parent": {
            "canonical": {
                "name": "add_parent",
                "description": "Attach one parent edge under this Commit.\n\nContract:\n- Owner `commit_id` is propagated from Commit via traversal lowering.\n- Only the explicit reference-side `parent_commit_id` is authored here.\n- Stable identity is keyed by `(commit_id, parent_id)`.",
                "is_constructor": False,
            },
            "input": CommitAddParentInput,
            "output": CommitAddParentOutput,
        },
        "create_via_lane": {
            "canonical": {
                "name": "create_via_lane",
                "description": "Creates a new Commit in the current Lane.",
                "is_constructor": True,
            },
            "input": CommitCreateViaLaneInput,
            "output": CommitCreateViaLaneOutput,
        },
    },
}

__all__ = [
    "Commit",
    "CommitAddParentInput",
    "CommitAddParentOutput",
    "CommitCreateViaLaneInput",
    "CommitCreateViaLaneOutput",
    "FUNCTIONS",
]
