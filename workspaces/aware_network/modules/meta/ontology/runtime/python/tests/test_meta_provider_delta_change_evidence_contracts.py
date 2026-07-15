from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_COMMITTED_SEMANTIC_CHANGE_CONTRACT_VERSION,
    META_PROVIDER_DELTA_READABLE_SEMANTIC_CHANGE_CHAIN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_CHANGE_REPORT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_COMMIT_EVIDENCE_CONTRACT_VERSION,
    META_PROVIDER_DELTA_SEMANTIC_WORLD_CHANGE_CONTRACT_VERSION,
    MetaProviderDeltaSemanticChangeReport,
    MetaProviderDeltaSemanticCommitEvidence,
)
from aware_meta.materialization.deltas.change_evidence import (
    _provider_delta_semantic_change_report,
    _provider_delta_semantic_commit_evidence,
)
from aware_meta.materialization.deltas.pipeline import (
    MetaProviderDeltaPipelineContext,
)


def test_semantic_change_report_contract_normalizes_ready_report() -> None:
    report = MetaProviderDeltaSemanticChangeReport.from_payload(
        _provider_delta_semantic_change_report(
            semantic_dirty_diff={
                "status": "semantic_dirty_diff_ready",
                "reason": "ready",
                "dirty_entry_count": 1,
            },
            provider_delta_typed_operation_plan=_typed_operation_plan(),
        )
    )

    assert report.ready is True
    assert report.status == "semantic_change_report_ready"
    assert report.semantic_dirty_entry_count == 1
    assert report.typed_operation_count == 1
    assert report.semantic_world_change_count == 1
    assert report.readable_line_count == 1
    assert report.readable_markdown == (
        "1. Update attribute `name` on `Device`. "
        "Type changes from `Int` to `String`."
    )
    assert report.change_key_counts == {
        "aware_meta.provider_delta.world_change.attribute.update": 1,
    }
    assert report.operation_family_counts == {"update": 1}
    assert report.readable_semantic_change_chain.contract_version == (
        META_PROVIDER_DELTA_READABLE_SEMANTIC_CHANGE_CHAIN_CONTRACT_VERSION
    )

    change = report.semantic_world_changes[0]
    assert change.contract_version == (
        META_PROVIDER_DELTA_SEMANTIC_WORLD_CHANGE_CONTRACT_VERSION
    )
    assert change.change_key == (
        "aware_meta.provider_delta.world_change.attribute.update"
    )
    assert change.semantic_key == ("graph:home.Home/node:home.Device/attribute:name")
    assert change.ontology_subject_kind == "attribute"
    assert change.delta_keys == ("delta:attribute:name",)
    assert change.condition_keys[-1] == ("meta.provider_delta.subject_kind.attribute")

    evidence = report.evidence_payload()
    assert evidence["contract_version"] == (
        META_PROVIDER_DELTA_SEMANTIC_CHANGE_REPORT_CONTRACT_VERSION
    )
    assert "events" not in evidence
    assert evidence["readable_semantic_change_chain_markdown"] == (
        report.readable_markdown
    )


def test_semantic_change_report_contract_preserves_blockers() -> None:
    report = MetaProviderDeltaSemanticChangeReport.from_payload(
        _provider_delta_semantic_change_report(
            semantic_dirty_diff={
                "status": "semantic_dirty_diff_blocked",
                "reason": "missing_baseline",
                "dirty_entry_count": 0,
            },
            provider_delta_typed_operation_plan={
                "status": "typed_operation_plan_blocked",
                "reason": "blocked",
                "typed_operations": (),
            },
        )
    )

    assert report.ready is False
    assert report.blocked is True
    assert report.semantic_world_changes == ()
    assert report.semantic_world_change_count == 0
    assert report.blockers == (
        "semantic_dirty_diff_not_ready:semantic_dirty_diff_blocked",
        "typed_operation_plan_not_ready:typed_operation_plan_blocked",
    )
    assert report.readable_markdown == "No semantic changes are ready."


def test_semantic_commit_evidence_contract_normalizes_ready_events() -> None:
    translation = MetaProviderDeltaSemanticCommitEvidence.from_payload(
        _provider_delta_semantic_commit_evidence(
            provider_delta_typed_operation_plan=_typed_operation_plan(),
            provider_delta_head_move_plan={"status": "head_move_applied"},
            provider_delta_head_move_applied_receipt={
                "status": "head_move_applied_receipt_ready",
                "head_refs": {
                    "semantic_package_commit_id": "semantic-commit-2",
                },
            },
            provider_delta_oig_commit_receipt={
                "status": "execute_flag_commit_applied",
                "commit_id": "oig-commit-2",
                "branch_id": "branch-main",
                "projection_hash": "projection-hash",
                "object_instance_graph_id": "oig-1",
                "object_instance_graph_identity_id": "oigi-1",
            },
        )
    )

    assert translation.ready is True
    assert translation.status == "semantic_commit_evidence_ready"
    assert translation.committed_semantic_change_count == 1
    assert translation.change_key_counts == {
        "aware_meta.attribute.update.committed": 1,
    }
    assert translation.operation_family_counts == {"update": 1}
    assert translation.changes_for_subject("attribute")

    change = translation.committed_semantic_changes[0]
    assert change.contract_version == (
        META_PROVIDER_DELTA_COMMITTED_SEMANTIC_CHANGE_CONTRACT_VERSION
    )
    assert change.change_key == "aware_meta.attribute.update.committed"
    assert change.source_change_key == "aware_meta.attribute.update"
    assert change.commit_ref["commit_id"] == "oig-commit-2"
    assert change.commit_ref["branch_id"] == "branch-main"
    assert change.head_refs["semantic_package_commit_id"] == ("semantic-commit-2")
    assert change.delta_keys == ("delta:attribute:name",)

    evidence = translation.evidence_payload()
    assert evidence["contract_version"] == (
        META_PROVIDER_DELTA_SEMANTIC_COMMIT_EVIDENCE_CONTRACT_VERSION
    )
    assert "semantic_events" not in evidence


def test_semantic_commit_evidence_contract_preserves_blockers() -> None:
    translation = MetaProviderDeltaSemanticCommitEvidence.from_payload(
        _provider_delta_semantic_commit_evidence(
            provider_delta_typed_operation_plan=_typed_operation_plan(),
            provider_delta_head_move_plan={"status": "head_move_plan_ready"},
            provider_delta_head_move_applied_receipt={
                "status": "head_move_applied_receipt_blocked",
            },
            provider_delta_oig_commit_receipt={
                "status": "execute_flag_commit_blocked",
            },
        )
    )

    assert translation.ready is False
    assert translation.blocked is True
    assert translation.committed_semantic_changes == ()
    assert translation.committed_semantic_change_count == 0
    assert translation.blockers == (
        "oig_commit_not_applied:execute_flag_commit_blocked",
        "head_move_not_applied:head_move_plan_ready",
        "head_move_applied_receipt_not_ready:head_move_applied_receipt_blocked",
    )


def test_pipeline_context_exposes_typed_semantic_change_summary() -> None:
    report = _provider_delta_semantic_change_report(
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "dirty_entry_count": 1,
        },
        provider_delta_typed_operation_plan=_typed_operation_plan(),
    )
    translation = _provider_delta_semantic_commit_evidence(
        provider_delta_typed_operation_plan=_typed_operation_plan(),
        provider_delta_head_move_plan={"status": "head_move_applied"},
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {"semantic_package_commit_id": "semantic-commit-2"},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
            "commit_id": "oig-commit-2",
        },
    )
    context = (
        _context()
        .with_semantic_change_report(report)
        .with_semantic_commit_evidence(translation)
    )
    summary = context.evidence_summary()

    assert context.semantic_change_report_ready is True
    assert context.semantic_commit_evidence_ready is True
    assert summary["semantic_change_report_status"] == ("semantic_change_report_ready")
    assert summary["semantic_world_change_count"] == 1
    assert summary["semantic_readable_change_line_count"] == 1
    assert summary["semantic_commit_evidence_status"] == (
        "semantic_commit_evidence_ready"
    )
    assert summary["committed_semantic_change_count"] == 1
    stage_statuses = cast(dict[str, object], summary["stage_statuses"])
    assert stage_statuses["semantic_change_report"] == ("semantic_change_report_ready")
    assert stage_statuses["semantic_commit_evidence"] == (
        "semantic_commit_evidence_ready"
    )


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


def _typed_operation_plan() -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operations": (_attribute_update_operation(),),
        "semantic_object_anchors": (),
        "blocked_operations": (),
    }


def _attribute_update_operation() -> dict[str, object]:
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": "op:attribute:update:name",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": "graph:home.Home/node:home.Device/attribute:name",
        "semantic_subject_type": "ObjectConfigGraphAttribute",
        "ontology_subject_kind": "attribute",
        "source_entry_key": "entry:attribute:name",
        "source_delta_key": "delta:attribute:name",
        "source_refs": ("aware/home/device.aware",),
        "baseline": {
            "object": {
                "attribute_name": "name",
                "owner_semantic_key": "graph:home.Home/node:home.Device",
                "attribute_signature": {
                    "kind": "primitive",
                    "primitive_base_type": "int",
                    "is_required": True,
                },
            },
        },
        "current": {
            "payload": {"package_name": "home-ontology"},
            "attribute_name": "name",
            "owner_semantic_key": "graph:home.Home/node:home.Device",
            "attribute_signature": {
                "kind": "primitive",
                "primitive_base_type": "string",
                "is_required": True,
            },
        },
        "semantic_change_projection": {
            "change_key": "aware_meta.attribute.update",
            "delta_keys": ("delta:attribute:name",),
            "condition_keys": ("meta.attribute.name.changed",),
            "payload": {"attribute_name": "name"},
        },
        "source_semantic_change": {
            "change_key": "aware_meta.attribute.update",
        },
        "ocg_operation": {
            "operation": "update_attribute_config",
            "attribute_name": "name",
        },
    }
