from __future__ import annotations

from types import SimpleNamespace

from aware_meta.materialization.deltas.pipeline import (
    MetaProviderDeltaPipelineContext,
)


def test_pipeline_context_updates_stages_immutably() -> None:
    context = _context()
    updated = (
        context.with_semantic_dirty_diff(
            {
                "status": "semantic_dirty_diff_ready",
                "dirty_entry_count": 1,
            }
        )
        .with_head_move_plan({"status": "head_move_plan_ready"})
        .with_typed_operation_plan(_typed_operation_plan())
    )

    assert context.semantic_dirty_diff == {}
    assert context.provider_delta_head_move_plan == {}
    assert context.provider_delta_typed_operation_plan == {}
    assert updated.semantic_dirty_diff["status"] == "semantic_dirty_diff_ready"
    assert updated.provider_delta_head_move_plan["status"] == ("head_move_plan_ready")
    assert updated.typed_operation_status == "typed_operation_plan_ready"
    assert len(updated.typed_operation_plan.typed_operations) == 1


def test_pipeline_context_exposes_typed_middle_stage_accessors() -> None:
    context = (
        _context()
        .with_typed_operation_plan(_typed_operation_plan())
        .with_ontology_execution_plan(
            {
                "status": "ontology_execution_plan_ready",
                "invocation_intent_count": "2",
            }
        )
        .with_functioncall_capability_matrix(
            {
                "coverage_status": "functioncall_capability_executable",
                "execution_allowed": True,
            }
        )
        .with_execute_flag_preflight(
            {
                "status": "execute_flag_preflight_ready",
                "provider_delta_active_execution_rail": {
                    "active_execution_rail": "ontology_function_call",
                    "status": "active_execution_rail_ready",
                },
            }
        )
    )

    assert context.typed_operation_status == "typed_operation_plan_ready"
    assert context.ontology_execution_status == "ontology_execution_plan_ready"
    assert context.ontology_execution_plan.invocation_intent_count == 2
    assert context.functioncall_execution_allowed is True
    assert context.execute_flag_ready is True


def test_pipeline_context_exposes_result_stage_payloads() -> None:
    context = (
        _context()
        .with_semantic_dirty_diff(
            {
                "status": "semantic_dirty_diff_ready",
                "available": True,
                "dirty_entry_count": 1,
                "semantic_dirty_entries": (),
            }
        )
        .with_head_move_plan({"status": "head_move_applied"})
        .with_typed_operation_plan(_typed_operation_plan())
        .with_semantic_change_report(
            {
                "status": "semantic_change_report_ready",
                "available": True,
                "semantic_world_change_count": 1,
                "semantic_world_changes": (),
            }
        )
        .with_mutation_plan({"status": "mutation_plan_ready"})
        .with_ontology_execution_plan(
            {
                "status": "ontology_execution_plan_ready",
                "invocation_intent_count": 2,
            }
        )
        .with_functioncall_capability_matrix(
            {
                "coverage_status": "functioncall_capability_executable",
                "execution_allowed": True,
            }
        )
        .with_execute_flag_preflight(
            {
                "status": "execute_flag_preflight_ready",
                "provider_delta_active_execution_rail": {
                    "active_execution_rail": "ontology_function_call",
                    "status": "active_execution_rail_ready",
                },
            }
        )
        .with_oig_commit_receipt(
            {
                "status": "execute_flag_commit_applied",
            }
        )
        .with_head_move_applied_receipt({"status": "head_move_applied_receipt_ready"})
        .with_runtime_package_index_patch(
            {"status": "runtime_package_index_patch_applied"}
        )
        .with_semantic_commit_evidence(
            {
                "status": "semantic_commit_evidence_ready",
                "available": True,
                "committed_semantic_change_count": 1,
                "committed_semantic_changes": (),
            }
        )
        .with_output_materialization(
            {"status": "provider_delta_output_materialization_ready"}
        )
    )
    stage_payloads = context.stage_payloads()

    assert stage_payloads["semantic_dirty_diff"]["status"] == (
        "semantic_dirty_diff_ready"
    )
    assert stage_payloads["provider_delta_typed_operation_plan"]["status"] == (
        "typed_operation_plan_ready"
    )
    assert stage_payloads["provider_delta_mutation_plan"]["status"] == (
        "mutation_plan_ready"
    )
    assert stage_payloads["provider_delta_oig_commit_receipt"]["status"] == (
        "execute_flag_commit_applied"
    )
    assert (
        "provider_delta_durable_oig_execution_inputs_preflight"
        not in stage_payloads
    )
    assert stage_payloads["provider_delta_semantic_commit_evidence"]["status"] == (
        "semantic_commit_evidence_ready"
    )


def test_pipeline_context_evidence_summary_is_stable_and_minimal() -> None:
    context = (
        _context()
        .with_semantic_dirty_diff(
            {
                "status": "semantic_dirty_diff_ready",
                "available": True,
                "dirty_entry_count": 3,
            }
        )
        .with_head_move_plan({"status": "head_move_plan_ready"})
        .with_typed_operation_plan(_typed_operation_plan())
        .with_ontology_execution_plan(
            {
                "status": "ontology_execution_plan_ready",
                "invocation_intent_count": 1,
            }
        )
        .with_functioncall_capability_matrix(
            {
                "coverage_status": "functioncall_capability_executable",
                "execution_allowed": True,
            }
        )
        .with_execute_flag_preflight(
            {
                "status": "execute_flag_preflight_ready",
                "provider_delta_active_execution_rail": {
                    "active_execution_rail": "ontology_function_call",
                    "status": "active_execution_rail_ready",
                },
            }
        )
        .with_semantic_change_report(
            {
                "status": "semantic_change_report_ready",
                "available": True,
                "semantic_world_change_count": 1,
                "minimal_readable_semantic_change_chain": {
                    "status": "readable_semantic_change_chain_ready",
                    "line_count": 1,
                    "lines": ("1. Update attribute `name`.",),
                    "markdown": "1. Update attribute `name`.",
                },
            }
        )
        .with_semantic_commit_evidence(
            {
                "status": "semantic_commit_evidence_ready",
                "available": True,
                "committed_semantic_change_count": 1,
                "committed_semantic_changes": (
                    {
                        "change_key": "aware_meta.attribute.update.committed",
                    },
                ),
            }
        )
        .with_mutation_plan({"status": "mutation_plan_ready"})
    )

    assert context.evidence_summary() == {
        "context_kind": "meta_ocg_provider_delta_pipeline_context",
        "manifest_path": "modules/home/structure/ontology/aware.toml",
        "current_delta_fingerprint": "sha256:current",
        "semantic_contract_provider_key": "aware_meta",
        "baseline_dirty_preflight_status": "baseline_dirty_preflight_ready",
        "semantic_dirty_diff_status": "semantic_dirty_diff_ready",
        "semantic_dirty_diff_ready": True,
        "semantic_dirty_entry_count": 3,
        "semantic_dirty_diff_baseline_index_compare_status": None,
        "semantic_dirty_diff_baseline_compare_operation_counts": {},
        "semantic_dirty_diff_stale_semantic_key_count": 0,
        "provider_delta_head_move_status": "head_move_plan_ready",
        "provider_delta_typed_operation_status": "typed_operation_plan_ready",
        "provider_delta_typed_operation_count": 1,
        "provider_delta_ontology_execution_status": ("ontology_execution_plan_ready"),
        "provider_delta_ontology_invocation_intent_count": 1,
        "provider_delta_functioncall_capability_status": (
            "functioncall_capability_executable"
        ),
        "provider_delta_functioncall_execution_allowed": True,
        "provider_delta_execute_flag_preflight_status": (
            "execute_flag_preflight_ready"
        ),
        "provider_delta_execute_flag_ready": True,
        "active_execution_rail": "ontology_function_call",
        "active_execution_status": "active_execution_rail_ready",
        "provider_delta_active_execution_rail": {
            "active_execution_rail": "ontology_function_call",
            "status": "active_execution_rail_ready",
        },
        "semantic_change_report_status": ("semantic_change_report_ready"),
        "semantic_change_report_ready": True,
        "semantic_world_change_count": 1,
        "semantic_readable_change_line_count": 1,
        "provider_delta_source_projection_status": None,
        "provider_delta_source_projection_ready": False,
        "provider_delta_source_projection_projected_entry_count": 0,
        "provider_delta_generated_materialization_status": None,
        "provider_delta_generated_materialization_ready": False,
        "provider_delta_generated_materialization_renderer_operation_count": 0,
        "semantic_commit_evidence_status": "semantic_commit_evidence_ready",
        "semantic_commit_evidence_ready": True,
        "committed_semantic_change_count": 1,
        "provider_delta_oig_commit_receipt_status": None,
        "provider_delta_oig_commit_applied": False,
        "provider_delta_oig_commit_id": None,
        "provider_delta_oig_object_instance_graph_commit_id": None,
        "provider_delta_head_move_applied_receipt_status": None,
        "provider_delta_head_move_applied": False,
        "provider_delta_head_ref_status": None,
        "provider_delta_semantic_package_commit_id": None,
        "provider_delta_runtime_package_index_patch_status": None,
        "provider_delta_runtime_package_index_patch_applied": False,
        "provider_delta_runtime_package_index_patch_upsert_count": 0,
        "provider_delta_runtime_package_index_patch_delete_count": 0,
        "provider_delta_output_materialization_status": None,
        "provider_delta_output_materialization_ready": False,
        "provider_delta_output_materialization_artifact_receipt_count": 0,
        "stage_statuses": {
            "baseline_dirty_preflight": "baseline_dirty_preflight_ready",
            "semantic_dirty_diff": "semantic_dirty_diff_ready",
            "head_move_plan": "head_move_plan_ready",
            "typed_operation_plan": "typed_operation_plan_ready",
            "semantic_change_report": "semantic_change_report_ready",
            "source_projection": None,
            "generated_materialization": None,
            "semantic_commit_evidence": "semantic_commit_evidence_ready",
            "ontology_execution_plan": "ontology_execution_plan_ready",
            "functioncall_capability_matrix": "functioncall_capability_executable",
            "execute_flag_preflight": "execute_flag_preflight_ready",
            "oig_commit_receipt": None,
            "head_move_applied_receipt": None,
            "runtime_package_index_patch": None,
            "output_materialization": None,
        },
    }


def _context() -> MetaProviderDeltaPipelineContext:
    return MetaProviderDeltaPipelineContext.create(
        request=SimpleNamespace(),
        package_payload={
            "package_name": "home-ontology",
            "manifest_path": "modules/home/structure/ontology/aware.toml",
        },
        semantic_contract_payload={"provider_key": "aware_meta"},
        manifest_path="modules/home/structure/ontology/aware.toml",
        current_delta_fingerprint="sha256:current",
        provider_delta_execution_context_preflight={
            "status": "execution_context_available"
        },
        baseline_dirty_preflight={"status": "baseline_dirty_preflight_ready"},
    )


def _typed_operation_plan() -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "reason": "meta_ocg_provider_delta_typed_operation_plan_ready",
        "typed_operations": (
            {
                "operation_key": "op:attribute:update",
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.attribute.update",
                "semantic_key": "home.Device/name",
                "ontology_subject_kind": "attribute",
                "baseline": {"object_id": "baseline-id"},
                "current": {"attribute_name": "name"},
            },
        ),
        "semantic_object_anchors": (),
        "blocked_operations": (),
    }
