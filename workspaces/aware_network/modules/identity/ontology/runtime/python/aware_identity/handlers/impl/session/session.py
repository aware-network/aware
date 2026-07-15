from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session import Session
from aware_identity_ontology.session.session_member import SessionMember
from aware_identity_ontology.session.session_provider_session import SessionProviderSession

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_session_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def join_actor(
    session: Session,
    actor_id: UUID,
    session_actor_config_id: UUID,
    status: str = "active",
    joined_at_unix_ms: int | None = None,
    left_at_unix_ms: int | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionMember:
    """
    Join one Actor to this Session under a SessionConfigActorConfig.

    Contract:
    - `session_actor_config_id` is required and points to session policy.
    - Stable identity is `(session_id, actor_id)`.
    - Member ActorRole evidence is added through SessionMemberActorRole.
    """

    # --- AWARE: LOGIC START join_actor
    session_id = session.id
    if session_id is None:
        raise RuntimeError("Session.join_actor requires Session.id")

    created = await SessionMember.create_via_session(
        session_id=session_id,
        actor_id=actor_id,
        session_actor_config_id=session_actor_config_id,
        status=status,
        joined_at_unix_ms=joined_at_unix_ms,
        left_at_unix_ms=left_at_unix_ms,
        metadata_json=metadata_json,
    )
    if created.session_id != session_id:
        raise RuntimeError("Session.join_actor context mismatch for created member: " f"session_member_id={created.id}")
    for existing in session.members:
        if existing.id == created.id:
            return existing

    session.members.append(created)
    return created
    # --- AWARE: LOGIC END join_actor


async def attach_provider_session(
    session: Session,
    provider_session_config_id: UUID,
    provider_session_key: str,
    provider_session_ref: str | None = None,
    provider_object_instance_graph_identity_id: UUID | None = None,
    provider_class_instance_identity_id: UUID | None = None,
    provider_object_instance_graph_branch_id: UUID | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionProviderSession:
    """
    Attach one provider-owned domain session/capability to this shared
    Identity Session.

    Contract:
    - Session remains the actor participation envelope.
    - Provider attachment is many-per-Session, not a singular owner.
    - Provider-specific detail is referenced through generic Meta graph
      portals or an opaque bridge ref; Identity does not import provider
      domain ontology.
    """

    # --- AWARE: LOGIC START attach_provider_session
    session_id = session.id
    if session_id is None:
        raise RuntimeError("Session.attach_provider_session requires Session.id")

    created = await SessionProviderSession.create_via_session(
        session_id=session_id,
        provider_session_config_id=provider_session_config_id,
        provider_session_key=provider_session_key,
        provider_session_ref=provider_session_ref,
        provider_object_instance_graph_identity_id=provider_object_instance_graph_identity_id,
        provider_class_instance_identity_id=provider_class_instance_identity_id,
        provider_object_instance_graph_branch_id=provider_object_instance_graph_branch_id,
        status=status,
        metadata_json=metadata_json,
    )
    if created.session_id != session_id:
        raise RuntimeError(
            "Session.attach_provider_session context mismatch for provider attachment: "
            f"session_provider_session_id={created.id}"
        )
    for existing in session.provider_sessions:
        if existing.id == created.id:
            return existing

    session.provider_sessions.append(created)
    return created
    # --- AWARE: LOGIC END attach_provider_session


async def build_via_session_config(
    session_config_id: UUID,
    key: str,
    parent_session_scope_key: str = "root",
    parent_session_id: UUID | None = None,
    title: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    status: str = "active",
    created_by_actor_id: UUID | None = None,
    source_kind: str | None = None,
    source_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> Session:
    """
    Construct one Session under a SessionConfig.

    Contract:
    - Stable identity is SessionConfig path + `key` + `parent_session_scope_key`.
    - Root sessions use `parent_session_scope_key = "root"` and
      `parent_session_id = null`.
    - Child sessions use `parent_session_scope_key = parent_session_id`.
    - The relationship is parent-only. Do not add a reverse child-session
      ownership rail.
    - Does not resolve Process/Thread/Layout/Attention.
    - Does not grant roles; Identity ActorRole truth remains separate.
    """

    # --- AWARE: LOGIC START build_via_session_config
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("Session.build_via_session_config requires non-empty key")
    normalized_parent_scope_key = (parent_session_scope_key or "root").strip()
    if parent_session_id is None:
        if normalized_parent_scope_key != "root":
            raise RuntimeError("Root Identity sessions must use parent_session_scope_key='root'")
    else:
        expected_parent_scope_key = str(parent_session_id)
        if normalized_parent_scope_key != expected_parent_scope_key:
            raise RuntimeError(
                "Child Identity sessions must use parent_session_scope_key equal " "to parent_session_id"
            )

    session_id = stable_session_id(
        session_config_id=session_config_id,
        parent_session_scope_key=normalized_parent_scope_key,
        key=normalized_key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(Session, session_id)
    if existing is not None:
        existing_key = (existing.key or "").strip()
        existing_parent_scope_key = (existing.parent_session_scope_key or "root").strip()
        if (
            existing.session_config_id != session_config_id
            or existing_parent_scope_key != normalized_parent_scope_key
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "Session.build_via_session_config key mismatch for existing session: " f"session_id={session_id}"
            )
        return existing

    return Session(
        id=session_id,
        session_config_id=session_config_id,
        parent_session_id=parent_session_id,
        parent_session_scope_key=normalized_parent_scope_key,
        key=normalized_key,
        title=title,
        description=description,
        purpose=purpose,
        status=status,
        created_by_actor_id=created_by_actor_id,
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END build_via_session_config
