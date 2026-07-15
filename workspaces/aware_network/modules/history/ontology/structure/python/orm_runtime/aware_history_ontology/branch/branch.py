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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_history_ontology.lane.lane import Lane
    from aware_history_ontology.version.version import Version


class Branch(ORMModel):
    """Branch is a bundle of lanes."""

    # Relationships
    lanes: list[Lane] = Field(default_factory=list, exclude=True)
    versions: list[Version] = Field(default_factory=list, exclude=True)

    # Attributes
    is_main: bool = Field(default=False)
    key: str = Field(default="default")
    name: str | None = Field(default=None)

    @classmethod
    async def create(
        cls, branch_id: UUID, lane_hash: str, key: str = "default", is_main: bool = False, name: str | None = None
    ) -> Branch:
        """
        Creates a new Branch as a bundle of lanes.

        Contract:
        - Stable identity is constructor-keyed by `key`.
        - Initial Lane is constructed via Branch->Lane propagation.
        """

        payload = {"branch_id": branch_id, "lane_hash": lane_hash, "key": key, "is_main": is_main, "name": name}
        result = await invoke_constructor(orm_class=cls, function_name="create", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, Branch):
            return value
        return Branch.validate_invocation_value(value)

    async def attach_lane(self, lane_hash: str) -> Lane:
        """
        Attaches a Lane to this Branch (idempotent).

        Contract:
        - Must be invoked as an instance function so the runtime can enforce
          "mutate self only" for the Branch→Lane relationship.
        - The Lane is created via Lane.create if missing.
        """

        payload = {"lane_hash": lane_hash}
        result = await invoke_instance(orm_model=self, function_name="attach_lane", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_history_ontology.lane.lane import Lane

        if isinstance(value, Lane):
            return value
        return Lane.validate_invocation_value(value)

    async def create_version(self, version_number: int, head_commit_id: UUID | None = None) -> Version:
        """
        Create one Version under this Branch.

        Contract:
        - Parent `branch_id` is propagated by traversal lowering.
        - Stable identity is keyed by `(branch_id, version_number)`.
        """

        payload = {"version_number": version_number, "head_commit_id": head_commit_id}
        result = await invoke_instance(orm_model=self, function_name="create_version", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_history_ontology.version.version import Version

        if isinstance(value, Version):
            return value
        return Version.validate_invocation_value(value)


class BranchCreateInput(BaseModel):
    branch_id: UUID
    lane_hash: str
    key: str = Field(default="default")
    is_main: bool = Field(default=False)
    name: str | None = Field(default=None)


class BranchCreateOutput(BaseModel):
    value: Branch


class BranchAttachLaneInput(BaseModel):
    lane_hash: str


class BranchAttachLaneOutput(BaseModel):
    value: Lane


class BranchCreateVersionInput(BaseModel):
    version_number: int
    head_commit_id: UUID | None = Field(default=None)


class BranchCreateVersionOutput(BaseModel):
    value: Version


FUNCTIONS = {
    "Branch": {
        "create": {
            "canonical": {
                "name": "create",
                "description": "Creates a new Branch as a bundle of lanes.\n\nContract:\n- Stable identity is constructor-keyed by `key`.\n- Initial Lane is constructed via Branch->Lane propagation.",
                "is_constructor": True,
            },
            "input": BranchCreateInput,
            "output": BranchCreateOutput,
        },
        "attach_lane": {
            "canonical": {
                "name": "attach_lane",
                "description": 'Attaches a Lane to this Branch (idempotent).\n\nContract:\n- Must be invoked as an instance function so the runtime can enforce\n  "mutate self only" for the Branch→Lane relationship.\n- The Lane is created via Lane.create if missing.',
                "is_constructor": False,
            },
            "input": BranchAttachLaneInput,
            "output": BranchAttachLaneOutput,
        },
        "create_version": {
            "canonical": {
                "name": "create_version",
                "description": "Create one Version under this Branch.\n\nContract:\n- Parent `branch_id` is propagated by traversal lowering.\n- Stable identity is keyed by `(branch_id, version_number)`.",
                "is_constructor": False,
            },
            "input": BranchCreateVersionInput,
            "output": BranchCreateVersionOutput,
        },
    },
}

__all__ = [
    "Branch",
    "BranchCreateInput",
    "BranchCreateOutput",
    "BranchAttachLaneInput",
    "BranchAttachLaneOutput",
    "BranchCreateVersionInput",
    "BranchCreateVersionOutput",
    "FUNCTIONS",
]
