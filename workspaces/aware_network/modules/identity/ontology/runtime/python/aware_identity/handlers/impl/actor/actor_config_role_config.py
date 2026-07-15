from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.actor.actor_config_role_config import ActorConfigRoleConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_actor_config_role_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_via_actor_config(actor_config_id: UUID, role_config_id: UUID) -> ActorConfigRoleConfig:
    """
    Create a deterministic ActorConfigRoleConfig association edge.

    Contract:
    - Parent ActorConfig scope is propagated by constructor lowering.
    - Stable identity is `(actor_config_id, role_config_id)`.
    - This is policy vocabulary only; it is not an ActorRole grant.
    """

    # --- AWARE: LOGIC START create_via_actor_config
    session = current_handler_session()
    actor_config_role_config_id = stable_actor_config_role_config_id(
        actor_config_id=actor_config_id,
        role_config_id=role_config_id,
    )

    existing = session.imap_get(ActorConfigRoleConfig, actor_config_role_config_id)
    if existing is not None:
        if existing.actor_config_id != actor_config_id or existing.role_config_id != role_config_id:
            raise RuntimeError(
                "ActorConfigRoleConfig.create_via_actor_config payload mismatch for existing association: "
                f"actor_config_role_config_id={actor_config_role_config_id}"
            )
        return existing

    return ActorConfigRoleConfig(
        id=actor_config_role_config_id,
        actor_config_id=actor_config_id,
        role_config_id=role_config_id,
    )
    # --- AWARE: LOGIC END create_via_actor_config
