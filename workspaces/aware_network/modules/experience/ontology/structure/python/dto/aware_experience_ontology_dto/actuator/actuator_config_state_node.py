from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ActuatorConfigStateNode(BaseModel):
    """
    ActuatorConfig-owned affected state-node footprint.
    Contract:
    - Anchors one Actuator config to one Meta ObjectProjectionGraphNode it can
    affect.
    - The linked node gives projection scope and class (`node.class_config`).
    - This is not a payload schema rail.
    """

    # Relationships
    object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None)
