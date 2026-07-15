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
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph import ObjectProjectionGraph


class ThreadConfigLayoutConfigSection(ORMModel):
    """
    Projection-host placement inside one ThreadConfig LayoutConfig option.
    Contract:
    - Attention owns layout section config.
    - Meta owns ObjectProjectionGraph authority.
    - Experience may later bind views/actions over these declared host slots.
    """

    # Relationships
    layout_config_section_config: LayoutConfigSectionConfig | None = Field(default=None)
    object_projection_graph: ObjectProjectionGraph | None = Field(default=None)

    # Attributes
    key: str | None = Field(
        default=None, description="Optional stable association key under the parent ThreadConfigLayoutConfig."
    )
    position: int | None = Field(default=None, description="Ordering hint within repeated section placements.")
    is_default: bool = Field(
        default=False, description="Marks the preferred/default placement for this layout section."
    )
    narrative: str | None = Field(
        default=None, description="Narrative text for why this projection belongs in the section."
    )
    intent: str | None = Field(default=None, description="Short canonical intent for the section placement.")

    # Foreign Keys
    thread_config_layout_config_id: UUID = Field(description="Foreign key for ThreadConfigLayoutConfig.sections")
    layout_config_section_config_id: UUID = Field(
        description="Foreign key for ThreadConfigLayoutConfigSection.layout_config_section_config"
    )
    object_projection_graph_id: UUID | None = Field(
        default=None, description="Foreign key for ThreadConfigLayoutConfigSection.object_projection_graph"
    )
