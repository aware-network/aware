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
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch


class ProgramBranch(ORMModel):
    # Relationships
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    view_key: str | None = Field(default=None)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.branches")
    object_instance_graph_branch_id: UUID = Field(
        description="Foreign key for ProgramBranch.object_instance_graph_branch"
    )

    @classmethod
    async def build_via_program(
        cls,
        program_id: UUID,
        object_instance_graph_branch_id: UUID,
        key: str | None = None,
        view_key: str | None = None,
        is_active: bool = True,
    ) -> ProgramBranch:
        """
        Create a deterministic ProgramBranch association edge.

        Contract:
        - Identity is derived from `(program_id, object_instance_graph_branch_id)`.
        - Constructor is idempotent for repeated calls with the same pair.
        """

        payload = {
            "program_id": program_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "key": key,
            "view_key": view_key,
            "is_active": is_active,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramBranch):
            return value
        return ProgramBranch.validate_invocation_value(value)


class ProgramBranchBuildViaProgramInput(BaseModel):
    program_id: UUID = Field(description="Foreign key for Program.branches")
    object_instance_graph_branch_id: UUID
    key: str | None = Field(default=None)
    view_key: str | None = Field(default=None)
    is_active: bool = Field(default=True)


class ProgramBranchBuildViaProgramOutput(BaseModel):
    value: ProgramBranch


FUNCTIONS = {
    "ProgramBranch": {
        "build_via_program": {
            "canonical": {
                "name": "build_via_program",
                "description": "Create a deterministic ProgramBranch association edge.\n\nContract:\n- Identity is derived from `(program_id, object_instance_graph_branch_id)`.\n- Constructor is idempotent for repeated calls with the same pair.",
                "is_constructor": True,
            },
            "input": ProgramBranchBuildViaProgramInput,
            "output": ProgramBranchBuildViaProgramOutput,
        },
    },
}

__all__ = [
    "ProgramBranch",
    "ProgramBranchBuildViaProgramInput",
    "ProgramBranchBuildViaProgramOutput",
    "FUNCTIONS",
]
