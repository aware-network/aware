from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime

# Code
from aware_code.types import Json

# History Ontology
from aware_history_ontology.change.change_enums import (
    ChangeDeltaKind,
    ChangeType,
)
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# History
from aware_history_ontology.stable_ids import stable_change_delta_id, stable_change_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(key: str, created_at: datetime, type: ChangeType) -> Change:
    """
    Create a standalone canonical change envelope.
    """

    # --- AWARE: LOGIC START create
    session = current_handler_session()
    change_id = stable_change_id(key=key)
    existing = session.imap_get(Change, change_id)
    if existing is not None:
        if existing.key != key:
            raise RuntimeError(
                "Change.create existing Change key mismatch: "
                f"change_id={change_id} have={existing.key!r} expected={key!r}"
            )
        return existing

    return Change(
        id=change_id,
        key=key,
        created_at=created_at,
        type=type,
    )
    # --- AWARE: LOGIC END create


async def create_delta(
    change: Change, position: int, kind: ChangeDeltaKind, payload: Json, property: str | None = None
) -> ChangeDelta:
    """
    Create one delta under this Change.

    Contract:
    - Parent `change_id` is propagated by traversal lowering.
    - Stable identity is keyed by `(change_id, position)`.
    """

    # --- AWARE: LOGIC START create_delta
    session = current_handler_session()
    change_id = change.id
    if change_id is None:
        raise RuntimeError("Change.create_delta requires Change.id")

    change_delta_id = stable_change_delta_id(change_id=change_id, position=position)
    existing = session.imap_get(ChangeDelta, change_delta_id)
    if existing is not None:
        if existing.change_id != change_id:
            raise RuntimeError(
                "Change.create_delta existing ChangeDelta parent mismatch: "
                f"change_delta_id={change_delta_id} have={existing.change_id} expected={change_id}"
            )
        if existing.position != position:
            raise RuntimeError(
                "Change.create_delta existing ChangeDelta position mismatch: "
                f"change_delta_id={change_delta_id} have={existing.position} expected={position}"
            )
        return existing

    change_delta = ChangeDelta(
        id=change_delta_id,
        change_id=change_id,
        position=position,
        kind=kind,
        payload=payload,
        property=property,
    )
    change.change_deltas.append(change_delta)
    return change_delta
    # --- AWARE: LOGIC END create_delta
