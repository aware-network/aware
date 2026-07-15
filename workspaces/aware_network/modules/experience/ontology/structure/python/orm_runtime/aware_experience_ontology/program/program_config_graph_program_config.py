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
    from aware_experience_ontology.program.program_config import ProgramConfig
    from aware_experience_ontology.program.program_config_graph_program_config_port_projection_experience_node_class import (
        ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass,
    )


class ProgramConfigGraphProgramConfig(ORMModel):
    # Relationships
    port_projection_experience_node_classes: list[ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass] = (
        Field(default_factory=list, exclude=True)
    )
    program_config: ProgramConfig | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.program_configs")
    program_config_id: UUID = Field(description="Foreign key for ProgramConfigGraphProgramConfig.program_config")

    async def add_port_projection_experience_node_class(
        self,
        program_config_port_projection_experience_node_id: UUID,
        projection_experience_node_class_identity_id: UUID,
        key: str | None = None,
    ) -> ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass:
        """
        Attach one graph-level wiring edge from program port-node contract to shared projection node-class
        identity.
        """

        payload = {
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "projection_experience_node_class_identity_id": projection_experience_node_class_identity_id,
            "key": key,
        }
        result = await invoke_instance(
            orm_model=self, function_name="add_port_projection_experience_node_class", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_graph_program_config_port_projection_experience_node_class import (
            ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass,
        )

        if isinstance(value, ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass):
            return value
        return ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.validate_invocation_value(value)

    @classmethod
    async def build_via_program_config_graph(
        cls, program_config_graph_id: UUID, program_config_id: UUID, key: str | None = None
    ) -> ProgramConfigGraphProgramConfig:
        """
        Create a deterministic ProgramConfigGraphProgramConfig under a ProgramConfigGraph.

        Contract:
        - Parent graph context (`program_config_graph_id`) is injected by parent-edge lowering.
        - Identity is derived from `(program_config_graph_id, program_config_id)`.
        """

        payload = {
            "program_config_graph_id": program_config_graph_id,
            "program_config_id": program_config_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_config_graph", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigGraphProgramConfig):
            return value
        return ProgramConfigGraphProgramConfig.validate_invocation_value(value)


class ProgramConfigGraphProgramConfigAddPortProjectionExperienceNodeClassInput(BaseModel):
    program_config_port_projection_experience_node_id: UUID
    projection_experience_node_class_identity_id: UUID
    key: str | None = Field(default=None)


class ProgramConfigGraphProgramConfigAddPortProjectionExperienceNodeClassOutput(BaseModel):
    value: ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass


class ProgramConfigGraphProgramConfigBuildViaProgramConfigGraphInput(BaseModel):
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.program_configs")
    program_config_id: UUID
    key: str | None = Field(default=None)


class ProgramConfigGraphProgramConfigBuildViaProgramConfigGraphOutput(BaseModel):
    value: ProgramConfigGraphProgramConfig


FUNCTIONS = {
    "ProgramConfigGraphProgramConfig": {
        "add_port_projection_experience_node_class": {
            "canonical": {
                "name": "add_port_projection_experience_node_class",
                "description": "Attach one graph-level wiring edge from program port-node contract to shared projection node-class identity.",
                "is_constructor": False,
            },
            "input": ProgramConfigGraphProgramConfigAddPortProjectionExperienceNodeClassInput,
            "output": ProgramConfigGraphProgramConfigAddPortProjectionExperienceNodeClassOutput,
        },
        "build_via_program_config_graph": {
            "canonical": {
                "name": "build_via_program_config_graph",
                "description": "Create a deterministic ProgramConfigGraphProgramConfig under a ProgramConfigGraph.\n\nContract:\n- Parent graph context (`program_config_graph_id`) is injected by parent-edge lowering.\n- Identity is derived from `(program_config_graph_id, program_config_id)`.",
                "is_constructor": True,
            },
            "input": ProgramConfigGraphProgramConfigBuildViaProgramConfigGraphInput,
            "output": ProgramConfigGraphProgramConfigBuildViaProgramConfigGraphOutput,
        },
    },
}

__all__ = [
    "ProgramConfigGraphProgramConfig",
    "ProgramConfigGraphProgramConfigAddPortProjectionExperienceNodeClassInput",
    "ProgramConfigGraphProgramConfigAddPortProjectionExperienceNodeClassOutput",
    "ProgramConfigGraphProgramConfigBuildViaProgramConfigGraphInput",
    "ProgramConfigGraphProgramConfigBuildViaProgramConfigGraphOutput",
    "FUNCTIONS",
]
