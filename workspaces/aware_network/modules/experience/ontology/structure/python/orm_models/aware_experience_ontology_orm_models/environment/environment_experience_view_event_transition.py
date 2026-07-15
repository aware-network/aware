from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.environment.environment_experience_event import EnvironmentExperienceEvent
    from aware_experience_ontology_orm_models.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_view import ProjectionExperienceView


class EnvironmentExperienceViewEventTransition(ORMModel):
    """
    Experience-owned View -> Event -> View transition policy.
    Contract:
    - Source view is the focused Experience projection view.
    - Trigger event is the profile-owned Reactivity event binding.
    - Target is the section-graph binding that resolves the next view + graph occurrence
    + Attention layout section.
    - This object never references Attention directly.
    """

    # Relationships
    source_view: ProjectionExperienceView | None = Field(default=None, exclude=True)
    trigger_event: EnvironmentExperienceEvent | None = Field(default=None, exclude=True)
    target_section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None, exclude=True)

    # Attributes
    transition_key: str
    name: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    idempotency_policy: str | None = Field(default=None)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.view_event_transitions"
    )
    source_view_id: UUID = Field(description="Foreign key for EnvironmentExperienceViewEventTransition.source_view")
    trigger_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceViewEventTransition.trigger_event")
    target_section_graph_binding_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceViewEventTransition.target_section_graph_binding"
    )
