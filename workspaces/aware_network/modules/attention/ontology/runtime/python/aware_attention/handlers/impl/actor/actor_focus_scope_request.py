from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.actor.actor_focus_scope_request import ActorFocusScopeRequest

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.stable_ids import stable_actor_focus_scope_request_id

# --- AWARE: USER_IMPORTS END


async def create_via_actor_focus_scope(
    actor_focus_scope_id: UUID, focus_scope_request_id: UUID
) -> ActorFocusScopeRequest:
    """
    Builds a new ActorFocusScopeRequest by linking ActorFocusScope to FocusScopeRequest.
    """

    # --- AWARE: LOGIC START create_via_actor_focus_scope
    actor_focus_scope_request_id = stable_actor_focus_scope_request_id(
        actor_focus_scope_id=actor_focus_scope_id,
        focus_scope_request_id=focus_scope_request_id,
    )
    return ActorFocusScopeRequest(
        id=actor_focus_scope_request_id,
        actor_focus_scope_id=actor_focus_scope_id,
        focus_scope_request_id=focus_scope_request_id,
    )
    # --- AWARE: LOGIC END create_via_actor_focus_scope
