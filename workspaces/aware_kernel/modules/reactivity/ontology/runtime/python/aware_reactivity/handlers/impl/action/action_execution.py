from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Reactivity Ontology
from aware_reactivity_ontology.action.action_enums import (
    ActionExecutionStatus,
    ActionFeedbackStage,
    ActionFeedbackStatus,
)
from aware_reactivity_ontology.action.action_execution import ActionExecution
from aware_reactivity_ontology.action.action_feedback import ActionFeedback

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_action_execution_id

# --- AWARE: USER_IMPORTS END


async def add_feedback(
    action_execution: ActionExecution,
    sequence: int,
    stage: ActionFeedbackStage,
    status: ActionFeedbackStatus,
    created_at_unix_ms: int = 0,
    message: str | None = None,
    payload: JsonObject = JsonObject(),
    payload_class_config_id: UUID | None = None,
) -> ActionFeedback:
    """
    Append one lifecycle feedback record for this execution.
    """

    # --- AWARE: LOGIC START add_feedback
    created = await ActionFeedback.create_via_action_execution(
        action_execution_id=action_execution.id,
        sequence=sequence,
        stage=stage,
        status=status,
        created_at_unix_ms=created_at_unix_ms,
        message=message,
        payload=dict(payload),
        payload_class_config_id=payload_class_config_id,
    )

    for existing in action_execution.action_feedback:
        if existing.id == created.id:
            return existing

    action_execution.action_feedback.append(created)
    return created
    # --- AWARE: LOGIC END add_feedback


async def set_status(
    action_execution: ActionExecution, status: ActionExecutionStatus, result_info: str | None = None
) -> None:
    """
    Update execution status after service fulfillment progress.
    """

    # --- AWARE: LOGIC START set_status
    action_execution.status = status
    action_execution.result_info = result_info
    # --- AWARE: LOGIC END set_status


async def create_via_action_intent(
    action_intent_id: UUID,
    execution_key: str = "primary",
    status: ActionExecutionStatus = ActionExecutionStatus.created,
    execution_context: JsonObject = JsonObject(),
    executor_ref: str | None = None,
    result_info: str | None = None,
) -> ActionExecution:
    """
    Create commit-backed action execution promise/correlation evidence.

    Contract:
    - This is the canonical "service accepted or will decide on fulfillment" record.
    - Deterministic id is derived from action intent and execution key.
    """

    # --- AWARE: LOGIC START create_via_action_intent
    return ActionExecution(
        id=stable_action_execution_id(
            action_intent_id=action_intent_id,
            execution_key=execution_key,
        ),
        action_intent_id=action_intent_id,
        execution_key=execution_key,
        status=status,
        execution_context=dict(execution_context),
        executor_ref=executor_ref,
        result_info=result_info,
    )
    # --- AWARE: LOGIC END create_via_action_intent
