from __future__ import annotations

from types import SimpleNamespace

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_OIG_COMMIT_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_OUTPUT_MATERIALIZATION_RECEIPT_CONTRACT_VERSION,
    META_PROVIDER_DELTA_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION,
    MetaProviderDeltaHeadMoveAppliedReceipt,
    MetaProviderDeltaOigCommitReceipt,
    MetaProviderDeltaOutputMaterializationReceipt,
    MetaProviderDeltaRuntimePackageIndexPatchReceipt,
)
from aware_meta.materialization.deltas.pipeline import (
    MetaProviderDeltaPipelineContext,
)


def test_receipt_contracts_normalize_applied_post_commit_truth() -> None:
    oig_receipt = MetaProviderDeltaOigCommitReceipt.from_payload(_oig_commit_receipt())
    head_receipt = MetaProviderDeltaHeadMoveAppliedReceipt.from_payload(
        _head_move_receipt()
    )
    index_patch = MetaProviderDeltaRuntimePackageIndexPatchReceipt.from_payload(
        _index_patch_receipt()
    )
    output_receipt = MetaProviderDeltaOutputMaterializationReceipt.from_payload(
        _output_receipt()
    )

    assert oig_receipt.applied is True
    assert oig_receipt.commit_id == "commit-1"
    assert oig_receipt.object_instance_graph_commit_id == "oig-commit-1"
    assert oig_receipt.applied_invocation_count == 2
    assert oig_receipt.evidence_payload()["contract_version"] == (
        META_PROVIDER_DELTA_OIG_COMMIT_RECEIPT_CONTRACT_VERSION
    )

    assert head_receipt.ready is True
    assert head_receipt.head_ref_status == "head_refs_available"
    assert head_receipt.semantic_package_commit_id == "semantic-package-commit-1"
    assert head_receipt.semantic_object_instance_graph_commit_id == "oig-commit-1"
    assert head_receipt.evidence_payload()["contract_version"] == (
        META_PROVIDER_DELTA_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION
    )

    assert index_patch.applied is True
    assert index_patch.semantic_object_upsert_count == 3
    assert index_patch.semantic_object_delete_count == 1
    assert index_patch.package_index_semantic_object_count == 12
    assert index_patch.evidence_payload()["contract_version"] == (
        META_PROVIDER_DELTA_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION
    )

    assert output_receipt.ready is True
    assert output_receipt.target_count == 2
    assert output_receipt.rendered_target_count == 2
    assert output_receipt.artifact_ownership_receipt_count == 4
    assert output_receipt.evidence_payload()["contract_version"] == (
        META_PROVIDER_DELTA_OUTPUT_MATERIALIZATION_RECEIPT_CONTRACT_VERSION
    )


def test_receipt_contracts_preserve_blocked_state() -> None:
    oig_receipt = MetaProviderDeltaOigCommitReceipt.from_payload(
        {
            "status": "execute_flag_commit_blocked",
            "reason": "meta_ocg_provider_delta_execute_flag_commit_blocked",
            "blocked": True,
        }
    )
    head_receipt = MetaProviderDeltaHeadMoveAppliedReceipt.from_payload(
        {
            "status": "head_move_applied_receipt_blocked",
            "reason": "meta_ocg_provider_delta_head_refs_incomplete",
            "blocked": True,
            "head_refs": {"head_ref_status": "head_refs_partial"},
        }
    )
    index_patch = MetaProviderDeltaRuntimePackageIndexPatchReceipt.from_payload(
        {
            "status": "runtime_package_index_patch_blocked",
            "reason": "meta_ocg_provider_delta_runtime_package_index_patch_blocked",
            "available": False,
            "blocked": True,
        }
    )
    output_receipt = MetaProviderDeltaOutputMaterializationReceipt.from_payload(
        {
            "status": "provider_delta_output_materialization_blocked",
            "reason": "provider_delta_head_move_not_ready",
            "blocked": True,
        }
    )

    assert oig_receipt.applied is False
    assert oig_receipt.blocked is True
    assert head_receipt.ready is False
    assert head_receipt.blocked is True
    assert head_receipt.head_ref_status == "head_refs_partial"
    assert index_patch.applied is False
    assert index_patch.available is False
    assert index_patch.blocked is True
    assert output_receipt.ready is False
    assert output_receipt.blocked is True


def test_pipeline_context_summarizes_post_commit_receipts() -> None:
    context = (
        _context()
        .with_oig_commit_receipt(_oig_commit_receipt())
        .with_head_move_applied_receipt(_head_move_receipt())
        .with_runtime_package_index_patch(_index_patch_receipt())
        .with_output_materialization(_output_receipt())
    )
    summary = context.evidence_summary()

    assert context.oig_commit_applied is True
    assert context.head_move_applied is True
    assert context.runtime_package_index_patch_applied is True
    assert context.output_materialization_ready is True
    assert summary["provider_delta_oig_commit_receipt_status"] == (
        "execute_flag_commit_applied"
    )
    assert summary["provider_delta_oig_commit_applied"] is True
    assert summary["provider_delta_head_ref_status"] == "head_refs_available"
    assert summary["provider_delta_runtime_package_index_patch_upsert_count"] == 3
    assert summary["provider_delta_output_materialization_artifact_receipt_count"] == 4
    assert summary["stage_statuses"] == {
        "baseline_dirty_preflight": "baseline_dirty_preflight_ready",
        "semantic_dirty_diff": None,
        "head_move_plan": None,
        "typed_operation_plan": None,
        "semantic_change_report": None,
        "source_projection": None,
        "generated_materialization": None,
        "semantic_commit_evidence": None,
        "ontology_execution_plan": None,
        "functioncall_capability_matrix": None,
        "execute_flag_preflight": None,
        "oig_commit_receipt": "execute_flag_commit_applied",
        "head_move_applied_receipt": "head_move_applied_receipt_ready",
        "runtime_package_index_patch": "runtime_package_index_patch_applied",
        "output_materialization": "provider_delta_output_materialization_ready",
    }


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


def _oig_commit_receipt() -> dict[str, object]:
    return {
        "receipt_kind": "meta_ocg_provider_delta_execute_flag_commit_receipt",
        "contract_version": META_PROVIDER_DELTA_OIG_COMMIT_RECEIPT_CONTRACT_VERSION,
        "status": "execute_flag_commit_applied",
        "reason": "meta_ocg_provider_delta_execute_flag_commit_applied",
        "commit_id": "commit-1",
        "domain_commit_id": "semantic-package-commit-1",
        "object_instance_graph_commit_id": "oig-commit-1",
        "branch_id": "branch-1",
        "projection_hash": "projection-hash-1",
        "ontology_function_call_execution_status": (
            "ontology_function_call_execution_applied"
        ),
        "ontology_function_call_execution_applied_invocation_count": 2,
    }


def _head_move_receipt() -> dict[str, object]:
    return {
        "receipt_kind": "meta_ocg_provider_delta_head_move_applied_receipt",
        "contract_version": (
            META_PROVIDER_DELTA_HEAD_MOVE_APPLIED_RECEIPT_CONTRACT_VERSION
        ),
        "status": "head_move_applied_receipt_ready",
        "reason": "meta_ocg_provider_delta_head_move_applied",
        "head_refs": {
            "head_ref_status": "head_refs_available",
            "semantic_package_commit_id": "semantic-package-commit-1",
            "semantic_object_instance_graph_commit_id": "oig-commit-1",
        },
        "dirty_status_after_head_move": "clean",
    }


def _index_patch_receipt() -> dict[str, object]:
    return {
        "receipt_kind": "meta_ocg_provider_delta_runtime_package_index_patch",
        "contract_version": (
            META_PROVIDER_DELTA_RUNTIME_PACKAGE_INDEX_PATCH_CONTRACT_VERSION
        ),
        "status": "runtime_package_index_patch_applied",
        "reason": "meta_ocg_provider_delta_runtime_package_index_patch_applied",
        "available": True,
        "semantic_object_upsert_count": 3,
        "semantic_object_delete_count": 1,
        "package_index_semantic_object_count": 12,
    }


def _output_receipt() -> dict[str, object]:
    return {
        "receipt_kind": "meta_provider_delta_output_materialization",
        "contract_version": (
            META_PROVIDER_DELTA_OUTPUT_MATERIALIZATION_RECEIPT_CONTRACT_VERSION
        ),
        "status": "provider_delta_output_materialization_ready",
        "reason": "provider_delta_outputs_materialized",
        "target_count": 2,
        "rendered_target_count": 2,
        "artifact_ownership_receipt_count": 4,
        "post_step_receipt_count": 1,
        "tool_step_receipt_count": 1,
    }
