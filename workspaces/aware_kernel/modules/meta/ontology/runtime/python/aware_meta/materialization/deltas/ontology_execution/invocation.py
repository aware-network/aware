from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from typing import cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphInvokeFunctionInput,
)


ONTOLOGY_INVOCATION_EXECUTION_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-ontology-invocation-execution.v1"
)


def ontology_invocation_runtime_preflight(
    *,
    request: object,
) -> dict[str, object]:
    runtime = _request_value(request=request, key="runtime")
    graph_runtime_context = _request_value(
        request=request,
        key="aware_meta.graph_runtime_context",
    )
    return {
        "preflight_kind": "meta_ocg_provider_delta_ontology_invocation_runtime_preflight",
        "contract_version": (
            "aware.meta.ocg.provider-delta-ontology-invocation-runtime-preflight.v1"
        ),
        "runtime_available": runtime is not None,
        "runtime_backend": type(runtime).__name__ if runtime is not None else None,
        "runtime_invoke_function_available": callable(
            getattr(runtime, "invoke_function", None)
        ),
        "runtime_invoke_instance_available": callable(
            getattr(runtime, "invoke_instance", None)
        ),
        "graph_runtime_context_available": graph_runtime_context is not None,
        "graph_runtime_context_backend": (
            type(graph_runtime_context).__name__
            if graph_runtime_context is not None
            else None
        ),
    }


async def execute_ontology_invocation_intents(
    *,
    runtime: object,
    graph_runtime_context: object,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    domain_object_instance_graph_id: UUID | None = None,
    domain_object_instance_graph_identity_id: UUID | None = None,
    invocation_intents: Sequence[Mapping[str, object]],
    initial_expected_head_commit_id: UUID | None = None,
) -> dict[str, object]:
    invoke_function = _invoke_function_callable(runtime=runtime)
    index = getattr(graph_runtime_context, "index", None)
    sorted_intents = _sorted_invocation_intents(invocation_intents)
    blockers = []
    if invoke_function is None:
        blockers.append("runtime_invoke_function_unavailable")
    if index is None:
        blockers.append("graph_runtime_context_index_unavailable")
    if not sorted_intents:
        blockers.append("ontology_invocation_intents_empty")
    if blockers:
        return _execution_payload(
            status="ontology_function_call_execution_blocked",
            reason="meta_ocg_ontology_function_call_execution_blocked",
            runtime=runtime,
            graph_runtime_context=graph_runtime_context,
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            blockers=tuple(blockers),
            invocation_intents=tuple(sorted_intents),
        )
    assert invoke_function is not None
    assert index is not None

    receipts: list[dict[str, object]] = []
    expected_head_commit_ids_by_projection_hash: dict[str, UUID | None] = {
        projection_hash: initial_expected_head_commit_id,
    }
    expected_graph_hash_pre_by_projection_hash: dict[str, str | None] = {}
    projection_hash_by_object_id: dict[UUID, str] = {}
    for intent in sorted_intents:
        input_or_blocked = _invoke_function_input_for_intent(
            index=cast(MetaGraphRuntimeIndex, index),
            actor_id=actor_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_object_instance_graph_id=domain_object_instance_graph_id,
            domain_object_instance_graph_identity_id=(
                domain_object_instance_graph_identity_id
            ),
            intent=intent,
            expected_head_commit_ids_by_projection_hash=(
                expected_head_commit_ids_by_projection_hash
            ),
            expected_graph_hash_pre_by_projection_hash=(
                expected_graph_hash_pre_by_projection_hash
            ),
            projection_hash_by_object_id=projection_hash_by_object_id,
        )
        input_blockers = _tuple_text(input_or_blocked.get("blockers"))
        if input_blockers:
            return _execution_payload(
                status="ontology_function_call_execution_blocked",
                reason="meta_ocg_ontology_function_call_input_blocked",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=input_blockers,
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
            )
        invoke_input = cast(
            MetaGraphInvokeFunctionInput,
            input_or_blocked.get("input"),
        )
        try:
            commit_receipt = await invoke_function(invoke_input)
        except Exception as exc:
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason="meta_ocg_ontology_function_call_invoke_failed",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        receipt_payload = _commit_receipt_payload(
            intent=intent,
            commit_receipt=commit_receipt,
        )
        receipts.append(receipt_payload)
        if _optional_text(receipt_payload.get("status")) != "succeeded":
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason="meta_ocg_ontology_function_call_commit_failed",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
                error_message=_optional_text(receipt_payload.get("error")),
            )
        if _commit_required_missing(receipt_payload=receipt_payload):
            return _execution_payload(
                status="ontology_function_call_execution_failed",
                reason="meta_ocg_ontology_function_call_required_commit_missing",
                runtime=runtime,
                graph_runtime_context=graph_runtime_context,
                actor_id=actor_id,
                branch_id=branch_id,
                projection_hash=projection_hash,
                blockers=(),
                invocation_intents=tuple(sorted_intents),
                invocation_receipts=tuple(receipts),
                error_message=(
                    "Ontology FunctionCall succeeded without a commit for a "
                    "commit-required intent."
                ),
            )
        receipt_projection_hash = _optional_text(receipt_payload.get("projection_hash"))
        if receipt_projection_hash is not None:
            expected_head_commit_ids_by_projection_hash[receipt_projection_hash] = (
                _uuid_value(receipt_payload.get("commit_id"))
            )
            expected_graph_hash_pre_by_projection_hash[receipt_projection_hash] = (
                _optional_text(receipt_payload.get("graph_hash_post"))
            )
            for object_id in _receipt_object_ids_for_projection_binding(
                intent=intent,
                receipt_payload=receipt_payload,
            ):
                projection_hash_by_object_id[object_id] = receipt_projection_hash

    return _execution_payload(
        status="ontology_function_call_execution_applied",
        reason="meta_ocg_ontology_function_call_execution_applied",
        runtime=runtime,
        graph_runtime_context=graph_runtime_context,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        blockers=(),
        invocation_intents=tuple(sorted_intents),
        invocation_receipts=tuple(receipts),
    )


def _invoke_function_input_for_intent(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    domain_object_instance_graph_id: UUID | None,
    domain_object_instance_graph_identity_id: UUID | None,
    intent: Mapping[str, object],
    expected_head_commit_ids_by_projection_hash: Mapping[str, UUID | None],
    expected_graph_hash_pre_by_projection_hash: Mapping[str, str | None],
    projection_hash_by_object_id: Mapping[UUID, str],
) -> dict[str, object]:
    owner_class_name = _optional_text(intent.get("owner_class_name"))
    function_name = _optional_text(intent.get("function_name"))
    invocation_mode = _optional_text(intent.get("invocation_mode"))
    blockers: list[str] = []
    if owner_class_name is None:
        blockers.append("owner_class_name_missing")
    if function_name is None:
        blockers.append("function_name_missing")
    if invocation_mode is None:
        blockers.append("invocation_mode_missing")
    if blockers:
        return {"blockers": tuple(blockers)}

    resolution = _resolve_function_for_intent(
        index=index,
        owner_class_name=owner_class_name or "",
        function_name=function_name or "",
    )
    function_id = _uuid_value(resolution.get("function_id"))
    if function_id is None:
        return {
            "blockers": (
                "ontology_function_unresolved:"
                f"{owner_class_name or 'unknown'}.{function_name or 'unknown'}",
            )
        }

    call_target = _call_target_for_mode(invocation_mode or "")
    if call_target is None:
        return {"blockers": (f"unsupported_invocation_mode:{invocation_mode}",)}

    target_object_id = None
    object_projection_graph_id = None
    invocation_projection_hash = projection_hash
    if call_target is MetaGraphCallTarget.instance:
        target_object_id = _uuid_value(intent.get("target_object_id"))
        if target_object_id is None:
            return {"blockers": ("target_object_id_missing_or_invalid",)}
        invocation_projection_hash = _invocation_projection_hash_for_instance_intent(
            index=index,
            intent=intent,
            target_object_id=target_object_id,
            default_projection_hash=projection_hash,
            projection_hash_by_object_id=projection_hash_by_object_id,
        )
    else:
        constructor_opg = _constructor_opg_for_intent(
            index=index,
            intent=intent,
            function_link_id=_uuid_value(resolution.get("function_link_id")),
            function_id=function_id,
        )
        if constructor_opg is None:
            return {
                "blockers": (
                    "ontology_constructor_opg_unresolved:"
                    f"{owner_class_name or 'unknown'}.{function_name or 'unknown'}",
                )
            }
        object_projection_graph_id = _uuid_value(getattr(constructor_opg, "id", None))
        invocation_projection_hash = _optional_text(
            getattr(constructor_opg, "projection_hash", None)
        ) or projection_hash

    expected_head_commit_id = expected_head_commit_ids_by_projection_hash.get(
        invocation_projection_hash,
    )
    expected_graph_hash_pre = expected_graph_hash_pre_by_projection_hash.get(
        invocation_projection_hash,
    )

    return {
        "blockers": (),
        "input": MetaGraphInvokeFunctionInput(
            index=index,
            actor_id=actor_id,
            function_id=function_id,
            domain_branch_id=branch_id,
            domain_projection_hash=invocation_projection_hash,
            domain_object_instance_graph_id=domain_object_instance_graph_id,
            domain_object_instance_graph_identity_id=(
                domain_object_instance_graph_identity_id
            ),
            call_target=call_target,
            target_object_id=target_object_id,
            object_projection_graph_id=object_projection_graph_id,
            args=JsonArray([]),
            kwargs=JsonObject(
                cast(dict[str, JsonValue], _mapping_text_keys(intent.get("kwargs")))
            ),
            expected_graph_hash_pre=expected_graph_hash_pre,
            expected_head_commit_id=expected_head_commit_id,
            commit=True,
            publish=False,
        ),
    }


def _resolve_function_for_intent(
    *,
    index: MetaGraphRuntimeIndex,
    owner_class_name: str,
    function_name: str,
) -> dict[str, object]:
    for class_config in _index_class_configs(index=index):
        if not _class_config_matches_owner(
            class_config=class_config,
            owner_class_name=owner_class_name,
        ):
            continue
        for function_link in getattr(
            class_config,
            "class_config_function_configs",
            (),
        ) or ():
            function_config = getattr(function_link, "function_config", None)
            if _optional_text(getattr(function_config, "name", None)) != function_name:
                continue
            function_id = (
                getattr(function_config, "id", None)
                or getattr(function_link, "function_config_id", None)
            )
            return {
                "class_config_id": getattr(class_config, "id", None),
                "function_link_id": getattr(function_link, "id", None),
                "function_id": function_id,
            }
    return {}


def _invocation_projection_hash_for_instance_intent(
    *,
    index: MetaGraphRuntimeIndex,
    intent: Mapping[str, object],
    target_object_id: UUID,
    default_projection_hash: str,
    projection_hash_by_object_id: Mapping[UUID, str],
) -> str:
    explicit_projection_hash = _optional_text(intent.get("target_projection_hash"))
    if explicit_projection_hash is not None:
        return explicit_projection_hash
    planned_projection_hash = projection_hash_by_object_id.get(target_object_id)
    if planned_projection_hash is not None:
        return planned_projection_hash
    target_projection_name = _optional_text(intent.get("target_projection_name"))
    if target_projection_name is not None:
        resolved = _projection_hash_for_name(
            index=index,
            projection_name=target_projection_name,
        )
        if resolved is not None:
            return resolved
    return default_projection_hash


def _constructor_opg_for_intent(
    *,
    index: MetaGraphRuntimeIndex,
    intent: Mapping[str, object],
    function_link_id: UUID | None,
    function_id: UUID,
) -> object | None:
    explicit_projection_hash = _optional_text(intent.get("result_projection_hash"))
    if explicit_projection_hash is not None:
        opg = _opg_for_projection_hash(
            index=index,
            projection_hash=explicit_projection_hash,
        )
        if opg is not None:
            return opg
    result_projection_name = _optional_text(intent.get("result_projection_name"))
    if result_projection_name is not None:
        opg = _opg_for_projection_name(
            index=index,
            projection_name=result_projection_name,
        )
        if opg is not None:
            return opg
    return _constructor_opg_for_function(
        index=index,
        function_link_id=function_link_id,
        function_id=function_id,
    )


def _projection_hash_for_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str | None:
    opg = _opg_for_projection_name(
        index=index,
        projection_name=projection_name,
    )
    if opg is not None:
        return _optional_text(getattr(opg, "projection_hash", None))
    return None


def _opg_for_projection_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> object | None:
    for opg in _index_opgs(index=index):
        if _optional_text(getattr(opg, "name", None)) == projection_name:
            return opg
    return None


def _opg_for_projection_hash(
    *,
    index: MetaGraphRuntimeIndex,
    projection_hash: str,
) -> object | None:
    for opg in _index_opgs(index=index):
        if _optional_text(getattr(opg, "projection_hash", None)) == projection_hash:
            return opg
    return None


def _index_class_configs(*, index: MetaGraphRuntimeIndex) -> tuple[object, ...]:
    class_configs = getattr(index, "class_configs_by_id", None)
    if isinstance(class_configs, Mapping):
        return tuple(class_configs.values())
    if isinstance(class_configs, Sequence) and not isinstance(
        class_configs,
        (str, bytes),
    ):
        return tuple(class_configs)
    return ()


def _class_config_matches_owner(
    *,
    class_config: object,
    owner_class_name: str,
) -> bool:
    candidates = _tuple_text(
        (
            getattr(class_config, "name", None),
            getattr(class_config, "class_fqn", None),
        )
    )
    for candidate in candidates:
        if owner_class_name == candidate:
            return True
        if owner_class_name.endswith(f".{candidate}"):
            return True
        if candidate.endswith(f".{owner_class_name}"):
            return True
    return False


def _constructor_opg_for_function(
    *,
    index: MetaGraphRuntimeIndex,
    function_link_id: UUID | None,
    function_id: UUID,
) -> object | None:
    ids = {
        item
        for item in (function_link_id, function_id)
        if item is not None
    }
    for opg in _index_opgs(index=index):
        for constructor in getattr(
            opg,
            "object_projection_graph_constructors",
            (),
        ) or ():
            constructor_function_id = _uuid_value(
                getattr(constructor, "function_constructor_id", None)
            )
            if constructor_function_id in ids:
                return opg
    return None


def _index_opgs(*, index: MetaGraphRuntimeIndex) -> tuple[object, ...]:
    seen: set[str] = set()
    opgs: list[object] = []
    for source in (
        getattr(index, "opg_by_id", None),
        getattr(index, "opg_by_hash", None),
    ):
        for opg in _mapping_or_sequence_values(source):
            opg_id = _optional_text(getattr(opg, "id", None))
            dedupe_key = opg_id or str(id(opg))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            opgs.append(opg)
    return tuple(opgs)


def _mapping_or_sequence_values(value: object) -> Iterable[object]:
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return ()


def _call_target_for_mode(value: str) -> MetaGraphCallTarget | None:
    if value == MetaGraphCallTarget.instance.value:
        return MetaGraphCallTarget.instance
    if value in {
        "constructor",
        MetaGraphCallTarget.opg_constructor.value,
    }:
        return MetaGraphCallTarget.opg_constructor
    return None


def _sorted_invocation_intents(
    invocation_intents: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    return tuple(
        sorted(
            (
                intent
                for intent in invocation_intents
                if isinstance(intent, Mapping)
            ),
            key=lambda intent: (
                _int_value(intent.get("invocation_order")),
                _optional_text(intent.get("intent_key")) or "",
            ),
        )
    )


def _execution_payload(
    *,
    status: str,
    reason: str,
    runtime: object,
    graph_runtime_context: object,
    actor_id: UUID,
    branch_id: UUID,
    projection_hash: str,
    blockers: tuple[str, ...],
    invocation_intents: tuple[Mapping[str, object], ...],
    invocation_receipts: tuple[Mapping[str, object], ...] = (),
    error_type: str | None = None,
    error_message: str | None = None,
) -> dict[str, object]:
    applied = status == "ontology_function_call_execution_applied"
    first_receipt = invocation_receipts[0] if invocation_receipts else {}
    last_receipt = invocation_receipts[-1] if invocation_receipts else {}
    return {
        "execution_kind": "meta_ocg_provider_delta_ontology_invocation_execution",
        "contract_version": ONTOLOGY_INVOCATION_EXECUTION_CONTRACT_VERSION,
        "status": status,
        "reason": reason,
        "available": applied,
        "blocked": status == "ontology_function_call_execution_blocked",
        "blockers": tuple(dict.fromkeys(blockers)),
        "blocker_count": len(tuple(dict.fromkeys(blockers))),
        "runtime_backend": type(runtime).__name__,
        "graph_runtime_context_backend": type(graph_runtime_context).__name__,
        "actor_id": str(actor_id),
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "invocation_intent_count": len(invocation_intents),
        "invocation_intents": tuple(dict(intent) for intent in invocation_intents),
        "applied_invocation_count": len(invocation_receipts),
        "invocation_receipts": tuple(dict(receipt) for receipt in invocation_receipts),
        "commit_id": _optional_text(last_receipt.get("commit_id")),
        "domain_commit_id": _optional_text(last_receipt.get("commit_id")),
        "object_instance_graph_commit_id": _optional_text(
            last_receipt.get("object_instance_graph_commit_id")
        ),
        "root_object_id": _optional_text(last_receipt.get("root_object_id")),
        "graph_hash_pre": _optional_text(first_receipt.get("graph_hash_pre")),
        "graph_hash_post": _optional_text(last_receipt.get("graph_hash_post")),
        "error_type": error_type,
        "error_message": error_message,
        "would_execute": bool(invocation_intents),
        "did_execute": applied,
        "would_persist": bool(invocation_intents),
        "did_persist": applied,
        "execution_wired": applied,
        "production_execution_wired": applied,
    }


def _commit_receipt_payload(
    *,
    intent: Mapping[str, object],
    commit_receipt: object,
) -> dict[str, object]:
    payload = _model_payload(commit_receipt)
    return {
        "receipt_kind": "meta_ocg_provider_delta_ontology_invocation_receipt",
        "intent_key": _optional_text(intent.get("intent_key")),
        "operation_key": _optional_text(intent.get("operation_key")),
        "semantic_key": _optional_text(intent.get("semantic_key")),
        "invocation_order": _int_value(intent.get("invocation_order")),
        "invocation_mode": _optional_text(intent.get("invocation_mode")),
        "owner_class_name": _optional_text(intent.get("owner_class_name")),
        "function_name": _optional_text(intent.get("function_name")),
        "status": _optional_text(
            getattr(commit_receipt, "status", None)
            or payload.get("status")
        ),
        "actor_id": _optional_text(
            getattr(commit_receipt, "actor_id", None)
            or payload.get("actor_id")
        ),
        "branch_id": _optional_text(
            getattr(commit_receipt, "domain_branch_id", None)
            or payload.get("domain_branch_id")
        ),
        "projection_hash": _optional_text(
            getattr(commit_receipt, "domain_projection_hash", None)
            or payload.get("domain_projection_hash")
        ),
        "expected_result_object_id": _optional_text(
            intent.get("expected_result_object_id")
        ),
        "target_projection_name": _optional_text(intent.get("target_projection_name")),
        "target_projection_hash": _optional_text(intent.get("target_projection_hash")),
        "result_projection_name": _optional_text(intent.get("result_projection_name")),
        "result_projection_hash": _optional_text(intent.get("result_projection_hash")),
        "lane_state_role": _optional_text(intent.get("lane_state_role")),
        "commit_required": _bool_value(intent.get("commit_required")),
        "commit_id": _optional_text(
            getattr(commit_receipt, "commit_id", None)
            or payload.get("commit_id")
        ),
        "object_instance_graph_commit_id": _optional_text(
            getattr(commit_receipt, "object_instance_graph_commit_id", None)
            or payload.get("object_instance_graph_commit_id")
        ),
        "root_object_id": _optional_text(
            getattr(commit_receipt, "root_object_id", None)
            or payload.get("root_object_id")
        ),
        "graph_hash_pre": _optional_text(
            getattr(commit_receipt, "graph_hash_pre", None)
            or payload.get("graph_hash_pre")
        ),
        "graph_hash_post": _optional_text(
            getattr(commit_receipt, "graph_hash_post", None)
            or payload.get("graph_hash_post")
        ),
        "function_call_id": _optional_text(
            getattr(commit_receipt, "function_call_id", None)
            or payload.get("function_call_id")
        ),
        "function_call_response_id": _optional_text(
            getattr(commit_receipt, "function_call_response_id", None)
            or payload.get("function_call_response_id")
        ),
        "error": _optional_text(
            getattr(commit_receipt, "error", None)
            or payload.get("error")
        ),
    }


def _commit_required_missing(
    *,
    receipt_payload: Mapping[str, object],
) -> bool:
    return (
        _bool_value(receipt_payload.get("commit_required"))
        and _optional_text(receipt_payload.get("commit_id")) is None
    )


def _receipt_object_ids_for_projection_binding(
    *,
    intent: Mapping[str, object],
    receipt_payload: Mapping[str, object],
) -> tuple[UUID, ...]:
    object_ids = tuple(
        object_id
        for object_id in (
            _uuid_value(intent.get("target_object_id")),
            _uuid_value(intent.get("expected_result_object_id")),
            _uuid_value(receipt_payload.get("root_object_id")),
        )
        if object_id is not None
    )
    return tuple(dict.fromkeys(object_ids))


def _request_value(*, request: object, key: str) -> object | None:
    context = getattr(request, "context", None)
    if isinstance(context, Mapping) and key in context:
        return context[key]
    return getattr(request, key, None)


def _invoke_function_callable(
    *,
    runtime: object,
) -> Callable[[MetaGraphInvokeFunctionInput], Awaitable[object]] | None:
    invoke_function = getattr(runtime, "invoke_function", None)
    if not callable(invoke_function):
        return None
    return cast(
        Callable[[MetaGraphInvokeFunctionInput], Awaitable[object]],
        invoke_function,
    )


def _mapping_text_keys(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _model_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        payload = model_dump(mode="python")
        if isinstance(payload, Mapping):
            return {str(key): item for key, item in payload.items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        text = str(value)
        return (text,) if text else ()
    if isinstance(value, Iterable):
        return tuple(
            text
            for item in value
            if (text := _optional_text(item)) is not None
        )
    text = _optional_text(value)
    return (text,) if text is not None else ()


def _uuid_value(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    text = _optional_text(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _int_value(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    text = _optional_text(value)
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = _optional_text(value)
    if text is None:
        return False
    return text.casefold() in {"1", "true", "yes", "y", "on"}


__all__ = [
    "ONTOLOGY_INVOCATION_EXECUTION_CONTRACT_VERSION",
    "execute_ontology_invocation_intents",
    "ontology_invocation_runtime_preflight",
]
