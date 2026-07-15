from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_capability_endpoint_response_config import ApiCapabilityEndpointResponseConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_api_capability_endpoint_request_config(
    api_capability_endpoint_request_config_id: UUID, class_config_id: UUID, description: str | None = None
) -> ApiCapabilityEndpointResponseConfig:
    """
    Create one endpoint response contract beneath ApiCapabilityEndpointRequestConfig.
    """

    # --- AWARE: LOGIC START build_via_api_capability_endpoint_request_config
    return ApiCapabilityEndpointResponseConfig(
        api_capability_endpoint_request_config_id=api_capability_endpoint_request_config_id,
        class_config_id=class_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_api_capability_endpoint_request_config
