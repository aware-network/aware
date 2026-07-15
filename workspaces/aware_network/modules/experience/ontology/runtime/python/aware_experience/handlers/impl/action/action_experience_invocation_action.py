from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.action.action_experience_invocation_action import ActionExperienceInvocationAction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_action_experience_invocation_action_id
from aware_experience_ontology.invocation.experience_invocation_action import (
    ExperienceInvocationAction,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_action_experience_invocation(
    action_experience_invocation_id: UUID,
    experience_invocation_action_config_id: UUID,
    invocation_key: UUID,
    actor_id: UUID | None = None,
    api_call_id: UUID | None = None,
    sdk_operation_call_id: UUID | None = None,
    request_ref: str | None = None,
    receipt_ref: str | None = None,
    status: str = "pending",
) -> ActionExperienceInvocationAction:
    """
    Create one deterministic action-experience provenance bridge.

    Contract:
    - Parent `ActionExperienceInvocation` scope is propagated by traversal
      lowering from `ActionExperienceInvocation::invocation_actions`; the
      child must not declare a parent reference or parent-id input.
    - `ExperienceInvocationAction` is ensured by standalone semantic keys
      `(experience_invocation_action_config, invocation_key)`.
    """

    # --- AWARE: LOGIC START build_via_action_experience_invocation
    experience_invocation_action = await ExperienceInvocationAction.build(
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        invocation_key=invocation_key,
        actor_id=actor_id,
        api_call_id=api_call_id,
        sdk_operation_call_id=sdk_operation_call_id,
        request_ref=request_ref,
        receipt_ref=receipt_ref,
        status=status,
    )
    action_id = stable_action_experience_invocation_action_id(
        action_experience_invocation_id=action_experience_invocation_id,
        experience_invocation_action_id=experience_invocation_action.id,
    )

    session = current_handler_session()
    existing = session.imap_get(ActionExperienceInvocationAction, action_id)
    if existing is not None:
        if (
            existing.action_experience_invocation_id != action_experience_invocation_id
            or existing.experience_invocation_action_id != experience_invocation_action.id
        ):
            raise RuntimeError(
                "ActionExperienceInvocationAction field mismatch for existing bridge: "
                + f"action_experience_invocation_action_id={action_id}"
            )
        existing.experience_invocation_action = experience_invocation_action
        return existing

    return ActionExperienceInvocationAction(
        id=action_id,
        action_experience_invocation_id=action_experience_invocation_id,
        experience_invocation_action_id=experience_invocation_action.id,
        experience_invocation_action=experience_invocation_action,
    )
    # --- AWARE: LOGIC END build_via_action_experience_invocation
