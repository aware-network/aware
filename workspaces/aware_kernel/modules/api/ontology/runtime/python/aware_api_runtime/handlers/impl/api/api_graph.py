from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Api Ontology
from aware_api_ontology.api.api_graph import ApiGraph
from aware_api_ontology.api.api_graph_capability import ApiGraphCapability
from aware_api_ontology.api.api_graph_function import ApiGraphFunction
from aware_api_ontology.api.api_graph_projection import ApiGraphProjection

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def create_graph_function(
    api_graph: ApiGraph, class_config_function_config_id: UUID, description: str | None = None
) -> ApiGraphFunction:
    """
    Create one standalone API graph callable target under this ApiGraph.
    """

    # --- AWARE: LOGIC START create_graph_function
    return await ApiGraphFunction.create_via_api_graph(
        api_graph_id=api_graph.id,
        class_config_function_config_id=class_config_function_config_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_graph_function


async def create_graph_projection(
    api_graph: ApiGraph, object_projection_graph_id: UUID, description: str | None = None
) -> ApiGraphProjection:
    """
    Create one graph-scoped projection mapping bridge under this ApiGraph.
    """

    # --- AWARE: LOGIC START create_graph_projection
    return await ApiGraphProjection.create_via_api_graph(
        api_graph_id=api_graph.id,
        object_projection_graph_id=object_projection_graph_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_graph_projection


async def create_graph_capability(
    api_graph: ApiGraph, api_capability_id: UUID, description: str | None = None
) -> ApiGraphCapability:
    """
    Bind one declared ApiCapability to this ApiGraph.
    """

    # --- AWARE: LOGIC START create_graph_capability
    return await ApiGraphCapability.create_via_api_graph(
        api_graph_id=api_graph.id,
        api_capability_id=api_capability_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_graph_capability


async def create_via_api(api_id: UUID, object_config_graph_id: UUID, description: str | None = None) -> ApiGraph:
    """
    Create one deterministic API graph bridge to one target ObjectConfigGraph.
    """

    # --- AWARE: LOGIC START create_via_api
    return ApiGraph(
        api_id=api_id,
        object_config_graph_id=object_config_graph_id,
        description=description,
    )
    # --- AWARE: LOGIC END create_via_api
