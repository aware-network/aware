from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.actuator.actuator_invocation_action import ActuatorInvocationAction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
)
from aware_experience.stable_ids import stable_actuator_invocation_action_id
from aware_experience_ontology.actuator.actuator_invocation_action_config import (
    ActuatorInvocationActionConfig,
)
from aware_experience_ontology.invocation.experience_invocation_action import (
    ExperienceInvocationAction,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    actuator_id: UUID, actuator_invocation_action_config_id: UUID, experience_invocation_action_id: UUID
) -> ActuatorInvocationAction:
    """
    Create one deterministic Actuator provenance bridge under an Actuator.

    Contract:
    - `actuator_id` is explicit provenance for the concrete Actuator instance.
    - `actuator_invocation_action_config` proves the action was exposed by
      the Actuator config.
    - `experience_invocation_action` carries the actual invocation receipt.
    """

    # --- AWARE: LOGIC START build
    normalized_actuator_id = as_uuid(
        actuator_id,
        field_name="ActuatorInvocationAction.actuator_id",
    )
    normalized_actuator_invocation_action_config_id = as_uuid(
        actuator_invocation_action_config_id,
        field_name="ActuatorInvocationAction.actuator_invocation_action_config_id",
    )
    normalized_experience_invocation_action_id = as_uuid(
        experience_invocation_action_id,
        field_name="ActuatorInvocationAction.experience_invocation_action_id",
    )
    action_id = stable_actuator_invocation_action_id(
        actuator_invocation_action_config_id=(normalized_actuator_invocation_action_config_id),
        experience_invocation_action_id=normalized_experience_invocation_action_id,
    )

    session = current_handler_session()
    actuator_invocation_action_config = session.imap_get(
        ActuatorInvocationActionConfig,
        normalized_actuator_invocation_action_config_id,
    )
    experience_invocation_action = session.imap_get(
        ExperienceInvocationAction,
        normalized_experience_invocation_action_id,
    )
    existing = session.imap_get(ActuatorInvocationAction, action_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "actuator_id": normalized_actuator_id,
                "actuator_invocation_action_config_id": (normalized_actuator_invocation_action_config_id),
                "experience_invocation_action_id": (normalized_experience_invocation_action_id),
            },
            label="ActuatorInvocationAction",
            object_id=action_id,
        )
        return existing

    return ActuatorInvocationAction(
        id=action_id,
        actuator_id=normalized_actuator_id,
        actuator_invocation_action_config_id=(normalized_actuator_invocation_action_config_id),
        experience_invocation_action_id=normalized_experience_invocation_action_id,
        actuator_invocation_action_config=actuator_invocation_action_config,
        experience_invocation_action=experience_invocation_action,
    )
    # --- AWARE: LOGIC END build
