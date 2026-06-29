from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# History Ontology
from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_delta import ChangeDelta
from aware_history_ontology.change.change_enums import ChangeDeltaKind, ChangeType
from aware_history_ontology.commit.commit import Commit

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.attribute.attribute_change import AttributeChange
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.attribute.attribute_value_change import AttributeValueChange
from aware_meta_ontology.enum.enum_option import EnumOption

# Meta Runtime
from aware_meta.graph.config.stable_ids import stable_object_config_graph_node_id
from aware_meta.graph.instance.commit.ocg_delta import (
    build_ocg_delta_from_oig_commit,
    index_oig_snapshot_for_ocg_delta,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_enum_config,
    make_ocg_node,
    test_class_fqn,
    test_enum_fqn,
)

from aware_code.types import JsonObject


def _meta_class(name: str):
    return make_class_config(
        name, class_fqn=test_class_fqn(name), class_config_attribute_configs=[]
    )


def _meta_enum(name: str):
    return make_enum_config(name, enum_fqn=test_enum_fqn(name), enum_options=[])


def _test_commit(*, key: str = "test-commit") -> Commit:
    return Commit(
        key=key,
        lane_id=uuid4(),
        author_id=uuid4(),
        created_at=datetime.now(UTC),
    )


def _test_change(*, key: str, type: ChangeType) -> Change:
    return Change(
        key=key,
        created_at=datetime.now(UTC),
        type=type,
        change_deltas=[],
    )


def _test_delta(
    *,
    change: Change,
    position: int,
    kind: ChangeDeltaKind,
    payload: JsonObject,
    property: str | None = None,
) -> ChangeDelta:
    return ChangeDelta(
        change_id=change.id,
        position=position,
        property=property,
        kind=kind,
        payload=payload,
    )


def _make_oig_commit(
    *,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_id: UUID,
    object_instance_graph_changes: list[ObjectInstanceGraphChange],
) -> ObjectInstanceGraphCommit:
    return ObjectInstanceGraphCommit(
        commit=_test_commit(),
        object_instance_graph_changes=object_instance_graph_changes,
        object_instance_graph_key="test-worldline",
        object_instance_graph_name="test worldline",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        projection_hash="sha256:test:opg",
        source_language=CodeLanguage.aware,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
    )


def test_ocg_delta_from_oig_commit_maps_class_config_create() -> None:
    ocg_id = uuid4()

    meta_class_config = _meta_class("ClassConfig")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_class_config,
            class_config_id=meta_class_config.id,
            object_config_graph_id=schema_graph.id,
        )
    ]

    entity_id = uuid4()
    change = _test_change(key="class_config:create", type=ChangeType.create)
    change.change_deltas = [
        _test_delta(
            change=change,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(meta_class_config.id)),
        ),
        _test_delta(
            change=change,
            position=1,
            property="name",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value="User"),
        ),
    ]

    ci_change = ClassInstanceChange(
        class_instance_id=entity_id,
        change=change,
    )
    og_change = ObjectInstanceGraphChange(
        change=change,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_change],
    )

    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_change],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit, schema_graph=schema_graph
    )
    assert delta.object_config_graph_id == ocg_id
    assert delta.language == CodeLanguage.aware
    assert delta.graph_hash_pre is None
    assert delta.graph_hash_post is None
    assert not delta.warnings

    assert len(delta.node_deltas) == 1
    node_delta = delta.node_deltas[0]
    assert node_delta.change_type == ChangeType.create
    assert node_delta.node_type == ObjectConfigGraphNodeType.class_
    assert node_delta.entity_id == entity_id
    assert node_delta.node_id == stable_object_config_graph_node_id(
        object_config_graph_id=ocg_id,
        type=ObjectConfigGraphNodeType.class_.value,
        node_key=str(entity_id),
    )
    assert node_delta.payload is not None
    assert node_delta.payload.get("name") == "User"


def test_ocg_delta_from_oig_commit_uses_post_index_when_class_config_id_missing() -> (
    None
):
    ocg_id = uuid4()

    meta_class_config = _meta_class("ClassConfig")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_class_config,
            class_config_id=meta_class_config.id,
            object_config_graph_id=schema_graph.id,
        )
    ]

    entity_id = uuid4()
    change = _test_change(key="class_config:update:name", type=ChangeType.update)
    change.change_deltas = [
        _test_delta(
            change=change,
            position=0,
            property="name",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value="UserRenamed"),
        ),
    ]

    ci_change = ClassInstanceChange(class_instance_id=entity_id, change=change)
    og_change = ObjectInstanceGraphChange(
        change=change,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_change],
    )
    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_change],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit,
        schema_graph=schema_graph,
        meta_class_config_id_by_entity_id_post={entity_id: meta_class_config.id},
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    assert delta.node_deltas[0].change_type == ChangeType.update


def test_ocg_delta_from_oig_commit_bubbles_nested_entity_updates_to_owner_node() -> (
    None
):
    ocg_id = uuid4()

    meta_enum_config = _meta_class("EnumConfig")
    meta_enum_option = _meta_class("EnumOption")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_config,
            class_config_id=meta_enum_config.id,
            object_config_graph_id=schema_graph.id,
        ),
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_option,
            class_config_id=meta_enum_option.id,
            object_config_graph_id=schema_graph.id,
        ),
    ]

    owner_enum_config_entity_id = uuid4()
    enum_option_entity_id = uuid4()
    change = _test_change(key="enum_option:update:value", type=ChangeType.update)
    change.change_deltas = [
        _test_delta(
            change=change,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(meta_enum_option.id)),
        ),
    ]
    ci_change = ClassInstanceChange(
        class_instance_id=enum_option_entity_id, change=change
    )
    og_change = ObjectInstanceGraphChange(
        change=change,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_change],
    )
    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_change],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit,
        schema_graph=schema_graph,
        meta_class_config_id_by_entity_id_post={
            enum_option_entity_id: meta_enum_option.id,
            owner_enum_config_entity_id: meta_enum_config.id,
        },
        owner_node_entity_id_by_entity_id_post={
            enum_option_entity_id: owner_enum_config_entity_id
        },
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    node_delta = delta.node_deltas[0]
    assert node_delta.change_type == ChangeType.update
    assert node_delta.node_type == ObjectConfigGraphNodeType.enum
    assert node_delta.entity_id == owner_enum_config_entity_id
    assert node_delta.node_id == stable_object_config_graph_node_id(
        object_config_graph_id=ocg_id,
        type=ObjectConfigGraphNodeType.enum.value,
        node_key=str(owner_enum_config_entity_id),
    )


def test_ocg_delta_from_oig_commit_extracts_payload_from_attribute_changes() -> None:
    ocg_id = uuid4()

    # Schema: meta ClassConfig has a "name" attribute (AttributeConfig id -> field name mapping).
    meta_td = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    meta_class_config = _meta_class("ClassConfig")
    name_attr_cfg = make_attribute_config(
        owner_key=meta_class_config.class_fqn, name="name", type_descriptor=meta_td
    )
    meta_class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=meta_class_config.id,
            attribute_config=name_attr_cfg,
            name=name_attr_cfg.name,
            position=0,
        )
    ]

    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_class_config,
            class_config_id=meta_class_config.id,
            object_config_graph_id=schema_graph.id,
        )
    ]

    entity_id = uuid4()
    ci_change_change = _test_change(key="class_instance:create", type=ChangeType.create)
    ci_change_change.change_deltas = [
        _test_delta(
            change=ci_change_change,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(meta_class_config.id)),
        ),
    ]

    attr_change_change = _test_change(
        key="attribute:create:name", type=ChangeType.create
    )
    attr_change_change.change_deltas = [
        _test_delta(
            change=attr_change_change,
            position=0,
            property="attribute_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(name_attr_cfg.id)),
        ),
    ]
    value_change_change = _test_change(
        key="attribute_value:create:name", type=ChangeType.create
    )
    value_change_change.change_deltas = [
        _test_delta(
            change=value_change_change,
            position=0,
            property="primitive_value",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value="User"),
        ),
    ]

    attr_change = AttributeChange(
        attribute_id=uuid4(),
        class_instance_change_id=uuid4(),
        change=attr_change_change,
        value_root_change=AttributeValueChange(
            attribute_value_id=uuid4(),
            change=value_change_change,
        ),
    )
    ci_change = ClassInstanceChange(
        class_instance_id=entity_id,
        change=ci_change_change,
        attribute_changes=[attr_change],
    )
    og_root = _test_change(key="oig:update:root", type=ChangeType.update)
    og_change = ObjectInstanceGraphChange(
        change=og_root,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_change],
    )

    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_change],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit, schema_graph=schema_graph
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    assert delta.node_deltas[0].payload is not None
    assert delta.node_deltas[0].payload.get("name") == "User"


def test_ocg_delta_from_oig_commit_extracts_enum_values_from_enum_option_id() -> None:
    ocg_id = uuid4()

    # Schema: meta ClassConfig has a "value_mode" attribute whose value is stored as enum_option_id.
    meta_td = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    meta_class_config = _meta_class("ClassConfig")
    value_mode_attr_cfg = make_attribute_config(
        owner_key=meta_class_config.class_fqn,
        name="value_mode",
        type_descriptor=meta_td,
    )
    meta_class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=meta_class_config.id,
            attribute_config=value_mode_attr_cfg,
            name=value_mode_attr_cfg.name,
            position=0,
        )
    ]

    value_mode_enum = _meta_enum("ClassValueMode")
    opt_graph_ref = EnumOption(
        value="graph_ref",
        enum_config_id=value_mode_enum.id,
        position=0,
    )
    value_mode_enum.enum_options = [opt_graph_ref]

    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_class_config,
            class_config_id=meta_class_config.id,
            object_config_graph_id=schema_graph.id,
        ),
        make_ocg_node(
            type=ObjectConfigGraphNodeType.enum,
            enum_config=value_mode_enum,
            enum_config_id=value_mode_enum.id,
            object_config_graph_id=schema_graph.id,
        ),
    ]

    entity_id = uuid4()
    ci_change_change = _test_change(
        key="class_instance:create:value_mode", type=ChangeType.create
    )
    ci_change_change.change_deltas = [
        _test_delta(
            change=ci_change_change,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(meta_class_config.id)),
        ),
    ]

    attr_change_change = _test_change(
        key="attribute:create:value_mode", type=ChangeType.create
    )
    attr_change_change.change_deltas = [
        _test_delta(
            change=attr_change_change,
            position=0,
            property="attribute_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(value_mode_attr_cfg.id)),
        ),
    ]
    value_change_change = _test_change(
        key="attribute_value:create:value_mode", type=ChangeType.create
    )
    value_change_change.change_deltas = [
        _test_delta(
            change=value_change_change,
            position=0,
            property="enum_option_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(opt_graph_ref.id)),
        ),
    ]

    attr_change = AttributeChange(
        attribute_id=uuid4(),
        class_instance_change_id=uuid4(),
        change=attr_change_change,
        value_root_change=AttributeValueChange(
            attribute_value_id=uuid4(),
            change=value_change_change,
        ),
    )
    ci_change = ClassInstanceChange(
        class_instance_id=entity_id,
        change=ci_change_change,
        attribute_changes=[attr_change],
    )
    og_root = _test_change(key="oig:update:enum-root", type=ChangeType.update)
    og_change = ObjectInstanceGraphChange(
        change=og_root,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_change],
    )

    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_change],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit, schema_graph=schema_graph
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    assert delta.node_deltas[0].payload is not None
    assert delta.node_deltas[0].payload.get("value_mode") == "graph_ref"


def test_ocg_delta_from_oig_commit_bubbles_via_relationship_bfs_without_owner_indexes() -> (
    None
):
    ocg_id = uuid4()

    meta_enum_config = _meta_class("EnumConfig")
    meta_enum_option = _meta_class("EnumOption")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_config,
            class_config_id=meta_enum_config.id,
            object_config_graph_id=schema_graph.id,
        ),
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_option,
            class_config_id=meta_enum_option.id,
            object_config_graph_id=schema_graph.id,
        ),
    ]

    enum_entity_id = uuid4()
    option_entity_id = uuid4()

    change_opt = _test_change(key="enum_option:create", type=ChangeType.create)
    change_opt.change_deltas = [
        _test_delta(
            change=change_opt,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(meta_enum_option.id)),
        ),
    ]
    change_enum = _test_change(key="enum:create", type=ChangeType.create)
    change_enum.change_deltas = [
        _test_delta(
            change=change_enum,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(meta_enum_config.id)),
        ),
    ]

    # Order: nested entity first, then owner node. Bubble-up must still find the owner via first-pass indexing.
    ci_option = ClassInstanceChange(
        class_instance_id=option_entity_id, change=change_opt
    )
    ci_enum = ClassInstanceChange(class_instance_id=enum_entity_id, change=change_enum)
    og_root = _test_change(key="oig:update:enum-rel-root", type=ChangeType.update)
    og_instances = ObjectInstanceGraphChange(
        change=og_root,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_option, ci_enum],
    )

    rel_change = ClassInstanceRelationshipChange(
        change=_test_change(key="relationship:create", type=ChangeType.create),
        class_config_relationship_id=uuid4(),
        source_class_instance_id=enum_entity_id,
        target_class_instance_id=option_entity_id,
    )
    og_rels = ObjectInstanceGraphChange(
        change=_test_change(key="relationship:update", type=ChangeType.update),
        type=ObjectInstanceGraphChangeType.object_instance_relationship,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_relationship_changes=[rel_change],
    )

    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_instances, og_rels],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit, schema_graph=schema_graph
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    assert delta.node_deltas[0].entity_id == enum_entity_id
    assert delta.node_deltas[0].node_type == ObjectConfigGraphNodeType.enum


def test_ocg_delta_from_oig_commit_bubbles_nested_delete_to_owner_using_pre_indexes() -> (
    None
):
    ocg_id = uuid4()

    meta_enum_config = _meta_class("EnumConfig")
    meta_enum_option = _meta_class("EnumOption")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_config,
            class_config_id=meta_enum_config.id,
            object_config_graph_id=schema_graph.id,
        ),
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_option,
            class_config_id=meta_enum_option.id,
            object_config_graph_id=schema_graph.id,
        ),
    ]

    owner_enum_entity_id = uuid4()
    option_entity_id = uuid4()

    delete_change = _test_change(key="enum_option:delete", type=ChangeType.delete)
    ci_option = ClassInstanceChange(
        class_instance_id=option_entity_id, change=delete_change
    )
    og_root = _test_change(key="oig:update:delete-root", type=ChangeType.update)
    og_change = ObjectInstanceGraphChange(
        change=og_root,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_option],
    )
    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_change],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit,
        schema_graph=schema_graph,
        meta_class_config_id_by_entity_id_pre={
            owner_enum_entity_id: meta_enum_config.id,
            option_entity_id: meta_enum_option.id,
        },
        owner_node_entity_id_by_entity_id_pre={option_entity_id: owner_enum_entity_id},
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    assert delta.node_deltas[0].change_type == ChangeType.update
    assert delta.node_deltas[0].node_type == ObjectConfigGraphNodeType.enum
    assert delta.node_deltas[0].entity_id == owner_enum_entity_id


def test_ocg_delta_from_oig_commit_emits_node_update_from_relationship_only_commit_when_indexed() -> (
    None
):
    ocg_id = uuid4()

    meta_enum_config = _meta_class("EnumConfig")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_config,
            class_config_id=meta_enum_config.id,
            object_config_graph_id=schema_graph.id,
        ),
    ]

    enum_entity_id = uuid4()
    option_entity_id = uuid4()
    rel_change = ClassInstanceRelationshipChange(
        change=_test_change(key="relationship:create:indexed", type=ChangeType.create),
        class_config_relationship_id=uuid4(),
        source_class_instance_id=enum_entity_id,
        target_class_instance_id=option_entity_id,
    )
    og_rels = ObjectInstanceGraphChange(
        change=_test_change(key="relationship:update:indexed", type=ChangeType.update),
        type=ObjectInstanceGraphChangeType.object_instance_relationship,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_relationship_changes=[rel_change],
    )
    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_rels],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit,
        schema_graph=schema_graph,
        meta_class_config_id_by_entity_id_post={enum_entity_id: meta_enum_config.id},
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    assert delta.node_deltas[0].change_type == ChangeType.update
    assert delta.node_deltas[0].node_type == ObjectConfigGraphNodeType.enum
    assert delta.node_deltas[0].entity_id == enum_entity_id


def test_index_oig_snapshot_can_drive_bubble_up_for_nested_update_without_relationship_changes() -> (
    None
):
    ocg_id = uuid4()

    meta_enum_config = _meta_class("EnumConfig")
    meta_enum_option = _meta_class("EnumOption")
    schema_graph = ObjectConfigGraph(
        name="meta",
        description=None,
        hash="sha256:test:meta",
        fqn_prefix="meta",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[],
    )
    schema_graph.object_config_graph_nodes = [
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_config,
            class_config_id=meta_enum_config.id,
            object_config_graph_id=schema_graph.id,
        ),
        make_ocg_node(
            type=ObjectConfigGraphNodeType.class_,
            class_config=meta_enum_option,
            class_config_id=meta_enum_option.id,
            object_config_graph_id=schema_graph.id,
        ),
    ]

    enum_entity_id = uuid4()
    option_entity_id = uuid4()

    # Post-snapshot includes the relationship, but the commit we translate will not.
    oig_post = ObjectInstanceGraph(
        id=ocg_id,
        key="post",
        name="post",
        description=None,
        hash="sha256:test:oig-post",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=enum_entity_id,
        root_class_instance=ClassInstance(
            id=enum_entity_id,
            object_instance_graph_id=ocg_id,
            class_config_id=meta_enum_config.id,
            source_object_id=enum_entity_id,
        ),
        class_instances=[
            ClassInstance(
                id=enum_entity_id,
                object_instance_graph_id=ocg_id,
                class_config_id=meta_enum_config.id,
                source_object_id=enum_entity_id,
            ),
            ClassInstance(
                id=option_entity_id,
                object_instance_graph_id=ocg_id,
                class_config_id=meta_enum_option.id,
                source_object_id=option_entity_id,
            ),
        ],
        class_instance_relationships=[
            ClassInstanceRelationship(
                id=uuid4(),
                object_instance_graph_id=ocg_id,
                class_config_relationship_id=uuid4(),
                source_class_instance_id=enum_entity_id,
                target_class_instance_id=option_entity_id,
            ),
        ],
    )

    meta_by_entity_id_post, owner_by_entity_id_post = index_oig_snapshot_for_ocg_delta(
        oig=oig_post, schema_graph=schema_graph
    )
    assert owner_by_entity_id_post.get(option_entity_id) == enum_entity_id

    # Commit updates only the nested entity; no relationship changes are present.
    change = _test_change(key="enum_option:update:index-post", type=ChangeType.update)
    change.change_deltas = [
        _test_delta(
            change=change,
            position=0,
            property="class_config_id",
            kind=ChangeDeltaKind.scalar_set,
            payload=JsonObject(value=str(meta_enum_option.id)),
        ),
    ]
    ci_change = ClassInstanceChange(class_instance_id=option_entity_id, change=change)
    og_root = _test_change(key="oig:update:index-post-root", type=ChangeType.update)
    og_change = ObjectInstanceGraphChange(
        change=og_root,
        type=ObjectInstanceGraphChangeType.object_instance,
        object_instance_graph_id=ocg_id,
        object_instance_graph_identity_id=ocg_id,
        class_instance_changes=[ci_change],
    )
    oig_commit = _make_oig_commit(
        object_instance_graph_identity_id=ocg_id,
        object_instance_graph_id=ocg_id,
        object_instance_graph_changes=[og_change],
    )

    delta = build_ocg_delta_from_oig_commit(
        commit=oig_commit,
        schema_graph=schema_graph,
        meta_class_config_id_by_entity_id_post=meta_by_entity_id_post,
        owner_node_entity_id_by_entity_id_post=owner_by_entity_id_post,
    )
    assert not delta.warnings
    assert len(delta.node_deltas) == 1
    assert delta.node_deltas[0].change_type == ChangeType.update
    assert delta.node_deltas[0].node_type == ObjectConfigGraphNodeType.enum
    assert delta.node_deltas[0].entity_id == enum_entity_id
