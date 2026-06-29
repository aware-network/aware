from __future__ import annotations

from collections.abc import Mapping

from aware_code.semantic_graph_execution import SemanticGraphFunctionInvocation
from aware_code.semantic_materialization import SemanticFunctionCallContext
from aware_api_runtime.semantic_functions.execution import (
    api_semantic_function_call_execution_backend_from_context,
)
from aware_api_runtime.semantic_function_refs import (
    API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
    API_CREATE_CAPABILITY_FUNCTION_REF,
    API_CREATE_FUNCTION_REF,
)
from aware_api_runtime.workspace_provider.deltas.typed_operations import (
    api_delta_operation_count_by_field,
)


API_TYPED_OPERATION_EXECUTION_PREFLIGHT_CONTRACT_VERSION = (
    "aware.api.provider-delta.typed-operation-execution-preflight.v1"
)
API_TYPED_OPERATION_EXECUTION_UPDATE_UPSERT_BLOCK_REASON = "api_provider_delta_typed_operation_execution_requires_update_upsert_executor_support"
API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON = (
    "api_provider_delta_typed_operation_execution_requires_typed_executor_support"
)
API_PROVIDER_KEY = "aware_api"
API_TYPED_OPERATION_EXECUTION_READY_REASON = (
    "api_provider_delta_typed_operation_execution_ready"
)
API_TYPED_OPERATION_EXECUTION_SUPPORTED_FAMILIES = frozenset(
    ("create", "update", "upsert")
)


def api_delta_typed_operation_execution_preflight(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> dict[str, object]:
    typed_operations = tuple(
        _mapping_payload(operation)
        for operation in _tuple_evidence(
            provider_delta_typed_operation_plan.get("typed_operations")
        )
        if isinstance(operation, Mapping)
    )
    blocked_operations = tuple(
        _mapping_payload(operation)
        for operation in _tuple_evidence(
            provider_delta_typed_operation_plan.get("blocked_operations")
        )
        if isinstance(operation, Mapping)
    )
    operation_preflights = tuple(
        api_delta_typed_operation_execution_operation_preflight(
            operation=operation,
        )
        for operation in typed_operations
    )
    missing_fields_by_operation = {
        str(preflight["operation_key"]): tuple(
            str(field) for field in _tuple_evidence(preflight.get("missing_fields"))
        )
        for preflight in operation_preflights
        if preflight["payload_complete"] is not True
    }
    family_counts = api_delta_operation_count_by_field(
        operations=typed_operations,
        field_name="operation_family",
    )
    operation_type_counts = api_delta_operation_count_by_field(
        operations=typed_operations,
        field_name="provider_operation_type",
    )
    plan_ready = (
        provider_delta_typed_operation_plan.get("status")
        == "typed_operation_plan_ready"
        and provider_delta_typed_operation_plan.get("blocked") is not True
    )
    update_operation_count = family_counts.get("update", 0)
    upsert_operation_count = family_counts.get("upsert", 0)
    unsupported_operation_count = sum(
        1
        for preflight in operation_preflights
        if preflight["executor_support_ready"] is not True
    )
    payload_complete = plan_ready and not missing_fields_by_operation
    status, reason = api_delta_typed_operation_execution_preflight_status_reason(
        plan_ready=plan_ready,
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
        typed_operation_count=len(typed_operations),
        payload_complete=payload_complete,
        update_operation_count=update_operation_count,
        upsert_operation_count=upsert_operation_count,
        unsupported_operation_count=unsupported_operation_count,
    )
    blocked = status not in {
        "typed_operation_execution_empty",
        "typed_operation_execution_ready",
    }
    return {
        "preflight_kind": "api_provider_delta_typed_operation_execution_preflight",
        "contract_version": (API_TYPED_OPERATION_EXECUTION_PREFLIGHT_CONTRACT_VERSION),
        "status": status,
        "reason": reason,
        "source": "aware_api.provider_delta.typed_operation_plan",
        "provider_key": API_PROVIDER_KEY,
        "typed_operation_plan_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "typed_operation_plan_reason": _optional_text(
            provider_delta_typed_operation_plan.get("reason")
        ),
        "typed_operation_plan_blocked": (
            provider_delta_typed_operation_plan.get("blocked") is True
        ),
        "typed_operation_count": len(typed_operations),
        "blocked_plan_operation_count": len(blocked_operations),
        "payload_completeness_checked": plan_ready,
        "payload_complete": payload_complete,
        "payload_ready_operation_count": (
            len(typed_operations) - len(missing_fields_by_operation)
        ),
        "payload_missing_operation_count": len(missing_fields_by_operation),
        "payload_missing_fields_by_operation": missing_fields_by_operation,
        "operation_family_counts": family_counts,
        "operation_type_counts": operation_type_counts,
        "create_operation_count": family_counts.get("create", 0),
        "update_operation_count": update_operation_count,
        "upsert_operation_count": upsert_operation_count,
        "delete_operation_count": family_counts.get("delete", 0),
        "noop_operation_count": family_counts.get("noop", 0),
        "unsupported_operation_count": unsupported_operation_count,
        "typed_operation_executor_declared": True,
        "create_executor_support_ready": True,
        "update_upsert_executor_support_ready": True,
        "delete_executor_support_ready": False,
        "operation_execution_preflights": operation_preflights,
        "available": plan_ready,
        "blocked": blocked,
        "blocked_status": status if blocked else None,
        "blocked_reason": reason if blocked else None,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def api_delta_typed_operation_execution_operation_preflight(
    *,
    operation: Mapping[str, object],
) -> dict[str, object]:
    operation_key = _optional_text(operation.get("operation_key"))
    if operation_key is None:
        operation_key = _optional_text(operation.get("semantic_key")) or "unknown"
    missing_fields = api_delta_typed_operation_execution_missing_fields(
        operation=operation,
    )
    operation_family = _optional_text(operation.get("operation_family"))
    executor_support_ready = (
        operation_family in API_TYPED_OPERATION_EXECUTION_SUPPORTED_FAMILIES
    )
    return {
        "operation_key": operation_key,
        "semantic_key": _optional_text(operation.get("semantic_key")),
        "operation_family": operation_family,
        "provider_operation_type": _optional_text(
            operation.get("provider_operation_type")
        ),
        "payload_complete": not missing_fields,
        "missing_fields": tuple(missing_fields),
        "executor_support_ready": executor_support_ready,
        "executor_block_reason": (
            None
            if executor_support_ready
            else API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON
        ),
        "would_execute": executor_support_ready and not missing_fields,
        "did_execute": False,
        "execution_wired": executor_support_ready,
    }


def api_delta_typed_operation_execution_missing_fields(
    *,
    operation: Mapping[str, object],
) -> tuple[str, ...]:
    missing: list[str] = []
    for field_name in (
        "operation_key",
        "operation_family",
        "provider_operation_type",
        "semantic_key",
    ):
        if _optional_text(operation.get(field_name)) is None:
            missing.append(field_name)
    api_operation = operation.get("api_operation")
    if not isinstance(api_operation, Mapping):
        missing.append("api_operation")
    else:
        missing.extend(
            api_delta_typed_api_operation_missing_fields(
                api_operation=_mapping_payload(api_operation),
            )
        )
    current_payload = operation.get("current")
    if not isinstance(current_payload, Mapping):
        missing.append("current")
    elif not isinstance(_mapping_payload(current_payload).get("payload"), Mapping):
        missing.append("current.payload")
    operation_family = _optional_text(operation.get("operation_family"))
    if operation_family in {"update", "upsert"}:
        baseline_payload = operation.get("baseline")
        if not isinstance(baseline_payload, Mapping):
            missing.append("baseline")
        elif (
            _optional_text(_mapping_payload(baseline_payload).get("object_id")) is None
        ):
            missing.append("baseline.object_id")
    return tuple(missing)


def api_delta_typed_api_operation_missing_fields(
    *,
    api_operation: Mapping[str, object],
) -> tuple[str, ...]:
    missing: list[str] = []
    operation_name = _optional_text(api_operation.get("operation"))
    if operation_name is None:
        missing.append("api_operation.operation")
    if _optional_text(api_operation.get("operation_family")) is None:
        missing.append("api_operation.operation_family")
    raw_arguments = api_operation.get("arguments")
    if not isinstance(raw_arguments, Mapping):
        missing.append("api_operation.arguments")
        return tuple(missing)
    arguments = _mapping_payload(raw_arguments)
    for argument_name in api_delta_typed_api_operation_required_arguments(
        operation_name=operation_name,
    ):
        if _optional_text(arguments.get(argument_name)) is None:
            missing.append(f"api_operation.arguments.{argument_name}")
    return tuple(missing)


def api_delta_typed_api_operation_required_arguments(
    *,
    operation_name: str | None,
) -> tuple[str, ...]:
    return {
        "ensure_api": ("name",),
        "ensure_api_capability": ("api_semantic_key", "name"),
        "ensure_api_capability_endpoint": (
            "capability_semantic_key",
            "name",
            "request_class_ref",
        ),
    }.get(operation_name or "", ())


def api_delta_typed_operation_execution_preflight_status_reason(
    *,
    plan_ready: bool,
    provider_delta_typed_operation_plan: Mapping[str, object],
    typed_operation_count: int,
    payload_complete: bool,
    update_operation_count: int,
    upsert_operation_count: int,
    unsupported_operation_count: int,
) -> tuple[str, str]:
    if not plan_ready:
        return (
            "typed_operation_execution_preflight_blocked",
            (
                _optional_text(provider_delta_typed_operation_plan.get("reason"))
                or "api_provider_delta_typed_operation_execution_requires_ready_plan"
            ),
        )
    if typed_operation_count == 0:
        return (
            "typed_operation_execution_empty",
            "api_provider_delta_typed_operation_execution_no_operations",
        )
    if not payload_complete:
        return (
            "typed_operation_execution_payload_incomplete",
            "api_provider_delta_typed_operation_execution_payload_incomplete",
        )
    if unsupported_operation_count > 0:
        return (
            "typed_operation_execution_blocked",
            API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON,
        )
    return (
        "typed_operation_execution_ready",
        API_TYPED_OPERATION_EXECUTION_READY_REASON,
    )


async def api_delta_execute_typed_operation_plan(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_typed_operation_execution_preflight: Mapping[str, object],
    context: Mapping[str, object],
    continue_on_failure: bool = False,
) -> dict[str, object]:
    typed_operations = tuple(
        _mapping_payload(operation)
        for operation in _tuple_evidence(
            provider_delta_typed_operation_plan.get("typed_operations")
        )
        if isinstance(operation, Mapping)
    )
    payload: dict[str, object] = {
        "execution_kind": "api_provider_delta_typed_operation_execution",
        "enabled": True,
        "continue_on_failure": continue_on_failure,
        "typed_operation_count": len(typed_operations),
        "typed_operation_execution_preflight_status": _optional_text(
            provider_delta_typed_operation_execution_preflight.get("status")
        ),
        "typed_operation_execution_preflight_reason": _optional_text(
            provider_delta_typed_operation_execution_preflight.get("reason")
        ),
        "would_execute": True,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
    }
    if provider_delta_typed_operation_execution_preflight.get("status") != (
        "typed_operation_execution_ready"
    ):
        payload.update(
            {
                "status": "preflight_not_ready",
                "reason": (
                    _optional_text(
                        provider_delta_typed_operation_execution_preflight.get("reason")
                    )
                    or "api_provider_delta_typed_operation_execution_preflight_not_ready"
                ),
                "execution_wired": False,
                "status_counts": {},
                "step_count": 0,
                "steps": (),
            }
        )
        return payload

    backend = api_semantic_function_call_execution_backend_from_context(
        context,
    )
    if backend is None:
        payload.update(
            {
                "status": "backend_unavailable",
                "reason": (
                    "api_provider_delta_typed_operation_execution_backend_unavailable"
                ),
                "execution_wired": False,
                "status_counts": {},
                "step_count": 0,
                "steps": (),
            }
        )
        return payload

    function_call_context = SemanticFunctionCallContext.from_materialization_context(
        context,
        provider_key=API_PROVIDER_KEY,
    )
    current_semantic_object_ids = _string_map(
        function_call_context.current_semantic_object_ids
    )
    resolved_argument_ref_object_ids = _string_map(
        function_call_context.resolved_argument_ref_object_ids
    )
    planned_object_ids: dict[str, str] = {}
    steps: list[dict[str, object]] = []
    status_counts: dict[str, int] = {}
    for ordinal, operation in enumerate(typed_operations, start=1):
        operation_payload = api_delta_typed_operation_invocation_payload(
            operation=operation,
            current_semantic_object_ids=current_semantic_object_ids,
            planned_object_ids=planned_object_ids,
            resolved_argument_ref_object_ids=resolved_argument_ref_object_ids,
        )
        if operation_payload["status"] != "ready":
            steps.append(
                api_delta_typed_operation_blocked_step(
                    operation=operation,
                    ordinal=ordinal,
                    reason=(
                        _optional_text(operation_payload.get("reason"))
                        or "api_provider_delta_typed_operation_not_ready"
                    ),
                )
            )
            status_counts["blocked"] = status_counts.get("blocked", 0) + 1
            if not continue_on_failure:
                break
            continue
        invocation = operation_payload["invocation"]
        if not isinstance(invocation, SemanticGraphFunctionInvocation):
            steps.append(
                api_delta_typed_operation_blocked_step(
                    operation=operation,
                    ordinal=ordinal,
                    reason="api_provider_delta_typed_operation_invocation_missing",
                )
            )
            status_counts["blocked"] = status_counts.get("blocked", 0) + 1
            if not continue_on_failure:
                break
            continue
        try:
            result = await backend.invoke(invocation)
        except Exception as exc:
            steps.append(
                api_delta_typed_operation_failed_step(
                    operation=operation,
                    ordinal=ordinal,
                    invocation=invocation,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            status_counts["failed"] = status_counts.get("failed", 0) + 1
            if not continue_on_failure:
                break
            continue
        result_payload = result.evidence_payload()
        semantic_key = _optional_text(operation.get("semantic_key"))
        result_object_id = _optional_text(result.object_id)
        if semantic_key is not None and result_object_id is not None:
            planned_object_ids[semantic_key] = result_object_id
        steps.append(
            {
                "status": "invoked",
                "resolution_status": api_delta_typed_operation_resolution_status(
                    operation=operation,
                ),
                "operation_key": _optional_text(operation.get("operation_key")),
                "operation_family": _optional_text(operation.get("operation_family")),
                "provider_operation_type": _optional_text(
                    operation.get("provider_operation_type")
                ),
                "semantic_key": semantic_key,
                "function_ref": invocation.function_ref,
                "call_target": invocation.call_target,
                "receiver_object_id": invocation.receiver_object_id,
                "result_object_id": result.object_id,
                "commit_id": result_payload.get("commit_id"),
                "head_commit_id": result_payload.get("head_commit_id"),
                "branch_id": result_payload.get("branch_id"),
                "projection_hash": result_payload.get("projection_hash"),
                "evidence": {
                    "operation": dict(operation),
                    "invocation": invocation.evidence_payload(),
                    "result": result_payload,
                },
            }
        )
        status_counts["invoked"] = status_counts.get("invoked", 0) + 1

    status = api_delta_typed_operation_execution_status(
        status_counts=status_counts,
    )
    invoked_count = status_counts.get("invoked", 0)
    payload.update(
        {
            "status": status,
            "reason": api_delta_typed_operation_execution_reason(status=status),
            "execution_wired": True,
            "did_execute": invoked_count > 0,
            "status_counts": dict(sorted(status_counts.items())),
            "step_count": len(steps),
            "steps": tuple(steps),
            "current_semantic_object_id_count": len(current_semantic_object_ids),
            "resolved_argument_ref_object_id_count": len(
                resolved_argument_ref_object_ids
            ),
            "result_object_ids_by_semantic_key": dict(
                sorted(planned_object_ids.items())
            ),
            "production_execution_wired": invoked_count > 0,
        }
    )
    return payload


def api_delta_typed_operation_invocation_payload(
    *,
    operation: Mapping[str, object],
    current_semantic_object_ids: Mapping[str, str],
    planned_object_ids: Mapping[str, str],
    resolved_argument_ref_object_ids: Mapping[str, str],
) -> dict[str, object]:
    api_operation = _mapping_payload(operation.get("api_operation"))
    operation_name = _optional_text(api_operation.get("operation"))
    arguments = _mapping_payload(api_operation.get("arguments"))
    operation_family = _optional_text(operation.get("operation_family"))
    semantic_key = _optional_text(operation.get("semantic_key"))
    if operation_family not in API_TYPED_OPERATION_EXECUTION_SUPPORTED_FAMILIES:
        return {
            "status": "blocked",
            "reason": API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON,
        }
    if operation_name == "ensure_api":
        return {
            "status": "ready",
            "invocation": SemanticGraphFunctionInvocation(
                call_target="constructor",
                function_ref=API_CREATE_FUNCTION_REF,
                arguments={
                    "name": arguments.get("name"),
                    "description": arguments.get("description"),
                },
                provider_key=API_PROVIDER_KEY,
                result_semantic_key=semantic_key,
                evidence=api_delta_typed_operation_invocation_evidence(
                    operation=operation,
                ),
            ),
        }
    if operation_name == "ensure_api_capability":
        receiver_semantic_key = _optional_text(
            api_operation.get("receiver_semantic_key")
        ) or _optional_text(arguments.get("api_semantic_key"))
        receiver_object_id = _resolve_typed_operation_receiver_object_id(
            receiver_semantic_key=receiver_semantic_key,
            current_semantic_object_ids=current_semantic_object_ids,
            planned_object_ids=planned_object_ids,
        )
        if receiver_object_id is None:
            return {
                "status": "blocked",
                "reason": "api_provider_delta_typed_operation_receiver_unresolved",
                "receiver_semantic_key": receiver_semantic_key,
            }
        return {
            "status": "ready",
            "invocation": SemanticGraphFunctionInvocation(
                call_target="instance",
                function_ref=API_CREATE_CAPABILITY_FUNCTION_REF,
                receiver_object_id=receiver_object_id,
                arguments={
                    "name": arguments.get("name"),
                    "description": arguments.get("description"),
                },
                provider_key=API_PROVIDER_KEY,
                result_semantic_key=semantic_key,
                evidence=api_delta_typed_operation_invocation_evidence(
                    operation=operation,
                ),
            ),
        }
    if operation_name == "ensure_api_capability_endpoint":
        receiver_semantic_key = _optional_text(
            api_operation.get("receiver_semantic_key")
        ) or _optional_text(arguments.get("capability_semantic_key"))
        receiver_object_id = _resolve_typed_operation_receiver_object_id(
            receiver_semantic_key=receiver_semantic_key,
            current_semantic_object_ids=current_semantic_object_ids,
            planned_object_ids=planned_object_ids,
        )
        if receiver_object_id is None:
            return {
                "status": "blocked",
                "reason": "api_provider_delta_typed_operation_receiver_unresolved",
                "receiver_semantic_key": receiver_semantic_key,
            }
        request_class_ref = _optional_text(arguments.get("request_class_ref"))
        request_class_config_id = (
            resolved_argument_ref_object_ids.get(request_class_ref)
            if request_class_ref is not None
            else None
        )
        if request_class_config_id is None:
            return {
                "status": "blocked",
                "reason": (
                    "api_provider_delta_typed_operation_argument_ref_unresolved"
                ),
                "argument_ref": request_class_ref,
            }
        return {
            "status": "ready",
            "invocation": SemanticGraphFunctionInvocation(
                call_target="instance",
                function_ref=API_CAPABILITY_CREATE_ENDPOINT_FUNCTION_REF,
                receiver_object_id=receiver_object_id,
                arguments={
                    "name": arguments.get("name"),
                    "description": arguments.get("description"),
                    "request_class_config_id": request_class_config_id,
                },
                provider_key=API_PROVIDER_KEY,
                result_semantic_key=semantic_key,
                evidence=api_delta_typed_operation_invocation_evidence(
                    operation=operation,
                ),
            ),
        }
    return {
        "status": "blocked",
        "reason": "api_provider_delta_typed_operation_unknown_api_operation",
        "operation": operation_name,
    }


def api_delta_typed_operation_invocation_evidence(
    *,
    operation: Mapping[str, object],
) -> dict[str, object]:
    return {
        "operation_key": _optional_text(operation.get("operation_key")),
        "operation_family": _optional_text(operation.get("operation_family")),
        "provider_operation_type": _optional_text(
            operation.get("provider_operation_type")
        ),
        "semantic_key": _optional_text(operation.get("semantic_key")),
        "api_operation": _mapping_payload(operation.get("api_operation")),
        "source_entry_key": _optional_text(operation.get("source_entry_key")),
        "source_delta_key": _optional_text(operation.get("source_delta_key")),
    }


def api_delta_typed_operation_blocked_step(
    *,
    operation: Mapping[str, object],
    ordinal: int,
    reason: str,
) -> dict[str, object]:
    return {
        "status": "blocked",
        "ordinal": ordinal,
        "reason": reason,
        "operation_key": _optional_text(operation.get("operation_key")),
        "operation_family": _optional_text(operation.get("operation_family")),
        "provider_operation_type": _optional_text(
            operation.get("provider_operation_type")
        ),
        "semantic_key": _optional_text(operation.get("semantic_key")),
        "evidence": {"operation": dict(operation)},
    }


def api_delta_typed_operation_failed_step(
    *,
    operation: Mapping[str, object],
    ordinal: int,
    invocation: SemanticGraphFunctionInvocation,
    error: str,
) -> dict[str, object]:
    return {
        "status": "failed",
        "ordinal": ordinal,
        "error": error,
        "operation_key": _optional_text(operation.get("operation_key")),
        "operation_family": _optional_text(operation.get("operation_family")),
        "provider_operation_type": _optional_text(
            operation.get("provider_operation_type")
        ),
        "semantic_key": _optional_text(operation.get("semantic_key")),
        "function_ref": invocation.function_ref,
        "call_target": invocation.call_target,
        "receiver_object_id": invocation.receiver_object_id,
        "evidence": {
            "operation": dict(operation),
            "invocation": invocation.evidence_payload(),
        },
    }


def api_delta_typed_operation_execution_status(
    *,
    status_counts: Mapping[str, int],
) -> str:
    if status_counts.get("failed", 0) > 0:
        return "failed"
    if status_counts.get("blocked", 0) > 0:
        return "blocked"
    if status_counts.get("invoked", 0) > 0:
        return "executed"
    return "no_operations"


def api_delta_typed_operation_execution_reason(*, status: str) -> str:
    return {
        "executed": "api_provider_delta_typed_operation_execution_invoked",
        "blocked": "api_provider_delta_typed_operation_execution_blocked",
        "failed": "api_provider_delta_typed_operation_execution_failed",
        "no_operations": "api_provider_delta_typed_operation_execution_no_operations",
    }.get(status, "api_provider_delta_typed_operation_execution_status_unknown")


def api_delta_typed_operation_resolution_status(
    *,
    operation: Mapping[str, object],
) -> str:
    operation_family = _optional_text(operation.get("operation_family")) or "unknown"
    subject_kind = _optional_text(operation.get("ontology_subject_kind")) or (
        "api_semantic_object"
    )
    subject_status = "root" if subject_kind == "api" else "child"
    return f"typed_{operation_family}_{subject_status}"


def _resolve_typed_operation_receiver_object_id(
    *,
    receiver_semantic_key: str | None,
    current_semantic_object_ids: Mapping[str, str],
    planned_object_ids: Mapping[str, str],
) -> str | None:
    if receiver_semantic_key is None:
        return None
    return planned_object_ids.get(receiver_semantic_key) or (
        current_semantic_object_ids.get(receiver_semantic_key)
    )


def _string_map(values: Mapping[str, object]) -> dict[str, str]:
    return {
        key: item
        for key, item in (
            (_optional_text(raw_key), _optional_text(raw_value))
            for raw_key, raw_value in values.items()
        )
        if key is not None and item is not None
    }


def api_delta_typed_operation_execution_block(
    *,
    provider_delta_typed_operation_execution_preflight: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if provider_delta_typed_operation_execution_preflight is None:
        return None
    status = _optional_text(
        provider_delta_typed_operation_execution_preflight.get("status")
    )
    if status != "typed_operation_execution_blocked":
        return None
    reason = (
        _optional_text(provider_delta_typed_operation_execution_preflight.get("reason"))
        or API_TYPED_OPERATION_EXECUTION_TYPED_EXECUTOR_BLOCK_REASON
    )
    return {
        "typed_operation_execution_preflight_status": status,
        "typed_operation_execution_preflight_reason": reason,
        "typed_operation_execution_preflight": dict(
            provider_delta_typed_operation_execution_preflight
        ),
        "typed_operation_count": api_delta_int_mapping_value(
            provider_delta_typed_operation_execution_preflight,
            "typed_operation_count",
        ),
        "typed_operation_update_count": api_delta_int_mapping_value(
            provider_delta_typed_operation_execution_preflight,
            "update_operation_count",
        ),
        "typed_operation_upsert_count": api_delta_int_mapping_value(
            provider_delta_typed_operation_execution_preflight,
            "upsert_operation_count",
        ),
        "operation_execution_status": "typed_operation_execution_blocked",
        "operation_execution_reason": reason,
    }


def api_delta_int_mapping_value(
    value: Mapping[str, object],
    key: str,
) -> int:
    raw_value = value.get(key)
    if isinstance(raw_value, int):
        return raw_value
    try:
        return int(str(raw_value))
    except Exception:
        return 0


def _mapping_payload(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    return text
