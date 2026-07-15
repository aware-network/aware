from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session import Session
from aware_identity_ontology.session.session_config import SessionConfig
from aware_identity_ontology.session.session_config_actor_config import SessionConfigActorConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_session_config_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create(
    key: str,
    title: str | None = None,
    description: str | None = None,
    purpose: str | None = None,
    status: str = "active",
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionConfig:
    """
    Create one deterministic Identity SessionConfig.

    Contract:
    - Stable identity is derived from `key`.
    - This is policy vocabulary only; it does not admit or grant an actor.
    """

    # --- AWARE: LOGIC START create
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("SessionConfig.create requires non-empty key")

    session_config_id = stable_session_config_id(key=normalized_key)
    handler_session = current_handler_session()
    existing = handler_session.imap_get(SessionConfig, session_config_id)
    if existing is not None:
        existing_key = (existing.key or "").strip()
        if existing_key != normalized_key:
            raise RuntimeError(
                "SessionConfig.create key mismatch for existing session config: "
                f"session_config_id={session_config_id}"
            )
        return existing

    return SessionConfig(
        id=session_config_id,
        key=normalized_key,
        title=title,
        description=description,
        purpose=purpose,
        status=status,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END create


async def add_actor_config(
    session_config: SessionConfig,
    actor_config_id: UUID,
    status: str = "active",
    purpose: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionConfigActorConfig:
    """
    Attach one ActorConfig as eligible for this SessionConfig.

    Contract:
    - The edge is session participation policy only.
    - Concrete membership is SessionMember.
    - Concrete permission evidence is SessionMemberActorRole.
    """

    # --- AWARE: LOGIC START add_actor_config
    session_config_id = session_config.id
    if session_config_id is None:
        raise RuntimeError("SessionConfig.add_actor_config requires SessionConfig.id")

    created = await SessionConfigActorConfig.create_via_session_config(
        session_config_id=session_config_id,
        actor_config_id=actor_config_id,
        status=status,
        purpose=purpose,
        metadata_json=metadata_json,
    )
    if created.session_config_id != session_config_id:
        raise RuntimeError(
            "SessionConfig.add_actor_config context mismatch for created policy edge: "
            f"session_config_actor_config_id={created.id}"
        )
    for existing in session_config.actor_configs:
        if existing.id == created.id:
            return existing

    session_config.actor_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_actor_config


async def start_session(
    session_config: SessionConfig,
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
    Start one concrete Session under this SessionConfig.

    Contract:
    - Stable identity is SessionConfig path + `key` + `parent_session_scope_key`.
    - Root sessions use `parent_session_scope_key = "root"` and
      `parent_session_id = null`.
    - Child sessions use `parent_session_scope_key = parent_session_id`.
    - Domains may reference this Session, but Identity owns membership.
    """

    # --- AWARE: LOGIC START start_session
    session_config_id = session_config.id
    if session_config_id is None:
        raise RuntimeError("SessionConfig.start_session requires SessionConfig.id")

    created = await Session.build_via_session_config(
        session_config_id=session_config_id,
        parent_session_scope_key=parent_session_scope_key,
        key=key,
        parent_session_id=parent_session_id,
        title=title,
        description=description,
        purpose=purpose,
        status=status,
        created_by_actor_id=created_by_actor_id,
        source_kind=source_kind,
        source_ref=source_ref,
        metadata_json=metadata_json,
    )
    if created.session_config_id != session_config_id:
        raise RuntimeError(
            "SessionConfig.start_session context mismatch for created session: " f"session_id={created.id}"
        )
    for existing in session_config.sessions:
        if existing.id == created.id:
            return existing

    session_config.sessions.append(created)
    return created
    # --- AWARE: LOGIC END start_session
