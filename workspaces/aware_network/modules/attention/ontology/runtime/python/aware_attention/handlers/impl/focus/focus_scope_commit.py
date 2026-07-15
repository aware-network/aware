from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.focus.focus_scope_commit import FocusScopeCommit

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_focus_scope_commit_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_focus_scope(
    focus_scope_id: UUID, focus_id: UUID, object_instance_graph_commit_id: UUID
) -> FocusScopeCommit:
    """
    Attach one existing Meta OIG commit under this FocusScope.
    """

    # --- AWARE: LOGIC START create_via_focus_scope
    focus_scope_commit_id = stable_focus_scope_commit_id(
        focus_scope_id=focus_scope_id,
        focus_id=focus_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    session = current_handler_session()
    existing = session.imap_get(FocusScopeCommit, focus_scope_commit_id)
    if existing is not None:
        return existing
    return FocusScopeCommit(
        id=focus_scope_commit_id,
        focus_scope_id=focus_scope_id,
        focus_id=focus_id,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    # --- AWARE: LOGIC END create_via_focus_scope
