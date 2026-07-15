from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.actuator.actuator import Actuator
from aware_experience_ontology.actuator.actuator_config import ActuatorConfig
from aware_experience_ontology.actuator.actuator_config_state_node import ActuatorConfigStateNode
from aware_experience_ontology.actuator.actuator_invocation_action_config import ActuatorInvocationActionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
    optional_token,
    required_token,
    status_token,
)
from aware_experience.stable_ids import stable_actuator_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_affected_state_node(
    actuator_config: ActuatorConfig, object_projection_graph_node_id: UUID
) -> ActuatorConfigStateNode:
    """
    Add one affected Projection node footprint to this Actuator config.

    Contract:
    - The state node is a Meta ObjectProjectionGraphNode portal.
    - This is not a payload schema. Payload DTO contracts resolve through
      the bound ExperienceInvocationActionConfig endpoint only.
    """

    # --- AWARE: LOGIC START add_affected_state_node
    created = await ActuatorConfigStateNode.build_via_actuator_config(
        actuator_config_id=actuator_config.id,
        object_projection_graph_node_id=object_projection_graph_node_id,
    )
    for existing in actuator_config.affected_state_nodes:
        if existing.id == created.id:
            return existing
    actuator_config.affected_state_nodes.append(created)
    return created
    # --- AWARE: LOGIC END add_affected_state_node


async def create_actuator(
    actuator_config: ActuatorConfig, actuator_instance_key: str, external_ref: str | None = None, status: str = "active"
) -> Actuator:
    """
    Create one deterministic Actuator instance under this Actuator config.

    Contract:
    - Config -> Instance is the canonical ownership rail.
    - Parent `ActuatorConfig` scope is propagated by constructor lowering.
    - `actuator_instance_key` identifies this runtime fulfillment.
    """

    # --- AWARE: LOGIC START create_actuator
    normalized_status = status_token(status, default="active")
    created = await Actuator.build_via_actuator_config(
        actuator_config_id=actuator_config.id,
        actuator_instance_key=actuator_instance_key,
        external_ref=external_ref,
        status=normalized_status,
    )
    for existing in actuator_config.actuators:
        if existing.id == created.id:
            return existing
    actuator_config.actuators.append(created)
    return created
    # --- AWARE: LOGIC END create_actuator


async def bind_invocation_action_config(
    actuator_config: ActuatorConfig, experience_invocation_action_config_id: UUID
) -> ActuatorInvocationActionConfig:
    """
    Bind one reusable Experience invocation action config to this Actuator config.

    Contract:
    - `ActuatorConfig` remains the raw actuator capability surface.
    - `ExperienceInvocationActionConfig` remains the shared target metadata.
    - Actuator instances use the matching action config binding when recording
      concrete invocation provenance.
    """

    # --- AWARE: LOGIC START bind_invocation_action_config
    created = await ActuatorInvocationActionConfig.build_via_actuator_config(
        actuator_config_id=actuator_config.id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
    )
    for existing in actuator_config.invocation_action_configs:
        if existing.id == created.id:
            return existing
    actuator_config.invocation_action_configs.append(created)
    return created
    # --- AWARE: LOGIC END bind_invocation_action_config


async def build_via_connector_config(
    connector_config_id: UUID,
    actuator_key: str,
    actuator_kind: str,
    target_ref: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> ActuatorConfig:
    """
    Create one deterministic Actuator config under a ConnectorConfig.

    Contract:
    - Parent `ConnectorConfig` scope is propagated by constructor lowering.
    - `actuator_key` is stable within the Connector config.
    - `actuator_kind` identifies the outbound target/action family.
    """

    # --- AWARE: LOGIC START build_via_connector_config
    normalized_connector_config_id = as_uuid(
        connector_config_id,
        field_name="ActuatorConfig.connector_config_id",
    )
    normalized_actuator_key = required_token(
        actuator_key,
        field_name="ActuatorConfig.actuator_key",
    )
    normalized_actuator_kind = required_token(
        actuator_kind,
        field_name="ActuatorConfig.actuator_kind",
    )
    normalized_target_ref = optional_token(target_ref)
    normalized_label = optional_token(label)
    normalized_description = optional_token(description)
    actuator_config_id = stable_actuator_config_id(
        connector_config_id=normalized_connector_config_id,
        actuator_key=normalized_actuator_key,
    )

    session = current_handler_session()
    existing = session.imap_get(ActuatorConfig, actuator_config_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "connector_config_id": normalized_connector_config_id,
                "actuator_key": normalized_actuator_key,
                "actuator_kind": normalized_actuator_kind,
                "target_ref": normalized_target_ref,
                "label": normalized_label,
                "description": normalized_description,
            },
            label="ActuatorConfig",
            object_id=actuator_config_id,
        )
        return existing

    return ActuatorConfig(
        id=actuator_config_id,
        connector_config_id=normalized_connector_config_id,
        actuator_key=normalized_actuator_key,
        actuator_kind=normalized_actuator_kind,
        target_ref=normalized_target_ref,
        label=normalized_label,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_connector_config
