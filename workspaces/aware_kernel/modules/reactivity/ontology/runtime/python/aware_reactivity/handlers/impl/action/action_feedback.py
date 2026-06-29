from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import (
    ActionFeedbackStage,
    ActionFeedbackStatus,
)
from aware_reactivity_ontology.action.action_feedback import ActionFeedback

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta_ontology.class_.inline_value_instance import InlineValueInstance
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_reactivity.stable_ids import stable_action_feedback_id

# --- AWARE: USER_IMPORTS END


async def create_via_action_execution(
    action_execution_id: UUID,
    sequence: int,
    stage: ActionFeedbackStage,
    status: ActionFeedbackStatus,
    created_at_unix_ms: int = 0,
    message: str | None = None,
    payload: JsonObject = JsonObject(),
    payload_class_config_id: UUID | None = None,
) -> ActionFeedback:
    """
    Create commit-backed lifecycle feedback evidence for one action execution.

    Contract:
    - This is append-only feedback truth under an ActionExecution.
    - Deterministic id is derived from action execution and sequence.
    - `payload_model` is typed stream feedback payload evidence. Its
      ClassConfig is supplied by the Experience/API resolver; Reactivity
      remains API-agnostic.
    - `payload` is deprecated compatibility metadata only.
    """

    # --- AWARE: LOGIC START create_via_action_execution
    action_feedback_id = stable_action_feedback_id(
        action_execution_id=action_execution_id,
        sequence=sequence,
    )
    payload_model = None
    if payload_class_config_id is not None:
        payload_model = InlineValueInstance(
            id=stable_inline_value_instance_id(
                class_config_id=payload_class_config_id,
                owner_key=action_feedback_id,
            ),
            class_config_id=payload_class_config_id,
            owner_key=action_feedback_id,
            attributes=[],
        )
    return ActionFeedback(
        id=action_feedback_id,
        action_execution_id=action_execution_id,
        sequence=sequence,
        stage=stage,
        status=status,
        created_at_unix_ms=created_at_unix_ms,
        message=message,
        payload=dict(payload),
        payload_model_id=(payload_model.id if payload_model is not None else None),
        payload_model=payload_model,
    )
    # --- AWARE: LOGIC END create_via_action_execution
