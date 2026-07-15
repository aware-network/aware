from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology Dto
from aware_experience_ontology_dto.program.program_enums import ProgramBranchBindingMode

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_experience_ontology_dto.projection.projection_experience import ProjectionExperience


class ProgramConfigPort(BaseModel):
    # Relationships
    projection: ProjectionExperience | None = Field(default=None)
    projection_nodes: list[ProgramConfigPortProjectionExperienceNode] = Field(default_factory=list)

    # Attributes
    key: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    branch_binding_mode: ProgramBranchBindingMode = Field(default=ProgramBranchBindingMode.reference)
