from __future__ import annotations

from aware_network.gate import build_community_gate_step


def test_community_gate_step_crosses_with_remote_auth_or_authority_proof() -> None:
    crossed = build_community_gate_step(
        endpoint="wss://node.aware.run",
        auth_session_available=True,
        authority_snapshot_available=False,
    )

    assert crossed.crossed is True
    assert crossed.key == "network"


def test_community_gate_step_blocks_when_no_remote_proof_exists() -> None:
    blocked = build_community_gate_step(
        endpoint="wss://node.aware.run",
        auth_session_available=False,
        authority_snapshot_available=False,
    )

    assert blocked.crossed is False
    assert "Authenticate against" in (blocked.description or "")
