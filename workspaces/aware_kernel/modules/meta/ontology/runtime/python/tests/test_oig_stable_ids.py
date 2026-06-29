from __future__ import annotations

from uuid import UUID, uuid4

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
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

from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.graph.config.stable_ids import stable_attribute_id
from aware_meta.test_support import make_attribute_config, test_class_fqn


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


def test_build_attribute_assigns_deterministic_ids_for_attribute_and_value_tree() -> (
    None
):
    owner_key = UUID("11111111-1111-1111-1111-111111111111")
    attribute_config_id = UUID("22222222-2222-2222-2222-222222222222")

    elem_desc = _desc(Kind.primitive)
    list_desc = _desc(Kind.collection, collection_kind=AttributeCollectionType.list)
    list_desc.child_links = [_dlink(elem_desc, Role.element)]

    cfg = AttributeConfig(
        id=attribute_config_id,
        owner_key=test_class_fqn("User"),
        name="items",
        description=None,
        default_value=None,
        is_primary=False,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        type_descriptor=list_desc,
        type_descriptor_id=list_desc.id,
    )

    a1 = build_attribute(
        owner_key=owner_key,
        attribute_config=cfg,
        value=[0, 1],
    )
    a2 = build_attribute(
        owner_key=owner_key,
        attribute_config=cfg,
        value=[0, 1],
    )

    assert a1.id == a2.id
    assert a1.id == stable_attribute_id(
        owner_key=owner_key, attribute_config_id=attribute_config_id
    )
    assert a1.owner_key == a2.owner_key == owner_key
    assert a1.value_root is not None and a2.value_root is not None
    assert a1.value_root.id == a2.value_root.id

    # Link + child ids are stable across rebuilds (slot-key based).
    assert len(a1.value_root.child_links) == len(a2.value_root.child_links) == 2
    for l1, l2 in zip(a1.value_root.child_links, a2.value_root.child_links):
        assert l1.id == l2.id
        assert l1.child_id == l2.child_id
        assert l1.child is not None and l2.child is not None
        assert l1.child.id == l2.child.id
