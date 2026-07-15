from __future__ import annotations

import re
from uuid import UUID, uuid4


from aware_history_ontology.change.change_enums import ChangeType

from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)

from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
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

from aware_meta.attribute.instance.value.builder import UnionSelection
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.diff import (
    DeltaOp,
    diff_object_instance_graph,
    ObjectInstanceGraphDelta,
)
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind as K
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _enum_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.enum, child_links=[])


def _class_desc(*, class_config_id: UUID) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=Kind.class_, class_config_id=class_config_id, child_links=[]
    )


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


def _build_root_delta(
    old_graph: ObjectInstanceGraph, new_graph: ObjectInstanceGraph
) -> ObjectInstanceGraphDelta:
    deltas = diff_object_instance_graph(old_graph, new_graph)
    assert len(deltas) == 1
    root = deltas[0]
    assert root.kind == K.class_instance
    assert root.operation == ChangeType.update
    return root


def _find_child(
    delta: ObjectInstanceGraphDelta, *, kind: K, path_key: str
) -> ObjectInstanceGraphDelta:
    children = delta.child_deltas.get(kind, [])
    matches = [d for d in children if d.path_key == path_key]
    assert (
        len(matches) == 1
    ), f"expected 1 child kind={kind} path_key={path_key}, got {len(matches)}"
    return matches[0]


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


def _make_graph(
    *, name: str, ci: ClassInstance, rels: list[ClassInstanceRelationship] | None = None
) -> ObjectInstanceGraph:
    rels = rels or []
    return build_object_instance_graph_from_class_instances(
        name=name,
        description="d",
        object_config_graph_id=uuid4(),
        object_projection_graph_id=uuid4(),
        root_class_instance=ci,
        class_instances=[ci],
        class_instance_relationships=rels,
        oig_id=ci.object_instance_graph_id,
    )


def test_diff_list_append_emits_create_slot_and_value() -> None:
    items_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="items",
        is_required=True,
        type_descriptor=_list_desc(element=_primitive_desc()),
    )
    user_cc = _make_user_config(attrs=[items_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        items: list[str]

    user_id = uuid4()
    graph_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, items=["a", "b"]),
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, items=["a", "b", "c"]),
    )

    g_old = _make_graph(name="g", ci=ci_old)
    g_new = _make_graph(name="g", ci=ci_new)

    root = _build_root_delta(g_old, g_new)
    attr = _find_child(root, kind=K.attribute, path_key=f"attr:{items_cfg.id}")
    container = _find_child(attr, kind=K.attribute_value, path_key="value")

    link_deltas = container.child_deltas.get(K.attribute_value_link, [])
    creates = [d for d in link_deltas if d.operation == ChangeType.create]
    assert len(creates) == 1
    assert creates[0].path_key == "link:element:2"

    created_link = creates[0]
    created_value = _find_child(created_link, kind=K.attribute_value, path_key="value")
    assert created_value.operation == ChangeType.create
    assert any(
        fd.property == "primitive_value" and fd.op == DeltaOp.SET and fd.value == "c"
        for fd in created_value.field_deltas
    )


def test_diff_set_add_emits_create_identity_slot() -> None:
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

    user_id = uuid4()
    graph_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, tags={"a", "b"}),
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, tags={"a", "b", "c"}),
    )

    g_old = _make_graph(name="g", ci=ci_old)
    g_new = _make_graph(name="g", ci=ci_new)

    root = _build_root_delta(g_old, g_new)
    attr = _find_child(root, kind=K.attribute, path_key=f"attr:{tags_cfg.id}")
    container = _find_child(attr, kind=K.attribute_value, path_key="value")

    link_deltas = container.child_deltas.get(K.attribute_value_link, [])
    creates = [d for d in link_deltas if d.operation == ChangeType.create]
    assert len(creates) == 1
    assert re.fullmatch(r"link:element:[0-9a-f]{64}", creates[0].path_key)

    created_value = _find_child(creates[0], kind=K.attribute_value, path_key="value")
    assert any(
        fd.property == "primitive_value" and fd.op == DeltaOp.SET and fd.value == "c"
        for fd in created_value.field_deltas
    )


def test_diff_mapping_value_update_targets_value_node_for_key() -> None:
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

    user_id = uuid4()
    graph_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, props={"k": "v1"}),
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, props={"k": "v2"}),
    )

    g_old = _make_graph(name="g", ci=ci_old)
    g_new = _make_graph(name="g", ci=ci_new)

    # Read the identity_key for key "k" from the old graph.
    attr_old = ci_old.attributes[0]
    assert attr_old.value_root is not None
    key_link = next(l for l in attr_old.value_root.child_links if l.role == Role.key)
    assert key_link.identity_key is not None
    ident = key_link.identity_key

    root = _build_root_delta(g_old, g_new)
    attr = _find_child(root, kind=K.attribute, path_key=f"attr:{props_cfg.id}")
    container = _find_child(attr, kind=K.attribute_value, path_key="value")

    # We expect the VALUE slot for this key to exist (same identity_key) and its child VALUE node to update.
    value_link = _find_child(
        container, kind=K.attribute_value_link, path_key=f"link:value:{ident}"
    )
    value_node = _find_child(value_link, kind=K.attribute_value, path_key="value")
    assert value_node.operation == ChangeType.update
    assert any(
        fd.property == "primitive_value" and fd.op == DeltaOp.SET and fd.value == "v2"
        for fd in value_node.field_deltas
    )


def test_diff_union_selection_switches_member_slot() -> None:
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

    user_id = uuid4()
    graph_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, u="a"),
        union_selections={"u": UnionSelection(position=1, value="a")},
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, u=5),
        union_selections={"u": UnionSelection(position=2, value=5)},
    )

    g_old = _make_graph(name="g", ci=ci_old)
    g_new = _make_graph(name="g", ci=ci_new)

    root = _build_root_delta(g_old, g_new)
    attr = _find_child(root, kind=K.attribute, path_key=f"attr:{union_cfg.id}")
    container = _find_child(attr, kind=K.attribute_value, path_key="value")

    link_deltas = container.child_deltas.get(K.attribute_value_link, [])
    deletes = [d for d in link_deltas if d.operation == ChangeType.delete]
    creates = [d for d in link_deltas if d.operation == ChangeType.create]
    assert len(deletes) == 1
    assert len(creates) == 1
    assert deletes[0].path_key == "link:member:1"
    assert creates[0].path_key == "link:member:2"


def test_diff_enum_update_uses_resolver_and_emits_set_delta() -> None:
    role_cfg = make_attribute_config(
        owner_key=_USER_FQN, name="role", is_required=True, type_descriptor=_enum_desc()
    )
    user_cc = _make_user_config(attrs=[role_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        role: str

    enum_user = uuid4()
    enum_admin = uuid4()

    def resolver(_desc: AttributeTypeDescriptor, value: object) -> UUID:
        if value == "user":
            return enum_user
        if value == "admin":
            return enum_admin
        raise ValueError(f"unknown: {value}")

    user_id = uuid4()
    graph_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, role="user"),
        enum_option_resolver=resolver,
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, role="admin"),
        enum_option_resolver=resolver,
    )

    g_old = _make_graph(name="g", ci=ci_old)
    g_new = _make_graph(name="g", ci=ci_new)

    root = _build_root_delta(g_old, g_new)
    attr = _find_child(root, kind=K.attribute, path_key=f"attr:{role_cfg.id}")
    value_node = _find_child(attr, kind=K.attribute_value, path_key="value")
    assert value_node.operation == ChangeType.update
    assert any(
        fd.property == "enum_option_id"
        and fd.op == DeltaOp.SET
        and fd.value == enum_admin
        for fd in value_node.field_deltas
    )


def test_diff_class_ref_update_emits_set_delta() -> None:
    target_cc = make_class_config(
        "Target", class_fqn=test_class_fqn("Target"), class_config_attribute_configs=[]
    )
    ref_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="target_id",
        is_required=True,
        type_descriptor=_class_desc(class_config_id=target_cc.id),
    )
    user_cc = _make_user_config(attrs=[ref_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        target_id: UUID

    user_id = uuid4()
    t1 = uuid4()
    t2 = uuid4()
    graph_id = uuid4()

    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, target_id=t1),
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, target_id=t2),
    )

    g_old = _make_graph(name="g", ci=ci_old)
    g_new = _make_graph(name="g", ci=ci_new)

    root = _build_root_delta(g_old, g_new)
    attr = _find_child(root, kind=K.attribute, path_key=f"attr:{ref_cfg.id}")
    value_node = _find_child(attr, kind=K.attribute_value, path_key="value")
    assert value_node.operation == ChangeType.update
    assert any(
        fd.property == "class_instance_id" and fd.op == DeltaOp.SET and fd.value == t2
        for fd in value_node.field_deltas
    )


def test_diff_relationship_add_and_remove() -> None:
    # Minimal graph: two instances, relationship is an independent member.
    cc = make_class_config(
        "X", class_fqn=test_class_fqn("X"), class_config_attribute_configs=[]
    )

    from aware_orm.models.base_model import BaseORMModel

    class X(BaseORMModel):
        pass

    a_id = uuid4()
    b_id = uuid4()
    graph_id = uuid4()
    a_ci = build_class_instance(
        object_instance_graph_id=graph_id, class_config=cc, source=X(id=a_id)
    )
    b_ci = build_class_instance(
        object_instance_graph_id=graph_id, class_config=cc, source=X(id=b_id)
    )

    rel_id = uuid4()
    rel = ClassInstanceRelationship(
        object_instance_graph_id=graph_id,
        class_config_relationship_id=rel_id,
        source_class_instance_id=a_ci.id,
        target_class_instance_id=b_ci.id,
    )

    g_empty = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=uuid4(),
        object_projection_graph_id=uuid4(),
        root_class_instance=a_ci,
        class_instances=[a_ci, b_ci],
        class_instance_relationships=[],
    )
    g_with_rel = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=uuid4(),
        object_projection_graph_id=g_empty.object_projection_graph_id,
        root_class_instance=a_ci,
        class_instances=[a_ci, b_ci],
        class_instance_relationships=[rel],
        oig_id=g_empty.id,
    )

    # Add relationship
    deltas_add = diff_object_instance_graph(g_empty, g_with_rel)
    assert len(deltas_add) == 1
    assert deltas_add[0].kind == K.relationship_instance
    assert deltas_add[0].operation == ChangeType.create

    # Remove relationship
    deltas_del = diff_object_instance_graph(g_with_rel, g_empty)
    assert len(deltas_del) == 1
    assert deltas_del[0].kind == K.relationship_instance
    assert deltas_del[0].operation == ChangeType.delete
