from __future__ import annotations

from pathlib import Path
from uuid import UUID

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)

# Code Runtime
from aware_code.builder import build_code_from_file
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.symbol_table import CodeSymbolTable

# Aware Grammar (canonical plugins)
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN

# Meta Runtime
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.enum.config.builder import standardize_enum_value
from aware_meta.attribute.config.type_descriptor_builder import (
    ensure_stable_descriptor_tree_ids,
)
from aware_meta.primitive.config.builder import build_primitive_config
from aware_meta.graph.config.stable_ids import (
    stable_attribute_config_id,
    stable_attribute_type_descriptor_id,
    stable_attribute_type_descriptor_link_id,
    stable_class_config_attribute_config_id,
    stable_class_config_function_config_id,
    stable_class_relationship_id,
    stable_class_relationship_association_edge_id,
    stable_class_relationship_attribute_id,
    stable_class_config_id,
    stable_code_primitive_type_element_type_id,
    stable_code_primitive_type_union_type_id,
    stable_enum_config_id,
    stable_function_config_attribute_config_id,
    stable_function_config_id,
    stable_object_config_graph_id,
    stable_object_config_graph_node_id,
)
from aware_meta_ontology.stable_ids import (
    stable_enum_option_id,
    stable_primitive_config_id,
)


def _build_code(tmp_path: Path, name: str, content: str):
    p = tmp_path / name
    p.write_text(content)
    sections_index = CodeSectionBuilderIndex()
    return build_code_from_file(
        sections_index=sections_index,
        file_path=str(p),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _ns(*, fqn_prefix: str, namespace: str, code_ids: list[UUID]):
    return {
        cid: NamespacePath(package=fqn_prefix, namespace=namespace) for cid in code_ids
    }, []


CANONICAL_CODE = """
enum Status {
    active
    inactive
}

class User {
    id UUID
    name String
    status Status
    tags String[]
    meta Json?
    posts Post[]

    fn build construct() -> User {
        \"\"\"Build a new User.\"\"\"
    }

    fn with_tags construct(tags String[]) -> User {
        \"\"\"Build a User with tags.\"\"\"
    }
}

class Post {
    title String
}
""".strip()


def _assert_descriptor_tree_stable(desc: AttributeTypeDescriptor) -> None:
    # FK backfills required for hashing
    primitive_config_id = desc.primitive_config_id
    if desc.primitive_config is not None:
        prim_cfg = desc.primitive_config
        assert prim_cfg.primitive_type is not None
        assert prim_cfg.primitive_type_id == prim_cfg.primitive_type.id
        assert prim_cfg.id == stable_primitive_config_id(
            primitive_type_id=prim_cfg.primitive_type.id
        )
        primitive_config_id = prim_cfg.id

    enum_config_id = desc.enum_config_id
    if desc.enum_config is not None:
        enum_config_id = desc.enum_config.id

    class_config_id = desc.class_config_id
    if desc.class_config is not None:
        class_config_id = desc.class_config.id

    # Fingerprint from deterministic child links
    child_entries: list[tuple[str, int, str]] = []
    for link in list(desc.child_links or []):
        role = link.role.value if hasattr(link.role, "value") else str(link.role)
        child_entries.append((role, int(link.position or 0), str(link.child.id)))
    child_entries_sorted = sorted(child_entries, key=lambda x: (x[0], x[1], x[2]))
    child_links_fingerprint = ";".join(
        [f"{r}:{p}:{cid}" for r, p, cid in child_entries_sorted]
    )

    kind = desc.kind.value if hasattr(desc.kind, "value") else str(desc.kind)
    collection_kind = (
        desc.collection_kind.value
        if (desc.collection_kind is not None and hasattr(desc.collection_kind, "value"))
        else (str(desc.collection_kind) if desc.collection_kind is not None else None)
    )
    entity_id = class_config_id or enum_config_id or primitive_config_id

    assert desc.id == stable_attribute_type_descriptor_id(
        kind=kind,
        collection_kind=collection_kind,
        entity_id=entity_id,
        child_links_fingerprint=child_links_fingerprint,
    )

    # Links
    for link in list(desc.child_links or []):
        role = link.role.value if hasattr(link.role, "value") else str(link.role)
        assert link.attribute_type_descriptor_id == desc.id
        assert link.child_id == link.child.id
        assert link.id == stable_attribute_type_descriptor_link_id(
            attribute_type_descriptor_id=desc.id,
            child_id=link.child.id,
            role=role,
            position=int(link.position or 0),
        )
        _assert_descriptor_tree_stable(link.child)


def test_attribute_type_descriptor_link_ids_are_parent_scoped() -> None:
    primitive = AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])
    left = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[],
    )
    right = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.set,
        child_links=[],
    )
    left.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=left.id,
            child=primitive,
            child_id=primitive.id,
            role=Role.element,
            position=0,
        )
    )
    right.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=right.id,
            child=primitive,
            child_id=primitive.id,
            role=Role.element,
            position=0,
        )
    )

    ensure_stable_descriptor_tree_ids(left)
    ensure_stable_descriptor_tree_ids(right)

    assert left.child_links[0].id != right.child_links[0].id


def _primitive_leaf_descriptor(
    base_type: CodePrimitiveBaseType,
) -> AttributeTypeDescriptor:
    primitive_type = build_code_primitive_type(base_type=base_type)
    primitive_config = build_primitive_config(primitive_type)
    descriptor = AttributeTypeDescriptor(
        kind=Kind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
        child_links=[],
    )
    ensure_stable_descriptor_tree_ids(descriptor)
    return descriptor


def test_attribute_type_descriptor_collection_id_tracks_collection_kind_and_element_structure() -> (
    None
):
    string_leaf = _primitive_leaf_descriptor(CodePrimitiveBaseType.string)
    int_leaf = _primitive_leaf_descriptor(CodePrimitiveBaseType.integer)

    list_desc = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[],
    )
    list_desc.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=list_desc.id,
            child=string_leaf,
            child_id=string_leaf.id,
            role=Role.element,
            position=0,
        )
    )

    set_desc = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.set,
        child_links=[],
    )
    set_desc.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=set_desc.id,
            child=string_leaf,
            child_id=string_leaf.id,
            role=Role.element,
            position=0,
        )
    )

    alt_list_desc = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[],
    )
    alt_list_desc.child_links.append(
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=alt_list_desc.id,
            child=int_leaf,
            child_id=int_leaf.id,
            role=Role.element,
            position=0,
        )
    )

    ensure_stable_descriptor_tree_ids(list_desc)
    ensure_stable_descriptor_tree_ids(set_desc)
    ensure_stable_descriptor_tree_ids(alt_list_desc)

    assert list_desc.id != set_desc.id
    assert list_desc.id != alt_list_desc.id


def test_attribute_type_descriptor_mapping_id_tracks_key_value_structure() -> None:
    key_leaf = _primitive_leaf_descriptor(CodePrimitiveBaseType.string)
    value_leaf = _primitive_leaf_descriptor(CodePrimitiveBaseType.integer)
    alt_value_leaf = _primitive_leaf_descriptor(CodePrimitiveBaseType.float)

    mapping_desc = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    mapping_desc.child_links.extend(
        [
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=mapping_desc.id,
                child=key_leaf,
                child_id=key_leaf.id,
                role=Role.key,
                position=0,
            ),
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=mapping_desc.id,
                child=value_leaf,
                child_id=value_leaf.id,
                role=Role.value_,
                position=0,
            ),
        ]
    )

    swapped_desc = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    swapped_desc.child_links.extend(
        [
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=swapped_desc.id,
                child=value_leaf,
                child_id=value_leaf.id,
                role=Role.key,
                position=0,
            ),
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=swapped_desc.id,
                child=key_leaf,
                child_id=key_leaf.id,
                role=Role.value_,
                position=0,
            ),
        ]
    )

    alt_mapping_desc = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    alt_mapping_desc.child_links.extend(
        [
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=alt_mapping_desc.id,
                child=key_leaf,
                child_id=key_leaf.id,
                role=Role.key,
                position=0,
            ),
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=alt_mapping_desc.id,
                child=alt_value_leaf,
                child_id=alt_value_leaf.id,
                role=Role.value_,
                position=0,
            ),
        ]
    )

    ensure_stable_descriptor_tree_ids(mapping_desc)
    ensure_stable_descriptor_tree_ids(swapped_desc)
    ensure_stable_descriptor_tree_ids(alt_mapping_desc)

    assert mapping_desc.id != swapped_desc.id
    assert mapping_desc.id != alt_mapping_desc.id


def test_attribute_type_descriptor_tuple_id_tracks_member_position() -> None:
    first = _primitive_leaf_descriptor(CodePrimitiveBaseType.string)
    second = _primitive_leaf_descriptor(CodePrimitiveBaseType.integer)

    tuple_desc = AttributeTypeDescriptor(kind=Kind.tuple, child_links=[])
    tuple_desc.child_links.extend(
        [
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=tuple_desc.id,
                child=first,
                child_id=first.id,
                role=Role.member,
                position=1,
            ),
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=tuple_desc.id,
                child=second,
                child_id=second.id,
                role=Role.member,
                position=2,
            ),
        ]
    )

    swapped_tuple_desc = AttributeTypeDescriptor(kind=Kind.tuple, child_links=[])
    swapped_tuple_desc.child_links.extend(
        [
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=swapped_tuple_desc.id,
                child=second,
                child_id=second.id,
                role=Role.member,
                position=1,
            ),
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=swapped_tuple_desc.id,
                child=first,
                child_id=first.id,
                role=Role.member,
                position=2,
            ),
        ]
    )

    ensure_stable_descriptor_tree_ids(tuple_desc)
    ensure_stable_descriptor_tree_ids(swapped_tuple_desc)

    assert tuple_desc.id != swapped_tuple_desc.id


def test_attribute_type_descriptor_union_id_tracks_member_order() -> None:
    member_a = _primitive_leaf_descriptor(CodePrimitiveBaseType.string)
    member_b = _primitive_leaf_descriptor(CodePrimitiveBaseType.null)

    union_desc = AttributeTypeDescriptor(kind=Kind.union, child_links=[])
    union_desc.child_links.extend(
        [
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=union_desc.id,
                child=member_a,
                child_id=member_a.id,
                role=Role.member,
                position=1,
            ),
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=union_desc.id,
                child=member_b,
                child_id=member_b.id,
                role=Role.member,
                position=2,
            ),
        ]
    )

    swapped_union_desc = AttributeTypeDescriptor(kind=Kind.union, child_links=[])
    swapped_union_desc.child_links.extend(
        [
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=swapped_union_desc.id,
                child=member_b,
                child_id=member_b.id,
                role=Role.member,
                position=1,
            ),
            AttributeTypeDescriptorLink(
                attribute_type_descriptor_id=swapped_union_desc.id,
                child=member_a,
                child_id=member_a.id,
                role=Role.member,
                position=2,
            ),
        ]
    )

    ensure_stable_descriptor_tree_ids(union_desc)
    ensure_stable_descriptor_tree_ids(swapped_union_desc)

    assert union_desc.id != swapped_union_desc.id


def test_ocg_stable_ids(tmp_path: Path) -> None:
    """
    End-to-end stability contract test for canonical OCG builds.

    This validates:
    - Stable IDs are deterministic across rebuilds
    - IDs match the deterministic rules in `stable_ids.py` for all supported entity kinds
    """
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)

    code_a = _build_code(tmp_path, "a.aware", CANONICAL_CODE)
    ns_a, domains_a = _ns(fqn_prefix="pkg", namespace="default", code_ids=[code_a.id])
    res_a = build_object_config_graph_from_code(
        name="stable",
        description="stable",
        fqn_prefix="pkg",
        file_codes=[("a.aware", code_a)],
        namespace_by_code_id=ns_a,
    )
    g1 = res_a.graph

    code_b = _build_code(tmp_path, "b.aware", CANONICAL_CODE)
    ns_b, domains_b = _ns(fqn_prefix="pkg", namespace="default", code_ids=[code_b.id])
    res_b = build_object_config_graph_from_code(
        name="stable",
        description="stable",
        fqn_prefix="pkg",
        file_codes=[("b.aware", code_b)],
        namespace_by_code_id=ns_b,
    )
    g2 = res_b.graph

    # Graph-level stability
    expected_ocg_id = stable_object_config_graph_id(
        fqn_prefix="pkg",
        language=CodeLanguage.aware.value,
    )
    assert g1.id == expected_ocg_id
    assert g2.id == expected_ocg_id
    # Semantic hash is stable across file renames; layout_hash captures placement changes.
    assert g1.hash == g2.hash
    assert g1.layout_hash is not None
    assert g2.layout_hash is not None
    assert g1.layout_hash != g2.layout_hash

    # OCG node IDs
    def _node_key(n: ObjectConfigGraphNode) -> tuple[str, str]:
        if n.type == ObjectConfigGraphNodeType.class_ and n.class_config is not None:
            return ("class", n.class_config.name)
        if n.type == ObjectConfigGraphNodeType.enum and n.enum_config is not None:
            return ("enum", n.enum_config.name)
        if (
            n.type == ObjectConfigGraphNodeType.function
            and n.function_config is not None
        ):
            return ("function", n.function_config.name)
        if (
            n.type == ObjectConfigGraphNodeType.relationship
            and n.class_config_relationship is not None
        ):
            return ("relationship", str(n.class_config_relationship.id))
        return ("unknown", str(n.id))

    nodes1 = {_node_key(n): n for n in g1.object_config_graph_nodes}
    nodes2 = {_node_key(n): n for n in g2.object_config_graph_nodes}
    assert set(nodes1.keys()) == set(nodes2.keys())

    for k in sorted(nodes1.keys()):
        n1 = nodes1[k]
        n2 = nodes2[k]
        assert n1.type == n2.type
        exp = stable_object_config_graph_node_id(
            object_config_graph_id=expected_ocg_id,
            type=n1.type.value,
            node_key=n1.node_key,
        )
        assert n1.id == exp
        assert n2.id == exp

    # Class IDs + attribute/function/link IDs + type descriptor rails
    def _assert_graph_entity_ids(g: ObjectConfigGraph) -> None:
        # Class configs (by name)
        class_nodes = {
            n.class_config.name: n
            for n in g.object_config_graph_nodes
            if n.class_config is not None
        }
        assert set(class_nodes.keys()) >= {"User", "Post"}

        for class_name, node in class_nodes.items():
            cc = node.class_config
            assert cc is not None
            class_fqn = cc.class_fqn
            assert cc.id == stable_class_config_id(
                object_config_graph_node_id=node.id, class_fqn=class_fqn
            )

            # Class attributes
            for edge in list(cc.class_config_attribute_configs or []):
                attr = edge.attribute_config
                assert attr is not None
                assert attr.id == stable_attribute_config_id(
                    owner_key=class_fqn, name=attr.name
                )
                assert edge.id == stable_class_config_attribute_config_id(
                    class_config_id=cc.id,
                    attribute_config_id=attr.id,
                )

                # Type descriptor tree stable IDs
                assert attr.type_descriptor is not None
                _assert_descriptor_tree_stable(attr.type_descriptor)

            # Class functions
            for edge in cc.class_config_function_configs:
                fn = edge.function_config
                assert fn is not None
                assert fn.id == stable_function_config_id(
                    owner_key=class_fqn, name=fn.name, kind=fn.kind.value
                )
                assert edge.id == stable_class_config_function_config_id(
                    class_config_id=cc.id,
                    function_config_id=fn.id,
                )

                # Function IO attributes
                for f_edge in list(fn.function_config_attribute_configs or []):
                    a = f_edge.attribute_config
                    assert a is not None
                    io_owner = f"{class_fqn}.{fn.name}::{f_edge.type.value.lower()}"
                    assert a.id == stable_attribute_config_id(
                        owner_key=io_owner, name=a.name
                    )
                    assert f_edge.id == stable_function_config_attribute_config_id(
                        function_config_id=fn.id,
                        name=a.name,
                        type=f_edge.type.value,
                    )
                    assert a.type_descriptor is not None
                    _assert_descriptor_tree_stable(a.type_descriptor)

        # Enum config + options
        enum_nodes = {
            n.enum_config.name: n
            for n in g.object_config_graph_nodes
            if n.enum_config is not None
        }
        assert "Status" in enum_nodes
        enum_node = enum_nodes["Status"]
        enum_cfg = enum_node.enum_config
        assert enum_cfg is not None
        enum_fqn = enum_cfg.enum_fqn
        assert enum_cfg.id == stable_enum_config_id(
            object_config_graph_node_id=enum_node.id, enum_fqn=enum_fqn
        )
        for opt in enum_cfg.enum_options:
            value = standardize_enum_value(opt.value)
            assert opt.id == stable_enum_option_id(
                enum_config_id=enum_cfg.id, value=value
            )

        # Relationship rail IDs
        rels = [
            n.class_config_relationship
            for n in g.object_config_graph_nodes
            if n.type == ObjectConfigGraphNodeType.relationship
            and n.class_config_relationship is not None
        ]
        assert rels, "Expected at least one relationship (User.posts -> Post)"
        for rel in rels:
            # Determine reference attribute id (canonical declaring anchor)
            ref_attr_id = None
            for ra in rel.class_config_relationship_attributes:
                if (
                    ra.direction == ClassConfigRelationshipDirection.forward
                    and ra.role == ClassConfigRelationshipAttributeRole.reference
                ):
                    ref_attr_id = ra.attribute_config_id
                    break
            assert ref_attr_id is not None
            assert rel.id == stable_class_relationship_id(
                source_class_id=rel.class_config_id,
                target_class_id=rel.target_class_config_id,
                relationship_key=rel.relationship_key,
            )
            for ra in rel.class_config_relationship_attributes:
                assert ra.id == stable_class_relationship_attribute_id(
                    relationship_id=rel.id,
                    attribute_config_id=ra.attribute_config_id,
                    direction=ra.direction.value,
                    role=ra.role.value,
                )
            if rel.class_config_relationship_association_edge is not None:
                assoc = rel.class_config_relationship_association_edge
                assert assoc.id == stable_class_relationship_association_edge_id(
                    relationship_id=rel.id,
                    association_class_id=assoc.class_config_id,
                )

    _assert_graph_entity_ids(g1)
    _assert_graph_entity_ids(g2)


def test_code_primitive_type_edge_ids_are_stable() -> None:
    """
    Cover stable ID rules for tuple/union edge rows on CodePrimitiveType.

    Note: Aware type syntax does not currently expose tuple/union constructs, so we validate
    the stable-id contract directly on the meta primitive representation.
    """
    # Tuple-like
    a = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    b = build_code_primitive_type(base_type=CodePrimitiveBaseType.integer)
    parent = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.tuple,
        element_types=(a, b),
    )

    from aware_meta.primitive.config.builder import build_primitive_config

    cfg = build_primitive_config(parent)
    assert cfg.primitive_type is not None
    prim = cfg.primitive_type
    assert prim.code_primitive_type_element_types
    for e in prim.code_primitive_type_element_types:
        assert e.id == stable_code_primitive_type_element_type_id(
            code_primitive_type_id=prim.id,
            position=e.position,
        )

    # Union-like
    x = build_code_primitive_type(base_type=CodePrimitiveBaseType.string)
    y = build_code_primitive_type(base_type=CodePrimitiveBaseType.null)
    u = build_code_primitive_type(
        base_type=CodePrimitiveBaseType.union,
        union_types=(x, y),
    )
    cfg2 = build_primitive_config(u)
    prim2 = cfg2.primitive_type
    assert prim2.code_primitive_type_union_types
    for e in prim2.code_primitive_type_union_types:
        assert e.id == stable_code_primitive_type_union_type_id(
            code_primitive_type_id=prim2.id,
            position=e.position,
        )
