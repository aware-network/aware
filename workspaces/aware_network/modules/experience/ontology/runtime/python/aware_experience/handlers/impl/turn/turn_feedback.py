from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.turn.turn_feedback import TurnFeedback

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience_ontology.turn.turn import Turn

# Experience
from aware_experience.stable_ids import stable_turn_feedback_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_turn(
    turn_id: UUID,
    sequence: int,
    stage: str,
    status: str,
    created_at_unix_ms: int,
    message: str | None = None,
    payload: JsonObject | None = None,
) -> TurnFeedback:
    """
    Construct a deterministic feedback record under a Turn.

    Contract:
    - Identity is derived from `(turn_id, sequence)`.
    - Constructor is idempotent for repeated calls with the same pair.
    """

    # --- AWARE: LOGIC START create_via_turn
    session = current_handler_session()
    turn = session.imap_get(Turn, turn_id)
    if turn is None:
        raise RuntimeError("TurnFeedback.create_via_turn requires Turn in session: " f"turn_id={turn_id}")

    normalized_mailbox_key = (turn.mailbox_key or "").strip()
    if not normalized_mailbox_key:
        raise RuntimeError("TurnFeedback.create_via_turn requires Turn.mailbox_key")

    normalized_stage = (stage or "").strip()
    normalized_status = (status or "").strip()
    if not normalized_stage:
        raise RuntimeError("TurnFeedback.create_via_turn requires non-empty stage")
    if not normalized_status:
        raise RuntimeError("TurnFeedback.create_via_turn requires non-empty status")

    sequence_value = int(sequence)
    if sequence_value < 0:
        raise RuntimeError("TurnFeedback.create_via_turn requires sequence >= 0")

    feedback_id = stable_turn_feedback_id(turn_id=turn_id, sequence=sequence_value)
    existing = session.imap_get(TurnFeedback, feedback_id)
    if existing is not None:
        if existing.turn_id != turn_id:
            raise RuntimeError(
                "TurnFeedback.create_via_turn turn_id mismatch for existing feedback: " f"feedback_id={feedback_id}"
            )
        if existing.mailbox_key != normalized_mailbox_key:
            raise RuntimeError(
                "TurnFeedback.create_via_turn mailbox_key mismatch for existing feedback: " f"feedback_id={feedback_id}"
            )
        return existing

    return TurnFeedback(
        id=feedback_id,
        turn_id=turn_id,
        mailbox_key=normalized_mailbox_key,
        sequence=sequence_value,
        stage=normalized_stage,
        status=normalized_status,
        created_at_unix_ms=int(created_at_unix_ms),
        message=message,
        payload=payload,
    )
    # --- AWARE: LOGIC END create_via_turn
