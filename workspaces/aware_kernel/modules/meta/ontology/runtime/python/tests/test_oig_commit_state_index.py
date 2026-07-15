from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.class_.class_instance_change import ClassInstanceChange
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateRow,
    CommitStateIndex,
    apply_commit_state_index_changes,
    apply_commit_state_index_row_changes,
    build_commit_state_index,
)
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def test_commit_state_index_hash_matches_full_oig_hash_for_nodes_attrs_edges() -> None:
    user_fqn = test_class_fqn("CommitStateUser")
    org_fqn = test_class_fqn("CommitStateOrg")
    name_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    title_cfg = make_attribute_config(
        owner_key=org_fqn,
        name="title",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = make_class_config(
        "CommitStateUser",
        class_fqn=user_fqn,
        class_config_attribute_configs=[],
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        )
    ]
    org_cc = make_class_config(
        "CommitStateOrg",
        class_fqn=org_fqn,
        class_config_attribute_configs=[],
    )
    org_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=org_cc.id,
            attribute_config=title_cfg,
            name=title_cfg.name,
            position=0,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    class Org(BaseORMModel):
        title: str

    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()
    org_id: UUID = uuid4()
    user_ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="Ada"),
    )
    org_ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=org_cc,
        source=Org(id=org_id, title="Lab"),
    )
    relationship_id = uuid4()
    graph = build_object_instance_graph_from_class_instances(
        name="state",
        description="state",
        object_config_graph_id=uuid4(),
        object_projection_graph_id=uuid4(),
        root_class_instance=user_ci,
        class_instances=[org_ci, user_ci],
        class_instance_relationships=[
            ClassInstanceRelationship(
                object_instance_graph_id=graph_id,
                class_config_relationship_id=relationship_id,
                source_class_instance_id=user_ci.id,
                target_class_instance_id=org_ci.id,
            )
        ],
        oig_id=graph_id,
    )

    state_index = build_commit_state_index(graph)

    assert state_index.compute_hash() == compute_hash(graph, index=build_index(graph))
    assert state_index.node_count == 2
    assert state_index.attribute_count == 2
    assert state_index.edge_count == 1
    assert CommitStateRow("NODE", str(user_cc.id), str(user_ci.id)) in state_index.rows
    assert (
        CommitStateRow(
            "EDGE",
            str(relationship_id),
            f"{user_ci.id}->{org_ci.id}",
        )
        in state_index.rows
    )


def test_commit_state_index_row_maps_group_nodes_attrs_and_edges() -> None:
    class_config_id = uuid4()
    class_instance_id = uuid4()
    attribute_config_id = uuid4()
    relationship_id = uuid4()
    target_class_instance_id = uuid4()
    rows = (
        CommitStateRow("NODE", str(class_config_id), str(class_instance_id)),
        CommitStateRow(
            "ATTR",
            str(class_instance_id),
            f"{attribute_config_id}:hash:value",
        ),
        CommitStateRow(
            "EDGE",
            str(relationship_id),
            f"{class_instance_id}->{target_class_instance_id}",
        ),
    )

    row_maps = CommitStateIndex(rows=rows).row_maps()

    assert row_maps.class_config_ids_by_class_instance_id == {
        class_instance_id: class_config_id,
    }
    assert row_maps.class_state_rows_by_id == {
        class_instance_id: rows[:2],
    }
    assert row_maps.class_state_rows_by_raw_id == {
        str(class_instance_id): rows[:2],
    }
    assert row_maps.relationship_keys == frozenset(
        {
            (
                relationship_id,
                class_instance_id,
                target_class_instance_id,
            ),
        }
    )
    assert (
        CommitStateIndex(rows=rows)
        .row_maps(
            include_relationship_keys=False,
        )
        .relationship_keys
        == frozenset()
    )


def test_commit_state_index_row_maps_reject_conflicting_node_rows() -> None:
    class_instance_id = uuid4()
    rows = (
        CommitStateRow("NODE", str(uuid4()), str(class_instance_id)),
        CommitStateRow("NODE", str(uuid4()), str(class_instance_id)),
    )

    with pytest.raises(ValueError, match="conflicting NODE rows"):
        _ = CommitStateIndex(rows=rows).row_maps()


def test_commit_state_index_row_changes_apply_without_post_class_instances() -> None:
    graph_id = uuid4()
    oigi_id = uuid4()
    class_config_id = uuid4()
    class_instance_id = uuid4()
    attribute_config_id = uuid4()
    relationship_id = uuid4()
    target_class_instance_id = uuid4()
    pre_index = CommitStateIndex(
        rows=(
            CommitStateRow("NODE", str(class_config_id), str(class_instance_id)),
            CommitStateRow(
                "ATTR",
                str(class_instance_id),
                f"{attribute_config_id}:old",
            ),
            CommitStateRow(
                "EDGE",
                str(relationship_id),
                f"{class_instance_id}->{target_class_instance_id}",
            ),
        )
    )
    post_rows = (
        CommitStateRow("NODE", str(class_config_id), str(class_instance_id)),
        CommitStateRow(
            "ATTR",
            str(class_instance_id),
            f"{attribute_config_id}:new",
        ),
    )
    replacement_target_id = uuid4()
    new_relationship_id = uuid4()
    changes = (
        _class_instance_oig_change(
            graph_id=graph_id,
            oigi_id=oigi_id,
            class_instance_id=class_instance_id,
            change_type=ChangeType.update,
        ),
        _relationship_oig_change(
            graph_id=graph_id,
            oigi_id=oigi_id,
            relationship_id=relationship_id,
            source_class_instance_id=class_instance_id,
            target_class_instance_id=target_class_instance_id,
            change_type=ChangeType.delete,
        ),
        _relationship_oig_change(
            graph_id=graph_id,
            oigi_id=oigi_id,
            relationship_id=new_relationship_id,
            source_class_instance_id=class_instance_id,
            target_class_instance_id=replacement_target_id,
            change_type=ChangeType.create,
        ),
    )

    post_index = apply_commit_state_index_row_changes(
        pre_state_index=pre_index,
        changes=changes,
        post_class_state_rows_by_id={class_instance_id: post_rows},
    )

    assert post_index.rows == (
        CommitStateRow("NODE", str(class_config_id), str(class_instance_id)),
        CommitStateRow(
            "ATTR",
            str(class_instance_id),
            f"{attribute_config_id}:new",
        ),
        CommitStateRow(
            "EDGE",
            str(new_relationship_id),
            f"{class_instance_id}->{replacement_target_id}",
        ),
    )


def test_commit_state_index_row_changes_reject_mismatched_post_rows() -> None:
    class_instance_id = uuid4()
    other_class_instance_id = uuid4()

    with pytest.raises(ValueError, match="unexpected state member"):
        apply_commit_state_index_row_changes(
            pre_state_index=CommitStateIndex(rows=()),
            changes=(
                _class_instance_oig_change(
                    graph_id=uuid4(),
                    oigi_id=uuid4(),
                    class_instance_id=class_instance_id,
                    change_type=ChangeType.create,
                ),
            ),
            post_class_state_rows_by_id={
                class_instance_id: (
                    CommitStateRow("NODE", str(uuid4()), str(class_instance_id)),
                    CommitStateRow(
                        "ATTR",
                        str(other_class_instance_id),
                        f"{uuid4()}:value",
                    ),
                ),
            },
        )


def test_commit_state_index_deduplicates_like_full_oig_hash() -> None:
    user_fqn = test_class_fqn("CommitStateDuplicateUser")
    name_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = make_class_config(
        "CommitStateDuplicateUser",
        class_fqn=user_fqn,
        class_config_attribute_configs=[],
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

    graph_id: UUID = uuid4()
    user_ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=uuid4(), name="Ada"),
    )
    user_ci.attributes.append(user_ci.attributes[0].model_copy(deep=True))
    relationship = ClassInstanceRelationship(
        object_instance_graph_id=graph_id,
        class_config_relationship_id=uuid4(),
        source_class_instance_id=user_ci.id,
        target_class_instance_id=user_ci.id,
    )
    graph = build_object_instance_graph_from_class_instances(
        name="state",
        description="state",
        object_config_graph_id=uuid4(),
        object_projection_graph_id=uuid4(),
        root_class_instance=user_ci,
        class_instances=[user_ci],
        class_instance_relationships=[relationship, relationship.model_copy(deep=True)],
        oig_id=graph_id,
    )

    state_index = build_commit_state_index(graph)

    assert state_index.compute_hash() == compute_hash(graph, index=build_index(graph))
    assert state_index.node_count == 1
    assert state_index.attribute_count == 1
    assert state_index.edge_count == 1


def _change(*, key: str, change_type: ChangeType) -> Change:
    from datetime import UTC, datetime

    return Change(
        key=key,
        change_deltas=[],
        type=change_type,
        created_at=datetime.now(UTC),
    )


def _class_instance_oig_change(
    *,
    graph_id: UUID,
    oigi_id: UUID,
    class_instance_id: UUID,
    change_type: ChangeType,
) -> ObjectInstanceGraphChange:
    change = _change(
        key=f"class_instance:{class_instance_id}:{change_type.value}",
        change_type=change_type,
    )
    return ObjectInstanceGraphChange(
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=graph_id,
        type=ObjectInstanceGraphChangeType.object_instance,
        change=change,
        change_id=change.id,
        class_instance_changes=[
            ClassInstanceChange(
                change=change,
                change_id=change.id,
                class_instance_id=class_instance_id,
                attribute_changes=[],
            )
        ],
        class_instance_relationship_changes=[],
    )


def _relationship_oig_change(
    *,
    graph_id: UUID,
    oigi_id: UUID,
    relationship_id: UUID,
    source_class_instance_id: UUID,
    target_class_instance_id: UUID,
    change_type: ChangeType,
) -> ObjectInstanceGraphChange:
    change = _change(
        key=(
            f"relationship:{relationship_id}:"
            f"{source_class_instance_id}->{target_class_instance_id}:"
            f"{change_type.value}"
        ),
        change_type=change_type,
    )
    return ObjectInstanceGraphChange(
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=graph_id,
        type=ObjectInstanceGraphChangeType.object_instance_relationship,
        change=change,
        change_id=change.id,
        class_instance_changes=[],
        class_instance_relationship_changes=[
            ClassInstanceRelationshipChange(
                change=change,
                change_id=change.id,
                class_config_relationship_id=relationship_id,
                source_class_instance_id=source_class_instance_id,
                target_class_instance_id=target_class_instance_id,
            )
        ],
    )


def test_commit_state_index_applies_oig_changes_with_full_hash_parity() -> None:
    user_fqn = test_class_fqn("CommitStateDeltaUser")
    org_fqn = test_class_fqn("CommitStateDeltaOrg")
    project_fqn = test_class_fqn("CommitStateDeltaProject")
    name_cfg = make_attribute_config(
        owner_key=user_fqn,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    title_cfg = make_attribute_config(
        owner_key=org_fqn,
        name="title",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    project_name_cfg = make_attribute_config(
        owner_key=project_fqn,
        name="project_name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    user_cc = make_class_config(
        "CommitStateDeltaUser",
        class_fqn=user_fqn,
        class_config_attribute_configs=[],
    )
    user_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=user_cc.id,
            attribute_config=name_cfg,
            name=name_cfg.name,
            position=0,
        )
    ]
    org_cc = make_class_config(
        "CommitStateDeltaOrg",
        class_fqn=org_fqn,
        class_config_attribute_configs=[],
    )
    org_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=org_cc.id,
            attribute_config=title_cfg,
            name=title_cfg.name,
            position=0,
        )
    ]
    project_cc = make_class_config(
        "CommitStateDeltaProject",
        class_fqn=project_fqn,
        class_config_attribute_configs=[],
    )
    project_cc.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=project_cc.id,
            attribute_config=project_name_cfg,
            name=project_name_cfg.name,
            position=0,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    class Org(BaseORMModel):
        title: str

    class Project(BaseORMModel):
        project_name: str

    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()
    org_id: UUID = uuid4()
    project_id: UUID = uuid4()
    pre_user_ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="Ada"),
    )
    post_user_ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="Grace"),
    )
    org_ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=org_cc,
        source=Org(id=org_id, title="Lab"),
    )
    project_ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=project_cc,
        source=Project(id=project_id, project_name="Compiler"),
    )
    relationship_id = uuid4()
    object_config_graph_id = uuid4()
    object_projection_graph_id = uuid4()
    pre_relationship = ClassInstanceRelationship(
        object_instance_graph_id=graph_id,
        class_config_relationship_id=relationship_id,
        source_class_instance_id=pre_user_ci.id,
        target_class_instance_id=org_ci.id,
    )
    post_relationship = ClassInstanceRelationship(
        object_instance_graph_id=graph_id,
        class_config_relationship_id=relationship_id,
        source_class_instance_id=post_user_ci.id,
        target_class_instance_id=project_ci.id,
    )
    pre_graph = build_object_instance_graph_from_class_instances(
        name="state",
        description="state",
        object_config_graph_id=object_config_graph_id,
        object_projection_graph_id=object_projection_graph_id,
        root_class_instance=pre_user_ci,
        class_instances=[org_ci, pre_user_ci],
        class_instance_relationships=[pre_relationship],
        oig_id=graph_id,
    )
    post_graph = build_object_instance_graph_from_class_instances(
        name="state",
        description="state",
        object_config_graph_id=object_config_graph_id,
        object_projection_graph_id=object_projection_graph_id,
        root_class_instance=post_user_ci,
        class_instances=[org_ci, project_ci, post_user_ci],
        class_instance_relationships=[post_relationship],
        oig_id=graph_id,
    )
    changes = diff_object_instance_graph_changes(
        old=pre_graph,
        new=post_graph,
        object_instance_graph_identity_id=uuid4(),
    )
    applied = apply_commit_state_index_changes(
        pre_state_index=build_commit_state_index(pre_graph),
        changes=changes,
        post_class_instances_by_id={
            class_instance.id: class_instance
            for class_instance in post_graph.class_instances
        },
    )

    assert applied.compute_hash() == build_commit_state_index(post_graph).compute_hash()
    assert applied.compute_hash() == compute_hash(
        post_graph, index=build_index(post_graph)
    )
