from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace
from typing import cast

import pytest

from aware_code.semantic_materialization import SemanticProviderDeltaRequest
from aware_meta.materialization import workspace_provider

from .budgets import BudgetTimer, assert_metric_lte
from .samples import meta_performance_sample_package_root


_FULL_ADAPTER_STAGES = (
    "request_identity",
    "provider_contract_check",
    "execution_context_preflight",
    "baseline_dirty_preflight",
    "code_delta_normalization",
    "semantic_analysis",
    "semantic_dirty_diff",
    "typed_operation_plan",
    "source_projection",
    "mutation_plan",
    "ontology_execution_plan",
    "functioncall_capability_matrix",
    "execute_flag_preflight",
    "operation_plan",
    "oig_commit_receipt",
    "head_move_applied_receipt",
    "runtime_package_index_patch",
    "semantic_commit_evidence",
    "output_materialization",
    "operation_execution_detail",
    "result_assembly",
)


@pytest.mark.asyncio
async def test_provider_delta_stage_timings_budget_for_adapter_path() -> None:
    request = _provider_delta_request_from_meta_perf_sample()

    timer = BudgetTimer.start(
        label="provider_delta_stage_timings_adapter_path",
        max_duration_s=1.25,
    )
    result = await workspace_provider.materialize_delta(request=request)
    elapsed_s = timer.assert_within_budget()

    details = _mapping(result["details"])
    timings = _stage_timings(details)
    stages_s = _stage_timings_s(details)
    assert result["status"] == "succeeded"
    assert timings["contract_version"] == ("aware.meta.provider-delta-stage-timings.v1")
    assert timings["timing_kind"] == "meta_provider_delta_stage_timings"
    stage_order = timings["stage_order"]
    assert isinstance(stage_order, (list, tuple))
    assert tuple(stage_order) == tuple(stages_s)
    assert timings["stage_count"] == len(stages_s)
    assert stages_s == _mapping(timings["stages_s"])
    assert set(_FULL_ADAPTER_STAGES).issubset(stages_s)
    assert _float_payload(timings["total_s"]) >= sum(
        _float_payload(value) for value in stages_s.values()
    )
    assert_metric_lte(
        label="provider_delta_stage_timings_adapter_path_s",
        actual=elapsed_s,
        maximum=1.25,
    )
    assert_metric_lte(
        label="provider_delta_stage_timings_reported_total_s",
        actual=_float_payload(timings["total_s"]),
        maximum=1.25,
    )


@pytest.mark.asyncio
async def test_provider_delta_stage_timings_present_on_fallback() -> None:
    request = _provider_delta_request_from_meta_perf_sample(
        provider_key="unsupported_meta_perf_provider",
    )

    result = await workspace_provider.materialize_delta(request=request)

    details = _mapping(result["details"])
    stages_s = _stage_timings_s(details)
    assert result["status"] == "fallback_required"
    assert result["fallback_reason"] == "meta_ocg_delta_semantic_contract_unsupported"
    assert set(stages_s) == {
        "request_identity",
        "provider_contract_check",
        "result_assembly",
    }


@pytest.mark.asyncio
async def test_provider_delta_stage_timings_present_on_baseline_blocked_execution() -> (
    None
):
    request = _provider_delta_request_from_meta_perf_sample()
    execution_request = SimpleNamespace(
        **request.model_dump(mode="json"),
        execute_provider_delta_materialization=True,
    )

    result = await workspace_provider.materialize_delta(request=execution_request)

    details = _mapping(result["details"])
    stages_s = _stage_timings_s(details)
    assert result["status"] == "succeeded"
    assert _mapping(details["baseline_dirty_preflight"])["status"] == (
        "baseline_context_missing"
    )
    assert set(stages_s) == {
        "request_identity",
        "provider_contract_check",
        "execution_context_preflight",
        "baseline_dirty_preflight",
        "execution_baseline_gate",
        "result_assembly",
    }


def _provider_delta_request_from_meta_perf_sample(
    *,
    provider_key: str = "aware_meta",
) -> SemanticProviderDeltaRequest:
    package_root = meta_performance_sample_package_root() / "structure" / "ontology"
    manifest_path = package_root / "aware.toml"
    source_relative_path = "aware/lab/device.aware"
    source_text = (package_root / source_relative_path).read_text(encoding="utf-8")
    return SemanticProviderDeltaRequest.model_validate(
        {
            "package": {
                "package_name": "meta-perf-lab-ontology",
                "workspace_manifest_kind": "aware_toml",
                "manifest_path": manifest_path.as_posix(),
                "source_code_package_id": "meta-perf-source-code-package-id",
            },
            "semantic_contract": {
                "module": "aware_meta.semantic_contract",
                "provider_key": provider_key,
                "role": "aware_meta.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:meta-perf-stage-timings",
            "delta_cause_hints": {
                "changed_path_count": 1,
                "source_owned_path_count": 1,
                "generated_fallout_path_count": 0,
                "changed_path_classifications": {"source_owned": 1},
                "top_changed_path_limit": 8,
                "top_changed_paths": [
                    {
                        "path": source_relative_path,
                        "change_kind": "update",
                        "classification": "source_owned",
                        "package_relative_path": source_relative_path,
                        "language": "aware",
                        "is_structural": True,
                    }
                ],
                "current_delta_fingerprint_available": True,
                "previous_delta_fingerprint_available": True,
            },
            "code_package_delta": {
                "package_name": "meta-perf-lab-ontology",
                "package_root": ".",
                "sources_root": "aware",
                "manifest_relative_path": manifest_path.name,
                "authority_kind": "local_fs_view",
                "source_revision_id": "meta-perf-current",
                "paths": [
                    {
                        "relative_path": source_relative_path,
                        "kind": "update",
                        "language": "aware",
                        "is_structural": True,
                        "path_role": "authored_source",
                        "content_text": source_text,
                    }
                ],
            },
        }
    )


def _stage_timings(details: Mapping[str, object]) -> dict[str, object]:
    return _mapping(details["provider_delta_stage_timings"])


def _stage_timings_s(details: Mapping[str, object]) -> dict[str, object]:
    return _mapping(details["provider_delta_stage_timings_s"])


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))


def _float_payload(value: object) -> float:
    assert isinstance(value, int | float)
    return float(value)
