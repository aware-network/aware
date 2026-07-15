from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_operation_api_capability_endpoint import SdkOperationApiCapabilityEndpoint

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_operation_api_capability_endpoint_id

# --- AWARE: USER_IMPORTS END


async def create_via_sdk_operation(
    sdk_operation_id: UUID,
    name: str,
    api_capability_endpoint_id: UUID,
    endpoint_ref: str | None = None,
    discriminant: str | None = None,
    role: str = "primary",
    order: int = 1,
    required: bool = True,
) -> SdkOperationApiCapabilityEndpoint:
    """
    Create one deterministic SDK operation binding to one API capability endpoint.
    """

    # --- AWARE: LOGIC START create_via_sdk_operation
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkOperationApiCapabilityEndpoint.create_via_sdk_operation requires non-empty name")
    normalized_endpoint_ref = (endpoint_ref or "").strip() or None
    normalized_discriminant = (discriminant or "").strip() or None
    normalized_role = (role or "").strip() or "primary"
    return SdkOperationApiCapabilityEndpoint(
        id=stable_sdk_operation_api_capability_endpoint_id(
            sdk_operation_id=sdk_operation_id,
            name=normalized_name,
            api_capability_endpoint_id=api_capability_endpoint_id,
        ),
        sdk_operation_id=sdk_operation_id,
        name=normalized_name,
        api_capability_endpoint_id=api_capability_endpoint_id,
        endpoint_ref=normalized_endpoint_ref,
        discriminant=normalized_discriminant,
        role=normalized_role,
        order=order,
        required=required,
    )
    # --- AWARE: LOGIC END create_via_sdk_operation
