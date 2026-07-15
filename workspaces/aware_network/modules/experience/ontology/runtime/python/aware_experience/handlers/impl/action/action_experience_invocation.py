from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.action.action_experience_invocation import ActionExperienceInvocation
from aware_experience_ontology.action.action_experience_invocation_request_field import (
    ActionExperienceInvocationRequestField,
)
from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_action_experience_invocation_id
from aware_experience_ontology.action.action_experience import ActionExperience
from aware_experience_ontology.action.action_experience_invocation_action import (
    ActionExperienceInvocationAction,
)
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def record_invocation(
    action_experience_invocation: ActionExperienceInvocation,
    invocation_key: UUID,
    actor_id: UUID | None = None,
    api_call_id: UUID | None = None,
    sdk_operation_call_id: UUID | None = None,
    request_ref: str | None = None,
    receipt_ref: str | None = None,
    status: str = "pending",
) -> ExperienceInvocationAction:
    """
    Record one actual invocation handled through this action experience binding.

    Contract:
    - Parentage is `ActionExperience -> ActionExperienceInvocation`.
    - `ExperienceInvocationActionConfig` remains target metadata only.
    - `ExperienceInvocationAction` is the single standalone invocation
      receipt for one action crossing.
    - The action-experience surface records provenance through
      `ActionExperienceInvocationAction`; it does not own receipt identity.
    - Concrete actuator/sensor/view provenance must attach to this same
      receipt through their provenance bridge objects; it must not create
      another invocation receipt for the same crossing.
    """

    # --- AWARE: LOGIC START record_invocation
    invocation_action = await ActionExperienceInvocationAction.build_via_action_experience_invocation(
        action_experience_invocation_id=action_experience_invocation.id,
        experience_invocation_action_config_id=(action_experience_invocation.experience_invocation_action_config_id),
        invocation_key=invocation_key,
        actor_id=actor_id,
        api_call_id=api_call_id,
        sdk_operation_call_id=sdk_operation_call_id,
        request_ref=request_ref,
        receipt_ref=receipt_ref,
        status=status,
    )
    for existing in action_experience_invocation.invocation_actions:
        if existing.id == invocation_action.id:
            if existing.experience_invocation_action is not None:
                return existing.experience_invocation_action
            break
    action_experience_invocation.invocation_actions.append(invocation_action)
    return invocation_action.experience_invocation_action
    # --- AWARE: LOGIC END record_invocation


async def add_request_field(
    action_experience_invocation: ActionExperienceInvocation,
    attribute_config_id: UUID,
    source_ref: str,
    required: bool = True,
    position: int | None = None,
) -> ActionExperienceInvocationRequestField:
    """
    Declare how this action activation composes one endpoint request field.

    Contract:
    - Parentage is `ActionExperience -> ActionExperienceInvocation`.
    - `attribute_config` must belong to the anchored endpoint request
      ClassConfig; runtime dispatch and materialization fail closed if it
      does not.
    - `source_ref` is a closed dispatch-context vocabulary entry:
      event.*, commit.*, intent.*, execution.*, api_call.key, binding.*,
      binding.node.<alias>.class_instance_identity_id,
      binding.node.<alias>.class_config_id, actor.id, or
      subscription.id. No payload paths and no graph reads.
    - This is Tier 1 composition only: declarative field copy from context
      to endpoint request payload. Domain enrichment belongs to the target
      service or to a prior Program step.
    """

    # --- AWARE: LOGIC START add_request_field
    action_experience_invocation_id = action_experience_invocation.id
    created = await ActionExperienceInvocationRequestField.build_via_action_experience_invocation(
        action_experience_invocation_id=action_experience_invocation_id,
        attribute_config_id=attribute_config_id,
        source_ref=source_ref,
        required=required,
        position=position,
    )
    if created.action_experience_invocation_id != action_experience_invocation_id:
        raise RuntimeError(
            "ActionExperienceInvocation.add_request_field context mismatch for created request field: "
            + f"action_experience_invocation_request_field_id={created.id}"
        )

    for existing in action_experience_invocation.request_fields:
        if existing.id == created.id:
            return existing
    action_experience_invocation.request_fields.append(created)
    return created
    # --- AWARE: LOGIC END add_request_field


async def build_via_action_experience(
    action_experience_id: UUID, experience_invocation_action_config_id: UUID
) -> ActionExperienceInvocation:
    """
    Create a deterministic ActionExperience invocation binding edge.
    """

    # --- AWARE: LOGIC START build_via_action_experience
    session = current_handler_session()
    action_experience = session.imap_get(ActionExperience, action_experience_id)
    if action_experience is None:
        raise RuntimeError(
            "ActionExperienceInvocation.build_via_action_experience requires existing ActionExperience in "
            + f"session: action_experience_id={action_experience_id}"
        )
    experience_invocation_action_config = session.imap_get(
        ExperienceInvocationActionConfig,
        experience_invocation_action_config_id,
    )

    assoc_id = stable_action_experience_invocation_id(
        action_experience_id=action_experience_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
    )
    existing = session.imap_get(ActionExperienceInvocation, assoc_id)
    if existing is not None:
        if (
            existing.action_experience_id != action_experience_id
            or existing.experience_invocation_action_config_id != experience_invocation_action_config_id
        ):
            raise RuntimeError(
                "ActionExperienceInvocation.build_via_action_experience field mismatch for existing association: "
                + f"action_experience_invocation_id={assoc_id}"
            )
        existing.experience_invocation_action_config = experience_invocation_action_config
        return existing

    return ActionExperienceInvocation(
        id=assoc_id,
        action_experience_id=action_experience_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        experience_invocation_action_config=experience_invocation_action_config,
    )
    # --- AWARE: LOGIC END build_via_action_experience
