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
    from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph


class ProgramConfigGraphObjectConfigGraph(ORMModel):
    """Bridge between Experience-Structure via ProgramConfigGraph-ObjectConfigGraph."""

    # Relationships
    object_config_graph: ObjectConfigGraph | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.object_config_graphs")
    object_config_graph_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphObjectConfigGraph.object_config_graph"
    )

    @classmethod
    async def build_via_program_config_graph(
        cls, program_config_graph_id: UUID, object_config_graph_id: UUID, key: str | None = None
    ) -> ProgramConfigGraphObjectConfigGraph:
        """
        Create a deterministic ProgramConfigGraphObjectConfigGraph under this.

        Contract:
        - Identity is derived from `(program_config_graph_id, object_config_graph_id)`.
        - Constructor is idempotent for the same pair.
        """

        payload = {
            "program_config_graph_id": program_config_graph_id,
            "object_config_graph_id": object_config_graph_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_config_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigGraphObjectConfigGraph):
            return value
        return ProgramConfigGraphObjectConfigGraph.validate_invocation_value(value)


class ProgramConfigGraphObjectConfigGraphBuildViaProgramConfigGraphInput(BaseModel):
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.object_config_graphs")
    object_config_graph_id: UUID
    key: str | None = Field(default=None)


class ProgramConfigGraphObjectConfigGraphBuildViaProgramConfigGraphOutput(BaseModel):
    value: ProgramConfigGraphObjectConfigGraph


FUNCTIONS = {
    "ProgramConfigGraphObjectConfigGraph": {
        "build_via_program_config_graph": {
            "canonical": {
                "name": "build_via_program_config_graph",
                "description": "Create a deterministic ProgramConfigGraphObjectConfigGraph under this.\n\nContract:\n- Identity is derived from `(program_config_graph_id, object_config_graph_id)`.\n- Constructor is idempotent for the same pair.",
                "is_constructor": True,
            },
            "input": ProgramConfigGraphObjectConfigGraphBuildViaProgramConfigGraphInput,
            "output": ProgramConfigGraphObjectConfigGraphBuildViaProgramConfigGraphOutput,
        },
    },
}

__all__ = [
    "ProgramConfigGraphObjectConfigGraph",
    "ProgramConfigGraphObjectConfigGraphBuildViaProgramConfigGraphInput",
    "ProgramConfigGraphObjectConfigGraphBuildViaProgramConfigGraphOutput",
    "FUNCTIONS",
]
