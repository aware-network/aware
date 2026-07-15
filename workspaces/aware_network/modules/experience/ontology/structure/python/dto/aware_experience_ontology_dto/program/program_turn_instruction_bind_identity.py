from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_experience_ontology_dto.projection.projection_experience_node_class_identity import (
        ProjectionExperienceNodeClassIdentity,
    )


class ProgramTurnInstructionBindIdentity(BaseModel):
    """
    Canonical node-alias resolution receipt under one ProgramTurnInstructionBind.
    Contract:
    - Freezes bind-time resolution of one ProgramConfig port-node contract to one ClassInstanceIdentity.
    - References graph wiring bridge used for the resolution proof.
    """

    # Relationships
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode | None = Field(
        default=None
    )
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None)
