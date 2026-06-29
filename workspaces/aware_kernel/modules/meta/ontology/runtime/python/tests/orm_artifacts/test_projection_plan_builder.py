# @code-under-test: ../../aware_meta/orm_artifacts/projection_plans.py

from __future__ import annotations

from uuid import uuid4

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_association import (
    ClassConfigRelationshipAssociation,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipType,
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
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)

from aware_meta.orm_artifacts.projection_plans import (
    compile_projection_plan_cache_from_object_config_graph,
)


def _bootstrap_ontology() -> None:
    import aware_meta_ontology as ontology_pkg

    bootstrap = getattr(ontology_pkg, "_bootstrap_models", None)
    if callable(bootstrap):
        bootstrap()


def _primitive_attr(*, name: str) -> AttributeConfig:
    return AttributeConfig(
        name=name,
        owner_key=name,
        type_descriptor=AttributeTypeDescriptor(
            kind=AttributeTypeDescriptorKind.primitive
        ),
    )


def _class_config(*, name: str) -> ClassConfig:
    return ClassConfig(name=name, class_fqn=f"pkg.{name}")


def test_projection_plan_marks_fk_attribute_columns() -> None:
    _bootstrap_ontology()
    ocg_id = uuid4()

    users = _class_config(name="Users")
    profiles = _class_config(name="Profiles")

    profile_id = _primitive_attr(name="profile_id")
    users.class_config_attribute_configs.append(
        ClassConfigAttributeConfig(
            class_config_id=users.id,
            attribute_config=profile_id,
            attribute_config_id=profile_id.id,
            position=0,
        )
    )

    rel = ClassConfigRelationship(
        relationship_key="users_profiles",
        relationship_type=ClassConfigRelationshipType.one_to_one,
        forward_required=True,
        class_config_id=users.id,
        target_class_config_id=profiles.id,
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=profile_id.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    )

    opg = ObjectProjectionGraph(
        language=CodeLanguage.sql,
        name="user_profile",
        projection_hash="sha256:user_profile",
        object_config_graph_id=ocg_id,
    )
    opg.object_projection_graph_nodes.extend(
        [
            ObjectProjectionGraphNode(
                is_root=True,
                object_projection_graph_id=opg.id,
                class_config_id=users.id,
            ),
            ObjectProjectionGraphNode(
                is_root=False,
                object_projection_graph_id=opg.id,
                class_config_id=profiles.id,
            ),
        ]
    )
    opg.object_projection_graph_edges.append(
        ObjectProjectionGraphEdge(
            object_projection_graph_id=opg.id,
            class_config_relationship_id=rel.id,
        )
    )

    graph = ObjectConfigGraph(
        id=ocg_id,
        name="g",
        description="g",
        hash="sha256:test",
        fqn_prefix="pkg",
        language=CodeLanguage.sql,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                node_key="class:Users",
                type=ObjectConfigGraphNodeType.class_,
                object_config_graph_id=ocg_id,
                class_config=users,
                class_config_id=users.id,
            ),
            ObjectConfigGraphNode(
                node_key="class:Profiles",
                type=ObjectConfigGraphNodeType.class_,
                object_config_graph_id=ocg_id,
                class_config=profiles,
                class_config_id=profiles.id,
            ),
            ObjectConfigGraphNode(
                node_key="relationship:users_profiles",
                type=ObjectConfigGraphNodeType.relationship,
                object_config_graph_id=ocg_id,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
            ),
        ],
        object_projection_graphs=[opg],
    )

    cache = compile_projection_plan_cache_from_object_config_graph(
        graph, dialect="sqlite"
    )
    plan = cache.require(dialect="sqlite", projection_hash=opg.projection_hash)

    users_table = next(t for t in plan.tables if t.table_key == "default.users")
    profile_col = next(c for c in users_table.columns if c.column_name == "profile_id")
    assert profile_col.source == "fk_attribute"
    assert profile_col.relationship_id == rel.id
    assert profile_col.direction == "forward"


def test_projection_plan_marks_soft_fk_columns_as_attribute() -> None:
    _bootstrap_ontology()
    ocg_id = uuid4()

    users = _class_config(name="Users")
    profiles = _class_config(name="Profiles")

    profile_id = _primitive_attr(name="profile_id")
    users.class_config_attribute_configs.append(
        ClassConfigAttributeConfig(
            class_config_id=users.id,
            attribute_config=profile_id,
            attribute_config_id=profile_id.id,
            position=0,
        )
    )

    rel = ClassConfigRelationship(
        relationship_key="users_profiles",
        relationship_type=ClassConfigRelationshipType.one_to_one,
        forward_required=True,
        class_config_id=users.id,
        target_class_config_id=profiles.id,
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=profile_id.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    )

    opg = ObjectProjectionGraph(
        language=CodeLanguage.sql,
        name="user_profile_softref",
        projection_hash="sha256:user_profile_softref",
        object_config_graph_id=ocg_id,
    )
    opg.object_projection_graph_nodes.extend(
        [
            ObjectProjectionGraphNode(
                is_root=True,
                object_projection_graph_id=opg.id,
                class_config_id=users.id,
            ),
            ObjectProjectionGraphNode(
                is_root=False,
                object_projection_graph_id=opg.id,
                class_config_id=profiles.id,
            ),
        ]
    )

    graph = ObjectConfigGraph(
        id=ocg_id,
        name="g",
        description="g",
        hash="sha256:test",
        fqn_prefix="pkg",
        language=CodeLanguage.sql,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                node_key="class:Users",
                type=ObjectConfigGraphNodeType.class_,
                object_config_graph_id=ocg_id,
                class_config=users,
                class_config_id=users.id,
            ),
            ObjectConfigGraphNode(
                node_key="class:Profiles",
                type=ObjectConfigGraphNodeType.class_,
                object_config_graph_id=ocg_id,
                class_config=profiles,
                class_config_id=profiles.id,
            ),
            ObjectConfigGraphNode(
                node_key="relationship:users_profiles",
                type=ObjectConfigGraphNodeType.relationship,
                object_config_graph_id=ocg_id,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
            ),
        ],
        object_projection_graphs=[opg],
    )

    cache = compile_projection_plan_cache_from_object_config_graph(
        graph, dialect="sqlite"
    )
    plan = cache.require(dialect="sqlite", projection_hash=opg.projection_hash)

    users_table = next(t for t in plan.tables if t.table_key == "default.users")
    profile_col = next(c for c in users_table.columns if c.column_name == "profile_id")
    assert profile_col.source == "attribute"


def test_projection_plan_emits_association_mapping() -> None:
    _bootstrap_ontology()
    ocg_id = uuid4()

    left = _class_config(name="Left")
    right = _class_config(name="Right")
    join = _class_config(name="LeftRightJoin")

    left_id = _primitive_attr(name="left_id")
    right_id = _primitive_attr(name="right_id")
    join.class_config_attribute_configs.extend(
        [
            ClassConfigAttributeConfig(
                class_config_id=join.id,
                attribute_config=left_id,
                attribute_config_id=left_id.id,
                position=0,
            ),
            ClassConfigAttributeConfig(
                class_config_id=join.id,
                attribute_config=right_id,
                attribute_config_id=right_id.id,
                position=1,
            ),
        ]
    )

    rel = ClassConfigRelationship(
        relationship_key="left_right",
        relationship_type=ClassConfigRelationshipType.many_to_many,
        forward_required=True,
        class_config_id=left.id,
        target_class_config_id=right.id,
    )
    rel.class_config_relationship_association_edge = ClassConfigRelationshipAssociation(
        class_config_id=join.id,
        class_config_relationship_id=rel.id,
    )
    rel.class_config_relationship_attributes.extend(
        [
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=left_id.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=right_id.id,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
        ]
    )

    opg = ObjectProjectionGraph(
        language=CodeLanguage.sql,
        name="lr",
        projection_hash="sha256:lr",
        object_config_graph_id=ocg_id,
    )
    opg.object_projection_graph_nodes.extend(
        [
            ObjectProjectionGraphNode(
                is_root=True,
                object_projection_graph_id=opg.id,
                class_config_id=left.id,
            ),
            ObjectProjectionGraphNode(
                is_root=False,
                object_projection_graph_id=opg.id,
                class_config_id=right.id,
            ),
        ]
    )

    graph = ObjectConfigGraph(
        id=ocg_id,
        name="g",
        description="g",
        hash="sha256:test",
        fqn_prefix="pkg",
        language=CodeLanguage.sql,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                node_key="class:Left",
                type=ObjectConfigGraphNodeType.class_,
                object_config_graph_id=ocg_id,
                class_config=left,
                class_config_id=left.id,
            ),
            ObjectConfigGraphNode(
                node_key="class:Right",
                type=ObjectConfigGraphNodeType.class_,
                object_config_graph_id=ocg_id,
                class_config=right,
                class_config_id=right.id,
            ),
            ObjectConfigGraphNode(
                node_key="class:LeftRightJoin",
                type=ObjectConfigGraphNodeType.class_,
                object_config_graph_id=ocg_id,
                class_config=join,
                class_config_id=join.id,
            ),
            ObjectConfigGraphNode(
                node_key="relationship:left_right",
                type=ObjectConfigGraphNodeType.relationship,
                object_config_graph_id=ocg_id,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
            ),
        ],
        object_projection_graphs=[opg],
    )

    cache = compile_projection_plan_cache_from_object_config_graph(
        graph, dialect="sqlite"
    )
    plan = cache.require(dialect="sqlite", projection_hash=opg.projection_hash)
    assert len(plan.associations) == 1

    assoc = plan.associations[0]
    assert assoc.association_table_key == "default.left_right_join"
    assert assoc.relationship_id == rel.id
    assert assoc.source_fk_column == "left_id"
    assert assoc.target_fk_column == "right_id"
