from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.graph.instance.object_instance_graph_lane import ObjectInstanceGraphLane

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# History
from aware_history_ontology.lane.lane import Lane

# Meta
from aware_meta.handlers.impl.function import function_call as function_call_handler
from aware_meta_ontology.stable_ids import stable_object_instance_graph_lane_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_function_call(
    object_instance_graph_lane: ObjectInstanceGraphLane,
    call_key: UUID,
    function_config_id: UUID,
    target_class_instance_identity_id: UUID | None = None,
    base_commit_id: UUID | None = None,
    graph_hash_pre: str | None = None,
) -> FunctionCall:
    """
    Create one durable function-call request envelope under this OIG lane.

    Contract:
    - Parent ObjectInstanceGraphLane ownership is propagated by traversal lowering.
    - `call_key` is the per-invocation identity; repeated calls on the same
      lane/function must not collapse.
    - FunctionCall is the Meta-owned execution root. Generic OIGOperation
      wrappers are intentionally not part of the clean rail.
    """

    # --- AWARE: LOGIC START create_function_call
    object_instance_graph_lane_id = object_instance_graph_lane.id
    if object_instance_graph_lane_id is None:
        raise RuntimeError("ObjectInstanceGraphLane.create_function_call requires ObjectInstanceGraphLane.id")

    created = await function_call_handler.build_via_object_instance_graph_lane(
        object_instance_graph_lane_id=object_instance_graph_lane_id,
        call_key=call_key,
        function_config_id=function_config_id,
        target_class_instance_identity_id=target_class_instance_identity_id,
        base_commit_id=base_commit_id,
        graph_hash_pre=graph_hash_pre,
    )
    if all(existing.id != created.id for existing in object_instance_graph_lane.function_calls):
        object_instance_graph_lane.function_calls.append(created)
    return created
    # --- AWARE: LOGIC END create_function_call


async def create_via_object_instance_graph_branch(
    object_instance_graph_branch_id: UUID, lane_id: UUID
) -> ObjectInstanceGraphLane:
    """
    Creates a linkage meta.ObjectInstanceGraphBranch to history.lane.

    Contract:
    - Parent ObjectInstanceGraphBranch ownership is propagated by traversal lowering.
    - Deterministic identity is constructor-keyed on `(lane_id)` plus parent path.
    """

    # --- AWARE: LOGIC START create_via_object_instance_graph_branch
    session = current_handler_session()
    oigl_id = stable_object_instance_graph_lane_id(
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        lane_id=lane_id,
    )
    existing = session.imap_get(ObjectInstanceGraphLane, oigl_id)
    if existing is not None:
        return existing

    lane = session.imap_get(Lane, lane_id)
    if lane is None:
        # Some nested runtime paths can temporarily drift `Lane._branch_id` while
        # preserving identity-map object identity. Recover by id from the local
        # session map and rebind to this session branch.
        identity_map = getattr(session, "_identity_map", None)
        raw_get = getattr(identity_map, "get", None)
        if callable(raw_get):
            candidate = raw_get(Lane, lane_id)
            if candidate is not None:
                lane = candidate
                try:
                    lane._branch_id = session.branch_id  # type: ignore[attr-defined]
                except Exception:
                    pass
    if lane is None:
        raise RuntimeError(
            "ObjectInstanceGraphLane.create_via_object requires lane to exist in OIG(pre) state: " f"lane_id={lane_id}"
        )

    return ObjectInstanceGraphLane(
        id=oigl_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        lane=lane,
        lane_id=lane_id,
    )
    # --- AWARE: LOGIC END create_via_object_instance_graph_branch
