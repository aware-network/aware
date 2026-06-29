from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from pydantic import BaseModel

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.graph.projection.branching import stable_portal_target_branch_id
from aware_meta.runtime.graph_commit_invocation_backend import (
    resolve_meta_graph_object_projection_graph_identity_id,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.handler_executor.execution_context import (
    MetaGraphHandlerContext,
)
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionCallable,
    MetaGraphInvokeFunctionInput,
)


@dataclass(frozen=True, slots=True)
class MetaPortalConstructorAuthorization:
    source_class_config_id: UUID
    source_instance_id: UUID
    source_object_id: UUID | None
    source_branch_id: UUID
    source_projection_hash: str
    class_config_relationship_id: UUID
    allowed_target_object_ids: frozenset[UUID]


@dataclass(frozen=True, slots=True)
class MetaPortalConstructorInvocationRequest:
    ctx: MetaGraphHandlerContext
    index: MetaGraphRuntimeIndex
    invoke_function: MetaGraphInvokeFunctionCallable | None
    target_projection_hash: str
    target_object_projection_graph_id: UUID
    target_class_config_id: UUID
    function_name: str
    payload: Mapping[str, object] | object
    target_object_id: UUID
    authorization: MetaPortalConstructorAuthorization
    target_branch_id: UUID | None = None
    commit: bool | None = None


@dataclass(frozen=True, slots=True)
class MetaPortalInvocationResult:
    status: str
    payload: JsonValue | None = None
    error: str | None = None
    branch_id: UUID | None = None
    root_object_id: UUID | None = None
    projection_hash: str | None = None
    graph_hash_pre: str | None = None
    graph_hash_post: str | None = None
    commit_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    function_call_id: UUID | None = None
    function_call_response_id: UUID | None = None


async def invoke_meta_portal_constructor(
    request: MetaPortalConstructorInvocationRequest,
) -> MetaPortalInvocationResult:
    try:
        invoke_function = request.invoke_function
        if invoke_function is None:
            raise RuntimeError(
                "Meta portal constructor invocation requires an active Meta "
                "graph invocation backend in handler execution context"
            )

        _validate_portal_authorization(request)
        target_branch_id = _resolve_target_branch_id(request)
        function_id = _resolve_function_id_for_class(
            index=request.index,
            class_config_id=request.target_class_config_id,
            function_name=request.function_name,
        )
        commit_intent = True if request.commit is None else bool(request.commit)
        commit_receipt = await invoke_function(
            MetaGraphInvokeFunctionInput(
                index=request.index,
                actor_id=request.ctx.requester_id,
                function_id=function_id,
                domain_branch_id=target_branch_id,
                domain_projection_hash=request.target_projection_hash,
                call_target=MetaGraphCallTarget.opg_constructor,
                target_object_id=request.target_object_id,
                object_projection_graph_id=(request.target_object_projection_graph_id),
                args=JsonArray([]),
                kwargs=_normalize_payload(request.payload),
                commit=commit_intent,
                publish=False,
            )
        )
        return _result_from_commit_receipt(commit_receipt)
    except Exception as exc:
        return MetaPortalInvocationResult(status="failed", error=str(exc))


def _validate_portal_authorization(
    request: MetaPortalConstructorInvocationRequest,
) -> None:
    ctx = request.ctx
    authorization = request.authorization
    if ctx.branch_id != authorization.source_branch_id:
        raise PermissionError(
            "Meta portal authorization branch mismatch: "
            f"ctx_branch_id={ctx.branch_id} "
            f"source_branch_id={authorization.source_branch_id}"
        )
    if ctx.projection_hash != authorization.source_projection_hash:
        raise PermissionError(
            "Meta portal authorization projection mismatch: "
            f"ctx_projection_hash={ctx.projection_hash} "
            f"source_projection_hash={authorization.source_projection_hash}"
        )
    if request.target_object_id not in authorization.allowed_target_object_ids:
        allowed = sorted(
            str(value) for value in authorization.allowed_target_object_ids
        )
        raise PermissionError(
            "Meta portal constructor target is not authorized by the source "
            "field request: "
            f"target_object_id={request.target_object_id} allowed={allowed}"
        )


def _resolve_target_branch_id(
    request: MetaPortalConstructorInvocationRequest,
) -> UUID:
    ctx = request.ctx
    source_object_instance_graph_id = ctx.domain_object_instance_graph_id
    if source_object_instance_graph_id is None:
        raise RuntimeError(
            "Meta portal constructor invocation requires source "
            "domain_object_instance_graph_id in handler context"
        )
    target_opg = request.index.opg_by_hash.get(request.target_projection_hash)
    if target_opg is None:
        raise RuntimeError(
            "Meta portal constructor target projection is missing from index: "
            f"projection_hash={request.target_projection_hash}"
        )
    if target_opg.id != request.target_object_projection_graph_id:
        raise RuntimeError(
            "Meta portal constructor target OPG id mismatch: "
            f"projection_hash={request.target_projection_hash} "
            f"opg_id={target_opg.id} "
            f"request_opg_id={request.target_object_projection_graph_id}"
        )
    target_opgi_id = resolve_meta_graph_object_projection_graph_identity_id(
        index=request.index,
        opg=target_opg,
    )
    canonical_branch_id = stable_portal_target_branch_id(
        object_instance_graph_id=source_object_instance_graph_id,
        object_projection_graph_identity_id=target_opgi_id,
        target_object_id=request.target_object_id,
    )
    if (
        request.target_branch_id is not None
        and request.target_branch_id != canonical_branch_id
    ):
        raise PermissionError(
            "Meta portal constructor invocation uses deterministic target "
            "branches in v0: "
            f"requested_branch_id={request.target_branch_id} "
            f"canonical_branch_id={canonical_branch_id}"
        )
    return canonical_branch_id


def _resolve_function_id_for_class(
    *,
    index: MetaGraphRuntimeIndex,
    class_config_id: UUID,
    function_name: str,
) -> UUID:
    class_config = index.class_configs_by_id.get(class_config_id)
    if class_config is not None:
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                return function_config.id

    for node in index.ocg.object_config_graph_nodes:
        node_class_config = node.class_config
        if node_class_config is None or node_class_config.id != class_config_id:
            continue
        for edge in node_class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                return function_config.id

    raise RuntimeError(
        "FunctionConfig not found for Meta portal constructor: "
        f"class_config_id={class_config_id} function_name={function_name!r}"
    )


def _normalize_payload(payload: Mapping[str, object] | object) -> JsonObject:
    if isinstance(payload, JsonObject):
        return payload
    if isinstance(payload, dict):
        payload_dict = cast(dict[object, object], payload)
        if all(isinstance(key, str) for key in payload_dict):
            return JsonObject(
                {
                    str(key): _jsonify_payload(value)
                    for key, value in payload_dict.items()
                }
            )
    if isinstance(payload, Mapping):
        payload_map = cast(Mapping[object, object], payload)
        return JsonObject(
            {str(key): _jsonify_payload(value) for key, value in payload_map.items()}
        )
    if isinstance(payload, BaseModel):
        model_payload = cast(dict[str, object], payload.model_dump(mode="json"))
        return _normalize_payload(model_payload)
    return JsonObject({"value": _jsonify_payload(payload)})


def _jsonify_payload(payload: object) -> JsonValue:
    if payload is None:
        return None
    if isinstance(payload, (str, int, float, bool)):
        return payload
    if isinstance(payload, UUID):
        return str(payload)
    if isinstance(payload, BaseModel):
        return _jsonify_payload(payload.model_dump(mode="json"))
    if isinstance(payload, Mapping):
        payload_map = cast(Mapping[object, object], payload)
        return {str(key): _jsonify_payload(value) for key, value in payload_map.items()}
    if isinstance(payload, (list, tuple, set)):
        return [_jsonify_payload(value) for value in payload]
    return str(payload)


def _result_from_commit_receipt(
    receipt: MetaGraphCommitReceipt,
) -> MetaPortalInvocationResult:
    return MetaPortalInvocationResult(
        status=receipt.status,
        payload=receipt.payload,
        error=receipt.error,
        branch_id=receipt.domain_branch_id,
        root_object_id=receipt.root_object_id,
        projection_hash=receipt.domain_projection_hash,
        graph_hash_pre=receipt.graph_hash_pre,
        graph_hash_post=receipt.graph_hash_post,
        commit_id=receipt.commit_id,
        object_instance_graph_commit_id=(receipt.object_instance_graph_commit_id),
        function_call_id=receipt.function_call_id,
        function_call_response_id=receipt.function_call_response_id,
    )


__all__ = [
    "MetaPortalConstructorAuthorization",
    "MetaPortalConstructorInvocationRequest",
    "MetaPortalInvocationResult",
    "invoke_meta_portal_constructor",
]
