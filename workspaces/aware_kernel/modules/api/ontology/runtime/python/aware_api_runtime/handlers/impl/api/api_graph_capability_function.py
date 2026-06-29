from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_graph_capability_function import ApiGraphCapabilityFunction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_api_graph_capability(
    api_graph_capability_id: UUID, name: str, api_graph_function_id: UUID, description: str | None = None
) -> ApiGraphCapabilityFunction:
    """
    Create one named graph-scoped capability function bound to one ApiGraphFunction.
    """

    # --- AWARE: LOGIC START create_via_api_graph_capability
    return ApiGraphCapabilityFunction(
        api_graph_capability_id=api_graph_capability_id,
        name=name,
        api_graph_function_id=api_graph_function_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api_graph_capability
