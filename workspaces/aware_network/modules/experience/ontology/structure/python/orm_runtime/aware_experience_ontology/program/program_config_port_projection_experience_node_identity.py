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
    from aware_experience_ontology.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )


class ProgramConfigPortProjectionExperienceNodeIdentity(ORMModel):
    """
    Port-level ProjectionExperienceNodeIdentity reference edge.
    Contract:
    - Edge is owned by ProgramConfigPortProjectionExperienceNode.
    - References one stable identity contract owned by ProjectionExperienceNode.
    """

    # Relationships
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)

    # Attributes
    key: str

    # Foreign Keys
    program_config_port_projection_experience_node_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramConfigPortProjectionExperienceNode.projection_node_identity"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for ProgramConfigPortProjectionExperienceNodeIdentity.projection_experience_node_identity"
    )

    @classmethod
    async def build_via_program_config_port_projection_experience_node(
        cls,
        program_config_port_projection_experience_node_id: UUID,
        projection_experience_node_identity_id: UUID,
        key: str,
    ) -> ProgramConfigPortProjectionExperienceNodeIdentity:
        """Create deterministic ProgramConfigPortProjectionExperienceNodeIdentity edge."""

        payload = {
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "projection_experience_node_identity_id": projection_experience_node_identity_id,
            "key": key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_config_port_projection_experience_node", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigPortProjectionExperienceNodeIdentity):
            return value
        return ProgramConfigPortProjectionExperienceNodeIdentity.validate_invocation_value(value)


class ProgramConfigPortProjectionExperienceNodeIdentityBuildViaProgramConfigPortProjectionExperienceNodeInput(
    BaseModel
):
    program_config_port_projection_experience_node_id: UUID = Field(
        description="Foreign key for ProgramConfigPortProjectionExperienceNode.projection_node_identity"
    )
    projection_experience_node_identity_id: UUID
    key: str


class ProgramConfigPortProjectionExperienceNodeIdentityBuildViaProgramConfigPortProjectionExperienceNodeOutput(
    BaseModel
):
    value: ProgramConfigPortProjectionExperienceNodeIdentity


FUNCTIONS = {
    "ProgramConfigPortProjectionExperienceNodeIdentity": {
        "build_via_program_config_port_projection_experience_node": {
            "canonical": {
                "name": "build_via_program_config_port_projection_experience_node",
                "description": "Create deterministic ProgramConfigPortProjectionExperienceNodeIdentity edge.",
                "is_constructor": True,
            },
            "input": ProgramConfigPortProjectionExperienceNodeIdentityBuildViaProgramConfigPortProjectionExperienceNodeInput,
            "output": ProgramConfigPortProjectionExperienceNodeIdentityBuildViaProgramConfigPortProjectionExperienceNodeOutput,
        },
    },
}

__all__ = [
    "ProgramConfigPortProjectionExperienceNodeIdentity",
    "ProgramConfigPortProjectionExperienceNodeIdentityBuildViaProgramConfigPortProjectionExperienceNodeInput",
    "ProgramConfigPortProjectionExperienceNodeIdentityBuildViaProgramConfigPortProjectionExperienceNodeOutput",
    "FUNCTIONS",
]
