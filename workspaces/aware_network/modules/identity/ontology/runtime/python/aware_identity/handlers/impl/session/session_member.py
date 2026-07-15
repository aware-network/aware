from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session_member import SessionMember
from aware_identity_ontology.session.session_member_actor_role import SessionMemberActorRole

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.session.session_config_actor_config import (
    SessionConfigActorConfig,
)
from aware_identity_ontology.stable_ids import stable_session_member_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def add_actor_role(
    session_member: SessionMember,
    actor_role_id: UUID,
    source_kind: str = "identity_session",
    status: str = "active",
    evidence_json: JsonObject | None = JsonObject(),
) -> SessionMemberActorRole:
    """
    Record an existing Identity ActorRole as SessionMember evidence.

    Contract:
    - This does not grant, revoke, scope, or expire permission.
    - Identity owns ActorRole lifecycle and any future temporal semantics.
    """

    # --- AWARE: LOGIC START add_actor_role
    session_member_id = session_member.id
    if session_member_id is None:
        raise RuntimeError("SessionMember.add_actor_role requires SessionMember.id")

    created = await SessionMemberActorRole.create_via_session_member(
        session_member_id=session_member_id,
        actor_role_id=actor_role_id,
        source_kind=source_kind,
        status=status,
        evidence_json=evidence_json,
    )
    if created.session_member_id != session_member_id:
        raise RuntimeError(
            "SessionMember.add_actor_role context mismatch for created actor-role evidence: "
            f"session_member_actor_role_id={created.id}"
        )
    for existing in session_member.actor_roles:
        if existing.id == created.id:
            return existing

    session_member.actor_roles.append(created)
    return created
    # --- AWARE: LOGIC END add_actor_role


async def create_via_session(
    session_id: UUID,
    actor_id: UUID,
    session_actor_config_id: UUID,
    status: str = "active",
    joined_at_unix_ms: int | None = None,
    left_at_unix_ms: int | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionMember:
    """
    Construct one SessionMember under a Session.

    Contract:
    - Identity is Session-scoped by Actor.
    - Session participation policy is selected by SessionConfigActorConfig.
    - Role evidence must be added as child ActorRole edges, not scalar UUIDs.
    """

    # --- AWARE: LOGIC START create_via_session
    member_id = stable_session_member_id(session_id=session_id, actor_id=actor_id)
    handler_session = current_handler_session()
    existing = handler_session.imap_get(SessionMember, member_id)
    if existing is not None:
        if existing.session_id != session_id or existing.actor_id != actor_id:
            raise RuntimeError(
                "SessionMember.create_via_session mismatch for existing member: " f"session_member_id={member_id}"
            )
        return existing

    session_actor_config = handler_session.imap_get(
        SessionConfigActorConfig,
        session_actor_config_id,
    )
    return SessionMember(
        id=member_id,
        session_id=session_id,
        actor_id=actor_id,
        session_actor_config_id=session_actor_config_id,
        session_actor_config=session_actor_config,
        status=status,
        joined_at_unix_ms=joined_at_unix_ms,
        left_at_unix_ms=left_at_unix_ms,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END create_via_session
