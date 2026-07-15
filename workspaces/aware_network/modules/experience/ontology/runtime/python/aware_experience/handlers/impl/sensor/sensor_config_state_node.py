from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.sensor.sensor_config_state_node import SensorConfigStateNode

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
)
from aware_experience.stable_ids import stable_sensor_config_state_node_id
from aware_meta.runtime.handler_context import current_handler_session
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)

# --- AWARE: USER_IMPORTS END


async def build_via_sensor_config(
    sensor_config_id: UUID, object_projection_graph_node_id: UUID
) -> SensorConfigStateNode:
    """
    Create deterministic SensorConfig observed state-node footprint edge.
    """

    # --- AWARE: LOGIC START build_via_sensor_config
    normalized_sensor_config_id = as_uuid(
        sensor_config_id,
        field_name="SensorConfigStateNode.sensor_config_id",
    )
    normalized_object_projection_graph_node_id = as_uuid(
        object_projection_graph_node_id,
        field_name="SensorConfigStateNode.object_projection_graph_node_id",
    )
    state_node_id = stable_sensor_config_state_node_id(
        sensor_config_id=normalized_sensor_config_id,
        object_projection_graph_node_id=normalized_object_projection_graph_node_id,
    )

    session = current_handler_session()
    object_projection_graph_node = session.imap_get(
        ObjectProjectionGraphNode,
        normalized_object_projection_graph_node_id,
    )
    existing = session.imap_get(SensorConfigStateNode, state_node_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "sensor_config_id": normalized_sensor_config_id,
                "object_projection_graph_node_id": (normalized_object_projection_graph_node_id),
            },
            label="SensorConfigStateNode",
            object_id=state_node_id,
        )
        return existing

    return SensorConfigStateNode(
        id=state_node_id,
        sensor_config_id=normalized_sensor_config_id,
        object_projection_graph_node_id=normalized_object_projection_graph_node_id,
        object_projection_graph_node=object_projection_graph_node,
    )
    # --- AWARE: LOGIC END build_via_sensor_config
