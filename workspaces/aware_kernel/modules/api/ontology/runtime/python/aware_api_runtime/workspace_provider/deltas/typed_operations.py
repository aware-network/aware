from __future__ import annotations

from collections.abc import Mapping

from aware_api_runtime.source.semantic_analysis import APISemanticAnalysisResult


API_TYPED_OPERATION_PLAN_CONTRACT_VERSION = (
    "aware.api.provider-delta.typed-operation-plan.v1"
)
API_TYPED_OPERATION_CONTRACT_VERSION = "aware.api.provider-delta.typed-operation.v1"
API_PROVIDER_KEY = "aware_api"


def api_delta_typed_operation_plan(
    *,
    analysis: APISemanticAnalysisResult,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    function_call_plans: tuple[object, ...],
) -> dict[str, object]:
    dirty_entries = tuple(
        _mapping_payload(entry)
        for entry in _tuple_evidence(semantic_dirty_diff.get("semantic_dirty_entries"))
        if isinstance(entry, Mapping)
    )
    preview = analysis.change_preview
    semantic_event_payloads = tuple(
        event.evidence_payload() for event in tuple(preview.semantic_events)
    )
    semantic_event_by_semantic_key = api_delta_semantic_event_by_semantic_key(
        semantic_event_payloads=semantic_event_payloads,
    )
    semantic_event_by_delta_key = api_delta_semantic_event_by_delta_key(
        semantic_event_payloads=semantic_event_payloads,
    )
    function_call_plan_by_semantic_key = api_delta_function_call_plan_by_semantic_key(
        function_call_plans=function_call_plans,
    )
    typed_operations = tuple(
        operation
        for operation in (
            api_delta_typed_operation_from_dirty_entry(
                entry=entry,
                blocked=False,
                semantic_event_by_semantic_key=semantic_event_by_semantic_key,
                semantic_event_by_delta_key=semantic_event_by_delta_key,
                function_call_plan_by_semantic_key=(function_call_plan_by_semantic_key),
            )
            for entry in dirty_entries
        )
        if operation is not None
    )
    blocked_operations = tuple(
        operation
        for operation in (
            api_delta_typed_operation_from_dirty_entry(
                entry=entry,
                blocked=True,
                semantic_event_by_semantic_key=semantic_event_by_semantic_key,
                semantic_event_by_delta_key=semantic_event_by_delta_key,
                function_call_plan_by_semantic_key=(function_call_plan_by_semantic_key),
            )
            for entry in dirty_entries
        )
        if operation is not None
    )
    plan_ready = api_delta_typed_operation_plan_ready(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
    )
    blocked_reason = api_delta_typed_operation_plan_blocked_reason(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
    )
    exposed_operations = typed_operations if plan_ready else ()
    exposed_blocked_operations = () if plan_ready else blocked_operations
    return {
        "plan_kind": "api_provider_delta_typed_operation_plan",
        "contract_version": API_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
        "operation_contract_version": API_TYPED_OPERATION_CONTRACT_VERSION,
        "status": (
            "typed_operation_plan_ready"
            if plan_ready
            else "typed_operation_plan_blocked"
        ),
        "reason": (
            "api_provider_delta_typed_operation_plan_ready"
            if plan_ready
            else blocked_reason
        ),
        "source": "aware_api.provider_delta.semantic_dirty_diff",
        "provider_key": API_PROVIDER_KEY,
        "current_delta_fingerprint": _optional_text(
            semantic_dirty_diff.get("current_delta_fingerprint")
        ),
        "semantic_dirty_diff_status": _optional_text(semantic_dirty_diff.get("status")),
        "semantic_dirty_diff_reason": _optional_text(semantic_dirty_diff.get("reason")),
        "provider_delta_head_move_status": _optional_text(
            provider_delta_head_move_plan.get("status")
        ),
        "provider_delta_head_move_reason": _optional_text(
            provider_delta_head_move_plan.get("reason")
        ),
        "baseline_index_compare_available": (
            semantic_dirty_diff.get("baseline_index_compare_available") is True
        ),
        "baseline_index_compare_status": _optional_text(
            semantic_dirty_diff.get("baseline_index_compare_status")
        ),
        "baseline_index_compare_reason": _optional_text(
            semantic_dirty_diff.get("baseline_index_compare_reason")
        ),
        "dirty_entry_count": len(dirty_entries),
        "typed_operation_count": len(exposed_operations),
        "blocked_operation_count": len(exposed_blocked_operations),
        "operation_family_counts": api_delta_operation_count_by_field(
            operations=exposed_operations,
            field_name="operation_family",
        ),
        "operation_type_counts": api_delta_operation_count_by_field(
            operations=exposed_operations,
            field_name="provider_operation_type",
        ),
        "blocked_operation_type_counts": api_delta_operation_count_by_field(
            operations=exposed_blocked_operations,
            field_name="provider_operation_type",
        ),
        "typed_operations": exposed_operations,
        "blocked_operations": exposed_blocked_operations,
        "semantic_event_projection_ready": plan_ready,
        "event_dispatch_wired": False,
        "available": plan_ready,
        "blocked": not plan_ready,
        "blocked_status": (
            None
            if plan_ready
            else api_delta_typed_operation_blocked_status(
                semantic_dirty_diff=semantic_dirty_diff,
                provider_delta_head_move_plan=provider_delta_head_move_plan,
            )
        ),
        "blocked_reason": None if plan_ready else blocked_reason,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def api_delta_typed_operation_plan_ready(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
) -> bool:
    return (
        semantic_dirty_diff.get("available") is True
        and semantic_dirty_diff.get("blocked") is not True
        and semantic_dirty_diff.get("baseline_index_compare_available") is True
        and semantic_dirty_diff.get("baseline_index_compare_status")
        == "baseline_index_compared"
        and provider_delta_head_move_plan.get("status") == "head_move_plan_ready"
        and provider_delta_head_move_plan.get("blocked") is not True
    )


def api_delta_typed_operation_plan_blocked_reason(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
) -> str:
    if semantic_dirty_diff.get("available") is not True:
        return (
            _optional_text(semantic_dirty_diff.get("reason"))
            or "api_typed_operations_require_semantic_dirty_diff"
        )
    if semantic_dirty_diff.get("baseline_index_compare_status") != (
        "baseline_index_compared"
    ):
        return (
            _optional_text(semantic_dirty_diff.get("baseline_index_compare_reason"))
            or "api_typed_operations_require_baseline_index_comparison"
        )
    if provider_delta_head_move_plan.get("status") != "head_move_plan_ready":
        return (
            _optional_text(provider_delta_head_move_plan.get("reason"))
            or "api_typed_operations_require_head_move_plan"
        )
    return "api_provider_delta_typed_operations_blocked"


def api_delta_typed_operation_blocked_status(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
) -> str:
    if semantic_dirty_diff.get("available") is not True:
        return (
            _optional_text(semantic_dirty_diff.get("status"))
            or "semantic_dirty_diff_blocked"
        )
    if semantic_dirty_diff.get("baseline_index_compare_status") != (
        "baseline_index_compared"
    ):
        return (
            _optional_text(semantic_dirty_diff.get("baseline_index_compare_status"))
            or "baseline_index_comparison_required"
        )
    return _optional_text(provider_delta_head_move_plan.get("status")) or (
        "head_move_plan_blocked"
    )


def api_delta_typed_operation_from_dirty_entry(
    *,
    entry: Mapping[str, object],
    blocked: bool,
    semantic_event_by_semantic_key: Mapping[str, Mapping[str, object]],
    semantic_event_by_delta_key: Mapping[str, Mapping[str, object]],
    function_call_plan_by_semantic_key: Mapping[str, Mapping[str, object]],
) -> dict[str, object] | None:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return None
    operation_family = api_delta_typed_operation_family(entry=entry)
    if not blocked and operation_family not in {"create", "update", "delete"}:
        return None
    subject_kind = _optional_text(entry.get("ontology_subject_kind")) or (
        "api_semantic_object"
    )
    provider_operation_type = f"aware_api.{subject_kind}.{operation_family}"
    source_delta_key = _optional_text(entry.get("source_delta_key"))
    source_semantic_event = semantic_event_by_semantic_key.get(semantic_key)
    if source_semantic_event is None and source_delta_key is not None:
        source_semantic_event = semantic_event_by_delta_key.get(source_delta_key)
    function_call_plan = function_call_plan_by_semantic_key.get(semantic_key)
    return {
        "operation_kind": "api_provider_delta_typed_operation",
        "contract_version": API_TYPED_OPERATION_CONTRACT_VERSION,
        "operation_key": (
            f"api_provider_delta:{operation_family}:{subject_kind}:" f"{semantic_key}"
        ),
        "operation_family": operation_family,
        "provider_operation_type": provider_operation_type,
        "semantic_key": semantic_key,
        "semantic_subject_type": _optional_text(entry.get("semantic_subject_type")),
        "ontology_subject_kind": subject_kind,
        "source_entry_key": _optional_text(entry.get("entry_key")),
        "source_delta_key": source_delta_key,
        "source_refs": tuple(_tuple_evidence(entry.get("source_refs"))),
        "baseline": api_delta_typed_operation_baseline_payload(entry=entry),
        "current": api_delta_typed_operation_current_payload(entry=entry),
        "api_operation": api_delta_typed_operation_api_payload(
            entry=entry,
            operation_family=operation_family,
        ),
        "source_semantic_event": (
            dict(source_semantic_event) if source_semantic_event is not None else None
        ),
        "semantic_event_projection": api_delta_typed_operation_event_projection(
            entry=entry,
            operation_family=operation_family,
            provider_operation_type=provider_operation_type,
        ),
        "function_call_plan": (
            dict(function_call_plan) if function_call_plan is not None else None
        ),
        "blocked": blocked,
        "blocked_reason": (
            api_delta_typed_operation_entry_blocked_reason(entry=entry)
            if blocked
            else None
        ),
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "event_dispatch_wired": False,
        "production_execution_wired": False,
    }


def api_delta_typed_operation_family(*, entry: Mapping[str, object]) -> str:
    operation = _optional_text(entry.get("baseline_compare_operation"))
    if operation is None:
        operation = _optional_text(entry.get("dirty_operation"))
    if operation is None:
        return "unknown"
    normalized = operation.strip().lower()
    if normalized == "blocked" or normalized.endswith("_blocked"):
        return "blocked"
    if normalized == "create" or normalized.endswith("_create"):
        return "create"
    if normalized == "update" or normalized.endswith("_update"):
        return "update"
    if normalized == "delete" or normalized.endswith("_delete"):
        return "delete"
    if normalized == "noop" or normalized.endswith("_noop"):
        return "noop"
    if normalized == "upsert" or normalized.endswith("_upsert"):
        return "upsert"
    return "unknown"


def api_delta_typed_operation_baseline_payload(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    return {
        "compare_status": _optional_text(entry.get("baseline_compare_status")),
        "compare_operation": _optional_text(entry.get("baseline_compare_operation")),
        "object_matched": entry.get("baseline_object_matched") is True,
        "object_id": _optional_text(entry.get("baseline_object_id")),
        "object_kind": _optional_text(entry.get("baseline_object_kind")),
        "object_instance_graph_commit_id": _optional_text(
            entry.get("baseline_object_instance_graph_commit_id")
        ),
    }


def api_delta_typed_operation_current_payload(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    payload = _mapping_payload(entry.get("payload"))
    return {
        "semantic_key": _optional_text(entry.get("semantic_key")),
        "object_kind": _optional_text(entry.get("ontology_subject_kind")),
        "semantic_subject_type": _optional_text(entry.get("semantic_subject_type")),
        "payload": payload,
    }


def api_delta_typed_operation_api_payload(
    *,
    entry: Mapping[str, object],
    operation_family: str,
) -> dict[str, object]:
    subject_kind = _optional_text(entry.get("ontology_subject_kind")) or (
        "api_semantic_object"
    )
    payload = _mapping_payload(entry.get("payload"))
    if subject_kind == "api":
        operation = "ensure_api"
        receiver_semantic_key = None
        arguments = {
            "name": payload.get("name"),
            "capability_count": payload.get("capability_count"),
            "graph_count": payload.get("graph_count"),
        }
    elif subject_kind == "api_capability":
        operation = "ensure_api_capability"
        receiver_semantic_key = _optional_text(payload.get("api_semantic_key"))
        arguments = {
            "api_semantic_key": payload.get("api_semantic_key"),
            "api_name": payload.get("api_name"),
            "name": payload.get("name"),
            "description": payload.get("description"),
            "endpoint_count": payload.get("endpoint_count"),
        }
    elif subject_kind == "api_capability_endpoint":
        operation = "ensure_api_capability_endpoint"
        receiver_semantic_key = _optional_text(payload.get("capability_semantic_key"))
        arguments = {
            "capability_semantic_key": payload.get("capability_semantic_key"),
            "api_name": payload.get("api_name"),
            "capability_name": payload.get("capability_name"),
            "name": payload.get("name"),
            "description": payload.get("description"),
            "request_class_ref": payload.get("request_class_ref"),
        }
    else:
        operation = "unknown_api_provider_delta_operation"
        receiver_semantic_key = None
        arguments = dict(payload)
    return {
        "operation": operation,
        "operation_family": operation_family,
        "receiver_semantic_key": receiver_semantic_key,
        "arguments": arguments,
        "execution_wired": False,
    }


def api_delta_typed_operation_event_projection(
    *,
    entry: Mapping[str, object],
    operation_family: str,
    provider_operation_type: str,
) -> dict[str, object]:
    subject_kind = _optional_text(entry.get("ontology_subject_kind")) or (
        "api_semantic_object"
    )
    source_delta_key = _optional_text(entry.get("source_delta_key"))
    return {
        "event_type": "semantic_operation_preview",
        "event_key": f"aware_api.provider_delta.{subject_kind}.{operation_family}",
        "semantic_key": _optional_text(entry.get("semantic_key")),
        "verb": operation_family,
        "subject_type": _optional_text(entry.get("semantic_subject_type")),
        "provider_operation_type": provider_operation_type,
        "source_refs": tuple(_tuple_evidence(entry.get("source_refs"))),
        "delta_keys": (source_delta_key,) if source_delta_key is not None else (),
        "condition_keys": (
            "api.baseline_index_compared",
            f"api.baseline_compare.{_optional_text(entry.get('baseline_compare_status')) or 'unknown'}",
            f"api.operation_family.{operation_family}",
        ),
        "payload": api_delta_typed_operation_current_payload(entry=entry),
        "event_dispatch_wired": False,
    }


def api_delta_typed_operation_entry_blocked_reason(
    *,
    entry: Mapping[str, object],
) -> str:
    return (
        _optional_text(entry.get("baseline_compare_status"))
        or "api_provider_delta_typed_operation_entry_blocked"
    )


def api_delta_semantic_event_by_semantic_key(
    *,
    semantic_event_payloads: tuple[Mapping[str, object], ...],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for event in semantic_event_payloads:
        semantic_key = _optional_text(event.get("semantic_key"))
        if semantic_key is not None:
            entries[semantic_key] = event
    return entries


def api_delta_semantic_event_by_delta_key(
    *,
    semantic_event_payloads: tuple[Mapping[str, object], ...],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for event in semantic_event_payloads:
        for delta_key in _tuple_evidence(event.get("delta_keys")):
            key = _optional_text(delta_key)
            if key is not None:
                entries[key] = event
    return entries


def api_delta_function_call_plan_by_semantic_key(
    *,
    function_call_plans: tuple[object, ...],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for plan in function_call_plans:
        evidence_payload = getattr(plan, "evidence_payload", None)
        if not callable(evidence_payload):
            continue
        payload = evidence_payload()
        if not isinstance(payload, Mapping):
            continue
        semantic_key = _optional_text(payload.get("result_semantic_key"))
        if semantic_key is not None:
            entries[semantic_key] = dict(payload)
    return entries


def api_delta_operation_count_by_field(
    *,
    operations: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for operation in operations:
        value = _optional_text(operation.get(field_name))
        if value is None:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


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
    text = str(value).strip()
    return text or None


__all__ = [
    "API_TYPED_OPERATION_CONTRACT_VERSION",
    "API_TYPED_OPERATION_PLAN_CONTRACT_VERSION",
    "api_delta_function_call_plan_by_semantic_key",
    "api_delta_operation_count_by_field",
    "api_delta_semantic_event_by_delta_key",
    "api_delta_semantic_event_by_semantic_key",
    "api_delta_typed_operation_api_payload",
    "api_delta_typed_operation_baseline_payload",
    "api_delta_typed_operation_blocked_status",
    "api_delta_typed_operation_current_payload",
    "api_delta_typed_operation_entry_blocked_reason",
    "api_delta_typed_operation_event_projection",
    "api_delta_typed_operation_family",
    "api_delta_typed_operation_from_dirty_entry",
    "api_delta_typed_operation_plan",
    "api_delta_typed_operation_plan_blocked_reason",
    "api_delta_typed_operation_plan_ready",
]
