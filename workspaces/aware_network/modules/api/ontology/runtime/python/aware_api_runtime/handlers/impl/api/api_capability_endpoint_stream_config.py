from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_capability_endpoint_stream_enums import (
    ApiCapabilityEndpointStreamEventKind,
    ApiCapabilityEndpointStreamMode,
)
from aware_api_ontology.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import ApiCapabilityEndpointStreamEventConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_event_config(
    api_capability_endpoint_stream_config: ApiCapabilityEndpointStreamConfig,
    kind: ApiCapabilityEndpointStreamEventKind,
    class_config_id: UUID,
    description: str | None = None,
) -> ApiCapabilityEndpointStreamEventConfig:
    """
    Create one typed stream event contract beneath this stream config.
    """

    # --- AWARE: LOGIC START create_event_config
    return await ApiCapabilityEndpointStreamEventConfig.create_via_api_capability_endpoint_stream_config(
        api_capability_endpoint_stream_config_id=api_capability_endpoint_stream_config.id,
        kind=kind,
        class_config_id=class_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_event_config


async def build_via_api_capability_endpoint_request_config(
    api_capability_endpoint_request_config_id: UUID,
    stream_mode: ApiCapabilityEndpointStreamMode,
    description: str | None = None,
) -> ApiCapabilityEndpointStreamConfig:
    """
    Create one endpoint stream contract beneath ApiCapabilityEndpointRequestConfig.
    """

    # --- AWARE: LOGIC START build_via_api_capability_endpoint_request_config
    return ApiCapabilityEndpointStreamConfig(
        api_capability_endpoint_request_config_id=api_capability_endpoint_request_config_id,
        stream_mode=stream_mode,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_api_capability_endpoint_request_config
