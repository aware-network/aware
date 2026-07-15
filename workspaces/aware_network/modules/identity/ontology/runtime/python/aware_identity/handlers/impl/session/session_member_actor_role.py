from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session_member_actor_role import SessionMemberActorRole

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_session_member_actor_role_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_session_member(
    session_member_id: UUID,
    actor_role_id: UUID,
    source_kind: str = "identity_session",
    status: str = "active",
    evidence_json: JsonObject | None = JsonObject(),
) -> SessionMemberActorRole:
    """
    Construct one ActorRole evidence edge under a SessionMember.

    Contract:
    - `actor_role_id` resolves an existing Identity ActorRole.
    - This object records evidence only; permission lifecycle remains
      ActorRole-owned.
    """

    # --- AWARE: LOGIC START create_via_session_member
    edge_id = stable_session_member_actor_role_id(
        session_member_id=session_member_id,
        actor_role_id=actor_role_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(SessionMemberActorRole, edge_id)
    if existing is not None:
        if existing.session_member_id != session_member_id or existing.actor_role_id != actor_role_id:
            raise RuntimeError(
                "SessionMemberActorRole.create_via_session_member mismatch for existing edge: "
                f"session_member_actor_role_id={edge_id}"
            )
        return existing

    return SessionMemberActorRole(
        id=edge_id,
        session_member_id=session_member_id,
        actor_role_id=actor_role_id,
        source_kind=source_kind,
        status=status,
        evidence_json=evidence_json,
    )
    # --- AWARE: LOGIC END create_via_session_member
