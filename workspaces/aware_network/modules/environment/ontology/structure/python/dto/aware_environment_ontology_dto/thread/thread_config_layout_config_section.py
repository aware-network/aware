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
    from aware_meta_ontology_dto.graph.projection.object_projection_graph import ObjectProjectionGraph


class ThreadConfigLayoutConfigSection(BaseModel):
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
