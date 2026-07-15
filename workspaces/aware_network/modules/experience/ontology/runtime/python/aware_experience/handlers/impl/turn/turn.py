from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.turn.turn_enums import TurnExecutionTerminalStatus
from aware_experience_ontology.turn.turn import Turn
from aware_experience_ontology.turn.turn_feedback import TurnFeedback

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Standard
import time

# Experience
from aware_experience.stable_ids import stable_turn_id
from aware_experience.mechanisms.turn_execution_state import (
    normalized_turn_state_value,
    normalized_turn_terminal_status_value,
)

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# Experience Ontology
from aware_experience_ontology.turn.turn_enums import TurnExecutionState

# --- AWARE: USER_IMPORTS END


async def build(
    environment_id: UUID,
    target_actor_id: UUID,
    key: str,
    mailbox_key: str,
    max_attempts: int = 1,
    created_at_unix_ms: int | None = None,
    accepted_at_unix_ms: int | None = None,
    idempotency_key: str | None = None,
    cause_event_id: UUID | None = None,
    cause_action_execution_id: UUID | None = None,
    payload: JsonObject | None = None,
    resolved_branch_id: UUID | None = None,
    resolved_projection_hash: str | None = None,
    lane_resolution_source: str | None = None,
) -> Turn:
    """
    Construct a deterministic Turn instance for runtime turn execution lifecycle.

    Contract:
    - Identity is derived from `(environment_id, target_actor_id, key)`.
    - Constructor is idempotent for repeated calls with the same identity tuple.
    """

    # --- AWARE: LOGIC START build
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("Turn.build requires non-empty key")

    normalized_mailbox_key = (mailbox_key or "").strip()
    if not normalized_mailbox_key:
        raise RuntimeError("Turn.build requires non-empty mailbox_key")

    if int(max_attempts) < 1:
        raise RuntimeError("Turn.build requires max_attempts >= 1")

    now_unix_ms = int(time.time() * 1000)
    created_ms = int(created_at_unix_ms) if created_at_unix_ms is not None else now_unix_ms
    accepted_ms = int(accepted_at_unix_ms) if accepted_at_unix_ms is not None else created_ms
    if accepted_ms < created_ms:
        raise RuntimeError("Turn.build requires accepted_at_unix_ms >= created_at_unix_ms")

    normalized_resolved_projection_hash = (
        str(resolved_projection_hash).strip() if resolved_projection_hash is not None else None
    )
    if normalized_resolved_projection_hash == "":
        normalized_resolved_projection_hash = None
    if (resolved_branch_id is None) ^ (normalized_resolved_projection_hash is None):
        raise RuntimeError(
            "Turn.build requires resolved_branch_id and resolved_projection_hash " "to be both present or both omitted"
        )
    normalized_lane_resolution_source = (
        str(lane_resolution_source).strip() if lane_resolution_source is not None else None
    )
    if normalized_lane_resolution_source == "":
        normalized_lane_resolution_source = None

    turn_id = stable_turn_id(
        environment_id=environment_id,
        target_actor_id=target_actor_id,
        key=normalized_key,
    )
    session = current_handler_session()
    existing = session.imap_get(Turn, turn_id)
    if existing is not None:
        if existing.environment_id != environment_id:
            raise RuntimeError("Turn.build environment mismatch for existing turn: " f"turn_id={turn_id}")
        if existing.target_actor_id != target_actor_id:
            raise RuntimeError("Turn.build target_actor mismatch for existing turn: " f"turn_id={turn_id}")
        if existing.key != normalized_key:
            raise RuntimeError("Turn.build key mismatch for existing turn: " f"turn_id={turn_id}")
        if existing.mailbox_key != normalized_mailbox_key:
            raise RuntimeError(
                "Turn.build mailbox_key mismatch for existing turn: "
                f"turn_id={turn_id} existing={existing.mailbox_key!r} "
                f"new={normalized_mailbox_key!r}"
            )
        if resolved_branch_id is not None and existing.resolved_branch_id not in {
            None,
            resolved_branch_id,
        }:
            raise RuntimeError(
                "Turn.build resolved_branch_id mismatch for existing turn: "
                f"turn_id={turn_id} existing={existing.resolved_branch_id} "
                f"new={resolved_branch_id}"
            )
        existing_projection = (
            str(existing.resolved_projection_hash).strip() if existing.resolved_projection_hash is not None else None
        )
        if normalized_resolved_projection_hash is not None and existing_projection not in {
            None,
            normalized_resolved_projection_hash,
        }:
            raise RuntimeError(
                "Turn.build resolved_projection_hash mismatch for existing turn: "
                f"turn_id={turn_id} existing={existing_projection!r} "
                f"new={normalized_resolved_projection_hash!r}"
            )
        existing_source = (
            str(existing.lane_resolution_source).strip() if existing.lane_resolution_source is not None else None
        )
        if normalized_lane_resolution_source is not None and existing_source not in {
            None,
            normalized_lane_resolution_source,
        }:
            raise RuntimeError(
                "Turn.build lane_resolution_source mismatch for existing turn: "
                f"turn_id={turn_id} existing={existing_source!r} "
                f"new={normalized_lane_resolution_source!r}"
            )
        return existing

    return Turn(
        id=turn_id,
        environment_id=environment_id,
        key=normalized_key,
        mailbox_key=normalized_mailbox_key,
        target_actor_id=target_actor_id,
        created_at_unix_ms=created_ms,
        accepted_at_unix_ms=accepted_ms,
        max_attempts=int(max_attempts),
        idempotency_key=((idempotency_key or "").strip() or None),
        cause_event_id=cause_event_id,
        cause_action_execution_id=cause_action_execution_id,
        payload=payload,
        resolved_branch_id=resolved_branch_id,
        resolved_projection_hash=normalized_resolved_projection_hash,
        lane_resolution_source=normalized_lane_resolution_source,
    )
    # --- AWARE: LOGIC END build


async def add_feedback(
    turn: Turn,
    sequence: int,
    stage: str,
    status: str,
    created_at_unix_ms: int,
    message: str | None = None,
    payload: JsonObject | None = None,
) -> TurnFeedback:
    """
    Append one feedback record under this Turn.

    Contract:
    - Mutates only this Turn membership (`feedbacks`).
    - Feedback identity is deterministic per `(turn_id, sequence)`.
    """

    # --- AWARE: LOGIC START add_feedback
    turn_id = turn.id
    if turn_id is None:
        raise RuntimeError("Turn.add_feedback requires Turn.id")

    normalized_stage = (stage or "").strip()
    normalized_status = (status or "").strip()
    if not normalized_stage:
        raise RuntimeError("Turn.add_feedback requires non-empty stage")
    if not normalized_status:
        raise RuntimeError("Turn.add_feedback requires non-empty status")

    sequence_value = int(sequence)
    if sequence_value < 0:
        raise RuntimeError("Turn.add_feedback requires sequence >= 0")

    created = await TurnFeedback.create_via_turn(
        turn_id=turn_id,
        sequence=sequence_value,
        stage=normalized_stage,
        status=normalized_status,
        created_at_unix_ms=int(created_at_unix_ms),
        message=message,
        payload=payload,
    )

    for existing in turn.feedbacks:
        if existing.id == created.id:
            return existing
        if int(existing.sequence) >= sequence_value:
            raise RuntimeError(
                "Turn.add_feedback requires monotonic increasing sequence: "
                f"turn_id={turn_id} existing={existing.sequence} new={sequence_value}"
            )

    turn.feedbacks.append(created)
    return created
    # --- AWARE: LOGIC END add_feedback


async def set_lane_resolution(
    turn: Turn, resolved_branch_id: UUID, resolved_projection_hash: str, lane_resolution_source: str | None = None
) -> Turn:
    """
    Persist runtime-resolved execution lane on this Turn.

    Contract:
    - Runtime-owned lane resolution metadata only.
    - Idempotent for repeated writes of the same lane resolution.
    """

    # --- AWARE: LOGIC START set_lane_resolution
    normalized_projection_hash = (resolved_projection_hash or "").strip()
    if not normalized_projection_hash:
        raise RuntimeError("Turn.set_lane_resolution requires non-empty resolved_projection_hash")
    normalized_source = str(lane_resolution_source).strip() if lane_resolution_source is not None else None
    if normalized_source == "":
        normalized_source = None

    existing_projection = (
        str(turn.resolved_projection_hash).strip() if turn.resolved_projection_hash is not None else None
    )
    if turn.resolved_branch_id is not None and turn.resolved_branch_id != resolved_branch_id:
        raise RuntimeError(
            "Turn.set_lane_resolution resolved_branch_id mismatch: "
            f"existing={turn.resolved_branch_id} new={resolved_branch_id}"
        )
    if existing_projection is not None and existing_projection != normalized_projection_hash:
        raise RuntimeError(
            "Turn.set_lane_resolution resolved_projection_hash mismatch: "
            f"existing={existing_projection!r} new={normalized_projection_hash!r}"
        )

    if turn.resolved_branch_id is None:
        turn.resolved_branch_id = resolved_branch_id
    if existing_projection is None:
        turn.resolved_projection_hash = normalized_projection_hash

    existing_source = str(turn.lane_resolution_source).strip() if turn.lane_resolution_source is not None else None
    if normalized_source is not None:
        if existing_source is not None and existing_source != normalized_source:
            raise RuntimeError(
                "Turn.set_lane_resolution lane_resolution_source mismatch: "
                f"existing={existing_source!r} new={normalized_source!r}"
            )
        turn.lane_resolution_source = normalized_source

    return turn
    # --- AWARE: LOGIC END set_lane_resolution


async def claim_running(
    turn: Turn,
    attempt_count: int,
    started_at_unix_ms: int,
    lease_owner: str | None = None,
    lease_expires_at_unix_ms: int | None = None,
) -> Turn:
    """
    Transition this Turn to `running` for an execution attempt.

    Contract:
    - State becomes `running`.
    - `attempt_count` is runtime-owned and must be monotonic.
    """

    # --- AWARE: LOGIC START claim_running
    attempt = int(attempt_count)
    if attempt < 1:
        raise RuntimeError("Turn.claim_running requires attempt_count >= 1")

    started_at = int(started_at_unix_ms)
    if started_at < int(turn.accepted_at_unix_ms):
        raise RuntimeError("Turn.claim_running requires started_at_unix_ms >= accepted_at_unix_ms")

    if int(turn.attempt_count) > attempt:
        raise RuntimeError(
            "Turn.claim_running requires non-decreasing attempt_count: " f"current={turn.attempt_count} new={attempt}"
        )

    if normalized_turn_state_value(turn.state) == "terminal":
        raise RuntimeError("Turn.claim_running cannot run after terminal state")

    turn.state = TurnExecutionState.running
    turn.attempt_count = attempt
    turn.started_at_unix_ms = started_at
    turn.lease_owner = (lease_owner or "").strip() or None
    turn.lease_expires_at_unix_ms = int(lease_expires_at_unix_ms) if lease_expires_at_unix_ms is not None else None
    turn.terminal_status = None
    turn.terminal_at_unix_ms = None
    return turn
    # --- AWARE: LOGIC END claim_running


async def mark_retry_pending(
    turn: Turn, attempt_count: int, accepted_at_unix_ms: int, error_code: str, error_message: str | None = None
) -> Turn:
    """
    Transition this Turn back to `accepted` after a retryable failure.

    Contract:
    - State becomes `accepted`.
    - Terminal fields are cleared.
    """

    # --- AWARE: LOGIC START mark_retry_pending
    attempt = int(attempt_count)
    if attempt < 1:
        raise RuntimeError("Turn.mark_retry_pending requires attempt_count >= 1")
    if int(turn.attempt_count) > attempt:
        raise RuntimeError(
            "Turn.mark_retry_pending requires non-decreasing attempt_count: "
            f"current={turn.attempt_count} new={attempt}"
        )

    accepted_at = int(accepted_at_unix_ms)
    if accepted_at < int(turn.created_at_unix_ms):
        raise RuntimeError("Turn.mark_retry_pending requires accepted_at_unix_ms >= created_at_unix_ms")

    normalized_error_code = (error_code or "").strip()
    if not normalized_error_code:
        raise RuntimeError("Turn.mark_retry_pending requires non-empty error_code")

    turn.state = TurnExecutionState.accepted
    turn.attempt_count = attempt
    turn.accepted_at_unix_ms = accepted_at
    turn.lease_owner = None
    turn.lease_expires_at_unix_ms = None
    turn.terminal_status = None
    turn.terminal_at_unix_ms = None
    turn.error_code = normalized_error_code
    turn.error_message = str(error_message).strip() if error_message is not None else None
    return turn
    # --- AWARE: LOGIC END mark_retry_pending


async def finish_terminal(
    turn: Turn,
    terminal_status: TurnExecutionTerminalStatus,
    terminal_at_unix_ms: int,
    result_summary: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    result_commit_ids: list[UUID] = [],
) -> Turn:
    """
    Transition this Turn to terminal.

    Contract:
    - State becomes `terminal`.
    - Terminal status and timing are written canonically on this Turn.
    """

    # --- AWARE: LOGIC START finish_terminal
    normalized_status = normalized_turn_terminal_status_value(terminal_status)
    if not normalized_status:
        raise RuntimeError("Turn.finish_terminal requires non-empty terminal_status")

    terminal_at = int(terminal_at_unix_ms)
    if terminal_at < int(turn.created_at_unix_ms):
        raise RuntimeError("Turn.finish_terminal requires terminal_at_unix_ms >= created_at_unix_ms")

    if normalized_turn_state_value(turn.state) == "terminal":
        if normalized_turn_terminal_status_value(turn.terminal_status) == normalized_status:
            return turn
        raise RuntimeError(
            "Turn.finish_terminal terminal_status mismatch for terminal turn: "
            f"existing={turn.terminal_status} new={normalized_status}"
        )

    turn.state = TurnExecutionState.terminal
    turn.terminal_status = TurnExecutionTerminalStatus(normalized_status)
    turn.terminal_at_unix_ms = terminal_at
    turn.lease_owner = None
    turn.lease_expires_at_unix_ms = None
    turn.result_summary = str(result_summary).strip() if result_summary is not None else None
    turn.error_code = str(error_code).strip() if error_code is not None else None
    turn.error_message = str(error_message).strip() if error_message is not None else None
    turn.result_commit_ids = list(result_commit_ids or [])
    return turn
    # --- AWARE: LOGIC END finish_terminal
