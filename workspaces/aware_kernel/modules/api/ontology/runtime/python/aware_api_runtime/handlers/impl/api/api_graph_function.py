from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_graph_function import ApiGraphFunction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_api_graph(
    api_graph_id: UUID, class_config_function_config_id: UUID, description: str | None = None
) -> ApiGraphFunction:
    """
    Create one standalone API-owned callable graph target.
    """

    # --- AWARE: LOGIC START create_via_api_graph
    return ApiGraphFunction(
        api_graph_id=api_graph_id,
        class_config_function_config_id=class_config_function_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api_graph
