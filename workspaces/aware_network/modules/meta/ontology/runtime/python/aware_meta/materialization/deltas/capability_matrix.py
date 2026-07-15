from __future__ import annotations

from collections.abc import Mapping

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION,
    MetaProviderDeltaOntologyExecutionPlan,
    MetaProviderDeltaTypedOperationPlan,
)
from aware_meta.materialization.deltas.ontology_execution.receiver_resolution import (
    optional_text,
    tuple_mappings,
    tuple_text,
    typed_operations_from_plan,
)


FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION = (
    META_PROVIDER_DELTA_FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION
)
FUNCTIONCALL_CAPABILITY_ENTRY_CONTRACT_VERSION = (
    "aware.meta.ocg.provider-delta-functioncall-capability-entry.v1"
)

EXECUTABLE_VIA_ONTOLOGY_FUNCTION = "executable_via_ontology_function"
BLOCKED_MISSING_ONTOLOGY_FUNCTION = "blocked_missing_ontology_function"
PLANNER_ONLY = "planner_only"
UNSUPPORTED = "unsupported"


def build_provider_delta_functioncall_capability_matrix(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_ontology_execution_plan: Mapping[str, object],
) -> dict[str, object]:
    typed_plan = MetaProviderDeltaTypedOperationPlan.from_payload(
        provider_delta_typed_operation_plan
    )
    ontology_plan = MetaProviderDeltaOntologyExecutionPlan.from_payload(
        provider_delta_ontology_execution_plan
    )
    typed_status = typed_plan.status
    ontology_status = ontology_plan.status
    operations = typed_operations_from_plan(
        provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
    )
    blocked_operation_payloads = tuple_mappings(
        provider_delta_typed_operation_plan.get("blocked_operations")
    )
    handler_result_by_operation_key = _handler_result_by_operation_key(
        provider_delta_ontology_execution_plan=provider_delta_ontology_execution_plan,
    )
    typed_plan_ready = typed_status == "typed_operation_plan_ready"
    coverage_entries = tuple(
        _capability_entry_from_operation(
            operation_key=operation.operation_key,
            semantic_key=operation.semantic_key,
            provider_operation_type=operation.provider_operation_type,
            ontology_subject_kind=operation.ontology_subject_kind,
            operation_family=operation.operation_family,
            typed_plan_ready=typed_plan_ready,
            handler_result=handler_result_by_operation_key.get(operation.operation_key),
        )
        for operation in operations
    )
    blocked_entries = tuple(
        _capability_entry_from_blocked_payload(payload=payload)
        for payload in blocked_operation_payloads
        if optional_text(payload.get("operation_key")) is not None
    )
    coverage_entries = (*coverage_entries, *blocked_entries)
    status_counts = _count_by_field(
        entries=coverage_entries,
        field_name="capability_status",
    )
    non_executable_entries = tuple(
        entry for entry in coverage_entries if entry.get("executable") is not True
    )
    blockers = _matrix_blockers(
        typed_status=typed_status,
        ontology_status=ontology_status,
        non_executable_entries=non_executable_entries,
    )
    execution_allowed = (
        typed_plan_ready
        and ontology_status == "ontology_execution_plan_ready"
        and bool(coverage_entries)
        and not non_executable_entries
    )
    coverage_status = _coverage_status(
        typed_plan_ready=typed_plan_ready,
        ontology_status=ontology_status,
        coverage_entries=coverage_entries,
        non_executable_entries=non_executable_entries,
    )
    return {
        "matrix_kind": "meta_ocg_provider_delta_functioncall_capability_matrix",
        "contract_version": FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION,
        "entry_contract_version": FUNCTIONCALL_CAPABILITY_ENTRY_CONTRACT_VERSION,
        "status": (
            "functioncall_capability_matrix_ready"
            if typed_plan_ready
            else "functioncall_capability_matrix_blocked"
        ),
        "reason": (
            "meta_ocg_functioncall_capability_matrix_ready"
            if typed_plan_ready
            else "meta_ocg_functioncall_capability_matrix_requires_typed_operations"
        ),
        "source": "aware_meta.provider_delta.ontology_execution_plan",
        "execution_policy": "ontology_function_call_only",
        "typed_operation_plan_status": typed_status,
        "ontology_execution_plan_status": ontology_status,
        "ontology_execution_plan_reason": optional_text(
            provider_delta_ontology_execution_plan.get("reason")
        ),
        "coverage_status": coverage_status,
        "operation_count": len(coverage_entries),
        "executable_operation_count": len(coverage_entries)
        - len(non_executable_entries),
        "non_executable_operation_count": len(non_executable_entries),
        "capability_status_counts": status_counts,
        "provider_operation_type_counts": _count_by_field(
            entries=coverage_entries,
            field_name="provider_operation_type",
        ),
        "ontology_subject_kind_counts": _count_by_field(
            entries=coverage_entries,
            field_name="ontology_subject_kind",
        ),
        "operation_family_counts": _count_by_field(
            entries=coverage_entries,
            field_name="operation_family",
        ),
        "missing_ontology_function_operation_count": status_counts.get(
            BLOCKED_MISSING_ONTOLOGY_FUNCTION,
            0,
        ),
        "planner_only_operation_count": status_counts.get(PLANNER_ONLY, 0),
        "unsupported_operation_count": status_counts.get(UNSUPPORTED, 0),
        "capability_entries": coverage_entries,
        "non_executable_operations": non_executable_entries,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "available": typed_plan_ready,
        "blocked": not typed_plan_ready or bool(blockers),
        "execution_allowed": execution_allowed,
        "apply_wired": execution_allowed,
        "would_execute": execution_allowed,
        "did_execute": False,
        "would_persist": execution_allowed,
        "did_persist": False,
        "production_execution_wired": False,
    }


def _capability_entry_from_operation(
    *,
    operation_key: str,
    semantic_key: str,
    provider_operation_type: str,
    ontology_subject_kind: str,
    operation_family: str,
    typed_plan_ready: bool,
    handler_result: Mapping[str, object] | None,
) -> dict[str, object]:
    if operation_family not in {"create", "update", "delete"}:
        return _capability_entry(
            operation_key=operation_key,
            semantic_key=semantic_key,
            provider_operation_type=provider_operation_type,
            ontology_subject_kind=ontology_subject_kind,
            operation_family=operation_family,
            capability_status=UNSUPPORTED,
            reason="meta_ocg_functioncall_capability_unsupported_operation_family",
            handler_result=handler_result,
            blockers=(f"unsupported_operation_family:{operation_family}",),
        )
    if not typed_plan_ready:
        return _capability_entry(
            operation_key=operation_key,
            semantic_key=semantic_key,
            provider_operation_type=provider_operation_type,
            ontology_subject_kind=ontology_subject_kind,
            operation_family=operation_family,
            capability_status=PLANNER_ONLY,
            reason="meta_ocg_functioncall_capability_requires_ready_typed_plan",
            handler_result=handler_result,
            blockers=("typed_operation_plan_not_ready",),
        )
    if handler_result is None:
        return _capability_entry(
            operation_key=operation_key,
            semantic_key=semantic_key,
            provider_operation_type=provider_operation_type,
            ontology_subject_kind=ontology_subject_kind,
            operation_family=operation_family,
            capability_status=BLOCKED_MISSING_ONTOLOGY_FUNCTION,
            reason="meta_ocg_functioncall_capability_handler_result_missing",
            handler_result=None,
            blockers=(
                f"ontology_function_call_handler_missing:{provider_operation_type}",
            ),
        )
    handler_status = optional_text(handler_result.get("status"))
    invocation_intent_count = _int_value(handler_result.get("invocation_intent_count"))
    handler_blockers = tuple_text(handler_result.get("blockers"))
    handler_reason = optional_text(handler_result.get("reason")) or (
        "meta_ocg_functioncall_capability_handler_blocked"
    )
    if (
        handler_status == "ontology_operation_handler_ready"
        and invocation_intent_count > 0
    ):
        return _capability_entry(
            operation_key=operation_key,
            semantic_key=semantic_key,
            provider_operation_type=provider_operation_type,
            ontology_subject_kind=ontology_subject_kind,
            operation_family=operation_family,
            capability_status=EXECUTABLE_VIA_ONTOLOGY_FUNCTION,
            reason="meta_ocg_functioncall_capability_executable",
            handler_result=handler_result,
            blockers=(),
        )
    if _handler_result_requires_ontology_function(
        handler_reason=handler_reason,
        handler_blockers=handler_blockers,
    ):
        return _capability_entry(
            operation_key=operation_key,
            semantic_key=semantic_key,
            provider_operation_type=provider_operation_type,
            ontology_subject_kind=ontology_subject_kind,
            operation_family=operation_family,
            capability_status=BLOCKED_MISSING_ONTOLOGY_FUNCTION,
            reason=handler_reason,
            handler_result=handler_result,
            blockers=handler_blockers,
        )
    return _capability_entry(
        operation_key=operation_key,
        semantic_key=semantic_key,
        provider_operation_type=provider_operation_type,
        ontology_subject_kind=ontology_subject_kind,
        operation_family=operation_family,
        capability_status=UNSUPPORTED,
        reason=handler_reason,
        handler_result=handler_result,
        blockers=handler_blockers or (f"unsupported_operation:{operation_key}",),
    )


def _capability_entry_from_blocked_payload(
    *,
    payload: Mapping[str, object],
) -> dict[str, object]:
    return _capability_entry(
        operation_key=optional_text(payload.get("operation_key")) or "",
        semantic_key=optional_text(payload.get("semantic_key")) or "",
        provider_operation_type=(
            optional_text(payload.get("provider_operation_type")) or ""
        ),
        ontology_subject_kind=(
            optional_text(payload.get("ontology_subject_kind")) or ""
        ),
        operation_family=optional_text(payload.get("operation_family")) or "blocked",
        capability_status=PLANNER_ONLY,
        reason=(
            optional_text(payload.get("blocked_reason"))
            or "meta_ocg_functioncall_capability_typed_operation_blocked"
        ),
        handler_result=None,
        blockers=("typed_operation_blocked",),
    )


def _capability_entry(
    *,
    operation_key: str,
    semantic_key: str,
    provider_operation_type: str,
    ontology_subject_kind: str,
    operation_family: str,
    capability_status: str,
    reason: str,
    handler_result: Mapping[str, object] | None,
    blockers: tuple[str, ...],
) -> dict[str, object]:
    invocation_intents = (
        tuple_mappings(handler_result.get("invocation_intents"))
        if handler_result is not None
        else ()
    )
    function_refs = tuple(
        dict.fromkeys(
            function_ref
            for intent in invocation_intents
            for function_ref in (optional_text(intent.get("function_ref")),)
            if function_ref is not None
        )
    )
    executable = capability_status == EXECUTABLE_VIA_ONTOLOGY_FUNCTION
    return {
        "entry_kind": "meta_ocg_provider_delta_functioncall_capability_entry",
        "contract_version": FUNCTIONCALL_CAPABILITY_ENTRY_CONTRACT_VERSION,
        "operation_key": operation_key,
        "semantic_key": semantic_key,
        "provider_operation_type": provider_operation_type,
        "ontology_subject_kind": ontology_subject_kind,
        "operation_family": operation_family,
        "capability_status": capability_status,
        "reason": reason,
        "executable": executable,
        "handler_key": (
            optional_text(handler_result.get("handler_key"))
            if handler_result is not None
            else None
        ),
        "handler_status": (
            optional_text(handler_result.get("status"))
            if handler_result is not None
            else None
        ),
        "handler_reason": (
            optional_text(handler_result.get("reason"))
            if handler_result is not None
            else None
        ),
        "invocation_intent_count": len(invocation_intents),
        "function_refs": function_refs,
        "blockers": blockers,
        "blocker_count": len(blockers),
        "apply_wired": executable,
        "would_execute": executable,
        "did_execute": False,
        "would_persist": executable,
        "did_persist": False,
        "production_execution_wired": False,
    }


def _handler_result_by_operation_key(
    *,
    provider_delta_ontology_execution_plan: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    results: dict[str, Mapping[str, object]] = {}
    for result in tuple_mappings(
        provider_delta_ontology_execution_plan.get("operation_handler_results")
    ):
        operation_key = optional_text(result.get("operation_key"))
        if operation_key is not None:
            results[operation_key] = result
    return results


def _handler_result_requires_ontology_function(
    *,
    handler_reason: str,
    handler_blockers: tuple[str, ...],
) -> bool:
    if handler_reason.endswith("_requires_update_functions"):
        return True
    if handler_reason.endswith("_requires_ontology_function"):
        return True
    if handler_reason == "meta_ocg_ontology_execution_handler_not_registered":
        return True
    return any(
        blocker.startswith("ontology_function_call_handler_missing:")
        or blocker.endswith("_ontology_function_missing")
        or blocker.endswith("_requires_update_functions")
        or blocker.endswith("_not_supported")
        for blocker in handler_blockers
    )


def _coverage_status(
    *,
    typed_plan_ready: bool,
    ontology_status: str | None,
    coverage_entries: tuple[Mapping[str, object], ...],
    non_executable_entries: tuple[Mapping[str, object], ...],
) -> str:
    if not typed_plan_ready:
        return "typed_operation_plan_blocked"
    if not coverage_entries:
        return "no_operations"
    if (
        ontology_status == "ontology_execution_plan_ready"
        and not non_executable_entries
    ):
        return "all_operations_executable"
    if len(non_executable_entries) == len(coverage_entries):
        return "all_operations_blocked"
    return "partial_operations_executable"


def _matrix_blockers(
    *,
    typed_status: str | None,
    ontology_status: str | None,
    non_executable_entries: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if typed_status != "typed_operation_plan_ready":
        blockers.append(f"typed_operation_plan_not_ready:{typed_status or 'unknown'}")
    if ontology_status != "ontology_execution_plan_ready":
        blockers.append(
            f"ontology_execution_plan_not_ready:{ontology_status or 'unknown'}"
        )
    for entry in non_executable_entries:
        operation_key = optional_text(entry.get("operation_key")) or "unknown"
        capability_status = optional_text(entry.get("capability_status")) or "unknown"
        blockers.append(f"{capability_status}:{operation_key}")
    return tuple(dict.fromkeys(blockers))


def _count_by_field(
    *,
    entries: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        value = optional_text(entry.get(field_name)) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    text = optional_text(value)
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


__all__ = [
    "BLOCKED_MISSING_ONTOLOGY_FUNCTION",
    "EXECUTABLE_VIA_ONTOLOGY_FUNCTION",
    "FUNCTIONCALL_CAPABILITY_ENTRY_CONTRACT_VERSION",
    "FUNCTIONCALL_CAPABILITY_MATRIX_CONTRACT_VERSION",
    "PLANNER_ONLY",
    "UNSUPPORTED",
    "build_provider_delta_functioncall_capability_matrix",
]
