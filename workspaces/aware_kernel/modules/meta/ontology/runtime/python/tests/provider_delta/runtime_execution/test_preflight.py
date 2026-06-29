from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from aware_meta.materialization import workspace_provider
from aware_meta.materialization.deltas.execution import (
    _provider_delta_baseline_domain_commit_id,
    _provider_delta_execute_flag_preflight,
    _provider_delta_head_move_applied_receipt,
    _provider_delta_oig_commit_receipt,
)

from ..fixtures import (
    baseline_ref_payload,
    provider_delta_request,
    write_meta_delta_fixture,
)


def test_execute_preflight_allows_functioncall_rail_when_mutation_plan_is_partial() -> (
    None
):
    preflight = _provider_delta_execute_flag_preflight(
        request=SimpleNamespace(execute_provider_delta_materialization=True),
        baseline_dirty_preflight={
            "status": "baseline_commit_refs_available",
            "commit_backed_baseline_available": True,
            "baseline_ref_available": True,
            "baseline_ref_hydrator_ready": True,
            "baseline_hydration_preflight": {"status": "baseline_hydrated"},
        },
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "dirty_entry_count": 1,
        },
        provider_delta_head_move_plan={"status": "head_move_plan_ready"},
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
        },
        provider_delta_mutation_plan={
            "status": "mutation_plan_partially_blocked",
        },
        provider_delta_ontology_execution_plan={
            "status": "ontology_execution_plan_ready",
            "invocation_intent_count": 1,
            "blockers": (),
            "invocation_runtime_preflight": {
                "runtime_invoke_function_available": True,
                "runtime_invoke_instance_available": False,
            },
        },
        provider_delta_functioncall_capability_matrix={
            "coverage_status": "all_operations_executable",
            "execution_allowed": True,
            "non_executable_operation_count": 0,
            "blockers": (),
        },
    )

    assert preflight["status"] == "execute_flag_preflight_ready"
    assert preflight["blockers"] == ()
    assert preflight["provider_delta_mutation_plan_status"] == (
        "mutation_plan_partially_blocked"
    )
    assert preflight["active_execution_rail"] == "ontology_function_call"
    assert preflight["active_execution_status"] == ("active_execution_rail_ready")
    active_execution_rail = cast(
        dict[str, object],
        preflight["provider_delta_active_execution_rail"],
    )
    assert active_execution_rail["execution_allowed"] is True
    assert "provider_delta_legacy_descriptor_tree_diagnostics" not in preflight
    assert "descriptor_tree_legacy_diagnostic_status" not in active_execution_rail
    assert preflight["provider_delta_functioncall_capability_execution_allowed"] is True


@pytest.mark.asyncio
async def test_execute_preflight_allows_noop_apply_without_ontology_invocations(
    tmp_path: Path,
) -> None:
    manifest_path = write_meta_delta_fixture(tmp_path)
    baseline_ref = baseline_ref_payload(manifest_path=manifest_path)
    request = SimpleNamespace(
        execute_provider_delta_materialization=True,
        baseline_ref=baseline_ref,
    )
    baseline_dirty_preflight = {
        "status": "baseline_commit_refs_available",
        "commit_backed_baseline_available": True,
        "baseline_ref_available": True,
        "baseline_ref_hydrator_ready": True,
        "baseline_hydration_preflight": {
            "status": "baseline_hydrated",
            "source_object_instance_graph_commit_id": baseline_ref[
                "source_object_instance_graph_commit_id"
            ],
            "semantic_branch_id": baseline_ref["semantic_branch_id"],
            "semantic_projection_name": baseline_ref["semantic_projection_name"],
            "semantic_projection_hash": "projection-hash",
            "semantic_package_id": baseline_ref["semantic_package_id"],
            "semantic_root_id": baseline_ref["semantic_root_id"],
            "semantic_package_commit_id": baseline_ref["semantic_package_commit_id"],
            "semantic_object_instance_graph_commit_id": baseline_ref[
                "semantic_object_instance_graph_commit_id"
            ],
            "semantic_root_object_instance_graph_commit_id": baseline_ref[
                "semantic_root_object_instance_graph_commit_id"
            ],
        },
    }
    preflight = _provider_delta_execute_flag_preflight(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        semantic_dirty_diff={
            "status": "semantic_dirty_diff_ready",
            "dirty_entry_count": 7,
            "blocked": False,
        },
        provider_delta_head_move_plan={
            "status": "head_move_plan_ready",
            "planned_operation_count": 0,
            "blocked": False,
        },
        provider_delta_typed_operation_plan={
            "status": "typed_operation_plan_ready",
            "typed_operation_count": 0,
            "blocked_operation_count": 0,
            "blocked": False,
        },
        provider_delta_mutation_plan={"status": "mutation_plan_empty"},
        provider_delta_ontology_execution_plan={
            "status": "ontology_execution_plan_empty",
            "invocation_intent_count": 0,
            "blockers": (),
            "invocation_runtime_preflight": {
                "runtime_invoke_function_available": False,
                "runtime_invoke_instance_available": False,
            },
        },
        provider_delta_functioncall_capability_matrix={
            "coverage_status": "no_operations",
            "execution_allowed": False,
            "non_executable_operation_count": 0,
            "blockers": (),
        },
    )

    assert preflight["status"] == "execute_flag_preflight_ready"
    assert preflight["noop_apply"] is True
    assert preflight["blockers"] == ()
    assert preflight["active_execution_rail"] == "semantic_noop"

    commit_receipt = await _provider_delta_oig_commit_receipt(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_mutation_plan={"status": "mutation_plan_empty"},
        provider_delta_ontology_execution_plan={
            "status": "ontology_execution_plan_empty",
            "invocation_intent_count": 0,
        },
        provider_delta_execute_flag_preflight=preflight,
    )
    assert commit_receipt["status"] == "execute_flag_commit_noop"
    assert commit_receipt["available"] is True
    assert commit_receipt["did_execute"] is False

    head_receipt = _provider_delta_head_move_applied_receipt(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_oig_commit_receipt=commit_receipt,
    )

    assert head_receipt["status"] == "head_move_applied_receipt_ready"
    assert head_receipt["reason"] == "meta_ocg_provider_delta_head_stayed_noop"
    assert head_receipt["dirty_status_after_head_move"] == "clean"
    assert head_receipt["did_execute"] is False
    head_refs = cast(dict[str, object], head_receipt["head_refs"])
    assert head_refs["head_ref_status"] == "head_refs_available"
    assert head_refs["semantic_package_commit_id"] == (
        baseline_ref["semantic_package_commit_id"]
    )
    assert head_refs["semantic_object_instance_graph_commit_id"] == (
        baseline_ref["semantic_object_instance_graph_commit_id"]
    )


def test_provider_delta_baseline_domain_commit_prefers_root_ocg_head() -> None:
    domain_commit_id = "11111111-1111-4111-8111-111111111111"
    package_commit_id = "22222222-2222-4222-8222-222222222222"
    baseline_ref = {
        "semantic_object_instance_graph_commit_id": domain_commit_id,
        "semantic_package_commit_id": package_commit_id,
    }

    resolved = _provider_delta_baseline_domain_commit_id(
        request=SimpleNamespace(),
        hydration={},
        baseline_ref=baseline_ref,
    )

    assert str(resolved) == domain_commit_id


@pytest.mark.asyncio
async def test_meta_provider_delta_blocks_execution_when_baseline_missing(
    tmp_path: Path,
) -> None:
    manifest_path = write_meta_delta_fixture(tmp_path)
    base_request = provider_delta_request(manifest_path=manifest_path)
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        execute_provider_delta_materialization=True,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])

    assert result["status"] == "succeeded"
    assert result["fallback_reason"] is None
    assert details["source_files"] == ()
    assert details["semantic_delta_count"] == 0
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    assert preflight["status"] == "baseline_context_missing"
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    assert operation_execution["status"] == "baseline_context_missing"
    assert operation_execution["reason"] == (
        "meta_ocg_provider_delta_operation_execution_requires_commit_backed_baseline"
    )
    assert operation_execution["flag_requested"] is True
    assert operation_execution["would_execute"] is False
    assert operation_execution["did_execute"] is False
    assert operation_execution["execution_wired"] is False
    execute_preflight = cast(
        dict[str, object],
        details["provider_delta_execute_flag_preflight"],
    )
    assert execute_preflight["status"] == "execute_flag_preflight_blocked"
    assert execute_preflight["flag_requested"] is True
    assert (
        "baseline_commit_ref_missing:" "baseline_source_object_instance_graph_commit_id"
    ) in cast(Sequence[str], execute_preflight["blockers"])
    assert operation_execution["execute_flag_preflight_status"] == (
        "execute_flag_preflight_blocked"
    )


@pytest.mark.asyncio
async def test_meta_provider_delta_falls_back_when_execution_requested_with_baseline(
    tmp_path: Path,
) -> None:
    manifest_path = write_meta_delta_fixture(tmp_path)
    base_request = provider_delta_request(
        manifest_path=manifest_path,
        include_baseline_refs=True,
    )
    request = SimpleNamespace(
        package=base_request.package,
        semantic_contract=base_request.semantic_contract,
        current_delta_fingerprint=base_request.current_delta_fingerprint,
        delta_cause_hints=base_request.delta_cause_hints,
        code_package_delta=base_request.code_package_delta,
        previous_materialization_evidence=(
            base_request.previous_materialization_evidence
        ),
        baseline_ref=base_request.baseline_ref,
        baseline_source_object_instance_graph_commit_id=(
            base_request.baseline_source_object_instance_graph_commit_id
        ),
        baseline_semantic_object_instance_graph_commit_id=(
            base_request.baseline_semantic_object_instance_graph_commit_id
        ),
        baseline_semantic_root_object_instance_graph_commit_id=(
            base_request.baseline_semantic_root_object_instance_graph_commit_id
        ),
        execute_provider_delta_materialization=True,
    )

    result = await workspace_provider.materialize_delta(request=request)
    details = cast(dict[str, object], result["details"])

    assert result["status"] == "fallback_required"
    assert result["fallback_reason"] == (
        "meta_ocg_delta_execute_flag_preflight_blocked"
    )
    preflight = cast(dict[str, object], details["baseline_dirty_preflight"])
    assert preflight["status"] == "baseline_commit_refs_available"
    operation_execution = cast(
        dict[str, object],
        details["provider_delta_operation_execution"],
    )
    assert operation_execution["status"] == "execute_preflight_blocked"
    assert operation_execution["flag_requested"] is True
    assert operation_execution["would_execute"] is False
    assert operation_execution["did_execute"] is False
    assert operation_execution["execution_wired"] is False
    execute_preflight = cast(
        dict[str, object],
        details["provider_delta_execute_flag_preflight"],
    )
    assert execute_preflight["status"] == "execute_flag_preflight_blocked"
    assert execute_preflight["baseline_hydration_status"] == (
        "baseline_hydrator_unavailable"
    )
    assert execute_preflight["provider_delta_mutation_plan_status"] == (
        "mutation_plan_blocked"
    )
    assert "provider_delta_legacy_descriptor_tree_diagnostics" not in execute_preflight
    assert {
        "baseline_hydration_not_ready:baseline_hydrator_unavailable",
        "ontology_execution_plan_not_ready:ontology_execution_plan_blocked",
        "ontology_execution_plan_has_no_invocation_intents",
        "ontology_function_call_runtime_unavailable",
    }.issubset(set(cast(Sequence[str], execute_preflight["blockers"])))
    operation_plan = cast(dict[str, object], details["delta_operation_plan"])
    assert operation_plan["provider_delta_execute_flag_preflight_status"] == (
        "execute_flag_preflight_blocked"
    )
    head_move_applied_receipt = cast(
        dict[str, object],
        details["provider_delta_head_move_applied_receipt"],
    )
    assert head_move_applied_receipt["status"] == (
        "head_move_applied_receipt_unavailable"
    )
    assert head_move_applied_receipt["blocked"] is True
    head_refs = cast(dict[str, object], head_move_applied_receipt["head_refs"])
    assert head_refs["head_ref_status"] == "head_refs_unavailable"
    assert operation_plan["provider_delta_head_move_applied_receipt_status"] == (
        "head_move_applied_receipt_unavailable"
    )
    semantic_commit_evidence = cast(
        dict[str, object],
        details["provider_delta_semantic_commit_evidence"],
    )
    assert semantic_commit_evidence["status"] == ("semantic_commit_evidence_blocked")
    assert "oig_commit_not_applied:execute_flag_commit_blocked" in cast(
        Sequence[str],
        semantic_commit_evidence["blockers"],
    )
