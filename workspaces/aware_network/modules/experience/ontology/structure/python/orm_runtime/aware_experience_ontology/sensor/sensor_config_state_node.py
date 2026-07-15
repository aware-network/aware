from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.graph.projection.object_projection_graph_node import ObjectProjectionGraphNode


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

    @classmethod
    async def build_via_sensor_config(
        cls, sensor_config_id: UUID, object_projection_graph_node_id: UUID
    ) -> SensorConfigStateNode:
        """Create deterministic SensorConfig observed state-node footprint edge."""

        payload = {
            "sensor_config_id": sensor_config_id,
            "object_projection_graph_node_id": object_projection_graph_node_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sensor_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SensorConfigStateNode):
            return value
        return SensorConfigStateNode.validate_invocation_value(value)


class SensorConfigStateNodeBuildViaSensorConfigInput(BaseModel):
    sensor_config_id: UUID = Field(description="Foreign key for SensorConfig.observed_state_nodes")
    object_projection_graph_node_id: UUID


class SensorConfigStateNodeBuildViaSensorConfigOutput(BaseModel):
    value: SensorConfigStateNode


FUNCTIONS = {
    "SensorConfigStateNode": {
        "build_via_sensor_config": {
            "canonical": {
                "name": "build_via_sensor_config",
                "description": "Create deterministic SensorConfig observed state-node footprint edge.",
                "is_constructor": True,
            },
            "input": SensorConfigStateNodeBuildViaSensorConfigInput,
            "output": SensorConfigStateNodeBuildViaSensorConfigOutput,
        },
    },
}

__all__ = [
    "SensorConfigStateNode",
    "SensorConfigStateNodeBuildViaSensorConfigInput",
    "SensorConfigStateNodeBuildViaSensorConfigOutput",
    "FUNCTIONS",
]
