from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.handlers.impl.config import (
    object_config_graph as object_config_graph_handler,
)
from aware_meta.handlers.impl.projection import (
    object_projection_graph as object_projection_graph_handler,
)
from aware_meta.handlers.impl.projection import (
    object_projection_graph_constructor as object_projection_graph_constructor_handler,
)
from aware_meta.handlers.impl.projection import (
    object_projection_graph_edge as object_projection_graph_edge_handler,
)
from aware_meta.handlers.impl.projection import (
    object_projection_graph_node as object_projection_graph_node_handler,
)
from aware_meta.handlers.impl.projection import (
    object_projection_graph_node_key as object_projection_graph_node_key_handler,
)
from aware_meta.handlers.impl.projection import (
    object_projection_graph_relationship as object_projection_graph_relationship_handler,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.graph.config.object_config_graph_binding_class import (
    ObjectConfigGraphBindingClass,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.stable_ids import (
    stable_object_projection_graph_constructor_id,
    stable_object_projection_graph_edge_id,
    stable_object_projection_graph_id,
    stable_object_projection_graph_node_id,
    stable_object_projection_graph_node_key_id,
    stable_object_projection_graph_relationship_id,
)


class _Session:
    def __init__(self) -> None:
        self._rows: dict[tuple[type, UUID], object] = {}

    def put(self, value: object) -> None:
        value_id = getattr(value, "id", None)
        if value_id is not None:
            self._rows[(type(value), UUID(str(value_id)))] = value

    def imap_get(self, cls: type, value_id: UUID):
        return self._rows.get((cls, UUID(str(value_id))))


def _make_ocg(graph_id: UUID, *, fqn_prefix: str) -> ObjectConfigGraph:
    return ObjectConfigGraph(
        id=graph_id,
        name=fqn_prefix,
        hash=f"{fqn_prefix}-hash",
        fqn_prefix=fqn_prefix,
        language=CodeLanguage.aware,
    )


def _make_opg(
    opg_id: UUID, *, object_config_graph_id: UUID, name: str
) -> ObjectProjectionGraph:
    return ObjectProjectionGraph(
        id=opg_id,
        object_config_graph_id=object_config_graph_id,
        name=name,
        projection_hash=f"{name}-projection-hash",
        language=CodeLanguage.aware,
        supports_virtual_build=True,
    )


def _make_class_config_attribute_config(
    *, class_config_id: UUID, is_identity_key: bool
) -> ClassConfigAttributeConfig:
    attribute_config_id = uuid4()
    attribute_config = AttributeConfig.model_construct(
        id=attribute_config_id,
        owner_key="test",
        name="label",
        description=None,
        default_value=None,
        is_primary=False,
        is_public=True,
        is_required=False,
        is_unique=False,
        is_virtual=False,
        exclude_serialization=False,
        type_descriptor=None,
        type_descriptor_id=uuid4(),
        code_section_attribute=None,
        code_section_attribute_id=None,
    )
    return ClassConfigAttributeConfig.model_construct(
        id=uuid4(),
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
        attribute_config=attribute_config,
        position=0,
        is_identity_key=is_identity_key,
    )


@pytest.mark.asyncio
async def test_object_projection_graph_build_is_idempotent(monkeypatch) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_projection_graph_handler,
        "current_handler_session",
        lambda: session,
    )

    object_config_graph_id = uuid4()
    created = await object_projection_graph_handler.build_via_object_config_graph(
        object_config_graph_id=object_config_graph_id,
        name="identity",
        projection_hash="projection-hash",
        language=CodeLanguage.aware,
    )
    expected_id = stable_object_projection_graph_id(
        object_config_graph_id=object_config_graph_id,
        name="identity",
    )
    assert created.id == expected_id
    session.put(created)

    created_again = await object_projection_graph_handler.build_via_object_config_graph(
        object_config_graph_id=object_config_graph_id,
        name="identity",
        projection_hash="projection-hash",
        language=CodeLanguage.aware,
    )
    assert created_again is created


@pytest.mark.asyncio
async def test_object_config_graph_create_object_projection_graph_appends_once(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_projection_graph_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        object_config_graph_handler.ObjectProjectionGraph,
        "build_via_object_config_graph",
        object_projection_graph_handler.build_via_object_config_graph,
    )

    graph = _make_ocg(uuid4(), fqn_prefix="aware_meta_test")

    created = await object_config_graph_handler.create_object_projection_graph(
        object_config_graph=graph,
        name="identity",
        projection_hash="projection-hash",
        language=CodeLanguage.aware,
    )
    session.put(created)

    created_again = await object_config_graph_handler.create_object_projection_graph(
        object_config_graph=graph,
        name="identity",
        projection_hash="projection-hash",
        language=CodeLanguage.aware,
    )

    assert created_again is created
    assert len(graph.object_projection_graphs) == 1


@pytest.mark.asyncio
async def test_object_projection_graph_child_build_handlers_are_idempotent(
    monkeypatch,
) -> None:
    session = _Session()
    for module in (
        object_projection_graph_node_handler,
        object_projection_graph_node_key_handler,
        object_projection_graph_edge_handler,
        object_projection_graph_constructor_handler,
        object_projection_graph_relationship_handler,
    ):
        monkeypatch.setattr(module, "current_handler_session", lambda: session)

    object_projection_graph_id = uuid4()
    class_config_id = uuid4()
    class_config_relationship_id = uuid4()
    root_node_id = uuid4()
    function_constructor_id = uuid4()
    target_object_projection_graph_id = uuid4()
    target_object_projection_graph_node_id = uuid4()

    node = await object_projection_graph_node_handler.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph_id,
        class_config_id=class_config_id,
        is_root=True,
        required_for_validity=True,
        selection=ObjectProjectionGraphNodeSelection.one,
        top_n=1,
        selector_condition_id=None,
        policy_refs=["a", "b"],
    )
    assert node.id == stable_object_projection_graph_node_id(
        object_projection_graph_id=object_projection_graph_id,
        class_config_id=class_config_id,
    )
    session.put(node)
    assert (
        await object_projection_graph_node_handler.build_via_object_projection_graph(
            object_projection_graph_id=object_projection_graph_id,
            class_config_id=class_config_id,
            is_root=True,
            required_for_validity=True,
            selection=ObjectProjectionGraphNodeSelection.one,
            top_n=1,
            selector_condition_id=None,
            policy_refs=["a", "b"],
        )
        is node
    )

    target_attribute = _make_class_config_attribute_config(
        class_config_id=class_config_id,
        is_identity_key=True,
    )
    session.put(target_attribute)
    binding_class = ObjectConfigGraphBindingClass(
        id=uuid4(),
        object_config_graph_binding_id=uuid4(),
        name="door_by_label",
        source_class_id=uuid4(),
        source_attr_id=None,
        target_class_id=class_config_id,
        target_attribute_id=target_attribute.id,
        target_attribute=target_attribute,
    )
    session.put(binding_class)

    node_key = await object_projection_graph_node_key_handler.build_via_object_projection_graph_node(
        object_projection_graph_node_id=node.id,
        object_config_graph_binding_class_id=binding_class.id,
        key="door_device",
        position=0,
        required=True,
    )
    assert node_key.id == stable_object_projection_graph_node_key_id(
        object_projection_graph_node_id=node.id,
        object_config_graph_binding_class_id=binding_class.id,
        key="door_device",
    )
    session.put(node_key)
    assert (
        await object_projection_graph_node_key_handler.build_via_object_projection_graph_node(
            object_projection_graph_node_id=node.id,
            object_config_graph_binding_class_id=binding_class.id,
            key="door_device",
            position=0,
            required=True,
        )
        is node_key
    )

    edge = await object_projection_graph_edge_handler.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
        include=ObjectProjectionGraphEdgeInclude.required,
        multiplicity=ObjectProjectionGraphEdgeMultiplicity.one,
        traversal_direction=ClassConfigRelationshipDirection.forward,
        depth_limit=2,
        attribute_role=ObjectProjectionGraphAttributeRole.reference,
        loading_override=None,
    )
    assert edge.id == stable_object_projection_graph_edge_id(
        object_projection_graph_id=object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
    )
    session.put(edge)
    assert (
        await object_projection_graph_edge_handler.build_via_object_projection_graph(
            object_projection_graph_id=object_projection_graph_id,
            class_config_relationship_id=class_config_relationship_id,
            include=ObjectProjectionGraphEdgeInclude.required,
            multiplicity=ObjectProjectionGraphEdgeMultiplicity.one,
            traversal_direction=ClassConfigRelationshipDirection.forward,
            depth_limit=2,
            attribute_role=ObjectProjectionGraphAttributeRole.reference,
            loading_override=None,
        )
        is edge
    )

    constructor = await object_projection_graph_constructor_handler.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph_id,
        root_node_id=root_node_id,
        function_constructor_id=function_constructor_id,
    )
    assert constructor.id == stable_object_projection_graph_constructor_id(
        object_projection_graph_id=object_projection_graph_id,
        root_node_id=root_node_id,
        function_constructor_id=function_constructor_id,
    )
    session.put(constructor)
    assert (
        await object_projection_graph_constructor_handler.build_via_object_projection_graph(
            object_projection_graph_id=object_projection_graph_id,
            root_node_id=root_node_id,
            function_constructor_id=function_constructor_id,
        )
        is constructor
    )

    relationship = await object_projection_graph_relationship_handler.build_via_object_projection_graph(
        object_projection_graph_id=object_projection_graph_id,
        target_object_projection_graph_id=target_object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
        source_object_projection_graph_node_id=root_node_id,
        target_object_projection_graph_node_id=target_object_projection_graph_node_id,
    )
    assert relationship.id == stable_object_projection_graph_relationship_id(
        object_projection_graph_id=object_projection_graph_id,
        target_object_projection_graph_id=target_object_projection_graph_id,
        class_config_relationship_id=class_config_relationship_id,
        source_object_projection_graph_node_id=root_node_id,
        target_object_projection_graph_node_id=target_object_projection_graph_node_id,
    )
    session.put(relationship)
    assert (
        await object_projection_graph_relationship_handler.build_via_object_projection_graph(
            object_projection_graph_id=object_projection_graph_id,
            target_object_projection_graph_id=target_object_projection_graph_id,
            class_config_relationship_id=class_config_relationship_id,
            source_object_projection_graph_node_id=root_node_id,
            target_object_projection_graph_node_id=target_object_projection_graph_node_id,
        )
        is relationship
    )


@pytest.mark.asyncio
async def test_object_projection_graph_create_children_append_once(monkeypatch) -> None:
    session = _Session()
    for module in (
        object_projection_graph_node_handler,
        object_projection_graph_node_key_handler,
        object_projection_graph_edge_handler,
        object_projection_graph_constructor_handler,
        object_projection_graph_relationship_handler,
    ):
        monkeypatch.setattr(module, "current_handler_session", lambda: session)

    monkeypatch.setattr(
        object_projection_graph_handler.ObjectProjectionGraphNode,
        "build_via_object_projection_graph",
        object_projection_graph_node_handler.build_via_object_projection_graph,
    )
    monkeypatch.setattr(
        object_projection_graph_node_handler.ObjectProjectionGraphNodeKey,
        "build_via_object_projection_graph_node",
        object_projection_graph_node_key_handler.build_via_object_projection_graph_node,
    )
    monkeypatch.setattr(
        object_projection_graph_handler.ObjectProjectionGraphEdge,
        "build_via_object_projection_graph",
        object_projection_graph_edge_handler.build_via_object_projection_graph,
    )
    monkeypatch.setattr(
        object_projection_graph_handler.ObjectProjectionGraphConstructor,
        "build_via_object_projection_graph",
        object_projection_graph_constructor_handler.build_via_object_projection_graph,
    )
    monkeypatch.setattr(
        object_projection_graph_handler.ObjectProjectionGraphRelationship,
        "build_via_object_projection_graph",
        object_projection_graph_relationship_handler.build_via_object_projection_graph,
    )

    opg = _make_opg(uuid4(), object_config_graph_id=uuid4(), name="Identity")

    node = await object_projection_graph_handler.create_node(
        object_projection_graph=opg,
        class_config_id=uuid4(),
        is_root=True,
        required_for_validity=True,
        selection=ObjectProjectionGraphNodeSelection.one,
        policy_refs=["policy.a"],
    )
    session.put(node)
    node_again = await object_projection_graph_handler.create_node(
        object_projection_graph=opg,
        class_config_id=node.class_config_id,
        is_root=True,
        required_for_validity=True,
        selection=ObjectProjectionGraphNodeSelection.one,
        policy_refs=["policy.a"],
    )
    assert node_again is node
    assert len(opg.object_projection_graph_nodes) == 1

    target_attribute = _make_class_config_attribute_config(
        class_config_id=node.class_config_id,
        is_identity_key=True,
    )
    session.put(target_attribute)
    binding_class = ObjectConfigGraphBindingClass(
        id=uuid4(),
        object_config_graph_binding_id=uuid4(),
        name="door_by_label",
        source_class_id=uuid4(),
        source_attr_id=None,
        target_class_id=node.class_config_id,
        target_attribute_id=target_attribute.id,
        target_attribute=target_attribute,
    )
    session.put(binding_class)

    node_key = await object_projection_graph_node_handler.create_key(
        object_projection_graph_node=node,
        object_config_graph_binding_class_id=binding_class.id,
        key="door_device",
        position=0,
        required=True,
    )
    session.put(node_key)
    node_key_again = await object_projection_graph_node_handler.create_key(
        object_projection_graph_node=node,
        object_config_graph_binding_class_id=binding_class.id,
        key="door_device",
        position=0,
        required=True,
    )
    assert node_key_again is node_key
    assert len(node.object_projection_graph_node_keys) == 1

    edge = await object_projection_graph_handler.create_edge(
        object_projection_graph=opg,
        class_config_relationship_id=uuid4(),
        include=ObjectProjectionGraphEdgeInclude.required,
        multiplicity=ObjectProjectionGraphEdgeMultiplicity.many,
        traversal_direction=ClassConfigRelationshipDirection.forward,
    )
    session.put(edge)
    edge_again = await object_projection_graph_handler.create_edge(
        object_projection_graph=opg,
        class_config_relationship_id=edge.class_config_relationship_id,
        include=ObjectProjectionGraphEdgeInclude.required,
        multiplicity=ObjectProjectionGraphEdgeMultiplicity.many,
        traversal_direction=ClassConfigRelationshipDirection.forward,
    )
    assert edge_again is edge
    assert len(opg.object_projection_graph_edges) == 1

    constructor = await object_projection_graph_handler.create_constructor(
        object_projection_graph=opg,
        root_node_id=node.id,
        function_constructor_id=uuid4(),
    )
    session.put(constructor)
    constructor_again = await object_projection_graph_handler.create_constructor(
        object_projection_graph=opg,
        root_node_id=node.id,
        function_constructor_id=constructor.function_constructor_id,
    )
    assert constructor_again is constructor
    assert len(opg.object_projection_graph_constructors) == 1

    relationship = await object_projection_graph_handler.create_relationship(
        object_projection_graph=opg,
        target_object_projection_graph_id=uuid4(),
        class_config_relationship_id=edge.class_config_relationship_id,
        source_object_projection_graph_node_id=node.id,
        target_object_projection_graph_node_id=uuid4(),
    )
    session.put(relationship)
    relationship_again = await object_projection_graph_handler.create_relationship(
        object_projection_graph=opg,
        target_object_projection_graph_id=relationship.target_object_projection_graph_id,
        class_config_relationship_id=edge.class_config_relationship_id,
        source_object_projection_graph_node_id=node.id,
        target_object_projection_graph_node_id=relationship.target_object_projection_graph_node_id,
    )
    assert relationship_again is relationship
    assert len(opg.object_projection_graph_relationships) == 1


@pytest.mark.asyncio
async def test_object_projection_graph_node_key_build_fails_closed_on_non_identity_target_attr(
    monkeypatch,
) -> None:
    session = _Session()
    monkeypatch.setattr(
        object_projection_graph_node_handler,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        object_projection_graph_node_key_handler,
        "current_handler_session",
        lambda: session,
    )

    node = await object_projection_graph_node_handler.build_via_object_projection_graph(
        object_projection_graph_id=uuid4(),
        class_config_id=uuid4(),
        is_root=True,
    )
    session.put(node)

    non_identity_target_attribute = _make_class_config_attribute_config(
        class_config_id=node.class_config_id,
        is_identity_key=False,
    )
    session.put(non_identity_target_attribute)
    binding_class = ObjectConfigGraphBindingClass(
        id=uuid4(),
        object_config_graph_binding_id=uuid4(),
        name="door_by_label",
        source_class_id=uuid4(),
        source_attr_id=None,
        target_class_id=node.class_config_id,
        target_attribute_id=non_identity_target_attribute.id,
        target_attribute=non_identity_target_attribute,
    )
    session.put(binding_class)

    with pytest.raises(RuntimeError, match="identity-key target attribute"):
        await object_projection_graph_node_key_handler.build_via_object_projection_graph_node(
            object_projection_graph_node_id=node.id,
            object_config_graph_binding_class_id=binding_class.id,
            key="door_device",
        )
