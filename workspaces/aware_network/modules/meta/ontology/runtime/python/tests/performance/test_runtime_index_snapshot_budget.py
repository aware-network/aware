from __future__ import annotations

from collections.abc import Iterator

import pytest

from aware_meta.runtime.graph_context import (
    _clear_meta_graph_runtime_index_snapshot_cache,
    build_meta_graph_runtime_context,
)

from .budgets import BudgetTimer, assert_metric_lte
from .samples import build_meta_performance_runtime_graph


@pytest.fixture(autouse=True)
def _clear_runtime_index_snapshot_cache() -> Iterator[None]:
    _clear_meta_graph_runtime_index_snapshot_cache()
    yield
    _clear_meta_graph_runtime_index_snapshot_cache()


def test_runtime_index_snapshot_first_build_budget() -> None:
    graph = build_meta_performance_runtime_graph(
        graph_name="meta_perf_snapshot_budget",
        class_count=40,
        attributes_per_class=6,
        include_relationships=True,
    )

    timer = BudgetTimer.start(
        label="runtime_index_snapshot_first_build",
        max_duration_s=0.75,
    )
    context = build_meta_graph_runtime_context(runtime_graphs=(graph,))
    elapsed_s = timer.assert_within_budget()

    assert context.runtime_index_snapshot_cache_status == "miss"
    assert_metric_lte(
        label="runtime_index_snapshot_first_build_s",
        actual=elapsed_s,
        maximum=0.75,
    )
    assert_metric_lte(
        label="runtime_index_snapshot_phase_s",
        actual=context.phase_timings_s["build_runtime_index_snapshot"],
        maximum=0.75,
    )
    assert len(context.index.class_configs_by_id) == 40
    assert len(context.index.attribute_configs_by_id) >= 270
    assert len(context.index.relationships_by_id) >= 39


def test_runtime_index_snapshot_equivalent_graph_cache_hit_budget() -> None:
    graph = build_meta_performance_runtime_graph(
        graph_name="meta_perf_snapshot_cache",
        class_count=40,
        attributes_per_class=6,
        include_relationships=True,
    )
    first = build_meta_graph_runtime_context(runtime_graphs=(graph,))
    equivalent_graph = graph.model_copy(deep=True)

    timer = BudgetTimer.start(
        label="runtime_index_snapshot_equivalent_graph_cache_hit",
        max_duration_s=0.2,
    )
    second = build_meta_graph_runtime_context(runtime_graphs=(equivalent_graph,))
    elapsed_s = timer.assert_within_budget()

    assert first.runtime_index_snapshot_cache_status == "miss"
    assert second.runtime_index_snapshot_cache_status == "hit"
    assert second.index is first.index
    assert_metric_lte(
        label="runtime_index_snapshot_equivalent_graph_cache_hit_s",
        actual=elapsed_s,
        maximum=0.2,
    )
    assert_metric_lte(
        label="runtime_index_snapshot_cache_hit_phase_s",
        actual=second.phase_timings_s["build_runtime_index_snapshot"],
        maximum=0.05,
    )


def test_runtime_index_snapshot_identity_drift_stays_miss_budget() -> None:
    graph = build_meta_performance_runtime_graph(
        graph_name="meta_perf_snapshot_drift",
        class_count=24,
        attributes_per_class=5,
        include_relationships=True,
    )
    first = build_meta_graph_runtime_context(runtime_graphs=(graph,))
    updated_graph = graph.model_copy(deep=True)
    updated_graph.hash = f"{graph.hash}:updated"

    timer = BudgetTimer.start(
        label="runtime_index_snapshot_identity_drift_miss",
        max_duration_s=1.0,
    )
    second = build_meta_graph_runtime_context(runtime_graphs=(updated_graph,))
    elapsed_s = timer.assert_within_budget()

    assert first.runtime_index_snapshot_cache_status == "miss"
    assert second.runtime_index_snapshot_cache_status == "miss"
    assert second.index is not first.index
    assert_metric_lte(
        label="runtime_index_snapshot_identity_drift_miss_s",
        actual=elapsed_s,
        maximum=1.0,
    )
