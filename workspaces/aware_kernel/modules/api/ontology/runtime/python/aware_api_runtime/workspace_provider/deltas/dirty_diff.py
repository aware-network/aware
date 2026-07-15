from __future__ import annotations

from collections.abc import Mapping

from aware_code.semantic_capability import SemanticCapabilityDelta
from aware_api_runtime.workspace_provider.deltas.baseline import (
    API_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION,
    api_delta_baseline_commit_refs,
    api_delta_baseline_ref_payload,
    api_delta_current_head_context_sources,
    api_delta_current_semantic_object_ids,
    api_delta_previous_materialization_baseline_semantic_object_index,
    api_delta_resolved_argument_ref_object_ids,
)
from aware_api_runtime.source.semantic_analysis import APISemanticAnalysisResult


API_DIRTY_DIFF_CONTRACT_VERSION = "aware.api.provider-delta.semantic-dirty-diff.v3"


def api_delta_semantic_dirty_diff_from_analysis(
    *,
    analysis: APISemanticAnalysisResult,
    request: object,
    current_delta_fingerprint: str,
    baseline_hydration_preflight: Mapping[str, object],
) -> dict[str, object]:
    preview = analysis.change_preview
    semantic_deltas = tuple(preview.semantic_deltas)
    current_semantic_object_ids = api_delta_current_semantic_object_ids(
        request=request,
    )
    baseline_semantic_object_index = (
        api_delta_previous_materialization_baseline_semantic_object_index(
            request=request,
        )
    )
    resolved_argument_ref_object_ids = api_delta_resolved_argument_ref_object_ids(
        request=request,
    )
    baseline_index_available = bool(baseline_semantic_object_index)
    baseline_index_sources = (
        api_delta_current_head_context_sources(request=request)
        if baseline_index_available
        else ()
    )
    baseline_commit_refs = api_delta_baseline_commit_refs(request=request)
    baseline_ref = api_delta_baseline_ref_payload(request=request)
    dirty_entries = tuple(
        api_delta_semantic_dirty_entry(
            delta=delta,
            current_semantic_object_ids=current_semantic_object_ids,
            baseline_semantic_object_index=baseline_semantic_object_index,
            resolved_argument_ref_object_ids=resolved_argument_ref_object_ids,
            baseline_index_available=baseline_index_available,
            baseline_object_instance_graph_commit_id=_optional_text(
                baseline_commit_refs.get(
                    "baseline_semantic_object_instance_graph_commit_id"
                )
            ),
        )
        for delta in semantic_deltas
    )
    blocked_entries = tuple(
        entry for entry in dirty_entries if entry.get("blocked") is True
    )
    diff_ready = not blocked_entries
    baseline_index_compare_status = (
        "baseline_index_compared"
        if baseline_index_available
        else "baseline_semantic_object_index_unavailable"
    )
    baseline_index_compare_reason = (
        "api_provider_delta_baseline_index_compared"
        if baseline_index_available
        else "api_provider_delta_baseline_current_head_index_required"
    )
    return {
        "diff_kind": "api_provider_delta_semantic_dirty_diff",
        "contract_version": API_DIRTY_DIFF_CONTRACT_VERSION,
        "status": (
            "semantic_dirty_diff_ready" if diff_ready else "semantic_dirty_diff_blocked"
        ),
        "reason": (
            "api_provider_delta_dirty_diff_ready"
            if diff_ready
            else "api_provider_delta_baseline_payload_comparison_blocked"
        ),
        "source": "aware_api.semantic_analysis",
        "baseline_identity_source": "workspace.baseline_ref",
        "baseline_hydration_status": baseline_hydration_preflight.get("status"),
        "baseline_hydration_reason": baseline_hydration_preflight.get("reason"),
        "baseline_branch_id": (
            _optional_text(baseline_ref.get("semantic_branch_id"))
            if baseline_ref is not None
            else None
        ),
        "baseline_projection_name": (
            _optional_text(baseline_ref.get("semantic_projection_name"))
            if baseline_ref is not None
            else None
        ),
        "baseline_semantic_package_id": (
            _optional_text(baseline_ref.get("semantic_package_id"))
            if baseline_ref is not None
            else None
        ),
        "baseline_semantic_package_commit_id": (
            _optional_text(baseline_ref.get("semantic_package_commit_id"))
            if baseline_ref is not None
            else None
        ),
        "baseline_semantic_object_instance_graph_commit_id": (
            baseline_commit_refs.get(
                "baseline_semantic_object_instance_graph_commit_id"
            )
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": (
            baseline_commit_refs.get(
                "baseline_semantic_root_object_instance_graph_commit_id"
            )
        ),
        "baseline_semantic_object_index_contract_version": (
            API_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION
        ),
        "baseline_semantic_object_index_available": bool(
            baseline_semantic_object_index
        ),
        "baseline_semantic_object_index_status": (
            "baseline_index_ready"
            if baseline_semantic_object_index
            else "baseline_semantic_object_index_unavailable"
        ),
        "baseline_semantic_object_index_count": len(baseline_semantic_object_index),
        "baseline_semantic_object_index_keys": tuple(
            sorted(baseline_semantic_object_index)
        ),
        "baseline_semantic_object_index_sources": baseline_index_sources,
        "baseline_index_compare_available": baseline_index_available,
        "baseline_index_compare_status": baseline_index_compare_status,
        "baseline_index_compare_reason": baseline_index_compare_reason,
        "current_delta_fingerprint": current_delta_fingerprint,
        "changed_source_files": tuple(preview.changed_source_files),
        "affected_api_names": tuple(preview.affected_api_names),
        "affected_capability_names": tuple(preview.affected_capability_names),
        "semantic_delta_count": len(semantic_deltas),
        "dirty_entry_count": len(dirty_entries),
        "actionable_entry_count": sum(
            1
            for entry in dirty_entries
            if _optional_text(entry.get("operation_family"))
            in {"create", "update", "upsert"}
        ),
        "noop_entry_count": sum(
            1
            for entry in dirty_entries
            if _optional_text(entry.get("operation_family")) == "noop"
        ),
        "blocked_entry_count": len(blocked_entries),
        "blockers": tuple(
            _optional_text(entry.get("blocked_reason"))
            or "api_provider_delta_dirty_entry_blocked"
            for entry in blocked_entries
        ),
        "dirty_entry_kind_counts": api_delta_dirty_entry_kind_counts(
            dirty_entries=dirty_entries,
        ),
        "dirty_operation_counts": api_delta_dirty_operation_counts(
            dirty_entries=dirty_entries,
            field_name="dirty_operation",
        ),
        "baseline_compare_operation_counts": api_delta_dirty_operation_counts(
            dirty_entries=dirty_entries,
            field_name="baseline_compare_operation",
        ),
        "semantic_dirty_entries": dirty_entries,
        "available": diff_ready,
        "blocked": not diff_ready,
        "blocked_status": (
            None if diff_ready else "baseline_payload_comparison_blocked"
        ),
        "blocked_reason": (
            None
            if diff_ready
            else "api_provider_delta_baseline_payload_comparison_blocked"
        ),
        "did_compare_against_current_delta": True,
        "compare_mode": (
            "api_commit_backed_semantic_payload_index"
            if baseline_semantic_object_index
            else "api_current_head_object_id_index_only"
        ),
        "would_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def api_delta_semantic_dirty_entry(
    *,
    delta: SemanticCapabilityDelta,
    current_semantic_object_ids: Mapping[str, str],
    baseline_semantic_object_index: Mapping[str, Mapping[str, object]],
    resolved_argument_ref_object_ids: Mapping[str, str],
    baseline_index_available: bool,
    baseline_object_instance_graph_commit_id: str | None,
) -> dict[str, object]:
    _ = resolved_argument_ref_object_ids
    payload = _mapping_payload(delta.evidence_payload())
    semantic_key = _optional_text(payload.get("semantic_key")) or ""
    subject_type = _optional_text(payload.get("subject_type"))
    subject_kind = api_delta_subject_kind(subject_type=subject_type)
    baseline_object_id = (
        _optional_text(current_semantic_object_ids.get(semantic_key))
        if baseline_index_available
        else None
    )
    matched = baseline_object_id is not None
    current_payload = _mapping_payload(payload.get("after_payload"))
    baseline_entry = _mapping_payload(baseline_semantic_object_index.get(semantic_key))
    baseline_payload = _api_delta_baseline_comparison_payload(
        entry=baseline_entry,
    )
    field_roles = _api_delta_field_roles(subject_kind=subject_kind)
    normalized_current, current_missing_fields = (
        _api_delta_normalized_comparison_payload(
            subject_kind=subject_kind,
            payload=current_payload,
        )
    )
    normalized_baseline, baseline_missing_fields = (
        _api_delta_normalized_comparison_payload(
            subject_kind=subject_kind,
            payload=baseline_payload,
        )
    )
    current_topology, current_missing_topology_fields = (
        _api_delta_normalized_topology_payload(
            subject_kind=subject_kind,
            payload=current_payload,
        )
    )
    baseline_topology, baseline_missing_topology_fields = (
        _api_delta_normalized_topology_payload(
            subject_kind=subject_kind,
            payload=baseline_payload,
        )
    )
    comparison_blocker = _api_delta_comparison_blocker(
        baseline_index_available=baseline_index_available,
        matched=matched,
        baseline_entry=baseline_entry,
        current_missing_fields=current_missing_fields,
        baseline_missing_fields=baseline_missing_fields,
    )
    changed_fields = tuple(
        field_name
        for field_name in _api_delta_comparison_fields(subject_kind=subject_kind)
        if normalized_current.get(field_name) != normalized_baseline.get(field_name)
    )
    changed_topology_fields = tuple(
        field_name
        for field_name in field_roles["topology_fields"]
        if matched
        and field_name not in current_missing_topology_fields
        and field_name not in baseline_missing_topology_fields
        and current_topology.get(field_name) != baseline_topology.get(field_name)
    )
    if comparison_blocker is not None:
        operation_family = "blocked"
    elif not matched:
        operation_family = "create"
    elif changed_fields:
        operation_family = "update"
    else:
        operation_family = "noop"
    operation = (
        "blocked"
        if operation_family == "blocked"
        else f"{subject_kind}_{operation_family}"
    )
    return {
        "entry_kind": "api_provider_delta_semantic_dirty_entry",
        "entry_key": _optional_text(payload.get("delta_key")) or semantic_key,
        "semantic_key": semantic_key,
        "source_delta_key": _optional_text(payload.get("delta_key")),
        "source": payload.get("source") or "aware_api.semantic_analysis",
        "source_refs": tuple(_tuple_evidence(payload.get("source_refs"))),
        "verb": payload.get("verb"),
        "semantic_subject_type": subject_type,
        "ontology_subject_kind": subject_kind,
        "dirty_operation": operation,
        "operation_family": operation_family,
        "baseline_compare_status": (
            "baseline_payload_changed"
            if matched and operation_family == "update"
            else (
                "baseline_payload_unchanged"
                if matched and operation_family == "noop"
                else (
                    "baseline_object_missing"
                    if not matched and baseline_index_available
                    else "baseline_payload_comparison_blocked"
                )
            )
        ),
        "baseline_compare_operation": operation,
        "baseline_object_matched": matched if baseline_index_available else None,
        "baseline_object_id": baseline_object_id,
        "baseline_object_kind": subject_kind if matched else None,
        "baseline_object_instance_graph_commit_id": (
            baseline_object_instance_graph_commit_id if matched else None
        ),
        "baseline_payload_available": bool(baseline_payload),
        "before_payload": normalized_baseline if matched else None,
        "after_payload": normalized_current,
        "changed_fields": changed_fields,
        "changed_field_count": len(changed_fields),
        "field_roles": field_roles,
        "identity_fields": field_roles["identity_fields"],
        "metadata_fields": field_roles["metadata_fields"],
        "comparable_metadata_fields": field_roles["comparable_metadata_fields"],
        "non_comparable_metadata_fields": field_roles["non_comparable_metadata_fields"],
        "contract_fields": field_roles["contract_fields"],
        "topology_fields": field_roles["topology_fields"],
        "before_topology_payload": baseline_topology if matched else None,
        "after_topology_payload": current_topology,
        "changed_topology_fields": changed_topology_fields,
        "changed_topology_field_count": len(changed_topology_fields),
        "current_missing_comparison_fields": current_missing_fields,
        "baseline_missing_comparison_fields": baseline_missing_fields,
        "current_missing_topology_fields": current_missing_topology_fields,
        "baseline_missing_topology_fields": (
            baseline_missing_topology_fields if matched else ()
        ),
        "blocked": comparison_blocker is not None,
        "blocked_reason": comparison_blocker,
        "payload": current_payload,
        "would_execute": False,
        "would_persist": False,
    }


def _api_delta_baseline_comparison_payload(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    nested = entry.get("payload")
    if isinstance(nested, Mapping):
        return _mapping_payload(nested)
    return {
        str(key): value
        for key, value in entry.items()
        if str(key)
        not in {
            "semantic_key",
            "object_id",
            "object_kind",
            "object_instance_graph_commit_id",
            "source",
            "source_refs",
        }
    }


def _api_delta_field_roles(*, subject_kind: str) -> dict[str, tuple[str, ...]]:
    roles = {
        "api": {
            "identity_fields": ("name",),
            "metadata_fields": ("description",),
            "comparable_metadata_fields": (),
            "contract_fields": (),
            "topology_fields": ("capability_count", "graph_count"),
        },
        "api_capability": {
            "identity_fields": ("api_name", "name"),
            "metadata_fields": ("description",),
            "comparable_metadata_fields": ("description",),
            "contract_fields": (),
            "topology_fields": ("endpoint_count",),
        },
        "api_capability_endpoint": {
            "identity_fields": ("api_name", "capability_name", "name"),
            "metadata_fields": ("description",),
            "comparable_metadata_fields": ("description",),
            "contract_fields": ("request_class_ref",),
            "topology_fields": (),
        },
    }.get(subject_kind, {})
    identity_fields = tuple(roles.get("identity_fields", ()))
    metadata_fields = tuple(roles.get("metadata_fields", ()))
    comparable_metadata_fields = tuple(roles.get("comparable_metadata_fields", ()))
    return {
        "identity_fields": identity_fields,
        "metadata_fields": metadata_fields,
        "comparable_metadata_fields": comparable_metadata_fields,
        "non_comparable_metadata_fields": tuple(
            field_name
            for field_name in metadata_fields
            if field_name not in comparable_metadata_fields
        ),
        "contract_fields": tuple(roles.get("contract_fields", ())),
        "topology_fields": tuple(roles.get("topology_fields", ())),
    }


def _api_delta_comparison_fields(*, subject_kind: str) -> tuple[str, ...]:
    roles = _api_delta_field_roles(subject_kind=subject_kind)
    return (
        roles["identity_fields"]
        + roles["comparable_metadata_fields"]
        + roles["contract_fields"]
    )


def _api_delta_normalized_comparison_payload(
    *,
    subject_kind: str,
    payload: Mapping[str, object],
) -> tuple[dict[str, object], tuple[str, ...]]:
    normalized = dict(payload)
    comparison_fields = _api_delta_comparison_fields(subject_kind=subject_kind)
    missing_fields = tuple(
        field_name
        for field_name in comparison_fields
        if field_name not in normalized
        or (
            field_name == "request_class_ref"
            and _optional_text(normalized.get(field_name)) is None
        )
    )
    return (
        {field_name: normalized.get(field_name) for field_name in comparison_fields},
        missing_fields,
    )


def _api_delta_normalized_topology_payload(
    *,
    subject_kind: str,
    payload: Mapping[str, object],
) -> tuple[dict[str, object], tuple[str, ...]]:
    topology_fields = _api_delta_field_roles(subject_kind=subject_kind)[
        "topology_fields"
    ]
    missing_fields = tuple(
        field_name for field_name in topology_fields if field_name not in payload
    )
    return (
        {field_name: payload.get(field_name) for field_name in topology_fields},
        missing_fields,
    )


def _api_delta_comparison_blocker(
    *,
    baseline_index_available: bool,
    matched: bool,
    baseline_entry: Mapping[str, object],
    current_missing_fields: tuple[str, ...],
    baseline_missing_fields: tuple[str, ...],
) -> str | None:
    if not baseline_index_available:
        return "api_provider_delta_baseline_object_id_index_unavailable"
    if not matched:
        return None
    if not baseline_entry:
        return "api_provider_delta_existing_object_baseline_payload_unavailable"
    if current_missing_fields:
        return "api_provider_delta_current_payload_comparison_fields_missing"
    if baseline_missing_fields:
        return "api_provider_delta_baseline_payload_comparison_fields_missing"
    return None


def api_delta_subject_kind(*, subject_type: str | None) -> str:
    return {
        "aware_api.Api": "api",
        "aware_api.ApiCapability": "api_capability",
        "aware_api.ApiCapabilityEndpoint": "api_capability_endpoint",
    }.get(subject_type or "", "api_semantic_object")


def api_delta_dirty_entry_kind_counts(
    *,
    dirty_entries: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in dirty_entries:
        kind = _optional_text(entry.get("ontology_subject_kind")) or "unknown"
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def api_delta_dirty_operation_counts(
    *,
    dirty_entries: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in dirty_entries:
        operation = _optional_text(entry.get(field_name)) or "unknown"
        counts[operation] = counts.get(operation, 0) + 1
    return counts


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
    "API_DIRTY_DIFF_CONTRACT_VERSION",
    "api_delta_dirty_entry_kind_counts",
    "api_delta_dirty_operation_counts",
    "api_delta_semantic_dirty_diff_from_analysis",
    "api_delta_semantic_dirty_entry",
    "api_delta_subject_kind",
]
