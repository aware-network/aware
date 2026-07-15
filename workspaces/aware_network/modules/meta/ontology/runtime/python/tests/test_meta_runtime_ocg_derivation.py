from __future__ import annotations

from contextlib import nullcontext
from types import SimpleNamespace
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
import aware_meta.graph.config.runtime_derivation.service as derivation_service
from aware_meta.graph.config.runtime_derivation import (
    RuntimeObjectConfigGraphDerivationResult,
    derive_runtime_object_config_graph,
    derive_runtime_object_config_graphs,
)
import aware_meta.semantic_analysis as semantic_analysis
from aware_meta.semantic_analysis import analyze_meta_ocg_sources
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
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
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
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

_TEST_ROOT = Path(__file__).resolve().parent


def _home_story_ontology_root() -> Path:
    return _TEST_ROOT / "fixtures" / "home_story_ontology"


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

    aliased = derivation_service._external_runtime_graphs_by_id_for_language_transform(  # noqa: SLF001
        source_graph=source,
        external_runtime_graphs=(runtime_storage,),
    )
    ambiguous = derivation_service._external_runtime_graphs_by_id_for_language_transform(  # noqa: SLF001
        source_graph=source,
        external_runtime_graphs=(runtime_storage, duplicate_storage),
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


def test_final_relationship_diagnostics_emit_only_after_unresolved_closure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    source_graph = _projection_stub_graph(
        name="source_runtime",
        fqn_prefix="aware_source",
    )
    target_graph = _projection_stub_graph(
        name="target_runtime",
        fqn_prefix="aware_target",
    )
    source_class = ClassConfig(
        id=uuid4(),
        class_fqn="aware_source.Source",
        name="Source",
    )
    target_class = ClassConfig(
        id=uuid4(),
        class_fqn="aware_target.Target",
        name="Target",
    )
    source_graph.object_config_graph_nodes.append(
        ObjectConfigGraphNode(
            id=uuid4(),
            type=ObjectConfigGraphNodeType.class_,
            node_key=source_class.class_fqn,
            object_config_graph_id=source_graph.id,
            class_config=source_class,
        )
    )
    target_graph.object_config_graph_nodes.append(
        ObjectConfigGraphNode(
            id=uuid4(),
            type=ObjectConfigGraphNodeType.class_,
            node_key=target_class.class_fqn,
            object_config_graph_id=target_graph.id,
            class_config=target_class,
        )
    )
    relationship = ClassConfigRelationship(
        id=uuid4(),
        relationship_key="target",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        class_config_id=source_class.id,
        target_class_config_id=target_class.id,
    )
    source_graph.object_config_graph_relationships = [
        ObjectConfigGraphRelationship(
            object_config_graph_id=source_graph.id,
            target_object_config_graph_id=target_graph.id,
            class_config_relationships=[relationship],
        )
    ]

    derivation_service._emit_final_relationship_endpoint_diagnostics(  # noqa: SLF001
        runtime_graphs=(source_graph, target_graph),
    )
    assert caplog.text == ""

    target_graph.object_config_graph_nodes = []
    derivation_service._emit_final_relationship_endpoint_diagnostics(  # noqa: SLF001
        runtime_graphs=(source_graph, target_graph),
    )
    assert (
        caplog.text.count("Runtime relationship endpoints unresolved after closure")
        == 1
    )
    assert str(relationship.id) in caplog.text
    assert "Source or target class missing for relationship" not in caplog.text


def test_runtime_derivation_lowers_lazy_single_reference_attributes_to_nullable() -> (
    None
):
    graph = _projection_stub_graph(name="meta_runtime", fqn_prefix="aware_meta")
    source_class = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.Owner",
        name="Owner",
    )
    explicit_lazy_target = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.ExplicitLazyTarget",
        name="ExplicitLazyTarget",
    )
    default_lazy_target = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.DefaultLazyTarget",
        name="DefaultLazyTarget",
    )
    eager_target = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.EagerTarget",
        name="EagerTarget",
    )
    collection_target = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.CollectionTarget",
        name="CollectionTarget",
    )

    explicit_lazy_attr = _runtime_class_ref_attr(
        source_class,
        "explicit_lazy_target",
        explicit_lazy_target,
    )
    default_lazy_attr = _runtime_class_ref_attr(
        source_class,
        "default_lazy_target",
        default_lazy_target,
    )
    eager_attr = _runtime_class_ref_attr(source_class, "eager_target", eager_target)
    collection_attr = _runtime_class_ref_attr(
        source_class,
        "collection_target",
        collection_target,
        collection_kind=AttributeCollectionType.list,
    )
    source_class.class_config_attribute_configs = [
        _runtime_class_attr_link(source_class, explicit_lazy_attr, position=0),
        _runtime_class_attr_link(source_class, default_lazy_attr, position=1),
        _runtime_class_attr_link(source_class, eager_attr, position=2),
        _runtime_class_attr_link(source_class, collection_attr, position=3),
    ]
    source_class.class_config_relationships = [
        _runtime_relationship_for_attr(
            source=source_class,
            target=explicit_lazy_target,
            attr=explicit_lazy_attr,
            key="explicit_lazy",
            strategy=ClassConfigRelationshipSideLoadingStrategy.lazy,
        ),
        _runtime_relationship_for_attr(
            source=source_class,
            target=default_lazy_target,
            attr=default_lazy_attr,
            key="default_lazy",
            strategy=None,
        ),
        _runtime_relationship_for_attr(
            source=source_class,
            target=eager_target,
            attr=eager_attr,
            key="eager",
            strategy=ClassConfigRelationshipSideLoadingStrategy.eager,
        ),
        _runtime_relationship_for_attr(
            source=source_class,
            target=collection_target,
            attr=collection_attr,
            key="collection",
            strategy=ClassConfigRelationshipSideLoadingStrategy.lazy,
        ),
    ]
    graph.object_config_graph_nodes = [
        _runtime_class_node(graph, source_class),
        _runtime_class_node(graph, explicit_lazy_target),
        _runtime_class_node(graph, default_lazy_target),
        _runtime_class_node(graph, eager_target),
        _runtime_class_node(graph, collection_target),
    ]

    lowered_count = derivation_service._normalize_lazy_relationship_reference_attributes(  # noqa: SLF001
        graph
    )

    assert lowered_count == 2
    assert explicit_lazy_attr.is_required is False
    assert explicit_lazy_attr.default_value == "null"
    assert default_lazy_attr.is_required is False
    assert default_lazy_attr.default_value == "null"
    assert eager_attr.is_required is True
    assert eager_attr.default_value is None
    assert collection_attr.is_required is True
    assert collection_attr.default_value is None


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


def _runtime_class_ref_attr(
    owner: ClassConfig,
    name: str,
    target: ClassConfig,
    *,
    collection_kind: AttributeCollectionType = AttributeCollectionType.single,
) -> AttributeConfig:
    descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        collection_kind=collection_kind,
        class_config=target,
        class_config_id=target.id,
    )
    return AttributeConfig(
        owner_key=owner.class_fqn,
        name=name,
        is_public=True,
        is_required=True,
        is_unique=False,
        is_virtual=False,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )


def _runtime_class_attr_link(
    owner: ClassConfig,
    attr: AttributeConfig,
    *,
    position: int,
) -> ClassConfigAttributeConfig:
    return ClassConfigAttributeConfig(
        class_config_id=owner.id,
        attribute_config=attr,
        attribute_config_id=attr.id,
        position=position,
    )


def _runtime_relationship_for_attr(
    *,
    source: ClassConfig,
    target: ClassConfig,
    attr: AttributeConfig,
    key: str,
    strategy: ClassConfigRelationshipSideLoadingStrategy | None,
) -> ClassConfigRelationship:
    relationship = ClassConfigRelationship(
        id=uuid4(),
        class_config_id=source.id,
        target_class_config_id=target.id,
        relationship_key=key,
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        forward_loading_strategy=strategy,
    )
    relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=relationship.id,
            attribute_config_id=attr.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    return relationship


def _runtime_class_node(
    graph: ObjectConfigGraph,
    class_config: ClassConfig,
) -> ObjectConfigGraphNode:
    return ObjectConfigGraphNode(
        id=uuid4(),
        type=ObjectConfigGraphNodeType.class_,
        node_key=class_config.class_fqn,
        object_config_graph_id=graph.id,
        class_config=class_config,
    )
