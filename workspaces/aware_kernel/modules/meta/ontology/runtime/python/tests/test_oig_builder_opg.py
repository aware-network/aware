from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
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
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphAttributeRole,
    ObjectProjectionGraphEdgeInclude,
    ObjectProjectionGraphEdgeMultiplicity,
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.graph.projection.object_projection_graph_relationship import (
    ObjectProjectionGraphRelationship,
)
from aware_code_ontology.code.code_enums import CodeLanguage

from aware_meta.graph.config.stable_ids import stable_class_instance_id
from aware_meta.graph.instance.builder import (
    InMemoryRelationshipResolver,
    InstanceRegistry,
    OigBuildError,
    build_rooted_object_instance_graph_base,
    build_object_instance_graph,
)
from aware_meta.graph.instance.member import ObjectInstanceGraphMember
from aware_meta.graph.instance.member_kind import ObjectInstanceGraphMemberKind
from aware_meta.graph.instance.topology import ObjectInstanceGraphTopology
from aware_meta.graph.instance.validator_opg import (
    validate_object_instance_graph_against_opg,
)
from aware_meta.class_.instance.handlers import link_attribute
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _class_desc(*, class_config_id: UUID) -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(
        kind=Kind.class_, child_links=[], class_config_id=class_config_id
    )


def _cfg(name: str, **kwargs) -> ClassConfig:
    return make_class_config(name, class_fqn=test_class_fqn(name), **kwargs)


def _attr(owner_name: str, name: str, **kwargs) -> AttributeConfig:
    return make_attribute_config(
        owner_key=test_class_fqn(owner_name), name=name, **kwargs
    )


def _edge(
    class_config: ClassConfig, attribute_config: AttributeConfig, *, position: int
) -> ClassConfigAttributeConfig:
    return make_class_attribute_edge(
        class_config_id=class_config.id,
        attribute_config=attribute_config,
        name=attribute_config.name,
        position=position,
    )


def _class_instance_id(
    *, object_instance_graph_id: UUID, class_config: ClassConfig, source_object_id: UUID
) -> UUID:
    return stable_class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=source_object_id,
    )


class _FakeTimings:
    def __init__(self) -> None:
        self.added: dict[str, float] = {}
        self.metrics: dict[str, object] = {}

    def add(self, name: str, duration_s: float) -> None:
        self.added[name] = duration_s

    def metric(self, key: str, value: object) -> None:
        self.metrics[key] = value


def _make_ocg_and_opg(*, edge_include: ObjectProjectionGraphEdgeInclude) -> tuple[
    ObjectConfigGraph,
    ObjectProjectionGraph,
    ClassConfig,
    ClassConfig,
    ClassConfigRelationship,
    AttributeConfig,
    AttributeConfig,
]:
    # Class B
    b_name_cfg = _attr("B", "name", is_required=True, type_descriptor=_primitive_desc())
    b_cc = _cfg("B", class_config_attribute_configs=[])
    b_cc.class_config_attribute_configs = [_edge(b_cc, b_name_cfg, position=0)]

    # Class A (has relationship attr `b`)
    a_name_cfg = _attr("A", "name", is_required=True, type_descriptor=_primitive_desc())
    a_b_cfg = _attr(
        "A",
        name="b",
        is_required=False,
        type_descriptor=_class_desc(class_config_id=b_cc.id),
    )
    a_b_id_cfg = _attr(
        "A", "b_id", is_required=False, type_descriptor=_primitive_desc()
    )
    a_cc = _cfg("A", class_config_attribute_configs=[], class_config_relationships=[])
    a_cc.class_config_attribute_configs = [
        _edge(a_cc, a_name_cfg, position=0),
        _edge(a_cc, a_b_cfg, position=1),
        _edge(a_cc, a_b_id_cfg, position=2),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_b",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cc.id,
        target_class_config_id=b_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=a_b_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=a_b_id_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    )
    a_cc.class_config_relationships = [rel]

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
            node_key=a_cc.class_fqn,
            class_config=a_cc,
            class_config_id=a_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cc.class_fqn,
            class_config=b_cc,
            class_config_id=b_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="0",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=a_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
        ObjectProjectionGraphNode(
            class_config_id=b_cc.id,
            object_projection_graph_id=opg.id,
            is_root=False,
            selection=ObjectProjectionGraphNodeSelection.all,
        ),
    ]
    opg.object_projection_graph_edges = [
        ObjectProjectionGraphEdge(
            class_config_relationship_id=rel.id,
            object_projection_graph_id=opg.id,
            include=edge_include,
            multiplicity=ObjectProjectionGraphEdgeMultiplicity.one,
            traversal_direction=ClassConfigRelationshipDirection.forward,
        )
    ]

    return ocg, opg, a_cc, b_cc, rel, a_name_cfg, a_b_cfg


def test_build_oig_from_opg_hydrated_reference() -> None:
    ocg, opg, a_cc, b_cc, rel, a_name_cfg, a_b_cfg = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B | None = None

    b = B(id=uuid4(), name="b")
    a = A(id=uuid4(), name="a", b=b)

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    a_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=a_cc, source_object_id=a.id
    )
    b_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=b_cc, source_object_id=b.id
    )
    assert graph.root_class_instance_id == a_ci_id
    ids = sorted([ci.id for ci in graph.class_instances])
    assert ids == sorted([a_ci_id, b_ci_id])

    # Relationship emitted
    assert len(graph.class_instance_relationships) == 1
    r = graph.class_instance_relationships[0]
    assert r.class_config_relationship_id == rel.id
    assert r.source_class_instance_id == a_ci_id
    assert r.target_class_instance_id == b_ci_id

    # Relationship attribute is not stored as Attribute on the ClassInstance.
    a_ci = next(ci for ci in graph.class_instances if ci.id == a_ci_id)
    assert [attr.attribute_config_id for attr in a_ci.attributes] == [a_name_cfg.id]
    assert a_b_cfg.id not in [attr.attribute_config_id for attr in a_ci.attributes]
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_oig_emits_build_profile_metrics() -> None:
    ocg, opg, a_cc, _b_cc, _rel, _a_name_cfg, _a_b_cfg = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B | None = None

    b = B(id=uuid4(), name="b")
    a = A(id=uuid4(), name="a", b=b)
    timings = _FakeTimings()

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
        timings=timings,
        timing_key_prefix="test_oig",
    )

    assert graph.root_class_instance_id == _class_instance_id(
        object_instance_graph_id=graph.id,
        class_config=a_cc,
        source_object_id=a.id,
    )
    assert "test_oig.build_indexes" in timings.added
    assert "test_oig.build_registry" in timings.added
    assert "test_oig.queue_walk" in timings.added
    assert "test_oig.finalize_graph" in timings.added
    assert "test_oig.class_instance.plan_attributes" in timings.added
    assert "test_oig.class_instance.materialize_attributes" in timings.added
    assert timings.metrics["test_oig_queue_pops"] == 2
    assert timings.metrics["test_oig_edges_visited"] == 1
    assert timings.metrics["test_oig_targets_resolved"] == 1
    assert timings.metrics["test_oig_relationships_emitted"] == 1
    assert timings.metrics["test_oig_class_instances_built"] == 2
    assert timings.metrics["test_oig_class_instance_cache_hits"] == 1
    assert timings.metrics["test_oig_class_instance_attr_links_total"] == 4
    assert timings.metrics["test_oig_class_instance_attributes_built"] == 2
    assert (
        timings.metrics["test_oig_class_instance_relationship_attributes_skipped"] == 2
    )
    assert timings.metrics["test_oig_class_instance_default_values_used"] == 0


def test_build_oig_includes_portal_foreign_key_attribute() -> None:
    """
    Cross-OPG portals cannot be traversed during OIG capture, but the source lane must
    retain the portal link field (`<ref>_id`) so runtime can route deterministically.
    """
    # Class B
    b_name_cfg = _attr("B", "name", is_required=True, type_descriptor=_primitive_desc())
    b_cc = _cfg("B", class_config_attribute_configs=[])
    b_cc.class_config_attribute_configs = [_edge(b_cc, b_name_cfg, position=0)]

    # Class A has a relationship to B via `b` + `b_id` (FK).
    a_name_cfg = _attr("A", "name", is_required=True, type_descriptor=_primitive_desc())
    a_b_cfg = _attr(
        "A",
        name="b",
        is_required=False,
        type_descriptor=_class_desc(class_config_id=b_cc.id),
    )
    a_b_id_cfg = _attr(
        "A", "b_id", is_required=False, type_descriptor=_primitive_desc()
    )
    a_cc = _cfg("A", class_config_attribute_configs=[], class_config_relationships=[])
    a_cc.class_config_attribute_configs = [
        _edge(a_cc, a_name_cfg, position=0),
        _edge(a_cc, a_b_cfg, position=1),
        _edge(a_cc, a_b_id_cfg, position=2),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_b",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cc.id,
        target_class_config_id=b_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.extend(
        [
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=a_b_cfg.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.reference,
            ),
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=a_b_id_cfg.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
        ]
    )
    a_cc.class_config_relationships = [rel]

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
            node_key=a_cc.class_fqn,
            class_config=a_cc,
            class_config_id=a_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cc.class_fqn,
            class_config=b_cc,
            class_config_id=b_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg_b = ObjectProjectionGraph(
        name="b-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="b",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg_b.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=b_cc.id,
            object_projection_graph_id=opg_b.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        )
    ]
    b_node = opg_b.object_projection_graph_nodes[0]

    opg_a = ObjectProjectionGraph(
        name="a-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="a",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg_a.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=a_cc.id,
            object_projection_graph_id=opg_a.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        )
    ]
    a_node = opg_a.object_projection_graph_nodes[0]

    opg_a.object_projection_graph_relationships = [
        ObjectProjectionGraphRelationship(
            object_projection_graph_id=opg_a.id,
            target_object_projection_graph_id=opg_b.id,
            class_config_relationship_id=rel.id,
            source_object_projection_graph_node_id=a_node.id,
            target_object_projection_graph_node_id=b_node.id,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class A(BaseORMModel):
        name: str
        b_id: UUID | None = None

    b_id = uuid4()
    a = A(id=uuid4(), name="a", b_id=b_id)

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg_a,
        name="g",
        description="d",
    )

    a_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=a_cc, source_object_id=a.id
    )
    a_ci = next(ci for ci in graph.class_instances if ci.id == a_ci_id)
    assert [attr.attribute_config_id for attr in a_ci.attributes] == [
        a_name_cfg.id,
        a_b_id_cfg.id,
    ]
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg_a
    )


def test_build_oig_includes_soft_ref_foreign_key_attribute() -> None:
    """
    If a relationship is not represented as an OPG edge, but has a deterministic forward
    FOREIGN_KEY binding, the FK UUID must be preserved as a commit-tracked Attribute (SoftRef).
    """
    # Class B
    b_name_cfg = _attr("B", "name", is_required=True, type_descriptor=_primitive_desc())
    b_cc = _cfg("B", class_config_attribute_configs=[])
    b_cc.class_config_attribute_configs = [_edge(b_cc, b_name_cfg, position=0)]

    # Class A has a relationship to B via `b` + `b_id` (FK).
    a_name_cfg = _attr("A", "name", is_required=True, type_descriptor=_primitive_desc())
    a_b_cfg = _attr(
        "A",
        name="b",
        is_required=False,
        type_descriptor=_class_desc(class_config_id=b_cc.id),
    )
    a_b_id_cfg = _attr(
        "A", "b_id", is_required=False, type_descriptor=_primitive_desc()
    )
    a_cc = _cfg("A", class_config_attribute_configs=[], class_config_relationships=[])
    a_cc.class_config_attribute_configs = [
        _edge(a_cc, a_name_cfg, position=0),
        _edge(a_cc, a_b_cfg, position=1),
        _edge(a_cc, a_b_id_cfg, position=2),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_b",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cc.id,
        target_class_config_id=b_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.extend(
        [
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=a_b_cfg.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.reference,
            ),
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=a_b_id_cfg.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
        ]
    )
    a_cc.class_config_relationships = [rel]

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
            node_key=a_cc.class_fqn,
            class_config=a_cc,
            class_config_id=a_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cc.class_fqn,
            class_config=b_cc,
            class_config_id=b_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    # Both endpoints are members, but there is no edge in this lens (SoftRef, not StrongRef).
    opg = ObjectProjectionGraph(
        name="soft-ref-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="soft",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=a_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
        ObjectProjectionGraphNode(
            class_config_id=b_cc.id,
            object_projection_graph_id=opg.id,
            is_root=False,
            selection=ObjectProjectionGraphNodeSelection.all,
        ),
    ]

    from aware_orm.models.base_model import BaseORMModel

    class A(BaseORMModel):
        name: str
        b_id: UUID | None = None

    b_id = uuid4()
    a = A(id=uuid4(), name="a", b_id=b_id)

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    assert graph.class_instance_relationships == []
    a_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=a_cc, source_object_id=a.id
    )
    a_ci = next(ci for ci in graph.class_instances if ci.id == a_ci_id)
    assert [attr.attribute_config_id for attr in a_ci.attributes] == [
        a_name_cfg.id,
        a_b_id_cfg.id,
    ]
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_oig_includes_soft_ref_reverse_foreign_key_attribute() -> None:
    """
    If a relationship is not represented as an OPG edge, reverse-owned FOREIGN_KEY
    bindings must still be preserved as commit-tracked attributes on the owner class.
    """
    # Class Parent -> Child (Child owns reverse FK `parent_id`).
    child_name_cfg = _attr(
        "Child", "name", is_required=True, type_descriptor=_primitive_desc()
    )
    child_parent_id_cfg = _attr(
        "Child", "parent_id", is_required=True, type_descriptor=_primitive_desc()
    )
    child_cc = _cfg("Child", class_config_attribute_configs=[])
    child_cc.class_config_attribute_configs = [
        _edge(child_cc, child_name_cfg, position=0),
        _edge(child_cc, child_parent_id_cfg, position=1),
    ]

    parent_children_cfg = _attr(
        "Parent",
        name="children",
        is_required=False,
        type_descriptor=_class_desc(class_config_id=child_cc.id),
    )
    parent_cc = _cfg(
        "Parent", class_config_attribute_configs=[], class_config_relationships=[]
    )
    parent_cc.class_config_attribute_configs = [
        _edge(parent_cc, parent_children_cfg, position=0)
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=parent_cc.id,
        target_class_config_id=child_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.extend(
        [
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=parent_children_cfg.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.reference,
            ),
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=child_parent_id_cfg.id,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
        ]
    )
    parent_cc.class_config_relationships = [rel]

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
            node_key=parent_cc.class_fqn,
            class_config=parent_cc,
            class_config_id=parent_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=child_cc.class_fqn,
            class_config=child_cc,
            class_config_id=child_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    # SoftRef reverse FK:
    # - only Child is in this projection frontier.
    opg = ObjectProjectionGraph(
        name="soft-ref-reverse-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="soft-reverse",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=child_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class Child(BaseORMModel):
        name: str
        parent_id: UUID

    child = Child(id=uuid4(), name="c", parent_id=uuid4())

    graph = build_object_instance_graph(
        root_instance=child,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    assert graph.class_instance_relationships == []
    child_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id,
        class_config=child_cc,
        source_object_id=child.id,
    )
    child_ci = next(ci for ci in graph.class_instances if ci.id == child_ci_id)
    assert [attr.attribute_config_id for attr in child_ci.attributes] == [
        child_name_cfg.id,
        child_parent_id_cfg.id,
    ]
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_oig_injects_target_owned_traversal_foreign_key_attribute() -> None:
    """
    Runtime-transformer-synthesized parent FKs are not authored fields on source
    models. When an OPG traversal discovers a child, the OIG builder must derive
    the target-owned FK from the traversed source object id.
    """
    child_name_cfg = _attr(
        "Child", "name", is_required=True, type_descriptor=_primitive_desc()
    )
    child_parent_id_cfg = _attr(
        "Child", "parent_id", is_required=True, type_descriptor=_primitive_desc()
    )
    child_cc = _cfg("Child", class_config_attribute_configs=[])
    child_cc.class_config_attribute_configs = [
        _edge(child_cc, child_name_cfg, position=0),
        _edge(child_cc, child_parent_id_cfg, position=1),
    ]

    parent_children_cfg = _attr(
        "Parent",
        name="children",
        is_required=False,
        type_descriptor=_class_desc(class_config_id=child_cc.id),
    )
    parent_cc = _cfg(
        "Parent", class_config_attribute_configs=[], class_config_relationships=[]
    )
    parent_cc.class_config_attribute_configs = [
        _edge(parent_cc, parent_children_cfg, position=0)
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=parent_cc.id,
        target_class_config_id=child_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.extend(
        [
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=parent_children_cfg.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.reference,
            ),
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=child_parent_id_cfg.id,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
        ]
    )
    parent_cc.class_config_relationships = [rel]

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
            node_key=parent_cc.class_fqn,
            class_config=parent_cc,
            class_config_id=parent_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=child_cc.class_fqn,
            class_config=child_cc,
            class_config_id=child_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="traversal-fk-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="traversal-fk",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=parent_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
        ObjectProjectionGraphNode(
            class_config_id=child_cc.id,
            object_projection_graph_id=opg.id,
            is_root=False,
            selection=ObjectProjectionGraphNodeSelection.all,
        ),
    ]
    opg.object_projection_graph_edges = [
        ObjectProjectionGraphEdge(
            class_config_relationship_id=rel.id,
            object_projection_graph_id=opg.id,
            include=ObjectProjectionGraphEdgeInclude.required,
            multiplicity=ObjectProjectionGraphEdgeMultiplicity.many,
            traversal_direction=ClassConfigRelationshipDirection.forward,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class Child(BaseORMModel):
        name: str

    class Parent(BaseORMModel):
        children: list[Child]

    child = Child(id=uuid4(), name="c")
    parent = Parent(id=uuid4(), children=[child])

    graph = build_object_instance_graph(
        root_instance=parent,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    child_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id,
        class_config=child_cc,
        source_object_id=child.id,
    )
    child_ci = next(ci for ci in graph.class_instances if ci.id == child_ci_id)
    parent_id_attr = next(
        attr
        for attr in child_ci.attributes
        if attr.attribute_config_id == child_parent_id_cfg.id
    )
    assert parent_id_attr.value_root is not None
    assert parent_id_attr.value_root.primitive_value == {"value": str(parent.id)}
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_oig_ignores_detached_required_fk_relationships() -> None:
    """
    Required-FK retention must ignore detached relationships whose endpoint classes
    are outside the active OCG dependency closure.
    """
    a_name_cfg = _attr("A", "name", is_required=True, type_descriptor=_primitive_desc())
    a_cc = _cfg("A", class_config_attribute_configs=[])
    a_cc.class_config_attribute_configs = [_edge(a_cc, a_name_cfg, position=0)]

    detached_rel = ClassConfigRelationship(
        relationship_key="detached_required_fk",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=uuid4(),
        target_class_config_id=uuid4(),
        class_config_relationship_attributes=[],
    )
    detached_rel.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=detached_rel.id,
            attribute_config_id=uuid4(),
            direction=ClassConfigRelationshipDirection.reverse,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]

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
            node_key=a_cc.class_fqn,
            class_config=a_cc,
            class_config_id=a_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=detached_rel.relationship_key,
            class_config_relationship=detached_rel,
            class_config_relationship_id=detached_rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="detached-required-fk-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="detached-required-fk",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=a_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class A(BaseORMModel):
        name: str

    a = A(id=uuid4(), name="a")

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    a_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=a_cc, source_object_id=a.id
    )
    assert graph.root_class_instance_id == a_ci_id
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_oig_hash_changes_on_attribute_value_change() -> None:
    ocg, opg, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B | None = None

    b_id = uuid4()
    a_id = uuid4()

    b = B(id=b_id, name="b")
    g1 = build_object_instance_graph(
        root_instance=A(id=a_id, name="a", b=b),
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    g2 = build_object_instance_graph(
        root_instance=A(id=a_id, name="a2", b=b),
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    assert g1.hash != g2.hash


def test_meta_graph_support_index_includes_attribute_value_root() -> None:
    ocg, opg, _, _, _, a_name_cfg, _ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_meta.graph.support.index import build_index as build_member_index
    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B | None = None

    b = B(id=uuid4(), name="b")
    a_id = uuid4()
    graph_id = uuid4()

    g1 = build_object_instance_graph(
        root_instance=A(id=a_id, name="a", b=b),
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
        oig_id=graph_id,
    )
    g2 = build_object_instance_graph(
        root_instance=A(id=a_id, name="a2", b=b),
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
        oig_id=graph_id,
    )

    topo = ObjectInstanceGraphTopology()
    idx1 = build_member_index(ObjectInstanceGraphMember(object_instance_graph=g1), topo)
    idx2 = build_member_index(ObjectInstanceGraphMember(object_instance_graph=g2), topo)

    # Find the value-root node for attribute "name" on A.
    value_paths_1 = [
        path
        for path, (_, kind) in idx1.get_all_paths().items()
        if kind == ObjectInstanceGraphMemberKind.attribute_value
        and f"attr:{a_name_cfg.id}" in path
    ]
    assert value_paths_1
    value_path = value_paths_1[0]

    m1, _ = idx1.get_by_path(value_path)  # type: ignore[assignment]
    m2, _ = idx2.get_by_path(value_path)  # type: ignore[assignment]
    assert m1.get_content_fields()["primitive_value"] == "a"
    assert m2.get_content_fields()["primitive_value"] == "a2"


def test_build_oig_required_edge_missing_raises() -> None:
    ocg, opg, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_orm.models.base_model import BaseORMModel

    class A(BaseORMModel):
        name: str
        b: object | None = None

    with pytest.raises(OigBuildError):
        build_object_instance_graph(
            root_instance=A(id=uuid4(), name="a"),
            object_config_graph=ocg,
            object_projection_graph=opg,
            name="g",
            description="d",
        )


def test_build_oig_registry_fallback_uses_ref_id() -> None:
    ocg, opg, a_cc, b_cc, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B | None = None
        b_id: UUID

    b = B(id=uuid4(), name="b")
    a = A(id=uuid4(), name="a", b_id=b.id)

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
        instance_registry=[b],
    )
    ids = sorted([ci.id for ci in graph.class_instances])
    assert ids == sorted(
        [
            _class_instance_id(
                object_instance_graph_id=graph.id,
                class_config=a_cc,
                source_object_id=a.id,
            ),
            _class_instance_id(
                object_instance_graph_id=graph.id,
                class_config=b_cc,
                source_object_id=b.id,
            ),
        ]
    )
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_oig_optional_edge_missing_is_ok() -> None:
    ocg, opg, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.optional
    )

    from aware_orm.models.base_model import BaseORMModel

    class A(BaseORMModel):
        name: str
        b: object | None = None
        b_id: UUID | None = None

    graph = build_object_instance_graph(
        root_instance=A(id=uuid4(), name="a"),
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )
    assert [ci.id for ci in graph.class_instances] == [graph.root_class_instance_id]
    assert graph.class_instance_relationships == []
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_oig_required_many_empty_collection_is_ok() -> None:
    b_name_cfg = _attr("B", "name", is_required=True, type_descriptor=_primitive_desc())
    b_cc = _cfg("B", class_config_attribute_configs=[])
    b_cc.class_config_attribute_configs = [_edge(b_cc, b_name_cfg, position=0)]

    a_name_cfg = _attr("A", "name", is_required=True, type_descriptor=_primitive_desc())
    a_bs_cfg = _attr(
        "A",
        name="bs",
        is_required=True,
        type_descriptor=_class_desc(class_config_id=b_cc.id),
    )
    a_cc = _cfg("A", class_config_attribute_configs=[], class_config_relationships=[])
    a_cc.class_config_attribute_configs = [
        _edge(a_cc, a_name_cfg, position=0),
        _edge(a_cc, a_bs_cfg, position=1),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_bs",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cc.id,
        target_class_config_id=b_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=a_bs_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    )
    a_cc.class_config_relationships = [rel]

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
            node_key=a_cc.class_fqn,
            class_config=a_cc,
            class_config_id=a_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cc.class_fqn,
            class_config=b_cc,
            class_config_id=b_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="0",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=a_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
        ObjectProjectionGraphNode(
            class_config_id=b_cc.id,
            object_projection_graph_id=opg.id,
            is_root=False,
            selection=ObjectProjectionGraphNodeSelection.all,
        ),
    ]
    opg.object_projection_graph_edges = [
        ObjectProjectionGraphEdge(
            class_config_relationship_id=rel.id,
            object_projection_graph_id=opg.id,
            include=ObjectProjectionGraphEdgeInclude.required,
            multiplicity=ObjectProjectionGraphEdgeMultiplicity.many,
            traversal_direction=ClassConfigRelationshipDirection.forward,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        bs: list[B]

    graph = build_object_instance_graph(
        root_instance=A(id=uuid4(), name="a", bs=[]),
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    assert [ci.class_config_id for ci in graph.class_instances] == [a_cc.id]
    assert graph.class_instance_relationships == []
    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_rooted_oig_base_uses_class_instance_attribute_edges() -> None:
    ocg, opg, a_cc, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.optional
    )
    root_source_object_id = uuid4()

    graph = build_rooted_object_instance_graph_base(
        key="rooted-base",
        name="g",
        description="d",
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=root_source_object_id,
    )

    assert len(graph.class_instances) == 1
    assert graph.root_class_instance_id == graph.class_instances[0].id
    assert graph.root_class_instance.class_config_id == a_cc.id
    assert graph.root_class_instance.source_object_id == root_source_object_id
    assert graph.root_class_instance.class_instance_attributes == []
    assert graph.root_class_instance.attributes == []


def test_build_oig_reverse_traversal_scans_registry() -> None:
    # Same A -> B relationship config, but traverse in reverse (root=B, targets are A that reference B).
    ocg, opg, a_cc, b_cc, rel, a_name_cfg, a_b_cfg = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )
    opg.object_projection_graph_nodes[0].is_root = False
    opg.object_projection_graph_nodes[1].is_root = True
    opg.object_projection_graph_edges[0].traversal_direction = (
        ClassConfigRelationshipDirection.reverse
    )

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B

    A.bind_class_config(a_cc)
    B.bind_class_config(b_cc)

    b = B(id=uuid4(), name="b")
    a = A(id=uuid4(), name="a", b=b)

    graph = build_object_instance_graph(
        root_instance=b,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
        instance_registry=[a],
    )

    a_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=a_cc, source_object_id=a.id
    )
    b_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=b_cc, source_object_id=b.id
    )
    assert graph.root_class_instance_id == b_ci_id
    ids = sorted([ci.id for ci in graph.class_instances])
    assert ids == sorted([a_ci_id, b_ci_id])

    # Relationship is stored in canonical forward orientation: A -> B.
    assert len(graph.class_instance_relationships) == 1
    r = graph.class_instance_relationships[0]
    assert r.class_config_relationship_id == rel.id
    assert r.source_class_instance_id == a_ci_id
    assert r.target_class_instance_id == b_ci_id

    # Relationship attribute is still omitted from A's Attributes.
    a_ci = next(ci for ci in graph.class_instances if ci.id == a_ci_id)
    assert [attr.attribute_config_id for attr in a_ci.attributes] == [a_name_cfg.id]
    assert a_b_cfg.id not in [attr.attribute_config_id for attr in a_ci.attributes]

    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_reverse_resolver_indexes_reference_candidates_once_per_registry() -> None:
    ocg, opg, a_cc, b_cc, rel, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )
    edge = opg.object_projection_graph_edges[0]
    edge.traversal_direction = ClassConfigRelationshipDirection.reverse

    from aware_orm.models.base_model import BaseORMModel

    reference_reads: dict[UUID, int] = {}

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B | None = None

        def try_field_value(self, field_name: str, include_unset: bool = False):
            if field_name == "b":
                reference_reads[self.id] = reference_reads.get(self.id, 0) + 1
            return super().try_field_value(field_name, include_unset=include_unset)

    A.bind_class_config(a_cc)
    B.bind_class_config(b_cc)

    b1 = B(id=uuid4(), name="b1")
    b2 = B(id=uuid4(), name="b2")
    a1 = A(id=uuid4(), name="a1", b=b1)
    a2 = A(id=uuid4(), name="a2", b=b2)
    registry = InstanceRegistry.from_instances([a1, a2, b1, b2])
    resolver = InMemoryRelationshipResolver()

    targets1 = resolver.resolve_targets(
        source_instance=b1,
        edge=edge,
        relationship=rel,
        reference_field_name="b",
        target_class_config_id=a_cc.id,
        registry=registry,
    )
    targets2 = resolver.resolve_targets(
        source_instance=b2,
        edge=edge,
        relationship=rel,
        reference_field_name="b",
        target_class_config_id=a_cc.id,
        registry=registry,
    )

    assert [target.id for target in targets1] == [a1.id]
    assert [target.id for target in targets2] == [a2.id]
    assert reference_reads == {a1.id: 1, a2.id: 1}


def test_reverse_fk_resolver_indexes_foreign_key_candidates_once_per_registry() -> None:
    ocg, opg, a_cc, b_cc, rel, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )
    edge = opg.object_projection_graph_edges[0]
    edge.traversal_direction = ClassConfigRelationshipDirection.reverse
    edge.attribute_role = ObjectProjectionGraphAttributeRole.foreign_key

    from aware_orm.models.base_model import BaseORMModel

    fk_reads: dict[UUID, int] = {}

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b_id: UUID | None = None

        def try_field_value(self, field_name: str, include_unset: bool = False):
            if field_name == "b_id":
                fk_reads[self.id] = fk_reads.get(self.id, 0) + 1
            return super().try_field_value(field_name, include_unset=include_unset)

    A.bind_class_config(a_cc)
    B.bind_class_config(b_cc)

    b1 = B(id=uuid4(), name="b1")
    b2 = B(id=uuid4(), name="b2")
    a1 = A(id=uuid4(), name="a1", b_id=b1.id)
    a2 = A(id=uuid4(), name="a2", b_id=b2.id)
    registry = InstanceRegistry.from_instances([a1, a2, b1, b2])
    resolver = InMemoryRelationshipResolver(
        attribute_configs_by_id={
            link.attribute_config.id: link.attribute_config
            for link in a_cc.class_config_attribute_configs
            if link.attribute_config is not None
        }
    )

    targets1 = resolver.resolve_targets(
        source_instance=b1,
        edge=edge,
        relationship=rel,
        reference_field_name="b",
        target_class_config_id=a_cc.id,
        registry=registry,
    )
    targets2 = resolver.resolve_targets(
        source_instance=b2,
        edge=edge,
        relationship=rel,
        reference_field_name="b",
        target_class_config_id=a_cc.id,
        registry=registry,
    )

    assert [target.id for target in targets1] == [a1.id]
    assert [target.id for target in targets2] == [a2.id]
    assert fk_reads == {a1.id: 1, a2.id: 1}


def test_build_oig_top_n_selection_limits_targets() -> None:
    # Configure A -> B as LIST relationship and apply TOP_N selection on B node.
    b_name_cfg = _attr("B", "name", is_required=True, type_descriptor=_primitive_desc())
    b_cc = _cfg("B", class_config_attribute_configs=[])
    b_cc.class_config_attribute_configs = [_edge(b_cc, b_name_cfg, position=0)]

    a_name_cfg = _attr("A", "name", is_required=True, type_descriptor=_primitive_desc())
    a_bs_cfg = _attr(
        "A",
        name="bs",
        is_required=False,
        type_descriptor=_class_desc(class_config_id=b_cc.id),
    )
    a_cc = _cfg("A", class_config_attribute_configs=[], class_config_relationships=[])
    a_cc.class_config_attribute_configs = [
        _edge(a_cc, a_name_cfg, position=0),
        _edge(a_cc, a_bs_cfg, position=1),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_bs",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cc.id,
        target_class_config_id=b_cc.id,
        class_config_relationship_attributes=[],
    )
    rel.class_config_relationship_attributes.append(
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=a_bs_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    )
    a_cc.class_config_relationships = [rel]

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
            node_key=a_cc.class_fqn,
            class_config=a_cc,
            class_config_id=a_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cc.class_fqn,
            class_config=b_cc,
            class_config_id=b_cc.id,
            object_config_graph_id=ocg.id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="0",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=a_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
        ObjectProjectionGraphNode(
            class_config_id=b_cc.id,
            object_projection_graph_id=opg.id,
            is_root=False,
            selection=ObjectProjectionGraphNodeSelection.top_n,
            top_n=1,
        ),
    ]
    opg.object_projection_graph_edges = [
        ObjectProjectionGraphEdge(
            class_config_relationship_id=rel.id,
            object_projection_graph_id=opg.id,
            include=ObjectProjectionGraphEdgeInclude.required,
            multiplicity=ObjectProjectionGraphEdgeMultiplicity.many,
            traversal_direction=ClassConfigRelationshipDirection.forward,
        )
    ]

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        bs: list[B]

    b1 = B(id=uuid4(), name="b1")
    b2 = B(id=uuid4(), name="b2")
    a = A(id=uuid4(), name="a", bs=[b2, b1])

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )
    a_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=a_cc, source_object_id=a.id
    )
    assert graph.root_class_instance_id == a_ci_id
    assert {ci.class_config_id for ci in graph.class_instances} == {a_cc.id, b_cc.id}
    assert len(graph.class_instances) == 2
    assert len(graph.class_instance_relationships) == 1

    validate_object_instance_graph_against_opg(
        graph=graph, object_config_graph=ocg, object_projection_graph=opg
    )


def test_build_oig_missing_reference_field_does_not_trigger_getattr() -> None:
    # Regression: builders must never access undeclared fields (would trigger RelationshipMixin.__getattr__ lazy load).
    ocg, opg, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from dataclasses import dataclass

    from aware_orm.models.introspection import ModelIntrospection

    @dataclass(frozen=True)
    class A(ModelIntrospection):
        id: UUID
        name: str

        def __getattr__(self, name: str):
            raise AssertionError(f"unexpected attribute access: {name}")

        def field_is_declared(self, name: str) -> bool:
            return name in {"id", "name"}

        def field_is_set(self, name: str) -> bool:
            return self.field_is_declared(name)

        def try_field_value(
            self, name: str, *, include_unset: bool = False
        ) -> tuple[bool, object]:
            if name == "id":
                return True, self.id
            if name == "name":
                return True, self.name
            return False, None

        def try_virtual_value(
            self, attribute_config: AttributeConfig
        ) -> tuple[bool, object]:
            return False, None

        def try_attribute_value(
            self, attribute_config: AttributeConfig
        ) -> tuple[bool, object]:
            return self.try_field_value(attribute_config.name, include_unset=False)

        def try_class_config_id(self) -> UUID | None:
            return None

    with pytest.raises(OigBuildError):
        build_object_instance_graph(
            root_instance=A(id=uuid4(), name="a"),
            object_config_graph=ocg,
            object_projection_graph=opg,
            name="g",
            description="d",
        )


def test_oig_validator_rejects_relationship_attributes_as_data_attributes() -> None:
    ocg, opg, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_orm.models.base_model import BaseORMModel
    from aware_meta.attribute.instance.builder import build_attribute
    from aware_meta.graph.instance.validator_opg import OigValidationError

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: B | None = None

    b = B(id=uuid4(), name="b")
    a = A(id=uuid4(), name="a", b=b)

    graph = build_object_instance_graph(
        root_instance=a,
        object_config_graph=ocg,
        object_projection_graph=opg,
        name="g",
        description="d",
    )

    # Inject the relationship attribute as a data Attribute (invalid canonical shape).
    a_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "A"
    )
    b_cc = next(
        n.class_config
        for n in ocg.object_config_graph_nodes
        if n.class_config and n.class_config.name == "B"
    )
    a_ci_id = _class_instance_id(
        object_instance_graph_id=graph.id, class_config=a_cc, source_object_id=a.id
    )
    a_ci = next(ci for ci in graph.class_instances if ci.id == a_ci_id)
    b_attr_cfg = next(
        link.attribute_config
        for link in a_cc.class_config_attribute_configs
        if link.attribute_config is not None and link.attribute_config.name == "b"
    )
    _ = link_attribute(
        a_ci,
        build_attribute(
            owner_key=a.id,
            attribute_config=b_attr_cfg,
            value=b.id,
            class_configs_by_id={a_cc.id: a_cc, b_cc.id: b_cc},
        ),
    )

    with pytest.raises(OigValidationError):
        validate_object_instance_graph_against_opg(
            graph=graph, object_config_graph=ocg, object_projection_graph=opg
        )


def test_build_oig_one_multiplicity_rejects_multiple_targets() -> None:
    ocg, opg, *_ = _make_ocg_and_opg(
        edge_include=ObjectProjectionGraphEdgeInclude.required
    )

    from aware_orm.models.base_model import BaseORMModel

    class B(BaseORMModel):
        name: str

    class A(BaseORMModel):
        name: str
        b: list[B]

    b1 = B(id=uuid4(), name="b1")
    b2 = B(id=uuid4(), name="b2")
    a = A(id=uuid4(), name="a", b=[b1, b2])

    with pytest.raises(OigBuildError):
        build_object_instance_graph(
            root_instance=a,
            object_config_graph=ocg,
            object_projection_graph=opg,
            name="g",
            description="d",
        )
