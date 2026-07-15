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


class SensorConfigStateNode(ORMModel):
    """
    SensorConfig-owned observed state-node footprint.
    Contract:
    - Anchors one Sensor config to one Meta ObjectProjectionGraphNode it
    observes.
    - The linked node gives projection scope and class (`node.class_config`).
    - This is not a payload schema rail.
    """

    # Relationships
    object_projection_graph_node: ObjectProjectionGraphNode | None = Field(default=None)

    # Foreign Keys
    sensor_config_id: UUID = Field(description="Foreign key for SensorConfig.observed_state_nodes")
    object_projection_graph_node_id: UUID = Field(
        description="Foreign key for SensorConfigStateNode.object_projection_graph_node"
    )
