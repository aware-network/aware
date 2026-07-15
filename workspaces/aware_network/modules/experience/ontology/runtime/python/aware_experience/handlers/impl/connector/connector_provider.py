from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.connector.connector_provider import ConnectorProvider
from aware_experience_ontology.connector.connector_session import ConnectorSession

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.handlers.impl._constructor_helpers import (
    as_uuid,
    ensure_existing_payload,
    optional_token,
    required_token,
    status_token,
)
from aware_experience.stable_ids import stable_connector_provider_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_session(
    connector_provider: ConnectorProvider,
    connector_id: UUID,
    session_key: str,
    session_ref: str | None = None,
    host_ref: str | None = None,
    principal_ref: str | None = None,
    status: str = "active",
) -> ConnectorSession:
    """
    Create one concrete provider session bound to a Connector instance.

    Contract:
    - Provider config stays reusable.
    - Session identity captures the concrete fulfillment context, e.g.
      a YouTube Music session on the FutureHills clinic computer.
    - The linked Connector owns fulfilled Sensor/Actuator instances.
    """

    # --- AWARE: LOGIC START create_session
    normalized_status = status_token(status, default="active")
    created = await ConnectorSession.build_via_connector_provider(
        connector_provider_id=connector_provider.id,
        connector_id=connector_id,
        session_key=session_key,
        session_ref=session_ref,
        host_ref=host_ref,
        principal_ref=principal_ref,
        status=normalized_status,
    )
    for existing in connector_provider.sessions:
        if existing.id == created.id:
            return existing
    connector_provider.sessions.append(created)
    return created
    # --- AWARE: LOGIC END create_session


async def build_via_connector_config(
    connector_config_id: UUID,
    provider_key: str,
    provider_kind: str,
    provider_ref: str | None = None,
    label: str | None = None,
    description: str | None = None,
) -> ConnectorProvider:
    """
    Create one deterministic provider config under a ConnectorConfig.

    Contract:
    - Parent `ConnectorConfig` scope is propagated by constructor lowering.
    - `provider_key` is stable within the Connector config.
    - `provider_kind` identifies the concrete external provider.
    """

    # --- AWARE: LOGIC START build_via_connector_config
    normalized_connector_config_id = as_uuid(
        connector_config_id,
        field_name="ConnectorProvider.connector_config_id",
    )
    normalized_provider_key = required_token(
        provider_key,
        field_name="ConnectorProvider.provider_key",
    )
    normalized_provider_kind = required_token(
        provider_kind,
        field_name="ConnectorProvider.provider_kind",
    )
    normalized_provider_ref = optional_token(provider_ref)
    normalized_label = optional_token(label)
    normalized_description = optional_token(description)
    provider_id = stable_connector_provider_id(
        connector_config_id=normalized_connector_config_id,
        provider_key=normalized_provider_key,
    )

    session = current_handler_session()
    existing = session.imap_get(ConnectorProvider, provider_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "connector_config_id": normalized_connector_config_id,
                "provider_key": normalized_provider_key,
                "provider_kind": normalized_provider_kind,
                "provider_ref": normalized_provider_ref,
                "label": normalized_label,
                "description": normalized_description,
            },
            label="ConnectorProvider",
            object_id=provider_id,
        )
        return existing

    return ConnectorProvider(
        id=provider_id,
        connector_config_id=normalized_connector_config_id,
        provider_key=normalized_provider_key,
        provider_kind=normalized_provider_kind,
        provider_ref=normalized_provider_ref,
        label=normalized_label,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_connector_config
