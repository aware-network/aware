from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.program_config_graph_object_config_graph import (
        ProgramConfigGraphObjectConfigGraph,
    )
    from aware_experience_ontology_orm_models.program.program_config_graph_program_config import (
        ProgramConfigGraphProgramConfig,
    )
    from aware_experience_ontology_orm_models.program.program_config_graph_projection_experience_oigi import (
        ProgramConfigGraphProjectionExperienceOIGI,
    )


class ProgramConfigGraph(ORMModel):
    """
    Canonical experience-level graph that binds program configs to one meta config graph.
    Contract:
    - This is the Experience bridge between Environment ThreadConfig context
    and Meta structure truth.
    - Branch/identity resolution remains runtime-owned (Thread/Turn/Projection); this object stores declarative config.
    """

    # Relationships
    object_config_graphs: list[ProgramConfigGraphObjectConfigGraph] = Field(default_factory=list, exclude=True)
    program_configs: list[ProgramConfigGraphProgramConfig] = Field(default_factory=list, exclude=True)
    projection_experience_oigis: list[ProgramConfigGraphProjectionExperienceOIGI] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    description: str | None = Field(default=None)
    intent: str | None = Field(default=None)
    key: str
    narrative: str | None = Field(default=None)
    title: str | None = Field(default=None)
