from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.actuator.actuator_config_state_node import ActuatorConfigStateNode

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
)
from aware_experience.stable_ids import stable_actuator_config_state_node_id
from aware_meta.runtime.handler_context import current_handler_session
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)

# --- AWARE: USER_IMPORTS END


async def build_via_actuator_config(
    actuator_config_id: UUID, object_projection_graph_node_id: UUID
) -> ActuatorConfigStateNode:
    """
    Create deterministic ActuatorConfig affected state-node footprint edge.
    """

    # --- AWARE: LOGIC START build_via_actuator_config
    normalized_actuator_config_id = as_uuid(
        actuator_config_id,
        field_name="ActuatorConfigStateNode.actuator_config_id",
    )
    normalized_object_projection_graph_node_id = as_uuid(
        object_projection_graph_node_id,
        field_name="ActuatorConfigStateNode.object_projection_graph_node_id",
    )
    state_node_id = stable_actuator_config_state_node_id(
        actuator_config_id=normalized_actuator_config_id,
        object_projection_graph_node_id=normalized_object_projection_graph_node_id,
    )

    session = current_handler_session()
    object_projection_graph_node = session.imap_get(
        ObjectProjectionGraphNode,
        normalized_object_projection_graph_node_id,
    )
    existing = session.imap_get(ActuatorConfigStateNode, state_node_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "actuator_config_id": normalized_actuator_config_id,
                "object_projection_graph_node_id": (normalized_object_projection_graph_node_id),
            },
            label="ActuatorConfigStateNode",
            object_id=state_node_id,
        )
        return existing

    return ActuatorConfigStateNode(
        id=state_node_id,
        actuator_config_id=normalized_actuator_config_id,
        object_projection_graph_node_id=normalized_object_projection_graph_node_id,
        object_projection_graph_node=object_projection_graph_node,
    )
    # --- AWARE: LOGIC END build_via_actuator_config
