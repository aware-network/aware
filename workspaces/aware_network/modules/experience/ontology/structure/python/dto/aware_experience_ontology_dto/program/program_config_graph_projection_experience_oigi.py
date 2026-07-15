from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.projection.projection_experience_oigi import ProjectionExperienceOIGI


class ProgramConfigGraphProjectionExperienceOIGI(BaseModel):
    """
    ProgramConfigGraph -> ProjectionExperienceOIGI association edge.
    Contract:
    - Declares which projection/meta topology rail is in scope for this graph.
    - Keeps ProgramConfigGraph independent from Environment bindings.
    """

    # Relationships
    projection_experience_oigi: ProjectionExperienceOIGI | None = Field(default=None)

    # Attributes
    key: str | None = Field(default=None)
