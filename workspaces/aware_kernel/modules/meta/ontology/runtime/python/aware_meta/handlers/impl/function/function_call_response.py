from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_call_response import FunctionCallResponse

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_instance_identity import ClassInstanceIdentity
from aware_meta_ontology.function.function_call import FunctionCall
from aware_meta_ontology.stable_ids import stable_function_call_response_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_function_call(
    function_call_id: UUID,
    success: bool = True,
    error_message: str | None = None,
    execution_time_ms: int = 0,
    graph_hash_post: str | None = None,
    root_class_instance_identity_id: UUID | None = None,
) -> FunctionCallResponse:
    """
    Build a deterministic response envelope under a FunctionCall scope.
    """

    # --- AWARE: LOGIC START build_via_function_call
    session = current_handler_session()
    function_call = session.imap_get(FunctionCall, function_call_id)
    if function_call is None:
        raise RuntimeError(
            "FunctionCallResponse.build_via_function_call requires existing FunctionCall: "
            f"function_call_id={function_call_id}"
        )

    function_call_response_id = stable_function_call_response_id(
        function_call_id=function_call_id,
    )
    root_class_instance_identity = None
    if root_class_instance_identity_id is not None:
        root_class_instance_identity = session.imap_get(
            ClassInstanceIdentity,
            root_class_instance_identity_id,
        )

    existing = session.imap_get(FunctionCallResponse, function_call_response_id)
    if existing is not None:
        if (
            existing.function_call_id != function_call_id
            or existing.success != success
            or (existing.error_message or None) != (error_message or None)
            or existing.execution_time_ms != execution_time_ms
            or (existing.graph_hash_post or None) != (graph_hash_post or None)
            or existing.root_class_instance_identity_id != root_class_instance_identity_id
        ):
            raise RuntimeError(
                "FunctionCallResponse.build_via_function_call payload mismatch for existing "
                f"FunctionCallResponse: function_call_response_id={function_call_response_id}"
            )
        if existing.root_class_instance_identity is None and root_class_instance_identity is not None:
            existing.root_class_instance_identity = root_class_instance_identity
        if function_call.function_call_response is None:
            function_call.function_call_response = existing
        return existing

    response = FunctionCallResponse(
        id=function_call_response_id,
        function_call_id=function_call_id,
        success=success,
        error_message=error_message,
        execution_time_ms=execution_time_ms,
        graph_hash_post=graph_hash_post,
        root_class_instance_identity=root_class_instance_identity,
        root_class_instance_identity_id=root_class_instance_identity_id,
    )
    function_call.function_call_response = response
    return response
    # --- AWARE: LOGIC END build_via_function_call
