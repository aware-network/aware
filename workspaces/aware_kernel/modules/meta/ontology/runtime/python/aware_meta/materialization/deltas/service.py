from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

from aware_code.semantic_capability import SemanticCapabilityFunctionCallPlan
from aware_code_ontology.code.code_plan import CodePackageDelta
from aware_meta.materialization.semantic_function_call_resolution import (
    META_OCG_BUILD_FUNCTION_REF,
    META_OCG_CREATE_NODE_FUNCTION_REF,
    META_OCG_PACKAGE_BUILD_FUNCTION_REF,
)
from aware_meta.semantic_analysis import (
    MetaOcgSemanticChangePreview,
    MetaOcgSemanticAnalysisResult,
    analyze_meta_ocg_code_package_delta,
)
from aware_meta.materialization.deltas.baseline import (
    _baseline_dirty_preflight,
    _baseline_semantic_object_index_from_oig,
    _int_payload_value,
)
from aware_meta.materialization.deltas.contracts import (
    META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION,
    META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION,
)
from aware_meta.materialization.deltas.capability_matrix import (
    build_provider_delta_functioncall_capability_matrix,
)
from aware_meta.materialization.deltas.dirty_diff import (
    _baseline_dirty_preflight_with_semantic_dirty_diff,
    _semantic_dirty_diff_from_analysis,
)
from aware_meta.materialization.deltas.execution import (
    _operation_execution_detail,
    _operation_execution_requested,
    _provider_delta_execute_flag_preflight,
    _provider_delta_execution_context_preflight,
    _provider_delta_head_move_applied_receipt,
    _provider_delta_oig_commit_receipt,
)
from aware_meta.materialization.deltas.change_evidence import (
    _provider_delta_semantic_change_report,
    _provider_delta_semantic_commit_evidence,
)
from aware_meta.materialization.deltas.head_move import (
    _operation_plan_with_provider_delta_head_move_plan,
    _provider_delta_head_move_plan,
)
from aware_meta.materialization.deltas.ocg_genesis import (
    ocg_genesis_preflight_from_provider_delta_request,
    ocg_genesis_semantic_dirty_diff_from_preflight,
)
from aware_meta.materialization.deltas.index_patch import (
    _provider_delta_runtime_package_index_patch_receipt,
)
from aware_meta.materialization.deltas.ontology_execution.service import (
    build_provider_delta_ontology_execution_plan,
)
from aware_meta.materialization.deltas.pipeline import (
    MetaProviderDeltaPipelineContext,
)
from aware_meta.materialization.deltas.result import (
    _baseline_context_missing_result,
    _fallback_result,
    _provider_delta_result,
)
from aware_meta.materialization.deltas.generated_materialization import (
    provider_delta_generated_materialization_stage,
)
from aware_meta.materialization.deltas.source_projection import (
    provider_delta_source_projection_stage,
)
from aware_meta.materialization.deltas import mutation_plan as _mutation_plan
from aware_meta.materialization.deltas.typed_operations import (
    _provider_delta_typed_operation_plan,
    _semantic_change_payload,
)


_SUPPORTED_DELTA_PROVIDER_KEY = "aware_meta"
_MUTATION_PLAN_CONTRACT_VERSION = META_PROVIDER_DELTA_MUTATION_PLAN_CONTRACT_VERSION
_MUTATION_STEP_CONTRACT_VERSION = META_PROVIDER_DELTA_MUTATION_STEP_CONTRACT_VERSION
_PROVIDER_DELTA_STAGE_TIMINGS_CONTRACT_VERSION = (
    "aware.meta.provider-delta-stage-timings.v1"
)
META_PROVIDER_DELTA_CLASS_CONFIG_CREATE_COLLECTION_ATTRIBUTE_FUNCTION_REF = (
    _mutation_plan.META_PROVIDER_DELTA_CLASS_CONFIG_CREATE_COLLECTION_ATTRIBUTE_FUNCTION_REF
)
META_PROVIDER_DELTA_FUNCTION_CONFIG_ADD_COLLECTION_ATTRIBUTE_FUNCTION_REF = (
    _mutation_plan.META_PROVIDER_DELTA_FUNCTION_CONFIG_ADD_COLLECTION_ATTRIBUTE_FUNCTION_REF
)
_mutation_step_from_typed_operation = _mutation_plan._mutation_step_from_typed_operation


class _ProviderDeltaStageTimings:
    def __init__(self) -> None:
        self._started_at = perf_counter()
        self._stages_s: dict[str, float] = {}
        self._stage_order: list[str] = []

    @contextmanager
    def record(self, stage_name: str) -> Iterator[None]:
        started_at = perf_counter()
        try:
            yield
        finally:
            self.record_duration(
                stage_name=stage_name,
                duration_s=perf_counter() - started_at,
            )

    def record_duration(self, *, stage_name: str, duration_s: float) -> None:
        if stage_name not in self._stages_s:
            self._stage_order.append(stage_name)
        self._stages_s[stage_name] = round(
            max(float(self._stages_s.get(stage_name, 0.0)) + duration_s, 0.0),
            6,
        )

    def payload(self) -> dict[str, object]:
        total_s = round(max(perf_counter() - self._started_at, 0.0), 6)
        stages_s = {
            stage_name: self._stages_s[stage_name]
            for stage_name in self._stage_order
            if stage_name in self._stages_s
        }
        return {
            "timing_kind": "meta_provider_delta_stage_timings",
            "contract_version": _PROVIDER_DELTA_STAGE_TIMINGS_CONTRACT_VERSION,
            "stage_order": tuple(self._stage_order),
            "stage_count": len(self._stage_order),
            "stages_s": stages_s,
            "total_s": total_s,
        }


async def materialize_delta(request: object) -> dict[str, object]:
    stage_timings = _ProviderDeltaStageTimings()
    with stage_timings.record("request_identity"):
        package = getattr(request, "package")
        semantic_contract = getattr(request, "semantic_contract")
        current_delta_fingerprint = str(getattr(request, "current_delta_fingerprint"))
        package_payload = _model_payload(package)
        semantic_contract_payload = _model_payload(semantic_contract)
    with stage_timings.record("provider_contract_check"):
        provider_key = str(semantic_contract_payload.get("provider_key") or "")
    if provider_key != _SUPPORTED_DELTA_PROVIDER_KEY:
        result_started_at = perf_counter()
        result = _fallback_result(
            request=request,
            fallback_reason="meta_ocg_delta_semantic_contract_unsupported",
            details={"provider_key": provider_key},
        )
        stage_timings.record_duration(
            stage_name="result_assembly",
            duration_s=perf_counter() - result_started_at,
        )
        return _with_provider_delta_stage_timings(
            result=result,
            stage_timings=stage_timings,
        )

    with stage_timings.record("execution_context_preflight"):
        provider_delta_execution_context_preflight = (
            _provider_delta_execution_context_preflight(request=request)
        )
    with stage_timings.record("baseline_dirty_preflight"):
        baseline_dirty_preflight = await _baseline_dirty_preflight(request=request)
    with stage_timings.record("execution_baseline_gate"):
        empty_lane_genesis_requested = _provider_delta_empty_lane_genesis_requested(
            request=request
        )
        baseline_missing_for_execution = (
            _operation_execution_requested(request=request)
            and not bool(baseline_dirty_preflight["commit_backed_baseline_available"])
            and not empty_lane_genesis_requested
        )
    if baseline_missing_for_execution:
        result_started_at = perf_counter()
        result = _baseline_context_missing_result(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            manifest_path=_optional_text(package_payload.get("manifest_path")),
            baseline_dirty_preflight=baseline_dirty_preflight,
        )
        stage_timings.record_duration(
            stage_name="result_assembly",
            duration_s=perf_counter() - result_started_at,
        )
        return _with_provider_delta_stage_timings(
            result=result,
            stage_timings=stage_timings,
        )

    with stage_timings.record("manifest_resolution"):
        manifest_path = _resolve_delta_manifest_path(
            package_payload.get("manifest_path")
        )
    if manifest_path is None:
        result_started_at = perf_counter()
        result = _fallback_result(
            request=request,
            fallback_reason="meta_ocg_delta_manifest_unavailable",
            details={"manifest_path": package_payload.get("manifest_path")},
        )
        stage_timings.record_duration(
            stage_name="result_assembly",
            duration_s=perf_counter() - result_started_at,
        )
        return _with_provider_delta_stage_timings(
            result=result,
            stage_timings=stage_timings,
        )

    try:
        with stage_timings.record("code_delta_normalization"):
            delta = _code_package_delta_from_provider_delta_request(
                request=request,
            )
    except Exception as exc:
        result_started_at = perf_counter()
        result = _fallback_result(
            request=request,
            fallback_reason="meta_ocg_delta_request_normalization_failed",
            details={
                "manifest_path": manifest_path.as_posix(),
                "error": f"{type(exc).__name__}: {exc}",
            },
        )
        stage_timings.record_duration(
            stage_name="result_assembly",
            duration_s=perf_counter() - result_started_at,
        )
        return _with_provider_delta_stage_timings(
            result=result,
            stage_timings=stage_timings,
        )
    if empty_lane_genesis_requested and delta is None:
        result_started_at = perf_counter()
        result = _fallback_result(
            request=request,
            fallback_reason="meta_ocg_empty_lane_genesis_code_delta_unavailable",
            details={
                "manifest_path": manifest_path.as_posix(),
                "provider_delta_lane_state_status": "empty_lane",
            },
        )
        stage_timings.record_duration(
            stage_name="result_assembly",
            duration_s=perf_counter() - result_started_at,
        )
        return _with_provider_delta_stage_timings(
            result=result,
            stage_timings=stage_timings,
        )
    with stage_timings.record("semantic_analysis"):
        if empty_lane_genesis_requested:
            assert delta is not None
            analysis = _meta_ocg_delta_analysis_for_empty_lane_genesis(
                package_root=manifest_path.parent,
                manifest_path=manifest_path,
                code_package_delta=delta,
            )
        else:
            analysis = _empty_meta_ocg_delta_analysis(
                package_root=manifest_path.parent,
                manifest_path=manifest_path,
                code_package_delta=delta,
            )
    with stage_timings.record("pipeline_context_initialization"):
        pipeline_context = MetaProviderDeltaPipelineContext.create(
            request=request,
            package_payload=package_payload,
            semantic_contract_payload=semantic_contract_payload,
            manifest_path=manifest_path.as_posix(),
            current_delta_fingerprint=current_delta_fingerprint,
            provider_delta_execution_context_preflight=(
                provider_delta_execution_context_preflight
            ),
            baseline_dirty_preflight=baseline_dirty_preflight,
        )
        applied_semantic_keys = ()

    with stage_timings.record("function_call_plan"):
        function_call_plans = _function_call_plans_from_analysis(analysis=analysis)
    with stage_timings.record("empty_lane_genesis_preflight"):
        provider_delta_empty_lane_genesis_preflight = (
            ocg_genesis_preflight_from_provider_delta_request(
                request=request,
                analysis=analysis,
            )
        )
        empty_lane_genesis_ready = (
            provider_delta_empty_lane_genesis_preflight.get("status")
            == "ocg_genesis_consumer_ready"
        )
    with stage_timings.record("semantic_dirty_diff"):
        semantic_dirty_diff = (
            ocg_genesis_semantic_dirty_diff_from_preflight(
                preflight=provider_delta_empty_lane_genesis_preflight,
                current_delta_fingerprint=current_delta_fingerprint,
            )
            if empty_lane_genesis_ready
            else _semantic_dirty_diff_from_analysis(
                analysis=analysis,
                current_delta_fingerprint=current_delta_fingerprint,
                baseline_dirty_preflight=baseline_dirty_preflight,
            )
        )
        pipeline_context = pipeline_context.with_semantic_dirty_diff(
            semantic_dirty_diff
        )
        semantic_dirty_diff = pipeline_context.dirty_diff.evidence_payload()
        stale_semantic_keys = pipeline_context.dirty_diff.stale_semantic_keys
    with stage_timings.record("head_move_plan_initial"):
        provider_delta_head_move_plan = _provider_delta_head_move_plan(
            request=request,
            semantic_dirty_diff=semantic_dirty_diff,
        )
        pipeline_context = pipeline_context.with_head_move_plan(
            provider_delta_head_move_plan
        )
    with stage_timings.record("typed_operation_plan"):
        provider_delta_typed_operation_plan = (
            _mapping_value(
                provider_delta_empty_lane_genesis_preflight.get("typed_operation_plan")
            )
            if empty_lane_genesis_ready
            else _provider_delta_typed_operation_plan(
                semantic_dirty_diff=semantic_dirty_diff,
                provider_delta_head_move_plan=(
                    pipeline_context.provider_delta_head_move_plan
                ),
                semantic_change_payloads=tuple(
                    event.evidence_payload()
                    for event in analysis.change_preview.semantic_events
                ),
                function_call_plans=function_call_plans,
            )
        )
        pipeline_context = pipeline_context.with_typed_operation_plan(
            provider_delta_typed_operation_plan
        )
    with stage_timings.record("semantic_change_report"):
        provider_delta_semantic_change_report = _provider_delta_semantic_change_report(
            semantic_dirty_diff=semantic_dirty_diff,
            provider_delta_typed_operation_plan=(
                pipeline_context.provider_delta_typed_operation_plan
            ),
        )
        pipeline_context = pipeline_context.with_semantic_change_report(
            provider_delta_semantic_change_report
        )
        provider_delta_semantic_change_report = (
            pipeline_context.semantic_change_report.evidence_payload()
        )
    with stage_timings.record("source_projection"):
        provider_delta_source_projection = provider_delta_source_projection_stage(
            package_payload=package_payload,
            manifest_path=manifest_path,
            current_delta_fingerprint=current_delta_fingerprint,
            provider_delta_semantic_change_report=(
                provider_delta_semantic_change_report
            ),
            provider_delta_typed_operation_plan=(
                pipeline_context.provider_delta_typed_operation_plan
            ),
            code_package_delta=delta,
        )
        pipeline_context = pipeline_context.with_source_projection(
            provider_delta_source_projection
        )
    with stage_timings.record("generated_materialization"):
        provider_delta_generated_materialization = (
            provider_delta_generated_materialization_stage(
                package_payload=package_payload,
                manifest_path=manifest_path,
                current_delta_fingerprint=current_delta_fingerprint,
                provider_delta_semantic_change_report=(
                    provider_delta_semantic_change_report
                ),
                provider_delta_typed_operation_plan=(
                    pipeline_context.provider_delta_typed_operation_plan
                ),
                code_package_delta=delta,
            )
        )
        pipeline_context = pipeline_context.with_generated_materialization(
            provider_delta_generated_materialization
        )
    with stage_timings.record("mutation_plan"):
        provider_delta_mutation_plan = _provider_delta_mutation_plan(
            provider_delta_typed_operation_plan=(
                pipeline_context.provider_delta_typed_operation_plan
            ),
        )
        pipeline_context = pipeline_context.with_mutation_plan(
            provider_delta_mutation_plan
        )
        provider_delta_mutation_plan = pipeline_context.mutation_plan.evidence_payload()
    with stage_timings.record("ontology_execution_plan"):
        provider_delta_ontology_execution_plan = (
            _mapping_value(
                provider_delta_empty_lane_genesis_preflight.get(
                    "ontology_execution_plan"
                ),
            )
            if empty_lane_genesis_ready
            else build_provider_delta_ontology_execution_plan(
                request=request,
                provider_delta_typed_operation_plan=(
                    pipeline_context.provider_delta_typed_operation_plan
                ),
            )
        )
        pipeline_context = pipeline_context.with_ontology_execution_plan(
            provider_delta_ontology_execution_plan
        )
    with stage_timings.record("functioncall_capability_matrix"):
        provider_delta_functioncall_capability_matrix = (
            _mapping_value(
                provider_delta_empty_lane_genesis_preflight.get(
                    "functioncall_capability_matrix"
                ),
            )
            if empty_lane_genesis_ready
            else build_provider_delta_functioncall_capability_matrix(
                provider_delta_typed_operation_plan=(
                    pipeline_context.provider_delta_typed_operation_plan
                ),
                provider_delta_ontology_execution_plan=(
                    pipeline_context.provider_delta_ontology_execution_plan
                ),
            )
        )
        pipeline_context = pipeline_context.with_functioncall_capability_matrix(
            provider_delta_functioncall_capability_matrix
        )
    with stage_timings.record("baseline_dirty_preflight_enrichment"):
        baseline_dirty_preflight = _baseline_dirty_preflight_with_semantic_dirty_diff(
            baseline_dirty_preflight=baseline_dirty_preflight,
            semantic_dirty_diff=semantic_dirty_diff,
        )
        pipeline_context = pipeline_context.with_baseline_dirty_preflight(
            baseline_dirty_preflight
        )
    with stage_timings.record("execute_flag_preflight"):
        provider_delta_execute_flag_preflight = _provider_delta_execute_flag_preflight(
            request=request,
            baseline_dirty_preflight=pipeline_context.baseline_dirty_preflight,
            semantic_dirty_diff=semantic_dirty_diff,
            provider_delta_head_move_plan=(
                pipeline_context.provider_delta_head_move_plan
            ),
            provider_delta_typed_operation_plan=(
                pipeline_context.provider_delta_typed_operation_plan
            ),
            provider_delta_mutation_plan=provider_delta_mutation_plan,
            provider_delta_ontology_execution_plan=(
                pipeline_context.provider_delta_ontology_execution_plan
            ),
            provider_delta_functioncall_capability_matrix=(
                pipeline_context.provider_delta_functioncall_capability_matrix
            ),
        )
        pipeline_context = pipeline_context.with_execute_flag_preflight(
            provider_delta_execute_flag_preflight
        )
    with stage_timings.record("operation_plan"):
        operation_plan = _operation_plan_from_analysis(
            analysis=analysis,
            current_delta_fingerprint=current_delta_fingerprint,
            function_call_plans=function_call_plans,
            baseline_dirty_preflight=pipeline_context.baseline_dirty_preflight,
            semantic_dirty_diff=semantic_dirty_diff,
            provider_delta_head_move_plan=(
                pipeline_context.provider_delta_head_move_plan
            ),
            provider_delta_typed_operation_plan=(
                pipeline_context.provider_delta_typed_operation_plan
            ),
            provider_delta_mutation_plan=provider_delta_mutation_plan,
            provider_delta_ontology_execution_plan=(
                pipeline_context.provider_delta_ontology_execution_plan
            ),
            provider_delta_functioncall_capability_matrix=(
                pipeline_context.provider_delta_functioncall_capability_matrix
            ),
            provider_delta_execute_flag_preflight=(
                pipeline_context.provider_delta_execute_flag_preflight
            ),
            provider_delta_empty_lane_genesis_preflight=(
                provider_delta_empty_lane_genesis_preflight
            ),
        )
    with stage_timings.record("oig_commit_receipt"):
        provider_delta_oig_commit_receipt = await _provider_delta_oig_commit_receipt(
            request=request,
            baseline_dirty_preflight=pipeline_context.baseline_dirty_preflight,
            provider_delta_mutation_plan=provider_delta_mutation_plan,
            provider_delta_ontology_execution_plan=(
                pipeline_context.provider_delta_ontology_execution_plan
            ),
            provider_delta_execute_flag_preflight=(
                pipeline_context.provider_delta_execute_flag_preflight
            ),
        )
        pipeline_context = pipeline_context.with_oig_commit_receipt(
            provider_delta_oig_commit_receipt
        )
    with stage_timings.record("head_move_applied_receipt"):
        provider_delta_head_move_applied_receipt = (
            _provider_delta_head_move_applied_receipt(
                request=request,
                baseline_dirty_preflight=pipeline_context.baseline_dirty_preflight,
                provider_delta_oig_commit_receipt=(
                    pipeline_context.provider_delta_oig_commit_receipt
                ),
            )
        )
        pipeline_context = pipeline_context.with_head_move_applied_receipt(
            provider_delta_head_move_applied_receipt
        )
    with stage_timings.record("head_move_plan_final"):
        provider_delta_head_refs = pipeline_context.head_move_applied_receipt.head_refs
        provider_delta_head_move_plan = _provider_delta_head_move_plan(
            request=request,
            semantic_dirty_diff=semantic_dirty_diff,
            head_refs=(
                provider_delta_head_refs
                if provider_delta_head_refs.get("head_ref_status")
                == "head_refs_available"
                else None
            ),
        )
        pipeline_context = pipeline_context.with_head_move_plan(
            provider_delta_head_move_plan
        )
        operation_plan = _operation_plan_with_provider_delta_head_move_plan(
            operation_plan=operation_plan,
            provider_delta_head_move_plan=(
                pipeline_context.provider_delta_head_move_plan
            ),
        )
    with stage_timings.record("runtime_package_index_patch"):
        provider_delta_runtime_package_index_patch = (
            _provider_delta_runtime_package_index_patch_receipt(
                request=request,
                provider_delta_typed_operation_plan=(
                    pipeline_context.provider_delta_typed_operation_plan
                ),
                provider_delta_head_move_applied_receipt=(
                    pipeline_context.provider_delta_head_move_applied_receipt
                ),
                provider_delta_oig_commit_receipt=(
                    pipeline_context.provider_delta_oig_commit_receipt
                ),
                current_delta_fingerprint=current_delta_fingerprint,
            )
        )
        pipeline_context = pipeline_context.with_runtime_package_index_patch(
            provider_delta_runtime_package_index_patch
        )
    with stage_timings.record("semantic_commit_evidence"):
        provider_delta_semantic_commit_evidence = (
            _provider_delta_semantic_commit_evidence(
                provider_delta_typed_operation_plan=(
                    pipeline_context.provider_delta_typed_operation_plan
                ),
                provider_delta_head_move_plan=(
                    pipeline_context.provider_delta_head_move_plan
                ),
                provider_delta_head_move_applied_receipt=(
                    pipeline_context.provider_delta_head_move_applied_receipt
                ),
                provider_delta_oig_commit_receipt=(
                    pipeline_context.provider_delta_oig_commit_receipt
                ),
            )
        )
        pipeline_context = pipeline_context.with_semantic_commit_evidence(
            provider_delta_semantic_commit_evidence
        )
    with stage_timings.record("output_materialization"):
        from aware_meta.materialization.workspace_provider import (  # noqa: WPS433
            materialize_provider_delta_outputs,
        )

        provider_delta_output_materialization = (
            await materialize_provider_delta_outputs(
                request=request,
                provider_delta_head_move_applied_receipt=(
                    pipeline_context.provider_delta_head_move_applied_receipt
                ),
                provider_delta_oig_commit_receipt=(
                    pipeline_context.provider_delta_oig_commit_receipt
                ),
                provider_delta_typed_operation_plan=(
                    pipeline_context.provider_delta_typed_operation_plan
                ),
            )
        )
        pipeline_context = pipeline_context.with_output_materialization(
            provider_delta_output_materialization
        )
    with stage_timings.record("operation_plan_receipts"):
        operation_plan = _operation_plan_with_pipeline_context_receipts(
            operation_plan=operation_plan,
            pipeline_context=pipeline_context,
        )
        stage_payloads = pipeline_context.stage_payloads()
    with stage_timings.record("operation_execution_detail"):
        operation_execution = _operation_execution_detail(
            request=request,
            function_call_plans=function_call_plans,
            baseline_dirty_preflight=stage_payloads["baseline_dirty_preflight"],
            provider_delta_execute_flag_preflight=(
                stage_payloads["provider_delta_execute_flag_preflight"]
            ),
            provider_delta_oig_commit_receipt=(
                stage_payloads["provider_delta_oig_commit_receipt"]
            ),
        )
    result_started_at = perf_counter()
    result = _provider_delta_result(
        request=request,
        package_payload=package_payload,
        semantic_contract_payload=semantic_contract_payload,
        manifest_path=manifest_path,
        analysis=analysis,
        current_delta_fingerprint=current_delta_fingerprint,
        operation_plan=operation_plan,
        operation_execution=operation_execution,
        provider_delta_execution_context_preflight=(
            stage_payloads["provider_delta_execution_context_preflight"]
        ),
        provider_delta_execute_flag_preflight=(
            stage_payloads["provider_delta_execute_flag_preflight"]
        ),
        provider_delta_oig_commit_receipt=(
            stage_payloads["provider_delta_oig_commit_receipt"]
        ),
        provider_delta_head_move_applied_receipt=(
            stage_payloads["provider_delta_head_move_applied_receipt"]
        ),
        provider_delta_runtime_package_index_patch=(
            stage_payloads["provider_delta_runtime_package_index_patch"]
        ),
        provider_delta_semantic_commit_evidence=(
            stage_payloads["provider_delta_semantic_commit_evidence"]
        ),
        provider_delta_source_projection=(
            stage_payloads["provider_delta_source_projection"]
        ),
        provider_delta_generated_materialization=(
            stage_payloads["provider_delta_generated_materialization"]
        ),
        provider_delta_output_materialization=(
            stage_payloads["provider_delta_output_materialization"]
        ),
        provider_delta_head_move_plan=stage_payloads["provider_delta_head_move_plan"],
        provider_delta_typed_operation_plan=(
            stage_payloads["provider_delta_typed_operation_plan"]
        ),
        provider_delta_mutation_plan=stage_payloads["provider_delta_mutation_plan"],
        provider_delta_ontology_execution_plan=(
            stage_payloads["provider_delta_ontology_execution_plan"]
        ),
        provider_delta_functioncall_capability_matrix=(
            stage_payloads["provider_delta_functioncall_capability_matrix"]
        ),
        baseline_dirty_preflight=stage_payloads["baseline_dirty_preflight"],
        semantic_dirty_diff=stage_payloads["semantic_dirty_diff"],
        applied_semantic_keys=applied_semantic_keys,
        stale_semantic_keys=stale_semantic_keys,
    )
    stage_timings.record_duration(
        stage_name="result_assembly",
        duration_s=perf_counter() - result_started_at,
    )
    return _with_provider_delta_stage_timings(
        result=result,
        stage_timings=stage_timings,
    )


def _with_provider_delta_stage_timings(
    *,
    result: dict[str, object],
    stage_timings: _ProviderDeltaStageTimings,
) -> dict[str, object]:
    timing_payload = stage_timings.payload()
    details = result.get("details")
    details_payload = dict(details) if isinstance(details, Mapping) else {}
    stages_s = timing_payload.get("stages_s")
    details_payload["provider_delta_stage_timings"] = timing_payload
    details_payload["provider_delta_stage_timings_s"] = (
        dict(stages_s) if isinstance(stages_s, Mapping) else {}
    )
    return {**result, "details": details_payload}


def _operation_plan_with_pipeline_context_receipts(
    *,
    operation_plan: Mapping[str, object],
    pipeline_context: MetaProviderDeltaPipelineContext,
) -> dict[str, object]:
    stage_payloads = pipeline_context.stage_payloads()
    provider_delta_oig_commit_receipt = stage_payloads[
        "provider_delta_oig_commit_receipt"
    ]
    provider_delta_ontology_execution_plan = stage_payloads[
        "provider_delta_ontology_execution_plan"
    ]
    provider_delta_functioncall_capability_matrix = stage_payloads[
        "provider_delta_functioncall_capability_matrix"
    ]
    provider_delta_head_move_applied_receipt = stage_payloads[
        "provider_delta_head_move_applied_receipt"
    ]
    provider_delta_runtime_package_index_patch = stage_payloads[
        "provider_delta_runtime_package_index_patch"
    ]
    provider_delta_semantic_commit_evidence = stage_payloads[
        "provider_delta_semantic_commit_evidence"
    ]
    provider_delta_semantic_change_report = stage_payloads[
        "provider_delta_semantic_change_report"
    ]
    provider_delta_source_projection = stage_payloads[
        "provider_delta_source_projection"
    ]
    provider_delta_generated_materialization = stage_payloads[
        "provider_delta_generated_materialization"
    ]
    provider_delta_output_materialization = stage_payloads[
        "provider_delta_output_materialization"
    ]
    provider_delta_execute_flag_preflight = stage_payloads[
        "provider_delta_execute_flag_preflight"
    ]
    provider_delta_active_execution_rail = _mapping_value(
        provider_delta_execute_flag_preflight.get(
            "provider_delta_active_execution_rail"
        )
    )
    return {
        **operation_plan,
        "active_execution_rail": _optional_text(
            provider_delta_active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(
            provider_delta_active_execution_rail.get("status")
        ),
        "active_execution_reason": _optional_text(
            provider_delta_active_execution_rail.get("reason")
        ),
        "provider_delta_active_execution_rail": provider_delta_active_execution_rail,
        "provider_delta_oig_commit_receipt_status": (
            pipeline_context.oig_commit_receipt.status
        ),
        "provider_delta_oig_commit_receipt_reason": (
            pipeline_context.oig_commit_receipt.reason
        ),
        "provider_delta_oig_commit_receipt": provider_delta_oig_commit_receipt,
        "provider_delta_ontology_execution_status": (
            pipeline_context.ontology_execution_status
        ),
        "provider_delta_ontology_execution_reason": _optional_text(
            provider_delta_ontology_execution_plan.get("reason")
        ),
        "provider_delta_ontology_execution_invocation_intent_count": (
            pipeline_context.ontology_execution_plan.invocation_intent_count
        ),
        "provider_delta_ontology_execution_blocker_count": _int_payload_value(
            provider_delta_ontology_execution_plan,
            "blocker_count",
        ),
        "provider_delta_ontology_execution_plan": (
            provider_delta_ontology_execution_plan
        ),
        "provider_delta_functioncall_capability_status": (
            pipeline_context.functioncall_capability_matrix.coverage_status
        ),
        "provider_delta_functioncall_capability_execution_allowed": (
            pipeline_context.functioncall_execution_allowed
        ),
        "provider_delta_functioncall_capability_non_executable_count": (
            _int_payload_value(
                provider_delta_functioncall_capability_matrix,
                "non_executable_operation_count",
            )
        ),
        "provider_delta_functioncall_capability_matrix": (
            provider_delta_functioncall_capability_matrix
        ),
        "provider_delta_head_move_applied_receipt_status": (
            pipeline_context.head_move_applied_receipt.status
        ),
        "provider_delta_head_move_applied_receipt_reason": (
            pipeline_context.head_move_applied_receipt.reason
        ),
        "provider_delta_head_move_applied_receipt": (
            provider_delta_head_move_applied_receipt
        ),
        "provider_delta_runtime_package_index_patch_status": (
            pipeline_context.runtime_package_index_patch.status
        ),
        "provider_delta_runtime_package_index_patch_reason": (
            pipeline_context.runtime_package_index_patch.reason
        ),
        "provider_delta_runtime_package_index_patch_semantic_object_upsert_count": (
            pipeline_context.runtime_package_index_patch.semantic_object_upsert_count
        ),
        "provider_delta_runtime_package_index_patch_semantic_object_delete_count": (
            pipeline_context.runtime_package_index_patch.semantic_object_delete_count
        ),
        "provider_delta_runtime_package_index_patch": (
            provider_delta_runtime_package_index_patch
        ),
        "provider_delta_semantic_commit_evidence_status": (
            pipeline_context.semantic_commit_evidence.status
        ),
        "provider_delta_semantic_commit_evidence_reason": (
            pipeline_context.semantic_commit_evidence.reason
        ),
        "provider_delta_committed_semantic_change_count": (
            pipeline_context.semantic_commit_evidence.committed_semantic_change_count
        ),
        "provider_delta_semantic_commit_evidence": (
            provider_delta_semantic_commit_evidence
        ),
        "provider_delta_semantic_change_report_status": (
            pipeline_context.semantic_change_report.status
        ),
        "provider_delta_semantic_change_report_reason": (
            pipeline_context.semantic_change_report.reason
        ),
        "provider_delta_semantic_world_change_count": (
            pipeline_context.semantic_change_report.semantic_world_change_count
        ),
        "provider_delta_semantic_change_report": (
            provider_delta_semantic_change_report
        ),
        "provider_delta_source_projection_status": _optional_text(
            provider_delta_source_projection.get("status")
        ),
        "provider_delta_source_projection_ready": (
            provider_delta_source_projection.get("ready") is True
        ),
        "provider_delta_source_projection_projected_entry_count": (
            _int_payload_value(
                provider_delta_source_projection,
                "projected_entry_count",
            )
        ),
        "provider_delta_source_projection": provider_delta_source_projection,
        "provider_delta_generated_materialization_status": _optional_text(
            provider_delta_generated_materialization.get("status")
        ),
        "provider_delta_generated_materialization_ready": (
            provider_delta_generated_materialization.get("ready") is True
        ),
        "provider_delta_generated_materialization_renderer_operation_count": (
            _int_payload_value(
                provider_delta_generated_materialization,
                "renderer_operation_count",
            )
        ),
        "provider_delta_generated_materialization": (
            provider_delta_generated_materialization
        ),
        "provider_delta_output_materialization_status": (
            pipeline_context.output_materialization.status
        ),
        "provider_delta_output_materialization_reason": (
            pipeline_context.output_materialization.reason
        ),
        "provider_delta_output_materialization_target_count": (
            pipeline_context.output_materialization.target_count
        ),
        "provider_delta_output_materialization_artifact_receipt_count": (
            pipeline_context.output_materialization.artifact_ownership_receipt_count
        ),
        "provider_delta_output_materialization": (
            provider_delta_output_materialization
        ),
    }


def _operation_plan_from_analysis(
    *,
    analysis: MetaOcgSemanticAnalysisResult,
    current_delta_fingerprint: str,
    function_call_plans: tuple[SemanticCapabilityFunctionCallPlan, ...],
    baseline_dirty_preflight: Mapping[str, object] | None = None,
    semantic_dirty_diff: Mapping[str, object] | None = None,
    provider_delta_head_move_plan: Mapping[str, object] | None = None,
    provider_delta_typed_operation_plan: Mapping[str, object] | None = None,
    provider_delta_mutation_plan: Mapping[str, object] | None = None,
    provider_delta_ontology_execution_plan: Mapping[str, object] | None = None,
    provider_delta_functioncall_capability_matrix: Mapping[str, object] | None = None,
    provider_delta_execute_flag_preflight: Mapping[str, object] | None = None,
    provider_delta_empty_lane_genesis_preflight: Mapping[str, object] | None = None,
) -> dict[str, object]:
    preview = analysis.change_preview
    semantic_deltas = preview.semantic_deltas
    semantic_delta_payloads = tuple(
        delta.evidence_payload() for delta in semantic_deltas
    )
    semantic_change_payloads = tuple(
        _semantic_change_payload(event.evidence_payload())
        for event in preview.semantic_events
    )
    function_call_plan_payloads = tuple(
        plan.evidence_payload() for plan in function_call_plans
    )
    active_execution_rail = (
        _mapping_value(
            provider_delta_execute_flag_preflight.get(
                "provider_delta_active_execution_rail"
            )
        )
        if provider_delta_execute_flag_preflight is not None
        else {}
    )
    return {
        "plan_kind": "meta_ocg_provider_delta_operation_plan",
        "contract_version": "aware.meta.ocg.provider-delta-operation-plan.v1",
        "status": "ready_non_executing",
        "reason": "meta_ocg_provider_delta_operation_plan_ready",
        "source": "aware_meta.semantic_analysis",
        "current_delta_fingerprint": current_delta_fingerprint,
        "changed_source_files": preview.changed_source_files,
        "affected_object_config_graph_keys": preview.affected_object_config_graph_keys,
        "affected_node_keys": preview.affected_node_keys,
        "required_materializations": preview.required_materializations,
        "graph_count": preview.graph_count,
        "node_count": preview.node_count,
        "class_count": preview.class_count,
        "enum_count": preview.enum_count,
        "function_count": preview.function_count,
        "relationship_count": preview.relationship_count,
        "semantic_delta_count": len(semantic_delta_payloads),
        "semantic_change_count": len(semantic_change_payloads),
        "semantic_function_call_plan_count": len(function_call_plan_payloads),
        "operation_count": len(semantic_delta_payloads),
        "semantic_deltas": semantic_delta_payloads,
        "semantic_changes": semantic_change_payloads,
        "semantic_function_call_plans": function_call_plan_payloads,
        "semantic_dirty_diff_available": (
            bool(semantic_dirty_diff.get("available"))
            if semantic_dirty_diff is not None
            else False
        ),
        "semantic_dirty_diff_status": (
            str(semantic_dirty_diff.get("status"))
            if semantic_dirty_diff is not None
            else "semantic_dirty_diff_not_requested"
        ),
        "semantic_dirty_diff_reason": (
            str(semantic_dirty_diff.get("reason"))
            if semantic_dirty_diff is not None
            else "provider_delta_semantic_dirty_diff_not_requested"
        ),
        "semantic_dirty_entry_count": (
            _int_payload_value(semantic_dirty_diff, "dirty_entry_count")
            if semantic_dirty_diff is not None
            else 0
        ),
        "baseline_index_compare_available": (
            bool(semantic_dirty_diff.get("baseline_index_compare_available"))
            if semantic_dirty_diff is not None
            else False
        ),
        "baseline_index_compare_status": (
            str(semantic_dirty_diff.get("baseline_index_compare_status"))
            if semantic_dirty_diff is not None
            else "semantic_dirty_diff_not_requested"
        ),
        "baseline_semantic_object_index_count": (
            _int_payload_value(
                semantic_dirty_diff,
                "baseline_semantic_object_index_count",
            )
            if semantic_dirty_diff is not None
            else 0
        ),
        "baseline_compare_operation_counts": (
            dict(
                _mapping_value(
                    semantic_dirty_diff.get("baseline_compare_operation_counts")
                )
            )
            if semantic_dirty_diff is not None
            else {}
        ),
        "provider_delta_head_move_status": (
            str(provider_delta_head_move_plan.get("status"))
            if provider_delta_head_move_plan is not None
            else "head_move_plan_not_requested"
        ),
        "provider_delta_head_move_reason": (
            str(provider_delta_head_move_plan.get("reason"))
            if provider_delta_head_move_plan is not None
            else "provider_delta_head_move_plan_not_requested"
        ),
        "provider_delta_head_move_planned_operation_count": (
            _int_payload_value(
                provider_delta_head_move_plan,
                "planned_operation_count",
            )
            if provider_delta_head_move_plan is not None
            else 0
        ),
        "provider_delta_head_move_plan": (
            dict(provider_delta_head_move_plan)
            if provider_delta_head_move_plan is not None
            else None
        ),
        "provider_delta_typed_operation_status": (
            str(provider_delta_typed_operation_plan.get("status"))
            if provider_delta_typed_operation_plan is not None
            else "typed_operation_plan_not_requested"
        ),
        "provider_delta_typed_operation_reason": (
            str(provider_delta_typed_operation_plan.get("reason"))
            if provider_delta_typed_operation_plan is not None
            else "provider_delta_typed_operation_plan_not_requested"
        ),
        "provider_delta_typed_operation_count": (
            _int_payload_value(
                provider_delta_typed_operation_plan,
                "typed_operation_count",
            )
            if provider_delta_typed_operation_plan is not None
            else 0
        ),
        "provider_delta_blocked_typed_operation_count": (
            _int_payload_value(
                provider_delta_typed_operation_plan,
                "blocked_operation_count",
            )
            if provider_delta_typed_operation_plan is not None
            else 0
        ),
        "provider_delta_typed_operation_plan": (
            dict(provider_delta_typed_operation_plan)
            if provider_delta_typed_operation_plan is not None
            else None
        ),
        "provider_delta_mutation_plan_status": (
            str(provider_delta_mutation_plan.get("status"))
            if provider_delta_mutation_plan is not None
            else "mutation_plan_not_requested"
        ),
        "provider_delta_mutation_plan_status_role": "legacy_diagnostic",
        "provider_delta_mutation_plan_reason": (
            str(provider_delta_mutation_plan.get("reason"))
            if provider_delta_mutation_plan is not None
            else "provider_delta_mutation_plan_not_requested"
        ),
        "provider_delta_mutation_step_count": (
            _int_payload_value(
                provider_delta_mutation_plan,
                "mutation_step_count",
            )
            if provider_delta_mutation_plan is not None
            else 0
        ),
        "provider_delta_blocked_mutation_step_count": (
            _int_payload_value(
                provider_delta_mutation_plan,
                "blocked_mutation_step_count",
            )
            if provider_delta_mutation_plan is not None
            else 0
        ),
        "provider_delta_execute_flag_preflight_status": (
            str(provider_delta_execute_flag_preflight.get("status"))
            if provider_delta_execute_flag_preflight is not None
            else "execute_flag_preflight_not_requested"
        ),
        "provider_delta_execute_flag_preflight_reason": (
            str(provider_delta_execute_flag_preflight.get("reason"))
            if provider_delta_execute_flag_preflight is not None
            else "meta_ocg_provider_delta_execute_flag_not_requested"
        ),
        "provider_delta_execute_flag_preflight_blocker_count": (
            _int_payload_value(
                provider_delta_execute_flag_preflight,
                "blocker_count",
            )
            if provider_delta_execute_flag_preflight is not None
            else 0
        ),
        "provider_delta_execute_flag_preflight": (
            _mapping_value(provider_delta_execute_flag_preflight)
            if provider_delta_execute_flag_preflight is not None
            else None
        ),
        "provider_delta_empty_lane_genesis_preflight_status": (
            str(provider_delta_empty_lane_genesis_preflight.get("status"))
            if provider_delta_empty_lane_genesis_preflight is not None
            else "empty_lane_genesis_preflight_not_requested"
        ),
        "provider_delta_empty_lane_genesis_route_active": (
            provider_delta_empty_lane_genesis_preflight.get("route_active") is True
            if provider_delta_empty_lane_genesis_preflight is not None
            else False
        ),
        "provider_delta_empty_lane_genesis_preflight": (
            _mapping_value(provider_delta_empty_lane_genesis_preflight)
            if provider_delta_empty_lane_genesis_preflight is not None
            else None
        ),
        "active_execution_rail": _optional_text(
            active_execution_rail.get("active_execution_rail")
        ),
        "active_execution_status": _optional_text(active_execution_rail.get("status")),
        "active_execution_reason": _optional_text(active_execution_rail.get("reason")),
        "provider_delta_active_execution_rail": (
            active_execution_rail
            if provider_delta_execute_flag_preflight is not None
            else None
        ),
        "provider_delta_mutation_plan": (
            dict(provider_delta_mutation_plan)
            if provider_delta_mutation_plan is not None
            else None
        ),
        "provider_delta_ontology_execution_status": (
            str(provider_delta_ontology_execution_plan.get("status"))
            if provider_delta_ontology_execution_plan is not None
            else "ontology_execution_plan_not_requested"
        ),
        "provider_delta_ontology_execution_reason": (
            str(provider_delta_ontology_execution_plan.get("reason"))
            if provider_delta_ontology_execution_plan is not None
            else "provider_delta_ontology_execution_plan_not_requested"
        ),
        "provider_delta_ontology_execution_invocation_intent_count": (
            _int_payload_value(
                provider_delta_ontology_execution_plan,
                "invocation_intent_count",
            )
            if provider_delta_ontology_execution_plan is not None
            else 0
        ),
        "provider_delta_ontology_execution_blocker_count": (
            _int_payload_value(
                provider_delta_ontology_execution_plan,
                "blocker_count",
            )
            if provider_delta_ontology_execution_plan is not None
            else 0
        ),
        "provider_delta_ontology_execution_plan": (
            dict(provider_delta_ontology_execution_plan)
            if provider_delta_ontology_execution_plan is not None
            else None
        ),
        "provider_delta_functioncall_capability_status": (
            str(provider_delta_functioncall_capability_matrix.get("coverage_status"))
            if provider_delta_functioncall_capability_matrix is not None
            else "functioncall_capability_matrix_not_requested"
        ),
        "provider_delta_functioncall_capability_execution_allowed": (
            provider_delta_functioncall_capability_matrix.get("execution_allowed")
            is True
            if provider_delta_functioncall_capability_matrix is not None
            else False
        ),
        "provider_delta_functioncall_capability_non_executable_count": (
            _int_payload_value(
                provider_delta_functioncall_capability_matrix,
                "non_executable_operation_count",
            )
            if provider_delta_functioncall_capability_matrix is not None
            else 0
        ),
        "provider_delta_functioncall_capability_matrix": (
            dict(provider_delta_functioncall_capability_matrix)
            if provider_delta_functioncall_capability_matrix is not None
            else None
        ),
        "semantic_dirty_diff": (
            dict(semantic_dirty_diff) if semantic_dirty_diff is not None else None
        ),
        "baseline_dirty_preflight": (
            dict(baseline_dirty_preflight)
            if baseline_dirty_preflight is not None
            else None
        ),
        "apply_wired": False,
        "production_execution_wired": False,
        "would_execute": False,
        "would_persist": False,
    }


def _empty_meta_ocg_delta_analysis(
    *,
    package_root: Path,
    manifest_path: Path,
    code_package_delta: CodePackageDelta | None,
) -> MetaOcgSemanticAnalysisResult:
    changed_source_files = _delta_changed_source_files(delta=code_package_delta)
    return MetaOcgSemanticAnalysisResult(
        schema_version=1,
        package_root=package_root.as_posix(),
        manifest_path=manifest_path.as_posix(),
        source_files=changed_source_files,
        namespace_mappings=(),
        source_object_config_graph=None,
        object_config_graph=None,
        runtime_derivation=None,
        diagnostics=(),
        change_preview=MetaOcgSemanticChangePreview(
            changed_source_files=changed_source_files,
            affected_object_config_graph_keys=(),
            affected_node_keys=(),
            semantic_deltas=(),
            semantic_events=(),
            graph_count=0,
            node_count=0,
            class_count=0,
            enum_count=0,
            function_count=0,
            relationship_count=0,
            required_materializations=(),
        ),
        code_package_delta=code_package_delta,
    )


def _meta_ocg_delta_analysis_for_empty_lane_genesis(
    *,
    package_root: Path,
    manifest_path: Path,
    code_package_delta: CodePackageDelta,
) -> MetaOcgSemanticAnalysisResult:
    return analyze_meta_ocg_code_package_delta(
        package_root=package_root,
        source_files=tuple(
            Path(source_file)
            for source_file in _delta_changed_source_files(
                delta=code_package_delta,
            )
        ),
        manifest_path=manifest_path,
        code_package_delta=code_package_delta,
        fail_on_error=False,
    )


def _delta_changed_source_files(
    *,
    delta: CodePackageDelta | None,
) -> tuple[str, ...]:
    if delta is None:
        return ()
    changed: list[str] = []
    sources_root = _optional_text(delta.sources_root)
    for path_delta in delta.paths:
        path = Path(path_delta.relative_path).as_posix().strip("/")
        if not path:
            continue
        if sources_root:
            prefix = f"{sources_root.strip('/')}/"
            if path.startswith(prefix):
                path = path.removeprefix(prefix)
        changed.append(path)
    return tuple(dict.fromkeys(changed))


def _provider_delta_empty_lane_genesis_requested(*, request: object) -> bool:
    lane_state = _model_payload(getattr(request, "provider_delta_lane_state", None))
    return _optional_text(lane_state.get("status")) == "empty_lane"


def _provider_delta_mutation_plan(
    *,
    provider_delta_typed_operation_plan: Mapping[str, object],
) -> dict[str, object]:
    typed_plan_ready = (
        provider_delta_typed_operation_plan.get("status")
        == "typed_operation_plan_ready"
        and provider_delta_typed_operation_plan.get("blocked") is not True
    )
    source_operations = (
        _mutation_plan_operations(
            provider_delta_typed_operation_plan.get("typed_operations")
        )
        if typed_plan_ready
        else _mutation_plan_operations(
            provider_delta_typed_operation_plan.get("blocked_operations")
        )
    )
    semantic_object_anchors = (
        _mutation_plan_operations(
            provider_delta_typed_operation_plan.get("semantic_object_anchors")
        )
        if typed_plan_ready
        else ()
    )
    typed_operation_by_semantic_key = _typed_operation_by_semantic_key(
        operations=(*semantic_object_anchors, *source_operations),
    )
    steps = tuple(
        _mutation_step_from_typed_operation(
            typed_operation=typed_operation,
            force_blocked=not typed_plan_ready,
            typed_operation_by_semantic_key=typed_operation_by_semantic_key,
        )
        for typed_operation in source_operations
    )
    mutation_steps = tuple(
        step for step in steps if step.get("status") == "mutation_step_ready"
    )
    blocked_mutation_steps = tuple(
        step for step in steps if step.get("status") == "mutation_step_blocked"
    )
    blocked = not typed_plan_ready or bool(blocked_mutation_steps)
    return {
        "plan_kind": "meta_ocg_provider_delta_mutation_plan",
        "contract_version": _MUTATION_PLAN_CONTRACT_VERSION,
        "step_contract_version": _MUTATION_STEP_CONTRACT_VERSION,
        "status": _mutation_plan_status(
            typed_plan_ready=typed_plan_ready,
            mutation_steps=mutation_steps,
            blocked_mutation_steps=blocked_mutation_steps,
        ),
        "reason": _mutation_plan_reason(
            typed_plan_ready=typed_plan_ready,
            provider_delta_typed_operation_plan=provider_delta_typed_operation_plan,
            blocked_mutation_steps=blocked_mutation_steps,
        ),
        "source": "aware_meta.provider_delta.typed_operations",
        "provider_key": _SUPPORTED_DELTA_PROVIDER_KEY,
        "typed_operation_plan_status": _optional_text(
            provider_delta_typed_operation_plan.get("status")
        ),
        "typed_operation_plan_reason": _optional_text(
            provider_delta_typed_operation_plan.get("reason")
        ),
        "typed_operation_count": _int_payload_value(
            provider_delta_typed_operation_plan,
            "typed_operation_count",
        ),
        "semantic_object_anchor_count": len(semantic_object_anchors),
        "blocked_typed_operation_count": _int_payload_value(
            provider_delta_typed_operation_plan,
            "blocked_operation_count",
        ),
        "source_operation_count": len(source_operations),
        "mutation_step_count": len(mutation_steps),
        "blocked_mutation_step_count": len(blocked_mutation_steps),
        "mutation_step_operation_counts": _mutation_step_count_by_field(
            steps=mutation_steps,
            field_name="provider_operation_type",
        ),
        "blocked_mutation_step_reason_counts": _mutation_step_count_by_field(
            steps=blocked_mutation_steps,
            field_name="reason",
        ),
        "mutation_steps": mutation_steps,
        "blocked_mutation_steps": blocked_mutation_steps,
        "available": bool(mutation_steps),
        "blocked": blocked,
        "apply_wired": False,
        "would_execute": False,
        "did_execute": False,
        "would_persist": False,
        "did_persist": False,
        "execution_wired": False,
        "production_execution_wired": False,
    }


def _typed_operation_by_semantic_key(
    *,
    operations: tuple[Mapping[str, object], ...],
) -> dict[str, Mapping[str, object]]:
    entries: dict[str, Mapping[str, object]] = {}
    for operation in operations:
        semantic_key = _optional_text(operation.get("semantic_key"))
        if semantic_key is not None:
            entries[semantic_key] = operation
    return entries


def _mutation_plan_status(
    *,
    typed_plan_ready: bool,
    mutation_steps: tuple[Mapping[str, object], ...],
    blocked_mutation_steps: tuple[Mapping[str, object], ...],
) -> str:
    if not typed_plan_ready:
        return "mutation_plan_blocked"
    if blocked_mutation_steps:
        return "mutation_plan_partially_blocked"
    if mutation_steps:
        return "mutation_plan_ready"
    return "mutation_plan_empty"


def _mutation_plan_reason(
    *,
    typed_plan_ready: bool,
    provider_delta_typed_operation_plan: Mapping[str, object],
    blocked_mutation_steps: tuple[Mapping[str, object], ...],
) -> str:
    if not typed_plan_ready:
        return (
            _optional_text(provider_delta_typed_operation_plan.get("reason"))
            or "meta_ocg_provider_delta_mutation_plan_requires_typed_operations"
        )
    if blocked_mutation_steps:
        return "meta_ocg_provider_delta_mutation_plan_has_blocked_steps"
    return "meta_ocg_provider_delta_mutation_plan_ready"


def _function_call_plans_from_analysis(
    *,
    analysis: MetaOcgSemanticAnalysisResult,
) -> tuple[SemanticCapabilityFunctionCallPlan, ...]:
    preview = analysis.change_preview
    return build_meta_runtime_ocg_function_call_plan_previews(
        change_preview={
            "semantic_deltas": tuple(
                delta.evidence_payload() for delta in preview.semantic_deltas
            )
        }
    )


def build_meta_runtime_ocg_function_call_plan_previews(
    *,
    change_preview: Mapping[str, object],
) -> tuple[SemanticCapabilityFunctionCallPlan, ...]:
    package_plans: list[SemanticCapabilityFunctionCallPlan] = []
    graph_plans: list[SemanticCapabilityFunctionCallPlan] = []
    node_plans: list[SemanticCapabilityFunctionCallPlan] = []
    for delta in _tuple_evidence(change_preview.get("semantic_deltas")):
        payload = _mapping_value(delta)
        subject_type = _string_value(payload.get("subject_type"))
        semantic_key = _optional_text(payload.get("semantic_key"))
        after_payload = _mapping_value(payload.get("after_payload"))
        metadata = {
            **_runtime_graph_metadata_from_delta(payload),
            "source_delta_key": _string_value(payload.get("delta_key")),
            "source_subject_type": subject_type,
        }
        if subject_type == "aware_meta.ObjectConfigGraphPackage":
            fqn_prefix = _optional_text(after_payload.get("fqn_prefix"))
            package_plans.append(
                SemanticCapabilityFunctionCallPlan(
                    function_ref=META_OCG_PACKAGE_BUILD_FUNCTION_REF,
                    binding_key="aware_meta.object_config_graph_package.build",
                    event_key=_event_key_for_delta(payload),
                    arguments={
                        "package_name": after_payload.get("package_name"),
                        "fqn_prefix": after_payload.get("fqn_prefix"),
                        "package_kind": after_payload.get("package_kind"),
                    },
                    result_semantic_key=semantic_key,
                    metadata={
                        **metadata,
                        "plan_kind": "object_config_graph_package_build",
                        "object_config_graph_semantic_key": (
                            f"ocg:{fqn_prefix}" if fqn_prefix is not None else None
                        ),
                    },
                )
            )
        elif subject_type == "aware_meta.ObjectConfigGraph":
            graph_plans.append(
                SemanticCapabilityFunctionCallPlan(
                    function_ref=META_OCG_BUILD_FUNCTION_REF,
                    binding_key="aware_meta.object_config_graph.build",
                    event_key=_event_key_for_delta(payload),
                    arguments={
                        "name": after_payload.get("name"),
                        "fqn_prefix": after_payload.get("fqn_prefix"),
                        "language": after_payload.get("language"),
                        "hash": after_payload.get("hash"),
                        "node_count": after_payload.get("node_count"),
                    },
                    result_semantic_key=semantic_key,
                    metadata={**metadata, "plan_kind": "object_config_graph_build"},
                )
            )
        elif subject_type == "aware_meta.ObjectConfigGraphNode":
            node_plans.append(
                SemanticCapabilityFunctionCallPlan(
                    function_ref=META_OCG_CREATE_NODE_FUNCTION_REF,
                    binding_key="aware_meta.object_config_graph.create_node",
                    event_key=_event_key_for_delta(payload),
                    receiver_semantic_key=_optional_text(
                        after_payload.get("graph_semantic_key")
                    ),
                    arguments={
                        "type": after_payload.get("node_type"),
                        "node_key": after_payload.get("node_key"),
                    },
                    result_semantic_key=semantic_key,
                    metadata={**metadata, "plan_kind": "object_config_graph_node"},
                )
            )
    return (*graph_plans, *node_plans, *package_plans)


def _runtime_graph_metadata_from_delta(
    delta_payload: Mapping[str, object],
) -> dict[str, object]:
    metadata = _mapping_value(delta_payload.get("metadata"))
    return {
        key: metadata.get(key)
        for key in (
            "semantic_truth_graph",
            "source_graph_role",
            "runtime_graph_role",
            "source_graph_hash",
            "runtime_graph_hash",
            "runtime_node_type",
        )
        if key in metadata
    }


def _event_key_for_delta(delta_payload: Mapping[str, object]) -> str | None:
    subject_type = _string_value(delta_payload.get("subject_type"))
    verb = _string_value(delta_payload.get("verb"))
    prefix = {
        "aware_meta.ObjectConfigGraphPackage": (
            "aware_meta.object_config_graph_package"
        ),
        "aware_meta.ObjectConfigGraph": "aware_meta.object_config_graph",
        "aware_meta.ObjectConfigGraphNode": "aware_meta.object_config_graph_node",
    }.get(subject_type, subject_type)
    if not prefix or not verb:
        return None
    return f"{prefix}.{verb}ed"


def _code_package_delta_from_provider_delta_request(
    *,
    request: object,
) -> CodePackageDelta | None:
    raw_delta = getattr(request, "code_package_delta", None)
    if raw_delta is None:
        return None
    if isinstance(raw_delta, CodePackageDelta):
        return raw_delta
    return CodePackageDelta.model_validate(raw_delta)


def _resolve_delta_manifest_path(value: object) -> Path | None:
    manifest_path_text = _optional_text(value)
    if manifest_path_text is None:
        return None
    candidate = Path(manifest_path_text).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    if not candidate.is_absolute():
        cwd_candidate = (Path.cwd() / candidate).resolve()
        if cwd_candidate.is_file():
            return cwd_candidate
    return None


def _model_payload(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    try:
        raw_vars = vars(value)
    except TypeError:
        return {}
    if isinstance(raw_vars, Mapping):
        return {str(key): item for key, item in raw_vars.items()}
    return {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _tuple_evidence(value: object) -> tuple[object, ...]:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return ()


def _mapping_value(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def _mutation_plan_operations(value: object) -> tuple[dict[str, object], ...]:
    return tuple(
        _mapping_value(operation)
        for operation in _tuple_evidence(value)
        if isinstance(operation, Mapping)
    )


def _mutation_step_count_by_field(
    *,
    steps: tuple[Mapping[str, object], ...],
    field_name: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for step in steps:
        value = _optional_text(step.get(field_name))
        if value is None:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _string_value(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _tuple_text(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(
        text for text in (_optional_text(item) for item in value) if text is not None
    )


__all__ = [
    "_baseline_semantic_object_index_from_oig",
    "build_meta_runtime_ocg_function_call_plan_previews",
    "materialize_delta",
]
