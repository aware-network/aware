from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_interface_ontology_orm_models.interface.pane_config import PaneConfig
    from aware_interface_ontology_orm_models.render.pane_render_node import PaneRenderNode
    from aware_interface_ontology_orm_models.render.pane_renderer_capability_requirement import (
        PaneRendererCapabilityRequirement,
    )
    from aware_meta_ontology_orm_models.class_.class_config import ClassConfig


class PaneRenderSpec(ORMModel):
    # Relationships
    pane_config: PaneConfig | None = Field(default=None)
    nodes: list[PaneRenderNode] = Field(default_factory=list)
    renderer_requirements: list[PaneRendererCapabilityRequirement] = Field(default_factory=list)
    state_model: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    name: str
    spec_version: str
    root_node_key: str
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    description: str | None = Field(default=None)

    # Foreign Keys
    pane_config_id: UUID = Field(description="Foreign key for PaneRenderSpec.pane_config")
    state_model_id: UUID | None = Field(default=None, description="Foreign key for PaneRenderSpec.state_model")
