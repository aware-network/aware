from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.thread.thread_program import ThreadProgram

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience_ontology.stable_ids import stable_thread_program_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(
    thread_id: UUID, program_id: UUID, key: str | None = None, position: int | None = None, is_default: bool = False
) -> ThreadProgram:
    """
    Construct a deterministic Thread -> Program association edge.

    Contract:
    - Identity is derived from `(thread_id, program_id)`.
    - Constructor is idempotent for repeated calls with the same pair.
    """

    # --- AWARE: LOGIC START create
    normalized_key = (key or "").strip() or None
    assoc_id = stable_thread_program_id(thread_id=thread_id, program_id=program_id)
    session = current_handler_session()
    existing = session.imap_get(ThreadProgram, assoc_id)
    if existing is not None:
        existing_key = (existing.key or "").strip() or None
        if (
            existing.program_id != program_id
            or existing.thread_id != thread_id
            or existing_key != normalized_key
            or existing.position != position
            or bool(existing.is_default) != bool(is_default)
        ):
            raise RuntimeError(
                "ThreadProgram.create payload mismatch for existing association: " f"association_id={assoc_id}"
            )
        return existing

    return ThreadProgram(
        id=assoc_id,
        program_id=program_id,
        thread_id=thread_id,
        key=normalized_key,
        position=position,
        is_default=bool(is_default),
    )
    # --- AWARE: LOGIC END create
