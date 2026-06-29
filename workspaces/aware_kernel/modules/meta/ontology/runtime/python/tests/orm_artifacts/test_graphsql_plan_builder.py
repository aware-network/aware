# @code-under-test: ../../aware_meta/orm_artifacts/graphsql.py

from __future__ import annotations

from uuid import UUID, uuid4

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

from aware_meta.orm_artifacts.graphsql import (
    build_relationship_descriptors,
    compile_plan_cache_from_object_config_graph,
    get_graph_config_registry,
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


def _build_minimal_sql_ocg() -> tuple[ObjectConfigGraph, UUID]:
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

    name_attr = _primitive_attr(name="name")
    profiles.class_config_attribute_configs.append(
        ClassConfigAttributeConfig(
            class_config_id=profiles.id,
            attribute_config=name_attr,
            attribute_config_id=name_attr.id,
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

    nodes = [
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
    ]

    graph = ObjectConfigGraph(
        id=ocg_id,
        name="g",
        description="g",
        hash="sha256:test",
        fqn_prefix="pkg",
        language=CodeLanguage.sql,
        object_config_graph_nodes=nodes,
    )
    return graph, rel.id


def test_build_relationship_descriptors_emits_join_condition() -> None:
    graph, _rel_id = _build_minimal_sql_ocg()
    registry = get_graph_config_registry(graph)

    descriptors = build_relationship_descriptors(graph, registry)
    assert len(descriptors) == 1
    desc = descriptors[0]
    assert desc.source_table_key == "default.users"
    assert desc.target_table_key == "default.profiles"
    assert desc.join_condition == "default.users.profile_id = default.profiles.id"
    assert desc.uses_collection is False


def test_compile_plan_cache_from_object_config_graph_compiles_plan() -> None:
    graph, rel_id = _build_minimal_sql_ocg()
    cache = compile_plan_cache_from_object_config_graph(graph)

    plan = cache.require("default.users")
    assert len(plan.steps) == 1

    step = plan.steps[0]
    assert step.table_key == "default.profiles"
    assert step.via_relationship_id == rel_id
    assert step.join_condition == "default.users.profile_id = default.profiles.id"
    assert "id" in plan.root_projection_fields
    assert "profile_id" in plan.root_projection_fields


def test_compile_plan_cache_includes_tables_without_relationships() -> None:
    graph, _rel_id = _build_minimal_sql_ocg()
    cache = compile_plan_cache_from_object_config_graph(graph)

    plan = cache.require("default.profiles")
    assert plan.steps == ()
