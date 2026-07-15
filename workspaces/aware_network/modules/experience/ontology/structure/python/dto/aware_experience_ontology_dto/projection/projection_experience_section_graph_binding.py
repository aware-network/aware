from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_attention_ontology_dto.layout.layout_config_section_config import LayoutConfigSectionConfig
    from aware_experience_ontology_dto.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )
    from aware_experience_ontology_dto.projection.projection_experience_view import ProjectionExperienceView


class ProjectionExperienceSectionGraphBinding(BaseModel):
    """
    ProjectionExperience-owned section graph binding contract.
    Contract:
    - Declares one stable coordination agreement between an Attention layout section,
    one Experience view, and one ProjectionExperienceGraphIdentity.
    - Keeps the graph-occurrence anchor explicit without coupling Interface pane
    mounts to one focused runtime object.
    """

    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None)
    projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(default=None)

    # Attributes
    binding_key: str
    section_key: str = Field(
        description="Denormalized lookup key derived from the target Attention layout section.\nAuthoritative section topology is `layout_config_section_config`."
    )
