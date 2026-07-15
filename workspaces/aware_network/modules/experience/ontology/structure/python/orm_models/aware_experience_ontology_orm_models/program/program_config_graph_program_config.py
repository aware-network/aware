from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config import ProgramConfig
    from aware_experience_ontology_orm_models.program.program_config_graph_program_config_port_projection_experience_node_class import (
        ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass,
    )


class ProgramConfigGraphProgramConfig(ORMModel):
    # Relationships
    port_projection_experience_node_classes: list[ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass] = (
        Field(default_factory=list, exclude=True)
    )
    program_config: ProgramConfig | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.program_configs")
    program_config_id: UUID = Field(description="Foreign key for ProgramConfigGraphProgramConfig.program_config")
