"""Canonical tests for the shared Aware→Runtime IR transformer."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from uuid import UUID

import pytest

from aware_code.builder import build_code_from_file
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code import Code
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.graph.config.object_config_graph_relationship import (
    ObjectConfigGraphRelationship,
)

from aware_meta.class_.config.relationship_side_loading_config import (
    ClassConfigRelationshipSideLoadingConfig,
    ClassConfigRelationshipSideLoadingEntry,
)
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code

from aware_grammar.transformers.aware_to_runtime_transformer import AwareToRuntimeTransformer
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN


# Needed for `build_code_from_file(..., language=CodeLanguage.aware, ...)`.
CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)


def _build_graph_from_aware_source(
    *,
    tmp_path: Path,
    source: str,
    package: str = "test_pkg",
    domain: str = "test_domain",
    schema: str = "test_schema",
) -> tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]:
    file_path = tmp_path / "sample.aware"
    _ = file_path.write_text(source, encoding="utf-8")
    code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(file_path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    file_codes: list[tuple[str, Code]] = [(str(file_path), code)]

    namespace_by_code_id: dict[UUID, NamespacePath] = {
        code.id: NamespacePath(
            package=package,
            namespace=_test_namespace(domain=domain, schema=schema),
        )
        for _, code in file_codes
    }
    result = build_object_config_graph_from_code(
        name="test_graph",
        description="test_graph",
        fqn_prefix=package,
        file_codes=file_codes,
        namespace_by_code_id=namespace_by_code_id,
        external_graphs=None,
    )
    return result.graph, namespace_by_code_id


def _test_namespace(*, domain: str, schema: str) -> str:
    parts: list[str] = []
    for value in (domain, schema):
        segment = value.strip()
        if not segment or segment == "default":
            continue
        if parts and parts[-1] == segment:
            continue
        parts.append(segment)
    return ".".join(parts) or "default"


def _classes(graph: ObjectConfigGraph) -> list[ClassConfig]:
    result: list[ClassConfig] = []
    for n in graph.object_config_graph_nodes:
        if n.type == ObjectConfigGraphNodeType.class_ and n.class_config is not None:
            result.append(n.class_config)
    return result


def _relationships(graph: ObjectConfigGraph) -> list[ClassConfigRelationship]:
    result: list[ClassConfigRelationship] = []
    for n in graph.object_config_graph_nodes:
        if n.type == ObjectConfigGraphNodeType.relationship and n.class_config_relationship is not None:
            result.append(n.class_config_relationship)
    return result


def _class_by_name(graph: ObjectConfigGraph, name: str) -> ClassConfig:
    for c in _classes(graph):
        if c.name == name:
            return c
    raise AssertionError(f"ClassConfig not found: {name}")


def _relationship_for_source_attr(
    graph: ObjectConfigGraph, *, source_class: str, forward_attr: str
) -> ClassConfigRelationship:
    by_id: dict[UUID, ClassConfig] = {c.id: c for c in _classes(graph)}
    for rel in _relationships(graph):
        src = by_id.get(rel.class_config_id)
        if src is None or src.name != source_class:
            continue
        for rel_attr in rel.class_config_relationship_attributes:
            if (
                rel_attr.direction == ClassConfigRelationshipDirection.forward
                and rel_attr.role == ClassConfigRelationshipAttributeRole.reference
            ):
                src_attr = next(
                    (
                        acc.attribute_config
                        for acc in src.class_config_attribute_configs
                        if acc.attribute_config.id == rel_attr.attribute_config_id
                    ),
                    None,
                )
                if src_attr is not None and src_attr.name == forward_attr:
                    return rel
    raise AssertionError(f"Relationship not found for {source_class}.{forward_attr}")


def _attr_by_name(cls: ClassConfig, name: str) -> AttributeConfig:
    for acc in cls.class_config_attribute_configs:
        attr = acc.attribute_config
        if attr.name == name:
            return attr
    raise AssertionError(f"AttributeConfig not found: {cls.name}.{name}")


def _attr_pos_by_name(cls: ClassConfig, name: str) -> int:
    for acc in cls.class_config_attribute_configs:
        attr = acc.attribute_config
        if attr.name == name:
            return int(acc.position)
    raise AssertionError(f"AttributeConfig not found: {cls.name}.{name}")


def _fk_attr_for_relationship(
    rel: ClassConfigRelationship,
    *,
    fk_owner_side: ClassConfigRelationshipDirection,
    class_by_id: dict[UUID, ClassConfig],
) -> AttributeConfig:
    owner = class_by_id.get(rel.class_config_id) if fk_owner_side == ClassConfigRelationshipDirection.forward else None
    if fk_owner_side == ClassConfigRelationshipDirection.reverse:
        owner = class_by_id.get(rel.target_class_config_id)
    if owner is None:
        raise AssertionError("FK owner class missing")
    for ra in rel.class_config_relationship_attributes:
        if ra.role != ClassConfigRelationshipAttributeRole.foreign_key:
            continue
        if ra.direction != fk_owner_side:
            continue
        fk_attr = next(
            (
                acc.attribute_config
                for acc in owner.class_config_attribute_configs
                if acc.attribute_config.id == ra.attribute_config_id
            ),
            None,
        )
        if fk_attr is not None:
            return fk_attr
    raise AssertionError("FOREIGN_KEY attribute not found for relationship")


def _assert_positions_are_dense_and_deterministic(classes: Iterable[ClassConfig]) -> None:
    for cls in classes:
        positions: list[int] = []
        for acc in cls.class_config_attribute_configs:
            positions.append(acc.position)
        assert sorted(positions) == list(range(len(positions))), f"{cls.name} positions not dense: {sorted(positions)}"


@pytest.fixture
def base_graph(tmp_path: Path) -> tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]:
    src = """
class Parent {
    // Relationships
    child Child

    // Attributes
    name String
}

class Child {
    // Attributes
    nickname String
}
""".lstrip()
    return _build_graph_from_aware_source(tmp_path=tmp_path, source=src)


def test_fk_required_when_lazy_by_default(base_graph: tuple[ObjectConfigGraph, dict[UUID, NamespacePath]]) -> None:
    graph, namespace_by_code_id = base_graph
    transformer = AwareToRuntimeTransformer(namespace_by_code_id=namespace_by_code_id, relationship_loading_config=None)
    transformed = transformer.transform(graph)

    parent = _class_by_name(transformed, "Parent")
    rel = _relationship_for_source_attr(transformed, source_class="Parent", forward_attr="child")
    class_by_id = {c.id: c for c in _classes(transformed)}

    # Canonical representation semantics (current):
    # - Default loading strategy is LAZY for pointers.
    # - LAZY pointers are excluded from serialization and given a default (round-trippable).
    child_attr = _attr_by_name(parent, "child")
    assert child_attr.exclude_serialization is True
    assert child_attr.default_value == "null"

    fk_attr = _fk_attr_for_relationship(
        rel, fk_owner_side=ClassConfigRelationshipDirection.forward, class_by_id=class_by_id
    )
    assert fk_attr.name == "child_id"
    assert fk_attr.is_required is True

    # Deterministic positions: synthetic FK must come after code-defined attrs.
    assert _attr_pos_by_name(parent, "child") < _attr_pos_by_name(parent, "name")
    assert _attr_pos_by_name(parent, "child_id") > max(
        _attr_pos_by_name(parent, "child"), _attr_pos_by_name(parent, "name")
    )


def test_cross_ocg_relationship_synthesizes_fk_with_external_graph_mapping(tmp_path: Path) -> None:
    """
    Regression:
    External graphs loaded from dependency artifacts do not hydrate
    `ObjectConfigGraphRelationship.target_object_config_graph` (excluded from JSON).

    The runtime transformer must still be able to analyze cross-OCG relationships
    deterministically when an explicit external graph mapping is provided.
    """
    history_graph, history_ns = _build_graph_from_aware_source(
        tmp_path=tmp_path,
        package="aware_history",
        domain="branch",
        schema="branch",
        source="class Branch {}".strip(),
    )
    _ = history_ns

    meta_source = """
class ObjectInstanceGraphBranch {
    // Relationships
    branch aware_history.branch.Branch
}
""".lstrip()
    meta_file_path = tmp_path / "meta.aware"
    _ = meta_file_path.write_text(meta_source, encoding="utf-8")
    meta_code = build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(meta_file_path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    meta_namespace_by_code_id: dict[UUID, NamespacePath] = {
        meta_code.id: NamespacePath(package="aware_meta", namespace="graph.instance"),
    }
    meta_build = build_object_config_graph_from_code(
        name="meta",
        description="meta",
        fqn_prefix="aware_meta",
        file_codes=[(str(meta_file_path), meta_code)],
        namespace_by_code_id=meta_namespace_by_code_id,
        external_graphs=[history_graph],
    )
    meta_graph = meta_build.graph

    cross_rels = meta_build.cross_relationships_by_target_ocg.get(history_graph.id)
    assert cross_rels is not None and len(cross_rels) == 1
    meta_graph.object_config_graph_relationships.append(
        ObjectConfigGraphRelationship(
            object_config_graph_id=meta_graph.id,
            target_object_config_graph_id=history_graph.id,
            # IMPORTANT: omit `target_object_config_graph` to simulate persisted artifacts.
            class_config_relationships=[cross_rels[0]],
        )
    )

    transformer = AwareToRuntimeTransformer(
        namespace_by_code_id=meta_namespace_by_code_id,
        relationship_loading_config=None,
        external_graphs_by_id={history_graph.id: history_graph},
    )
    transformed = transformer.transform(meta_graph)

    branch_cls = _class_by_name(transformed, "ObjectInstanceGraphBranch")
    class_by_id = {c.id: c for c in _classes(transformed)}

    # Cross relationships are not RELATIONSHIP nodes; they are attached via object_config_graph_relationships.
    rel = None
    for ocg_rel in transformed.object_config_graph_relationships:
        for candidate in ocg_rel.class_config_relationships:
            if candidate.class_config_id != branch_cls.id:
                continue
            for rel_attr in candidate.class_config_relationship_attributes:
                if (
                    rel_attr.direction == ClassConfigRelationshipDirection.forward
                    and rel_attr.role == ClassConfigRelationshipAttributeRole.reference
                ):
                    src_attr = next(
                        (
                            acc.attribute_config
                            for acc in branch_cls.class_config_attribute_configs
                            if acc.attribute_config.id == rel_attr.attribute_config_id
                        ),
                        None,
                    )
                    if src_attr is not None and src_attr.name == "branch":
                        rel = candidate
                        break
            if rel is not None:
                break
        if rel is not None:
            break

    assert rel is not None, "Expected cross-OCG relationship for ObjectInstanceGraphBranch.branch"

    fk_attr = _fk_attr_for_relationship(
        rel, fk_owner_side=ClassConfigRelationshipDirection.forward, class_by_id=class_by_id
    )
    assert fk_attr.name == "branch_id"
    _assert_positions_are_dense_and_deterministic(_classes(transformed))


def test_fk_optional_when_forward_side_is_eager(
    base_graph: tuple[ObjectConfigGraph, dict[UUID, NamespacePath]],
) -> None:
    graph, namespace_by_code_id = base_graph
    config = ClassConfigRelationshipSideLoadingConfig(
        entries=[
            ClassConfigRelationshipSideLoadingEntry(
                schema_name="test_schema",
                class_name="Parent",
                attribute="child",
                forward=ClassConfigRelationshipSideLoadingStrategy.eager,
                reverse=None,
            )
        ]
    )
    transformer = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id, relationship_loading_config=config
    )
    transformed = transformer.transform(graph)

    parent = _class_by_name(transformed, "Parent")
    child_attr = _attr_by_name(parent, "child")
    assert child_attr.exclude_serialization is False
    assert child_attr.is_required is True

    rel = _relationship_for_source_attr(transformed, source_class="Parent", forward_attr="child")
    class_by_id = {c.id: c for c in _classes(transformed)}
    fk_attr = _fk_attr_for_relationship(
        rel, fk_owner_side=ClassConfigRelationshipDirection.forward, class_by_id=class_by_id
    )
    assert fk_attr.name == "child_id"
    assert fk_attr.is_required is False


def test_fk_optional_when_relationship_is_optional(tmp_path: Path) -> None:
    src = """
class Parent {
    // Relationships
    child Child?
}

class Child {
}
""".lstrip()
    graph, namespace_by_code_id = _build_graph_from_aware_source(tmp_path=tmp_path, source=src)
    config = ClassConfigRelationshipSideLoadingConfig(
        entries=[
            ClassConfigRelationshipSideLoadingEntry(
                schema_name="test_schema",
                class_name="Parent",
                attribute="child",
                forward=ClassConfigRelationshipSideLoadingStrategy.lazy,
                reverse=None,
            )
        ]
    )
    transformer = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id, relationship_loading_config=config
    )
    transformed = transformer.transform(graph)

    rel = _relationship_for_source_attr(transformed, source_class="Parent", forward_attr="child")
    class_by_id = {c.id: c for c in _classes(transformed)}
    fk_attr = _fk_attr_for_relationship(
        rel, fk_owner_side=ClassConfigRelationshipDirection.forward, class_by_id=class_by_id
    )
    assert fk_attr.name == "child_id"
    assert fk_attr.is_required is False


def test_fk_override_nullable_and_name(tmp_path: Path) -> None:
    src = """
class Parent {
    // Relationships
    child Child
}

class Child {
}

ann test_schema.Parent::child override fk nullable name parent_child_id
""".lstrip()
    graph, namespace_by_code_id = _build_graph_from_aware_source(tmp_path=tmp_path, source=src)
    transformer = AwareToRuntimeTransformer(namespace_by_code_id=namespace_by_code_id, relationship_loading_config=None)
    transformed = transformer.transform(graph)

    rel = _relationship_for_source_attr(transformed, source_class="Parent", forward_attr="child")
    class_by_id = {c.id: c for c in _classes(transformed)}
    fk_attr = _fk_attr_for_relationship(
        rel, fk_owner_side=ClassConfigRelationshipDirection.forward, class_by_id=class_by_id
    )
    assert fk_attr.name == "parent_child_id"
    assert fk_attr.is_required is False
    assert rel.forward_required is False


def test_one_to_many_fk_requiredness_follows_relationship_truth(tmp_path: Path) -> None:
    src = """
class Department {
    // Relationships
    employees Employee[]
}

class Employee {
    // Attributes
    name String
}
""".lstrip()
    graph, namespace_by_code_id = _build_graph_from_aware_source(tmp_path=tmp_path, source=src)

    # Reverse eager loading keeps reverse one_to_many FK optional in runtime/language models.
    # DB requiredness remains relationship truth and is validated in SQL/meta tests.
    config = ClassConfigRelationshipSideLoadingConfig(
        entries=[
            ClassConfigRelationshipSideLoadingEntry(
                schema_name="test_schema",
                class_name="Department",
                attribute="employees",
                forward=None,
                reverse=ClassConfigRelationshipSideLoadingStrategy.eager,
            )
        ]
    )
    transformer = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id, relationship_loading_config=config
    )
    transformed = transformer.transform(graph)

    rel = _relationship_for_source_attr(transformed, source_class="Department", forward_attr="employees")
    assert rel.relationship_type == ClassConfigRelationshipType.one_to_many

    class_by_id = {c.id: c for c in _classes(transformed)}
    employee = _class_by_name(transformed, "Employee")
    reverse_view = _attr_by_name(employee, "department")
    assert reverse_view.exclude_serialization is False
    assert reverse_view.is_required is True

    fk_attr = _fk_attr_for_relationship(
        rel, fk_owner_side=ClassConfigRelationshipDirection.reverse, class_by_id=class_by_id
    )
    assert fk_attr.name == "department_id"
    assert fk_attr.is_required is False
    _assert_positions_are_dense_and_deterministic(_classes(transformed))


def test_path_scoped_constructor_preserves_identity_keys_with_parent_context(
    tmp_path: Path,
) -> None:
    src = """
class Parent {
    // Relationships
    children Child[]

    fn add_child (child_key String) -> Child {
        let child = construct children.create_child(
            key = child_key
        )
    }
}

class Child {
    fn create_child construct (key String key) -> Child {
    }
}
""".lstrip()
    graph, namespace_by_code_id = _build_graph_from_aware_source(tmp_path=tmp_path, source=src)
    transformed = AwareToRuntimeTransformer(
        namespace_by_code_id=namespace_by_code_id, relationship_loading_config=None
    ).transform(graph)

    parent = _class_by_name(transformed, "Parent")
    child = _class_by_name(transformed, "Child")

    child_fn_by_name = {link.function_config.name: link.function_config for link in child.class_config_function_configs}
    path_ctor = child_fn_by_name.get("create_child_via_parent")
    assert path_ctor is not None

    input_edges = [
        edge
        for edge in sorted(
            path_ctor.function_config_attribute_configs,
            key=lambda edge: edge.position,
        )
        if edge.type == FunctionAttributeType.input
    ]
    assert [edge.attribute_config.name for edge in input_edges] == ["parent_id", "key"]
    assert [edge.is_identity_key for edge in input_edges] == [True, True]

    add_child_fn = next(
        link.function_config
        for link in parent.class_config_function_configs
        if link.function_config.name == "add_child"
    )
    assert len(add_child_fn.invocations) == 1
    invocation = add_child_fn.invocations[0]
    assert invocation.target_function_config_id == path_ctor.id
    assert invocation.target_function_config is not None
    assert invocation.target_function_config.name == "create_child_via_parent"
