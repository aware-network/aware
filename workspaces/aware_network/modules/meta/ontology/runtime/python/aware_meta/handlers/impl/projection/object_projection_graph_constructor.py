from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.projection.object_projection_graph_constructor import ObjectProjectionGraphConstructor

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.stable_ids import stable_object_projection_graph_constructor_id

# Meta Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_object_projection_graph(
    object_projection_graph_id: UUID, root_node_id: UUID, function_constructor_id: UUID
) -> ObjectProjectionGraphConstructor:
    """
    Create deterministic ObjectProjectionGraphConstructor under one ObjectProjectionGraph.

    Contract:
    - Parent `object_projection_graph_id` is propagated by constructor lowering.
    - Identity is always OPG-scoped.
    """

    # --- AWARE: LOGIC START build_via_object_projection_graph
    object_projection_graph_constructor_id = stable_object_projection_graph_constructor_id(
        object_projection_graph_id=object_projection_graph_id,
        root_node_id=root_node_id,
        function_constructor_id=function_constructor_id,
    )
    session = current_handler_session()
    existing = session.imap_get(
        ObjectProjectionGraphConstructor,
        object_projection_graph_constructor_id,
    )
    if existing is not None:
        if (
            existing.object_projection_graph_id != object_projection_graph_id
            or existing.root_node_id != root_node_id
            or existing.function_constructor_id != function_constructor_id
        ):
            raise RuntimeError(
                "ObjectProjectionGraphConstructor.build_via_object_projection_graph payload mismatch for "
                "existing ObjectProjectionGraphConstructor: "
                f"object_projection_graph_constructor_id={object_projection_graph_constructor_id}"
            )
        return existing

    return ObjectProjectionGraphConstructor(
        id=object_projection_graph_constructor_id,
        object_projection_graph_id=object_projection_graph_id,
        root_node_id=root_node_id,
        function_constructor_id=function_constructor_id,
    )
    # --- AWARE: LOGIC END build_via_object_projection_graph
