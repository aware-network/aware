from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.projection.projection_experience import ProjectionExperience
    from aware_experience_ontology_orm_models.projection.projection_experience_layout_graph_binding import (
        ProjectionExperienceLayoutGraphBinding,
    )


class AppConfigScreenConfig(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None)
    projection_experience_layout_graph_binding: ProjectionExperienceLayoutGraphBinding | None = Field(default=None)

    # Attributes
    screen_key: str

    # Foreign Keys
    app_config_id: UUID = Field(description="Foreign key for AppConfig.screen_configs")
    projection_experience_id: UUID = Field(description="Foreign key for AppConfigScreenConfig.projection_experience")
    projection_experience_layout_graph_binding_id: UUID = Field(
        description="Foreign key for AppConfigScreenConfig.projection_experience_layout_graph_binding"
    )
