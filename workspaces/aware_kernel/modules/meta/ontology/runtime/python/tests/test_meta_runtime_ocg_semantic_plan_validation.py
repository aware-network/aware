from __future__ import annotations

from pathlib import Path

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)
from aware_meta.semantic_analysis import (
    analyze_meta_ocg_code_package_delta,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _home_story_ontology_root() -> Path:
    return (
        _REPO_ROOT
        / "modules"
        / "meta"
        / "runtime"
        / "tests"
        / "fixtures"
        / "home_story_ontology"
    )


def _home_story_source_files(package_root: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path.relative_to(package_root)
            for path in (package_root / "aware").rglob("*.aware")
        )
    )


def _delta_for_home_story_source(
    *,
    package_root: Path,
    relative_path: str,
) -> CodePackageDelta:
    return CodePackageDelta(
        package_name="home-ontology",
        package_root=".",
        sources_root="aware",
        manifest_relative_path="aware.toml",
        authority_kind="workspace_sdk",
        source_revision_id="meta-runtime-ocg-plan-validation",
        paths=[
            CodePackageDeltaPath(
                relative_path=relative_path,
                kind=CodePackageDeltaKind.update,
                content_text=(package_root / "aware" / relative_path).read_text(
                    encoding="utf-8"
                ),
                language=CodeLanguage.aware,
                is_structural=True,
            )
        ],
    )


def test_home_story_changed_class_includes_runtime_relationship_node_deltas() -> None:
    package_root = _home_story_ontology_root()
    result = analyze_meta_ocg_code_package_delta(
        package_root=package_root,
        source_files=_home_story_source_files(package_root),
        manifest_path=package_root / "aware.toml",
        code_package_delta=_delta_for_home_story_source(
            package_root=package_root,
            relative_path="home/home.aware",
        ),
    )

    assert result.source_object_config_graph is not None
    assert result.object_config_graph is not None
    assert result.runtime_derivation is not None
    assert result.object_config_graph is result.runtime_derivation.runtime_graph
    assert result.source_object_config_graph is result.runtime_derivation.source_graph
    assert result.source_object_config_graph.hash != result.object_config_graph.hash

    relationship_deltas = tuple(
        delta
        for delta in result.change_preview.semantic_deltas
        if delta.subject_type == "aware_meta.ObjectConfigGraphNode"
        and (delta.after_payload or {}).get("node_type") == "relationship"
    )
    assert relationship_deltas
    assert {
        (delta.after_payload or {}).get("entity_name") for delta in relationship_deltas
    } == {"doors", "tvs"}
    assert all("home/home.aware" in delta.source_refs for delta in relationship_deltas)
    assert all(
        delta.metadata["semantic_truth_graph"] == "runtime_ocg"
        for delta in relationship_deltas
    )
    assert all(
        delta.metadata["runtime_node_type"] == "relationship"
        for delta in relationship_deltas
    )


def test_meta_preview_deltas_and_events_are_runtime_graph_scoped() -> None:
    package_root = _home_story_ontology_root()
    result = analyze_meta_ocg_code_package_delta(
        package_root=package_root,
        source_files=_home_story_source_files(package_root),
        manifest_path=package_root / "aware.toml",
        code_package_delta=_delta_for_home_story_source(
            package_root=package_root,
            relative_path="home/home.aware",
        ),
    )
    assert result.runtime_derivation is not None
    runtime_hash = result.runtime_derivation.runtime_graph_hash
    source_hash = result.runtime_derivation.source_graph_hash

    assert runtime_hash != source_hash
    assert result.change_preview.semantic_deltas
    assert result.change_preview.semantic_events
    for delta in result.change_preview.semantic_deltas:
        assert delta.metadata["semantic_truth_graph"] == "runtime_ocg"
        assert delta.metadata["source_graph_role"] == "compiler_ir"
        assert delta.metadata["runtime_graph_role"] == "runtime_ocg"
        assert delta.metadata["source_graph_hash"] == source_hash
        assert delta.metadata["runtime_graph_hash"] == runtime_hash
    for event in result.change_preview.semantic_events:
        assert event.metadata["semantic_truth_graph"] == "runtime_ocg"
        assert event.metadata["source_graph_role"] == "compiler_ir"
        assert event.metadata["runtime_graph_role"] == "runtime_ocg"
        assert event.metadata["source_graph_hash"] == source_hash
        assert event.metadata["runtime_graph_hash"] == runtime_hash


def test_home_story_runtime_relationship_nodes_are_in_runtime_preview_keys() -> None:
    package_root = _home_story_ontology_root()
    result = analyze_meta_ocg_code_package_delta(
        package_root=package_root,
        source_files=_home_story_source_files(package_root),
        manifest_path=package_root / "aware.toml",
        code_package_delta=_delta_for_home_story_source(
            package_root=package_root,
            relative_path="home/home.aware",
        ),
    )
    assert result.object_config_graph is not None
    relationship_node_keys = {
        f"ocg:{result.object_config_graph.fqn_prefix}/node:{node.node_key}"
        for node in result.object_config_graph.object_config_graph_nodes
        if node.type is ObjectConfigGraphNodeType.relationship
    }

    affected_relationship_keys = tuple(
        key
        for key in result.change_preview.affected_node_keys
        if key in relationship_node_keys
    )
    assert affected_relationship_keys == (
        "ocg:aware_home/node:aware_home.default.home.Home:doors:one_to_many:aware_home.default.home.Door",
        "ocg:aware_home/node:aware_home.default.home.Home:tvs:one_to_many:aware_home.default.home.Tv",
    )
