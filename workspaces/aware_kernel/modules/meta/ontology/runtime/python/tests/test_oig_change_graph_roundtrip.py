from __future__ import annotations

from decimal import Decimal
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
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig
from aware_code.primitive_codec_base import build_code_primitive_type
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

from aware_meta.attribute.instance.value.builder import UnionSelection
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.apply import (
    apply_object_instance_graph_body_draft,
    apply_object_instance_graph_changes,
)
from aware_meta.graph.instance.commit.body_codec import (
    build_oig_commit_body_from_changes,
    build_oig_commit_body_from_draft,
    oig_commit_body_draft_from_changes,
)
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.diff import (
    ClassInstanceChangeBuildProfile,
    build_class_instance_changes_from_iterables,
    build_object_instance_graph_create_body_draft,
    diff_object_instance_graph_changes,
)
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_orm.models.constructor_profile import capture_orm_constructor_profile
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import (
    disable_change_tracking_hooks,
    scoped_change_collection,
)
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


def _decimal_desc() -> AttributeTypeDescriptor:
    primitive_type = build_code_primitive_type(base_type=CodePrimitiveBaseType.decimal)
    primitive_config = PrimitiveConfig(
        primitive_type=primitive_type,
        primitive_type_id=primitive_type.id,
    )
    return AttributeTypeDescriptor(
        kind=Kind.primitive,
        primitive_config=primitive_config,
        primitive_config_id=primitive_config.id,
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

    with scoped_change_collection() as collector:
        _ = apply_object_instance_graph_changes(
            graph=g1,
            changes=changes,
            attribute_configs_by_id={name_cfg.id: name_cfg},
        )

    replay_changes = collector.snapshot()
    assert not replay_changes.created_ids
    assert not replay_changes.touched_ids
    assert not replay_changes.deleted_ids
    assert _hash(g1) == _hash(g2)


def test_decimal_snapshot_hash_delta_and_replay_are_canonical() -> None:
    amount_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="amount",
        is_required=True,
        type_descriptor=_decimal_desc(),
    )
    user_cc = _make_user_config(attrs=[amount_cfg])

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        amount: Decimal

    user_id = uuid4()
    graph_id = uuid4()
    ocg_id = uuid4()
    opg_id = uuid4()

    def _graph(value: Decimal) -> ObjectInstanceGraph:
        class_instance = build_class_instance(
            object_instance_graph_id=graph_id,
            class_config=user_cc,
            source=User(id=user_id, amount=value),
        )
        return build_object_instance_graph_from_class_instances(
            name="g",
            description="d",
            object_config_graph_id=ocg_id,
            object_projection_graph_id=opg_id,
            root_class_instance=class_instance,
            class_instances=[class_instance],
            class_instance_relationships=[],
            oig_id=graph_id,
        )

    initial = _graph(Decimal("1.2300"))
    equivalent = _graph(Decimal("1.23"))
    updated = _graph(Decimal("2.500"))

    value_root = initial.root_class_instance.class_instance_attributes[
        0
    ].attribute.value_root
    assert value_root.primitive_value == {"value": "1.23"}
    assert _hash(initial) == _hash(equivalent)

    snapshot = ObjectInstanceGraph.model_validate_json(initial.model_dump_json())
    assert _hash(snapshot) == _hash(initial)

    changes = diff_object_instance_graph_changes(
        initial,
        updated,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    assert changes
    apply_object_instance_graph_changes(
        graph=initial,
        changes=changes,
        attribute_configs_by_id={amount_cfg.id: amount_cfg},
    )
    assert _hash(initial) == _hash(updated)
    replayed_value = initial.root_class_instance.class_instance_attributes[
        0
    ].attribute.value_root.primitive_value
    assert replayed_value == {"value": "2.5"}


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


def test_sparse_create_profile_counts_exclusive_value_tree_constructors() -> None:
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

    graph_id = uuid4()
    class_instance = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=uuid4(), items=[1, 2]),
    )
    graph = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=uuid4(),
        object_projection_graph_id=uuid4(),
        root_class_instance=class_instance,
        class_instances=[class_instance],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    profile = ClassInstanceChangeBuildProfile()

    with (
        disable_autobind(),
        disable_change_tracking_hooks(),
        capture_orm_constructor_profile(
            model_names=("Change", "ChangeDelta")
        ) as constructor_profile,
    ):
        changes = build_class_instance_changes_from_iterables(
            graph=graph,
            old_class_instances=(),
            new_class_instances=(class_instance,),
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            build_profile=profile,
        )

    attribute = class_instance.attributes[0]
    value_count, link_count = _value_tree_counts(attribute.value_root)
    assert len(changes) == 1
    assert profile.create_class_instance_wrapper_count == 1
    assert profile.create_attribute_input_count == 1
    assert profile.create_attribute_unique_count == 1
    assert profile.create_attribute_wrapper_count == 1
    assert profile.create_attribute_value_wrapper_count == value_count
    assert profile.create_attribute_value_link_wrapper_count == link_count
    assert profile.create_change_shell_count == 2 + value_count + link_count
    assert profile.create_change_delta_count > profile.create_change_shell_count
    assert (
        profile.create_change_delta_payload_value_count
        == profile.create_change_delta_count
    )
    assert (
        profile.create_change_delta_json_wrapper_count
        == profile.create_change_delta_count
    )
    assert profile.create_change_delta_model_count == profile.create_change_delta_count
    assert profile.create_change_shell_s >= 0.0
    assert profile.create_change_deltas_s >= 0.0
    assert profile.create_change_delta_payload_value_s >= 0.0
    assert profile.create_change_delta_json_wrapper_s >= 0.0
    assert profile.create_change_delta_model_s >= 0.0
    assert profile.create_attribute_value_wrapper_s >= 0.0
    assert profile.create_attribute_value_link_wrapper_s >= 0.0
    change_metrics = constructor_profile.models["Change"]
    change_delta_metrics = constructor_profile.models["ChangeDelta"]
    assert change_metrics.model_validation_count == profile.create_change_shell_count
    assert change_metrics.relationship_pre_validator_count == (
        profile.create_change_shell_count
    )
    assert change_metrics.uuid_default_count == profile.create_change_shell_count
    assert (
        change_metrics.post_init_hook_guard_count == profile.create_change_shell_count
    )
    assert change_delta_metrics.model_validation_count == (
        profile.create_change_delta_count
    )
    assert change_delta_metrics.relationship_pre_validator_count == (
        profile.create_change_delta_count
    )
    assert change_delta_metrics.uuid_default_count == profile.create_change_delta_count
    assert change_delta_metrics.post_init_hook_guard_count == (
        profile.create_change_delta_count
    )

    semantic_replay = graph.model_copy(deep=True)
    semantic_replay.class_instances = []
    semantic_replay.root_class_instance = None
    semantic_changes = diff_object_instance_graph_changes(
        semantic_replay,
        graph,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    body_draft = oig_commit_body_draft_from_changes(semantic_changes)
    commit_id = uuid4()
    semantic_body = build_oig_commit_body_from_changes(
        commit_id=commit_id,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph.id,
        changes=semantic_changes,
    )
    draft_body = build_oig_commit_body_from_draft(
        commit_id=commit_id,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph.id,
        draft=body_draft,
    )
    assert draft_body.canonical_bytes == semantic_body.canonical_bytes

    draft_replay = semantic_replay.model_copy(deep=True)
    apply_object_instance_graph_changes(
        graph=semantic_replay,
        changes=semantic_changes,
        attribute_configs_by_id={items_cfg.id: items_cfg},
        class_configs_by_id={user_cc.id: user_cc},
    )
    apply_object_instance_graph_body_draft(
        graph=draft_replay,
        body_draft=body_draft,
        attribute_configs_by_id={items_cfg.id: items_cfg},
        class_configs_by_id={user_cc.id: user_cc},
    )
    assert _hash(draft_replay) == _hash(semantic_replay)

    direct_draft = build_object_instance_graph_create_body_draft(
        class_instances=(class_instance,),
        created_at=semantic_changes[0].change.created_at,
    )
    direct_replay = draft_replay.model_copy(deep=True)
    direct_replay.class_instances = []
    direct_replay.root_class_instance = None
    apply_object_instance_graph_body_draft(
        graph=direct_replay,
        body_draft=direct_draft,
        attribute_configs_by_id={items_cfg.id: items_cfg},
        class_configs_by_id={user_cc.id: user_cc},
    )
    assert _hash(direct_replay) == _hash(semantic_replay)


def _value_tree_counts(value: AttributeValue) -> tuple[int, int]:
    value_count = 1
    link_count = len(value.child_links)
    for link in value.child_links:
        if link.child is None:
            continue
        child_value_count, child_link_count = _value_tree_counts(link.child)
        value_count += child_value_count
        link_count += child_link_count
    return value_count, link_count


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
