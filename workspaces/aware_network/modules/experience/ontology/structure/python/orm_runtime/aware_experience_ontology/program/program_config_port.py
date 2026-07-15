from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramBranchBindingMode

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_experience_ontology.projection.projection_experience import ProjectionExperience


class ProgramConfigPort(ORMModel):
    # Relationships
    projection: ProjectionExperience | None = Field(default=None, exclude=True)
    projection_nodes: list[ProgramConfigPortProjectionExperienceNode] = Field(default_factory=list, exclude=True)

    # Attributes
    key: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    branch_binding_mode: ProgramBranchBindingMode = Field(default=ProgramBranchBindingMode.reference)

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.ports")
    projection_id: UUID = Field(description="Foreign key for ProgramConfigPort.projection")

    async def create_projection_node(
        self, projection_experience_node_id: UUID, key: str
    ) -> ProgramConfigPortProjectionExperienceNode:
        """Attach one ProjectionExperienceNode contract under this ProgramConfigPort."""

        payload = {"projection_experience_node_id": projection_experience_node_id, "key": key}
        result = await invoke_instance(orm_model=self, function_name="create_projection_node", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_port_projection_experience_node import (
            ProgramConfigPortProjectionExperienceNode,
        )

        if isinstance(value, ProgramConfigPortProjectionExperienceNode):
            return value
        return ProgramConfigPortProjectionExperienceNode.validate_invocation_value(value)

    @classmethod
    async def build_via_program_config(
        cls,
        program_config_id: UUID,
        projection_id: UUID,
        key: str | None = None,
        intent: str | None = None,
        branch_binding_mode: ProgramBranchBindingMode = ProgramBranchBindingMode.reference,
    ) -> ProgramConfigPort:
        """Create a deterministic ProgramConfigPort under a ProgramConfig."""

        payload = {
            "program_config_id": program_config_id,
            "projection_id": projection_id,
            "key": key,
            "intent": intent,
            "branch_binding_mode": branch_binding_mode,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigPort):
            return value
        return ProgramConfigPort.validate_invocation_value(value)


class ProgramConfigPortCreateProjectionNodeInput(BaseModel):
    projection_experience_node_id: UUID
    key: str


class ProgramConfigPortCreateProjectionNodeOutput(BaseModel):
    value: ProgramConfigPortProjectionExperienceNode


class ProgramConfigPortBuildViaProgramConfigInput(BaseModel):
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.ports")
    projection_id: UUID
    key: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    branch_binding_mode: ProgramBranchBindingMode = Field(default=ProgramBranchBindingMode.reference)


class ProgramConfigPortBuildViaProgramConfigOutput(BaseModel):
    value: ProgramConfigPort


FUNCTIONS = {
    "ProgramConfigPort": {
        "create_projection_node": {
            "canonical": {
                "name": "create_projection_node",
                "description": "Attach one ProjectionExperienceNode contract under this ProgramConfigPort.",
                "is_constructor": False,
            },
            "input": ProgramConfigPortCreateProjectionNodeInput,
            "output": ProgramConfigPortCreateProjectionNodeOutput,
        },
        "build_via_program_config": {
            "canonical": {
                "name": "build_via_program_config",
                "description": "Create a deterministic ProgramConfigPort under a ProgramConfig.",
                "is_constructor": True,
            },
            "input": ProgramConfigPortBuildViaProgramConfigInput,
            "output": ProgramConfigPortBuildViaProgramConfigOutput,
        },
    },
}

__all__ = [
    "ProgramConfigPort",
    "ProgramConfigPortCreateProjectionNodeInput",
    "ProgramConfigPortCreateProjectionNodeOutput",
    "ProgramConfigPortBuildViaProgramConfigInput",
    "ProgramConfigPortBuildViaProgramConfigOutput",
    "FUNCTIONS",
]
