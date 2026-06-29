from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.diff import (
    DeltaOp,
    _class_instance_seed_change,
    build_object_instance_graph_seed_changes,
    diff_object_instance_graph,
)
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def test_class_instance_seed_change_dedupes_equivalent_attributes() -> None:
    user_fqn = test_class_fqn("User")
    name_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = make_class_config(
        "User", class_fqn=user_fqn, class_config_attribute_configs=[]
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    ci = build_class_instance(
        object_instance_graph_id=uuid4(),
        class_config=user_cc,
        source=User(id=uuid4(), name="Ada"),
    )
    ci.attributes.append(ci.attributes[0].model_copy(deep=True))

    change = _class_instance_seed_change(
        class_instance=ci,
        operation=ChangeType.create,
        created_at=datetime.now(timezone.utc),
    )

    assert len(change.attribute_changes) == 1
    assert change.attribute_changes[0].attribute_id == ci.attributes[0].id


def test_seed_changes_with_before_update_existing_attribute_value() -> None:
    user_fqn = test_class_fqn("User")
    name_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = make_class_config(
        "User", class_fqn=user_fqn, class_config_attribute_configs=[]
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    user_id = uuid4()
    graph_id = uuid4()
    ocg_id = uuid4()
    opg_id = uuid4()
    oigi_id = uuid4()

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="before"),
    )
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="after"),
    )
    before = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    after = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci2,
        class_instances=[ci2],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = build_object_instance_graph_seed_changes(
        before=before,
        new=after,
        object_instance_graph_identity_id=oigi_id,
    )
    attr_change = changes[0].class_instance_changes[0].attribute_changes[0]

    assert attr_change.change.type == ChangeType.update

    candidate = before.model_copy(deep=True)
    apply_object_instance_graph_changes(
        graph=candidate,
        changes=changes,
        attribute_configs_by_id={name_cfg.id: name_cfg},
        class_configs_by_id={user_cc.id: user_cc},
    )

    assert compute_hash(candidate, index=build_index(candidate)) == compute_hash(
        after,
        index=build_index(after),
    )


def test_oig_diff_updates_correct_attribute_value() -> None:
    """
    Regression: when a class has multiple primitive attributes, value-tree nodes must
    reconcile by full path (attribute-local) so the diff reports the correct old/new.
    """
    user_fqn = test_class_fqn("User")
    # Config: User(first: str, last: str)
    first_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="first",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    last_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="last",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )

    user_cc = make_class_config(
        "User", class_fqn=user_fqn, class_config_attribute_configs=[]
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=first_cfg,
            name=first_cfg.name,
            position=0,
        ),
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=last_cfg,
            name=last_cfg.name,
            position=1,
        ),
    ]

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        first: str
        last: str

    user_id: UUID = uuid4()
    graph_id: UUID = uuid4()
    ocg_id: UUID = uuid4()
    opg_id: UUID = uuid4()
    u1 = User(id=user_id, first="a", last="b")
    u2 = User(id=user_id, first="a2", last="b")

    ci1 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u1
    )
    ci2 = build_class_instance(
        object_instance_graph_id=graph_id, class_config=user_cc, source=u2
    )

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
        oig_id=g1.id,
    )

    changes = diff_object_instance_graph(g1, g2)
    assert len(changes) == 1
    root = changes[0]
    assert root.kind == ObjectInstanceGraphMemberKind.class_instance
    assert root.operation == ChangeType.update

    attrs = root.child_deltas.get(ObjectInstanceGraphMemberKind.attribute, [])
    assert len(attrs) == 1
    attr_delta = attrs[0]
    assert attr_delta.path_key == f"attr:{first_cfg.id}"

    values = attr_delta.child_deltas.get(
        ObjectInstanceGraphMemberKind.attribute_value, []
    )
    assert len(values) == 1
    value_delta = values[0]
    assert value_delta.operation == ChangeType.update

    assert any(
        fd.property == "primitive_value" and fd.op == DeltaOp.SET and fd.value == "a2"
        for fd in value_delta.field_deltas
    )


def test_oig_diff_changes_do_not_turn_identity_fields_into_updates() -> None:
    """
    ClassInstance identity/provenance fields are constructor/create evidence.

    Runtime handler updates can rebuild a full OIG snapshot from ORM models. The
    diff-to-change conversion must keep unchanged class instances out of the
    commit payload and must not inject class_config_id/source_object_id into
    UPDATE changes for the changed target.
    """
    user_fqn = test_class_fqn("User")
    name_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = make_class_config(
        "User", class_fqn=user_fqn, class_config_attribute_configs=[]
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    changed_id: UUID = uuid4()
    unchanged_id: UUID = uuid4()
    graph_id: UUID = uuid4()
    ocg_id: UUID = uuid4()
    opg_id: UUID = uuid4()
    oigi_id: UUID = uuid4()

    before_changed = User(id=changed_id, name="before")
    before_unchanged = User(id=unchanged_id, name="same")
    after_changed = User(id=changed_id, name="after")
    after_unchanged = User(id=unchanged_id, name="same")

    ci_before_changed = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=before_changed,
    )
    ci_before_unchanged = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=before_unchanged,
    )
    ci_after_changed = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=after_changed,
    )
    ci_after_unchanged = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=after_unchanged,
    )

    before = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_before_changed,
        class_instances=[ci_before_changed, ci_before_unchanged],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    after = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg_id,
        object_projection_graph_id=opg_id,
        root_class_instance=ci_after_changed,
        class_instances=[ci_after_changed, ci_after_unchanged],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    changes = diff_object_instance_graph_changes(
        old=before,
        new=after,
        object_instance_graph_identity_id=oigi_id,
    )

    class_changes = [
        ci_change
        for root_change in changes
        for ci_change in root_change.class_instance_changes
    ]
    assert [ci_change.class_instance_id for ci_change in class_changes] == [
        ci_after_changed.id
    ]
    updated_properties = {
        delta.property
        for delta in class_changes[0].change.change_deltas
        if delta.property is not None
    }
    assert "class_config_id" not in updated_properties
    assert "source_object_id" not in updated_properties
    assert class_changes[0].attribute_changes
