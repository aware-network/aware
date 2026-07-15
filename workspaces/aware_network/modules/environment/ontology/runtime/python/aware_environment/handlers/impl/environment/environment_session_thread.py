from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Environment Ontology
from aware_environment_ontology.environment.environment_session_thread import EnvironmentSessionThread

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_environment_session_thread_id,
)

# --- AWARE: USER_IMPORTS END


async def select_attention_session(
    environment_session_thread: EnvironmentSessionThread, attention_session_id: UUID | None = None
) -> EnvironmentSessionThread:
    """
    Select the session-local AttentionSession resolution for this pin.

    Contract:
    - Mutates only the invoked EnvironmentSessionThread.
    - Does not mutate Thread, ThreadLayout, AttentionSession, or
      EnvironmentNavigationContext.
    """

    # --- AWARE: LOGIC START select_attention_session
    environment_session_thread.attention_session_id = attention_session_id
    environment_session_thread.attention_session = None
    return environment_session_thread
    # --- AWARE: LOGIC END select_attention_session


async def build_via_environment_session(
    environment_session_id: UUID,
    thread_id: UUID,
    thread_layout_id: UUID,
    attention_session_id: UUID | None = None,
    key: str | None = None,
    title: str | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> EnvironmentSessionThread:
    """
    Construct one session-local Thread/Layout resolution row.

    Contract:
    - Stable identity is EnvironmentSession path + Thread + ThreadLayout.
    - `thread_layout_id` points at a Thread-owned layout attachment.
    - `attention_session_id` points at an Environment-owned
      EnvironmentSessionAttentionSession row.
    - Mutating attention pointer on this row records session-local attention
      resolution history through commits.
    """

    # --- AWARE: LOGIC START build_via_environment_session
    session_thread_id = stable_environment_session_thread_id(
        environment_session_id=environment_session_id,
        thread_id=thread_id,
        thread_layout_id=thread_layout_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(EnvironmentSessionThread, session_thread_id)
    if existing is not None:
        if (
            existing.environment_session_id != environment_session_id
            or existing.thread_id != thread_id
            or existing.thread_layout_id != thread_layout_id
        ):
            raise RuntimeError(
                "EnvironmentSessionThread.build_via_environment_session "
                f"mismatch for existing row: environment_session_thread_id={session_thread_id}"
            )
        return existing

    return EnvironmentSessionThread(
        id=session_thread_id,
        environment_session_id=environment_session_id,
        thread_id=thread_id,
        thread_layout_id=thread_layout_id,
        attention_session_id=attention_session_id,
        key=key,
        title=title,
        status=status,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_environment_session
