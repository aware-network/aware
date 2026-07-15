from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_operation_api_view_capability_endpoint import SdkOperationApiViewCapabilityEndpoint

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import (
    stable_sdk_operation_api_view_capability_endpoint_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_sdk_operation(
    sdk_operation_id: UUID,
    sdk_operation_api_capability_endpoint_id: UUID,
    api_view_id: UUID,
    api_view_capability_endpoint_id: UUID,
    api_view_ref: str,
    action_key: str,
    endpoint_ref: str,
) -> SdkOperationApiViewCapabilityEndpoint:
    """
    Create one deterministic SDK operation binding to one API view endpoint.

    Contract:
    - `sdk_operation_api_capability_endpoint_id` points at the SDK-owned
      operation endpoint row.
    - `api_view_capability_endpoint_id` points at API-owned view action
      truth.
    - `api_view_ref`, `action_key`, and `endpoint_ref` are copied from API
      view capability endpoint resolution for runtime consumers.
    """

    # --- AWARE: LOGIC START create_via_sdk_operation
    normalized_api_view_ref = (api_view_ref or "").strip()
    normalized_action_key = (action_key or "").strip()
    normalized_endpoint_ref = (endpoint_ref or "").strip()
    if not normalized_api_view_ref or not normalized_action_key or not normalized_endpoint_ref:
        raise RuntimeError(
            "SdkOperationApiViewCapabilityEndpoint.create_via_sdk_operation "
            "requires api_view_ref, action_key, and endpoint_ref"
        )
    return SdkOperationApiViewCapabilityEndpoint(
        id=stable_sdk_operation_api_view_capability_endpoint_id(
            sdk_operation_id=sdk_operation_id,
            sdk_operation_api_capability_endpoint_id=(sdk_operation_api_capability_endpoint_id),
            api_view_id=api_view_id,
            api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        ),
        sdk_operation_id=sdk_operation_id,
        sdk_operation_api_capability_endpoint_id=(sdk_operation_api_capability_endpoint_id),
        api_view_id=api_view_id,
        api_view_capability_endpoint_id=api_view_capability_endpoint_id,
        api_view_ref=normalized_api_view_ref,
        action_key=normalized_action_key,
        endpoint_ref=normalized_endpoint_ref,
    )
    # --- AWARE: LOGIC END create_via_sdk_operation
