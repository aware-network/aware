from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_oigi import ProjectionExperienceOIGI


class ProgramConfigGraphProjectionExperienceOIGI(ORMModel):
    """
    ProgramConfigGraph -> ProjectionExperienceOIGI association edge.
    Contract:
    - Declares which projection/meta topology rail is in scope for this graph.
    - Keeps ProgramConfigGraph independent from Environment bindings.
    """

    # Relationships
    projection_experience_oigi: ProjectionExperienceOIGI | None = Field(default=None, exclude=True)

    # Attributes
    key: str | None = Field(default=None)

    # Foreign Keys
    program_config_graph_id: UUID = Field(description="Foreign key for ProgramConfigGraph.projection_experience_oigis")
    projection_experience_oigi_id: UUID = Field(
        description="Foreign key for ProgramConfigGraphProjectionExperienceOIGI.projection_experience_oigi"
    )
