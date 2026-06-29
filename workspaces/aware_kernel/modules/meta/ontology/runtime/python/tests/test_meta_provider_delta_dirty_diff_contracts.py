from __future__ import annotations

from types import SimpleNamespace

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION,
    MetaProviderDeltaDirtyEntry,
    MetaProviderDeltaSemanticDirtyDiff,
)
from aware_meta.materialization.deltas.pipeline import (
    MetaProviderDeltaPipelineContext,
)


def test_dirty_diff_contract_normalizes_ready_diff_entries() -> None:
    dirty_diff = MetaProviderDeltaSemanticDirtyDiff.from_payload(_ready_dirty_diff())

    assert dirty_diff.ready is True
    assert dirty_diff.available is True
    assert dirty_diff.status == "semantic_dirty_diff_ready"
    assert dirty_diff.dirty_entry_count == 4
    assert len(dirty_diff.dirty_entries) == 4
    assert dirty_diff.baseline_index_compare_status == "baseline_index_compared"
    assert dirty_diff.baseline_compare_operation_counts == {
        "create": 1,
        "delete": 1,
        "noop": 1,
        "update": 1,
    }
    assert dirty_diff.dirty_operation_counts == {
        "attribute_delete": 1,
        "attribute_update": 1,
        "class_create": 1,
        "class_noop": 1,
    }
    assert dirty_diff.stale_semantic_keys == ("home.Device/attribute:old_name",)

    create_entry = dirty_diff.entries_for_operation("create")[0]
    assert create_entry.semantic_key == "home.NewDevice"
    assert create_entry.operation_kind == "create"
    assert create_entry.ontology_subject_kind == "class"
    assert create_entry.source_refs == ("aware/home/device.aware",)
    assert create_entry.baseline == {}
    assert create_entry.current["node_key"] == "home.NewDevice"

    update_entry = dirty_diff.entries_for_operation("update")[0]
    assert update_entry.baseline_object_matched is True
    assert update_entry.baseline_object_id == "attr-1"
    assert update_entry.baseline["semantic_fingerprint"] == "sha256:old"
    assert update_entry.current["semantic_fingerprint"] == "sha256:new"

    delete_entry = dirty_diff.entries_for_operation("delete")[0]
    assert delete_entry.semantic_key == "home.Device/attribute:old_name"
    assert delete_entry.baseline_object_kind == "attribute"
    assert delete_entry.current["attribute_name"] == "old_name"

    assert dirty_diff.evidence_payload()["contract_version"] == (
        META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION
    )


def test_dirty_entry_contract_preserves_blocked_compare_state() -> None:
    entry = MetaProviderDeltaDirtyEntry.from_payload(
        {
            "entry_key": "dirty:blocked:1",
            "semantic_key": "home.Device/attribute:name",
            "source_refs": ("aware/home/device.aware",),
            "ontology_subject_kind": "attribute",
            "dirty_operation": "attribute_blocked",
            "baseline_compare_status": ("baseline_semantic_object_index_unavailable"),
            "baseline_compare_operation": "blocked",
            "baseline_compare_reason": (
                "meta_ocg_dirty_diff_requires_baseline_semantic_object_index"
            ),
            "payload": {"attribute_name": "name"},
        }
    )

    assert entry is not None
    assert entry.blocked is True
    assert entry.operation_kind == "blocked"
    assert entry.blocker_reason == (
        "meta_ocg_dirty_diff_requires_baseline_semantic_object_index"
    )
    assert entry.current == {"attribute_name": "name"}


def test_dirty_diff_contract_normalizes_blocked_diff() -> None:
    dirty_diff = MetaProviderDeltaSemanticDirtyDiff.from_payload(
        {
            "diff_kind": "meta_ocg_semantic_dirty_diff",
            "contract_version": (
                META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION
            ),
            "status": "semantic_dirty_diff_blocked",
            "reason": "meta_ocg_dirty_diff_requires_hydrated_baseline",
            "available": False,
            "blocked": True,
            "blocked_status": "baseline_context_missing",
            "blocked_reason": ("meta_ocg_dirty_diff_requires_commit_backed_baseline"),
            "baseline_index_compare_available": False,
            "baseline_index_compare_status": "requires_hydrated_baseline",
            "dirty_entry_count": 0,
            "semantic_dirty_entries": (),
        }
    )

    assert dirty_diff.ready is False
    assert dirty_diff.blocked is True
    assert dirty_diff.blocked_status == "baseline_context_missing"
    assert dirty_diff.blocked_reason == (
        "meta_ocg_dirty_diff_requires_commit_backed_baseline"
    )
    assert dirty_diff.baseline_index_compare_status == "requires_hydrated_baseline"
    assert dirty_diff.dirty_entries == ()


def test_pipeline_context_exposes_typed_dirty_diff_summary() -> None:
    context = _context().with_semantic_dirty_diff(_ready_dirty_diff())
    summary = context.evidence_summary()

    assert context.dirty_diff.ready is True
    assert context.dirty_diff.stale_semantic_key_count == 1
    assert summary["semantic_dirty_diff_status"] == "semantic_dirty_diff_ready"
    assert summary["semantic_dirty_diff_ready"] is True
    assert summary["semantic_dirty_entry_count"] == 4
    assert summary["semantic_dirty_diff_baseline_index_compare_status"] == (
        "baseline_index_compared"
    )
    assert summary["semantic_dirty_diff_baseline_compare_operation_counts"] == {
        "create": 1,
        "delete": 1,
        "noop": 1,
        "update": 1,
    }
    assert summary["semantic_dirty_diff_stale_semantic_key_count"] == 1


def _context() -> MetaProviderDeltaPipelineContext:
    return MetaProviderDeltaPipelineContext.create(
        request=SimpleNamespace(),
        package_payload={"package_name": "home-ontology"},
        semantic_contract_payload={"provider_key": "aware_meta"},
        manifest_path="modules/home/structure/ontology/aware.toml",
        current_delta_fingerprint="sha256:current",
        provider_delta_execution_context_preflight={
            "status": "execution_context_available",
        },
        baseline_dirty_preflight={"status": "baseline_dirty_preflight_ready"},
    )


def _ready_dirty_diff() -> dict[str, object]:
    return {
        "diff_kind": "meta_ocg_semantic_dirty_diff",
        "contract_version": (META_PROVIDER_DELTA_SEMANTIC_DIRTY_DIFF_CONTRACT_VERSION),
        "status": "semantic_dirty_diff_ready",
        "reason": "meta_ocg_dirty_diff_ready",
        "available": True,
        "blocked": False,
        "baseline_index_compare_available": True,
        "baseline_index_compare_status": "baseline_index_compared",
        "baseline_index_compare_reason": (
            "meta_ocg_dirty_diff_compared_against_baseline_semantic_object_index"
        ),
        "current_delta_fingerprint": "sha256:current",
        "semantic_delta_count": 4,
        "dirty_entry_count": 4,
        "dirty_entry_kind_counts": {"attribute": 2, "class": 2},
        "dirty_operation_counts": {
            "attribute_delete": 1,
            "attribute_update": 1,
            "class_create": 1,
            "class_noop": 1,
        },
        "baseline_compare_operation_counts": {
            "create": 1,
            "delete": 1,
            "noop": 1,
            "update": 1,
        },
        "stale_semantic_key_count": 1,
        "stale_semantic_keys": ("home.Device/attribute:old_name",),
        "semantic_dirty_entries": (
            _dirty_entry(
                semantic_key="home.NewDevice",
                subject_kind="class",
                dirty_operation="class_create",
                compare_operation="create",
                payload={"node_key": "home.NewDevice"},
            ),
            _dirty_entry(
                semantic_key="home.Device/attribute:name",
                subject_kind="attribute",
                dirty_operation="attribute_update",
                compare_operation="update",
                baseline_object={
                    "object_id": "attr-1",
                    "object_kind": "attribute",
                    "semantic_fingerprint": "sha256:old",
                },
                payload={
                    "attribute_name": "name",
                    "semantic_fingerprint": "sha256:new",
                },
            ),
            _dirty_entry(
                semantic_key="home.Device/attribute:stable",
                subject_kind="class",
                dirty_operation="class_noop",
                compare_operation="noop",
                baseline_object={
                    "object_id": "class-1",
                    "object_kind": "class",
                    "semantic_fingerprint": "sha256:stable",
                },
                payload={
                    "node_key": "home.Device",
                    "semantic_fingerprint": "sha256:stable",
                },
            ),
            _dirty_entry(
                semantic_key="home.Device/attribute:old_name",
                subject_kind="attribute",
                dirty_operation="attribute_delete",
                compare_operation="delete",
                baseline_object={
                    "object_id": "attr-old",
                    "object_kind": "attribute",
                    "semantic_fingerprint": "sha256:old-name",
                },
                payload={"attribute_name": "old_name"},
            ),
        ),
    }


def _dirty_entry(
    *,
    semantic_key: str,
    subject_kind: str,
    dirty_operation: str,
    compare_operation: str,
    payload: dict[str, object],
    baseline_object: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "entry_kind": "meta_ocg_semantic_dirty_entry",
        "entry_key": f"dirty:{semantic_key}",
        "semantic_key": semantic_key,
        "source_delta_key": f"delta:{semantic_key}",
        "source_refs": ("aware/home/device.aware",),
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": subject_kind,
        "dirty_operation": dirty_operation,
        "baseline_compare_operation": compare_operation,
        "baseline_compare_status": f"baseline_object_{compare_operation}",
        "baseline_object_matched": baseline_object is not None,
        "baseline_object_id": (
            str(baseline_object["object_id"]) if baseline_object is not None else None
        ),
        "baseline_object_kind": (
            str(baseline_object["object_kind"]) if baseline_object is not None else None
        ),
        "baseline_object": baseline_object,
        "payload": payload,
        "would_execute": False,
        "would_persist": False,
    }
