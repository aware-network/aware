from __future__ import annotations

from uuid import UUID, uuid4

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateRow,
    apply_commit_state_index_changes,
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
