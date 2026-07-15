from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.sensor.sensor_invocation_action import SensorInvocationAction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
)
from aware_experience.stable_ids import stable_sensor_invocation_action_id
from aware_experience_ontology.invocation.experience_invocation_action import (
    ExperienceInvocationAction,
)
from aware_experience_ontology.sensor.sensor_invocation_action_config import (
    SensorInvocationActionConfig,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    sensor_id: UUID, sensor_invocation_action_config_id: UUID, experience_invocation_action_id: UUID
) -> SensorInvocationAction:
    """
    Create one deterministic Sensor provenance bridge under a Sensor.

    Contract:
    - `sensor_id` is explicit provenance for the concrete Sensor instance.
    - `sensor_invocation_action_config` proves the action was exposed by
      the Sensor config.
    - `experience_invocation_action` carries the actual invocation receipt.
    """

    # --- AWARE: LOGIC START build
    normalized_sensor_id = as_uuid(
        sensor_id,
        field_name="SensorInvocationAction.sensor_id",
    )
    normalized_sensor_invocation_action_config_id = as_uuid(
        sensor_invocation_action_config_id,
        field_name="SensorInvocationAction.sensor_invocation_action_config_id",
    )
    normalized_experience_invocation_action_id = as_uuid(
        experience_invocation_action_id,
        field_name="SensorInvocationAction.experience_invocation_action_id",
    )
    action_id = stable_sensor_invocation_action_id(
        sensor_invocation_action_config_id=(normalized_sensor_invocation_action_config_id),
        experience_invocation_action_id=normalized_experience_invocation_action_id,
    )

    session = current_handler_session()
    sensor_invocation_action_config = session.imap_get(
        SensorInvocationActionConfig,
        normalized_sensor_invocation_action_config_id,
    )
    experience_invocation_action = session.imap_get(
        ExperienceInvocationAction,
        normalized_experience_invocation_action_id,
    )
    existing = session.imap_get(SensorInvocationAction, action_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "sensor_id": normalized_sensor_id,
                "sensor_invocation_action_config_id": (normalized_sensor_invocation_action_config_id),
                "experience_invocation_action_id": (normalized_experience_invocation_action_id),
            },
            label="SensorInvocationAction",
            object_id=action_id,
        )
        return existing

    return SensorInvocationAction(
        id=action_id,
        sensor_id=normalized_sensor_id,
        sensor_invocation_action_config_id=(normalized_sensor_invocation_action_config_id),
        experience_invocation_action_id=normalized_experience_invocation_action_id,
        sensor_invocation_action_config=sensor_invocation_action_config,
        experience_invocation_action=experience_invocation_action,
    )
    # --- AWARE: LOGIC END build
