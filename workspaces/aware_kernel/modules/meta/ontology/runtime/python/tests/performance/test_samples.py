from __future__ import annotations

from pathlib import Path

from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

from .samples import (
    build_meta_performance_graph_bundle,
    build_meta_performance_runtime_graph,
    meta_performance_sample_package_root,
)


def test_meta_performance_sample_package_is_meta_owned() -> None:
    root = meta_performance_sample_package_root()

    assert (root / "aware.ontology.toml").is_file()
    assert (root / "structure" / "ontology" / "aware.toml").is_file()
    assert {path.relative_to(root).as_posix() for path in root.rglob("*.aware")} == {
        "structure/ontology/aware/lab/device.aware",
        "structure/ontology/aware/lab/signal.aware",
    }

    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )
    assert "aware_home" not in text
    assert "home-ontology" not in text
    assert "workspaces/aware_home" not in text


def test_meta_performance_runtime_graph_sample_is_deterministic() -> None:
    first = build_meta_performance_runtime_graph(
        class_count=5,
        attributes_per_class=3,
    )
    second = build_meta_performance_runtime_graph(
        class_count=5,
        attributes_per_class=3,
    )

    assert isinstance(first, ObjectConfigGraph)
    assert first.id == second.id
    assert first.hash == second.hash
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert len(first.object_config_graph_nodes) == 5

    class_configs = [
        node.class_config
        for node in first.object_config_graph_nodes
        if node.class_config is not None
    ]
    assert len(class_configs) == 5
    attribute_counts = [
        len(item.class_config_attribute_configs) for item in class_configs
    ]
    assert attribute_counts == [4, 4, 4, 4, 3]
    assert all(len(item.class_config_function_configs) == 1 for item in class_configs)
    assert sum(len(item.class_config_relationships) for item in class_configs) == 4


def test_meta_performance_graph_bundle_has_source_and_dependency_closure() -> None:
    bundle = build_meta_performance_graph_bundle(
        source_class_count=6,
        dependency_graph_count=2,
        dependency_class_count=3,
    )

    assert bundle.source_graph.fqn_prefix == "aware_meta_perf_lab"
    assert tuple(graph.fqn_prefix for graph in bundle.dependency_graphs) == (
        "aware_meta_perf_dep_0",
        "aware_meta_perf_dep_1",
    )
    assert len(bundle.source_graph.object_config_graph_nodes) == 6
    assert [
        len(graph.object_config_graph_nodes) for graph in bundle.dependency_graphs
    ] == [
        3,
        3,
    ]
    assert all(
        isinstance(path, Path) for path in (meta_performance_sample_package_root(),)
    )
