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
    from aware_experience_ontology.program.program_config_graph_object_config_graph import (
        ProgramConfigGraphObjectConfigGraph,
    )
    from aware_experience_ontology.program.program_config_graph_program_config import ProgramConfigGraphProgramConfig
    from aware_experience_ontology.program.program_config_graph_projection_experience_oigi import (
        ProgramConfigGraphProjectionExperienceOIGI,
    )


class ProgramConfigGraph(ORMModel):
    """
    Canonical experience-level graph that binds program configs to one meta config graph.
    Contract:
    - This is the Experience bridge between Environment ThreadConfig context
    and Meta structure truth.
    - Branch/identity resolution remains runtime-owned (Thread/Turn/Projection); this object stores declarative config.
    """

    # Relationships
    object_config_graphs: list[ProgramConfigGraphObjectConfigGraph] = Field(default_factory=list, exclude=True)
    program_configs: list[ProgramConfigGraphProgramConfig] = Field(default_factory=list, exclude=True)
    projection_experience_oigis: list[ProgramConfigGraphProjectionExperienceOIGI] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)

    @classmethod
    async def build(
        cls,
        key: str,
        thread_config_id: UUID,
        object_config_graph_id: UUID,
        title: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
        intent: str | None = None,
    ) -> ProgramConfigGraph:
        """
        Create a deterministic ProgramConfigGraph bound to one Environment ThreadConfig and one
        ObjectConfigGraph.

        Contract:
        - Identity is derived from class key `key`.
        - Constructor is idempotent for the same key.
        """

        payload = {
            "key": key,
            "thread_config_id": thread_config_id,
            "object_config_graph_id": object_config_graph_id,
            "title": title,
            "description": description,
            "narrative": narrative,
            "intent": intent,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigGraph):
            return value
        return ProgramConfigGraph.validate_invocation_value(value)

    async def add_program_config(
        self, program_config_id: UUID, key: str | None = None
    ) -> ProgramConfigGraphProgramConfig:
        """
        Link one existing ProgramConfig under this ProgramConfigGraph.

        Contract:
        - Association identity is deterministic from `(program_config_graph_id, program_config_id)`.
        - ProgramConfig creation is graph-agnostic and happens outside this edge API.
        """

        payload = {"program_config_id": program_config_id, "key": key}
        result = await invoke_instance(orm_model=self, function_name="add_program_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_graph_program_config import (
            ProgramConfigGraphProgramConfig,
        )

        if isinstance(value, ProgramConfigGraphProgramConfig):
            return value
        return ProgramConfigGraphProgramConfig.validate_invocation_value(value)

    async def add_projection_experience_oigi(
        self, projection_experience_oigi_id: UUID, key: str | None = None
    ) -> ProgramConfigGraphProjectionExperienceOIGI:
        """Link one ProjectionExperienceOIGI under this ProgramConfigGraph."""

        payload = {"projection_experience_oigi_id": projection_experience_oigi_id, "key": key}
        result = await invoke_instance(orm_model=self, function_name="add_projection_experience_oigi", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_graph_projection_experience_oigi import (
            ProgramConfigGraphProjectionExperienceOIGI,
        )

        if isinstance(value, ProgramConfigGraphProjectionExperienceOIGI):
            return value
        return ProgramConfigGraphProjectionExperienceOIGI.validate_invocation_value(value)


class ProgramConfigGraphBuildInput(BaseModel):
    key: str
    thread_config_id: UUID
    object_config_graph_id: UUID
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    narrative: str | None = Field(default=None)
    intent: str | None = Field(default=None)


class ProgramConfigGraphBuildOutput(BaseModel):
    value: ProgramConfigGraph


class ProgramConfigGraphAddProgramConfigInput(BaseModel):
    program_config_id: UUID
    key: str | None = Field(default=None)


class ProgramConfigGraphAddProgramConfigOutput(BaseModel):
    value: ProgramConfigGraphProgramConfig


class ProgramConfigGraphAddProjectionExperienceOigiInput(BaseModel):
    projection_experience_oigi_id: UUID
    key: str | None = Field(default=None)


class ProgramConfigGraphAddProjectionExperienceOigiOutput(BaseModel):
    value: ProgramConfigGraphProjectionExperienceOIGI


FUNCTIONS = {
    "ProgramConfigGraph": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create a deterministic ProgramConfigGraph bound to one Environment ThreadConfig and one ObjectConfigGraph.\n\nContract:\n- Identity is derived from class key `key`.\n- Constructor is idempotent for the same key.",
                "is_constructor": True,
            },
            "input": ProgramConfigGraphBuildInput,
            "output": ProgramConfigGraphBuildOutput,
        },
        "add_program_config": {
            "canonical": {
                "name": "add_program_config",
                "description": "Link one existing ProgramConfig under this ProgramConfigGraph.\n\nContract:\n- Association identity is deterministic from `(program_config_graph_id, program_config_id)`.\n- ProgramConfig creation is graph-agnostic and happens outside this edge API.",
                "is_constructor": False,
            },
            "input": ProgramConfigGraphAddProgramConfigInput,
            "output": ProgramConfigGraphAddProgramConfigOutput,
        },
        "add_projection_experience_oigi": {
            "canonical": {
                "name": "add_projection_experience_oigi",
                "description": "Link one ProjectionExperienceOIGI under this ProgramConfigGraph.",
                "is_constructor": False,
            },
            "input": ProgramConfigGraphAddProjectionExperienceOigiInput,
            "output": ProgramConfigGraphAddProjectionExperienceOigiOutput,
        },
    },
}

__all__ = [
    "ProgramConfigGraph",
    "ProgramConfigGraphBuildInput",
    "ProgramConfigGraphBuildOutput",
    "ProgramConfigGraphAddProgramConfigInput",
    "ProgramConfigGraphAddProgramConfigOutput",
    "ProgramConfigGraphAddProjectionExperienceOigiInput",
    "ProgramConfigGraphAddProjectionExperienceOigiOutput",
    "FUNCTIONS",
]
