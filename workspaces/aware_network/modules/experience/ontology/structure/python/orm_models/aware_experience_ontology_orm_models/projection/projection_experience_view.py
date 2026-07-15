from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_view import ApiView
    from aware_experience_ontology_orm_models.projection.projection_experience_view_instance import (
        ProjectionExperienceViewInstance,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_view_invocation_action_config import (
        ProjectionExperienceViewInvocationActionConfig,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_view_state_provider import (
        ProjectionExperienceViewStateProvider,
    )


class ProjectionExperienceView(ORMModel):
    # Relationships
    api_view: ApiView | None = Field(
        default=None, description="API-owned lower view-state contract this Experience view exposes."
    )
    invocation_action_configs: list[ProjectionExperienceViewInvocationActionConfig] = Field(
        default_factory=list, description="Experience-owned invocation actions that panes may render and dispatch."
    )
    view_instances: list[ProjectionExperienceViewInstance] = Field(
        default_factory=list, description="Concrete rendered/view-state instances of this view."
    )
    state_providers: list[ProjectionExperienceViewStateProvider] = Field(
        default_factory=list,
        exclude=True,
        description="Canonical provider binding that turns host-owned materialized state into this view state.",
    )

    # Attributes
    name: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_views"
    )
    api_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.api_view")
