from __future__ import annotations

from collections.abc import Mapping

from aware_code.semantic_capability import SemanticCapabilityDelta
from aware_api_runtime.workspace_provider.deltas.baseline import (
    API_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION,
    api_delta_baseline_commit_refs,
    api_delta_baseline_ref_payload,
    api_delta_current_head_context_sources,
    api_delta_current_semantic_object_ids,
)
from aware_api_runtime.source.semantic_analysis import APISemanticAnalysisResult


API_DIRTY_DIFF_CONTRACT_VERSION = "aware.api.provider-delta.semantic-dirty-diff.v1"


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
    baseline_index_sources = api_delta_current_head_context_sources(
        request=request,
    )
    baseline_index_available = baseline_hydration_preflight.get(
        "current_head_context_available"
    ) is True and bool(current_semantic_object_ids)
    baseline_commit_refs = api_delta_baseline_commit_refs(request=request)
    baseline_ref = api_delta_baseline_ref_payload(request=request)
    dirty_entries = tuple(
        api_delta_semantic_dirty_entry(
            delta=delta,
            current_semantic_object_ids=current_semantic_object_ids,
            baseline_index_available=baseline_index_available,
            baseline_object_instance_graph_commit_id=_optional_text(
                baseline_commit_refs.get(
                    "baseline_semantic_object_instance_graph_commit_id"
                )
            ),
        )
        for delta in semantic_deltas
    )
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
        "status": "semantic_dirty_diff_ready",
        "reason": "api_provider_delta_dirty_diff_ready",
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
        "baseline_semantic_object_index_available": baseline_index_available,
        "baseline_semantic_object_index_status": (
            "baseline_index_ready"
            if baseline_index_available
            else "baseline_semantic_object_index_unavailable"
        ),
        "baseline_semantic_object_index_count": len(current_semantic_object_ids),
        "baseline_semantic_object_index_keys": tuple(
            sorted(current_semantic_object_ids)
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
        "available": True,
        "blocked": False,
        "blocked_status": None,
        "blocked_reason": None,
        "did_compare_against_current_delta": True,
        "compare_mode": (
            "api_current_head_semantic_key_index"
            if baseline_index_available
            else "api_current_head_semantic_key_index_unavailable"
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
    baseline_index_available: bool,
    baseline_object_instance_graph_commit_id: str | None,
) -> dict[str, object]:
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
    operation = (
        f"{subject_kind}_{'update' if matched else 'create'}"
        if baseline_index_available
        else "blocked"
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
        "baseline_compare_status": (
            "baseline_object_matched"
            if matched
            else (
                "baseline_object_missing"
                if baseline_index_available
                else "baseline_index_comparison_blocked"
            )
        ),
        "baseline_compare_operation": operation,
        "baseline_object_matched": matched if baseline_index_available else None,
        "baseline_object_id": baseline_object_id,
        "baseline_object_kind": subject_kind if matched else None,
        "baseline_object_instance_graph_commit_id": (
            baseline_object_instance_graph_commit_id if matched else None
        ),
        "payload": _mapping_payload(payload.get("after_payload")),
        "would_execute": False,
        "would_persist": False,
    }


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
