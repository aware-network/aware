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
    from aware_experience_ontology.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_experience_ontology.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )


class ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass(ORMModel):
    """
    Graph-level binding edge for one program port-node contract.
    Contract:
    - Wires one ProgramConfigPortProjectionExperienceNode requirement to one
    shared projection node-class identity bridge.
    - Keeps ProgramConfig pure contract while enabling deterministic runtime resolution.
    """

    # Relationships
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(
        default=None, exclude=True
    )
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_program_config_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProgramConfig.port_projection_experience_node_classes"
    )
    projection_experience_node_class_identity_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.projection_experience_node_class_identity"
    )
    program_config_port_projection_experience_node_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.program_config_port_projection_experience_node"
    )

    @classmethod
    async def build_via_program_config_graph_program_config(
        cls,
        program_config_graph_program_config_id: UUID,
        program_config_port_projection_experience_node_id: UUID,
        projection_experience_node_class_identity_id: UUID,
        key: str | None = None,
    ) -> ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass:
        """
        Create deterministic ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass
        under ProgramConfigGraphProgramConfig.
        """

        payload = {
            "program_config_graph_program_config_id": program_config_graph_program_config_id,
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "projection_experience_node_class_identity_id": projection_experience_node_class_identity_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_config_graph_program_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass):
            return value
        return ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass.validate_invocation_value(value)


class ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClassBuildViaProgramConfigGraphProgramConfigInput(
    BaseModel
):
    program_config_graph_program_config_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProgramConfig.port_projection_experience_node_classes"
    )
    program_config_port_projection_experience_node_id: UUID
    projection_experience_node_class_identity_id: UUID
    key: str | None = Field(default=None)


class ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClassBuildViaProgramConfigGraphProgramConfigOutput(
    BaseModel
):
    value: ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass


FUNCTIONS = {
    "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass": {
        "build_via_program_config_graph_program_config": {
            "canonical": {
                "name": "build_via_program_config_graph_program_config",
                "description": "Create deterministic ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass\nunder ProgramConfigGraphProgramConfig.",
                "is_constructor": True,
            },
            "input": ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClassBuildViaProgramConfigGraphProgramConfigInput,
            "output": ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClassBuildViaProgramConfigGraphProgramConfigOutput,
        },
    },
}

__all__ = [
    "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass",
    "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClassBuildViaProgramConfigGraphProgramConfigInput",
    "ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClassBuildViaProgramConfigGraphProgramConfigOutput",
    "FUNCTIONS",
]
