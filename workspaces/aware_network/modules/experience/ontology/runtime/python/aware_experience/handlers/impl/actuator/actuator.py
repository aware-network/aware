from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.actuator.actuator import Actuator

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
from aware_experience.stable_ids import stable_actuator_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_actuator_config(
    actuator_config_id: UUID, actuator_instance_key: str, external_ref: str | None = None, status: str = "active"
) -> Actuator:
    """
    Create one deterministic Actuator instance under an ActuatorConfig.

    Contract:
    - Parent `ActuatorConfig` scope is propagated by constructor lowering.
    - `actuator_instance_key` identifies this runtime fulfillment.
    """

    # --- AWARE: LOGIC START build_via_actuator_config
    normalized_actuator_config_id = as_uuid(
        actuator_config_id,
        field_name="Actuator.actuator_config_id",
    )
    normalized_actuator_instance_key = required_token(
        actuator_instance_key,
        field_name="Actuator.actuator_instance_key",
    )
    normalized_external_ref = optional_token(external_ref)
    normalized_status = status_token(status, default="active")
    actuator_id = stable_actuator_id(
        actuator_config_id=normalized_actuator_config_id,
        actuator_instance_key=normalized_actuator_instance_key,
    )

    session = current_handler_session()
    existing = session.imap_get(Actuator, actuator_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "actuator_config_id": normalized_actuator_config_id,
                "actuator_instance_key": normalized_actuator_instance_key,
                "external_ref": normalized_external_ref,
                "status": normalized_status,
            },
            label="Actuator",
            object_id=actuator_id,
        )
        return existing

    return Actuator(
        id=actuator_id,
        actuator_config_id=normalized_actuator_config_id,
        actuator_instance_key=normalized_actuator_instance_key,
        external_ref=normalized_external_ref,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_actuator_config
