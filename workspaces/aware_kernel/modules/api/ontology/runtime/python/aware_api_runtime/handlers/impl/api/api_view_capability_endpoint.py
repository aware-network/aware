from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_api_view(
    api_view_id: UUID,
    action_key: str,
    api_capability_endpoint_id: UUID,
    endpoint_ref: str,
    description: str | None = None,
) -> ApiViewCapabilityEndpoint:
    """
    Create one deterministic endpoint-backed action binding beneath ApiView.

    Contract:
    - Identity is scoped by parent `ApiView` and `api_capability_endpoint`.
    - `action_key` is the stable dispatch key exposed to Experience/Interface
      consumers and must not be used to duplicate the same endpoint.
    """

    # --- AWARE: LOGIC START build_via_api_view
    return ApiViewCapabilityEndpoint(
        api_view_id=api_view_id,
        action_key=action_key,
        api_capability_endpoint_id=api_capability_endpoint_id,
        endpoint_ref=endpoint_ref,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_api_view
