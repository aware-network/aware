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
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)

from aware_meta.attribute.instance.value.builder import UnionSelection
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")
_TEST_OIGI_ID = uuid4()


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _link(
    *,
    parent: AttributeTypeDescriptor,
    child: AttributeTypeDescriptor,
    role: Role,
    position: int = 0,
) -> AttributeTypeDescriptorLink:
    return AttributeTypeDescriptorLink(
        attribute_type_descriptor_id=parent.id,
        child=child,
        child_id=child.id,
        role=role,
        position=position,
    )


def _list_desc(*, element: AttributeTypeDescriptor) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[],
    )
    desc.child_links.append(_link(parent=desc, child=element, role=Role.element))
    return desc


def _set_desc(*, element: AttributeTypeDescriptor) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.set,
        child_links=[],
    )
    desc.child_links.append(_link(parent=desc, child=element, role=Role.element))
    return desc


def _mapping_desc(
    *, key: AttributeTypeDescriptor, value: AttributeTypeDescriptor
) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    desc.child_links.append(_link(parent=desc, child=key, role=Role.key))
    desc.child_links.append(_link(parent=desc, child=value, role=Role.value_))
    return desc


def _union_desc(*, members: list[AttributeTypeDescriptor]) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(kind=Kind.union, child_links=[])
    for idx, member in enumerate(members, start=1):
        desc.child_links.append(
            _link(parent=desc, child=member, role=Role.member, position=idx)
        )
    return desc


def _make_user_config(*, attrs: list[AttributeConfig]) -> ClassConfig:
    cc = make_class_config(
        "User", class_fqn=_USER_FQN, class_config_attribute_configs=[]
    )
    cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=cc.id, attribute_config=cfg, name=cfg.name, position=pos
        )
        for pos, cfg in enumerate(attrs)
    ]
    return cc


def _hash(g) -> str:
    return compute_hash(g, index=build_index(g))


def _scalar_set_value(change, prop: str):
    for d in change.change_deltas:
        if d.kind == ChangeDeltaKind.scalar_set and d.property == prop:
            return d.payload.get("value")
    return None


def test_change_graph_roundtrip_primitive_update() -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = _make_user_config(attrs=[name_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    user_id: UUID = uuid4()
    graph_id = uuid4()
    u1 = User(id=user_id, name="a")
    u2 = User(id=user_id, name="b")

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )

    ocg_id = uuid4()
    opg_id = uuid4()
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = diff_object_instance_graph_changes(
        g1, g2, object_instance_graph_identity_id=_TEST_OIGI_ID
    )
    assert changes

    # ClassInstance identity/provenance fields are create evidence; UPDATE deltas
    # stay sparse so handler commits do not rewrite stable identity fields.
    object_changes = next(c for c in changes if c.class_instance_changes)
    ci_change = object_changes.class_instance_changes[0]
    assert ci_change.change.type == ChangeType.update
    class_update_properties = {
        delta.property
        for delta in ci_change.change.change_deltas
        if delta.property is not None
    }
    assert "class_config_id" not in class_update_properties
    assert "source_object_id" not in class_update_properties

    attr_change = ci_change.attribute_changes[0]
    assert attr_change.change.type == ChangeType.update
    assert _scalar_set_value(attr_change.change, "attribute_config_id") == str(
        name_cfg.id
    )

    apply_object_instance_graph_changes(
        graph=g1, changes=changes, attribute_configs_by_id={name_cfg.id: name_cfg}
    )
    assert _hash(g1) == _hash(g2)


def test_change_graph_roundtrip_list_append() -> None:
    items_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="items",
        is_required=True,
        type_descriptor=_list_desc(element=_primitive_desc()),
    )
    user_cc = _make_user_config(attrs=[items_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        items: list[int]

    user_id: UUID = uuid4()
    graph_id = uuid4()
    u1 = User(id=user_id, items=[1])
    u2 = User(id=user_id, items=[1, 2])

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )

    ocg_id = uuid4()
    opg_id = uuid4()
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = diff_object_instance_graph_changes(
        g1, g2, object_instance_graph_identity_id=_TEST_OIGI_ID
    )
    assert changes

    apply_object_instance_graph_changes(
        graph=g1, changes=changes, attribute_configs_by_id={items_cfg.id: items_cfg}
    )
    assert _hash(g1) == _hash(g2)


def test_change_graph_roundtrip_mapping_value_update() -> None:
    props_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="props",
        is_required=True,
        type_descriptor=_mapping_desc(key=_primitive_desc(), value=_primitive_desc()),
    )
    user_cc = _make_user_config(attrs=[props_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        props: dict[str, str]

    user_id: UUID = uuid4()
    graph_id = uuid4()
    u1 = User(id=user_id, props={"k": "v1"})
    u2 = User(id=user_id, props={"k": "v2"})

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )

    ocg_id = uuid4()
    opg_id = uuid4()
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = diff_object_instance_graph_changes(
        g1, g2, object_instance_graph_identity_id=_TEST_OIGI_ID
    )
    assert changes

    apply_object_instance_graph_changes(
        graph=g1, changes=changes, attribute_configs_by_id={props_cfg.id: props_cfg}
    )
    assert _hash(g1) == _hash(g2)


def test_change_graph_roundtrip_set_add() -> None:
    tags_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="tags",
        is_required=True,
        type_descriptor=_set_desc(element=_primitive_desc()),
    )
    user_cc = _make_user_config(attrs=[tags_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        tags: set[str]

    user_id: UUID = uuid4()
    graph_id = uuid4()
    u1 = User(id=user_id, tags={"a", "b"})
    u2 = User(id=user_id, tags={"a", "b", "c"})

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )

    ocg_id = uuid4()
    opg_id = uuid4()
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = diff_object_instance_graph_changes(
        g1, g2, object_instance_graph_identity_id=_TEST_OIGI_ID
    )
    assert changes

    apply_object_instance_graph_changes(
        graph=g1, changes=changes, attribute_configs_by_id={tags_cfg.id: tags_cfg}
    )
    assert _hash(g1) == _hash(g2)


def test_change_graph_roundtrip_union_selection_switch() -> None:
    union_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="u",
        is_required=True,
        type_descriptor=_union_desc(members=[_primitive_desc(), _primitive_desc()]),
    )
    user_cc = _make_user_config(attrs=[union_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        u: object

    user_id: UUID = uuid4()
    graph_id = uuid4()
    u1 = User(id=user_id, u="a")
    u2 = User(id=user_id, u=5)

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=u1,
        union_selections={"u": UnionSelection(position=1, value="a")},
    )
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=u2,
        union_selections={"u": UnionSelection(position=2, value=5)},
    )

    ocg_id = uuid4()
    opg_id = uuid4()
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g2 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = diff_object_instance_graph_changes(
        g1, g2, object_instance_graph_identity_id=_TEST_OIGI_ID
    )
    assert changes

    apply_object_instance_graph_changes(
        graph=g1, changes=changes, attribute_configs_by_id={union_cfg.id: union_cfg}
    )
    assert _hash(g1) == _hash(g2)
