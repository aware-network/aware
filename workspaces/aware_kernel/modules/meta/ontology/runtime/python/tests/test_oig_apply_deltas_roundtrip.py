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
from aware_meta_ontology.class_.class_config_enums import ClassValueMode
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph

from aware_meta.attribute.instance.value.builder import UnionSelection
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.apply import apply_object_instance_graph_deltas
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.diff import diff_object_instance_graph
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("User")
_ROLE_ELEMENT = Role("element")
_ROLE_KEY = Role("key")
_ROLE_MEMBER = Role("member")
_ROLE_VALUE = Role("value")


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
    desc.child_links.append(_link(parent=desc, child=element, role=_ROLE_ELEMENT))
    return desc


def _set_desc(*, element: AttributeTypeDescriptor) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.set,
        child_links=[],
    )
    desc.child_links.append(_link(parent=desc, child=element, role=_ROLE_ELEMENT))
    return desc


def _mapping_desc(
    *, key: AttributeTypeDescriptor, value: AttributeTypeDescriptor
) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(kind=Kind.mapping, child_links=[])
    desc.child_links.append(_link(parent=desc, child=key, role=_ROLE_KEY))
    desc.child_links.append(_link(parent=desc, child=value, role=_ROLE_VALUE))
    return desc


def _union_desc(*, members: list[AttributeTypeDescriptor]) -> AttributeTypeDescriptor:
    desc = AttributeTypeDescriptor(kind=Kind.union, child_links=[])
    for idx, member in enumerate(members, start=1):
        desc.child_links.append(
            _link(parent=desc, child=member, role=_ROLE_MEMBER, position=idx)
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


def _hash(g: ObjectInstanceGraph) -> str:
    return compute_hash(g, build_index(g))


def _make_ocg_and_opg(
    *, root_class_config: ClassConfig
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph]:
    ocg = ObjectConfigGraph(
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=root_class_config.class_fqn,
            class_config=root_class_config,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=root_class_config.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
    ]
    return ocg, opg


def _apply_roundtrip(
    *,
    old_g: ObjectInstanceGraph,
    new_g: ObjectInstanceGraph,
    attr_cfgs: list[AttributeConfig],
) -> None:
    deltas = diff_object_instance_graph(old_g, new_g)
    expected = _hash(new_g)
    _ = apply_object_instance_graph_deltas(
        graph=old_g,
        deltas=deltas,
        attribute_configs_by_id={cfg.id: cfg for cfg in attr_cfgs},
    )
    assert _hash(old_g) == expected


def test_apply_deltas_create_attribute_builds_value_root_before_attribute_append() -> (
    None
):
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = _make_user_config(attrs=[name_cfg])
    ocg, opg = _make_ocg_and_opg(root_class_config=user_cc)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    user_id = uuid4()
    graph_id = uuid4()

    g_root = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )
    ci_full = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g_full = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci_full,
        class_instances=[ci_full],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    deltas = diff_object_instance_graph(g_root, g_full)
    _ = apply_object_instance_graph_deltas(
        graph=g_root,
        deltas=deltas,
        attribute_configs_by_id={name_cfg.id: name_cfg},
        class_configs_by_id={user_cc.id: user_cc},
    )

    assert _hash(g_root) == _hash(g_full)
    root_attr = g_root.root_class_instance.attributes[0]
    assert root_attr.owner_key == user_id
    assert root_attr.value_root_id == root_attr.value_root.id


def test_apply_deltas_list_append_roundtrip() -> None:
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
    ocg_id = uuid4()
    opg_id = uuid4()
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

    g_old = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_old,
        class_instances=[ci_old],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_new = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=g_old.object_projection_graph_id,
        root_class_instance=ci_new,
        class_instances=[ci_new],
        class_instance_relationships=[],
        oig_id=g_old.id,
    )

    _apply_roundtrip(old_g=g_old, new_g=g_new, attr_cfgs=[items_cfg])


def test_apply_deltas_set_add_roundtrip() -> None:
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
    ocg_id = uuid4()
    opg_id = uuid4()
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

    g_old = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_old,
        class_instances=[ci_old],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_new = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=g_old.object_projection_graph_id,
        root_class_instance=ci_new,
        class_instances=[ci_new],
        class_instance_relationships=[],
        oig_id=g_old.id,
    )

    _apply_roundtrip(old_g=g_old, new_g=g_new, attr_cfgs=[tags_cfg])


def test_apply_deltas_inline_class_payload_roundtrip() -> None:
    payload_cc = make_class_config(
        "Payload",
        class_fqn=test_class_fqn("Payload"),
        value_mode=ClassValueMode.inline_value,
    )
    payload_desc = AttributeTypeDescriptor(
        kind=Kind.class_,
        class_config_id=payload_cc.id,
        class_config=payload_cc,
        child_links=[],
    )
    payload_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="payload",
        is_required=True,
        type_descriptor=payload_desc,
    )
    user_cc = _make_user_config(attrs=[payload_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        payload: dict[str, object]

    user_id = uuid4()
    graph_id = uuid4()
    ocg_id = uuid4()
    opg_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, payload={"k": "v1"}),
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, payload={"k": "v2"}),
    )

    g_old = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_old,
        class_instances=[ci_old],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_new = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=g_old.object_projection_graph_id,
        root_class_instance=ci_new,
        class_instances=[ci_new],
        class_instance_relationships=[],
        oig_id=g_old.id,
    )

    _apply_roundtrip(old_g=g_old, new_g=g_new, attr_cfgs=[payload_cfg])


def test_apply_deltas_mapping_value_update_roundtrip() -> None:
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
    ocg_id = uuid4()
    opg_id = uuid4()
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

    g_old = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_old,
        class_instances=[ci_old],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_new = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=g_old.object_projection_graph_id,
        root_class_instance=ci_new,
        class_instances=[ci_new],
        class_instance_relationships=[],
        oig_id=g_old.id,
    )

    _apply_roundtrip(old_g=g_old, new_g=g_new, attr_cfgs=[props_cfg])


def test_apply_deltas_union_selection_switch_roundtrip() -> None:
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
    ocg_id = uuid4()
    opg_id = uuid4()
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

    g_old = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_old,
        class_instances=[ci_old],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_new = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=g_old.object_projection_graph_id,
        root_class_instance=ci_new,
        class_instances=[ci_new],
        class_instance_relationships=[],
        oig_id=g_old.id,
    )

    _apply_roundtrip(old_g=g_old, new_g=g_new, attr_cfgs=[union_cfg])


def test_apply_deltas_enum_and_class_ref_roundtrip() -> None:
    role_cfg = make_attribute_config(
        owner_key=_USER_FQN, name="role", is_required=True, type_descriptor=_enum_desc()
    )
    target_cc = make_class_config(
        "Target", class_fqn=test_class_fqn("Target"), class_config_attribute_configs=[]
    )
    ref_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="target_id",
        is_required=True,
        type_descriptor=_class_desc(class_config_id=target_cc.id),
    )
    user_cc = _make_user_config(attrs=[role_cfg, ref_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        role: str
        target_id: UUID

    enum_user = uuid4()
    enum_admin = uuid4()

    def resolver(_desc: AttributeTypeDescriptor, value: object) -> UUID:
        if value == "user":
            return enum_user
        if value == "admin":
            return enum_admin
        raise ValueError(f"unknown: {value}")

    user_id = uuid4()
    t1 = uuid4()
    t2 = uuid4()
    graph_id = uuid4()
    ocg_id = uuid4()
    opg_id = uuid4()
    ci_old = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, role="user", target_id=t1),
        enum_option_resolver=resolver,
    )
    ci_new = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, role="admin", target_id=t2),
        enum_option_resolver=resolver,
    )

    g_old = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_old,
        class_instances=[ci_old],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_new = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=g_old.object_projection_graph_id,
        root_class_instance=ci_new,
        class_instances=[ci_new],
        class_instance_relationships=[],
        oig_id=g_old.id,
    )

    _apply_roundtrip(old_g=g_old, new_g=g_new, attr_cfgs=[role_cfg, ref_cfg])


def test_apply_deltas_relationship_add_and_remove_roundtrip() -> None:
    cc = make_class_config(
        "X", class_fqn=test_class_fqn("X"), class_config_attribute_configs=[]
    )

    from aware_orm.models.base_model import BaseORMModel

    class X(BaseORMModel):
        pass

    a_id = uuid4()
    b_id = uuid4()
    graph_id = uuid4()
    ocg_id = uuid4()
    opg_id = uuid4()
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
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=a_ci,
        class_instances=[a_ci, b_ci],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    g_with_rel = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=g_empty.object_projection_graph_id,
        root_class_instance=a_ci,
        class_instances=[a_ci, b_ci],
        class_instance_relationships=[rel],
        oig_id=g_empty.id,
    )

    # Add relationship
    empty_hash = _hash(g_empty)
    with_hash = _hash(g_with_rel)
    deltas_add = diff_object_instance_graph(g_empty, g_with_rel)
    deltas_del = diff_object_instance_graph(g_with_rel, g_empty)
    _ = apply_object_instance_graph_deltas(
        graph=g_empty, deltas=deltas_add, attribute_configs_by_id={}
    )
    assert _hash(g_empty) == with_hash

    # Remove relationship
    _ = apply_object_instance_graph_deltas(
        graph=g_with_rel, deltas=deltas_del, attribute_configs_by_id={}
    )
    assert _hash(g_with_rel) == empty_hash
