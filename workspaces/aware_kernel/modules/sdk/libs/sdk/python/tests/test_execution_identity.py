from __future__ import annotations

import pytest

from aware_sdk_core.execution_identity import (
    ProviderExecutionIdentityError,
    local_sdk_actor_ref,
    normalize_provider_key,
    resolve_provider_execution_identity,
    try_resolve_provider_execution_identity,
)


def test_resolve_provider_execution_identity_uses_codex_thread_id() -> None:
    identity = resolve_provider_execution_identity(
        env={"CODEX_THREAD_ID": "019e-local-thread"},
        role="Coordinator",
    )

    assert identity.provider_key == "codex"
    assert identity.provider_session_id == "019e-local-thread"
    assert identity.execution_id == "codex-019e-local-thread"
    assert identity.role == "coordinator"
    assert local_sdk_actor_ref(identity) == "codex-019e-local-thread"
    assert identity.to_payload() == {
        "provider_key": "codex",
        "provider_session_id": "019e-local-thread",
        "execution_id": "codex-019e-local-thread",
        "role": "coordinator",
    }


def test_resolve_provider_execution_identity_strips_provider_prefix() -> None:
    identity = resolve_provider_execution_identity(
        provider_key="Codex",
        provider_session_id="codex-019e-local-thread",
    )

    assert identity.provider_key == "codex"
    assert identity.provider_session_id == "019e-local-thread"
    assert identity.execution_id == "codex-019e-local-thread"


def test_resolve_provider_execution_identity_normalizes_provider_key() -> None:
    assert normalize_provider_key("Claude Code") == "claude_code"

    identity = resolve_provider_execution_identity(
        provider_key="Claude-Code",
        provider_session_id="session-1",
    )

    assert identity.provider_key == "claude_code"
    assert identity.provider_session_id == "session-1"
    assert identity.execution_id == "claude_code-session-1"


def test_resolve_provider_execution_identity_fails_closed_without_session() -> None:
    with pytest.raises(ProviderExecutionIdentityError, match="provider session id"):
        resolve_provider_execution_identity(env={})

    assert try_resolve_provider_execution_identity(env={}) is None
