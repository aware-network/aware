from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.program.program_enums import ProgramBranchBindingMode

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_port_projection_experience_node import (
        ProgramConfigPortProjectionExperienceNode,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience import ProjectionExperience


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
