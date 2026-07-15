from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


class ActuatorConfigStateNode(ORMModel):
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

    # Foreign Keys
    actuator_config_id: UUID = Field(description="Foreign key for ActuatorConfig.affected_state_nodes")
    object_projection_graph_node_id: UUID = Field(
        description="Foreign key for ActuatorConfigStateNode.object_projection_graph_node"
    )
