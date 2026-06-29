import pytest
from pathlib import Path
from collections.abc import Sequence
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code import Code

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import ObjectConfigGraphNodeType
from aware_meta_ontology.attribute.attribute_type_descriptor import AttributeTypeDescriptor
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
)

# Code Runtime
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.builder import build_code_from_file
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.meta_language_plugin import AWARE_META_PLUGIN

# Aware Meta
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry


@pytest.fixture(scope="session")
def sample_files() -> dict[str, str]:
    current_dir = Path(__file__).parent
    samples_dir = current_dir / "samples"
    augment = samples_dir / "augment.aware"
    assoc = samples_dir / "association_relationship.aware"
    many = samples_dir / "many_to_many.aware"
    user_post = samples_dir / "user_post.aware"
    rel_types = samples_dir / "relationship_types.aware"
    missing_assoc = samples_dir / "missing_association.aware"
    dup1 = samples_dir / "duplicate_user_one.aware"
    dup2 = samples_dir / "duplicate_user_two.aware"
    bad_edge = samples_dir / "edge_contains_relationship.aware"
    external_user = samples_dir / "external_user.aware"
    cross_ocg_ref = samples_dir / "cross_ocg_ref.aware"

    for p in (
        augment,
        assoc,
        many,
        user_post,
        rel_types,
        missing_assoc,
        dup1,
        dup2,
        bad_edge,
        external_user,
        cross_ocg_ref,
    ):
        if not p.exists():
            pytest.fail(f"Missing sample: {p}")
    return {
        "augment": str(augment),
        "association": str(assoc),
        "many": str(many),
        "user_post": str(user_post),
        "relationship_types": str(rel_types),
        "missing_association": str(missing_assoc),
        "dup_user_one": str(dup1),
        "dup_user_two": str(dup2),
        "edge_contains_relationship": str(bad_edge),
        "external_user": str(external_user),
        "cross_ocg_ref": str(cross_ocg_ref),
    }


def _build_code(path: str) -> Code:
    sections_index = CodeSectionBuilderIndex()
    code = build_code_from_file(
        sections_index=sections_index,
        file_path=path,
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )
    return code


def _build_test_namespace_by_code_id(
    *,
    package_name: str,
    codes: Sequence[tuple[str, Code]],
    domain_name: str = "test_domain",
    schema_name: str = "test_schema",
) -> dict[UUID, NamespacePath]:
    """Build a deterministic code_id -> NamespacePath mapping for tests."""

    return {
        code.id: NamespacePath(
            package=package_name,
            namespace=f"{domain_name}.{schema_name}",
        )
        for _, code in codes
    }


def _classes_by_name(graph: ObjectConfigGraph) -> dict[str, ClassConfig]:
    classes: dict[str, ClassConfig] = {}
    for n in graph.object_config_graph_nodes:
        if n.type != ObjectConfigGraphNodeType.class_:
            continue
        cls = n.class_config
        if cls is None:
            continue
        classes[cls.name] = cls
    return classes


def _relationships(graph: ObjectConfigGraph) -> list[ClassConfigRelationship]:
    rels: list[ClassConfigRelationship] = []
    for n in graph.object_config_graph_nodes:
        if n.type != ObjectConfigGraphNodeType.relationship:
            continue
        rel = n.class_config_relationship
        if rel is not None:
            rels.append(rel)
    return rels


def _attribute_configs(cls: ClassConfig):
    return [link.attribute_config for link in cls.class_config_attribute_configs]


def _attr_name_by_id(cls: ClassConfig, attribute_config_id: UUID) -> str | None:
    for attr in _attribute_configs(cls):
        if attr.id == attribute_config_id:
            return attr.name
    return None


def test_ocg_builder_is_ssot_driven(sample_files: dict[str, str]) -> None:
    # Ensure plugin registered for type descriptor parsing
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    codes = [
        ("augment", _build_code(sample_files["augment"])),
        ("association", _build_code(sample_files["association"])),
        ("many", _build_code(sample_files["many"])),
    ]
    namespace_by_code_id = _build_test_namespace_by_code_id(package_name="test_pkg", codes=codes)

    result = build_object_config_graph_from_code(
        name="test_ocg",
        description="kernel meta OCG build (canonical, no adapters)",
        fqn_prefix="test_pkg",
        file_codes=codes,
        namespace_by_code_id=namespace_by_code_id,
    )

    graph = result.graph
    assert graph.name == "test_ocg"
    assert graph.fqn_prefix == "test_pkg"
    assert graph.language == CodeLanguage.aware

    # At minimum, we should have CLASS nodes for the classes present in samples.
    node_types = [n.type for n in graph.object_config_graph_nodes]
    assert ObjectConfigGraphNodeType.class_ in node_types

    # Augment is modeled via parent_class_id (class-first)
    classes = _classes_by_name(graph)
    assert classes["TerminalEnv"].parent_class_id == classes["Terminal"].id

    # many-to-many should produce a MANY_TO_MANY relationship with association resolved from edge_spec_name
    rels = _relationships(graph)
    assert rels, "Expected at least one relationship"
    m2m_rels = [r for r in rels if r.relationship_type == ClassConfigRelationshipType.many_to_many]
    assert m2m_rels, "Expected at least one MANY_TO_MANY relationship"

    # Ensure the association points to the edge container class
    assoc_names: set[str] = set()
    for rel in m2m_rels:
        assoc = rel.class_config_relationship_association_edge
        if assoc is None:
            continue
        assoc_names.add(next((c.name for c in classes.values() if c.id == assoc.class_config_id), ""))
    assert "UserGroupEdge" in assoc_names

    # Association classes should not emit their own relationships from attributes (canonical rule)
    assoc_cls = classes["UserGroupEdge"]
    assert all(r.class_config_id != assoc_cls.id for r in rels)


def test_cross_ocg_reference_emits_cross_map(sample_files: dict[str, str]) -> None:
    # Ensure plugin registered for type descriptor parsing
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    # Build dependency OCG (different package/domain/schema)
    dep_code = _build_code(sample_files["external_user"])
    dep_ns = _build_test_namespace_by_code_id(
        package_name="dep_pkg",
        codes=[("dep", dep_code)],
        domain_name="dep_domain",
        schema_name="dep_schema",
    )
    dep_result = build_object_config_graph_from_code(
        name="dep_ocg",
        description="dependency graph",
        fqn_prefix="dep_pkg",
        file_codes=[("external_user", dep_code)],
        namespace_by_code_id=dep_ns,
    )

    # Build local OCG that references the external class via FULL FQN
    local_code = _build_code(sample_files["cross_ocg_ref"])
    local_ns = _build_test_namespace_by_code_id(
        package_name="main_pkg",
        codes=[("local", local_code)],
        domain_name="main_domain",
        schema_name="main_schema",
    )
    local_result = build_object_config_graph_from_code(
        name="local_ocg",
        description="local graph with cross-ocg ref",
        fqn_prefix="main_pkg",
        file_codes=[("cross_ocg_ref", local_code)],
        namespace_by_code_id=local_ns,
        external_graphs=[dep_result.graph],
    )

    # Canonical invariant: cross relationships are returned detached (not embedded in local graph).
    assert dep_result.graph.id in local_result.cross_relationships_by_target_ocg
    cross_rels = local_result.cross_relationships_by_target_ocg[dep_result.graph.id]
    assert len(cross_rels) == 1

    # Ensure local graph itself has no relationship nodes (relationship lives cross-OCG).
    assert _relationships(local_result.graph) == []

    # Cross relationship should still carry its canonical relationship attribute representation.
    rel = cross_rels[0]
    assert len(rel.class_config_relationship_attributes) == 1
    ra = rel.class_config_relationship_attributes[0]
    assert ra.direction == ClassConfigRelationshipDirection.forward
    assert ra.role == ClassConfigRelationshipAttributeRole.reference


def test_ocg_builder_user_post(sample_files: dict[str, str]) -> None:
    """
    Canonical deep validation for the generic OCG builder fail-closed rail.

    Invariants:
    - No adapters/CodeNode needed: build uses CodeSections + SSOT only.
    - All class references in type descriptors must resolve (strict attach_class_reference).
    - Standalone/global functions are rejected from canonical OCG builds.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code = _build_code(sample_files["user_post"])
    namespace_by_code_id = _build_test_namespace_by_code_id(
        package_name="test_pkg",
        codes=[("user_post", code)],
    )

    with pytest.raises(ValueError, match="Standalone/global functions are not modeled in canonical ObjectConfigGraph"):
        build_object_config_graph_from_code(
            name="test_user_post_ocg",
            description="deep canonical kernel meta OCG build",
            fqn_prefix="test_pkg",
            file_codes=[("user_post", code)],
            namespace_by_code_id=namespace_by_code_id,
        )


def test_ocg_hash_is_stable_across_two_builds(sample_files: dict[str, str]) -> None:
    """
    Determinism invariant: same inputs produce the same graph.hash even if UUIDs differ.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    def _build_hash() -> str:
        # Use a single file with no standalone/global functions to keep the
        # canonical OCG builder on the supported class-scoped rail.
        code = _build_code(sample_files["association"])
        codes = [("association", code)]
        namespace_by_code_id = _build_test_namespace_by_code_id(package_name="test_pkg", codes=codes)
        result = build_object_config_graph_from_code(
            name="test_ocg",
            description="hash stability test",
            fqn_prefix="test_pkg",
            file_codes=codes,
            namespace_by_code_id=namespace_by_code_id,
        )
        return result.graph.hash

    h1 = _build_hash()
    h2 = _build_hash()
    assert h1 == h2


def test_unresolved_class_descriptor_raises(tmp_path: Path) -> None:
    """
    Canonical invariant: CLASS references must resolve (no stubs).
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    sample = tmp_path / "bad.aware"
    _ = sample.write_text("class A {\n    b MissingType\n}\n")

    code = _build_code(str(sample))
    namespace_by_code_id = _build_test_namespace_by_code_id(
        package_name="test_pkg",
        codes=[("bad", code)],
    )

    with pytest.raises(ValueError):
        _ = build_object_config_graph_from_code(
            name="bad",
            description="should fail",
            fqn_prefix="test_pkg",
            file_codes=[("bad", code)],
            namespace_by_code_id=namespace_by_code_id,
        )


def test_ocg_builder_resolves_import_aliases(tmp_path: Path) -> None:
    """
    Canonical invariant: Meta resolves identifiers deterministically, including explicit import aliases.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(AWARE_META_PLUGIN)

    source = """
import test_pkg.test_domain.test_schema.Foo as FooAlias;

class Foo {
    // Attributes
    name String
}

class Bar {
    // Relationships
    foo FooAlias
}
""".lstrip()
    sample = tmp_path / "alias.aware"
    _ = sample.write_text(source, encoding="utf-8")

    code = _build_code(str(sample))
    namespace_by_code_id = _build_test_namespace_by_code_id(
        package_name="test_pkg",
        codes=[("alias", code)],
    )

    result = build_object_config_graph_from_code(
        name="alias",
        description="import alias resolution",
        fqn_prefix="test_pkg",
        file_codes=[("alias", code)],
        namespace_by_code_id=namespace_by_code_id,
    )

    graph = result.graph
    classes = _classes_by_name(graph)
    assert "Foo" in classes
    assert "Bar" in classes

    rels = _relationships(graph)
    assert rels, "Expected relationship node for Bar.foo"

    foo = classes["Foo"]
    bar = classes["Bar"]
    assert any(r.class_config_id == bar.id and r.target_class_config_id == foo.id for r in rels)


def test_ocg_builder_ignores_import_without_alias_for_resolution(tmp_path: Path) -> None:
    """
    Canonical Aware policy: imports only affect resolution when an explicit alias is provided.
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    MetaLanguagePluginRegistry.register(AWARE_META_PLUGIN)

    source = """
import test_pkg.test_domain.test_schema;

class Foo {
    // Attributes
    name String
}

class Bar {
    // Relationships
    foo test_pkg.Foo
}
""".lstrip()
    sample = tmp_path / "no_alias.aware"
    _ = sample.write_text(source, encoding="utf-8")

    code = _build_code(str(sample))
    namespace_by_code_id = _build_test_namespace_by_code_id(
        package_name="test_pkg",
        codes=[("no_alias", code)],
    )

    with pytest.raises(ValueError):
        _ = build_object_config_graph_from_code(
            name="no_alias",
            description="import without alias should not affect resolution",
            fqn_prefix="test_pkg",
            file_codes=[("no_alias", code)],
            namespace_by_code_id=namespace_by_code_id,
        )


def test_relationship_type_matrix(sample_files: dict[str, str]) -> None:
    """
    Validate the four relationship types:
    - MANY_TO_ONE
    - ONE_TO_ONE
    - ONE_TO_MANY
    - MANY_TO_MANY (+ association)
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    code = _build_code(sample_files["relationship_types"])
    namespace_by_code_id = _build_test_namespace_by_code_id(
        package_name="test_pkg",
        codes=[("relationship_types", code)],
    )

    result = build_object_config_graph_from_code(
        name="matrix",
        description="relationship type matrix",
        fqn_prefix="test_pkg",
        file_codes=[("relationship_types", code)],
        namespace_by_code_id=namespace_by_code_id,
    )
    graph = result.graph
    classes = _classes_by_name(graph)
    assert set(["User", "Post", "Image", "Group", "Membership", "UserGroupEdge"]).issubset(set(classes.keys()))

    rels = _relationships(graph)
    assert rels

    id_to_name = {str(v.id): k for k, v in classes.items()}
    triples = {
        (
            id_to_name.get(str(r.class_config_id)),
            id_to_name.get(str(r.target_class_config_id)),
            r.relationship_type,
        )
        for r in rels
    }

    assert ("Post", "User", ClassConfigRelationshipType.many_to_one) in triples
    assert ("User", "Image", ClassConfigRelationshipType.one_to_one) in triples
    assert ("User", "Post", ClassConfigRelationshipType.one_to_many) in triples
    assert ("Membership", "User", ClassConfigRelationshipType.many_to_many) in triples

    # Association must be present for MANY_TO_MANY in this sample
    m2m = next(
        r
        for r in rels
        if id_to_name.get(str(r.class_config_id)) == "Membership"
        and id_to_name.get(str(r.target_class_config_id)) == "User"
        and r.relationship_type == ClassConfigRelationshipType.many_to_many
    )
    assert m2m.class_config_relationship_association_edge is not None
    assert m2m.class_config_relationship_association_edge.class_config_id is not None
    assoc_name = id_to_name.get(str(m2m.class_config_relationship_association_edge.class_config_id))
    assert assoc_name == "UserGroupEdge"

    # Association classes should not generate relationships from their own attributes
    assoc_cls = classes["UserGroupEdge"]
    assert all(r.class_config_id != assoc_cls.id for r in rels)

    # Canonical invariant: each relationship has exactly one REFERENCE+FORWARD attribute.
    def _source_attr_name_for_rel(source_name: str, target_name: str, rel_type: ClassConfigRelationshipType) -> str:
        if (source_name, target_name, rel_type) == ("User", "Post", ClassConfigRelationshipType.one_to_many):
            return "posts"
        if (source_name, target_name, rel_type) == ("User", "Image", ClassConfigRelationshipType.one_to_one):
            return "profile"
        if (source_name, target_name, rel_type) == ("Post", "User", ClassConfigRelationshipType.many_to_one):
            return "author"
        if (source_name, target_name, rel_type) == ("Membership", "User", ClassConfigRelationshipType.many_to_many):
            return "users"
        raise AssertionError(f"Unhandled relationship triple: {(source_name, target_name, rel_type)}")

    expected_triples = [
        ("User", "Post", ClassConfigRelationshipType.one_to_many),
        ("User", "Image", ClassConfigRelationshipType.one_to_one),
        ("Post", "User", ClassConfigRelationshipType.many_to_one),
        ("Membership", "User", ClassConfigRelationshipType.many_to_many),
    ]

    for source_name, target_name, rel_type in expected_triples:
        expected_attr = _source_attr_name_for_rel(source_name, target_name, rel_type)
        rel = next(
            r
            for r in rels
            if id_to_name.get(str(r.class_config_id)) == source_name
            and id_to_name.get(str(r.target_class_config_id)) == target_name
            and r.relationship_type == rel_type
        )

        linked_names: list[str] = []
        for ra in rel.class_config_relationship_attributes:
            if ra.direction != ClassConfigRelationshipDirection.forward:
                continue
            if ra.role != ClassConfigRelationshipAttributeRole.reference:
                continue
            src_cls = classes[source_name]
            name = _attr_name_by_id(src_cls, ra.attribute_config_id)
            if name is not None:
                linked_names.append(name)
        assert linked_names == [
            expected_attr
        ], f"Expected exactly one REFERENCE attribute linked to relationship: {expected_attr}"
