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
    from aware_experience_ontology.projection.projection_experience_oigi import ProjectionExperienceOIGI


class ProgramConfigGraphProjectionExperienceOIGI(ORMModel):
    """
    ProgramConfigGraph -> ProjectionExperienceOIGI association edge.
    Contract:
    - Declares which projection/meta topology rail is in scope for this graph.
    - Keeps ProgramConfigGraph independent from Environment bindings.
    """

    # Relationships
    projection_experience_oigi: ProjectionExperienceOIGI | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.projection_experience_oigis")
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProjectionExperienceOIGI.projection_experience_oigi"
    )

    @classmethod
    async def build_via_program_config_graph(
        cls, program_config_graph_id: UUID, projection_experience_oigi_id: UUID, key: str | None = None
    ) -> ProgramConfigGraphProjectionExperienceOIGI:
        """Create deterministic ProgramConfigGraphProjectionExperienceOIGI edge."""

        payload = {
            "program_config_graph_id": program_config_graph_id,
            "projection_experience_oigi_id": projection_experience_oigi_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_config_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigGraphProjectionExperienceOIGI):
            return value
        return ProgramConfigGraphProjectionExperienceOIGI.validate_invocation_value(value)


class ProgramConfigGraphProjectionExperienceOIGIBuildViaProgramConfigGraphInput(BaseModel):
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.projection_experience_oigis")
    projection_experience_oigi_id: UUID
    key: str | None = Field(default=None)


class ProgramConfigGraphProjectionExperienceOIGIBuildViaProgramConfigGraphOutput(BaseModel):
    value: ProgramConfigGraphProjectionExperienceOIGI


FUNCTIONS = {
    "ProgramConfigGraphProjectionExperienceOIGI": {
        "build_via_program_config_graph": {
            "canonical": {
                "name": "build_via_program_config_graph",
                "description": "Create deterministic ProgramConfigGraphProjectionExperienceOIGI edge.",
                "is_constructor": True,
            },
            "input": ProgramConfigGraphProjectionExperienceOIGIBuildViaProgramConfigGraphInput,
            "output": ProgramConfigGraphProjectionExperienceOIGIBuildViaProgramConfigGraphOutput,
        },
    },
}

__all__ = [
    "ProgramConfigGraphProjectionExperienceOIGI",
    "ProgramConfigGraphProjectionExperienceOIGIBuildViaProgramConfigGraphInput",
    "ProgramConfigGraphProjectionExperienceOIGIBuildViaProgramConfigGraphOutput",
    "FUNCTIONS",
]
