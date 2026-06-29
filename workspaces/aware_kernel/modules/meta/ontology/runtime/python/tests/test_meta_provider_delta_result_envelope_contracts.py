from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION,
    META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
    MetaProviderDeltaResultEnvelope,
)
from aware_meta.materialization.deltas.result import (
    _baseline_context_missing_result,
    _fallback_result,
    _provider_delta_result,
)


def test_provider_delta_result_envelope_normalizes_succeeded_payload() -> None:
    result = _provider_delta_result(
        request=_request(execute=False),
        package_payload=_package_payload(),
        semantic_contract_payload=_semantic_contract_payload(),
        manifest_path=Path("modules/home/structure/ontology/aware.toml"),
        analysis=_analysis(),
        current_delta_fingerprint="sha256:current",
        operation_plan={"status": "ready"},
        operation_execution={"status": "dry_run"},
        provider_delta_execution_context_preflight={"status": "available"},
        provider_delta_execute_flag_preflight={
            "status": "execute_flag_preflight_ready",
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
            "commit_id": "oig-commit-2",
        },
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": _head_refs(),
        },
        provider_delta_runtime_package_index_patch={
            "status": "runtime_package_index_patch_applied",
            "semantic_object_upsert_count": 1,
        },
        provider_delta_semantic_commit_evidence={
            "status": "semantic_commit_evidence_ready",
            "available": True,
            "committed_semantic_change_count": 1,
            "committed_semantic_changes": (
                {"change_key": "aware_meta.attribute.update.committed"},
            ),
        },
        provider_delta_output_materialization={
            "status": "provider_delta_output_materialization_ready",
            "artifact_ownership_receipt_count": 1,
            "artifact_ownership_receipts": (
                {"artifact_path": "modules/home/generated.py"},
            ),
        },
        provider_delta_head_move_plan={"status": "head_move_applied"},
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operations": (),
            "semantic_object_anchors": (),
            "blocked_operations": (),
        },
        provider_delta_mutation_plan={"status": "mutation_plan_ready"},
        provider_delta_ontology_execution_plan={
            "status": "ontology_execution_plan_ready"
        },
        provider_delta_functioncall_capability_matrix={
            "coverage_status": "functioncall_capability_executable",
            "execution_allowed": True,
        },
        baseline_dirty_preflight={"status": "baseline_dirty_preflight_ready"},
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "available": True,
            "dirty_entry_count": 1,
            "semantic_dirty_entries": (),
        },
        applied_semantic_keys=("graph:home.Home/node:home.Device",),
        stale_semantic_keys=("graph:home.Home/node:home.Legacy",),
    )
    envelope = MetaProviderDeltaResultEnvelope.from_payload(result)

    assert result["contract_version"] == META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
    assert envelope.succeeded is True
    assert envelope.fallback_required is False
    assert envelope.applied_semantic_keys == ("graph:home.Home/node:home.Device",)
    assert envelope.stale_semantic_keys == ("graph:home.Home/node:home.Legacy",)
    assert envelope.details.provider_key == "aware_meta"
    assert envelope.details.manifest_path == (
        "modules/home/structure/ontology/aware.toml"
    )
    assert envelope.details.semantic_delta_count == 1
    assert envelope.details.semantic_change_count == 1
    assert envelope.details.commit_applied is True
    assert envelope.details.head_move_applied is True
    assert envelope.details.runtime_package_index_patched is True
    assert envelope.details.semantic_commit_evidence_ready is True
    assert envelope.details.output_materialized is True
    assert envelope.details.production_execution_wired is True
    assert envelope.commit_ref_ready is True
    assert envelope.commit_ref_contract.contract_version == (
        META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION
    )
    assert envelope.commit_ref_contract.missing_required_fields == ()
    assert envelope.bundle_package.semantic_branch_id == "branch-main"
    assert envelope.bundle_package.semantic_head_commit_id == "semantic-commit-2"
    assert envelope.evidence_payload()["details"] == result["details"]


def test_provider_delta_result_envelope_normalizes_fallback_payload() -> None:
    result = _fallback_result(
        request=_request(execute=True),
        fallback_reason="meta_ocg_delta_execute_flag_commit_failed",
        details={
            "manifest_path": "modules/home/structure/ontology/aware.toml",
            "provider_delta_oig_commit_receipt": {
                "status": "execute_flag_commit_blocked",
            },
        },
    )
    envelope = MetaProviderDeltaResultEnvelope.from_payload(result)

    assert envelope.fallback_required is True
    assert envelope.succeeded is False
    assert envelope.fallback_reason == "meta_ocg_delta_execute_flag_commit_failed"
    assert envelope.applied_semantic_keys == ()
    assert envelope.details.oig_commit_receipt_status == ("execute_flag_commit_blocked")
    assert envelope.details.production_execution_wired is False
    assert envelope.commit_ref_contract.status == "not_applicable_fallback_required"
    assert envelope.commit_ref_ready is False
    assert envelope.bundle_package.commit_ref_contract_status == (
        "not_applicable_fallback_required"
    )


def test_baseline_context_missing_result_uses_typed_envelope_shape() -> None:
    result = _baseline_context_missing_result(
        request=_request(execute=True),
        package_payload=_package_payload(),
        semantic_contract_payload=_semantic_contract_payload(),
        manifest_path="modules/home/structure/ontology/aware.toml",
        baseline_dirty_preflight={
            "status": "baseline_context_missing",
            "reason": "meta_ocg_dirty_diff_requires_commit_backed_baseline",
            "available": False,
        },
    )
    envelope = MetaProviderDeltaResultEnvelope.from_payload(result)

    assert envelope.succeeded is True
    assert envelope.details.delta_operation_plan["status"] == "blocked"
    assert envelope.details.baseline_dirty_preflight_status == (
        "baseline_context_missing"
    )
    assert envelope.details.execute_flag_preflight_status is not None
    assert envelope.details.production_execution_wired is False
    assert envelope.commit_ref_contract.status == "missing_durable_refs"
    assert envelope.commit_ref_contract.ready is False
    assert envelope.bundle_packages[0].manifest_toml_path == (
        "modules/home/structure/ontology/aware.toml"
    )


def _request(*, execute: bool) -> SimpleNamespace:
    return SimpleNamespace(
        package=SimpleNamespace(**_package_payload()),
        semantic_contract=SimpleNamespace(**_semantic_contract_payload()),
        current_delta_fingerprint="sha256:current",
        execute_provider_delta_materialization=execute,
        baseline_source_object_instance_graph_commit_id=("source-baseline-commit"),
        baseline_semantic_object_instance_graph_commit_id=("semantic-baseline-commit"),
        baseline_semantic_root_object_instance_graph_commit_id=("root-baseline-commit"),
        baseline_ref=None,
        delta_cause_hints=SimpleNamespace(
            changed_path_count=1,
            source_owned_path_count=1,
            generated_fallout_path_count=0,
            top_changed_path_limit=5,
            top_changed_paths=(SimpleNamespace(path="modules/home/home.aware"),),
        ),
        previous_materialization_evidence=None,
    )


def _analysis() -> SimpleNamespace:
    return SimpleNamespace(
        source_files=("modules/home/home.aware",),
        change_preview=SimpleNamespace(
            changed_source_files=("modules/home/home.aware",),
            semantic_deltas=(SimpleNamespace(delta_key="delta:attribute:name"),),
            semantic_events=(SimpleNamespace(event_key="aware_meta.attribute.update"),),
        ),
    )


def _package_payload() -> dict[str, object]:
    return {
        "package_name": "home-ontology",
        "manifest_path": "modules/home/structure/ontology/aware.toml",
        "source_code_package_id": "source-code-package-1",
    }


def _semantic_contract_payload() -> dict[str, object]:
    return {
        "provider_key": "aware_meta",
        "role": "semantic_provider",
        "name": "Aware Meta",
    }


def _head_refs() -> dict[str, object]:
    return {
        "source_object_instance_graph_commit_id": "source-commit-2",
        "semantic_package_id": "semantic-package-1",
        "semantic_branch_id": "branch-main",
        "semantic_projection_name": "ObjectConfigGraph",
        "semantic_projection_hash": "projection-hash",
        "semantic_package_commit_id": "semantic-commit-2",
        "semantic_object_instance_graph_commit_id": "semantic-oig-commit-2",
        "semantic_root_id": "semantic-root-1",
        "semantic_root_object_instance_graph_commit_id": "root-oig-commit-2",
    }
