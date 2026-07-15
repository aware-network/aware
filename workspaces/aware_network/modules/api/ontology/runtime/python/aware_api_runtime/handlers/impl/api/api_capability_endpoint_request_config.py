from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamMode
from aware_api_ontology.api.api_capability_endpoint_request_config import ApiCapabilityEndpointRequestConfig
from aware_api_ontology.api.api_capability_endpoint_response_config import ApiCapabilityEndpointResponseConfig
from aware_api_ontology.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_response_config(
    api_capability_endpoint_request_config: ApiCapabilityEndpointRequestConfig,
    class_config_id: UUID,
    description: str | None = None,
) -> ApiCapabilityEndpointResponseConfig:
    """
    Create one optional terminal response contract beneath this request contract.
    """

    # --- AWARE: LOGIC START create_response_config
    return await ApiCapabilityEndpointResponseConfig.build_via_api_capability_endpoint_request_config(
        api_capability_endpoint_request_config_id=api_capability_endpoint_request_config.id,
        class_config_id=class_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_response_config


async def create_stream_config(
    api_capability_endpoint_request_config: ApiCapabilityEndpointRequestConfig,
    stream_mode: ApiCapabilityEndpointStreamMode,
    description: str | None = None,
) -> ApiCapabilityEndpointStreamConfig:
    """
    Create one optional stream contract beneath this request contract.
    """

    # --- AWARE: LOGIC START create_stream_config
    return await ApiCapabilityEndpointStreamConfig.build_via_api_capability_endpoint_request_config(
        api_capability_endpoint_request_config_id=api_capability_endpoint_request_config.id,
        stream_mode=stream_mode,
        description=description,
    )
    # --- AWARE: LOGIC END create_stream_config


async def build_via_api_capability_endpoint(
    api_capability_endpoint_id: UUID, class_config_id: UUID, description: str | None = None
) -> ApiCapabilityEndpointRequestConfig:
    """
    Create one endpoint request contract beneath ApiCapabilityEndpoint.
    """

    # --- AWARE: LOGIC START build_via_api_capability_endpoint
    return ApiCapabilityEndpointRequestConfig(
        api_capability_endpoint_id=api_capability_endpoint_id,
        class_config_id=class_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_api_capability_endpoint
