from __future__ import annotations

from collections.abc import Mapping

from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION,
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION,
    MetaProviderDeltaTypedOperation,
)
from aware_meta.materialization.deltas.coverage_matrix import (
    META_OCG_DELTA_COVERAGE_MATRIX_CONTRACT_VERSION,
    matrix_entries_for_registration_key,
)
from aware_meta.materialization.deltas.feature_registry import (
    typed_operation_dirty_entries_from_feature_provider,
)


_SUPPORTED_DELTA_PROVIDER_KEY = "aware_meta"
_TYPED_OPERATION_PLAN_CONTRACT_VERSION = (
    META_PROVIDER_DELTA_TYPED_OPERATION_PLAN_CONTRACT_VERSION
)
_TYPED_OPERATION_CONTRACT_VERSION = META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION
_ATTRIBUTE_UPDATE_READINESS_FIELDS = (
    "name",
    "attribute_config_name",
    "type_descriptor",
    "default_value",
)


def _provider_delta_typed_operation_plan(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    semantic_change_payloads: tuple[Mapping[str, object], ...],
    function_call_plans: tuple[SemanticCapabilityFunctionCallPlan, ...],
) -> dict[str, object]:
    semantic_change_payloads = tuple(
        _semantic_change_payload(payload) for payload in semantic_change_payloads
    )
    dirty_entries = tuple(
        _mapping_value(entry)
        for entry in _tuple_evidence(semantic_dirty_diff.get("semantic_dirty_entries"))
        if isinstance(entry, Mapping)
    )
    semantic_change_by_semantic_key = _semantic_change_by_semantic_key(
        semantic_change_payloads=semantic_change_payloads,
    )
    semantic_change_by_delta_key = _semantic_change_by_delta_key(
        semantic_change_payloads=semantic_change_payloads,
    )
    function_call_plan_by_semantic_key = _function_call_plan_by_semantic_key(
        function_call_plans=function_call_plans,
    )
    semantic_object_anchors = tuple(
        anchor
        for anchor in (
            _semantic_object_anchor_from_dirty_entry(entry=entry)
            for entry in dirty_entries
        )
        if anchor is not None
    )
    typed_operations = tuple(
        operation
        for entry in dirty_entries
        for operation in _typed_operations_from_dirty_entry(
            entry=entry,
            blocked=False,
            semantic_change_by_semantic_key=semantic_change_by_semantic_key,
            semantic_change_by_delta_key=semantic_change_by_delta_key,
            function_call_plan_by_semantic_key=function_call_plan_by_semantic_key,
        )
    )
    typed_operation_entry_blockers = _typed_operation_entry_blockers(
        operations=typed_operations,
    )
    blocked_operations = tuple(
        operation
        for entry in dirty_entries
        for operation in _typed_operations_from_dirty_entry(
            entry=entry,
            blocked=True,
            semantic_change_by_semantic_key=semantic_change_by_semantic_key,
            semantic_change_by_delta_key=semantic_change_by_delta_key,
            function_call_plan_by_semantic_key=function_call_plan_by_semantic_key,
        )
    )
    base_plan_ready = _typed_operation_plan_ready(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
    )
    plan_ready = base_plan_ready and not typed_operation_entry_blockers
    blocked_reason = _typed_operation_plan_blocked_reason(
        semantic_dirty_diff=semantic_dirty_diff,
        provider_delta_head_move_plan=provider_delta_head_move_plan,
        typed_operation_entry_blockers=typed_operation_entry_blockers,
    )
    exposed_operations = typed_operations if plan_ready else ()
    exposed_anchors = semantic_object_anchors if plan_ready else ()
    exposed_blocked_operations = (
        ()
        if plan_ready
        else (
            *_blocked_typed_operations_from_ready_path(
                operations=typed_operations,
            ),
            *blocked_operations,
        )
    )
    return {
        "plan_kind": "meta_ocg_provider_delta_typed_operation_plan",
        "contract_version": _TYPED_OPERATION_PLAN_CONTRACT_VERSION,
        "operation_contract_version": _TYPED_OPERATION_CONTRACT_VERSION,
        "status": (
            "typed_operation_plan_ready"
            if plan_ready
            else "typed_operation_plan_blocked"
        ),
        "reason": (
            "meta_ocg_provider_delta_typed_operation_plan_ready"
            if plan_ready
            else blocked_reason
        ),
        "source": "aware_meta.provider_delta.semantic_dirty_diff",
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
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
        "semantic_object_anchor_count": len(exposed_anchors),
        "blocked_operation_count": len(exposed_blocked_operations),
        "typed_operation_entry_blockers": typed_operation_entry_blockers,
        "operation_family_counts": _typed_operation_count_by_field(
            operations=exposed_operations,
            field_name="operation_family",
        ),
        "operation_type_counts": _typed_operation_count_by_field(
            operations=exposed_operations,
            field_name="provider_operation_type",
        ),
        "blocked_operation_type_counts": _typed_operation_count_by_field(
            operations=exposed_blocked_operations,
            field_name="provider_operation_type",
        ),
        "typed_operations": exposed_operations,
        "semantic_object_anchors": exposed_anchors,
        "blocked_operations": exposed_blocked_operations,
        "semantic_change_projection_ready": plan_ready,
        "available": plan_ready,
        "blocked": not plan_ready,
        "blocked_status": (
            None
            if plan_ready
            else _typed_operation_blocked_status(
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


def _typed_operation_plan_ready(
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


def _typed_operation_plan_blocked_reason(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    typed_operation_entry_blockers: tuple[str, ...],
) -> str:
    if typed_operation_entry_blockers:
        return (
            typed_operation_entry_blockers[0]
            or "meta_ocg_typed_operation_entry_blocked"
        )
    if semantic_dirty_diff.get("available") is not True:
        return (
            _optional_text(semantic_dirty_diff.get("reason"))
            or "meta_ocg_typed_operations_require_semantic_dirty_diff"
        )
    if semantic_dirty_diff.get("baseline_index_compare_status") != (
        "baseline_index_compared"
    ):
        return (
            _optional_text(semantic_dirty_diff.get("baseline_index_compare_reason"))
            or "meta_ocg_typed_operations_require_baseline_index_comparison"
        )
    if provider_delta_head_move_plan.get("status") != "head_move_plan_ready":
        return (
            _optional_text(provider_delta_head_move_plan.get("reason"))
            or "meta_ocg_typed_operations_require_head_move_plan"
        )
    return "meta_ocg_typed_operations_blocked"


def _typed_operation_blocked_status(
    *,
    semantic_dirty_diff: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
) -> str:
    if semantic_dirty_diff.get("available") is not True:
        return _string_value(semantic_dirty_diff.get("status")) or (
            "semantic_dirty_diff_blocked"
        )
    if semantic_dirty_diff.get("baseline_index_compare_status") != (
        "baseline_index_compared"
    ):
        return (
            _string_value(semantic_dirty_diff.get("baseline_index_compare_status"))
            or "baseline_index_comparison_required"
        )
    return _string_value(provider_delta_head_move_plan.get("status")) or (
        "head_move_plan_blocked"
    )


def _typed_operation_entry_blockers(
    *,
    operations: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    for operation in operations:
        if operation.get("blocked") is not True:
            continue
        reason = _optional_text(operation.get("blocked_reason"))
        current = _mapping_value(operation.get("current"))
        scope_blockers = _tuple_text(current.get("semantic_scope_closure_blockers"))
        blockers.extend(scope_blockers)
        if reason is not None:
            blockers.append(reason)
    return tuple(dict.fromkeys(blockers))


def _blocked_typed_operations_from_ready_path(
    *,
    operations: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        operation for operation in operations if operation.get("blocked") is True
    )


def _typed_operation_entry_is_blocked(
    *,
    entry: Mapping[str, object],
) -> bool:
    return entry.get("semantic_scope_closure_blocked") is True


def _typed_operation_from_dirty_entry(
    *,
    entry: Mapping[str, object],
    blocked: bool,
    semantic_change_by_semantic_key: Mapping[str, Mapping[str, object]],
    semantic_change_by_delta_key: Mapping[str, Mapping[str, object]],
    function_call_plan_by_semantic_key: Mapping[str, Mapping[str, object]],
) -> dict[str, object] | None:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return None
    operation_family = _typed_operation_family(entry=entry)
    if not blocked and operation_family not in {"create", "update", "delete"}:
        return None
    subject_kind = _string_value(entry.get("ontology_subject_kind"))
    provider_operation_type = (
        _optional_text(entry.get("provider_operation_type"))
        or f"meta_ocg.{subject_kind}.{operation_family}"
    )
    readiness_evidence = _typed_operation_readiness_evidence(
        entry=entry,
        operation_family=operation_family,
        subject_kind=subject_kind,
        provider_operation_type=provider_operation_type,
    )
    entry_blocked = blocked or _typed_operation_entry_is_blocked(entry=entry)
    source_delta_key = _optional_text(entry.get("source_delta_key"))
    source_semantic_change = semantic_change_by_semantic_key.get(semantic_key)
    if source_semantic_change is None and source_delta_key is not None:
        source_semantic_change = semantic_change_by_delta_key.get(source_delta_key)
    function_call_plan = function_call_plan_by_semantic_key.get(semantic_key)
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        contract_version=_TYPED_OPERATION_CONTRACT_VERSION,
        operation_key=(
            _optional_text(entry.get("typed_operation_key"))
            or (
                f"meta_ocg_provider_delta:{operation_family}:{subject_kind}:"
                f"{semantic_key}"
            )
        ),
        operation_family=operation_family,
        provider_operation_type=provider_operation_type,
        semantic_key=semantic_key,
        semantic_subject_type=_optional_text(entry.get("semantic_subject_type")),
        ontology_subject_kind=subject_kind,
        source_entry_key=_optional_text(entry.get("entry_key")),
        source_delta_key=source_delta_key,
        source_refs=_tuple_text(entry.get("source_refs")),
        baseline=_typed_operation_baseline_payload(entry=entry),
        current=_typed_operation_current_payload(entry=entry),
        ocg_operation=_typed_operation_ocg_payload(
            entry=entry,
            operation_family=operation_family,
        ),
        source_semantic_change=(
            dict(source_semantic_change) if source_semantic_change is not None else None
        ),
        semantic_change_projection=_typed_operation_change_projection(
            entry=entry,
            operation_family=operation_family,
            provider_operation_type=provider_operation_type,
        ),
        function_call_plan=(
            dict(function_call_plan) if function_call_plan is not None else None
        ),
        blocked=entry_blocked,
        blocked_reason=(
            _typed_operation_entry_blocked_reason(entry=entry)
            if entry_blocked
            else None
        ),
        include_operation_evidence=True,
        extra=readiness_evidence,
    ).evidence_payload()


def _typed_operations_from_dirty_entry(
    *,
    entry: Mapping[str, object],
    blocked: bool,
    semantic_change_by_semantic_key: Mapping[str, Mapping[str, object]],
    semantic_change_by_delta_key: Mapping[str, Mapping[str, object]],
    function_call_plan_by_semantic_key: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    operation_family = _typed_operation_family(entry=entry)
    subject_kind = _string_value(entry.get("ontology_subject_kind"))
    if not blocked:
        feature_operations = _feature_provider_typed_operations(
            entry=entry,
            operation_family=operation_family,
            subject_kind=subject_kind,
            semantic_change_by_semantic_key=semantic_change_by_semantic_key,
            semantic_change_by_delta_key=semantic_change_by_delta_key,
            function_call_plan_by_semantic_key=function_call_plan_by_semantic_key,
        )
        if feature_operations:
            return feature_operations
    if not blocked and operation_family == "update" and subject_kind == "attribute":
        return _feature_provider_typed_operations(
            entry=entry,
            operation_family=operation_family,
            subject_kind=subject_kind,
            semantic_change_by_semantic_key=semantic_change_by_semantic_key,
            semantic_change_by_delta_key=semantic_change_by_delta_key,
            function_call_plan_by_semantic_key=function_call_plan_by_semantic_key,
        )
    if not blocked and operation_family == "update" and subject_kind == "function":
        return _feature_provider_typed_operations(
            entry=entry,
            operation_family=operation_family,
            subject_kind=subject_kind,
            semantic_change_by_semantic_key=semantic_change_by_semantic_key,
            semantic_change_by_delta_key=semantic_change_by_delta_key,
            function_call_plan_by_semantic_key=function_call_plan_by_semantic_key,
        )
    operation = _typed_operation_from_dirty_entry(
        entry=entry,
        blocked=blocked,
        semantic_change_by_semantic_key=semantic_change_by_semantic_key,
        semantic_change_by_delta_key=semantic_change_by_delta_key,
        function_call_plan_by_semantic_key=function_call_plan_by_semantic_key,
    )
    return (operation,) if operation is not None else ()


def _feature_provider_typed_operations(
    *,
    entry: Mapping[str, object],
    operation_family: str,
    subject_kind: str,
    semantic_change_by_semantic_key: Mapping[str, Mapping[str, object]],
    semantic_change_by_delta_key: Mapping[str, Mapping[str, object]],
    function_call_plan_by_semantic_key: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    planned_entries = typed_operation_dirty_entries_from_feature_provider(
        entry=entry,
        ontology_subject_kind=subject_kind,
        operation_family=operation_family,
    )
    if planned_entries is None:
        return ()
    operations: list[dict[str, object]] = []
    for planned_entry in planned_entries:
        operation = _typed_operation_from_dirty_entry(
            entry=planned_entry,
            blocked=False,
            semantic_change_by_semantic_key=semantic_change_by_semantic_key,
            semantic_change_by_delta_key=semantic_change_by_delta_key,
            function_call_plan_by_semantic_key=function_call_plan_by_semantic_key,
        )
        if operation is not None:
            operations.append(operation)
    return tuple(operations)


def _semantic_object_anchor_from_dirty_entry(
    *,
    entry: Mapping[str, object],
) -> dict[str, object] | None:
    semantic_key = _optional_text(entry.get("semantic_key"))
    if semantic_key is None:
        return None
    subject_kind = _string_value(entry.get("ontology_subject_kind"))
    operation_family = _typed_operation_family(entry=entry)
    return MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_semantic_object_anchor",
        contract_version=_TYPED_OPERATION_CONTRACT_VERSION,
        operation_key=(f"meta_ocg_provider_delta:anchor:{subject_kind}:{semantic_key}"),
        operation_family="anchor",
        provider_operation_type=f"meta_ocg.{subject_kind}.anchor",
        semantic_key=semantic_key,
        semantic_subject_type=_optional_text(entry.get("semantic_subject_type")),
        ontology_subject_kind=subject_kind,
        source_entry_key=_optional_text(entry.get("entry_key")),
        source_delta_key=_optional_text(entry.get("source_delta_key")),
        source_refs=_tuple_text(entry.get("source_refs")),
        baseline=_typed_operation_baseline_payload(entry=entry),
        current=_typed_operation_current_payload(entry=entry),
        extra={
            "baseline_compare_operation": operation_family,
            "baseline_compare_status": _optional_text(
                entry.get("baseline_compare_status")
            ),
        },
    ).evidence_payload()


def _typed_operation_family(*, entry: Mapping[str, object]) -> str:
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


def _typed_operation_readiness_evidence(
    *,
    entry: Mapping[str, object],
    operation_family: str,
    subject_kind: str,
    provider_operation_type: str,
) -> dict[str, object]:
    case_key = _typed_operation_readiness_case_key(
        entry=entry,
        operation_family=operation_family,
        subject_kind=subject_kind,
        provider_operation_type=provider_operation_type,
    )
    if case_key is None:
        matching_entries = tuple(
            matrix_entry
            for matrix_entry in matrix_entries_for_registration_key(
                ontology_subject_kind=subject_kind,
                operation_family=operation_family,
            )
            if matrix_entry.provider_operation_type == provider_operation_type
        )
        policies = {
            matrix_entry.source_projection_policy for matrix_entry in matching_entries
        }
        if len(matching_entries) == 1:
            case_key = matching_entries[0].case_key
        elif len(policies) == 1 and matching_entries:
            case_key = matching_entries[0].case_key
        else:
            return _typed_operation_unknown_readiness_evidence(
                case_key=None,
                reason="meta_ocg_typed_operation_readiness_case_ambiguous",
            )
    matrix_entries = tuple(
        matrix_entry
        for matrix_entry in matrix_entries_for_registration_key(
            ontology_subject_kind=subject_kind,
            operation_family=operation_family,
        )
        if matrix_entry.case_key == case_key
        and matrix_entry.provider_operation_type == provider_operation_type
    )
    if not matrix_entries:
        return _typed_operation_unknown_readiness_evidence(
            case_key=case_key,
            reason="meta_ocg_typed_operation_readiness_case_unregistered",
        )
    matrix_entry = matrix_entries[0]
    return {
        "readiness_case_key": matrix_entry.case_key,
        "readiness_contract_version": matrix_entry.contract_version,
        "source_projection_policy": matrix_entry.source_projection_policy,
        "source_projection_status": matrix_entry.source_projection_status,
        "source_projection_reason": matrix_entry.source_projection_reason,
    }


def _typed_operation_unknown_readiness_evidence(
    *,
    case_key: str | None,
    reason: str,
) -> dict[str, object]:
    return {
        "readiness_case_key": case_key,
        "readiness_contract_version": (META_OCG_DELTA_COVERAGE_MATRIX_CONTRACT_VERSION),
        "source_projection_policy": None,
        "source_projection_status": None,
        "source_projection_reason": reason,
    }


def _typed_operation_readiness_case_key(
    *,
    entry: Mapping[str, object],
    operation_family: str,
    subject_kind: str,
    provider_operation_type: str,
) -> str | None:
    explicit_case_key = _optional_text(entry.get("readiness_case_key"))
    if explicit_case_key is not None:
        return explicit_case_key
    if operation_family != "update":
        return None
    if subject_kind == "attribute" and provider_operation_type == (
        "meta_ocg.attribute.update"
    ):
        return _attribute_update_readiness_case_key(entry=entry)
    if subject_kind == "function" and provider_operation_type == (
        "meta_ocg.function.update"
    ):
        return _function_update_readiness_case_key(entry=entry)
    return None


def _attribute_update_readiness_case_key(
    *,
    entry: Mapping[str, object],
) -> str | None:
    current_signature = _mapping_value(entry.get("attribute_signature"))
    baseline_signature = _mapping_value(entry.get("baseline_attribute_signature"))
    if not baseline_signature:
        baseline_object = _mapping_value(entry.get("baseline_object"))
        baseline_signature = _mapping_value(baseline_object.get("attribute_signature"))
    changed_fields = _changed_mapping_fields(
        current=_mapping_field_projection(
            current_signature,
            fields=_ATTRIBUTE_UPDATE_READINESS_FIELDS,
        ),
        baseline=_mapping_field_projection(
            baseline_signature,
            fields=_ATTRIBUTE_UPDATE_READINESS_FIELDS,
        ),
    )
    if not changed_fields:
        return None
    if changed_fields & {"name", "attribute_config_name"}:
        return "attribute.update.identity_name"
    if changed_fields == {"type_descriptor"}:
        return "attribute.update.primitive_type"
    if changed_fields == {"default_value"}:
        return "attribute.update.default_value"
    return None


def _function_update_readiness_case_key(
    *,
    entry: Mapping[str, object],
) -> str | None:
    current_signature = _mapping_value(entry.get("function_signature"))
    baseline_signature = _mapping_value(entry.get("baseline_function_signature"))
    if not baseline_signature:
        baseline_object = _mapping_value(entry.get("baseline_object"))
        baseline_signature = _mapping_value(baseline_object.get("function_signature"))
    changed_fields = _changed_mapping_fields(
        current=current_signature,
        baseline=baseline_signature,
    )
    if changed_fields == {"description"}:
        return "function.update.description"
    if changed_fields:
        return "function.update.signature_shape"
    return None


def _changed_mapping_fields(
    *,
    current: Mapping[str, object],
    baseline: Mapping[str, object],
) -> set[str]:
    if not current or not baseline:
        return set()
    fields = set(current) | set(baseline)
    return {field for field in fields if current.get(field) != baseline.get(field)}


def _mapping_field_projection(
    value: Mapping[str, object],
    *,
    fields: tuple[str, ...],
) -> dict[str, object]:
    return {field: value.get(field) for field in fields}


def _typed_operation_baseline_payload(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    baseline_object = _mapping_value(entry.get("baseline_object"))
    return {
        "compare_status": _optional_text(entry.get("baseline_compare_status")),
        "compare_operation": _optional_text(entry.get("baseline_compare_operation")),
        "object_matched": entry.get("baseline_object_matched") is True,
        "object_id": _optional_text(entry.get("baseline_object_id")),
        "object_kind": _optional_text(entry.get("baseline_object_kind")),
        "object_instance_graph_commit_id": _optional_text(
            entry.get("baseline_object_instance_graph_commit_id")
        ),
        "object": baseline_object if baseline_object else None,
    }


def _typed_operation_current_payload(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    subject_kind = _string_value(entry.get("ontology_subject_kind"))
    payload = _mapping_value(entry.get("payload"))
    current: dict[str, object] = {
        "semantic_key": _optional_text(entry.get("semantic_key")),
        "object_kind": subject_kind,
        "semantic_subject_type": _optional_text(entry.get("semantic_subject_type")),
        "node_type": _optional_text(entry.get("node_type")),
        "node_key": _optional_text(entry.get("node_key")),
        "entity_id": _optional_text(entry.get("entity_id")),
        "entity_name": _optional_text(entry.get("entity_name")),
        "graph_semantic_key": _optional_text(entry.get("graph_semantic_key")),
        "payload": payload,
    }
    if subject_kind == "attribute":
        current.update(
            {
                "owner_semantic_key": _optional_text(entry.get("parent_semantic_key")),
                "owner_object_id": _optional_text(entry.get("owner_object_id")),
                "attribute_name": _optional_text(entry.get("attribute_name")),
                "attribute_config_id": _optional_text(entry.get("attribute_config_id")),
                "class_config_id": _optional_text(entry.get("class_config_id")),
                "class_config_attribute_config_id": _optional_text(
                    entry.get("class_config_attribute_config_id")
                ),
                "function_config_id": _optional_text(entry.get("function_config_id")),
                "function_config_attribute_config_id": _optional_text(
                    entry.get("function_config_attribute_config_id")
                ),
                "function_attribute_type": _optional_text(
                    entry.get("function_attribute_type")
                ),
                "attribute_membership_semantic_key": _optional_text(
                    entry.get("attribute_membership_semantic_key")
                ),
                "attribute_membership_owner_kind": _optional_text(
                    entry.get("attribute_membership_owner_kind")
                ),
                "attribute_membership_signature": _mapping_value(
                    entry.get("attribute_membership_signature")
                    or payload.get("attribute_membership_signature")
                ),
                "attribute_signature": _mapping_value(
                    entry.get("attribute_signature")
                    or payload.get("attribute_signature")
                ),
            }
        )
    elif subject_kind == "class":
        current.update(
            {
                "class_config_id": _optional_text(
                    entry.get("class_config_id")
                    or entry.get("entity_id")
                    or payload.get("class_config_id")
                    or payload.get("entity_id")
                ),
                "object_config_graph_node_id": _optional_text(
                    entry.get("node_id")
                    or payload.get("node_id")
                    or entry.get("object_config_graph_node_id")
                    or payload.get("object_config_graph_node_id")
                ),
                "class_fqn": _optional_text(
                    entry.get("class_fqn") or payload.get("class_fqn")
                ),
                "name": _optional_text(
                    entry.get("name")
                    or entry.get("entity_name")
                    or payload.get("name")
                    or payload.get("entity_name")
                ),
                "description": _optional_text(
                    entry.get("description") or payload.get("description")
                ),
                "value_mode": _optional_text(
                    entry.get("value_mode") or payload.get("value_mode")
                ),
                "identity_mode": _optional_text(
                    entry.get("identity_mode") or payload.get("identity_mode")
                ),
                "is_base": _bool_value(
                    entry.get("is_base")
                    if entry.get("is_base") is not None
                    else payload.get("is_base")
                ),
                "is_edge": _bool_value(
                    entry.get("is_edge")
                    if entry.get("is_edge") is not None
                    else payload.get("is_edge")
                ),
                "class_signature": _mapping_value(
                    entry.get("class_signature") or payload.get("class_signature")
                ),
                "semantic_scope_closure_consumed": (
                    entry.get("semantic_scope_closure_consumed") is True
                ),
                "semantic_scope_closure_ready": (
                    entry.get("semantic_scope_closure_ready") is True
                ),
                "semantic_scope_closure_status": _optional_text(
                    entry.get("semantic_scope_closure_status")
                ),
                "semantic_scope_closure_gate_status": _optional_text(
                    entry.get("semantic_scope_closure_gate_status")
                ),
                "semantic_scope_closure_blockers": _tuple_text(
                    entry.get("semantic_scope_closure_blockers")
                ),
                "semantic_scope_closure_gate": _mapping_value(
                    entry.get("semantic_scope_closure_gate")
                ),
            }
        )
    elif subject_kind == "enum":
        current.update(
            {
                "enum_config_id": _optional_text(
                    entry.get("enum_config_id")
                    or entry.get("entity_id")
                    or payload.get("enum_config_id")
                    or payload.get("entity_id")
                ),
                "object_config_graph_node_id": _optional_text(
                    entry.get("node_id")
                    or payload.get("node_id")
                    or entry.get("object_config_graph_node_id")
                    or payload.get("object_config_graph_node_id")
                ),
                "enum_fqn": _optional_text(
                    entry.get("enum_fqn") or payload.get("enum_fqn")
                ),
                "name": _optional_text(
                    entry.get("name")
                    or entry.get("entity_name")
                    or payload.get("name")
                    or payload.get("entity_name")
                ),
                "description": _optional_text(
                    entry.get("description") or payload.get("description")
                ),
                "values": _tuple_text(entry.get("values") or payload.get("values")),
                "semantic_scope_closure_consumed": (
                    entry.get("semantic_scope_closure_consumed") is True
                ),
                "semantic_scope_closure_ready": (
                    entry.get("semantic_scope_closure_ready") is True
                ),
                "semantic_scope_closure_status": _optional_text(
                    entry.get("semantic_scope_closure_status")
                ),
                "semantic_scope_closure_gate_status": _optional_text(
                    entry.get("semantic_scope_closure_gate_status")
                ),
                "semantic_scope_closure_blockers": _tuple_text(
                    entry.get("semantic_scope_closure_blockers")
                ),
                "semantic_scope_closure_gate": _mapping_value(
                    entry.get("semantic_scope_closure_gate")
                ),
            }
        )
    elif subject_kind == "enum_option":
        current.update(
            {
                "enum_semantic_key": _optional_text(
                    entry.get("enum_semantic_key")
                    or entry.get("parent_semantic_key")
                    or payload.get("enum_semantic_key")
                    or payload.get("parent_semantic_key")
                ),
                "parent_semantic_key": _optional_text(
                    entry.get("parent_semantic_key")
                    or entry.get("enum_semantic_key")
                    or payload.get("parent_semantic_key")
                    or payload.get("enum_semantic_key")
                ),
                "enum_config_id": _optional_text(
                    entry.get("enum_config_id") or payload.get("enum_config_id")
                ),
                "enum_option_id": _optional_text(
                    entry.get("enum_option_id")
                    or entry.get("entity_id")
                    or payload.get("enum_option_id")
                    or payload.get("entity_id")
                ),
                "enum_fqn": _optional_text(
                    entry.get("enum_fqn") or payload.get("enum_fqn")
                ),
                "value": _optional_text(
                    entry.get("value")
                    or entry.get("option_value")
                    or entry.get("entity_name")
                    or payload.get("value")
                    or payload.get("option_value")
                    or payload.get("entity_name")
                ),
                "label": _optional_text(entry.get("label") or payload.get("label")),
                "description": _optional_text(
                    entry.get("description") or payload.get("description")
                ),
                "position": _int_value(
                    entry.get("position")
                    if entry.get("position") is not None
                    else payload.get("position")
                ),
                "semantic_scope_closure_consumed": (
                    entry.get("semantic_scope_closure_consumed") is True
                ),
                "semantic_scope_closure_ready": (
                    entry.get("semantic_scope_closure_ready") is True
                ),
                "semantic_scope_closure_status": _optional_text(
                    entry.get("semantic_scope_closure_status")
                ),
                "semantic_scope_closure_gate_status": _optional_text(
                    entry.get("semantic_scope_closure_gate_status")
                ),
                "semantic_scope_closure_blockers": _tuple_text(
                    entry.get("semantic_scope_closure_blockers")
                ),
                "semantic_scope_closure_gate": _mapping_value(
                    entry.get("semantic_scope_closure_gate")
                ),
            }
        )
    elif subject_kind == "attribute_membership":
        current.update(
            {
                "owner_semantic_key": _optional_text(
                    entry.get("parent_semantic_key") or entry.get("owner_semantic_key")
                ),
                "attribute_semantic_key": _optional_text(
                    entry.get("attribute_semantic_key")
                    or entry.get("parent_semantic_key")
                ),
                "attribute_config_id": _optional_text(entry.get("attribute_config_id")),
                "class_config_id": _optional_text(entry.get("class_config_id")),
                "class_config_attribute_config_id": _optional_text(
                    entry.get("class_config_attribute_config_id")
                    or entry.get("entity_id")
                ),
                "function_config_id": _optional_text(entry.get("function_config_id")),
                "function_config_attribute_config_id": _optional_text(
                    entry.get("function_config_attribute_config_id")
                    or entry.get("entity_id")
                ),
                "function_attribute_type": _optional_text(
                    entry.get("function_attribute_type")
                ),
                "attribute_membership_owner_kind": _optional_text(
                    entry.get("attribute_membership_owner_kind")
                ),
                "attribute_membership_signature": _mapping_value(
                    entry.get("attribute_membership_signature")
                ),
                "attribute_membership_changed_fields": _tuple_text(
                    entry.get("attribute_membership_changed_fields")
                ),
                "attribute_membership_mutable_update_fields": _tuple_text(
                    entry.get("attribute_membership_mutable_update_fields")
                ),
                "attribute_membership_identity_replacement_fields": _tuple_text(
                    entry.get("attribute_membership_identity_replacement_fields")
                ),
                "attribute_membership_replacement_required": (
                    entry.get("attribute_membership_replacement_required") is True
                ),
            }
        )
    elif subject_kind == "function":
        current.update(
            {
                "owner_semantic_key": _optional_text(
                    entry.get("parent_semantic_key")
                    or entry.get("owner_semantic_key")
                    or entry.get("class_semantic_key")
                ),
                "class_config_id": _optional_text(entry.get("class_config_id")),
                "class_config_function_config_id": _optional_text(
                    entry.get("class_config_function_config_id")
                ),
                "function_config_id": _optional_text(entry.get("function_config_id")),
                "function_membership_semantic_key": _optional_text(
                    entry.get("function_membership_semantic_key")
                ),
                "function_membership_signature": _mapping_value(
                    entry.get("function_membership_signature")
                ),
                "function_name": _optional_text(entry.get("function_name")),
                "owner_key": _optional_text(
                    entry.get("owner_key") or payload.get("owner_key")
                ),
                "kind": _optional_text(entry.get("kind") or payload.get("kind")),
                "description": _optional_text(
                    entry.get("description")
                    or entry.get("function_description")
                    or payload.get("description")
                    or payload.get("function_description")
                ),
                "verb": _optional_text(
                    entry.get("verb")
                    or entry.get("function_verb")
                    or payload.get("verb")
                    or payload.get("function_verb")
                ),
                "is_async": _bool_value(
                    entry.get("is_async")
                    if entry.get("is_async") is not None
                    else payload.get("is_async")
                ),
                "is_public": _bool_value(
                    entry.get("is_public")
                    if entry.get("is_public") is not None
                    else payload.get("is_public")
                ),
                "is_constructor": _bool_value(
                    entry.get("is_constructor")
                    if entry.get("is_constructor") is not None
                    else payload.get("is_constructor")
                ),
                "position": (
                    entry.get("position")
                    if entry.get("position") is not None
                    else payload.get("position")
                ),
                "function_signature": _mapping_value(entry.get("function_signature")),
                "semantic_scope_closure_consumed": (
                    entry.get("semantic_scope_closure_consumed") is True
                ),
                "semantic_scope_closure_ready": (
                    entry.get("semantic_scope_closure_ready") is True
                ),
                "semantic_scope_closure_status": _optional_text(
                    entry.get("semantic_scope_closure_status")
                ),
                "semantic_scope_closure_gate_status": _optional_text(
                    entry.get("semantic_scope_closure_gate_status")
                ),
                "semantic_scope_closure_blockers": _tuple_text(
                    entry.get("semantic_scope_closure_blockers")
                ),
                "semantic_scope_closure_gate": _mapping_value(
                    entry.get("semantic_scope_closure_gate")
                ),
            }
        )
    elif subject_kind == "function_membership":
        current.update(
            {
                "owner_semantic_key": _optional_text(
                    entry.get("parent_semantic_key") or entry.get("owner_semantic_key")
                ),
                "class_config_id": _optional_text(entry.get("class_config_id")),
                "class_config_function_config_id": _optional_text(
                    entry.get("class_config_function_config_id")
                    or entry.get("entity_id")
                ),
                "function_config_id": _optional_text(entry.get("function_config_id")),
                "function_name": _optional_text(entry.get("function_name")),
                "function_semantic_key": _optional_text(
                    entry.get("function_semantic_key")
                    or entry.get("parent_semantic_key")
                ),
                "function_membership_signature": _mapping_value(
                    entry.get("function_membership_signature")
                ),
            }
        )
    elif subject_kind == "function_impl":
        current.update(
            {
                "owner_semantic_key": _optional_text(entry.get("owner_semantic_key")),
                "function_semantic_key": _optional_text(
                    entry.get("function_semantic_key")
                    or entry.get("parent_semantic_key")
                ),
                "function_name": _optional_text(entry.get("function_name")),
                "function_impl_key": _optional_text(entry.get("function_impl_key")),
                "function_impl_kind": _optional_text(entry.get("function_impl_kind")),
                "function_impl_signature": _mapping_value(
                    entry.get("function_impl_signature")
                ),
            }
        )
    elif subject_kind == "relationship":
        current.update(
            {
                "owner_semantic_key": _optional_text(
                    entry.get("parent_semantic_key")
                    or entry.get("owner_semantic_key")
                    or entry.get("source_class_semantic_key")
                ),
                "source_class_semantic_key": _optional_text(
                    entry.get("source_class_semantic_key")
                    or entry.get("parent_semantic_key")
                    or entry.get("owner_semantic_key")
                ),
                "source_class_config_id": _optional_text(
                    entry.get("source_class_config_id")
                    or entry.get("class_config_id")
                    or payload.get("source_class_config_id")
                    or payload.get("class_config_id")
                ),
                "target_class_config_id": _optional_text(
                    entry.get("target_class_config_id")
                    or payload.get("target_class_config_id")
                ),
                "relationship_config_id": _optional_text(
                    entry.get("relationship_config_id")
                    or entry.get("class_config_relationship_id")
                    or entry.get("entity_id")
                    or payload.get("relationship_config_id")
                    or payload.get("class_config_relationship_id")
                    or payload.get("entity_id")
                ),
                "class_config_relationship_id": _optional_text(
                    entry.get("class_config_relationship_id")
                    or entry.get("relationship_config_id")
                    or entry.get("entity_id")
                    or payload.get("class_config_relationship_id")
                    or payload.get("relationship_config_id")
                    or payload.get("entity_id")
                ),
                "source_class_fqn": _optional_text(
                    entry.get("source_class_fqn") or payload.get("source_class_fqn")
                ),
                "target_class_fqn": _optional_text(
                    entry.get("target_class_fqn") or payload.get("target_class_fqn")
                ),
                "relationship_key": _optional_text(entry.get("relationship_key")),
                "relationship_type": _optional_text(entry.get("relationship_type")),
                "relationship_signature": _mapping_value(
                    entry.get("relationship_signature")
                ),
                "semantic_scope_closure_consumed": (
                    entry.get("semantic_scope_closure_consumed") is True
                ),
                "semantic_scope_closure_ready": (
                    entry.get("semantic_scope_closure_ready") is True
                ),
                "semantic_scope_closure_status": _optional_text(
                    entry.get("semantic_scope_closure_status")
                ),
                "semantic_scope_closure_gate_status": _optional_text(
                    entry.get("semantic_scope_closure_gate_status")
                ),
                "semantic_scope_closure_blockers": _tuple_text(
                    entry.get("semantic_scope_closure_blockers")
                ),
                "semantic_scope_closure_gate": _mapping_value(
                    entry.get("semantic_scope_closure_gate")
                ),
                "semantic_scope_closure_gates": tuple(
                    _tuple_evidence(entry.get("semantic_scope_closure_gates"))
                ),
            }
        )
    return current


def _typed_operation_ocg_payload(
    *,
    entry: Mapping[str, object],
    operation_family: str,
) -> dict[str, object]:
    subject_kind = _string_value(entry.get("ontology_subject_kind"))
    payload = _mapping_value(entry.get("payload"))
    if operation_family == "delete":
        if subject_kind == "attribute":
            operation = "delete_attribute_config"
            arguments = {
                "semantic_key": entry.get("semantic_key"),
                "object_id": entry.get("baseline_object_id"),
                "owner_semantic_key": entry.get("parent_semantic_key"),
                "name": entry.get("attribute_name"),
            }
            receiver_semantic_key = _optional_text(entry.get("parent_semantic_key"))
        elif subject_kind == "function_impl":
            operation = "delete_function_impl"
            arguments = {
                "semantic_key": entry.get("semantic_key"),
                "object_id": entry.get("baseline_object_id"),
                "function_semantic_key": entry.get("function_semantic_key"),
                "function_impl_key": entry.get("function_impl_key"),
            }
            receiver_semantic_key = _optional_text(
                entry.get("function_semantic_key") or entry.get("parent_semantic_key")
            )
        elif subject_kind == "function":
            operation = "delete_function_config"
            arguments = {
                "semantic_key": entry.get("semantic_key"),
                "object_id": entry.get("baseline_object_id"),
                "function_config_id": (
                    entry.get("function_config_id") or entry.get("entity_id")
                ),
                "class_config_id": entry.get("class_config_id"),
                "owner_semantic_key": (
                    entry.get("owner_semantic_key")
                    or entry.get("parent_semantic_key")
                    or entry.get("class_semantic_key")
                ),
                "name": entry.get("function_name") or entry.get("name"),
            }
            receiver_semantic_key = _optional_text(
                entry.get("owner_semantic_key")
                or entry.get("parent_semantic_key")
                or entry.get("class_semantic_key")
            )
        elif subject_kind in {"class", "enum", "relationship", "function"}:
            operation = "delete_object_config_graph_node"
            arguments = {
                "semantic_key": entry.get("semantic_key"),
                "object_id": entry.get("baseline_object_id"),
                "graph_semantic_key": entry.get("graph_semantic_key"),
                "node_key": entry.get("node_key"),
                "node_type": entry.get("node_type"),
            }
            receiver_semantic_key = _optional_text(entry.get("graph_semantic_key"))
        else:
            operation = "delete_meta_ocg_object"
            arguments = {
                "semantic_key": entry.get("semantic_key"),
                "object_id": entry.get("baseline_object_id"),
                "object_kind": subject_kind,
            }
            receiver_semantic_key = None
    elif subject_kind == "object_config_graph_package":
        operation = "ensure_object_config_graph_package"
        arguments = {
            "package_name": payload.get("package_name"),
            "fqn_prefix": payload.get("fqn_prefix"),
            "package_kind": payload.get("package_kind"),
        }
        receiver_semantic_key = None
    elif subject_kind == "object_config_graph":
        operation = "ensure_object_config_graph"
        arguments = {
            "name": payload.get("name"),
            "fqn_prefix": payload.get("fqn_prefix"),
            "language": payload.get("language"),
            "hash": payload.get("hash"),
            "node_count": payload.get("node_count"),
        }
        receiver_semantic_key = None
    elif subject_kind == "attribute":
        operation = "ensure_attribute_config"
        arguments = {
            "owner_semantic_key": entry.get("parent_semantic_key"),
            "name": entry.get("attribute_name"),
            "attribute_signature": _mapping_value(entry.get("attribute_signature")),
        }
        receiver_semantic_key = _optional_text(entry.get("parent_semantic_key"))
    elif subject_kind == "attribute_membership":
        operation = "ensure_attribute_membership_config"
        arguments = {
            "semantic_key": entry.get("semantic_key"),
            "object_id": (
                entry.get("class_config_attribute_config_id")
                or entry.get("function_config_attribute_config_id")
                or payload.get("class_config_attribute_config_id")
                or payload.get("function_config_attribute_config_id")
                or payload.get("entity_id")
            ),
            "owner_kind": (
                entry.get("attribute_membership_owner_kind")
                or payload.get("attribute_membership_owner_kind")
            ),
            "class_config_id": (
                entry.get("class_config_id") or payload.get("class_config_id")
            ),
            "function_config_id": (
                entry.get("function_config_id") or payload.get("function_config_id")
            ),
            "attribute_config_id": (
                entry.get("attribute_config_id") or payload.get("attribute_config_id")
            ),
            "attribute_name": (
                entry.get("attribute_name")
                or payload.get("attribute_name")
                or payload.get("entity_name")
            ),
            "function_attribute_type": (
                entry.get("function_attribute_type")
                or payload.get("function_attribute_type")
            ),
            "attribute_membership_signature": _mapping_value(
                entry.get("attribute_membership_signature")
                or payload.get("attribute_membership_signature")
            ),
        }
        receiver_semantic_key = _optional_text(
            entry.get("parent_semantic_key")
            or entry.get("owner_semantic_key")
            or payload.get("parent_semantic_key")
        )
    elif subject_kind in {"class", "enum", "relationship", "function"}:
        operation = "ensure_object_config_graph_node"
        arguments = {
            "graph_semantic_key": payload.get("graph_semantic_key"),
            "node_key": payload.get("node_key"),
            "node_type": payload.get("node_type"),
            "entity_id": payload.get("entity_id"),
            "entity_name": payload.get("entity_name"),
            "function_signature": payload.get("function_signature"),
            "relationship_signature": payload.get("relationship_signature"),
            "source_paths": payload.get("source_paths"),
        }
        receiver_semantic_key = _optional_text(payload.get("graph_semantic_key"))
    elif subject_kind == "function_membership":
        operation = "ensure_class_config_function_config"
        arguments = {
            "semantic_key": entry.get("semantic_key"),
            "object_id": (
                entry.get("class_config_function_config_id")
                or payload.get("class_config_function_config_id")
                or payload.get("entity_id")
            ),
            "class_config_id": (
                entry.get("class_config_id") or payload.get("class_config_id")
            ),
            "function_config_id": (
                entry.get("function_config_id") or payload.get("function_config_id")
            ),
            "function_name": (
                entry.get("function_name")
                or payload.get("function_name")
                or payload.get("entity_name")
            ),
            "function_membership_signature": _mapping_value(
                entry.get("function_membership_signature")
                or payload.get("function_membership_signature")
            ),
        }
        receiver_semantic_key = _optional_text(
            entry.get("parent_semantic_key")
            or entry.get("owner_semantic_key")
            or payload.get("parent_semantic_key")
        )
    elif subject_kind == "function_impl":
        operation = "ensure_function_impl"
        arguments = {
            "function_semantic_key": payload.get("function_semantic_key"),
            "function_name": payload.get("function_name"),
            "function_impl_key": payload.get("function_impl_key"),
            "function_impl_kind": payload.get("function_impl_kind"),
            "function_impl_signature": payload.get("function_impl_signature"),
        }
        receiver_semantic_key = _optional_text(
            payload.get("function_semantic_key") or payload.get("parent_semantic_key")
        )
    else:
        operation = "unknown_meta_ocg_operation"
        arguments = dict(payload)
        receiver_semantic_key = None
    return {
        "operation": operation,
        "operation_family": operation_family,
        "receiver_semantic_key": receiver_semantic_key,
        "arguments": arguments,
        "execution_wired": False,
    }


def _typed_operation_change_projection(
    *,
    entry: Mapping[str, object],
    operation_family: str,
    provider_operation_type: str,
) -> dict[str, object]:
    subject_kind = _string_value(entry.get("ontology_subject_kind"))
    semantic_key = _optional_text(entry.get("semantic_key"))
    return {
        "change_type": "semantic_operation_preview",
        "change_key": f"aware_meta.provider_delta.{subject_kind}.{operation_family}",
        "semantic_key": semantic_key,
        "verb": operation_family,
        "subject_type": _optional_text(entry.get("semantic_subject_type")),
        "provider_operation_type": provider_operation_type,
        "source_refs": _tuple_text(entry.get("source_refs")),
        "delta_keys": (
            (source_delta_key,)
            if (source_delta_key := _optional_text(entry.get("source_delta_key")))
            is not None
            else ()
        ),
        "condition_keys": (
            "meta.baseline_index_compared",
            f"meta.baseline_compare.{_string_value(entry.get('baseline_compare_status'))}",
            f"meta.operation_family.{operation_family}",
        ),
        "payload": _typed_operation_current_payload(entry=entry),
    }


def _typed_operation_entry_blocked_reason(
    *,
    entry: Mapping[str, object],
) -> str:
    return (
        _optional_text(entry.get("blocked_reason"))
        or _optional_text(entry.get("semantic_scope_closure_blocked_reason"))
        or _first_text(_tuple_text(entry.get("semantic_scope_closure_blockers")))
        or _optional_text(entry.get("baseline_compare_status"))
        or "meta_ocg_typed_operation_entry_blocked"
    )


def _semantic_change_by_semantic_key(
    *,
    semantic_change_payloads: tuple[Mapping[str, object], ...],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for change in semantic_change_payloads:
        semantic_key = _optional_text(change.get("semantic_key"))
        if semantic_key is not None:
            entries[semantic_key] = change
    return entries


def _semantic_change_by_delta_key(
    *,
    semantic_change_payloads: tuple[Mapping[str, object], ...],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for change in semantic_change_payloads:
        for delta_key in _tuple_text(change.get("delta_keys")):
            entries[delta_key] = change
    return entries


def _semantic_change_payload(payload: Mapping[str, object]) -> dict[str, object]:
    normalized = {str(key): value for key, value in payload.items()}
    if "change_key" not in normalized:
        event_key = _optional_text(normalized.pop("event_key", None))
        if event_key is not None:
            normalized["change_key"] = event_key
    else:
        normalized.pop("event_key", None)
    if "change_type" not in normalized:
        event_type = _optional_text(normalized.pop("event_type", None))
        if event_type is not None:
            normalized["change_type"] = event_type
    else:
        normalized.pop("event_type", None)
    if "change_kind" not in normalized:
        event_kind = _optional_text(normalized.pop("event_kind", None))
        if event_kind is not None:
            normalized["change_kind"] = event_kind
    else:
        normalized.pop("event_kind", None)
    return normalized


def _function_call_plan_by_semantic_key(
    *,
    function_call_plans: tuple[SemanticCapabilityFunctionCallPlan, ...],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for plan in function_call_plans:
        payload = plan.evidence_payload()
        semantic_key = _optional_text(payload.get("result_semantic_key"))
        if semantic_key is not None:
            entries[semantic_key] = payload
    return entries


def _typed_operation_count_by_field(
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


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_text(values: tuple[str, ...]) -> str | None:
    return values[0] if values else None


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = _optional_text(value)
    if text is None:
        return False
    return text.casefold() in {"1", "true", "yes", "y", "on"}


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = _optional_text(value)
    if text is None:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _tuple_text(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text for text in (_optional_text(item) for item in value) if text is not None
    )


__all__ = [
    "_provider_delta_typed_operation_plan",
    "_typed_operation_count_by_field",
]
