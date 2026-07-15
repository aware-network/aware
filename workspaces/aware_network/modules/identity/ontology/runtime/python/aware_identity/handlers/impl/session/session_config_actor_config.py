from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session_config_actor_config import SessionConfigActorConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_session_config_actor_config_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_session_config(
    session_config_id: UUID,
    actor_config_id: UUID,
    status: str = "active",
    purpose: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionConfigActorConfig:
    """
    Create one deterministic SessionConfig -> ActorConfig policy edge.

    Contract:
    - Stable identity is `(session_config_id, actor_config_id)`.
    - This is eligibility vocabulary only.
    """

    # --- AWARE: LOGIC START create_via_session_config
    edge_id = stable_session_config_actor_config_id(
        session_config_id=session_config_id,
        actor_config_id=actor_config_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(SessionConfigActorConfig, edge_id)
    if existing is not None:
        if existing.session_config_id != session_config_id or existing.actor_config_id != actor_config_id:
            raise RuntimeError(
                "SessionConfigActorConfig.create_via_session_config mismatch for existing edge: "
                f"session_config_actor_config_id={edge_id}"
            )
        return existing

    return SessionConfigActorConfig(
        id=edge_id,
        session_config_id=session_config_id,
        actor_config_id=actor_config_id,
        status=status,
        purpose=purpose,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END create_via_session_config
