from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from aware_meta.materialization import workspace_provider

from .budgets import BudgetTimer, assert_metric_lte
from .samples import build_meta_performance_graph_bundle


@pytest.mark.asyncio
async def test_provider_delta_structural_output_budget_prunes_targets_and_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_meta_perf_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=("meta-perf-dep-0-ontology",),
    )
    bundle = build_meta_performance_graph_bundle(
        source_class_count=8,
        dependency_graph_count=3,
        dependency_class_count=4,
    )
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(
                SimpleNamespace(
                    name="render",
                    duration_s=0.002,
                    status="succeeded",
                    details={},
                ),
            ),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    timer = BudgetTimer.start(
        label="provider_delta_structural_output_budget",
        max_duration_s=0.25,
    )
    result = await workspace_provider.materialize_provider_delta_outputs(
        request=_provider_delta_output_request(
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            source_graph=bundle.source_graph,
            runtime_graphs=bundle.dependency_graphs,
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan=_relationship_update_typed_plan(),
    )
    timer.assert_within_budget()

    assert result["status"] == "provider_delta_output_materialization_ready"
    assert result["target_count"] == 5
    assert result["rendered_target_count"] == 3
    selected_target_count = result["language_target_impact_selected_target_count"]
    assert selected_target_count == 3
    assert result["language_target_impact_skipped_target_count"] == 2
    assert_metric_lte(
        label="selected_target_count",
        actual=_int_payload(selected_target_count),
        maximum=3,
    )
    assert [call.materialization_source for call in calls] == [
        "ontology_dto",
        "ontology",
        "ontology",
    ]
    assert {
        tuple(graph.fqn_prefix for graph in call.external_runtime_graphs)
        for call in calls
    } == {("aware_meta_perf_dep_0",)}
    assert {
        tuple(graph.fqn_prefix for graph in call.package_dependency_graphs)
        for call in calls
    } == {("aware_meta_perf_dep_0",)}
    assert _tool_total_s(result) <= 0.01
    timings = _output_phase_timings(result)
    assert timings["timing_kind"] == "meta_provider_delta_output_phase_timings"
    assert timings["contract_version"] == (
        "aware.meta.provider-delta.output-phase-timings.v1"
    )
    phase_order = _tuple_payload(timings["phase_order"])
    for phase_name in (
        "language_target_collection",
        "language_target_impact_plan",
        "source_graph_resolution",
        "dependency_graph_resolution",
        "language_plugin_invocation",
        "language_receipt_assembly",
        "tool_step_timing_assembly",
    ):
        assert phase_name in phase_order
        assert phase_name in _output_phase_timings_s(result)


@pytest.mark.asyncio
async def test_provider_delta_function_impl_output_budget_keeps_runtime_targets_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_meta_perf_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=(),
    )
    bundle = build_meta_performance_graph_bundle(
        source_class_count=6,
        dependency_graph_count=2,
        dependency_class_count=3,
    )
    calls: list[Any] = []

    def fake_language_materialization(request: Any) -> object:
        calls.append(request)
        return SimpleNamespace(
            ownership_receipts=(),
            post_step_receipts=(),
            tool_steps=(
                SimpleNamespace(
                    name="render",
                    duration_s=0.002,
                    status="succeeded",
                    details={},
                ),
            ),
        )

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        fake_language_materialization,
    )

    timer = BudgetTimer.start(
        label="provider_delta_function_impl_output_budget",
        max_duration_s=0.25,
    )
    result = await workspace_provider.materialize_provider_delta_outputs(
        request=_provider_delta_output_request(
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            source_graph=bundle.source_graph,
            runtime_graphs=bundle.dependency_graphs,
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan=_function_impl_update_typed_plan(),
    )
    timer.assert_within_budget()

    assert result["status"] == "provider_delta_output_materialization_ready"
    assert result["target_count"] == 5
    assert result["rendered_target_count"] == 2
    assert [call.materialization_source for call in calls] == [
        "runtime_handlers",
        "runtime_handlers",
    ]
    assert [call.renderer_kind for call in calls] == [
        "runtime_handlers_impl",
        "runtime_handlers_meta",
    ]
    assert all(call.external_runtime_graphs == () for call in calls)
    assert all(call.package_dependency_graphs == () for call in calls)
    assert {
        call.runtime_to_language_cache.store_language_results for call in calls
    } == {True}
    assert _tool_total_s(result) <= 0.01
    timings_s = _output_phase_timings_s(result)
    assert timings_s["language_plugin_invocation"] <= 0.05
    assert timings_s["total_s"] <= 0.25


@pytest.mark.asyncio
async def test_provider_delta_output_subphase_timings_present_on_blocked_preflight(
    tmp_path: Path,
) -> None:
    result = await workspace_provider.materialize_provider_delta_outputs(
        request=SimpleNamespace(context={}),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan=None,
    )

    assert result["status"] == "provider_delta_output_materialization_blocked"
    assert result["reason"] == "provider_delta_workspace_root_unavailable"
    timings_s = _output_phase_timings_s(result)
    assert "request_context_resolution" in timings_s
    assert "workspace_root_resolution" in timings_s
    assert "language_plugin_invocation" not in timings_s


@pytest.mark.asyncio
async def test_provider_delta_output_subphase_timings_present_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_meta_perf_workspace_manifest(
        workspace_root=tmp_path,
        dependency_package_names=(),
    )
    bundle = build_meta_performance_graph_bundle(
        source_class_count=2,
        dependency_graph_count=0,
        dependency_class_count=0,
    )

    def failing_language_materialization(request: Any) -> object:
        _ = request
        raise RuntimeError("synthetic renderer failure")

    monkeypatch.setattr(
        workspace_provider,
        "materialize_object_config_graph_via_language_plugin",
        failing_language_materialization,
    )

    result = await workspace_provider.materialize_provider_delta_outputs(
        request=_provider_delta_output_request(
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            source_graph=bundle.source_graph,
            runtime_graphs=bundle.dependency_graphs,
        ),
        provider_delta_head_move_applied_receipt={
            "status": "head_move_applied_receipt_ready",
            "head_refs": {},
        },
        provider_delta_oig_commit_receipt={
            "status": "execute_flag_commit_applied",
        },
        provider_delta_typed_operation_plan=_relationship_update_typed_plan(),
    )

    assert result["status"] == "provider_delta_output_materialization_failed"
    assert "synthetic renderer failure" in str(result["error"])
    timings_s = _output_phase_timings_s(result)
    assert "source_graph_resolution" in timings_s
    assert "dependency_graph_resolution" in timings_s
    assert "language_plugin_invocation" in timings_s


def _int_payload(value: object) -> int:
    assert isinstance(value, int)
    return value


def _tool_total_s(result: dict[str, object]) -> float:
    tool_timings = cast(dict[str, object], result["tool_timings_s"])
    total = tool_timings["total"]
    assert isinstance(total, int | float)
    return float(total)


def _output_phase_timings(result: dict[str, object]) -> dict[str, object]:
    timings = result["provider_delta_output_phase_timings"]
    assert isinstance(timings, dict)
    return timings


def _output_phase_timings_s(result: dict[str, object]) -> dict[str, float]:
    timings_s = result["provider_delta_output_phase_timings_s"]
    assert isinstance(timings_s, dict)
    return {
        str(key): float(value)
        for key, value in timings_s.items()
        if isinstance(value, int | float)
    }


def _tuple_payload(value: object) -> tuple[object, ...]:
    assert isinstance(value, tuple)
    return value


def _provider_delta_output_request(
    *,
    workspace_root: Path,
    manifest_path: Path,
    source_graph: object,
    runtime_graphs: tuple[object, ...],
) -> SimpleNamespace:
    return SimpleNamespace(
        workspace_root=workspace_root,
        package={
            "manifest_path": manifest_path.relative_to(workspace_root).as_posix(),
        },
        context={
            "semantic_object_config_graphs": (source_graph,),
            "runtime_object_config_graphs": runtime_graphs,
            "language_materialization_targets": [
                {
                    "target_language_plugin_id": "python",
                    "output_root": "runtime/aware_meta_perf_lab_runtime_impl",
                    "import_root": "aware_meta_perf_lab_runtime",
                    "package_name": "aware_meta_perf_lab_runtime",
                    "materialization_source": "runtime_handlers",
                    "code_package_surface": "runtime",
                    "renderer_kind": "runtime_handlers_impl",
                    "source_is_runtime": True,
                },
                {
                    "target_language_plugin_id": "python",
                    "output_root": "structure/ontology/python_dto",
                    "import_root": "aware_meta_perf_lab_ontology_dto",
                    "package_name": "meta-perf-lab-ontology-dto",
                    "materialization_source": "ontology_dto",
                    "code_package_surface": "structure",
                    "renderer_profile": "ontology_dto",
                },
                {
                    "target_language_plugin_id": "python",
                    "output_root": "structure/ontology/python",
                    "import_root": "aware_meta_perf_lab_ontology",
                    "package_name": "meta-perf-lab-ontology",
                    "materialization_source": "ontology",
                    "code_package_surface": "structure",
                    "renderer_profile": "orm_runtime",
                },
                {
                    "target_language_plugin_id": "python",
                    "output_root": "runtime/aware_meta_perf_lab_runtime_meta",
                    "import_root": "aware_meta_perf_lab_runtime",
                    "package_name": "aware_meta_perf_lab_runtime",
                    "materialization_source": "runtime_handlers",
                    "code_package_surface": "runtime",
                    "renderer_kind": "runtime_handlers_meta",
                    "source_is_runtime": True,
                },
                {
                    "target_language_plugin_id": "sql",
                    "output_root": "structure/ontology/sql",
                    "import_root": "aware_meta_perf_lab_ontology",
                    "package_name": "meta-perf-lab-ontology-sql",
                    "materialization_source": "ontology",
                    "code_package_surface": "structure",
                    "renderer_profile": "orm_runtime",
                },
            ],
        },
    )


def _relationship_update_typed_plan() -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:"
                    "ocg:aware_meta_perf_lab/relationship:device_signals"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.relationship.update",
                "semantic_key": "ocg:aware_meta_perf_lab/relationship:device_signals",
                "ontology_subject_kind": "relationship",
            },
        ),
    }


def _function_impl_update_typed_plan() -> dict[str, object]:
    return {
        "status": "typed_operation_plan_ready",
        "typed_operations": (
            {
                "operation_key": (
                    "meta_ocg_provider_delta:update:"
                    "ocg:aware_meta_perf_lab/function_impl:rename"
                ),
                "operation_family": "update",
                "provider_operation_type": "meta_ocg.function_impl.update",
                "semantic_key": "ocg:aware_meta_perf_lab/function_impl:rename",
                "ontology_subject_kind": "function_impl",
            },
        ),
    }


def _write_meta_perf_workspace_manifest(
    *,
    workspace_root: Path,
    dependency_package_names: tuple[str, ...],
) -> Path:
    package_root = (
        workspace_root / "modules" / "meta_perf_lab" / "structure" / "ontology"
    )
    package_root.mkdir(parents=True)
    _write_module_toml(workspace_root / "modules" / "meta_perf_lab")
    dependency_lines = [
        line
        for package_name in dependency_package_names
        for line in ("", "[[dependencies]]", f'package_name = "{package_name}"')
    ]
    manifest_path = package_root / "aware.toml"
    manifest_path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "meta-perf-lab-ontology"',
                'fqn_prefix = "aware_meta_perf_lab"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_meta_perf_lab"',
                *dependency_lines,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_dependency_manifest(
        workspace_root=workspace_root,
        module_name="meta_perf_dep_0",
        package_name="meta-perf-dep-0-ontology",
        fqn_prefix="aware_meta_perf_dep_0",
    )
    _write_dependency_manifest(
        workspace_root=workspace_root,
        module_name="meta_perf_dep_1",
        package_name="meta-perf-dep-1-ontology",
        fqn_prefix="aware_meta_perf_dep_1",
    )
    return manifest_path


def _write_dependency_manifest(
    *,
    workspace_root: Path,
    module_name: str,
    package_name: str,
    fqn_prefix: str,
) -> None:
    module_root = workspace_root / "modules" / module_name
    package_root = module_root / "structure" / "ontology"
    package_root.mkdir(parents=True)
    _write_module_toml(module_root)
    (package_root / "aware.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                f'package_name = "{package_name}"',
                f'fqn_prefix = "{fqn_prefix}"',
                'kind = "ontology"',
                "",
                "[build]",
                f'environment_slug = "{fqn_prefix}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_module_toml(module_root: Path) -> None:
    module_root.mkdir(parents=True, exist_ok=True)
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
