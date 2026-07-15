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
    from aware_history_ontology.commit.commit import Commit


class Lane(ORMModel):
    """Lane is a pointer to commit with specific hash (projection_hash)."""

    # Relationships
    commits: list[Commit] = Field(default_factory=list)
    head_commit: Commit | None = Field(default=None)

    # Attributes
    lane_hash: str

    # Foreign Keys
    branch_id: UUID = Field(description="Foreign key for Branch.lanes")
    head_commit_id: UUID | None = Field(default=None, description="Foreign key for Lane.head_commit")

    async def create_commit(
        self, key: str, author_id: UUID, created_at: datetime, status: CommitStatus = CommitStatus.local
    ) -> Commit:
        """
        Create one Commit under this Lane.

        Contract:
        - Parent `lane_id` is propagated by traversal lowering.
        - Stable identity is keyed by `(lane_id, key)`.
        """

        payload = {"key": key, "author_id": author_id, "created_at": created_at, "status": status}
        result = await invoke_instance(orm_model=self, function_name="create_commit", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_history_ontology.commit.commit import Commit

        if isinstance(value, Commit):
            return value
        return Commit.validate_invocation_value(value)

    async def advance_head(self, commit_id: UUID) -> Lane:
        """
        Advance this Lane's head_commit pointer (SSOT: commit store).

        Canonical v0:
        - Used by the OIGI history plane projector to mirror domain lane heads.
        - Mutates only self (`Lane.head_commit_id` + `Lane.head_commit`).
        """

        payload = {"commit_id": commit_id}
        result = await invoke_instance(orm_model=self, function_name="advance_head", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Lane):
            return value
        return Lane.validate_invocation_value(value)

    @classmethod
    async def create_via_branch(cls, branch_id: UUID, lane_hash: str) -> Lane:
        """Creates a new Lane in the current Branch."""

        payload = {"branch_id": branch_id, "lane_hash": lane_hash}
        result = await invoke_constructor(orm_class=cls, function_name="create_via_branch", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Lane):
            return value
        return Lane.validate_invocation_value(value)


class LaneCreateCommitInput(BaseModel):
    key: str
    author_id: UUID
    created_at: datetime
    status: CommitStatus = Field(default=CommitStatus.local)


class LaneCreateCommitOutput(BaseModel):
    value: Commit


class LaneAdvanceHeadInput(BaseModel):
    commit_id: UUID


class LaneAdvanceHeadOutput(BaseModel):
    value: Lane


class LaneCreateViaBranchInput(BaseModel):
    branch_id: UUID = Field(description="Foreign key for Branch.lanes")
    lane_hash: str


class LaneCreateViaBranchOutput(BaseModel):
    value: Lane


FUNCTIONS = {
    "Lane": {
        "create_commit": {
            "canonical": {
                "name": "create_commit",
                "description": "Create one Commit under this Lane.\n\nContract:\n- Parent `lane_id` is propagated by traversal lowering.\n- Stable identity is keyed by `(lane_id, key)`.",
                "is_constructor": False,
            },
            "input": LaneCreateCommitInput,
            "output": LaneCreateCommitOutput,
        },
        "advance_head": {
            "canonical": {
                "name": "advance_head",
                "description": "Advance this Lane's head_commit pointer (SSOT: commit store).\n\nCanonical v0:\n- Used by the OIGI history plane projector to mirror domain lane heads.\n- Mutates only self (`Lane.head_commit_id` + `Lane.head_commit`).",
                "is_constructor": False,
            },
            "input": LaneAdvanceHeadInput,
            "output": LaneAdvanceHeadOutput,
        },
        "create_via_branch": {
            "canonical": {
                "name": "create_via_branch",
                "description": "Creates a new Lane in the current Branch.",
                "is_constructor": True,
            },
            "input": LaneCreateViaBranchInput,
            "output": LaneCreateViaBranchOutput,
        },
    },
}

__all__ = [
    "Lane",
    "LaneCreateCommitInput",
    "LaneCreateCommitOutput",
    "LaneAdvanceHeadInput",
    "LaneAdvanceHeadOutput",
    "LaneCreateViaBranchInput",
    "LaneCreateViaBranchOutput",
    "FUNCTIONS",
]
