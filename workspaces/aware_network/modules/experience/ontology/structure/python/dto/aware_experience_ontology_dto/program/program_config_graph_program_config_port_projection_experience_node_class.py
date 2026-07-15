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


class ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass(BaseModel):
    """
    Graph-level binding edge for one program port-node contract.
    Contract:
    - Wires one ProgramConfigPortProjectionExperienceNode requirement to one
    shared projection node-class identity bridge.
    - Keeps ProgramConfig pure contract while enabling deterministic runtime resolution.
    """

    # Relationships
    projection_experience_node_class_identity: ProjectionExperienceNodeClassIdentity | None = Field(default=None)
    program_config_port_projection_experience_node: ProgramConfigPortProjectionExperienceNode | None = Field(
        default=None
    )

    # Attributes
    key: str | None = Field(default=None)
