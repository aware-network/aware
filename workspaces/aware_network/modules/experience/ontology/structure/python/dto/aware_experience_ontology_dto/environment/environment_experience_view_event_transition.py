from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.environment.environment_experience_event import EnvironmentExperienceEvent
    from aware_experience_ontology_dto.projection.projection_experience_section_graph_binding import (
        ProjectionExperienceSectionGraphBinding,
    )
    from aware_experience_ontology_dto.projection.projection_experience_view import ProjectionExperienceView


class EnvironmentExperienceViewEventTransition(BaseModel):
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
    source_view: ProjectionExperienceView | None = Field(default=None)
    trigger_event: EnvironmentExperienceEvent | None = Field(default=None)
    target_section_graph_binding: ProjectionExperienceSectionGraphBinding | None = Field(default=None)

    # Attributes
    transition_key: str
    name: str | None = Field(default=None)
    rationale: str | None = Field(default=None)
    idempotency_policy: str | None = Field(default=None)
