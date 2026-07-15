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
    from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
        ProgramConfigPortProjectionExperienceNodeIdentity,
    )
    from aware_experience_ontology.projection.projection_experience_node import ProjectionExperienceNode


class ProgramConfigPortProjectionExperienceNode(ORMModel):
    """
    Port-level ProjectionExperienceNode reference edge.
    Contract:
    - Port does not declare structural traversal; it references one ProjectionExperienceNode
    owned by ProjectionExperience contracts.
    - Node-level identities are attached under this edge.
    """

    # Relationships
    projection_experience_node: ProjectionExperienceNode | None = Field(default=None, exclude=True)
    projection_node_identity: ProgramConfigPortProjectionExperienceNodeIdentity | None = Field(
        default=None, exclude=True
    )

    # Attributes
    key: str

    # Foreign Keys
    program_config_port_id: UUID = Field(description="Foreign key for ProgramConfigPort.projection_nodes")
    projection_experience_node_id: UUID = Field(
        description="Foreign key for ProgramConfigPortProjectionExperienceNode.projection_experience_node"
    )

    async def create_identity(
        self, projection_experience_node_identity_id: UUID, key: str
    ) -> ProgramConfigPortProjectionExperienceNodeIdentity:
        """Attach one optional ProjectionExperienceNodeIdentity under this port node edge."""

        payload = {"projection_experience_node_identity_id": projection_experience_node_identity_id, "key": key}
        result = await invoke_instance(orm_model=self, function_name="create_identity", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_port_projection_experience_node_identity import (
            ProgramConfigPortProjectionExperienceNodeIdentity,
        )

        if isinstance(value, ProgramConfigPortProjectionExperienceNodeIdentity):
            return value
        return ProgramConfigPortProjectionExperienceNodeIdentity.validate_invocation_value(value)

    @classmethod
    async def build_via_program_config_port(
        cls, program_config_port_id: UUID, projection_experience_node_id: UUID, key: str
    ) -> ProgramConfigPortProjectionExperienceNode:
        """Create deterministic ProgramConfigPortProjectionExperienceNode edge."""

        payload = {
            "program_config_port_id": program_config_port_id,
            "projection_experience_node_id": projection_experience_node_id,
            "key": key,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program_config_port", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigPortProjectionExperienceNode):
            return value
        return ProgramConfigPortProjectionExperienceNode.validate_invocation_value(value)


class ProgramConfigPortProjectionExperienceNodeCreateIdentityInput(BaseModel):
    projection_experience_node_identity_id: UUID
    key: str


class ProgramConfigPortProjectionExperienceNodeCreateIdentityOutput(BaseModel):
    value: ProgramConfigPortProjectionExperienceNodeIdentity


class ProgramConfigPortProjectionExperienceNodeBuildViaProgramConfigPortInput(BaseModel):
    program_config_port_id: UUID = Field(description="Foreign key for ProgramConfigPort.projection_nodes")
    projection_experience_node_id: UUID
    key: str


class ProgramConfigPortProjectionExperienceNodeBuildViaProgramConfigPortOutput(BaseModel):
    value: ProgramConfigPortProjectionExperienceNode


FUNCTIONS = {
    "ProgramConfigPortProjectionExperienceNode": {
        "create_identity": {
            "canonical": {
                "name": "create_identity",
                "description": "Attach one optional ProjectionExperienceNodeIdentity under this port node edge.",
                "is_constructor": False,
            },
            "input": ProgramConfigPortProjectionExperienceNodeCreateIdentityInput,
            "output": ProgramConfigPortProjectionExperienceNodeCreateIdentityOutput,
        },
        "build_via_program_config_port": {
            "canonical": {
                "name": "build_via_program_config_port",
                "description": "Create deterministic ProgramConfigPortProjectionExperienceNode edge.",
                "is_constructor": True,
            },
            "input": ProgramConfigPortProjectionExperienceNodeBuildViaProgramConfigPortInput,
            "output": ProgramConfigPortProjectionExperienceNodeBuildViaProgramConfigPortOutput,
        },
    },
}

__all__ = [
    "ProgramConfigPortProjectionExperienceNode",
    "ProgramConfigPortProjectionExperienceNodeCreateIdentityInput",
    "ProgramConfigPortProjectionExperienceNodeCreateIdentityOutput",
    "ProgramConfigPortProjectionExperienceNodeBuildViaProgramConfigPortInput",
    "ProgramConfigPortProjectionExperienceNodeBuildViaProgramConfigPortOutput",
    "FUNCTIONS",
]
