from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session_provider_session_config import SessionProviderSessionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_session_provider_session_config_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def create_via_session_provider(
    session_provider_id: UUID,
    config_key: str,
    session_config_id: UUID,
    title: str | None = None,
    status: str = "active",
    provider_contract_ref: str | None = None,
    selection_policy: str = "contract_required",
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionProviderSessionConfig:
    """
    Bind one provider capability to one Identity SessionConfig.

    Contract:
    - Stable identity is `(session_provider_id, config_key,
      session_config_id)`.
    - This is provider capability eligibility only.
    """

    # --- AWARE: LOGIC START create_via_session_provider
    normalized_key = (config_key or "").strip()
    if not normalized_key:
        raise RuntimeError("SessionProviderSessionConfig.create_via_session_provider requires non-empty config_key")

    binding_id = stable_session_provider_session_config_id(
        session_provider_id=session_provider_id,
        config_key=normalized_key,
        session_config_id=session_config_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(SessionProviderSessionConfig, binding_id)
    if existing is not None:
        existing_key = (existing.config_key or "").strip()
        if (
            existing.session_provider_id != session_provider_id
            or existing.session_config_id != session_config_id
            or existing_key != normalized_key
        ):
            raise RuntimeError(
                "SessionProviderSessionConfig.create_via_session_provider mismatch for existing binding: "
                f"session_provider_session_config_id={binding_id}"
            )
        return existing

    return SessionProviderSessionConfig(
        id=binding_id,
        session_provider_id=session_provider_id,
        config_key=normalized_key,
        session_config_id=session_config_id,
        title=title,
        status=status,
        provider_contract_ref=provider_contract_ref,
        selection_policy=selection_policy,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END create_via_session_provider
