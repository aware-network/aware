from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
import sys
from pathlib import Path
from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
import aware_meta.graph.config.runtime_derivation.service as derivation_service
from aware_meta.graph.config.runtime_derivation import (
    RuntimeObjectConfigGraphDerivationResult,
    derive_runtime_object_config_graph,
    derive_runtime_object_config_graphs,
)
import aware_meta.semantic_analysis as semantic_analysis
from aware_meta.semantic_analysis import analyze_meta_ocg_sources
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipType,
)
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_binding import (
    ObjectProjectionGraphBinding,
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


def test_meta_runtime_derivation_turns_home_story_source_ocg_into_runtime_truth() -> (
    None
):
    package_root = _home_story_ontology_root()
    source_files = tuple(
        sorted(
            path.relative_to(package_root)
            for path in (package_root / "aware").rglob("*.aware")
        )
    )
    analysis = analyze_meta_ocg_sources(
        package_root=package_root,
        source_files=source_files,
        manifest_path=package_root / "aware.toml",
    )
    source_graph = analysis.source_object_config_graph
    assert source_graph is not None

    before_imports = set(sys.modules)
    result = derive_runtime_object_config_graph(source_graph)
    newly_imported_modules = set(sys.modules) - before_imports

    runtime_graph = result.runtime_graph
    timing_names = {step.name for step in result.timings}
    assert result.source_graph is source_graph
    assert runtime_graph is not source_graph
    assert result.source_graph_role == "compiler_ir"
    assert result.runtime_graph_role == "runtime_ocg"
    assert result.source_language is CodeLanguage.aware
    assert result.runtime_language is CodeLanguage.aware
    assert result.source_graph_hash == source_graph.hash
    assert result.runtime_graph_hash == runtime_graph.hash
    assert result.source_graph_hash != result.runtime_graph_hash
    assert runtime_graph.object_projection_graphs
    assert tuple(opg.name for opg in runtime_graph.object_projection_graphs) == (
        "Home",
    )
    assert (
        sum(
            1
            for node in runtime_graph.object_config_graph_nodes
            if node.type is ObjectConfigGraphNodeType.relationship
        )
        == 4
    )
    assert "clone_source_graph_handoff.shallow" in timing_names
    assert "clone_source_graph_handoff.deepcopy" not in timing_names
    assert any(
        class_config.class_config_relationships
        for node in runtime_graph.object_config_graph_nodes
        if (class_config := node.class_config) is not None
    )
    forbidden_materializer_prefixes = (
        "aware_environment_artifacts",
        "aware_structure.materialization",
        "aware_structure.repository",
        "aware_structure.setup_language_plugins",
    )
    assert not any(
        module_name.startswith(forbidden_materializer_prefixes)
        for module_name in newly_imported_modules
    )


def test_runtime_derivation_external_projection_pass_can_see_source_graph(
    monkeypatch,
) -> None:
    source_graph = _projection_stub_graph(name="source", fqn_prefix="aware_source")
    external_a = _projection_stub_graph(name="external_a", fqn_prefix="aware_a")
    external_b = _projection_stub_graph(name="external_b", fqn_prefix="aware_b")
    calls: list[tuple[str, tuple[str, ...], bool]] = []

    def _fake_build_object_projection_graphs(
        graph: ObjectConfigGraph,
        *,
        external_graphs: list[ObjectConfigGraph],
        provision_portals: bool = True,
    ) -> list[object]:
        calls.append(
            (
                graph.name,
                tuple(external.name for external in external_graphs),
                provision_portals,
            )
        )
        return []

    monkeypatch.setattr(
        derivation_service,
        "build_object_projection_graphs",
        _fake_build_object_projection_graphs,
    )

    derivation_service._derive_runtime_projection_graphs(
        runtime_graph=source_graph,
        runtime_external_graphs=(external_a, external_b),
        source_is_runtime=False,
        timer=_NoopTimer(),
    )

    assert calls == [
        ("external_a", ("source", "external_b"), False),
        ("external_b", ("source", "external_a"), False),
        ("source", ("external_a", "external_b"), False),
        ("external_a", ("source", "external_b"), True),
        ("external_b", ("source", "external_a"), True),
        ("source", ("external_a", "external_b"), True),
    ]


def test_semantic_analysis_passes_attached_external_opgs_as_runtime_graphs(
    monkeypatch,
) -> None:
    package_root = _home_story_ontology_root()
    source_files = tuple(
        sorted(
            path.relative_to(package_root)
            for path in (package_root / "aware").rglob("*.aware")
        )
    )
    runtime_dependency = _projection_stub_graph(
        name="runtime_dep",
        fqn_prefix="aware_dep",
    )
    runtime_dependency.object_projection_graphs = [
        ObjectProjectionGraph(
            id=uuid4(),
            name="DependencyProjection",
            key="aware_dep:DependencyProjection",
            object_config_graph_id=runtime_dependency.id,
            language=CodeLanguage.aware,
            projection_hash="sha256:dependency-projection",
        )
    ]
    captured: dict[str, tuple[ObjectConfigGraph, ...]] = {}

    def _fake_derive_runtime_object_config_graph(
        source_graph: ObjectConfigGraph,
        *,
        external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
        include_projection_graphs: bool = True,
    ) -> RuntimeObjectConfigGraphDerivationResult:
        captured["external_runtime_graphs"] = external_runtime_graphs
        return RuntimeObjectConfigGraphDerivationResult(
            source_graph=source_graph,
            runtime_graph=source_graph,
            runtime_external_graphs=external_runtime_graphs,
            source_language=source_graph.language,
            runtime_language=source_graph.language,
            source_graph_hash=source_graph.hash,
            runtime_graph_hash=source_graph.hash,
            timings=(),
            metrics={"include_projection_graphs": include_projection_graphs},
        )

    def _fail_derive_runtime_object_config_graphs(
        *args, **kwargs
    ):  # noqa: ANN002, ANN003
        raise AssertionError("attached runtime dependencies must not be rederived")

    monkeypatch.setattr(
        semantic_analysis,
        "derive_runtime_object_config_graph",
        _fake_derive_runtime_object_config_graph,
    )
    monkeypatch.setattr(
        semantic_analysis,
        "derive_runtime_object_config_graphs",
        _fail_derive_runtime_object_config_graphs,
    )

    analyze_meta_ocg_sources(
        package_root=package_root,
        source_files=source_files,
        manifest_path=package_root / "aware.toml",
        external_graphs=(runtime_dependency,),
    )

    assert captured["external_runtime_graphs"] == (runtime_dependency,)


def test_runtime_derivation_can_skip_external_projection_pass_without_portals(
    monkeypatch,
) -> None:
    source_graph = _projection_stub_graph(name="source", fqn_prefix="aware_source")
    external_a = _projection_stub_graph(name="external_a", fqn_prefix="aware_a")
    external_b = _projection_stub_graph(name="external_b", fqn_prefix="aware_b")
    calls: list[tuple[str, tuple[str, ...], bool]] = []

    def _fake_build_object_projection_graphs(
        graph: ObjectConfigGraph,
        *,
        external_graphs: list[ObjectConfigGraph],
        provision_portals: bool = True,
    ) -> list[object]:
        calls.append(
            (
                graph.name,
                tuple(external.name for external in external_graphs),
                provision_portals,
            )
        )
        return []

    monkeypatch.setattr(
        derivation_service,
        "build_object_projection_graphs",
        _fake_build_object_projection_graphs,
    )

    derivation_service._derive_runtime_projection_graphs(
        runtime_graph=source_graph,
        runtime_external_graphs=(external_a, external_b),
        derive_external_projection_graphs=False,
        source_is_runtime=False,
        timer=_NoopTimer(),
    )

    assert calls == [
        ("source", ("external_a", "external_b"), True),
    ]


def test_runtime_derivation_keeps_external_projection_pass_for_portals(
    monkeypatch,
) -> None:
    source_graph = _projection_stub_graph(
        name="source",
        fqn_prefix="aware_source",
        target_projection_name="aware_a.Default",
    )
    external_a = _projection_stub_graph(name="external_a", fqn_prefix="aware_a")
    external_b = _projection_stub_graph(name="external_b", fqn_prefix="aware_b")
    calls: list[tuple[str, tuple[str, ...], bool]] = []

    def _fake_build_object_projection_graphs(
        graph: ObjectConfigGraph,
        *,
        external_graphs: list[ObjectConfigGraph],
        provision_portals: bool = True,
    ) -> list[object]:
        calls.append(
            (
                graph.name,
                tuple(external.name for external in external_graphs),
                provision_portals,
            )
        )
        return []

    monkeypatch.setattr(
        derivation_service,
        "build_object_projection_graphs",
        _fake_build_object_projection_graphs,
    )

    derivation_service._derive_runtime_projection_graphs(
        runtime_graph=source_graph,
        runtime_external_graphs=(external_a, external_b),
        derive_external_projection_graphs=False,
        source_is_runtime=False,
        timer=_NoopTimer(),
    )

    assert calls == [
        ("external_a", ("source", "external_b"), False),
        ("external_b", ("source", "external_a"), False),
        ("source", ("external_a", "external_b"), False),
        ("external_a", ("source", "external_b"), True),
        ("external_b", ("source", "external_a"), True),
        ("source", ("external_a", "external_b"), True),
    ]


def test_runtime_derivation_graph_bundle_derives_cross_graph_projection_pass(
    monkeypatch,
) -> None:
    source = _projection_stub_graph(name="source", fqn_prefix="aware_source")
    external_a = _projection_stub_graph(name="external_a", fqn_prefix="aware_a")
    external_b = _projection_stub_graph(name="external_b", fqn_prefix="aware_b")
    derive_calls: list[tuple[str, tuple[str, ...], bool]] = []
    projection_calls: list[tuple[str, tuple[str, ...], bool]] = []

    def _fake_derive_runtime_object_config_graph(
        graph: ObjectConfigGraph,
        *,
        external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
        include_projection_graphs: bool,
    ) -> SimpleNamespace:
        derive_calls.append(
            (
                graph.name,
                tuple(external.name for external in external_runtime_graphs),
                include_projection_graphs,
            )
        )
        return SimpleNamespace(runtime_graph=graph)

    def _fake_build_object_projection_graphs(
        graph: ObjectConfigGraph,
        *,
        external_graphs: list[ObjectConfigGraph],
        provision_portals: bool = True,
    ) -> list[object]:
        projection_calls.append(
            (
                graph.name,
                tuple(external.name for external in external_graphs),
                provision_portals,
            )
        )
        return []

    monkeypatch.setattr(
        derivation_service,
        "derive_runtime_object_config_graph",
        _fake_derive_runtime_object_config_graph,
    )
    monkeypatch.setattr(
        derivation_service,
        "build_object_projection_graphs",
        _fake_build_object_projection_graphs,
    )

    assert derive_runtime_object_config_graphs((source, external_a, external_b)) == (
        source,
        external_a,
        external_b,
    )
    assert derive_calls == [
        ("source", (), False),
        ("external_a", (), False),
        ("external_b", (), False),
        ("source", ("external_a", "external_b"), False),
        ("external_a", ("source", "external_b"), False),
        ("external_b", ("source", "external_a"), False),
    ]
    assert projection_calls == [
        ("source", ("external_a", "external_b"), False),
        ("external_a", ("source", "external_b"), False),
        ("external_b", ("source", "external_a"), False),
        ("source", ("external_a", "external_b"), True),
        ("external_a", ("source", "external_b"), True),
        ("external_b", ("source", "external_a"), True),
    ]


def test_runtime_derivation_graph_bundle_uses_supplied_external_runtime_graphs(
    monkeypatch,
) -> None:
    source = _projection_stub_graph(name="source", fqn_prefix="aware_source")
    sibling = _projection_stub_graph(name="sibling", fqn_prefix="aware_sibling")
    context_graph = _projection_stub_graph(
        name="context_runtime",
        fqn_prefix="aware_context",
    )
    derive_calls: list[tuple[str, tuple[str, ...], bool]] = []
    projection_calls: list[tuple[str, tuple[str, ...], bool]] = []

    def _fake_derive_runtime_object_config_graph(
        graph: ObjectConfigGraph,
        *,
        external_runtime_graphs: tuple[ObjectConfigGraph, ...] = (),
        include_projection_graphs: bool,
    ) -> SimpleNamespace:
        derive_calls.append(
            (
                graph.name,
                tuple(external.name for external in external_runtime_graphs),
                include_projection_graphs,
            )
        )
        return SimpleNamespace(runtime_graph=graph)

    def _fake_build_object_projection_graphs(
        graph: ObjectConfigGraph,
        *,
        external_graphs: list[ObjectConfigGraph],
        provision_portals: bool = True,
    ) -> list[object]:
        projection_calls.append(
            (
                graph.name,
                tuple(external.name for external in external_graphs),
                provision_portals,
            )
        )
        return []

    monkeypatch.setattr(
        derivation_service,
        "derive_runtime_object_config_graph",
        _fake_derive_runtime_object_config_graph,
    )
    monkeypatch.setattr(
        derivation_service,
        "build_object_projection_graphs",
        _fake_build_object_projection_graphs,
    )

    assert derive_runtime_object_config_graphs(
        (source, sibling),
        external_runtime_graphs=(context_graph,),
    ) == (
        source,
        sibling,
    )
    assert derive_calls == [
        ("source", ("context_runtime",), False),
        ("sibling", ("context_runtime",), False),
        ("source", ("context_runtime", "sibling"), False),
        ("sibling", ("context_runtime", "source"), False),
    ]
    assert projection_calls == [
        ("source", ("context_runtime", "sibling"), False),
        ("sibling", ("context_runtime", "source"), False),
        ("source", ("context_runtime", "sibling"), True),
        ("sibling", ("context_runtime", "source"), True),
    ]


def test_runtime_derivation_rebinds_cached_source_relationship_targets_to_runtime_externals() -> (
    None
):
    source = _projection_stub_graph(name="source", fqn_prefix="aware_source")
    stale_source_history = _projection_stub_graph(
        name="history_source",
        fqn_prefix="aware_history",
    )
    runtime_history = _projection_stub_graph(
        name="history_runtime",
        fqn_prefix="aware_history",
    )
    relationship = ObjectConfigGraphRelationship(
        object_config_graph_id=source.id,
        target_object_config_graph=stale_source_history,
        target_object_config_graph_id=stale_source_history.id,
    )
    source.object_config_graph_relationships = [relationship]

    derivation_service._rebind_relationship_targets_to_runtime_closure(
        runtime_graph=source,
        runtime_external_graphs=(runtime_history,),
    )

    assert relationship.target_object_config_graph is runtime_history
    assert relationship.target_object_config_graph_id == runtime_history.id


def test_runtime_derivation_language_transform_aliases_source_relationship_target_ids() -> (
    None
):
    source = _projection_stub_graph(name="source", fqn_prefix="aware_source")
    source_storage = _projection_stub_graph(
        name="storage_source",
        fqn_prefix="aware_storage",
    )
    runtime_storage = _projection_stub_graph(
        name="storage_runtime",
        fqn_prefix="aware_storage",
    )
    duplicate_storage = _projection_stub_graph(
        name="storage_duplicate",
        fqn_prefix="aware_storage",
    )
    relationship = ObjectConfigGraphRelationship(
        object_config_graph_id=source.id,
        target_object_config_graph=source_storage,
        target_object_config_graph_id=source_storage.id,
    )
    source.object_config_graph_relationships = [relationship]

    aliased = (
        derivation_service._external_runtime_graphs_by_id_for_language_transform(  # noqa: SLF001
            source_graph=source,
            external_runtime_graphs=(runtime_storage,),
        )
    )
    ambiguous = (
        derivation_service._external_runtime_graphs_by_id_for_language_transform(  # noqa: SLF001
            source_graph=source,
            external_runtime_graphs=(runtime_storage, duplicate_storage),
        )
    )

    assert aliased[runtime_storage.id] is runtime_storage
    assert aliased[source_storage.id] is runtime_storage
    assert ambiguous[runtime_storage.id] is runtime_storage
    assert ambiguous[duplicate_storage.id] is duplicate_storage
    assert source_storage.id not in ambiguous


def test_runtime_derivation_preserves_existing_external_runtime_class_relationships() -> (
    None
):
    graph = _projection_stub_graph(name="meta_runtime", fqn_prefix="aware_meta")
    source_class = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.graph.instance.ObjectInstanceGraphCommit",
        name="ObjectInstanceGraphCommit",
    )
    external_target_class_id = uuid4()
    relationship = ClassConfigRelationship(
        id=uuid4(),
        relationship_key="commit",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        class_config_id=source_class.id,
        target_class_config_id=external_target_class_id,
    )
    source_class.class_config_relationships = [relationship]
    graph.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            id=uuid4(),
            type=ObjectConfigGraphNodeType.class_,
            node_key="aware_meta.graph.instance.ObjectInstanceGraphCommit",
            object_config_graph_id=graph.id,
            class_config=source_class,
        )
    ]

    derivation_service._attach_relationships_to_class_configs(
        graph,
        preserve_existing_attached=True,
    )

    assert [item.id for item in source_class.class_config_relationships] == [
        relationship.id
    ]


class _NoopTimer:
    def step(self, _: str):
        return nullcontext()


def _projection_stub_graph(
    *,
    name: str,
    fqn_prefix: str,
    target_projection_name: str | None = None,
) -> ObjectConfigGraph:
    graph_id = uuid4()
    declaration_id = uuid4()
    bindings = []
    if target_projection_name is not None:
        bindings.append(
            ObjectProjectionGraphBinding(
                id=uuid4(),
                fqn_prefix=fqn_prefix,
                namespace="",
                class_name="Root",
                attribute_name="target",
                target_projection_name=target_projection_name,
                object_projection_graph_declaration_id=declaration_id,
            )
        )
    return ObjectConfigGraph(
        id=graph_id,
        name=name,
        hash=f"hash:{name}",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
        object_projection_graph_declarations=[
            ObjectProjectionGraphDeclaration(
                id=declaration_id,
                object_config_graph_id=graph_id,
                key=f"{fqn_prefix}:Default",
                projection_name="Default",
                object_projection_graph_bindings=bindings,
            )
        ],
    )
