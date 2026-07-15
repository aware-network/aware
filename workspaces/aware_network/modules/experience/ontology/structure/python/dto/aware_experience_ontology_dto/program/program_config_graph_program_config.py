from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.program_config import ProgramConfig
    from aware_experience_ontology_dto.program.program_config_graph_program_config_port_projection_experience_node_class import (
        ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass,
    )


class ProgramConfigGraphProgramConfig(BaseModel):
    # Relationships
    port_projection_experience_node_classes: list[ProgramConfigGraphProgramConfigPortProjectionExperienceNodeClass] = (
        Field(default_factory=list)
    )
    program_config: ProgramConfig | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
