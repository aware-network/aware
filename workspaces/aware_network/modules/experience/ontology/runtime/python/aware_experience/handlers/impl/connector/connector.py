from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.connector.connector import Connector

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
from aware_experience.stable_ids import stable_connector_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_connector_config(
    connector_config_id: UUID, connector_instance_key: str, runtime_ref: str | None = None, status: str = "active"
) -> Connector:
    """
    Create one deterministic Connector instance under a ConnectorConfig.

    Contract:
    - Parent `ConnectorConfig` scope is propagated by constructor lowering.
    - `connector_instance_key` identifies this runtime fulfillment.
    """

    # --- AWARE: LOGIC START build_via_connector_config
    normalized_connector_config_id = as_uuid(
        connector_config_id,
        field_name="Connector.connector_config_id",
    )
    normalized_connector_instance_key = required_token(
        connector_instance_key,
        field_name="Connector.connector_instance_key",
    )
    normalized_runtime_ref = optional_token(runtime_ref)
    normalized_status = status_token(status, default="active")
    connector_id = stable_connector_id(
        connector_config_id=normalized_connector_config_id,
        connector_instance_key=normalized_connector_instance_key,
    )

    session = current_handler_session()
    existing = session.imap_get(Connector, connector_id)
    if existing is not None:
        ensure_existing_payload(
            existing,
            fields={
                "connector_config_id": normalized_connector_config_id,
                "connector_instance_key": normalized_connector_instance_key,
                "runtime_ref": normalized_runtime_ref,
                "status": normalized_status,
            },
            label="Connector",
            object_id=connector_id,
        )
        return existing

    return Connector(
        id=connector_id,
        connector_config_id=normalized_connector_config_id,
        connector_instance_key=normalized_connector_instance_key,
        runtime_ref=normalized_runtime_ref,
        status=normalized_status,
    )
    # --- AWARE: LOGIC END build_via_connector_config
