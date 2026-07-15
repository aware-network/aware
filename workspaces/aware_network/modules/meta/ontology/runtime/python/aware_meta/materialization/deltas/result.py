from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aware_meta.materialization.deltas.baseline import (
    _BASELINE_COMMIT_REF_FIELDS,
    _baseline_commit_refs,
    _baseline_ref_missing_required_fields,
    _baseline_ref_payload,
    _mapping_value,
    _model_payload,
    _optional_text,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION,
    META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
    MetaProviderDeltaResultEnvelope,
)
from aware_meta.materialization.deltas.execution import (
    _baseline_context_missing_operation_execution_detail,
    _operation_execution_requested,
    _provider_delta_execute_flag_preflight,
    _provider_delta_execution_context_preflight,
)
from aware_meta.materialization.deltas.ontology_mutation_proof import (
    build_provider_delta_ontology_mutation_proof,
)


_SUPPORTED_DELTA_PROVIDER_KEY = "aware_meta"
_DELTA_COMMIT_REF_REQUIRED_FIELDS = (
    "source_code_package_id",
    "source_object_instance_graph_commit_id",
    "semantic_package_id",
    "semantic_branch_id",
    "semantic_object_instance_graph_commit_id",
)


def _provider_delta_result(
    *,
    request: object,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: Path,
    analysis: Any,
    current_delta_fingerprint: str,
    operation_plan: Mapping[str, object],
    operation_execution: Mapping[str, object],
    provider_delta_execution_context_preflight: Mapping[str, object],
    provider_delta_execute_flag_preflight: Mapping[str, object],
    provider_delta_oig_commit_receipt: Mapping[str, object],
    provider_delta_head_move_applied_receipt: Mapping[str, object],
    provider_delta_runtime_package_index_patch: Mapping[str, object],
    provider_delta_semantic_commit_evidence: Mapping[str, object],
    provider_delta_source_projection: Mapping[str, object] | None = None,
    provider_delta_generated_materialization: Mapping[str, object] | None = None,
    provider_delta_output_materialization: Mapping[str, object],
    provider_delta_head_move_plan: Mapping[str, object],
    provider_delta_typed_operation_plan: Mapping[str, object],
    provider_delta_mutation_plan: Mapping[str, object],
    provider_delta_ontology_execution_plan: Mapping[str, object],
    provider_delta_functioncall_capability_matrix: Mapping[str, object],
    baseline_dirty_preflight: Mapping[str, object],
    semantic_dirty_diff: Mapping[str, object],
    applied_semantic_keys: tuple[str, ...],
    stale_semantic_keys: tuple[str, ...],
) -> dict[str, object]:
    flag_requested = _operation_execution_requested(request=request)
    execute_preflight_ready = (
        provider_delta_execute_flag_preflight.get("status")
        == "execute_flag_preflight_ready"
    )
    commit_applied = (
        provider_delta_oig_commit_receipt.get("status") == "execute_flag_commit_applied"
    )
    commit_noop = (
        provider_delta_oig_commit_receipt.get("status") == "execute_flag_commit_noop"
    )
    commit_satisfied = commit_applied or commit_noop
    head_move_applied = provider_delta_head_move_plan.get("status") == (
        "head_move_applied"
    )
    runtime_package_index_patched = provider_delta_runtime_package_index_patch.get(
        "status"
    ) in {
        "runtime_package_index_patch_applied",
        "runtime_package_index_patch_empty",
    }
    semantic_commit_evidence_ready = (
        provider_delta_semantic_commit_evidence.get("status")
        == "semantic_commit_evidence_ready"
    )
    source_projection = dict(provider_delta_source_projection or {})
    generated_materialization = dict(provider_delta_generated_materialization or {})
    output_materialization = dict(provider_delta_output_materialization or {})
    output_materialized = _provider_delta_output_materialized(
        provider_delta_output_materialization=output_materialization,
    )
    result_status = _provider_delta_result_status(
        flag_requested=flag_requested,
        commit_applied=commit_satisfied,
        head_move_applied=head_move_applied,
        runtime_package_index_patched=runtime_package_index_patched,
        semantic_commit_evidence_ready=semantic_commit_evidence_ready,
        output_materialized=output_materialized,
    )
    fallback_reason = _provider_delta_fallback_reason(
        flag_requested=flag_requested,
        execute_preflight_ready=execute_preflight_ready,
        commit_status=_optional_text(provider_delta_oig_commit_receipt.get("status")),
        commit_applied=commit_satisfied,
        head_move_applied=head_move_applied,
        runtime_package_index_patched=runtime_package_index_patched,
        semantic_commit_evidence_ready=semantic_commit_evidence_ready,
        output_materialized=output_materialized,
        output_materialization_status=_optional_text(
            output_materialization.get("status")
        ),
    )
    commit_ref_payload = _commit_ref_payload(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path.as_posix(),
        result_status=result_status,
        head_refs=_mapping_value(
            provider_delta_head_move_applied_receipt.get("head_refs")
        ),
    )
    provider_delta_active_execution_rail = _mapping_value(
        provider_delta_execute_flag_preflight.get(
            "provider_delta_active_execution_rail"
        )
    )
    provider_delta_ontology_mutation_proof = (
        build_provider_delta_ontology_mutation_proof(
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            provider_delta_ontology_execution_plan=(
                provider_delta_ontology_execution_plan
            ),
            provider_delta_oig_commit_receipt=provider_delta_oig_commit_receipt,
            provider_delta_head_move_applied_receipt=(
                provider_delta_head_move_applied_receipt
            ),
        )
    )
    preview = analysis.change_preview
    details = {
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "mode": "meta_ocg_provider_delta_result_dry_run",
        "manifest_path": manifest_path.as_posix(),
        "source_files": analysis.source_files,
        "changed_source_files": preview.changed_source_files,
        "semantic_delta_count": len(preview.semantic_deltas),
        "semantic_change_count": len(preview.semantic_events),
        "current_delta_fingerprint": current_delta_fingerprint,
        "delta_operation_plan": dict(operation_plan),
        "provider_delta_operation_execution": dict(operation_execution),
        "provider_delta_execution_context_preflight": dict(
            provider_delta_execution_context_preflight
        ),
        "provider_delta_execute_flag_preflight": dict(
            provider_delta_execute_flag_preflight
        ),
        "provider_delta_active_execution_rail": (provider_delta_active_execution_rail),
        "active_execution_rail": _optional_text(
            provider_delta_active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(
            provider_delta_active_execution_rail.get("status")
        ),
        "active_execution_reason": _optional_text(
            provider_delta_active_execution_rail.get("reason")
        ),
        "provider_delta_oig_commit_receipt": dict(provider_delta_oig_commit_receipt),
        "provider_delta_head_move_applied_receipt": dict(
            provider_delta_head_move_applied_receipt
        ),
        "provider_delta_runtime_package_index_patch": dict(
            provider_delta_runtime_package_index_patch
        ),
        "provider_delta_semantic_commit_evidence": dict(
            provider_delta_semantic_commit_evidence
        ),
        "provider_delta_source_projection": source_projection,
        "provider_delta_source_projection_status": _optional_text(
            source_projection.get("status")
        ),
        "provider_delta_source_projection_ready": (
            source_projection.get("ready") is True
        ),
        "provider_delta_source_projection_projected_entry_count": (
            _int_mapping_value(
                source_projection,
                "projected_entry_count",
            )
        ),
        "provider_delta_generated_materialization": generated_materialization,
        "provider_delta_generated_materialization_status": _optional_text(
            generated_materialization.get("status")
        ),
        "provider_delta_generated_materialization_ready": (
            generated_materialization.get("ready") is True
        ),
        "provider_delta_generated_materialization_renderer_operation_count": (
            _int_mapping_value(
                generated_materialization,
                "renderer_operation_count",
            )
        ),
        "provider_delta_output_materialization": output_materialization,
        "artifact_ownership_receipts": _mapping_tuple(
            output_materialization.get("artifact_ownership_receipts")
        ),
        "language_post_step_receipts": _mapping_tuple(
            output_materialization.get("post_step_receipts")
        ),
        "language_materialization_tool_step_receipts": _mapping_tuple(
            output_materialization.get("tool_step_receipts")
        ),
        "language_materialization_tool_timings_s": dict(
            _mapping_value(output_materialization.get("tool_timings_s"))
        ),
        "language_materialization_runtime_to_language_cache": dict(
            _mapping_value(output_materialization.get("runtime_to_language_cache"))
        ),
        "provider_delta_head_move_plan": dict(provider_delta_head_move_plan),
        "provider_delta_typed_operation_plan": dict(
            provider_delta_typed_operation_plan
        ),
        "provider_delta_mutation_plan": dict(provider_delta_mutation_plan),
        "provider_delta_ontology_execution_plan": dict(
            provider_delta_ontology_execution_plan
        ),
        "provider_delta_ontology_mutation_proof": (
            provider_delta_ontology_mutation_proof
        ),
        "provider_delta_ontology_mutation_proof_status": _optional_text(
            provider_delta_ontology_mutation_proof.get("status")
        ),
        "provider_delta_ontology_mutation_proof_ready": (
            provider_delta_ontology_mutation_proof.get("ready") is True
        ),
        "provider_delta_ontology_mutation_proof_entry_count": (
            _int_mapping_value(
                provider_delta_ontology_mutation_proof,
                "mutation_entry_count",
            )
        ),
        "provider_delta_functioncall_capability_matrix": dict(
            provider_delta_functioncall_capability_matrix
        ),
        "baseline_dirty_preflight": dict(baseline_dirty_preflight),
        "semantic_dirty_diff": dict(semantic_dirty_diff),
        "production_execution_wired": (
            commit_satisfied
            and head_move_applied
            and runtime_package_index_patched
            and output_materialized
        ),
        **_request_detail(request=request),
    }
    return _normalize_provider_delta_result(
        {
            "contract_version": META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
            "status": result_status,
            "package": dict(package_payload),
            "semantic_contract": dict(semantic_contract_payload),
            "current_delta_fingerprint": current_delta_fingerprint,
            "applied_semantic_keys": (
                applied_semantic_keys if result_status == "succeeded" else ()
            ),
            "skipped_semantic_keys": (),
            "stale_semantic_keys": stale_semantic_keys,
            "implementation_required": False,
            "implementation_work_items": (),
            "fallback_reason": fallback_reason,
            "commit_ref_contract": commit_ref_payload["commit_ref_contract"],
            "bundle_package": commit_ref_payload["bundle_package"],
            "bundle_packages": (commit_ref_payload["bundle_package"],),
            "details": details,
            "error": None,
        }
    )


def _normalize_provider_delta_result(
    payload: Mapping[str, object],
) -> dict[str, object]:
    return MetaProviderDeltaResultEnvelope.from_payload(payload).evidence_payload()


def _provider_delta_result_status(
    *,
    flag_requested: bool,
    commit_applied: bool,
    head_move_applied: bool,
    runtime_package_index_patched: bool,
    semantic_commit_evidence_ready: bool,
    output_materialized: bool,
) -> str:
    if not flag_requested:
        return "succeeded"
    if (
        commit_applied
        and head_move_applied
        and runtime_package_index_patched
        and semantic_commit_evidence_ready
        and output_materialized
    ):
        return "succeeded"
    return "fallback_required"


def _provider_delta_fallback_reason(
    *,
    flag_requested: bool,
    execute_preflight_ready: bool,
    commit_status: str | None,
    commit_applied: bool,
    head_move_applied: bool,
    runtime_package_index_patched: bool,
    semantic_commit_evidence_ready: bool,
    output_materialized: bool,
    output_materialization_status: str | None,
) -> str | None:
    if not flag_requested:
        return None
    if (
        commit_applied
        and head_move_applied
        and runtime_package_index_patched
        and semantic_commit_evidence_ready
        and output_materialized
    ):
        return None
    if not execute_preflight_ready:
        return "meta_ocg_delta_execute_flag_preflight_blocked"
    if commit_status == "execute_flag_commit_blocked":
        return "meta_ocg_delta_execute_flag_commit_blocked"
    if commit_applied and not head_move_applied:
        return "meta_ocg_delta_head_move_applied_receipt_blocked"
    if commit_applied and head_move_applied and not runtime_package_index_patched:
        return "meta_ocg_delta_runtime_package_index_patch_blocked"
    if (
        commit_applied
        and head_move_applied
        and runtime_package_index_patched
        and not semantic_commit_evidence_ready
    ):
        return "meta_ocg_delta_semantic_commit_evidence_blocked"
    if (
        commit_applied
        and head_move_applied
        and runtime_package_index_patched
        and semantic_commit_evidence_ready
        and not output_materialized
    ):
        return (
            "meta_ocg_delta_outputs_not_materialized:"
            f"{output_materialization_status or 'unknown'}"
        )
    return "meta_ocg_delta_execute_flag_commit_failed"


def _provider_delta_output_materialized(
    *,
    provider_delta_output_materialization: Mapping[str, object],
) -> bool:
    if not provider_delta_output_materialization:
        return True
    status = _optional_text(provider_delta_output_materialization.get("status"))
    if status == "provider_delta_output_materialization_not_required":
        return True
    if status != "provider_delta_output_materialization_ready":
        return False
    artifact_count = provider_delta_output_materialization.get(
        "artifact_ownership_receipt_count"
    )
    if isinstance(artifact_count, bool):
        return False
    if isinstance(artifact_count, int):
        return artifact_count > 0
    return bool(
        _mapping_tuple(
            provider_delta_output_materialization.get("artifact_ownership_receipts")
        )
    )


def _mapping_tuple(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(dict(item) for item in value if isinstance(item, Mapping))


def _baseline_context_missing_result(
    *,
    request: object,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: str | None,
    baseline_dirty_preflight: Mapping[str, object],
) -> dict[str, object]:
    current_delta_fingerprint = str(getattr(request, "current_delta_fingerprint"))
    provider_delta_execution_context_preflight = (
        _provider_delta_execution_context_preflight(request=request)
    )
    execute_flag_preflight = _provider_delta_execute_flag_preflight(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        semantic_dirty_diff={},
        provider_delta_head_move_plan={},
        provider_delta_typed_operation_plan={},
        provider_delta_mutation_plan={},
    )
    operation_execution = _baseline_context_missing_operation_execution_detail(
        request=request,
        baseline_dirty_preflight=baseline_dirty_preflight,
        provider_delta_execute_flag_preflight=execute_flag_preflight,
    )
    provider_delta_active_execution_rail = _mapping_value(
        execute_flag_preflight.get("provider_delta_active_execution_rail")
    )
    operation_plan = {
        "plan_kind": "meta_ocg_provider_delta_operation_plan",
        "contract_version": "aware.meta.ocg.provider-delta-operation-plan.v1",
        "status": "blocked",
        "reason": (
            "meta_ocg_provider_delta_operation_execution_requires_commit_backed_baseline"
        ),
        "source": "aware_meta.provider_delta_request_preflight",
        "current_delta_fingerprint": current_delta_fingerprint,
        "changed_source_files": (),
        "affected_object_config_graph_keys": (),
        "affected_node_keys": (),
        "required_materializations": (),
        "graph_count": 0,
        "node_count": 0,
        "class_count": 0,
        "enum_count": 0,
        "function_count": 0,
        "relationship_count": 0,
        "semantic_delta_count": 0,
        "semantic_change_count": 0,
        "semantic_function_call_plan_count": 0,
        "operation_count": 0,
        "semantic_deltas": (),
        "semantic_changes": (),
        "semantic_function_call_plans": (),
        "provider_delta_execute_flag_preflight_status": (
            execute_flag_preflight["status"]
        ),
        "provider_delta_execute_flag_preflight_reason": (
            execute_flag_preflight["reason"]
        ),
        "provider_delta_execute_flag_preflight_blocker_count": (
            execute_flag_preflight["blocker_count"]
        ),
        "provider_delta_execute_flag_preflight": execute_flag_preflight,
        "provider_delta_active_execution_rail": provider_delta_active_execution_rail,
        "active_execution_rail": _optional_text(
            provider_delta_active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(
            provider_delta_active_execution_rail.get("status")
        ),
        "active_execution_reason": _optional_text(
            provider_delta_active_execution_rail.get("reason")
        ),
        "baseline_dirty_preflight": dict(baseline_dirty_preflight),
        "apply_wired": False,
        "production_execution_wired": False,
        "would_execute": False,
        "would_persist": False,
    }
    commit_ref_payload = _commit_ref_payload(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path,
        result_status="succeeded",
    )
    details = {
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "mode": "meta_ocg_provider_delta_result_dry_run",
        "manifest_path": manifest_path,
        "source_files": (),
        "changed_source_files": (),
        "semantic_delta_count": 0,
        "semantic_change_count": 0,
        "current_delta_fingerprint": current_delta_fingerprint,
        "delta_operation_plan": operation_plan,
        "provider_delta_operation_execution": operation_execution,
        "provider_delta_execution_context_preflight": (
            provider_delta_execution_context_preflight
        ),
        "provider_delta_execute_flag_preflight": execute_flag_preflight,
        "provider_delta_active_execution_rail": provider_delta_active_execution_rail,
        "active_execution_rail": _optional_text(
            provider_delta_active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(
            provider_delta_active_execution_rail.get("status")
        ),
        "active_execution_reason": _optional_text(
            provider_delta_active_execution_rail.get("reason")
        ),
        "baseline_dirty_preflight": dict(baseline_dirty_preflight),
        "production_execution_wired": False,
        **_request_detail(request=request),
    }
    return _normalize_provider_delta_result(
        {
            "contract_version": META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
            "status": "succeeded",
            "package": dict(package_payload),
            "semantic_contract": dict(semantic_contract_payload),
            "current_delta_fingerprint": current_delta_fingerprint,
            "applied_semantic_keys": (),
            "skipped_semantic_keys": (),
            "stale_semantic_keys": (),
            "implementation_required": False,
            "implementation_work_items": (),
            "fallback_reason": None,
            "commit_ref_contract": commit_ref_payload["commit_ref_contract"],
            "bundle_package": commit_ref_payload["bundle_package"],
            "bundle_packages": (commit_ref_payload["bundle_package"],),
            "details": details,
            "error": None,
        }
    )


def _fallback_result(
    *,
    request: object,
    fallback_reason: str,
    details: Mapping[str, object] | None = None,
) -> dict[str, object]:
    package = getattr(request, "package")
    semantic_contract = getattr(request, "semantic_contract")
    current_delta_fingerprint = str(getattr(request, "current_delta_fingerprint"))
    package_payload = _model_payload(package)
    semantic_contract_payload = _model_payload(semantic_contract)
    manifest_path = _optional_text(
        (details or {}).get("manifest_path")
        if details is not None
        else package_payload.get("manifest_path")
    )
    if manifest_path is None:
        manifest_path = _optional_text(package_payload.get("manifest_path"))
    commit_ref_payload = _commit_ref_payload(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path,
        result_status="fallback_required",
    )
    payload_details: dict[str, object] = {
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "mode": "meta_ocg_provider_delta_result_dry_run",
        "production_execution_wired": False,
    }
    if details:
        payload_details.update(dict(details))
    return _normalize_provider_delta_result(
        {
            "contract_version": META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
            "status": "fallback_required",
            "package": package_payload,
            "semantic_contract": semantic_contract_payload,
            "current_delta_fingerprint": current_delta_fingerprint,
            "applied_semantic_keys": (),
            "skipped_semantic_keys": (),
            "stale_semantic_keys": (),
            "implementation_required": False,
            "implementation_work_items": (),
            "fallback_reason": fallback_reason,
            "commit_ref_contract": commit_ref_payload["commit_ref_contract"],
            "bundle_package": commit_ref_payload["bundle_package"],
            "bundle_packages": (commit_ref_payload["bundle_package"],),
            "details": payload_details,
            "error": None,
        }
    )


def _commit_ref_payload(
    *,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: str | None,
    result_status: str,
    head_refs: Mapping[str, object] | None = None,
) -> dict[str, dict[str, object]]:
    bundle_package = _bundle_package_contract(
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path,
        head_refs=head_refs or {},
    )
    missing_required_fields = [
        field_name
        for field_name in _DELTA_COMMIT_REF_REQUIRED_FIELDS
        if not bundle_package.get(field_name)
    ]
    available_fields = [
        field_name
        for field_name in _DELTA_COMMIT_REF_REQUIRED_FIELDS
        if bundle_package.get(field_name)
    ]
    receipt_persistence_contract_ready = (
        result_status == "succeeded" and not missing_required_fields
    )
    if result_status == "succeeded":
        status = (
            "ready" if receipt_persistence_contract_ready else "missing_durable_refs"
        )
        reason = (
            "meta_ocg_provider_delta_commit_refs_complete"
            if status == "ready"
            else "meta_ocg_provider_delta_dry_run_does_not_materialize_commits"
        )
    else:
        status = "not_applicable_fallback_required"
        reason = "meta_ocg_provider_delta_result_requires_full_rebuild"
    contract: dict[str, object] = {
        "contract_version": META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION,
        "contract_kind": "provider_delta_semantic_package_commit_ref_contract",
        "status": status,
        "reason": reason,
        "required_fields": list(_DELTA_COMMIT_REF_REQUIRED_FIELDS),
        "available_fields": available_fields,
        "missing_required_fields": missing_required_fields,
        "receipt_persistence_contract_ready": receipt_persistence_contract_ready,
        "production_execution_wired": False,
        "would_persist": False,
    }
    bundle_package["commit_ref_contract_version"] = (
        META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION
    )
    bundle_package["commit_ref_contract_status"] = status
    bundle_package["commit_ref_contract_reason"] = reason
    bundle_package["receipt_persistence_contract_ready"] = (
        receipt_persistence_contract_ready
    )
    return {
        "commit_ref_contract": contract,
        "bundle_package": bundle_package,
    }


def _bundle_package_contract(
    *,
    package_payload: Mapping[str, object],
    semantic_contract_payload: Mapping[str, object],
    manifest_path: str | None,
    head_refs: Mapping[str, object],
) -> dict[str, object]:
    package_name = _optional_text(package_payload.get("package_name"))
    return {
        "package_key": package_name,
        "package_kind": "object_config_graph",
        "manifest_toml_path": manifest_path,
        "semantic_owner_module": "aware_meta",
        "semantic_package_kind": "object_config_graph_package",
        "semantic_contract_provider_key": semantic_contract_payload.get("provider_key"),
        "semantic_contract_role": semantic_contract_payload.get("role"),
        "semantic_contract_name": semantic_contract_payload.get("name"),
        "semantic_projection_name": head_refs.get("semantic_projection_name"),
        "semantic_root_kind": "object_config_graph",
        "source_code_package_id": package_payload.get("source_code_package_id"),
        "source_object_instance_graph_commit_id": head_refs.get(
            "source_object_instance_graph_commit_id"
        ),
        "semantic_package_id": head_refs.get("semantic_package_id"),
        "semantic_branch_id": head_refs.get("semantic_branch_id"),
        "semantic_projection_hash": head_refs.get("semantic_projection_hash"),
        "semantic_head_commit_id": head_refs.get("semantic_package_commit_id"),
        "semantic_object_instance_graph_commit_id": head_refs.get(
            "semantic_object_instance_graph_commit_id"
        ),
        "semantic_root_id": head_refs.get("semantic_root_id"),
        "semantic_root_object_instance_graph_commit_id": head_refs.get(
            "semantic_root_object_instance_graph_commit_id"
        ),
    }


def _request_detail(*, request: object) -> dict[str, object]:
    hints = getattr(request, "delta_cause_hints", None)
    changed_paths = _top_changed_path_payloads(request=request)
    baseline_refs = _baseline_commit_refs(request=request)
    baseline_ref = _baseline_ref_payload(request=request)
    missing_baseline_fields = tuple(
        field_name
        for field_name in _BASELINE_COMMIT_REF_FIELDS
        if not baseline_refs.get(field_name)
    )
    previous_evidence = getattr(request, "previous_materialization_evidence", None)
    previous_evidence_source = None
    if isinstance(previous_evidence, Mapping):
        previous_evidence_source = _optional_text(
            previous_evidence.get("evidence_source")
        )
    return {
        "delta_cause_hints": {
            "changed_path_count": _int_attr(hints, "changed_path_count"),
            "source_owned_path_count": _int_attr(hints, "source_owned_path_count"),
            "generated_fallout_path_count": _int_attr(
                hints,
                "generated_fallout_path_count",
            ),
            "top_changed_path_limit": _int_attr(hints, "top_changed_path_limit"),
            "top_changed_paths": changed_paths,
        },
        "baseline_commit_refs": baseline_refs,
        "baseline_commit_ref_missing_required_fields": missing_baseline_fields,
        "baseline_ref": baseline_ref,
        "baseline_ref_missing_required_fields": (
            _baseline_ref_missing_required_fields(baseline_ref=baseline_ref)
        ),
        "previous_materialization_evidence_source": previous_evidence_source,
    }


def _top_changed_path_payloads(*, request: object) -> tuple[dict[str, object], ...]:
    hints = getattr(request, "delta_cause_hints", None)
    raw_paths = getattr(hints, "top_changed_paths", ())
    if not isinstance(raw_paths, (list, tuple)):
        return ()
    return tuple(_model_payload(path) for path in raw_paths)


def _int_attr(value: object, key: str) -> int:
    if value is None:
        return 0
    raw_value = getattr(value, key, None)
    if isinstance(raw_value, int):
        return raw_value
    try:
        return int(str(raw_value))
    except Exception:
        return 0


def _int_mapping_value(value: Mapping[str, object], key: str) -> int:
    raw_value = value.get(key)
    if isinstance(raw_value, bool):
        return 0
    if isinstance(raw_value, int):
        return raw_value
    try:
        return int(str(raw_value))
    except Exception:
        return 0


__all__ = [
    "_baseline_context_missing_result",
    "_commit_ref_payload",
    "_fallback_result",
    "_provider_delta_result",
]
