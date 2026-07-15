from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_session_attention_session import (
    EnvironmentSessionAttentionSession,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_session_attention_session_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_session(
    environment_session_id: UUID,
    attention_session_id: UUID,
    key: str | None = None,
    title: str | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentSessionAttentionSession:
    """
    Construct one EnvironmentSession -> AttentionSession portal row.

    Contract:
    - Stable identity is EnvironmentSession path + AttentionSession.
    - AttentionSession is only a portal target here.
    - No Attention layout/section/focus internals are authored here.
    """

    # --- AWARE: LOGIC START build_via_environment_session
    assoc_id = stable_environment_session_attention_session_id(
        environment_session_id=environment_session_id,
        attention_session_id=attention_session_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(EnvironmentSessionAttentionSession, assoc_id)
    if existing is not None:
        if (
            existing.environment_session_id != environment_session_id
            or existing.attention_session_id != attention_session_id
        ):
            raise RuntimeError(
                "EnvironmentSessionAttentionSession.build_via_environment_session "
                f"mismatch for existing row: environment_session_attention_session_id={assoc_id}"
            )
        return existing

    return EnvironmentSessionAttentionSession(
        id=assoc_id,
        environment_session_id=environment_session_id,
        attention_session_id=attention_session_id,
        key=key,
        title=title,
        status=status,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_environment_session
