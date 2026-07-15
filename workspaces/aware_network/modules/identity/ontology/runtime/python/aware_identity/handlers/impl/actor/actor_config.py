from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.actor.actor_enums import ActorType
from aware_identity_ontology.actor.actor_config import ActorConfig
from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_actor_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(
    key: str, title: str | None = None, description: str | None = None, type: ActorType | None = None
) -> ActorConfig:
    """
    Create one deterministic Identity-owned ActorConfig.

    Contract:
    - Stable identity is derived from `key`.
    - The object is pure policy vocabulary; it does not grant access by itself.
    - Concrete grants are Identity Role / ActorRole materialization.
    """

    # --- AWARE: LOGIC START create
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ActorConfig.create requires non-empty key")

    actor_config_id = stable_actor_config_id(key=normalized_key)
    session = current_handler_session()
    existing = session.imap_get(ActorConfig, actor_config_id)
    if existing is not None:
        existing_key = (existing.key or "").strip()
        if existing_key != normalized_key:
            raise RuntimeError(
                "ActorConfig.create key mismatch for existing actor config: " f"actor_config_id={actor_config_id}"
            )
        return existing

    return ActorConfig(
        id=actor_config_id,
        key=normalized_key,
        title=title,
        description=description,
        type=type,
    )
    # --- AWARE: LOGIC END create


async def add_role_config(actor_config: ActorConfig, role_config_id: UUID) -> ActorConfigRoleConfig:
    """
    Attach one RoleConfig to this ActorConfig archetype.

    Contract:
    - The edge is eligibility vocabulary only.
    - Admission scopes consume this bundle and delegate concrete role
      assignment back to Identity.
    """

    # --- AWARE: LOGIC START add_role_config
    actor_config_id = actor_config.id
    if actor_config_id is None:
        raise RuntimeError("ActorConfig.add_role_config requires id")

    created = await ActorConfigRoleConfig.create_via_actor_config(
        actor_config_id=actor_config_id,
        role_config_id=role_config_id,
    )
    if created.actor_config_id != actor_config_id:
        raise RuntimeError(
            "ActorConfig.add_role_config context mismatch for created association: "
            f"actor_config_role_config_id={created.id}"
        )
    for existing in actor_config.role_configs:
        if existing.id == created.id:
            return existing

    actor_config.role_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_role_config
