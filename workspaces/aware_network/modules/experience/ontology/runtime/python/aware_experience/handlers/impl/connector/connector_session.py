from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
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
from aware_experience.stable_ids import stable_connector_session_id
from aware_experience_ontology.connector.connector import Connector
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_connector_provider(
    connector_provider_id: UUID,
    connector_id: UUID,
    session_key: str,
    session_ref: str | None = None,
    host_ref: str | None = None,
    principal_ref: str | None = None,
    status: str = "active",
) -> ConnectorSession:
    """
    Create one deterministic Connector session under a ConnectorProvider.

    Contract:
    - Parent `ConnectorProvider` scope is propagated by constructor lowering.
    - `connector_id` binds the session to the runtime Connector fulfillment.
    - `session_key` identifies the concrete provider session.
    """

    # --- AWARE: LOGIC START build_via_connector_provider
    normalized_connector_provider_id = as_uuid(
        connector_provider_id,
        field_name="ConnectorSession.connector_provider_id",
    )
    normalized_connector_id = as_uuid(
        connector_id,
        field_name="ConnectorSession.connector_id",
    )
    normalized_session_key = required_token(
        session_key,
        field_name="ConnectorSession.session_key",
    )
    normalized_session_ref = optional_token(session_ref)
    normalized_host_ref = optional_token(host_ref)
    normalized_principal_ref = optional_token(principal_ref)
    normalized_status = status_token(status, default="active")
    session_id = stable_connector_session_id(
        connector_provider_id=normalized_connector_provider_id,
        connector_id=normalized_connector_id,
        session_key=normalized_session_key,
    )

    handler_session = current_handler_session()
    connector = handler_session.imap_get(Connector, normalized_connector_id)
    existing = handler_session.imap_get(ConnectorSession, session_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "connector_provider_id": normalized_connector_provider_id,
                "connector_id": normalized_connector_id,
                "session_key": normalized_session_key,
                "session_ref": normalized_session_ref,
                "host_ref": normalized_host_ref,
                "principal_ref": normalized_principal_ref,
                "status": normalized_status,
            },
            label="ConnectorSession",
            object_id=session_id,
        )
        return existing

    return ConnectorSession(
        id=session_id,
        connector_provider_id=normalized_connector_provider_id,
        connector_id=normalized_connector_id,
        connector=connector,
        session_key=normalized_session_key,
        session_ref=normalized_session_ref,
        host_ref=normalized_host_ref,
        principal_ref=normalized_principal_ref,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_connector_provider
