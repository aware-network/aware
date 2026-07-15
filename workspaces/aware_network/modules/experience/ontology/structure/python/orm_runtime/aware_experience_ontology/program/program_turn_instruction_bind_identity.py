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


class ProgramTurnInstructionBindIdentity(ORMModel):
    """
    Canonical node-alias resolution receipt under one ProgramTurnInstructionBind.
    Contract:
    - Freezes bind-time resolution of one ProgramConfig port-node contract to one ClassInstanceIdentity.
    - References graph wiring bridge used for the resolution proof.
    """

    # Relationships
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode | None = Field(
        default=None, exclude=True
    )
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(
        default=None, exclude=True
    )

    # Foreign Keys
    program_turn_instruction_bind_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionBind.resolved_node_identities"
    )
    program_config_port_projection_experience_node_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionBindIdentity.program_config_port_projection_experience_node"
    )
    projection_experience_node_class_identity_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionBindIdentity.projection_experience_node_class_identity"
    )

    @classmethod
    async def build_via_program_turn_instruction_bind(
        cls,
        program_turn_instruction_bind_id: UUID,
        program_config_port_projection_experience_node_id: UUID,
        projection_experience_node_class_identity_id: UUID,
    ) -> ProgramTurnInstructionBindIdentity:
        """Create deterministic ProgramTurnInstructionBindIdentity under ProgramTurnInstructionBind."""

        payload = {
            "program_turn_instruction_bind_id": program_turn_instruction_bind_id,
            "program_config_port_projection_experience_node_id": program_config_port_projection_experience_node_id,
            "projection_experience_node_class_identity_id": projection_experience_node_class_identity_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_turn_instruction_bind", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurnInstructionBindIdentity):
            return value
        return ProgramTurnInstructionBindIdentity.validate_invocation_value(value)


class ProgramTurnInstructionBindIdentityBuildViaProgramTurnInstructionBindInput(BaseModel):
    program_turn_instruction_bind_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionBind.resolved_node_identities"
    )
    program_config_port_projection_experience_node_id: UUID
    projection_experience_node_class_identity_id: UUID


class ProgramTurnInstructionBindIdentityBuildViaProgramTurnInstructionBindOutput(BaseModel):
    value: ProgramTurnInstructionBindIdentity


FUNCTIONS = {
    "ProgramTurnInstructionBindIdentity": {
        "build_via_program_turn_instruction_bind": {
            "canonical": {
                "name": "build_via_program_turn_instruction_bind",
                "description": "Create deterministic ProgramTurnInstructionBindIdentity under ProgramTurnInstructionBind.",
                "is_constructor": True,
            },
            "input": ProgramTurnInstructionBindIdentityBuildViaProgramTurnInstructionBindInput,
            "output": ProgramTurnInstructionBindIdentityBuildViaProgramTurnInstructionBindOutput,
        },
    },
}

__all__ = [
    "ProgramTurnInstructionBindIdentity",
    "ProgramTurnInstructionBindIdentityBuildViaProgramTurnInstructionBindInput",
    "ProgramTurnInstructionBindIdentityBuildViaProgramTurnInstructionBindOutput",
    "FUNCTIONS",
]
