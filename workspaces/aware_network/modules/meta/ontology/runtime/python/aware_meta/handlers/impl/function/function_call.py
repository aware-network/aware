from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.function.function_call_response import FunctionCallResponse

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.stable_ids import stable_function_call_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_response(
    function_call: FunctionCall,
    success: bool = True,
    error_message: str | None = None,
    execution_time_ms: int = 0,
    graph_hash_post: str | None = None,
    root_class_instance_identity_id: UUID | None = None,
) -> FunctionCallResponse:
    # --- AWARE: LOGIC START create_response
    function_call_id = function_call.id
    if function_call_id is None:
        raise RuntimeError("FunctionCall.create_response requires FunctionCall.id")

    response = await FunctionCallResponse.build_via_function_call(
        function_call_id=function_call_id,
        success=success,
        error_message=error_message,
        execution_time_ms=execution_time_ms,
        graph_hash_post=graph_hash_post,
        root_class_instance_identity_id=root_class_instance_identity_id,
    )
    if function_call.function_call_response is not None and function_call.function_call_response.id != response.id:
        raise RuntimeError(
            "FunctionCall.create_response cannot replace existing FunctionCallResponse: "
            f"function_call_id={function_call_id}"
        )
    function_call.function_call_response = response
    return response
    # --- AWARE: LOGIC END create_response


async def build_via_object_instance_graph_lane(
    object_instance_graph_lane_id: UUID,
    call_key: UUID,
    function_config_id: UUID,
    target_class_instance_identity_id: UUID | None = None,
    base_commit_id: UUID | None = None,
    graph_hash_pre: str | None = None,
) -> FunctionCall:
    """
    Build one durable FunctionCall envelope under an ObjectInstanceGraphLane.

    Contract:
    - Parent ObjectInstanceGraphLane ownership is propagated by traversal lowering.
    - `call_key` is the per-invocation identity and is required.
    - `function_config` is execution contract truth.
    - `target_class_instance_identity` is null for constructor calls until
      response materialization identifies the created root identity.
    """

    # --- AWARE: LOGIC START build_via_object_instance_graph_lane
    session = current_handler_session()
    function_call_id = stable_function_call_id(
        object_instance_graph_lane_id=object_instance_graph_lane_id,
        function_config_id=function_config_id,
        call_key=call_key,
    )

    function_config = session.imap_get(FunctionConfig, function_config_id)
    target_class_instance_identity = None
    if target_class_instance_identity_id is not None:
        target_class_instance_identity = session.imap_get(
            ClassInstanceIdentity,
            target_class_instance_identity_id,
        )
    base_commit = None
    if base_commit_id is not None:
        base_commit = session.imap_get(ObjectInstanceGraphCommit, base_commit_id)

    existing = session.imap_get(FunctionCall, function_call_id)
    if existing is not None:
        if (
            existing.object_instance_graph_lane_id != object_instance_graph_lane_id
            or existing.call_key != call_key
            or existing.function_config_id != function_config_id
            or existing.target_class_instance_identity_id != target_class_instance_identity_id
            or existing.base_commit_id != base_commit_id
            or (existing.graph_hash_pre or None) != (graph_hash_pre or None)
        ):
            raise RuntimeError(
                "FunctionCall.build_via_object_instance_graph_lane payload mismatch for existing "
                f"FunctionCall: function_call_id={function_call_id}"
            )
        if existing.function_config is None and function_config is not None:
            existing.function_config = function_config
        if existing.target_class_instance_identity is None and target_class_instance_identity is not None:
            existing.target_class_instance_identity = target_class_instance_identity
        if existing.base_commit is None and base_commit is not None:
            existing.base_commit = base_commit
        return existing

    return FunctionCall(
        id=function_call_id,
        object_instance_graph_lane_id=object_instance_graph_lane_id,
        call_key=call_key,
        function_config=function_config,
        function_config_id=function_config_id,
        target_class_instance_identity=target_class_instance_identity,
        target_class_instance_identity_id=target_class_instance_identity_id,
        base_commit=base_commit,
        base_commit_id=base_commit_id,
        graph_hash_pre=graph_hash_pre,
    )
    # --- AWARE: LOGIC END build_via_object_instance_graph_lane
