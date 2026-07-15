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

    @classmethod
    async def build_via_actuator_config(
        cls, actuator_config_id: UUID, object_projection_graph_node_id: UUID
    ) -> ActuatorConfigStateNode:
        """Create deterministic ActuatorConfig affected state-node footprint edge."""

        payload = {
            "actuator_config_id": actuator_config_id,
            "object_projection_graph_node_id": object_projection_graph_node_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_actuator_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ActuatorConfigStateNode):
            return value
        return ActuatorConfigStateNode.validate_invocation_value(value)


class ActuatorConfigStateNodeBuildViaActuatorConfigInput(BaseModel):
    actuator_config_id: UUID = Field(description="Foreign key for ActuatorConfig.affected_state_nodes")
    object_projection_graph_node_id: UUID


class ActuatorConfigStateNodeBuildViaActuatorConfigOutput(BaseModel):
    value: ActuatorConfigStateNode


FUNCTIONS = {
    "ActuatorConfigStateNode": {
        "build_via_actuator_config": {
            "canonical": {
                "name": "build_via_actuator_config",
                "description": "Create deterministic ActuatorConfig affected state-node footprint edge.",
                "is_constructor": True,
            },
            "input": ActuatorConfigStateNodeBuildViaActuatorConfigInput,
            "output": ActuatorConfigStateNodeBuildViaActuatorConfigOutput,
        },
    },
}

__all__ = [
    "ActuatorConfigStateNode",
    "ActuatorConfigStateNodeBuildViaActuatorConfigInput",
    "ActuatorConfigStateNodeBuildViaActuatorConfigOutput",
    "FUNCTIONS",
]
