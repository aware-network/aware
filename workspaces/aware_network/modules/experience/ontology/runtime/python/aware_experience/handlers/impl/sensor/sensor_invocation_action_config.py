from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
from aware_experience_ontology.sensor.sensor_invocation_action_config import SensorInvocationActionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
)
from aware_experience.stable_ids import stable_sensor_invocation_action_config_id
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def record_invocation(
    sensor_invocation_action_config: SensorInvocationActionConfig,
    invocation_key: UUID,
    actor_id: UUID | None = None,
    api_call_id: UUID | None = None,
    sdk_operation_call_id: UUID | None = None,
    request_ref: str | None = None,
    receipt_ref: str | None = None,
    status: str = "pending",
) -> ExperienceInvocationAction:
    """
    Record one actual invocation handled through this sensor action config.

    Contract:
    - Parentage is `SensorConfig -> SensorInvocationActionConfig`.
    - `ExperienceInvocationActionConfig` remains target metadata only.
    - Concrete Sensor instance provenance is recorded by `SensorInvocationAction`,
      which links to the actual Experience invocation receipt.
    """

    # --- AWARE: LOGIC START record_invocation
    raise RuntimeError(
        "SensorInvocationActionConfig.record_invocation cannot construct "
        "ExperienceInvocationAction directly. Create or receive a generic "
        "ExperienceInvocationAction through its owning surface, then bind it "
        "to a concrete Sensor with SensorInvocationAction.build."
    )
    # --- AWARE: LOGIC END record_invocation


async def build_via_sensor_config(
    sensor_config_id: UUID, experience_invocation_action_config_id: UUID
) -> SensorInvocationActionConfig:
    """
    Bind one generic invocation action config under a SensorConfig.

    Contract:
    - Parent `SensorConfig` scope is propagated by constructor lowering.
    - This object only says that the sensor config can invoke that reusable
      Experience action target.
    """

    # --- AWARE: LOGIC START build_via_sensor_config
    normalized_sensor_config_id = as_uuid(
        sensor_config_id,
        field_name="SensorInvocationActionConfig.sensor_config_id",
    )
    normalized_experience_invocation_action_config_id = as_uuid(
        experience_invocation_action_config_id,
        field_name=("SensorInvocationActionConfig." "experience_invocation_action_config_id"),
    )
    action_config_id = stable_sensor_invocation_action_config_id(
        sensor_config_id=normalized_sensor_config_id,
        experience_invocation_action_config_id=(normalized_experience_invocation_action_config_id),
    )

    session = current_handler_session()
    experience_invocation_action_config = session.imap_get(
        ExperienceInvocationActionConfig,
        normalized_experience_invocation_action_config_id,
    )
    existing = session.imap_get(SensorInvocationActionConfig, action_config_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "sensor_config_id": normalized_sensor_config_id,
                "experience_invocation_action_config_id": (normalized_experience_invocation_action_config_id),
            },
            label="SensorInvocationActionConfig",
            object_id=action_config_id,
        )
        return existing

    return SensorInvocationActionConfig(
        id=action_config_id,
        sensor_config_id=normalized_sensor_config_id,
        experience_invocation_action_config_id=(normalized_experience_invocation_action_config_id),
        experience_invocation_action_config=experience_invocation_action_config,
    )
    # --- AWARE: LOGIC END build_via_sensor_config
