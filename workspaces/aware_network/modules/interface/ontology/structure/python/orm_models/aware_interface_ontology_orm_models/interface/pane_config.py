from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience_view import ProjectionExperienceView


class PaneConfig(ORMModel):
    # Relationships
    projection_experience_view: ProjectionExperienceView | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    pane_kind: str
    view_ref: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_view_id: UUID = Field(description="Foreign key for PaneConfig.projection_experience_view")
