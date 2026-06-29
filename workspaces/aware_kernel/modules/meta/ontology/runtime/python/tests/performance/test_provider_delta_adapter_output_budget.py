from __future__ import annotations

from collections.abc import Mapping
from typing import cast

import pytest

from aware_code.semantic_materialization import SemanticProviderDeltaRequest
from aware_meta.materialization import workspace_provider

from .budgets import BudgetTimer, assert_metric_lte
from .samples import meta_performance_sample_package_root


@pytest.mark.asyncio
async def test_provider_delta_adapter_invocation_budget_blocks_output_without_head_move() -> (
    None
):
    request = _provider_delta_request_from_meta_perf_sample()

    timer = BudgetTimer.start(
        label="provider_delta_adapter_invocation",
        max_duration_s=1.0,
    )
    result = await workspace_provider.materialize_delta(request=request)
    elapsed_s = timer.assert_within_budget()

    details = _mapping(result["details"])
    output_materialization = _mapping(details["provider_delta_output_materialization"])
    assert result["status"] == "succeeded"
    assert result["fallback_reason"] is None
    assert details["mode"] == "meta_ocg_provider_delta_result_dry_run"
    assert output_materialization["status"] == (
        "provider_delta_output_materialization_blocked"
    )
    assert (
        output_materialization["reason"] == "provider_delta_workspace_root_unavailable"
    )
    assert output_materialization["rendered_target_count"] == 0
    assert_metric_lte(
        label="provider_delta_adapter_invocation_s",
        actual=elapsed_s,
        maximum=1.0,
    )
    assert_metric_lte(
        label="provider_delta_adapter_output_stage_s",
        actual=_float_payload(output_materialization["duration_s"]),
        maximum=0.05,
    )


@pytest.mark.asyncio
async def test_provider_delta_adapter_output_handoff_budget_forwards_stage_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _provider_delta_request_from_meta_perf_sample()
    calls: list[dict[str, object]] = []

    async def fake_materialize_provider_delta_outputs(
        *,
        request: object,
        provider_delta_head_move_applied_receipt: Mapping[str, object],
        provider_delta_oig_commit_receipt: Mapping[str, object],
        provider_delta_typed_operation_plan: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        calls.append(
            {
                "request": request,
                "head_move": dict(provider_delta_head_move_applied_receipt),
                "commit": dict(provider_delta_oig_commit_receipt),
                "typed_plan": dict(provider_delta_typed_operation_plan or {}),
            }
        )
        return {
            "receipt_kind": "meta_provider_delta_output_materialization",
            "contract_version": "aware.meta.provider-delta.output-materialization.v1",
            "status": "provider_delta_output_materialization_not_required",
            "reason": "provider_delta_output_stage_faked_for_budget",
            "available": False,
            "blocked": False,
            "target_count": 0,
            "rendered_target_count": 0,
            "artifact_ownership_receipt_count": 0,
            "artifact_ownership_receipts": (),
            "post_step_receipt_count": 0,
            "post_step_receipts": (),
            "tool_step_receipt_count": 0,
            "tool_step_receipts": (),
            "tool_timings_s": {},
            "runtime_to_language_cache": {},
            "runtime_derivation_cache": {},
            "blockers": (),
            "blocker_count": 0,
            "duration_s": 0.0,
            "error": None,
        }

    monkeypatch.setattr(
        workspace_provider,
        "materialize_provider_delta_outputs",
        fake_materialize_provider_delta_outputs,
    )

    timer = BudgetTimer.start(
        label="provider_delta_adapter_output_handoff",
        max_duration_s=1.0,
    )
    result = await workspace_provider.materialize_delta(request=request)
    elapsed_s = timer.assert_within_budget()

    details = _mapping(result["details"])
    output_materialization = _mapping(details["provider_delta_output_materialization"])
    assert len(calls) == 1
    call = calls[0]
    assert call["request"] is request
    assert _mapping(call["commit"])["status"] == "execute_flag_commit_not_requested"
    assert _mapping(call["head_move"])["status"] == (
        "head_move_applied_receipt_unavailable"
    )
    typed_plan = _mapping(call["typed_plan"])
    assert typed_plan["plan_kind"] == "meta_ocg_provider_delta_typed_operation_plan"
    assert output_materialization["status"] == (
        "provider_delta_output_materialization_not_required"
    )
    assert output_materialization["rendered_target_count"] == 0
    assert_metric_lte(
        label="provider_delta_adapter_output_handoff_s",
        actual=elapsed_s,
        maximum=1.0,
    )


def _provider_delta_request_from_meta_perf_sample() -> SemanticProviderDeltaRequest:
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
                "provider_key": "aware_meta",
                "role": "aware_meta.provider",
                "name": "aware.semantic_provider",
            },
            "current_delta_fingerprint": "sha256:meta-perf-adapter-output",
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


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, Mapping)
    return dict(cast(Mapping[str, object], value))


def _float_payload(value: object) -> float:
    assert isinstance(value, int | float)
    return float(value)
