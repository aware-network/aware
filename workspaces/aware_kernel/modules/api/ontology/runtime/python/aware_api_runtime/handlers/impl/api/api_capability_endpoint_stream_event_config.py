from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamEventKind
from aware_api_ontology.api.api_capability_endpoint_stream_event_config import ApiCapabilityEndpointStreamEventConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_api_capability_endpoint_stream_config(
    api_capability_endpoint_stream_config_id: UUID,
    kind: ApiCapabilityEndpointStreamEventKind,
    class_config_id: UUID,
    description: str | None = None,
) -> ApiCapabilityEndpointStreamEventConfig:
    """
    Create one typed stream event contract beneath ApiCapabilityEndpointStreamConfig.
    """

    # --- AWARE: LOGIC START create_via_api_capability_endpoint_stream_config
    return ApiCapabilityEndpointStreamEventConfig(
        api_capability_endpoint_stream_config_id=api_capability_endpoint_stream_config_id,
        kind=kind,
        class_config_id=class_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api_capability_endpoint_stream_config
