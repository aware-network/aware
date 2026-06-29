from __future__ import annotations

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.materialization import (
    LanguagePluginMaterializationRequest,
    RuntimeToLanguageLoweringCache,
    materialize_object_config_graph_via_language_plugin,
)
from aware_meta.materialization.language_service import (
    RuntimeObjectConfigGraphDerivationCache,
)
from aware_meta.graph.config.runtime_derivation.clone import (
    clone_source_graph_for_runtime_handoff,
)

from .budgets import (
    BudgetTimer,
    assert_metric_gte,
    assert_metric_lte,
    count_steps_with_name,
    metric_int,
    sum_steps_with_name,
)
from .fake_sql_plugin import (
    PerfRuntimeToSqlTransformer,
    isolated_meta_language_plugin_registries,
    register_perf_sql_plugin,
)
from .samples import build_meta_performance_graph_bundle


class _RecordingTimer:
    def __init__(self) -> None:
        self.steps: list[tuple[str, float]] = []

    def add(self, name: str, duration_s: float) -> None:
        self.steps.append((name, duration_s))


def test_runtime_to_language_budget_reuses_request_scoped_caches() -> None:
    bundle = build_meta_performance_graph_bundle(
        source_class_count=10,
        dependency_graph_count=2,
        dependency_class_count=5,
    )
    runtime_to_language_cache = RuntimeToLanguageLoweringCache()
    runtime_derivation_cache = RuntimeObjectConfigGraphDerivationCache()

    with isolated_meta_language_plugin_registries():
        register_perf_sql_plugin()
        first_timer = BudgetTimer.start(
            label="runtime_to_language_first_materialization",
            max_duration_s=5.0,
        )
        first = materialize_object_config_graph_via_language_plugin(
            LanguagePluginMaterializationRequest(
                source_graph=bundle.source_graph,
                target_language_plugin_id=CodeLanguage.sql,
                external_runtime_graphs=bundle.dependency_graphs,
                package_dependency_graphs=bundle.dependency_graphs,
                source_is_runtime=True,
                reuse_external_runtime_graphs=True,
                runtime_to_language_cache=runtime_to_language_cache,
                runtime_derivation_cache=runtime_derivation_cache,
            )
        )
        first_elapsed_s = first_timer.assert_within_budget()

        second_timer = BudgetTimer.start(
            label="runtime_to_language_second_materialization_cache_hit",
            max_duration_s=1.0,
        )
        second = materialize_object_config_graph_via_language_plugin(
            LanguagePluginMaterializationRequest(
                source_graph=bundle.source_graph,
                target_language_plugin_id=CodeLanguage.sql,
                external_runtime_graphs=bundle.dependency_graphs,
                package_dependency_graphs=bundle.dependency_graphs,
                source_is_runtime=True,
                reuse_external_runtime_graphs=True,
                runtime_to_language_cache=runtime_to_language_cache,
                runtime_derivation_cache=runtime_derivation_cache,
            )
        )
        second_elapsed_s = second_timer.assert_within_budget()

    assert first.status == "succeeded"
    assert second.status == "succeeded"
    assert_metric_lte(
        label="second_materialization_elapsed_s",
        actual=second_elapsed_s,
        maximum=max(first_elapsed_s * 3.0, 0.25),
    )

    first_clone_count = count_steps_with_name(first.tool_steps, ".clone_graph")
    second_clone_count = count_steps_with_name(second.tool_steps, ".clone_graph")
    assert first_clone_count == 3
    assert second_clone_count == 0
    assert (
        count_steps_with_name(
            first.tool_steps,
            "runtime_derivation:clone_runtime_graph.shallow",
        )
        == 1
    )
    assert_metric_lte(
        label="first_clone_graph_s",
        actual=sum_steps_with_name(first.tool_steps, ".clone_graph"),
        maximum=4.0,
    )
    assert sum_steps_with_name(second.tool_steps, ".clone_graph") == 0.0
    assert count_steps_with_name(second.tool_steps, "runtime_derivation:") == 0

    derivation_cache = second.metrics["runtime_derivation_cache"]
    assert isinstance(derivation_cache, dict)
    assert metric_int(derivation_cache, "entry_count") == 1
    assert metric_int(derivation_cache, "miss_count") == 1
    assert metric_int(derivation_cache, "store_count") == 1
    assert_metric_gte(
        label="runtime_derivation_cache_hit_count",
        actual=metric_int(derivation_cache, "hit_count"),
        minimum=1,
    )

    lowering_cache = second.metrics["runtime_to_language_cache"]
    assert isinstance(lowering_cache, dict)
    assert metric_int(lowering_cache, "entry_count") == 3
    assert metric_int(lowering_cache, "miss_count") == 3
    assert metric_int(lowering_cache, "store_count") == 3
    assert_metric_gte(
        label="runtime_to_language_cache_hit_count",
        actual=metric_int(lowering_cache, "hit_count"),
        minimum=3,
    )
    assert len(PerfRuntimeToSqlTransformer.calls) == 3


def test_source_runtime_handoff_clone_is_shallow_and_mutation_isolated() -> None:
    bundle = build_meta_performance_graph_bundle(
        source_class_count=3,
        dependency_graph_count=0,
    )
    source = bundle.source_graph
    timer = _RecordingTimer()

    handoff = clone_source_graph_for_runtime_handoff(source, timer=timer)

    source_class = source.object_config_graph_nodes[0].class_config
    handoff_class = handoff.object_config_graph_nodes[0].class_config
    assert source_class is not None
    assert handoff_class is not None
    assert handoff_class is not source_class
    assert handoff_class.class_config_attribute_configs is not (
        source_class.class_config_attribute_configs
    )
    assert handoff_class.class_config_relationships is not (
        source_class.class_config_relationships
    )
    assert handoff_class.class_config_attribute_configs[0] is not (
        source_class.class_config_attribute_configs[0]
    )
    assert handoff_class.class_config_attribute_configs[0].attribute_config is not (
        source_class.class_config_attribute_configs[0].attribute_config
    )

    source_attr_count = len(source_class.class_config_attribute_configs)
    source_relationship_count = len(source_class.class_config_relationships)
    handoff_class.class_config_attribute_configs.clear()
    handoff_class.class_config_relationships.clear()

    assert len(source_class.class_config_attribute_configs) == source_attr_count
    assert len(source_class.class_config_relationships) == source_relationship_count
    assert [name for name, _ in timer.steps] == ["clone_source_graph_handoff.shallow"]
