from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.actuator.actuator_invocation_action_config import ActuatorInvocationActionConfig
from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
)
from aware_experience.stable_ids import stable_actuator_invocation_action_config_id
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def record_invocation(
    actuator_invocation_action_config: ActuatorInvocationActionConfig,
    invocation_key: UUID,
    actor_id: UUID | None = None,
    api_call_id: UUID | None = None,
    sdk_operation_call_id: UUID | None = None,
    request_ref: str | None = None,
    receipt_ref: str | None = None,
    status: str = "pending",
) -> ExperienceInvocationAction:
    """
    Record one actual invocation handled through this actuator action config.

    Contract:
    - Parentage is `ActuatorConfig -> ActuatorInvocationActionConfig`.
    - `ExperienceInvocationActionConfig` remains target metadata only.
    - Concrete Actuator instance provenance is recorded by `ActuatorInvocationAction`,
      which links to the actual Experience invocation receipt.
    """

    # --- AWARE: LOGIC START record_invocation
    raise RuntimeError(
        "ActuatorInvocationActionConfig.record_invocation cannot construct "
        "ExperienceInvocationAction directly. Create or receive a generic "
        "ExperienceInvocationAction through its owning surface, then bind it "
        "to a concrete Actuator with ActuatorInvocationAction.build."
    )
    # --- AWARE: LOGIC END record_invocation


async def build_via_actuator_config(
    actuator_config_id: UUID, experience_invocation_action_config_id: UUID
) -> ActuatorInvocationActionConfig:
    """
    Bind one generic invocation action config under an ActuatorConfig.

    Contract:
    - Parent `ActuatorConfig` scope is propagated by constructor lowering.
    - This object only says that the actuator config can invoke that reusable
      Experience action target.
    """

    # --- AWARE: LOGIC START build_via_actuator_config
    normalized_actuator_config_id = as_uuid(
        actuator_config_id,
        field_name="ActuatorInvocationActionConfig.actuator_config_id",
    )
    normalized_experience_invocation_action_config_id = as_uuid(
        experience_invocation_action_config_id,
        field_name=("ActuatorInvocationActionConfig." "experience_invocation_action_config_id"),
    )
    action_config_id = stable_actuator_invocation_action_config_id(
        actuator_config_id=normalized_actuator_config_id,
        experience_invocation_action_config_id=(normalized_experience_invocation_action_config_id),
    )

    session = current_handler_session()
    experience_invocation_action_config = session.imap_get(
        ExperienceInvocationActionConfig,
        normalized_experience_invocation_action_config_id,
    )
    existing = session.imap_get(ActuatorInvocationActionConfig, action_config_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "actuator_config_id": normalized_actuator_config_id,
                "experience_invocation_action_config_id": (normalized_experience_invocation_action_config_id),
            },
            label="ActuatorInvocationActionConfig",
            object_id=action_config_id,
        )
        return existing

    return ActuatorInvocationActionConfig(
        id=action_config_id,
        actuator_config_id=normalized_actuator_config_id,
        experience_invocation_action_config_id=(normalized_experience_invocation_action_config_id),
        experience_invocation_action_config=experience_invocation_action_config,
    )
    # --- AWARE: LOGIC END build_via_actuator_config
