from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_graph_projection import ApiGraphProjection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_via_api_graph(
    api_graph_id: UUID, object_projection_graph_id: UUID, description: str | None = None
) -> ApiGraphProjection:
    """
    Create deterministic graph-scoped projection bridge.
    """

    # --- AWARE: LOGIC START create_via_api_graph
    return ApiGraphProjection(
        api_graph_id=api_graph_id,
        object_projection_graph_id=object_projection_graph_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api_graph
