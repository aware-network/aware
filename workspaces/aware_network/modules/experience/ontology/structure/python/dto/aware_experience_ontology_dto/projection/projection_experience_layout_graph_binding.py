from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_config import LayoutConfig
    from aware_experience_ontology_dto.projection.projection_experience_layout_section_graph_binding import (
        ProjectionExperienceLayoutSectionGraphBinding,
    )


class ProjectionExperienceLayoutGraphBinding(BaseModel):
    """
    ProjectionExperience-owned layout graph binding contract.
    Contract:
    - Declares one stable coordination agreement between an Attention layout and
    a set of Experience-owned section graph bindings.
    - Keeps apps and Interface packages from selecting section bindings or pane
    defaults directly.
    - Does not own ordering or runtime activation; Attention layout topology and
    sessions own those resolutions.
    """

    # Relationships
    layout_config: LayoutConfig | None = Field(default=None)
    layout_section_graph_bindings: list[ProjectionExperienceLayoutSectionGraphBinding] = Field(default_factory=list)

    # Attributes
    binding_key: str
