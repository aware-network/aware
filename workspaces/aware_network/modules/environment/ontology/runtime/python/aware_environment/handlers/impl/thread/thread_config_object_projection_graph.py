from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Environment Ontology
from aware_environment_ontology.thread.thread_config_object_projection_graph import ThreadConfigObjectProjectionGraph

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_meta.runtime.handler_context import current_handler_session
from aware_environment_ontology.stable_ids import (
    stable_thread_config_object_projection_graph_id,
)

# --- AWARE: USER_IMPORTS END


async def create_via_thread_config(
    thread_config_id: UUID,
    object_projection_graph_id: UUID,
    view_key: str | None = None,
    position: int | None = None,
    is_default: bool = False,
    narrative: str | None = None,
    intent: str | None = None,
) -> ThreadConfigObjectProjectionGraph:
    """
    Create a deterministic ThreadConfigObjectProjectionGraph association edge.

    Contract:
    - Identity is `(thread_config_id, object_projection_graph_id)`.
    - Projection authority is Meta-owned.
    """

    # --- AWARE: LOGIC START create_via_thread_config
    thread_config_object_projection_graph_id = stable_thread_config_object_projection_graph_id(
        thread_config_id=thread_config_id,
        object_projection_graph_id=object_projection_graph_id,
    )
    handler_session = current_handler_session()
    existing = handler_session.imap_get(
        ThreadConfigObjectProjectionGraph,
        thread_config_object_projection_graph_id,
    )
    if existing is not None:
        if (
            existing.thread_config_id != thread_config_id
            or existing.object_projection_graph_id != object_projection_graph_id
        ):
            raise RuntimeError(
                "ThreadConfigObjectProjectionGraph.create_via_thread_config "
                "mismatch for existing thread_config_object_projection_graph_id="
                f"{thread_config_object_projection_graph_id}"
            )
        return existing

    return ThreadConfigObjectProjectionGraph(
        id=thread_config_object_projection_graph_id,
        thread_config_id=thread_config_id,
        object_projection_graph_id=object_projection_graph_id,
        view_key=view_key,
        position=position,
        is_default=is_default,
        narrative=narrative,
        intent=intent,
    )
    # --- AWARE: LOGIC END create_via_thread_config
