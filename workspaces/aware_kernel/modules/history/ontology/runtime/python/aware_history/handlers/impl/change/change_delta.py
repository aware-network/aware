from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import Json

# History Ontology
from aware_history_ontology.change.change_enums import ChangeDeltaKind
from aware_history_ontology.change.change_delta import ChangeDelta

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# History
from aware_history_ontology.stable_ids import stable_change_delta_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_change(
    change_id: UUID, position: int, kind: ChangeDeltaKind, payload: Json, property: str | None = None
) -> ChangeDelta:
    """
    Create one delta under this Change.
    """

    # --- AWARE: LOGIC START create_via_change
    session = current_handler_session()
    change_delta_id = stable_change_delta_id(change_id=change_id, position=position)
    existing = session.imap_get(ChangeDelta, change_delta_id)
    if existing is not None:
        return existing

    return ChangeDelta(
        id=change_delta_id,
        change_id=change_id,
        position=position,
        kind=kind,
        payload=payload,
        property=property,
    )
    # --- AWARE: LOGIC END create_via_change
