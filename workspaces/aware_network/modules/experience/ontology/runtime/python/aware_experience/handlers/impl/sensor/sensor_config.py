from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.sensor.sensor import Sensor
from aware_experience_ontology.sensor.sensor_config import SensorConfig
from aware_experience_ontology.sensor.sensor_config_state_node import SensorConfigStateNode
from aware_experience_ontology.sensor.sensor_invocation_action_config import SensorInvocationActionConfig

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
from aware_experience.stable_ids import stable_sensor_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_observed_state_node(
    sensor_config: SensorConfig, object_projection_graph_node_id: UUID
) -> SensorConfigStateNode:
    """
    Add one observed Projection node footprint to this Sensor config.

    Contract:
    - The state node is a Meta ObjectProjectionGraphNode portal.
    - This is not a payload schema. Payload DTO contracts resolve through
      the bound ExperienceInvocationActionConfig endpoint only.
    """

    # --- AWARE: LOGIC START add_observed_state_node
    created = await SensorConfigStateNode.build_via_sensor_config(
        sensor_config_id=sensor_config.id,
        object_projection_graph_node_id=object_projection_graph_node_id,
    )
    for existing in sensor_config.observed_state_nodes:
        if existing.id == created.id:
            return existing
    sensor_config.observed_state_nodes.append(created)
    return created
    # --- AWARE: LOGIC END add_observed_state_node


async def create_sensor(
    sensor_config: SensorConfig, sensor_instance_key: str, external_ref: str | None = None, status: str = "active"
) -> Sensor:
    """
    Create one deterministic Sensor instance under this Sensor config.

    Contract:
    - Config -> Instance is the canonical ownership rail.
    - Parent `SensorConfig` scope is propagated by constructor lowering.
    - `sensor_instance_key` identifies this runtime fulfillment.
    """

    # --- AWARE: LOGIC START create_sensor
    normalized_status = status_token(status, default="active")
    created = await Sensor.build_via_sensor_config(
        sensor_config_id=sensor_config.id,
        sensor_instance_key=sensor_instance_key,
        external_ref=external_ref,
        status=normalized_status,
    )
    for existing in sensor_config.sensors:
        if existing.id == created.id:
            return existing
    sensor_config.sensors.append(created)
    return created
    # --- AWARE: LOGIC END create_sensor


async def bind_invocation_action_config(
    sensor_config: SensorConfig, experience_invocation_action_config_id: UUID
) -> SensorInvocationActionConfig:
    """
    Bind one reusable Experience invocation action config to this Sensor config.

    Contract:
    - `SensorConfig` remains the raw sensor capability surface.
    - `ExperienceInvocationActionConfig` remains the shared target metadata.
    - Sensor instances use the matching action config binding when recording
      concrete invocation provenance.
    """

    # --- AWARE: LOGIC START bind_invocation_action_config
    created = await SensorInvocationActionConfig.build_via_sensor_config(
        sensor_config_id=sensor_config.id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
    )
    for existing in sensor_config.invocation_action_configs:
        if existing.id == created.id:
            return existing
    sensor_config.invocation_action_configs.append(created)
    return created
    # --- AWARE: LOGIC END bind_invocation_action_config


async def build_via_connector_config(
    connector_config_id: UUID,
    sensor_key: str,
    sensor_kind: str,
    source_ref: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> SensorConfig:
    """
    Create one deterministic Sensor config under a ConnectorConfig.

    Contract:
    - Parent `ConnectorConfig` scope is propagated by constructor lowering.
    - `sensor_key` is stable within the Connector config.
    - `sensor_kind` identifies the inbound event/source family.
    """

    # --- AWARE: LOGIC START build_via_connector_config
    normalized_connector_config_id = as_uuid(
        connector_config_id,
        field_name="SensorConfig.connector_config_id",
    )
    normalized_sensor_key = required_token(
        sensor_key,
        field_name="SensorConfig.sensor_key",
    )
    normalized_sensor_kind = required_token(
        sensor_kind,
        field_name="SensorConfig.sensor_kind",
    )
    normalized_source_ref = optional_token(source_ref)
    normalized_label = optional_token(label)
    normalized_description = optional_token(description)
    sensor_config_id = stable_sensor_config_id(
        connector_config_id=normalized_connector_config_id,
        sensor_key=normalized_sensor_key,
    )

    session = current_handler_session()
    existing = session.imap_get(SensorConfig, sensor_config_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "connector_config_id": normalized_connector_config_id,
                "sensor_key": normalized_sensor_key,
                "sensor_kind": normalized_sensor_kind,
                "source_ref": normalized_source_ref,
                "label": normalized_label,
                "description": normalized_description,
            },
            label="SensorConfig",
            object_id=sensor_config_id,
        )
        return existing

    return SensorConfig(
        id=sensor_config_id,
        connector_config_id=normalized_connector_config_id,
        sensor_key=normalized_sensor_key,
        sensor_kind=normalized_sensor_kind,
        source_ref=normalized_source_ref,
        label=normalized_label,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_connector_config
