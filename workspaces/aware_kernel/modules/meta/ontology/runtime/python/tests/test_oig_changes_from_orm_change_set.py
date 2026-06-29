from __future__ import annotations

import copy
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import Field


# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# History Api
from aware_history_ontology.change.change_enums import ChangeType

# Meta Api
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)

# Meta Ontology
from aware_meta_ontology import _bootstrap_models
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
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_edge import (
    ObjectProjectionGraphEdge,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.stable_ids import stable_class_instance_id


# Meta Runtime
from aware_meta.graph.instance.apply import apply_object_instance_graph_changes
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.graph.config.relationship_analysis import (
    stable_reified_association_source_relationship_id,
    stable_reified_association_target_relationship_id,
)
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    test_class_fqn,
)

# ORM
from aware_orm.models.orm_model import ORMModel
from aware_orm.session.change_collector import ORMChangeSet
from aware_orm.session.change_collector import scoped_change_collection
from aware_orm.session.current_session_ctx import set_session
from aware_orm.session.session import Session

_TEST_OIGI_ID = uuid4()


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


def _attribute_configs_by_id(ocg: ObjectConfigGraph) -> dict[UUID, AttributeConfig]:
    out: dict[UUID, AttributeConfig] = {}
    for node in ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.class_ or node.class_config is None:
            continue
        for link in node.class_config.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            out[link.attribute_config.id] = link.attribute_config
    return out


def _ci_id(*, graph_id: UUID, class_config_id: UUID, source_object_id: UUID) -> UUID:
    return stable_class_instance_id(
        object_instance_graph_id=graph_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
    )


def _make_before_oig(
    *,
    ocg_id: UUID,
    opg: ObjectProjectionGraph,
    root_class_config_id: UUID,
    root_source_object_id: UUID,
    before_oig_id: UUID | None = None,
    class_instances: list[ClassInstance] | None = None,
    class_instance_relationships: list[ClassInstanceRelationship] | None = None,
    name: str = "PRE",
) -> ObjectInstanceGraph:
    before_oig = build_rooted_object_instance_graph_base(
        key="pre",
        name=name,
        description="",
        object_config_graph_id=ocg_id,
        object_projection_graph=opg,
        root_source_object_id=root_source_object_id,
        root_class_config_id=root_class_config_id,
        oig_id=before_oig_id,
    )
    if class_instances is not None:
        root = next(
            ci for ci in class_instances if ci.id == before_oig.root_class_instance_id
        )
        before_oig.class_instances = class_instances
        before_oig.root_class_instance = root
        before_oig.root_class_instance_id = root.id
    if class_instance_relationships is not None:
        before_oig.class_instance_relationships = class_instance_relationships
    before_oig.hash = compute_hash(before_oig, index=build_index(before_oig))
    return before_oig


def test_created_instance_includes_soft_ref_foreign_key_attribute() -> None:
    """
    Regression: diff_orm must preserve SoftRef forward FOREIGN_KEY attributes as commit-tracked data.

    Without this, created instances can miss required FK columns during DB projection
    (e.g. AgentProcessConfig.analytic_id), causing "DB commit failed after lane append"
    and cascading FK failures for downstream objects.
    """
    _bootstrap_models()

    class B(ORMModel):
        name: str | None = None

    class A(ORMModel):
        name: str
        b: B | None = Field(default=None, exclude=True)
        b_id: UUID

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:softref-fk-attr"
    opg_id = uuid4()

    # Class B
    b_name_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    b_name_cfg = _attr(
        "B",
        name="name",
        is_required=False,
        type_descriptor=b_name_desc,
        type_descriptor_id=b_name_desc.id,
    )
    b_cfg = _cfg("B")
    b_cfg.class_config_attribute_configs = [_edge(b_cfg, b_name_cfg, position=0)]

    # Class A has a relationship to B via `b` + required `b_id` (FK SoftRef).
    a_name_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    a_name_cfg = _attr(
        "A",
        name="name",
        is_required=True,
        type_descriptor=a_name_desc,
        type_descriptor_id=a_name_desc.id,
    )
    a_b_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=b_cfg.id
    )
    a_b_cfg = _attr(
        "A",
        name="b",
        is_required=False,
        type_descriptor=a_b_desc,
        type_descriptor_id=a_b_desc.id,
    )
    a_b_id_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    a_b_id_cfg = _attr(
        "A",
        name="b_id",
        is_required=True,
        type_descriptor=a_b_id_desc,
        type_descriptor_id=a_b_id_desc.id,
    )
    a_cfg = _cfg("A")
    a_cfg.class_config_attribute_configs = [
        _edge(a_cfg, a_name_cfg, position=0),
        _edge(a_cfg, a_b_cfg, position=1),
        _edge(a_cfg, a_b_id_cfg, position=2),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_b",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cfg.id,
        target_class_config_id=b_cfg.id,
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
    a_cfg.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=a_cfg.class_fqn,
            class_config=a_cfg,
            class_config_id=a_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cfg.class_fqn,
            class_config=b_cfg,
            class_config_id=b_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg_id,
        ),
    ]

    # SoftRef: both endpoints are members, but the relationship is NOT an OPG edge.
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=a_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=b_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )

    A.bind_class_config(a_cfg)
    B.bind_class_config(b_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    a_id = uuid4()
    b_id = uuid4()

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=a_cfg.id,
        root_source_object_id=a_id,
        before_oig_id=uuid4(),
    )

    with set_session(session):
        a = A(id=a_id, name="a", b_id=b_id)
        with scoped_change_collection() as collector:
            collector.record_create(a)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    a_ci_id = _ci_id(
        graph_id=before_oig.id, class_config_id=a_cfg.id, source_object_id=a_id
    )
    created = next(ci for ci in after_oig.class_instances if ci.id == a_ci_id)
    created_attr_ids = [attr.attribute_config_id for attr in created.attributes]
    assert a_b_id_cfg.id in created_attr_ids


def test_created_instance_includes_soft_ref_foreign_key_attribute_cross_frontier() -> (
    None
):
    """
    Regression: preserve source-owned FK attributes when relationship target class is
    outside the active OPG node frontier.
    """
    _bootstrap_models()

    class B(ORMModel):
        name: str | None = None

    class A(ORMModel):
        name: str
        b: B | None = Field(default=None, exclude=True)
        b_id: UUID

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:softref-cross-frontier"
    opg_id = uuid4()

    b_name_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    b_name_cfg = _attr(
        "B",
        name="name",
        is_required=False,
        type_descriptor=b_name_desc,
        type_descriptor_id=b_name_desc.id,
    )
    b_cfg = _cfg("B")
    b_cfg.class_config_attribute_configs = [_edge(b_cfg, b_name_cfg, position=0)]

    a_name_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    a_name_cfg = _attr(
        "A",
        name="name",
        is_required=True,
        type_descriptor=a_name_desc,
        type_descriptor_id=a_name_desc.id,
    )
    a_b_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=b_cfg.id
    )
    a_b_cfg = _attr(
        "A",
        name="b",
        is_required=False,
        type_descriptor=a_b_desc,
        type_descriptor_id=a_b_desc.id,
    )
    a_b_id_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    a_b_id_cfg = _attr(
        "A",
        name="b_id",
        is_required=True,
        type_descriptor=a_b_id_desc,
        type_descriptor_id=a_b_id_desc.id,
    )
    a_cfg = _cfg("A")
    a_cfg.class_config_attribute_configs = [
        _edge(a_cfg, a_name_cfg, position=0),
        _edge(a_cfg, a_b_cfg, position=1),
        _edge(a_cfg, a_b_id_cfg, position=2),
    ]

    rel = ClassConfigRelationship(
        relationship_key="a_b",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=a_cfg.id,
        target_class_config_id=b_cfg.id,
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
    a_cfg.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=a_cfg.class_fqn,
            class_config=a_cfg,
            class_config_id=a_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=b_cfg.class_fqn,
            class_config=b_cfg,
            class_config_id=b_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg_id,
        ),
    ]

    # Cross-frontier SoftRef:
    # - source class A is in the active OPG,
    # - target class B is outside the OPG.
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=a_cfg.id,
                is_root=True,
            ),
        ],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )

    A.bind_class_config(a_cfg)
    B.bind_class_config(b_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    a_id = uuid4()
    b_id = uuid4()

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=a_cfg.id,
        root_source_object_id=a_id,
        before_oig_id=uuid4(),
    )

    with set_session(session):
        a = A(id=a_id, name="a", b_id=b_id)
        with scoped_change_collection() as collector:
            collector.record_create(a)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    a_ci_id = _ci_id(
        graph_id=before_oig.id, class_config_id=a_cfg.id, source_object_id=a_id
    )
    created = next(ci for ci in after_oig.class_instances if ci.id == a_ci_id)
    created_attr_ids = [attr.attribute_config_id for attr in created.attributes]
    assert a_b_id_cfg.id in created_attr_ids


def test_created_instance_includes_soft_ref_reverse_foreign_key_attribute() -> None:
    """
    Regression: preserve reverse-owned FK attributes for SoftRef relationships.

    Shape:
    - Parent -> Child is the relationship source/target.
    - Child.parent_id is bound as reverse FOREIGN_KEY.
    - Active OPG includes only Child.
    """
    _bootstrap_models()

    class Child(ORMModel):
        name: str
        parent_id: UUID

    class Parent(ORMModel):
        children: list[Child] = Field(default_factory=list, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:softref-reverse-fk"
    opg_id = uuid4()

    parent_children_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_
    )
    parent_children_cfg = _attr(
        "Parent",
        name="children",
        is_required=False,
        type_descriptor=parent_children_desc,
        type_descriptor_id=parent_children_desc.id,
    )
    parent_cfg = _cfg("Parent")
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, parent_children_cfg, position=0)
    ]

    child_name_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_name_cfg = _attr(
        "Child",
        name="name",
        is_required=True,
        type_descriptor=child_name_desc,
        type_descriptor_id=child_name_desc.id,
    )
    child_parent_id_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_parent_id_cfg = _attr(
        "Child",
        name="parent_id",
        is_required=True,
        type_descriptor=child_parent_id_desc,
        type_descriptor_id=child_parent_id_desc.id,
    )
    child_cfg = _cfg("Child")
    child_cfg.class_config_attribute_configs = [
        _edge(child_cfg, child_name_cfg, position=0),
        _edge(child_cfg, child_parent_id_cfg, position=1),
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=False,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
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
    parent_cfg.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=parent_cfg.class_fqn,
            class_config=parent_cfg,
            class_config_id=parent_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=child_cfg.class_fqn,
            class_config=child_cfg,
            class_config_id=child_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg_id,
        ),
    ]

    # SoftRef reverse FK with cross-frontier source class:
    # - only Child is in active OPG nodes.
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=True,
            )
        ],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    child_id = uuid4()
    parent_id = uuid4()

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=child_cfg.id,
        root_source_object_id=child_id,
        before_oig_id=uuid4(),
    )

    with set_session(session):
        child = Child(id=child_id, name="c", parent_id=parent_id)
        with scoped_change_collection() as collector:
            collector.record_create(child)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    child_ci_id = _ci_id(
        graph_id=before_oig.id, class_config_id=child_cfg.id, source_object_id=child_id
    )
    created = next(ci for ci in after_oig.class_instances if ci.id == child_ci_id)
    created_attr_ids = [attr.attribute_config_id for attr in created.attributes]
    assert child_parent_id_cfg.id in created_attr_ids


def test_created_instance_infers_target_owned_fk_from_relationship_context() -> None:
    """
    Regression: ORM diff rebuilds changed objects independently, so target-owned
    propagation FKs must be recovered from captured relationship references.

    Shape mirrors CodePackageCode -> Code:
    - Parent.children is the forward relationship reference.
    - Child.parent_id is a required target-owned FK in ClassConfig.
    - Child's Python model intentionally does not declare parent_id.
    """
    _bootstrap_models()

    class Child(ORMModel):
        name: str

    class Parent(ORMModel):
        children: list[Child] = Field(default_factory=list, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:strongref-target-fk-context"
    opg_id = uuid4()

    parent_children_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_
    )
    parent_children_cfg = _attr(
        "Parent",
        name="children",
        is_required=False,
        type_descriptor=parent_children_desc,
        type_descriptor_id=parent_children_desc.id,
    )
    parent_cfg = _cfg("Parent")
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, parent_children_cfg, position=0)
    ]

    child_name_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_name_cfg = _attr(
        "Child",
        name="name",
        is_required=True,
        type_descriptor=child_name_desc,
        type_descriptor_id=child_name_desc.id,
    )
    child_parent_id_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_parent_id_cfg = _attr(
        "Child",
        name="parent_id",
        is_required=True,
        type_descriptor=child_parent_id_desc,
        type_descriptor_id=child_parent_id_desc.id,
    )
    child_cfg = _cfg("Child")
    child_cfg.class_config_attribute_configs = [
        _edge(child_cfg, child_name_cfg, position=0),
        _edge(child_cfg, child_parent_id_cfg, position=1),
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        forward_loading_strategy=None,
        reverse_loading_strategy=None,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
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
    parent_cfg.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=parent_cfg.class_fqn,
            class_config=parent_cfg,
            class_config_id=parent_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=child_cfg.class_fqn,
            class_config=child_cfg,
            class_config_id=child_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=rel.relationship_key,
            class_config_relationship=rel,
            class_config_relationship_id=rel.id,
            object_config_graph_id=ocg_id,
        ),
    ]

    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            )
        ],
        object_projection_graph_relationships=[],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    parent_id = uuid4()
    child_id = uuid4()

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=parent_cfg.id,
        root_source_object_id=parent_id,
        before_oig_id=uuid4(),
    )

    with set_session(session):
        parent = Parent(id=parent_id)
        child = Child(id=child_id, name="c")
        parent.children.append(child)
        with scoped_change_collection() as collector:
            collector.record_create(parent)
            collector.record_create(child)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    child_ci_id = _ci_id(
        graph_id=before_oig.id, class_config_id=child_cfg.id, source_object_id=child_id
    )
    created = next(ci for ci in after_oig.class_instances if ci.id == child_ci_id)
    created_attr_ids = [attr.attribute_config_id for attr in created.attributes]
    assert child_parent_id_cfg.id in created_attr_ids


def test_created_instance_ignores_detached_required_fk_relationships() -> None:
    """
    Required-FK retention must ignore detached relationships that reference classes
    outside the active OCG dependency closure.
    """
    _bootstrap_models()

    class A(ORMModel):
        name: str

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:detached-required-fk"
    opg_id = uuid4()

    a_name_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    a_name_cfg = _attr(
        "A",
        name="name",
        is_required=True,
        type_descriptor=a_name_desc,
        type_descriptor_id=a_name_desc.id,
    )
    a_cfg = _cfg("A")
    a_cfg.class_config_attribute_configs = [_edge(a_cfg, a_name_cfg, position=0)]

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
        id=ocg_id,
        name="test",
        description=None,
        hash="0",
        fqn_prefix="test",
        language=CodeLanguage.python,
        object_config_graph_nodes=[],
        object_projection_graphs=[],
    )
    ocg.object_config_graph_nodes = [
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.class_,
            node_key=a_cfg.class_fqn,
            class_config=a_cfg,
            class_config_id=a_cfg.id,
            object_config_graph_id=ocg_id,
        ),
        ObjectConfigGraphNode(
            type=ObjectConfigGraphNodeType.relationship,
            node_key=detached_rel.relationship_key,
            class_config_relationship=detached_rel,
            class_config_relationship_id=detached_rel.id,
            object_config_graph_id=ocg_id,
        ),
    ]

    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=a_cfg.id,
                is_root=True,
            )
        ],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )

    A.bind_class_config(a_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    a_id = uuid4()

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=a_cfg.id,
        root_source_object_id=a_id,
        before_oig_id=uuid4(),
    )

    with set_session(session):
        a = A(id=a_id, name="a")
        with scoped_change_collection() as collector:
            collector.record_create(a)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    a_ci_id = _ci_id(
        graph_id=before_oig.id, class_config_id=a_cfg.id, source_object_id=a_id
    )
    created = next(ci for ci in after_oig.class_instances if ci.id == a_ci_id)
    created_attr_ids = [attr.attribute_config_id for attr in created.attributes]
    assert a_name_cfg.id in created_attr_ids


@pytest.mark.asyncio
async def test_relationship_append_does_not_delete_preexisting_edges() -> None:
    _bootstrap_models()

    class Child(ORMModel):
        name: str | None = None

    class Parent(ORMModel):
        children: list[Child] = Field(default_factory=list, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:no-delete"
    opg_id = uuid4()

    child_cfg = _cfg("Child")
    parent_cfg = _cfg("Parent")

    children_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=child_cfg.id
    )
    children_cfg = _attr(
        "Parent",
        name="children",
        type_descriptor=children_desc,
        type_descriptor_id=children_desc.id,
    )
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, children_cfg, position=0)
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
    )
    rel.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=children_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test-ocg",
        description="test",
        hash="sha256:test",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=parent_cfg.class_fqn,
                class_config=parent_cfg,
                class_config_id=parent_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=child_cfg.class_fqn,
                class_config=child_cfg,
                class_config_id=child_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel.relationship_key,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
                object_config_graph_id=ocg_id,
            ),
        ],
        object_projection_graphs=[],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    parent_id = uuid4()
    child1_id = uuid4()
    child2_id = uuid4()
    before_oig_id = uuid4()
    parent_ci_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=parent_cfg.id,
        source_object_id=parent_id,
    )
    child1_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=child_cfg.id, source_object_id=child1_id
    )
    child2_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=child_cfg.id, source_object_id=child2_id
    )

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=parent_cfg.id,
        root_source_object_id=parent_id,
        before_oig_id=before_oig_id,
        class_instances=[
            ClassInstance(
                id=parent_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=parent_cfg.id,
                source_object_id=parent_id,
                attributes=[],
            ),
            ClassInstance(
                id=child1_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=child_cfg.id,
                source_object_id=child1_id,
                attributes=[],
            ),
            ClassInstance(
                id=child2_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=child_cfg.id,
                source_object_id=child2_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[
            ClassInstanceRelationship(
                object_instance_graph_id=before_oig_id,
                class_config_relationship_id=rel.id,
                source_class_instance_id=parent_ci_id,
                target_class_instance_id=child1_ci_id,
            )
        ],
    )

    with set_session(session):
        parent = Parent(id=parent_id)
        _ = Child(id=child1_id)
        child2 = Child(id=child2_id)

        # Simulate "unhydrated" relationship state: Parent.children is empty even
        # though OIG(pre) contains an existing edge to child1.
        assert parent.children == []

        with scoped_change_collection() as collector:
            parent.children.append(child2)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    # Must not emit a deletion for the pre-existing edge.
    deletes = []
    for root in changes:
        for rel_change in root.class_instance_relationship_changes:
            if rel_change.change.type == ChangeType.delete:
                deletes.append(rel_change)
    assert not any(c.target_class_instance_id == child1_ci_id for c in deletes)

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig, changes=changes, attribute_configs_by_id=None
    )

    edges = {
        (
            e.class_config_relationship_id,
            e.source_class_instance_id,
            e.target_class_instance_id,
        )
        for e in after_oig.class_instance_relationships
    }
    assert (rel.id, parent_ci_id, child1_ci_id) in edges
    assert (rel.id, parent_ci_id, child2_ci_id) in edges


def test_created_snapshot_skips_relationship_create_already_in_prestate() -> None:
    _bootstrap_models()

    class Child(ORMModel):
        name: str | None = None

    class Parent(ORMModel):
        children: list[Child] = Field(default_factory=list, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:direct-snapshot-existing-edge"
    opg_id = uuid4()

    child_cfg = _cfg("Child")
    parent_cfg = _cfg("Parent")

    children_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_,
        class_config_id=child_cfg.id,
    )
    children_cfg = _attr(
        "Parent",
        name="children",
        type_descriptor=children_desc,
        type_descriptor_id=children_desc.id,
    )
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, children_cfg, position=0)
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
    )
    rel.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=children_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    parent_cfg.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test-ocg",
        description="test",
        hash="sha256:test",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_projection_graphs=[],
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=parent_cfg.class_fqn,
                class_config=parent_cfg,
                class_config_id=parent_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=child_cfg.class_fqn,
                class_config=child_cfg,
                class_config_id=child_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel.relationship_key,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
                object_config_graph_id=ocg_id,
            ),
        ],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    parent_id = uuid4()
    child_id = uuid4()
    before_oig_id = uuid4()
    parent_ci_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=parent_cfg.id,
        source_object_id=parent_id,
    )
    child_ci_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=child_cfg.id,
        source_object_id=child_id,
    )
    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=parent_cfg.id,
        root_source_object_id=parent_id,
        before_oig_id=before_oig_id,
        class_instances=[
            ClassInstance(
                id=parent_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=parent_cfg.id,
                source_object_id=parent_id,
                attributes=[],
            ),
            ClassInstance(
                id=child_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=child_cfg.id,
                source_object_id=child_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[
            ClassInstanceRelationship(
                object_instance_graph_id=before_oig_id,
                class_config_relationship_id=rel.id,
                source_class_instance_id=parent_ci_id,
                target_class_instance_id=child_ci_id,
            )
        ],
    )

    parent = Parent(id=parent_id)
    child = Child(id=child_id)
    parent.children.append(child)
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids={parent_id, child_id},
        touched_ids={parent_id, child_id},
        deleted_ids=set(),
        objects_by_id={parent_id: parent, child_id: child},
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    rel_changes = [
        rel_change
        for root in changes
        for rel_change in root.class_instance_relationship_changes
    ]
    assert not any(
        rel_change.change.type == ChangeType.create
        and rel_change.class_config_relationship_id == rel.id
        and rel_change.source_class_instance_id == parent_ci_id
        and rel_change.target_class_instance_id == child_ci_id
        for rel_change in rel_changes
    )


@pytest.mark.asyncio
async def test_relationship_append_uses_deltas_without_scanning_current_list(
    monkeypatch,
) -> None:
    _bootstrap_models()

    class Child(ORMModel):
        name: str | None = None

    class Parent(ORMModel):
        children: list[Child] = Field(default_factory=list, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:delta-set-no-scan"
    opg_id = uuid4()

    child_cfg = _cfg("Child")
    parent_cfg = _cfg("Parent")

    children_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=child_cfg.id
    )
    children_cfg = _attr(
        "Parent",
        name="children",
        type_descriptor=children_desc,
        type_descriptor_id=children_desc.id,
    )
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, children_cfg, position=0)
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
    )
    rel.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=children_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    parent_cfg.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test-ocg",
        description="test",
        hash="sha256:test",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_projection_graphs=[],
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=parent_cfg.class_fqn,
                class_config=parent_cfg,
                class_config_id=parent_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=child_cfg.class_fqn,
                class_config=child_cfg,
                class_config_id=child_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel.relationship_key,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
                object_config_graph_id=ocg_id,
            ),
        ],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    parent_id = uuid4()
    child_id = uuid4()
    before_oig_id = uuid4()
    parent_ci_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=parent_cfg.id,
        source_object_id=parent_id,
    )
    child_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=child_cfg.id, source_object_id=child_id
    )

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=parent_cfg.id,
        root_source_object_id=parent_id,
        before_oig_id=before_oig_id,
        class_instances=[
            ClassInstance(
                id=parent_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=parent_cfg.id,
                source_object_id=parent_id,
                attributes=[],
            ),
            ClassInstance(
                id=child_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=child_cfg.id,
                source_object_id=child_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[],
    )

    with set_session(session):
        parent = Parent(id=parent_id)
        child = Child(id=child_id)

        with scoped_change_collection() as collector:
            parent.children.append(child)
            change_set = collector.snapshot()

    import aware_meta.graph.instance.diff_orm as diff_orm

    def _boom(*_args, **_kwargs):
        raise AssertionError(
            "diff_orm.snapshot_list should not be called for list membership updates"
        )

    monkeypatch.setattr(diff_orm, "snapshot_list", _boom)

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    creates = []
    for root in changes:
        for rel_change in root.class_instance_relationship_changes or []:
            if rel_change.change.type == ChangeType.create:
                creates.append(rel_change)
    assert any(c.target_class_instance_id == child_ci_id for c in creates)


@pytest.mark.asyncio
async def test_relationship_remove_uses_deltas_without_scanning_current_list(
    monkeypatch,
) -> None:
    _bootstrap_models()

    class Child(ORMModel):
        name: str | None = None

    class Parent(ORMModel):
        children: list[Child] = Field(default_factory=list, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:delta-set-remove-no-scan"
    opg_id = uuid4()

    child_cfg = _cfg("Child")
    parent_cfg = _cfg("Parent")

    children_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=child_cfg.id
    )
    children_cfg = _attr(
        "Parent",
        name="children",
        type_descriptor=children_desc,
        type_descriptor_id=children_desc.id,
    )
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, children_cfg, position=0)
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_children",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
    )
    rel.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=children_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]
    parent_cfg.class_config_relationships = [rel]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test-ocg",
        description="test",
        hash="sha256:test",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_projection_graphs=[],
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=parent_cfg.class_fqn,
                class_config=parent_cfg,
                class_config_id=parent_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=child_cfg.class_fqn,
                class_config=child_cfg,
                class_config_id=child_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel.relationship_key,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
                object_config_graph_id=ocg_id,
            ),
        ],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    parent_id = uuid4()
    child1_id = uuid4()
    child2_id = uuid4()
    before_oig_id = uuid4()
    parent_ci_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=parent_cfg.id,
        source_object_id=parent_id,
    )
    child1_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=child_cfg.id, source_object_id=child1_id
    )
    child2_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=child_cfg.id, source_object_id=child2_id
    )

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=parent_cfg.id,
        root_source_object_id=parent_id,
        before_oig_id=before_oig_id,
        class_instances=[
            ClassInstance(
                id=parent_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=parent_cfg.id,
                source_object_id=parent_id,
                attributes=[],
            ),
            ClassInstance(
                id=child1_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=child_cfg.id,
                source_object_id=child1_id,
                attributes=[],
            ),
            ClassInstance(
                id=child2_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=child_cfg.id,
                source_object_id=child2_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[
            ClassInstanceRelationship(
                object_instance_graph_id=before_oig_id,
                class_config_relationship_id=rel.id,
                source_class_instance_id=parent_ci_id,
                target_class_instance_id=child1_ci_id,
            ),
            ClassInstanceRelationship(
                object_instance_graph_id=before_oig_id,
                class_config_relationship_id=rel.id,
                source_class_instance_id=parent_ci_id,
                target_class_instance_id=child2_ci_id,
            ),
        ],
    )

    with set_session(session):
        parent = Parent(id=parent_id)
        child1 = Child(id=child1_id)
        child2 = Child(id=child2_id)
        parent.children.extend([child1, child2])

        with scoped_change_collection() as collector:
            parent.children.remove(child1)
            change_set = collector.snapshot()

    import aware_meta.graph.instance.diff_orm as diff_orm

    def _boom(*_args, **_kwargs):
        raise AssertionError(
            "diff_orm.snapshot_list should not be called for list membership updates"
        )

    monkeypatch.setattr(diff_orm, "snapshot_list", _boom)

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    deletes = []
    for root in changes:
        for rel_change in root.class_instance_relationship_changes or []:
            if rel_change.change.type == ChangeType.delete:
                deletes.append(rel_change)
    assert any(c.target_class_instance_id == child1_ci_id for c in deletes)

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig, changes=changes, attribute_configs_by_id=None
    )

    edges = {
        (
            e.class_config_relationship_id,
            e.source_class_instance_id,
            e.target_class_instance_id,
        )
        for e in after_oig.class_instance_relationships
    }
    assert (rel.id, parent_ci_id, child1_ci_id) not in edges
    assert (rel.id, parent_ci_id, child2_ci_id) in edges


@pytest.mark.asyncio
async def test_created_instances_emit_initial_relationship_edges() -> None:
    _bootstrap_models()

    class Child(ORMModel):
        name: str

    class Parent(ORMModel):
        value: int
        child: Child | None = Field(default=None, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:create-initial-rel"
    opg_id = uuid4()

    child_name_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_name_cfg = _attr(
        "Child",
        name="name",
        type_descriptor=child_name_desc,
        type_descriptor_id=child_name_desc.id,
    )
    child_cfg = _cfg("Child")
    child_cfg.class_config_attribute_configs = [
        _edge(child_cfg, child_name_cfg, position=0)
    ]

    parent_value_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    parent_value_cfg = _attr(
        "Parent",
        name="value",
        type_descriptor=parent_value_desc,
        type_descriptor_id=parent_value_desc.id,
    )
    parent_child_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=child_cfg.id
    )
    parent_child_cfg = _attr(
        "Parent",
        name="child",
        type_descriptor=parent_child_desc,
        type_descriptor_id=parent_child_desc.id,
    )
    parent_cfg = _cfg("Parent")
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, parent_value_cfg, position=0),
        _edge(parent_cfg, parent_child_cfg, position=1),
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_child",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
    )
    rel.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=parent_child_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test-ocg",
        description="test",
        hash="sha256:test",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=parent_cfg.class_fqn,
                class_config=parent_cfg,
                class_config_id=parent_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=child_cfg.class_fqn,
                class_config=child_cfg,
                class_config_id=child_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel.relationship_key,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
                object_config_graph_id=ocg_id,
            ),
        ],
        object_projection_graphs=[],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    parent_id = uuid4()
    child_id = uuid4()
    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=parent_cfg.id,
        root_source_object_id=parent_id,
        before_oig_id=uuid4(),
        name="EMPTY",
    )

    with set_session(session):
        with scoped_change_collection() as collector:
            child = Child(id=child_id, name="child")
            parent = Parent(id=parent_id, value=1, child=child)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    parent_ci_id = _ci_id(
        graph_id=before_oig.id,
        class_config_id=parent_cfg.id,
        source_object_id=parent.id,
    )
    child_ci_id = _ci_id(
        graph_id=before_oig.id, class_config_id=child_cfg.id, source_object_id=child.id
    )
    edges = {
        (
            e.class_config_relationship_id,
            e.source_class_instance_id,
            e.target_class_instance_id,
        )
        for e in after_oig.class_instance_relationships
    }
    assert (rel.id, parent_ci_id, child_ci_id) in edges


@pytest.mark.asyncio
async def test_created_instance_relationship_edges_follow_current_model_ids() -> None:
    _bootstrap_models()

    class Child(ORMModel):
        name: str

    class Parent(ORMModel):
        value: int
        child: Child | None = Field(default=None, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:create-initial-rel:stabilized-id"
    opg_id = uuid4()

    child_name_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_name_cfg = _attr(
        "Child",
        name="name",
        type_descriptor=child_name_desc,
        type_descriptor_id=child_name_desc.id,
    )
    child_cfg = _cfg("Child")
    child_cfg.class_config_attribute_configs = [
        _edge(child_cfg, child_name_cfg, position=0)
    ]

    parent_value_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    parent_value_cfg = _attr(
        "Parent",
        name="value",
        type_descriptor=parent_value_desc,
        type_descriptor_id=parent_value_desc.id,
    )
    parent_child_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=child_cfg.id
    )
    parent_child_cfg = _attr(
        "Parent",
        name="child",
        type_descriptor=parent_child_desc,
        type_descriptor_id=parent_child_desc.id,
    )
    parent_cfg = _cfg("Parent")
    parent_cfg.class_config_attribute_configs = [
        _edge(parent_cfg, parent_value_cfg, position=0),
        _edge(parent_cfg, parent_child_cfg, position=1),
    ]

    rel = ClassConfigRelationship(
        relationship_key="parent_child",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        class_config_id=parent_cfg.id,
        target_class_config_id=child_cfg.id,
    )
    rel.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel.id,
            attribute_config_id=parent_child_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        )
    ]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test-ocg",
        description="test",
        hash="sha256:test",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=parent_cfg.class_fqn,
                class_config=parent_cfg,
                class_config_id=parent_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=child_cfg.class_fqn,
                class_config=child_cfg,
                class_config_id=child_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel.relationship_key,
                class_config_relationship=rel,
                class_config_relationship_id=rel.id,
                object_config_graph_id=ocg_id,
            ),
        ],
        object_projection_graphs=[],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=parent_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )

    Parent.bind_class_config(parent_cfg)
    Child.bind_class_config(child_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    parent_id = uuid4()
    provisional_child_id = uuid4()
    stable_child_id = uuid4()
    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=parent_cfg.id,
        root_source_object_id=parent_id,
        before_oig_id=uuid4(),
        name="EMPTY",
    )

    with set_session(session):
        with scoped_change_collection() as collector:
            child = Child(id=provisional_child_id, name="child")
            child.id = stable_child_id
            parent = Parent(id=parent_id, value=1, child=child)
            change_set = collector.snapshot()

    assert stable_child_id in change_set.created_ids
    assert provisional_child_id not in change_set.created_ids

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    parent_ci_id = _ci_id(
        graph_id=before_oig.id,
        class_config_id=parent_cfg.id,
        source_object_id=parent.id,
    )
    child_ci_id = _ci_id(
        graph_id=before_oig.id,
        class_config_id=child_cfg.id,
        source_object_id=stable_child_id,
    )
    edges = {
        (
            e.class_config_relationship_id,
            e.source_class_instance_id,
            e.target_class_instance_id,
        )
        for e in after_oig.class_instance_relationships
    }
    assert (rel.id, parent_ci_id, child_ci_id) in edges


@pytest.mark.asyncio
async def test_reified_association_edge_emits_two_runtime_relationship_edges() -> None:
    _bootstrap_models()

    class Right(ORMModel):
        name: str | None = None

    class LeftRightEdge(ORMModel):
        left_id: UUID
        right_id: UUID
        right: Right | None = Field(default=None, exclude=True)

    class Left(ORMModel):
        right_edges: list[LeftRightEdge] = Field(default_factory=list, exclude=True)

    ocg_id = uuid4()
    projection_hash = "sha256:test:from-orm:reified-association"
    opg_id = uuid4()

    left_cfg = _cfg("Left")
    right_cfg = _cfg("Right")
    edge_cfg = _cfg("LeftRightEdge")

    edges_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=edge_cfg.id
    )
    right_edges_cfg = _attr(
        "Left",
        "right_edges",
        type_descriptor=edges_desc,
        type_descriptor_id=edges_desc.id,
    )

    fk_desc = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    left_fk_cfg = _attr(
        "LeftRightEdge",
        "left_id",
        type_descriptor=fk_desc,
        type_descriptor_id=fk_desc.id,
    )
    right_fk_cfg = _attr(
        "LeftRightEdge",
        "right_id",
        type_descriptor=fk_desc,
        type_descriptor_id=fk_desc.id,
    )
    right_ref_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.class_, class_config_id=right_cfg.id
    )
    right_ref_cfg = _attr(
        "LeftRightEdge",
        name="right",
        type_descriptor=right_ref_desc,
        type_descriptor_id=right_ref_desc.id,
    )

    left_cfg.class_config_attribute_configs = [
        _edge(left_cfg, right_edges_cfg, position=0),
    ]
    edge_cfg.class_config_attribute_configs = [
        _edge(edge_cfg, left_fk_cfg, position=0),
        _edge(edge_cfg, right_fk_cfg, position=1),
        _edge(edge_cfg, right_ref_cfg, position=2),
    ]

    canonical_rel_id = uuid4()
    rel_source_id = stable_reified_association_source_relationship_id(
        relationship_id=canonical_rel_id
    )
    rel_target_id = stable_reified_association_target_relationship_id(
        relationship_id=canonical_rel_id
    )

    rel_left_edges = ClassConfigRelationship(
        id=rel_source_id,
        relationship_key="left_right_edges",
        relationship_type=ClassConfigRelationshipType.one_to_many,
        forward_required=True,
        class_config_id=left_cfg.id,
        target_class_config_id=edge_cfg.id,
    )
    rel_left_edges.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel_source_id,
            attribute_config_id=right_edges_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        ),
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel_source_id,
            attribute_config_id=left_fk_cfg.id,
            direction=ClassConfigRelationshipDirection.reverse,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        ),
    ]

    rel_edge_right = ClassConfigRelationship(
        id=rel_target_id,
        relationship_key="edge_right",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=True,
        class_config_id=edge_cfg.id,
        target_class_config_id=right_cfg.id,
    )
    rel_edge_right.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel_target_id,
            attribute_config_id=right_ref_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.reference,
        ),
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=rel_target_id,
            attribute_config_id=right_fk_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        ),
    ]

    ocg = ObjectConfigGraph(
        id=ocg_id,
        name="test-ocg",
        description="test",
        hash="sha256:test",
        fqn_prefix="test",
        language=CodeLanguage.aware,
        object_config_graph_nodes=[
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=left_cfg.class_fqn,
                class_config=left_cfg,
                class_config_id=left_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=right_cfg.class_fqn,
                class_config=right_cfg,
                class_config_id=right_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=edge_cfg.class_fqn,
                class_config=edge_cfg,
                class_config_id=edge_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel_left_edges.relationship_key,
                class_config_relationship=rel_left_edges,
                class_config_relationship_id=rel_left_edges.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=rel_edge_right.relationship_key,
                class_config_relationship=rel_edge_right,
                class_config_relationship_id=rel_edge_right.id,
                object_config_graph_id=ocg_id,
            ),
        ],
        object_projection_graphs=[],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash=projection_hash,
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=left_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=edge_cfg.id,
                is_root=False,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=right_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel_source_id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=rel_target_id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )

    Left.bind_class_config(left_cfg)
    Right.bind_class_config(right_cfg)
    LeftRightEdge.bind_class_config(edge_cfg)

    session = Session(branch_id=uuid4(), skip_db=True)
    left_id = uuid4()
    right_id = uuid4()
    edge_id = uuid4()
    before_oig_id = uuid4()
    left_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=left_cfg.id, source_object_id=left_id
    )
    right_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=right_cfg.id, source_object_id=right_id
    )
    edge_ci_id = _ci_id(
        graph_id=before_oig_id, class_config_id=edge_cfg.id, source_object_id=edge_id
    )

    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=left_cfg.id,
        root_source_object_id=left_id,
        before_oig_id=before_oig_id,
        class_instances=[
            ClassInstance(
                id=left_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=left_cfg.id,
                source_object_id=left_id,
                attributes=[],
            ),
            ClassInstance(
                id=right_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=right_cfg.id,
                source_object_id=right_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[],
    )

    with set_session(session):
        edge = LeftRightEdge(id=edge_id, left_id=left_id, right_id=right_id)

        with scoped_change_collection() as collector:
            collector.record_create(edge)
            change_set = collector.snapshot()

    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )

    after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=after_oig,
        changes=changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    edges = {
        (
            e.class_config_relationship_id,
            e.source_class_instance_id,
            e.target_class_instance_id,
        )
        for e in after_oig.class_instance_relationships
    }
    assert (rel_source_id, left_ci_id, edge_ci_id) in edges
    assert (rel_target_id, edge_ci_id, right_ci_id) in edges
    assert not any(rel_id == canonical_rel_id for rel_id, _src, _tgt in edges)

    assert any(
        ci.id == edge_ci_id and ci.class_config_id == edge_cfg.id
        for ci in after_oig.class_instances
    )
