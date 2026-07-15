from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Identity Ontology
from aware_identity_ontology.session.session_provider import SessionProvider
from aware_identity_ontology.session.session_provider_session_config import SessionProviderSessionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_session_provider_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def register(
    provider_key: str,
    provider_kind: str = "provider",
    title: str | None = None,
    status: str = "active",
    contract_ref: str | None = None,
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionProvider:
    """
    Register one provider-neutral session capability descriptor.

    Contract:
    - Stable identity is derived from `provider_key`.
    - This does not grant actors access and does not activate provider
      behavior.
    """

    # --- AWARE: LOGIC START register
    normalized_key = (provider_key or "").strip()
    if not normalized_key:
        raise RuntimeError("SessionProvider.register requires non-empty provider_key")

    provider_id = stable_session_provider_id(provider_key=normalized_key)
    handler_session = current_handler_session()
    existing = handler_session.imap_get(SessionProvider, provider_id)
    if existing is not None:
        existing_key = (existing.provider_key or "").strip()
        if existing_key != normalized_key:
            raise RuntimeError(
                "SessionProvider.register key mismatch for existing provider: " f"session_provider_id={provider_id}"
            )
        return existing

    return SessionProvider(
        id=provider_id,
        provider_key=normalized_key,
        provider_kind=provider_kind,
        title=title,
        status=status,
        contract_ref=contract_ref,
        metadata_json=metadata_json,
    )
    # --- AWARE: LOGIC END register


async def bind_session_config(
    session_provider: SessionProvider,
    config_key: str,
    session_config_id: UUID,
    title: str | None = None,
    status: str = "active",
    provider_contract_ref: str | None = None,
    selection_policy: str = "contract_required",
    metadata_json: JsonObject | None = JsonObject(),
) -> SessionProviderSessionConfig:
    """
    Declare that this provider can attach concrete provider sessions under
    one Identity SessionConfig.

    Contract:
    - This is provider/config eligibility vocabulary only.
    - A concrete attachment is `SessionProviderSession` under `Session`.
    """

    # --- AWARE: LOGIC START bind_session_config
    provider_id = session_provider.id
    if provider_id is None:
        raise RuntimeError("SessionProvider.bind_session_config requires SessionProvider.id")

    created = await SessionProviderSessionConfig.create_via_session_provider(
        session_provider_id=provider_id,
        config_key=config_key,
        session_config_id=session_config_id,
        title=title,
        status=status,
        provider_contract_ref=provider_contract_ref,
        selection_policy=selection_policy,
        metadata_json=metadata_json,
    )
    if created.session_provider_id != provider_id:
        raise RuntimeError(
            "SessionProvider.bind_session_config context mismatch for created binding: "
            f"session_provider_session_config_id={created.id}"
        )
    for existing in session_provider.session_provider_session_configs:
        if existing.id == created.id:
            return existing

    session_provider.session_provider_session_configs.append(created)
    return created
    # --- AWARE: LOGIC END bind_session_config
