from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_endpoint(
    api_capability: ApiCapability, name: str, request_class_config_id: UUID, description: str | None = None
) -> ApiCapabilityEndpoint:
    """
    Create one external/public endpoint rail under this ApiCapability.
    """

    # --- AWARE: LOGIC START create_endpoint
    return await ApiCapabilityEndpoint.create_via_api_capability(
        api_capability_id=api_capability.id,
        name=name,
        request_class_config_id=request_class_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_endpoint


async def create_via_api(api_id: UUID, name: str, description: str | None = None) -> ApiCapability:
    """
    Create one named reusable API capability contract under Api.
    """

    # --- AWARE: LOGIC START create_via_api
    return ApiCapability(
        api_id=api_id,
        name=name,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api
