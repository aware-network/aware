from __future__ import annotations

from uuid import UUID

from aware_experience.stable_ids import (
    stable_turn_feedback_id,
    stable_turn_id,
)


def test_stable_turn_id_is_deterministic() -> None:
    environment_id = UUID("00000000-0000-0000-0000-000000000111")
    target_actor_id = UUID("00000000-0000-0000-0000-000000000222")
    first = stable_turn_id(
        environment_id=environment_id,
        target_actor_id=target_actor_id,
        key="idempotency:abc",
    )
    second = stable_turn_id(
        environment_id=environment_id,
        target_actor_id=target_actor_id,
        key="idempotency:abc",
    )
    third = stable_turn_id(
        environment_id=environment_id,
        target_actor_id=target_actor_id,
        key="idempotency:def",
    )
    assert first == second
    assert first != third


def test_stable_turn_feedback_id_is_deterministic() -> None:
    turn_id = UUID("00000000-0000-0000-0000-000000000999")
    first = stable_turn_feedback_id(turn_id=turn_id, sequence=0)
    second = stable_turn_feedback_id(turn_id=turn_id, sequence=0)
    third = stable_turn_feedback_id(turn_id=turn_id, sequence=1)
    assert first == second
    assert first != third
