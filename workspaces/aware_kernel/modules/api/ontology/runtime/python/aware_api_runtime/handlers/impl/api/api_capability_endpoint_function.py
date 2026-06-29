from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_api_capability_endpoint(
    api_capability_endpoint_id: UUID, name: str, api_graph_capability_function_id: UUID, description: str | None = None
) -> ApiCapabilityEndpointFunction:
    """
    Create one named endpoint-owned binding to one graph-scoped capability function.
    """

    # --- AWARE: LOGIC START create_via_api_capability_endpoint
    return ApiCapabilityEndpointFunction(
        api_capability_endpoint_id=api_capability_endpoint_id,
        name=name,
        api_graph_capability_function_id=api_graph_capability_function_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api_capability_endpoint
