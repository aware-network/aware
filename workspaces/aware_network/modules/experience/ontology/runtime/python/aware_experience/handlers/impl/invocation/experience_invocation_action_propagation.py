from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action_propagation import (
    ExperienceInvocationActionPropagation,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_experience_invocation_action_propagation_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_experience_invocation_action(
    experience_invocation_action_id: UUID,
    target_invocation_action_id: UUID,
    propagation_kind: str = "invokes",
    description: str | None = None,
) -> ExperienceInvocationActionPropagation:
    """
    Link this invocation action to a target invocation action it caused.

    Contract:
    - Parent `ExperienceInvocationAction` is the source action.
    - Target action keeps its own receipts and graph/event provenance.
    """

    # --- AWARE: LOGIC START build_via_experience_invocation_action
    normalized_propagation_kind = (propagation_kind or "").strip() or "invokes"
    normalized_description = (description or "").strip() or None
    propagation_id = stable_experience_invocation_action_propagation_id(
        experience_invocation_action_id=experience_invocation_action_id,
        target_invocation_action_id=target_invocation_action_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ExperienceInvocationActionPropagation, propagation_id)
    if existing is not None:
        if (
            existing.experience_invocation_action_id != experience_invocation_action_id
            or existing.target_invocation_action_id != target_invocation_action_id
            or existing.propagation_kind != normalized_propagation_kind
            or existing.description != normalized_description
        ):
            raise RuntimeError(
                "ExperienceInvocationActionPropagation payload mismatch for existing propagation: "
                + f"experience_invocation_action_propagation_id={propagation_id}"
            )
        return existing

    return ExperienceInvocationActionPropagation(
        id=propagation_id,
        experience_invocation_action_id=experience_invocation_action_id,
        target_invocation_action_id=target_invocation_action_id,
        propagation_kind=normalized_propagation_kind,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_invocation_action
