from __future__ import annotations

from uuid import uuid4

import pytest

from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)

from aware_meta.attribute.instance.value import (
    AttributeValueBuildError,
    UnionSelection,
    build_attribute_value_tree,
)


def _desc(
    kind: Kind,
    *,
    collection_kind: AttributeCollectionType = AttributeCollectionType.single,
) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=kind,
        collection_kind=collection_kind,
        child_links=[],
    )


def _dlink(
    child: AttributeTypeDescriptor, role: Role, *, position: int = 0
) -> AttributeTypeDescriptorLink:
    return AttributeTypeDescriptorLink(
        child=child,
        role=role,
        position=position,
        attribute_type_descriptor_id=uuid4(),
        child_id=child.id,
    )


def test_primitive_leaf_valid() -> None:
    desc = _desc(Kind.primitive)
    root = build_attribute_value_tree(type_descriptor=desc, value="hello")
    assert root.primitive_value == {"value": "hello"}


def test_enum_leaf_requires_enum_option_id() -> None:
    desc = _desc(Kind.enum)
    enum_option_id = uuid4()
    root = build_attribute_value_tree(type_descriptor=desc, value=enum_option_id)
    assert root.enum_option_id == enum_option_id

    with pytest.raises(AttributeValueBuildError):
        build_attribute_value_tree(type_descriptor=desc, value=None)


def test_class_leaf_requires_class_instance_id() -> None:
    desc = _desc(Kind.class_)
    class_instance_id = uuid4()
    root = build_attribute_value_tree(type_descriptor=desc, value=class_instance_id)
    assert root.class_instance_id == class_instance_id

    with pytest.raises(AttributeValueBuildError):
        build_attribute_value_tree(type_descriptor=desc, value=None)


def test_list_collection_validates_and_canonicalizes() -> None:
    elem_desc = _desc(Kind.primitive)
    list_desc = _desc(Kind.collection, collection_kind=AttributeCollectionType.list)
    list_desc.child_links = [_dlink(elem_desc, Role.element)]

    root = build_attribute_value_tree(type_descriptor=list_desc, value=[0, 1])

    assert [l.position for l in root.child_links] == [0, 1]
    values = []
    for l in root.child_links:
        assert l.child.primitive_value is not None
        values.append(l.child.primitive_value["value"])
    assert values == [0, 1]


def test_set_collection_requires_identity_key() -> None:
    elem_desc = _desc(Kind.primitive)
    set_desc = _desc(Kind.collection, collection_kind=AttributeCollectionType.set)
    set_desc.child_links = [_dlink(elem_desc, Role.element)]

    root = build_attribute_value_tree(type_descriptor=set_desc, value={"x", "y"})
    assert all(l.identity_key for l in root.child_links)
    assert all(l.position is None for l in root.child_links)


def test_mapping_requires_key_and_value_per_identity_key() -> None:
    key_desc = _desc(Kind.primitive)
    val_desc = _desc(Kind.primitive)
    map_desc = _desc(Kind.mapping)
    map_desc.child_links = [
        _dlink(key_desc, Role.key),
        _dlink(val_desc, Role.value_),
    ]

    root = build_attribute_value_tree(type_descriptor=map_desc, value={"a": 1})
    keys = [l for l in root.child_links if l.role == Role.key]
    vals = [l for l in root.child_links if l.role == Role.value_]
    assert len(keys) == 1 and len(vals) == 1
    assert (
        keys[0].identity_key is not None
        and keys[0].identity_key == vals[0].identity_key
    )
    assert keys[0].child.primitive_value is not None
    assert keys[0].child.primitive_value["value"] == "a"
    assert vals[0].child.primitive_value is not None
    assert vals[0].child.primitive_value["value"] == 1


def test_tuple_validates_members_by_position() -> None:
    m1 = _desc(Kind.primitive)
    m2 = _desc(Kind.enum)
    tup = _desc(Kind.tuple)
    tup.child_links = [
        _dlink(m1, Role.member, position=1),
        _dlink(m2, Role.member, position=2),
    ]

    enum_opt_id = uuid4()
    root = build_attribute_value_tree(type_descriptor=tup, value=["x", enum_opt_id])
    assert [l.position for l in root.child_links] == [1, 2]
    assert root.child_links[0].child.primitive_value is not None
    assert root.child_links[0].child.primitive_value["value"] == "x"
    assert root.child_links[1].child.enum_option_id == enum_opt_id


def test_union_selects_exactly_one_member() -> None:
    u1 = _desc(Kind.primitive)
    u2 = _desc(Kind.enum)
    uni = _desc(Kind.union)
    uni.child_links = [
        _dlink(u1, Role.member, position=1),
        _dlink(u2, Role.member, position=2),
    ]

    enum_opt_id = uuid4()
    root = build_attribute_value_tree(
        type_descriptor=uni,
        value="ignored",
        union=UnionSelection(position=2, value=enum_opt_id),
    )
    assert len(root.child_links) == 1
    assert root.child_links[0].position == 2
    assert root.child_links[0].child.enum_option_id == enum_opt_id

    with pytest.raises(AttributeValueBuildError):
        build_attribute_value_tree(type_descriptor=uni, value="x")


def test_container_rejects_leaf_payload() -> None:
    elem_desc = _desc(Kind.primitive)
    list_desc = _desc(Kind.collection, collection_kind=AttributeCollectionType.list)
    list_desc.child_links = [_dlink(elem_desc, Role.element)]

    with pytest.raises(AttributeValueBuildError):
        build_attribute_value_tree(type_descriptor=list_desc, value="nope")
