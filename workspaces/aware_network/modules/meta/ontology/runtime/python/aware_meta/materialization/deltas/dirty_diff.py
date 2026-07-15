from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
)
from aware_meta.materialization.runtime_delta import (
    META_OCG_RUNTIME_DELTA_TRANSFORM_CONTRACT_VERSION,
    MetaOcgRuntimeDeltaTransformRequest,
    build_meta_ocg_runtime_delta_transform,
)
from aware_meta.materialization.deltas.relationship_support import (
    relationship_deferred_attribute_dirty_entry,
    relationship_support_attribute_delta_only,
    relationship_update_support_attribute_index,
)
from aware_meta.semantic_analysis import MetaOcgSemanticAnalysisResult


_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION = (
    META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION
)
_BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION = (
    "aware.meta.ocg.baseline-semantic-object-index.v1"
)


def _semantic_dirty_diff_from_analysis(
    *,
    analysis: MetaOcgSemanticAnalysisResult,
    current_delta_fingerprint: str,
    baseline_dirty_preflight: Mapping[str, object],
) -> dict[str, object]:
    hydration = _mapping_value(
        baseline_dirty_preflight.get("baseline_hydration_preflight")
    )
    hydration_status = _string_value(hydration.get("status"))
    baseline_ready = hydration_status == "baseline_hydrated"
    semantic_delta_payloads = tuple(
        delta.evidence_payload()
        for delta in analysis.change_preview.semantic_deltas
    )
    if not baseline_ready:
        return _semantic_dirty_diff_blocked_payload(
            current_delta_fingerprint=current_delta_fingerprint,
            analysis=analysis,
            semantic_delta_count=len(semantic_delta_payloads),
            baseline_dirty_preflight=baseline_dirty_preflight,
            hydration=hydration,
        )
    baseline_semantic_object_index = _mapping_value(
        hydration.get("baseline_semantic_object_index")
    )
    runtime_delta_transform = build_meta_ocg_runtime_delta_transform(
        request=MetaOcgRuntimeDeltaTransformRequest(
            code_package_delta=analysis.code_package_delta,
            current_delta_fingerprint=current_delta_fingerprint,
            namespace_mappings=analysis.namespace_mappings,
            baseline_semantic_object_index=cast(
                Mapping[str, Mapping[str, object]],
                baseline_semantic_object_index,
            ),
            baseline_branch_id=_optional_text(hydration.get("semantic_branch_id")),
            baseline_projection_name=_optional_text(
                hydration.get("semantic_projection_name")
            ),
            baseline_projection_hash=_optional_text(
                hydration.get("semantic_projection_hash")
            ),
            baseline_semantic_package_id=_optional_text(
                hydration.get("semantic_package_id")
            ),
            baseline_semantic_object_instance_graph_commit_id=_optional_text(
                hydration.get("semantic_object_instance_graph_commit_id")
            ),
            baseline_semantic_root_object_instance_graph_commit_id=_optional_text(
                hydration.get("semantic_root_object_instance_graph_commit_id")
            ),
            changed_source_files=analysis.change_preview.changed_source_files,
            analysis_source_files=analysis.source_files,
        )
    )
    runtime_delta_transform_payload = runtime_delta_transform.evidence_payload()
    if not runtime_delta_transform.available:
        return _semantic_dirty_diff_runtime_delta_blocked_payload(
            current_delta_fingerprint=current_delta_fingerprint,
            analysis=analysis,
            semantic_delta_count=len(semantic_delta_payloads),
            baseline_dirty_preflight=baseline_dirty_preflight,
            hydration=hydration,
            baseline_semantic_object_index=baseline_semantic_object_index,
            runtime_delta_transform=runtime_delta_transform_payload,
        )
    dirty_entries = _semantic_dirty_entries_from_runtime_delta_transform(
        runtime_delta_transform=runtime_delta_transform_payload,
    )
    dirty_entries = _semantic_dirty_entries_with_baseline_index(
        dirty_entries=dirty_entries,
        baseline_semantic_object_index=baseline_semantic_object_index,
        baseline_commit_id=_optional_text(
            hydration.get("semantic_object_instance_graph_commit_id")
        ),
        runtime_delta_transform=runtime_delta_transform_payload,
    )
    dirty_entries = _semantic_dirty_entries_with_relationship_support_normalization(
        dirty_entries=dirty_entries,
    )
    stale_semantic_keys = _semantic_dirty_entries_stale_semantic_keys(
        dirty_entries=dirty_entries,
    )
    entry_kind_counts = _dirty_entry_kind_counts(dirty_entries=dirty_entries)
    operation_counts = _dirty_operation_counts(dirty_entries=dirty_entries)
    baseline_compare_operation_counts = _baseline_compare_operation_counts(
        dirty_entries=dirty_entries,
    )
    baseline_index_compare_available = bool(baseline_semantic_object_index)
    baseline_index_compare_status = (
        "baseline_index_compared"
        if baseline_index_compare_available
        else "baseline_semantic_object_index_unavailable"
    )
    baseline_index_compare_reason = (
        "meta_ocg_dirty_diff_compared_against_baseline_semantic_object_index"
        if baseline_index_compare_available
        else "meta_ocg_dirty_diff_requires_baseline_semantic_object_index"
    )
    return {
        "diff_kind": "meta_ocg_semantic_dirty_diff",
        "contract_version": _SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "source": "aware_meta.semantic_analysis",
        "baseline_identity_source": "workspace.baseline_ref",
        "baseline_hydration_status": hydration_status,
        "baseline_hydration_reason": _optional_text(hydration.get("reason")),
        "baseline_branch_id": _optional_text(hydration.get("semantic_branch_id")),
        "baseline_projection_name": _optional_text(
            hydration.get("semantic_projection_name")
        ),
        "baseline_projection_hash": _optional_text(
            hydration.get("semantic_projection_hash")
        ),
        "baseline_semantic_package_id": _optional_text(
            hydration.get("semantic_package_id")
        ),
        "baseline_semantic_package_commit_id": _optional_text(
            hydration.get("semantic_package_commit_id")
        ),
        "baseline_semantic_object_instance_graph_commit_id": _optional_text(
            hydration.get("semantic_object_instance_graph_commit_id")
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": _optional_text(
            hydration.get("semantic_root_object_instance_graph_commit_id")
        ),
        "baseline_object_counts": _mapping_value(hydration.get("object_counts")),
        "baseline_semantic_object_index_contract_version": (
            _BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION
        ),
        "baseline_semantic_object_index_available": (
            bool(hydration.get("baseline_semantic_object_index_available"))
            and baseline_index_compare_available
        ),
        "baseline_semantic_object_index_status": _optional_text(
            hydration.get("baseline_semantic_object_index_status")
        ),
        "baseline_semantic_object_index_count": len(baseline_semantic_object_index),
        "baseline_semantic_object_index_keys": tuple(
            sorted(baseline_semantic_object_index)
        ),
        "baseline_index_compare_available": baseline_index_compare_available,
        "baseline_index_compare_status": baseline_index_compare_status,
        "baseline_index_compare_reason": baseline_index_compare_reason,
        "runtime_delta_transform_contract_version": (
            META_OCG_RUNTIME_DELTA_TRANSFORM_CONTRACT_VERSION
        ),
        "runtime_delta_transform_status": _optional_text(
            runtime_delta_transform_payload.get("status")
        ),
        "runtime_delta_transform_reason": _optional_text(
            runtime_delta_transform_payload.get("reason")
        ),
        "runtime_delta_transform": runtime_delta_transform_payload,
        "current_delta_fingerprint": current_delta_fingerprint,
        "changed_source_files": analysis.change_preview.changed_source_files,
        "affected_object_config_graph_keys": (
            analysis.change_preview.affected_object_config_graph_keys
        ),
        "semantic_delta_count": len(semantic_delta_payloads),
        "dirty_entry_count": len(dirty_entries),
        "dirty_entry_kind_counts": entry_kind_counts,
        "dirty_operation_counts": operation_counts,
        "baseline_compare_operation_counts": baseline_compare_operation_counts,
        "stale_semantic_key_count": len(stale_semantic_keys),
        "stale_semantic_keys": stale_semantic_keys,
        "stale_source_refs": _tuple_text(
            runtime_delta_transform_payload.get("changed_runtime_source_refs")
        ),
        "deleted_source_refs": _tuple_text(
            runtime_delta_transform_payload.get("deleted_runtime_source_refs")
        ),
        "semantic_dirty_entries": dirty_entries,
        "available": True,
        "blocked": False,
        "blocked_status": None,
        "blocked_reason": None,
        "did_compare_against_current_delta": True,
        "compare_mode": "hydrated_baseline_index_runtime_delta_transform",
        "would_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def _semantic_dirty_diff_blocked_payload(
    *,
    current_delta_fingerprint: str,
    analysis: MetaOcgSemanticAnalysisResult,
    semantic_delta_count: int,
    baseline_dirty_preflight: Mapping[str, object],
    hydration: Mapping[str, object],
) -> dict[str, object]:
    hydration_status = _string_value(hydration.get("status"))
    if not hydration_status:
        hydration_status = _string_value(
            baseline_dirty_preflight.get("semantic_dirty_diff_status")
        )
    blocked_reason = _semantic_dirty_diff_blocked_reason(
        hydration_status=hydration_status,
    )
    return {
        "diff_kind": "meta_ocg_semantic_dirty_diff",
        "contract_version": _SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
        "status": "semantic_dirty_diff_blocked",
        "reason": blocked_reason,
        "source": "aware_meta.semantic_analysis",
        "baseline_identity_source": "workspace.baseline_ref",
        "baseline_hydration_status": hydration_status,
        "baseline_hydration_reason": _optional_text(hydration.get("reason")),
        "baseline_branch_id": _optional_text(hydration.get("semantic_branch_id")),
        "baseline_projection_name": _optional_text(
            hydration.get("semantic_projection_name")
        ),
        "baseline_projection_hash": _optional_text(
            hydration.get("semantic_projection_hash")
        ),
        "baseline_semantic_package_id": _optional_text(
            hydration.get("semantic_package_id")
        ),
        "baseline_semantic_package_commit_id": _optional_text(
            hydration.get("semantic_package_commit_id")
        ),
        "baseline_semantic_object_instance_graph_commit_id": _optional_text(
            hydration.get("semantic_object_instance_graph_commit_id")
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": _optional_text(
            hydration.get("semantic_root_object_instance_graph_commit_id")
        ),
        "baseline_object_counts": _mapping_value(hydration.get("object_counts")),
        "baseline_semantic_object_index_contract_version": (
            _BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION
        ),
        "baseline_semantic_object_index_available": False,
        "baseline_semantic_object_index_status": "baseline_not_hydrated",
        "baseline_semantic_object_index_count": 0,
        "baseline_semantic_object_index_keys": (),
        "baseline_index_compare_available": False,
        "baseline_index_compare_status": "requires_hydrated_baseline",
        "baseline_index_compare_reason": blocked_reason,
        "current_delta_fingerprint": current_delta_fingerprint,
        "changed_source_files": analysis.change_preview.changed_source_files,
        "affected_object_config_graph_keys": (
            analysis.change_preview.affected_object_config_graph_keys
        ),
        "semantic_delta_count": semantic_delta_count,
        "dirty_entry_count": 0,
        "dirty_entry_kind_counts": {},
        "dirty_operation_counts": {},
        "baseline_compare_operation_counts": {},
        "semantic_dirty_entries": (),
        "available": False,
        "blocked": True,
        "blocked_status": hydration_status,
        "blocked_reason": blocked_reason,
        "did_compare_against_current_delta": False,
        "compare_mode": "requires_hydrated_baseline",
        "would_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def _semantic_dirty_diff_runtime_delta_blocked_payload(
    *,
    current_delta_fingerprint: str,
    analysis: MetaOcgSemanticAnalysisResult,
    semantic_delta_count: int,
    baseline_dirty_preflight: Mapping[str, object],
    hydration: Mapping[str, object],
    baseline_semantic_object_index: Mapping[str, object],
    runtime_delta_transform: Mapping[str, object],
) -> dict[str, object]:
    _ = baseline_dirty_preflight
    hydration_status = _string_value(hydration.get("status"))
    blocked_reason = (
        _optional_text(runtime_delta_transform.get("reason"))
        or "meta_ocg_runtime_delta_transform_required"
    )
    baseline_index_available = bool(baseline_semantic_object_index)
    return {
        "diff_kind": "meta_ocg_semantic_dirty_diff",
        "contract_version": _SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
        "status": "semantic_dirty_diff_blocked",
        "reason": blocked_reason,
        "source": "aware_meta.materialization.runtime_delta",
        "baseline_identity_source": "workspace.baseline_ref",
        "baseline_hydration_status": hydration_status,
        "baseline_hydration_reason": _optional_text(hydration.get("reason")),
        "baseline_branch_id": _optional_text(hydration.get("semantic_branch_id")),
        "baseline_projection_name": _optional_text(
            hydration.get("semantic_projection_name")
        ),
        "baseline_projection_hash": _optional_text(
            hydration.get("semantic_projection_hash")
        ),
        "baseline_semantic_package_id": _optional_text(
            hydration.get("semantic_package_id")
        ),
        "baseline_semantic_package_commit_id": _optional_text(
            hydration.get("semantic_package_commit_id")
        ),
        "baseline_semantic_object_instance_graph_commit_id": _optional_text(
            hydration.get("semantic_object_instance_graph_commit_id")
        ),
        "baseline_semantic_root_object_instance_graph_commit_id": _optional_text(
            hydration.get("semantic_root_object_instance_graph_commit_id")
        ),
        "baseline_object_counts": _mapping_value(hydration.get("object_counts")),
        "baseline_semantic_object_index_contract_version": (
            _BASELINE_SEMANTIC_OBJECT_INDEX_CONTRACT_VERSION
        ),
        "baseline_semantic_object_index_available": baseline_index_available,
        "baseline_semantic_object_index_status": _optional_text(
            hydration.get("baseline_semantic_object_index_status")
        ),
        "baseline_semantic_object_index_count": len(baseline_semantic_object_index),
        "baseline_semantic_object_index_keys": tuple(
            sorted(baseline_semantic_object_index)
        ),
        "baseline_index_compare_available": False,
        "baseline_index_compare_status": "runtime_delta_transform_blocked",
        "baseline_index_compare_reason": blocked_reason,
        "runtime_delta_transform_contract_version": (
            META_OCG_RUNTIME_DELTA_TRANSFORM_CONTRACT_VERSION
        ),
        "runtime_delta_transform_status": _optional_text(
            runtime_delta_transform.get("status")
        ),
        "runtime_delta_transform_reason": blocked_reason,
        "runtime_delta_transform": dict(runtime_delta_transform),
        "current_delta_fingerprint": current_delta_fingerprint,
        "changed_source_files": analysis.change_preview.changed_source_files,
        "affected_object_config_graph_keys": (
            analysis.change_preview.affected_object_config_graph_keys
        ),
        "semantic_delta_count": semantic_delta_count,
        "dirty_entry_count": 0,
        "dirty_entry_kind_counts": {},
        "dirty_operation_counts": {},
        "baseline_compare_operation_counts": {},
        "semantic_dirty_entries": (),
        "available": False,
        "blocked": True,
        "blocked_status": _optional_text(runtime_delta_transform.get("status")),
        "blocked_reason": blocked_reason,
        "did_compare_against_current_delta": False,
        "compare_mode": "runtime_delta_transform_required",
        "would_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def _semantic_dirty_entries_from_runtime_delta_transform(
    *,
    runtime_delta_transform: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    current_index = _mapping_value(
        runtime_delta_transform.get("current_runtime_semantic_object_index")
    )
    entries: list[dict[str, object]] = []
    for position, semantic_key in enumerate(sorted(current_index)):
        current_entry = _mapping_value(current_index.get(semantic_key))
        subject_kind = _optional_text(
            current_entry.get("ontology_subject_kind")
            or current_entry.get("object_kind")
            or current_entry.get("kind")
        )
        entries.append(
            {
                "entry_kind": "meta_ocg_semantic_dirty_entry",
                "entry_key": f"dirty:runtime_delta:{position}:{semantic_key}",
                "semantic_key": semantic_key,
                "source_delta_key": _optional_text(
                    current_entry.get("source_delta_key")
                ),
                "source": "aware_meta.materialization.runtime_delta",
                "source_refs": _tuple_text(current_entry.get("source_refs")),
                "verb": _optional_text(current_entry.get("verb")) or "upsert",
                "semantic_subject_type": _optional_text(
                    current_entry.get("semantic_subject_type")
                ),
                "ontology_subject_kind": subject_kind or "unknown",
                "dirty_operation": f"{subject_kind or 'unknown'}_upsert",
                "node_type": _optional_text(current_entry.get("node_type")),
                "node_key": _optional_text(current_entry.get("node_key")),
                "entity_id": _optional_text(
                    current_entry.get("entity_id") or current_entry.get("object_id")
                ),
                "entity_name": _optional_text(current_entry.get("entity_name")),
                "graph_semantic_key": _optional_text(
                    current_entry.get("graph_semantic_key")
                ),
                "parent_semantic_key": _optional_text(
                    current_entry.get("parent_semantic_key")
                    or current_entry.get("owner_semantic_key")
                ),
                "owner_semantic_key": _optional_text(
                    current_entry.get("owner_semantic_key")
                    or current_entry.get("parent_semantic_key")
                ),
                "owner_object_id": _optional_text(
                    current_entry.get("owner_object_id")
                ),
                "attribute_name": _optional_text(
                    current_entry.get("attribute_name")
                ),
                "class_config_attribute_config_id": _optional_text(
                    current_entry.get("class_config_attribute_config_id")
                ),
                "function_config_attribute_config_id": _optional_text(
                    current_entry.get("function_config_attribute_config_id")
                ),
                "attribute_config_id": _optional_text(
                    current_entry.get("attribute_config_id")
                ),
                "attribute_membership_semantic_key": _optional_text(
                    current_entry.get("attribute_membership_semantic_key")
                ),
                "attribute_membership_owner_kind": _optional_text(
                    current_entry.get("attribute_membership_owner_kind")
                ),
                "attribute_membership_signature": _mapping_value(
                    current_entry.get("attribute_membership_signature")
                ),
                "function_attribute_type": _optional_text(
                    current_entry.get("function_attribute_type")
                ),
                "attribute_signature": _mapping_value(
                    current_entry.get("attribute_signature")
                ),
                "function_name": _optional_text(current_entry.get("function_name")),
                "class_config_id": _optional_text(
                    current_entry.get("class_config_id")
                ),
                "class_config_function_config_id": _optional_text(
                    current_entry.get("class_config_function_config_id")
                ),
                "function_config_id": _optional_text(
                    current_entry.get("function_config_id")
                ),
                "function_membership_semantic_key": _optional_text(
                    current_entry.get("function_membership_semantic_key")
                ),
                "function_membership_signature": _mapping_value(
                    current_entry.get("function_membership_signature")
                ),
                "function_signature": _mapping_value(
                    current_entry.get("function_signature")
                ),
                "function_semantic_key": _optional_text(
                    current_entry.get("function_semantic_key")
                ),
                "function_impl_key": _optional_text(
                    current_entry.get("function_impl_key")
                ),
                "function_impl_kind": _optional_text(
                    current_entry.get("function_impl_kind")
                ),
                "function_impl_signature": _mapping_value(
                    current_entry.get("function_impl_signature")
                ),
                "relationship_key": _optional_text(
                    current_entry.get("relationship_key")
                ),
                "relationship_type": _optional_text(
                    current_entry.get("relationship_type")
                ),
                "relationship_signature": _mapping_value(
                    current_entry.get("relationship_signature")
                ),
                "semantic_fingerprint": _optional_text(
                    current_entry.get("semantic_fingerprint")
                ),
                "payload": current_entry,
                "baseline_compare_status": "runtime_delta_current_object_index",
                "would_execute": False,
                "would_persist": False,
            }
        )
    return tuple(entries)


def _semantic_dirty_diff_blocked_reason(*, hydration_status: str) -> str:
    return {
        "baseline_context_missing": (
            "meta_ocg_dirty_diff_requires_commit_backed_baseline"
        ),
        "baseline_ref_missing": "meta_ocg_dirty_diff_requires_workspace_baseline_ref",
        "baseline_ref_incomplete": (
            "meta_ocg_dirty_diff_requires_complete_workspace_baseline_ref"
        ),
        "baseline_hydrator_unavailable": (
            "meta_ocg_dirty_diff_requires_baseline_hydrator_context"
        ),
        "baseline_projection_unresolved": (
            "meta_ocg_dirty_diff_requires_resolvable_baseline_projection"
        ),
        "baseline_runtime_index_missing": (
            "meta_ocg_dirty_diff_requires_baseline_hydrator_runtime_index"
        ),
        "baseline_oig_payload_ref_missing": (
            "meta_ocg_dirty_diff_requires_workspace_oig_payload_ref_or_local_commit"
        ),
        "baseline_oig_payload_import_failed": (
            "meta_ocg_dirty_diff_baseline_oig_payload_import_failed"
        ),
        "baseline_oig_commit_missing": (
            "meta_ocg_dirty_diff_requires_local_baseline_oig_commit"
        ),
        "baseline_oig_lane_head_missing": (
            "meta_ocg_dirty_diff_requires_local_baseline_oig_lane_head"
        ),
        "baseline_hydration_failed": "meta_ocg_dirty_diff_baseline_hydration_failed",
        "baseline_ref_invalid": (
            "meta_ocg_dirty_diff_requires_valid_workspace_baseline_ref"
        ),
    }.get(hydration_status, "meta_ocg_dirty_diff_requires_hydrated_baseline")


def _semantic_dirty_entries_with_baseline_index(
    *,
    dirty_entries: tuple[dict[str, object], ...],
    baseline_semantic_object_index: Mapping[str, object],
    baseline_commit_id: str | None,
    runtime_delta_transform: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    if not baseline_semantic_object_index:
        return tuple(
            _semantic_dirty_entry_without_baseline_index(entry=entry)
            for entry in dirty_entries
        )
    compared_entries: list[dict[str, object]] = []
    current_semantic_keys: set[str] = set()
    for entry in dirty_entries:
        semantic_key = _optional_text(entry.get("semantic_key"))
        if semantic_key is not None:
            current_semantic_keys.add(semantic_key)
        baseline_entry = _mapping_value(
            baseline_semantic_object_index.get(semantic_key or "")
        )
        compared_entries.append(
            _semantic_dirty_entry_with_baseline_match(
                entry=entry,
                semantic_key=semantic_key,
                baseline_entry=baseline_entry,
                baseline_commit_id=baseline_commit_id,
            )
        )
    compared_entries.extend(
        _stale_semantic_dirty_entries_from_baseline_index(
            baseline_semantic_object_index=baseline_semantic_object_index,
            baseline_commit_id=baseline_commit_id,
            current_semantic_keys=current_semantic_keys,
            runtime_delta_transform=runtime_delta_transform,
            start_position=len(compared_entries),
        )
    )
    return tuple(compared_entries)


def _semantic_dirty_entries_with_relationship_support_normalization(
    *,
    dirty_entries: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    relationship_support_index = relationship_update_support_attribute_index(
        dirty_entries=dirty_entries,
    )
    if not relationship_support_index:
        return dirty_entries
    normalized: list[dict[str, object]] = []
    for entry in dirty_entries:
        semantic_key = _optional_text(entry.get("semantic_key"))
        relationship_semantic_key = relationship_support_index.get(
            semantic_key or "",
        )
        if relationship_semantic_key is not None and (
            relationship_support_attribute_delta_only(entry=entry)
        ):
            normalized.append(
                relationship_deferred_attribute_dirty_entry(
                    entry=entry,
                    relationship_semantic_key=relationship_semantic_key,
                )
            )
            continue
        normalized.append(entry)
    return tuple(normalized)


def _stale_semantic_dirty_entries_from_baseline_index(
    *,
    baseline_semantic_object_index: Mapping[str, object],
    baseline_commit_id: str | None,
    current_semantic_keys: set[str],
    runtime_delta_transform: Mapping[str, object],
    start_position: int,
) -> tuple[dict[str, object], ...]:
    changed_source_refs = set(
        _tuple_text(runtime_delta_transform.get("changed_runtime_source_refs"))
    )
    if not changed_source_refs:
        return ()
    stale_entries: list[dict[str, object]] = []
    for semantic_key in sorted(baseline_semantic_object_index):
        if semantic_key in current_semantic_keys:
            continue
        baseline_entry = _mapping_value(
            baseline_semantic_object_index.get(semantic_key)
        )
        baseline_source_refs = _tuple_text(baseline_entry.get("source_refs"))
        if not _baseline_source_refs_are_precise_for_delta_scope(
            baseline_source_refs=baseline_source_refs,
            changed_source_refs=changed_source_refs,
        ):
            continue
        subject_kind = _baseline_entry_subject_kind(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        )
        if subject_kind not in {
            "attribute",
            "class",
            "function",
            "function_impl",
            "relationship",
        }:
            continue
        stale_entries.append(
            _semantic_dirty_stale_entry_from_baseline(
                semantic_key=semantic_key,
                baseline_entry=baseline_entry,
                baseline_commit_id=baseline_commit_id,
                subject_kind=subject_kind,
                source_refs=baseline_source_refs,
                position=start_position + len(stale_entries),
            )
        )
    return tuple(stale_entries)


def _baseline_source_refs_are_precise_for_delta_scope(
    *,
    baseline_source_refs: tuple[str, ...],
    changed_source_refs: set[str],
) -> bool:
    if not baseline_source_refs:
        return False
    baseline_ref_set = set(baseline_source_refs)
    if not baseline_ref_set.intersection(changed_source_refs):
        return False
    return baseline_ref_set.issubset(changed_source_refs)


def _semantic_dirty_stale_entry_from_baseline(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
    baseline_commit_id: str | None,
    subject_kind: str,
    source_refs: tuple[str, ...],
    position: int,
) -> dict[str, object]:
    baseline_object_id = _optional_text(
        baseline_entry.get("object_id")
        or baseline_entry.get("semantic_object_id")
        or baseline_entry.get("id")
    )
    baseline_object_kind = _optional_text(
        baseline_entry.get("object_kind")
        or baseline_entry.get("semantic_object_kind")
        or baseline_entry.get("kind")
    )
    payload = {
        "semantic_key": semantic_key,
        "object_kind": subject_kind,
        "ontology_subject_kind": subject_kind,
        "semantic_subject_type": _semantic_subject_type_for_kind(
            subject_kind=subject_kind,
        ),
        "verb": "delete",
        "source_refs": source_refs,
        "graph_semantic_key": _semantic_key_graph_semantic_key(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "node_key": _semantic_key_node_key(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "attribute_name": _semantic_key_attribute_name(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "function_name": _semantic_key_function_name(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "function_semantic_key": _semantic_key_function_semantic_key(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "function_impl_key": _semantic_key_function_impl_key(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "relationship_key": _semantic_key_relationship_key(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "parent_semantic_key": _semantic_key_parent_semantic_key(
            semantic_key=semantic_key,
            baseline_entry=baseline_entry,
        ),
        "baseline_object_id": baseline_object_id,
    }
    payload = {key: value for key, value in payload.items() if value is not None}
    return {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:runtime_delta_stale:{position}:{semantic_key}",
        "semantic_key": semantic_key,
        "source_delta_key": f"aware_meta.runtime_delta.stale:{semantic_key}",
        "source": "aware_meta.materialization.runtime_delta.baseline_stale",
        "source_refs": source_refs,
        "verb": "delete",
        "semantic_subject_type": _semantic_subject_type_for_kind(
            subject_kind=subject_kind,
        ),
        "ontology_subject_kind": subject_kind,
        "dirty_operation": f"{subject_kind}_delete",
        "node_type": (
            subject_kind if subject_kind != "attribute" else None
        ),
        "node_key": payload.get("node_key"),
        "entity_id": baseline_object_id,
        "entity_name": (
            payload.get("attribute_name")
            if subject_kind == "attribute"
            else payload.get("function_name")
            if subject_kind == "function"
            else payload.get("function_impl_key")
            if subject_kind == "function_impl"
            else payload.get("relationship_key")
            if subject_kind == "relationship"
            else payload.get("node_key")
        ),
        "graph_semantic_key": payload.get("graph_semantic_key"),
        "parent_semantic_key": payload.get("parent_semantic_key"),
        "owner_semantic_key": payload.get("parent_semantic_key"),
        "attribute_name": payload.get("attribute_name"),
        "class_config_attribute_config_id": _optional_text(
            baseline_entry.get("class_config_attribute_config_id")
        ),
        "function_config_attribute_config_id": _optional_text(
            baseline_entry.get("function_config_attribute_config_id")
        ),
        "attribute_config_id": _optional_text(
            baseline_entry.get("attribute_config_id")
        ),
        "attribute_membership_semantic_key": _optional_text(
            baseline_entry.get("attribute_membership_semantic_key")
        ),
        "attribute_membership_owner_kind": _optional_text(
            baseline_entry.get("attribute_membership_owner_kind")
        ),
        "attribute_membership_signature": _mapping_value(
            baseline_entry.get("attribute_membership_signature")
        ),
        "function_attribute_type": _optional_text(
            baseline_entry.get("function_attribute_type")
        ),
        "attribute_signature": _mapping_value(
            baseline_entry.get("attribute_signature")
        ),
        "function_name": payload.get("function_name"),
        "class_config_id": _optional_text(baseline_entry.get("class_config_id")),
        "class_config_function_config_id": _optional_text(
            baseline_entry.get("class_config_function_config_id")
        ),
        "function_config_id": _optional_text(
            baseline_entry.get("function_config_id")
        ),
        "function_membership_semantic_key": _optional_text(
            baseline_entry.get("function_membership_semantic_key")
        ),
        "function_membership_signature": _mapping_value(
            baseline_entry.get("function_membership_signature")
        ),
        "function_signature": _mapping_value(
            baseline_entry.get("function_signature")
        ),
        "function_semantic_key": payload.get("function_semantic_key"),
        "function_impl_key": payload.get("function_impl_key"),
        "function_impl_kind": _optional_text(baseline_entry.get("function_impl_kind")),
        "function_impl_signature": _mapping_value(
            baseline_entry.get("function_impl_signature")
        ),
        "relationship_key": payload.get("relationship_key"),
        "relationship_signature": _mapping_value(
            baseline_entry.get("relationship_signature")
        ),
        "semantic_fingerprint": _optional_text(
            baseline_entry.get("semantic_fingerprint")
            or baseline_entry.get("runtime_delta_fingerprint")
        ),
        "payload": payload,
        "baseline_compare_status": "baseline_object_stale",
        "baseline_compare_operation": "delete",
        "baseline_object_matched": bool(baseline_object_id),
        "baseline_object_id": baseline_object_id,
        "baseline_object_kind": baseline_object_kind or subject_kind,
        "baseline_object_instance_graph_commit_id": _optional_text(
            baseline_entry.get("object_instance_graph_commit_id")
        )
        or baseline_commit_id,
        "baseline_object": dict(baseline_entry),
        "would_execute": False,
        "would_persist": False,
    }


def _baseline_entry_subject_kind(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str:
    object_kind = _optional_text(
        baseline_entry.get("object_kind")
        or baseline_entry.get("semantic_object_kind")
        or baseline_entry.get("ontology_subject_kind")
        or baseline_entry.get("kind")
    )
    if object_kind is not None:
        return object_kind
    if "/function_impl:" in semantic_key:
        return "function_impl"
    if "/attribute:" in semantic_key:
        return "attribute"
    node_type = _optional_text(baseline_entry.get("node_type"))
    if node_type is not None:
        return node_type
    return "unknown"


def _semantic_subject_type_for_kind(*, subject_kind: str) -> str:
    if subject_kind == "attribute":
        return "aware_meta.AttributeConfig"
    if subject_kind == "attribute_membership":
        return "aware_meta.AttributeMembership"
    if subject_kind == "function_impl":
        return "aware_meta.FunctionImpl"
    if subject_kind == "object_config_graph":
        return "aware_meta.ObjectConfigGraph"
    if subject_kind == "object_config_graph_package":
        return "aware_meta.ObjectConfigGraphPackage"
    return "aware_meta.ObjectConfigGraphNode"


def _semantic_key_graph_semantic_key(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    graph_semantic_key = _optional_text(baseline_entry.get("graph_semantic_key"))
    if graph_semantic_key is not None:
        return graph_semantic_key
    marker = "/node:"
    if marker not in semantic_key:
        return semantic_key if semantic_key.startswith("ocg:") else None
    return semantic_key.split(marker, 1)[0]


def _semantic_key_node_key(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    node_key = _optional_text(baseline_entry.get("node_key"))
    if node_key is not None:
        return node_key
    marker = "/node:"
    if marker not in semantic_key:
        return None
    tail = semantic_key.split(marker, 1)[1]
    tail = tail.split("/function_impl:", 1)[0]
    return tail.split("/attribute:", 1)[0]


def _semantic_key_attribute_name(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    attribute_name = _optional_text(baseline_entry.get("attribute_name"))
    if attribute_name is not None:
        return attribute_name
    marker = "/attribute:"
    if marker not in semantic_key:
        return None
    return semantic_key.rsplit(marker, 1)[1]


def _semantic_key_function_name(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    function_name = _optional_text(
        baseline_entry.get("function_name")
        or baseline_entry.get("entity_name")
    )
    if function_name is not None:
        return function_name
    marker = "/node:"
    if marker not in semantic_key:
        return None
    node_key = semantic_key.split(marker, 1)[1]
    node_key = node_key.split("/function_impl:", 1)[0]
    if ":" in node_key or "." not in node_key:
        return None
    return node_key.rsplit(".", 1)[1]


def _semantic_key_function_semantic_key(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    function_semantic_key = _optional_text(
        baseline_entry.get("function_semantic_key")
    )
    if function_semantic_key is not None:
        return function_semantic_key
    marker = "/function_impl:"
    if marker not in semantic_key:
        return None
    return semantic_key.split(marker, 1)[0]


def _semantic_key_function_impl_key(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    function_impl_key = _optional_text(baseline_entry.get("function_impl_key"))
    if function_impl_key is not None:
        return function_impl_key
    marker = "/function_impl:"
    if marker not in semantic_key:
        return None
    return semantic_key.split(marker, 1)[1] or None


def _semantic_key_relationship_key(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    relationship_key = _optional_text(
        baseline_entry.get("relationship_key")
        or baseline_entry.get("entity_name")
    )
    if relationship_key is not None:
        return relationship_key
    marker = "/node:"
    if marker not in semantic_key:
        return None
    node_key = semantic_key.split(marker, 1)[1]
    parts = node_key.split(":")
    if len(parts) >= 2:
        return parts[1]
    return None


def _semantic_key_parent_semantic_key(
    *,
    semantic_key: str,
    baseline_entry: Mapping[str, object],
) -> str | None:
    parent_semantic_key = _optional_text(
        baseline_entry.get("parent_semantic_key")
        or baseline_entry.get("owner_semantic_key")
    )
    if parent_semantic_key is not None:
        return parent_semantic_key
    marker = "/function_impl:"
    if marker in semantic_key:
        return semantic_key.split(marker, 1)[0]
    marker = "/attribute:"
    if marker not in semantic_key:
        return None
    return semantic_key.rsplit(marker, 1)[0]


def _semantic_dirty_entry_without_baseline_index(
    *,
    entry: Mapping[str, object],
) -> dict[str, object]:
    updated = dict(entry)
    updated.update(
        {
            "baseline_compare_status": "baseline_semantic_object_index_unavailable",
            "baseline_compare_operation": "blocked",
            "baseline_object_matched": False,
            "baseline_object_id": None,
            "baseline_object_kind": None,
            "baseline_object_instance_graph_commit_id": None,
            "baseline_object": None,
        }
    )
    return updated


def _semantic_dirty_entry_with_baseline_match(
    *,
    entry: Mapping[str, object],
    semantic_key: str | None,
    baseline_entry: Mapping[str, object],
    baseline_commit_id: str | None,
) -> dict[str, object]:
    updated = dict(entry)
    subject_kind = _string_value(updated.get("ontology_subject_kind"))
    baseline_object_id = _optional_text(
        baseline_entry.get("object_id")
        or baseline_entry.get("semantic_object_id")
        or baseline_entry.get("id")
    )
    baseline_object_kind = _optional_text(
        baseline_entry.get("object_kind")
        or baseline_entry.get("semantic_object_kind")
        or baseline_entry.get("kind")
    )
    matched = bool(semantic_key and baseline_entry and baseline_object_id)
    current_payload = _mapping_value(updated.get("payload"))
    current_fingerprint = _optional_text(
        updated.get("semantic_fingerprint")
        or current_payload.get("semantic_fingerprint")
    )
    baseline_fingerprint = _optional_text(
        baseline_entry.get("semantic_fingerprint")
        or baseline_entry.get("runtime_delta_fingerprint")
    )
    unchanged = bool(
        matched
        and current_fingerprint is not None
        and baseline_fingerprint == current_fingerprint
    ) or _semantic_signature_unchanged(
        subject_kind=subject_kind,
        entry=updated,
        baseline_entry=baseline_entry,
    )
    if unchanged:
        compare_operation = "noop"
    elif matched:
        compare_operation = "update"
    else:
        compare_operation = "create"
    if semantic_key is None:
        compare_status = "semantic_key_missing"
    elif unchanged:
        compare_status = "baseline_object_unchanged"
    elif matched:
        compare_status = "baseline_object_matched"
    else:
        compare_status = "baseline_object_missing"
    updated.update(
        {
            "dirty_operation": f"{subject_kind}_{compare_operation}",
            "baseline_compare_status": compare_status,
            "baseline_compare_operation": compare_operation,
            "baseline_object_matched": matched,
            "baseline_object_id": baseline_object_id,
            "baseline_object_kind": baseline_object_kind,
            "baseline_object_instance_graph_commit_id": _optional_text(
                baseline_entry.get("object_instance_graph_commit_id")
            )
            or baseline_commit_id,
            "baseline_object": dict(baseline_entry) if baseline_entry else None,
        }
    )
    return updated


def _semantic_signature_unchanged(
    *,
    subject_kind: str,
    entry: Mapping[str, object],
    baseline_entry: Mapping[str, object],
) -> bool:
    if subject_kind != "function_impl":
        return False
    current_payload = _mapping_value(entry.get("payload"))
    baseline_payload = _mapping_value(baseline_entry.get("payload"))
    current_signature = _mapping_value(
        entry.get("function_impl_signature")
        or current_payload.get("function_impl_signature")
    )
    baseline_signature = _mapping_value(
        baseline_entry.get("function_impl_signature")
        or baseline_payload.get("function_impl_signature")
    )
    if not current_signature and not baseline_signature:
        return False
    return _normalized_signature_value(current_signature) == (
        _normalized_signature_value(baseline_signature)
    )


def _normalized_signature_value(value: object) -> object:
    if isinstance(value, Mapping):
        return tuple(
            (str(key), _normalized_signature_value(item))
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, (list, tuple)):
        return tuple(_normalized_signature_value(item) for item in value)
    return value


def _dirty_entry_kind_counts(
    *,
    dirty_entries: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in dirty_entries:
        kind = _string_value(entry.get("ontology_subject_kind"))
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def _dirty_operation_counts(
    *,
    dirty_entries: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in dirty_entries:
        operation = _string_value(entry.get("dirty_operation"))
        counts[operation] = counts.get(operation, 0) + 1
    return dict(sorted(counts.items()))


def _baseline_compare_operation_counts(
    *,
    dirty_entries: tuple[Mapping[str, object], ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in dirty_entries:
        operation = _string_value(entry.get("baseline_compare_operation"))
        counts[operation] = counts.get(operation, 0) + 1
    return dict(sorted(counts.items()))


def _semantic_dirty_entries_stale_semantic_keys(
    *,
    dirty_entries: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    keys: list[str] = []
    for entry in dirty_entries:
        if _optional_text(entry.get("baseline_compare_operation")) != "delete":
            continue
        semantic_key = _optional_text(entry.get("semantic_key"))
        if semantic_key is not None:
            keys.append(semantic_key)
    return tuple(sorted(dict.fromkeys(keys)))


def _semantic_dirty_diff_stale_semantic_keys(
    *,
    semantic_dirty_diff: Mapping[str, object],
) -> tuple[str, ...]:
    return tuple(
        key
        for key in _tuple_text(semantic_dirty_diff.get("stale_semantic_keys"))
        if key
    )


def _baseline_dirty_preflight_with_semantic_dirty_diff(
    *,
    baseline_dirty_preflight: Mapping[str, object],
    semantic_dirty_diff: Mapping[str, object],
) -> dict[str, object]:
    updated = dict(baseline_dirty_preflight)
    if semantic_dirty_diff.get("available") is True:
        updated.update(
            {
                "semantic_dirty_diff_available": True,
                "semantic_dirty_diff_status": semantic_dirty_diff["status"],
                "semantic_dirty_diff_reason": semantic_dirty_diff["reason"],
                "semantic_dirty_entry_count": (
                    semantic_dirty_diff["dirty_entry_count"]
                ),
                "did_compare_against_current_delta": True,
                "baseline_index_compare_available": semantic_dirty_diff[
                    "baseline_index_compare_available"
                ],
                "baseline_index_compare_status": semantic_dirty_diff[
                    "baseline_index_compare_status"
                ],
                "baseline_index_compare_reason": semantic_dirty_diff[
                    "baseline_index_compare_reason"
                ],
                "baseline_semantic_object_index_count": semantic_dirty_diff[
                    "baseline_semantic_object_index_count"
                ],
            }
        )
    else:
        updated.update(
            {
                "semantic_dirty_diff_available": False,
                "semantic_dirty_diff_status": semantic_dirty_diff["status"],
                "semantic_dirty_diff_reason": semantic_dirty_diff["reason"],
                "semantic_dirty_entry_count": 0,
                "did_compare_against_current_delta": False,
                "baseline_index_compare_available": False,
                "baseline_index_compare_status": semantic_dirty_diff[
                    "baseline_index_compare_status"
                ],
                "baseline_index_compare_reason": semantic_dirty_diff[
                    "baseline_index_compare_reason"
                ],
                "baseline_semantic_object_index_count": semantic_dirty_diff[
                    "baseline_semantic_object_index_count"
                ],
            }
        )
    return updated


def _mapping_value(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_value(value: object) -> str:
    text = _optional_text(value)
    return text if text is not None else ""


def _tuple_text(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values: list[str] = []
        for item in value:
            text = _optional_text(item)
            if text is not None:
                values.append(text)
        return tuple(values)
    text = _optional_text(value)
    return (text,) if text is not None else ()


__all__ = [
    "_baseline_dirty_preflight_with_semantic_dirty_diff",
    "_semantic_dirty_diff_from_analysis",
    "_semantic_dirty_diff_stale_semantic_keys",
]
