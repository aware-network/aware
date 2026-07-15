from __future__ import annotations

from uuid import uuid4

from aware_identity.gate import build_identity_gate_step


def test_identity_gate_step_crosses_when_auth_actor_matches_expected_actor() -> None:
    actor_id = uuid4()

    step = build_identity_gate_step(
        expected_actor_id=actor_id,
        auth_session_available=True,
        auth_actor_id=actor_id,
    )

    assert step.crossed is True
    assert step.key == "identity"


def test_identity_gate_step_blocks_on_actor_mismatch() -> None:
    step = build_identity_gate_step(
        expected_actor_id=uuid4(),
        auth_session_available=True,
        auth_actor_id=uuid4(),
    )

    assert step.crossed is False
    assert "does not match" in (step.description or "")
