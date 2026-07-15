from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_node_class_identity import (
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
