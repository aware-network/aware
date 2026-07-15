from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session_provider_session import SessionProviderSession

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_session_provider_session_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_session(
    session_id: UUID,
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
    Attach one concrete provider capability to the parent Identity Session.

    Contract:
    - Stable identity is `(session_id, provider_session_config_id,
      provider_session_key)`.
    - This is not session ownership; many provider sessions may attach to
      one Identity Session.
    """

    # --- AWARE: LOGIC START create_via_session
    normalized_key = (provider_session_key or "").strip()
    if not normalized_key:
        raise RuntimeError("SessionProviderSession.create_via_session requires non-empty provider_session_key")

    attachment_id = stable_session_provider_session_id(
        session_id=session_id,
        provider_session_config_id=provider_session_config_id,
        provider_session_key=normalized_key,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(SessionProviderSession, attachment_id)
    if existing is not None:
        existing_key = (existing.provider_session_key or "").strip()
        if (
            existing.session_id != session_id
            or existing.provider_session_config_id != provider_session_config_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "SessionProviderSession.create_via_session mismatch for existing attachment: "
                f"session_provider_session_id={attachment_id}"
            )
        return existing

    return SessionProviderSession(
        id=attachment_id,
        session_id=session_id,
        provider_session_config_id=provider_session_config_id,
        provider_session_key=normalized_key,
        provider_session_ref=provider_session_ref,
        provider_object_instance_graph_identity_id=provider_object_instance_graph_identity_id,
        provider_class_instance_identity_id=provider_class_instance_identity_id,
        provider_object_instance_graph_branch_id=provider_object_instance_graph_branch_id,
        status=status,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END create_via_session
