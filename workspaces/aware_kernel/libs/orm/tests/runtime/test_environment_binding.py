from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from uuid import uuid4

# Kernel Graph Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)

# ORM
from aware_orm.models.orm_model import ORMModel
from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.bundle_binding import install_bindings_from_bundle
from aware_meta.orm_artifacts.binding import (
    dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph,
)


def _build_graph() -> ObjectConfigGraph:
    # Ensure ontology models are rebuilt so forward refs (e.g. ClassConfigChange) are resolved.
    import aware_meta_ontology as ontology_pkg

    bootstrap = getattr(ontology_pkg, "_bootstrap_models", None)
    if callable(bootstrap):
        bootstrap()

    ocg_id = uuid4()
    user = ClassConfig(name="User", class_fqn="pkg.User")
    node = ObjectConfigGraphNode(
        type=ObjectConfigGraphNodeType.class_,
        node_key=user.class_fqn,
        class_config=user,
        object_config_graph_id=ocg_id,
        class_config_id=user.id,
    )
    return ObjectConfigGraph(
        id=ocg_id,
        name="g",
        description="g",
        hash="sha256:test",
        fqn_prefix="pkg",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[node],
    )


@pytest.mark.parametrize(
    "identity_key",
    ("canonical_entity_id", "canonical_class_config_id"),
)
def test_install_bindings_from_bundle_binds_canonical_class_config(
    tmp_path: Path,
    identity_key: str,
) -> None:
    graph = _build_graph()
    user_cls = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config and n.class_config.name == "User"
    )
    assert user_cls is not None and user_cls.id is not None

    class UserModel(ORMModel):
        name: str

    fqn = f"{UserModel.__module__}.{UserModel.__name__}"
    ORMModelRegistry.register_class_stub(UserModel)

    bindings = {
        "version": "1.0.0",
        "planner_version": "test",
        "bindings": [
            {
                "class_fqn": fqn,
                identity_key: str(user_cls.id),
                "sql_mapping": [],
            }
        ],
    }

    bundle = SimpleNamespace(
        orm_graph_binding_snapshot_bytes=(
            dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
                object_config_graph=graph
            )
        ),
        bindings=json.dumps(bindings).encode("utf-8"),
    )

    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(UserModel)
        res = install_bindings_from_bundle(bundle, strict=True)
        assert res.bound_count == 1
        cc = UserModel.get_class_config()
        assert cc is not None
        assert str(cc.id) == str(user_cls.id)


def test_install_bindings_from_bundle_uses_orm_graph_artifact_metadata(
    tmp_path: Path,
) -> None:
    graph = _build_graph()
    user_cls = next(
        n.class_config
        for n in graph.object_config_graph_nodes
        if n.class_config and n.class_config.name == "User"
    )
    assert user_cls is not None and user_cls.id is not None

    class UserModel(ORMModel):
        name: str

    fqn = f"{UserModel.__module__}.{UserModel.__name__}"
    rich_user_cls = user_cls.model_copy(deep=True)
    reference_attribute = AttributeConfig.model_construct(
        id=uuid4(),
        owner_key="pkg.User",
        name="best_friend",
    )
    rich_user_cls.class_config_attribute_configs = [
        ClassConfigAttributeConfig(
            class_config_id=rich_user_cls.id,
            attribute_config=reference_attribute,
            attribute_config_id=reference_attribute.id,
            name=reference_attribute.name,
            position=0,
        )
    ]
    relationship = ClassConfigRelationship.model_construct(
        id=uuid4(),
        class_config_id=rich_user_cls.id,
        target_class_config_id=rich_user_cls.id,
        relationship_key="best_friend",
        class_config_relationship_attributes=[],
    )
    relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=relationship.id,
            attribute_config_id=reference_attribute.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    rich_user_cls.class_config_relationships = [relationship]
    rich_graph = graph.model_copy(deep=True)
    for node in rich_graph.object_config_graph_nodes:
        if node.class_config and node.class_config.id == rich_user_cls.id:
            node.class_config = rich_user_cls
            break

    bindings = {
        "version": "1.0.0",
        "planner_version": "test",
        "bindings": [
            {
                "class_fqn": fqn,
                "canonical_entity_id": str(user_cls.id),
                "sql_mapping": [],
            }
        ],
    }
    bundle = SimpleNamespace(
        orm_graph_binding_snapshot_bytes=dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
            object_config_graph=rich_graph
        ),
        bindings=json.dumps(bindings).encode("utf-8"),
    )

    with ORMModelRegistry.temporary_clear():
        ORMModelRegistry.register_class_stub(UserModel)
        res = install_bindings_from_bundle(bundle, strict=True)

    assert res.bound_count == 1
    rebound = UserModel.get_class_config()
    assert rebound is not None
    assert {
        link.attribute_config_id for link in rebound.class_config_attribute_configs
    } == {reference_attribute.id}
    assert {rel.id for rel in rebound.class_config_relationships} == {relationship.id}
