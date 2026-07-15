from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.thread.thread_layout import ThreadLayout

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Environment Ontology
from aware_environment_ontology.stable_ids import stable_thread_layout_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_thread(thread_id: UUID, layout_id: UUID, key: str | None = None) -> ThreadLayout:
    """
    Create a deterministic ThreadLayout association edge.

    Contract:
    - Identity is derived from propagated parent Thread context (`_via_thread_layouts`) + `layout_id`.
    - Idempotent for repeated calls with the same parent/layout pair.
    """

    # --- AWARE: LOGIC START create_via_thread
    if not isinstance(thread_id, UUID):
        raise TypeError("ThreadLayout.create_via_thread requires thread_id (UUID)")
    if not isinstance(layout_id, UUID):
        raise TypeError("ThreadLayout.create_via_thread requires layout_id (UUID)")

    normalized_key = (key or "").strip() or None
    assoc_id = stable_thread_layout_id(thread_id=thread_id, layout_id=layout_id)

    session = current_handler_session()
    existing = session.imap_get(ThreadLayout, assoc_id)
    if existing is not None:
        return existing

    return ThreadLayout(
        id=assoc_id,
        thread_id=thread_id,
        layout_id=layout_id,
        key=normalized_key,
    )
    # --- AWARE: LOGIC END create_via_thread
