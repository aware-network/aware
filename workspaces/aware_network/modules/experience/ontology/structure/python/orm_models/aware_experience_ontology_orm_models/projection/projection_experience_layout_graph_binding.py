from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_config import LayoutConfig
    from aware_experience_ontology_orm_models.projection.projection_experience_layout_section_graph_binding import (
        ProjectionExperienceLayoutSectionGraphBinding,
    )


class ProjectionExperienceLayoutGraphBinding(ORMModel):
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
    layout_config: LayoutConfig | None = Field(default=None, exclude=True)
    layout_section_graph_bindings: list[ProjectionExperienceLayoutSectionGraphBinding] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    binding_key: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_layout_graph_bindings"
    )
    layout_config_id: UUID = Field(description="Foreign key for ProjectionExperienceLayoutGraphBinding.layout_config")
