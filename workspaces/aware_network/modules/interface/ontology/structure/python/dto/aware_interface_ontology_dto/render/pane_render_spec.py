from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_interface_ontology_dto.interface.pane_config import PaneConfig
    from aware_interface_ontology_dto.render.pane_render_node import PaneRenderNode
    from aware_interface_ontology_dto.render.pane_renderer_capability_requirement import (
        PaneRendererCapabilityRequirement,
    )
    from aware_meta_ontology_dto.class_.class_config import ClassConfig


class PaneRenderSpec(BaseModel):
    # Relationships
    pane_config: PaneConfig | None = Field(default=None)
    nodes: list[PaneRenderNode] = Field(default_factory=list)
    renderer_requirements: list[PaneRendererCapabilityRequirement] = Field(default_factory=list)
    state_model: ClassConfig | None = Field(default=None)

    # Attributes
    name: str
    spec_version: str
    root_node_key: str
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    description: str | None = Field(default=None)
