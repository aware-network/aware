from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_attention_ontology_orm_models.layout.layout_config_section_config import LayoutConfigSectionConfig
    from aware_experience_ontology_orm_models.projection.projection_experience_graph_identity import (
        ProjectionExperienceGraphIdentity,
    )
    from aware_experience_ontology_orm_models.projection.projection_experience_view import ProjectionExperienceView


class ProjectionExperienceSectionGraphBinding(ORMModel):
    """
    ProjectionExperience-owned section graph binding contract.
    Contract:
    - Declares one stable coordination agreement between an Attention layout section,
    one Experience view, and one ProjectionExperienceGraphIdentity.
    - Keeps the graph-occurrence anchor explicit without coupling Interface pane
    mounts to one focused runtime object.
    """

    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None, exclude=True)
    projection_experience_view: ProjectionExperienceView | None = Field(default=None, exclude=True)
    projection_experience_graph_identity: ProjectionExperienceGraphIdentity | None = Field(default=None, exclude=True)

    # Attributes
    binding_key: str
    section_key: str = Field(
        description="Denormalized lookup key derived from the target Attention layout section.\nAuthoritative section topology is `layout_config_section_config`."
    )

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_section_graph_bindings"
    )
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionGraphBinding.layout_config_section_config"
    )
    projection_experience_view_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionGraphBinding.projection_experience_view"
    )
    projection_experience_graph_identity_id: UUID = Field(
        description="Foreign key for ProjectionExperienceSectionGraphBinding.projection_experience_graph_identity"
    )
