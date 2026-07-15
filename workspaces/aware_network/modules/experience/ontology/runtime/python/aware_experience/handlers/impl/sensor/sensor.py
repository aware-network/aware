from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.sensor.sensor import Sensor

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
from aware_experience.stable_ids import stable_sensor_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_sensor_config(
    sensor_config_id: UUID, sensor_instance_key: str, external_ref: str | None = None, status: str = "active"
) -> Sensor:
    """
    Create one deterministic Sensor instance under a SensorConfig.

    Contract:
    - Parent `SensorConfig` scope is propagated by constructor lowering.
    - `sensor_instance_key` identifies this runtime fulfillment.
    """

    # --- AWARE: LOGIC START build_via_sensor_config
    normalized_sensor_config_id = as_uuid(
        sensor_config_id,
        field_name="Sensor.sensor_config_id",
    )
    normalized_sensor_instance_key = required_token(
        sensor_instance_key,
        field_name="Sensor.sensor_instance_key",
    )
    normalized_external_ref = optional_token(external_ref)
    normalized_status = status_token(status, default="active")
    sensor_id = stable_sensor_id(
        sensor_config_id=normalized_sensor_config_id,
        sensor_instance_key=normalized_sensor_instance_key,
    )

    session = current_handler_session()
    existing = session.imap_get(Sensor, sensor_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "sensor_config_id": normalized_sensor_config_id,
                "sensor_instance_key": normalized_sensor_instance_key,
                "external_ref": normalized_external_ref,
                "status": normalized_status,
            },
            label="Sensor",
            object_id=sensor_id,
        )
        return existing

    return Sensor(
        id=sensor_id,
        sensor_config_id=normalized_sensor_config_id,
        sensor_instance_key=normalized_sensor_instance_key,
        external_ref=normalized_external_ref,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_sensor_config
