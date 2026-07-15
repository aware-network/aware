from __future__ import annotations

import copy
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import Field


# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage

# History Api
from aware_history_ontology.change.change import Change
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
from aware_meta_ontology.class_.class_instance_relationship_change import (
    ClassInstanceRelationshipChange,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
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
from aware_meta_ontology.stable_ids import stable_class_instance_id


# Meta Runtime
from aware_meta.graph.instance.apply import (
    apply_object_instance_graph_body_draft,
    apply_object_instance_graph_changes,
)
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
    summarize_commit_perf_events,
)
from aware_meta.graph.instance.diff_orm import (
    OrmChangeTranslationError,
    _try_direct_class_instance_create_draft,
    build_object_instance_graph_changes_from_orm_change_set,
    build_object_instance_graph_evidence_from_orm_change_set,
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
from aware_orm.session.autobind import disable_autobind
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


def test_collected_object_class_collision_is_a_typed_translation_failure() -> None:
    _bootstrap_models()

    class Root(ORMModel):
        name: str

    class CollidingRuntimeObject(ORMModel):
        key: str

    root_cfg = _cfg("Root")
    collision_cfg = _cfg("CollidingRuntimeObject")
    Root.bind_class_config(root_cfg)
    CollidingRuntimeObject.bind_class_config(collision_cfg)

    ocg_id = uuid4()
    opg_id = uuid4()
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
                node_key=root_cfg.class_fqn,
                class_config=root_cfg,
                class_config_id=root_cfg.id,
                object_config_graph_id=ocg_id,
            )
        ],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="sha256:test:collected-object-class-collision",
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=root_cfg.id,
                is_root=True,
            )
        ],
        object_projection_graph_edges=[],
    )
    root_id = uuid4()
    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=root_cfg.id,
        root_source_object_id=root_id,
    )
    colliding_object = CollidingRuntimeObject.model_construct(
        id=root_id,
        key="runtime-object",
    )
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=set(),
        touched_ids={root_id},
        deleted_ids=set(),
        objects_by_id={root_id: colliding_object},
        scalar_fields_by_id={root_id: {"key"}},
        list_fields_by_id={},
        scalar_baseline={(root_id, "key"): "before"},
        list_baseline={},
        list_added={},
        list_removed={},
    )

    with pytest.raises(
        OrmChangeTranslationError,
        match=(
            "Collected ORM object class does not match pre-state identity: "
            f"source_object_id={root_id} "
            f"expected_class_config_id={root_cfg.id} "
            f"actual_class_config_id={collision_cfg.id}"
        ),
    ):
        build_object_instance_graph_changes_from_orm_change_set(
            before_oig=before_oig,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            ocg=ocg,
            opg=opg,
            change_set=change_set,
        )


def test_scalar_relationship_replacement_rejects_unresolved_external_target() -> None:
    _bootstrap_models()

    class CommitPin(ORMModel):
        graph_hash: str | None = None

    class RuntimePackage(ORMModel):
        object_instance_graph_commit_id: UUID | None = None

    ocg_id = uuid4()
    opg_id = uuid4()
    commit_cfg = _cfg("CommitPin")
    commit_hash_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    commit_hash_cfg = _attr(
        "CommitPin",
        name="graph_hash",
        is_required=False,
        type_descriptor=commit_hash_desc,
        type_descriptor_id=commit_hash_desc.id,
    )
    commit_cfg.class_config_attribute_configs = [
        _edge(commit_cfg, commit_hash_cfg, position=0)
    ]

    runtime_commit_id_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    runtime_commit_id_cfg = _attr(
        "RuntimePackage",
        name="object_instance_graph_commit_id",
        is_required=False,
        type_descriptor=runtime_commit_id_desc,
        type_descriptor_id=runtime_commit_id_desc.id,
    )
    runtime_cfg = _cfg("RuntimePackage")
    runtime_cfg.class_config_attribute_configs = [
        _edge(runtime_cfg, runtime_commit_id_cfg, position=0)
    ]

    relationship = ClassConfigRelationship(
        relationship_key="runtime_package_commit",
        relationship_type=ClassConfigRelationshipType.many_to_one,
        forward_required=False,
        class_config_id=runtime_cfg.id,
        target_class_config_id=commit_cfg.id,
        class_config_relationship_attributes=[],
    )
    relationship.class_config_relationship_attributes = [
        ClassConfigRelationshipAttribute(
            class_config_relationship_id=relationship.id,
            attribute_config_id=runtime_commit_id_cfg.id,
            direction=ClassConfigRelationshipDirection.forward,
            role=ClassConfigRelationshipAttributeRole.foreign_key,
        )
    ]
    runtime_cfg.class_config_relationships = [relationship]

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
                node_key=runtime_cfg.class_fqn,
                class_config=runtime_cfg,
                class_config_id=runtime_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.class_,
                node_key=commit_cfg.class_fqn,
                class_config=commit_cfg,
                class_config_id=commit_cfg.id,
                object_config_graph_id=ocg_id,
            ),
            ObjectConfigGraphNode(
                type=ObjectConfigGraphNodeType.relationship,
                node_key=relationship.relationship_key,
                class_config_relationship=relationship,
                class_config_relationship_id=relationship.id,
                object_config_graph_id=ocg_id,
            ),
        ],
    )
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="sha256:test:unresolved-external-target",
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=runtime_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=commit_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=relationship.id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            )
        ],
    )

    RuntimePackage.bind_class_config(runtime_cfg)
    CommitPin.bind_class_config(commit_cfg)
    runtime_package_id = uuid4()
    old_commit_id = uuid4()
    new_commit_id = uuid4()
    before_oig_id = uuid4()
    runtime_ci_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=runtime_cfg.id,
        source_object_id=runtime_package_id,
    )
    old_commit_ci_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=commit_cfg.id,
        source_object_id=old_commit_id,
    )
    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=runtime_cfg.id,
        root_source_object_id=runtime_package_id,
        before_oig_id=before_oig_id,
        class_instances=[
            ClassInstance(
                id=runtime_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=runtime_cfg.id,
                source_object_id=runtime_package_id,
                attributes=[],
            ),
            ClassInstance(
                id=old_commit_ci_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=commit_cfg.id,
                source_object_id=old_commit_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[
            ClassInstanceRelationship(
                object_instance_graph_id=before_oig_id,
                class_config_relationship_id=relationship.id,
                source_class_instance_id=runtime_ci_id,
                target_class_instance_id=old_commit_ci_id,
            )
        ],
    )
    runtime_package = RuntimePackage.model_construct(
        id=runtime_package_id,
        object_instance_graph_commit_id=new_commit_id,
    )
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=set(),
        touched_ids={runtime_package_id},
        deleted_ids=set(),
        objects_by_id={runtime_package_id: runtime_package},
        scalar_fields_by_id={runtime_package_id: {"object_instance_graph_commit_id"}},
        list_fields_by_id={},
        scalar_baseline={
            (runtime_package_id, "object_instance_graph_commit_id"): old_commit_id
        },
        list_baseline={},
        list_added={},
        list_removed={},
    )

    with pytest.raises(
        OrmChangeTranslationError,
        match=(
            "operation=create_scalar_target.*"
            f"unresolved_source_object_id={new_commit_id}"
        ),
    ):
        build_object_instance_graph_changes_from_orm_change_set(
            before_oig=before_oig,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            ocg=ocg,
            opg=opg,
            change_set=change_set,
        )


def test_created_instance_includes_soft_ref_foreign_key_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    untraced_changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )
    recorder = CommitPerfTraceRecorder(
        default_category="meta.runtime.handler_execution"
    )
    with active_commit_perf_trace(recorder):
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
    untraced_after_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=untraced_after_oig,
        changes=untraced_changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )
    assert compute_hash(after_oig, build_index(after_oig)) == compute_hash(
        untraced_after_oig,
        build_index(untraced_after_oig),
    )

    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    build_prefix = (
        "handler_execution.orm_change_translation."
        "class_instance_changes.build_profile"
    )
    emission_prefix = (
        "handler_execution.orm_change_translation."
        "class_instance_changes.emission_profile"
    )
    assert trace_summary[f"{build_prefix}.attribute_link_input"]["count"] == 3
    assert trace_summary[f"{build_prefix}.source_attribute_lookup"]["count"] == 2
    assert trace_summary[f"{build_prefix}.attribute_built"]["count"] == 2
    assert trace_summary[f"{build_prefix}.build_attributes"]["total_ms"] >= 0.0
    assert trace_summary[f"{build_prefix}.link_attributes"]["total_ms"] >= 0.0
    assert trace_summary[f"{emission_prefix}.candidate_input"]["count"] == 1
    assert trace_summary[f"{emission_prefix}.update_candidate"]["count"] == 1
    assert (
        trace_summary[f"{emission_prefix}.update_attribute_membership_path"]["count"]
        == 1
    )
    assert trace_summary[f"{emission_prefix}.change_emitted"]["count"] == 1
    assert (
        trace_summary[f"{emission_prefix}.update_attribute_membership"]["total_ms"]
        >= 0.0
    )
    a_ci_id = _ci_id(
        graph_id=before_oig.id, class_config_id=a_cfg.id, source_object_id=a_id
    )
    created = next(ci for ci in after_oig.class_instances if ci.id == a_ci_id)
    created_attr_ids = [attr.attribute_config_id for attr in created.attributes]
    assert a_b_id_cfg.id in created_attr_ids

    direct_before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=b_cfg.id,
        root_source_object_id=b_id,
        before_oig_id=uuid4(),
    )
    semantic_direct_changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=direct_before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )
    semantic_direct_after_oig = copy.deepcopy(direct_before_oig)
    apply_object_instance_graph_changes(
        graph=semantic_direct_after_oig,
        changes=semantic_direct_changes,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
    )

    def fail_full_builder(**_kwargs):
        raise AssertionError("direct created-instance evidence used full builder")

    monkeypatch.setattr(
        "aware_meta.graph.instance.diff_orm.build_class_instance",
        fail_full_builder,
    )
    evidence = build_object_instance_graph_evidence_from_orm_change_set(
        before_oig=direct_before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=change_set,
    )
    assert evidence.changes == ()
    assert evidence.body_draft is not None
    direct_after_oig = copy.deepcopy(direct_before_oig)
    apply_object_instance_graph_body_draft(
        graph=direct_after_oig,
        body_draft=evidence.body_draft,
        attribute_configs_by_id=_attribute_configs_by_id(ocg),
        class_configs_by_id={a_cfg.id: a_cfg, b_cfg.id: b_cfg},
    )
    direct_a_ci_id = _ci_id(
        graph_id=direct_before_oig.id,
        class_config_id=a_cfg.id,
        source_object_id=a_id,
    )
    direct_created = next(
        ci for ci in direct_after_oig.class_instances if ci.id == direct_a_ci_id
    )
    assert a_b_id_cfg.id in {
        attribute.attribute_config_id for attribute in direct_created.attributes
    }
    assert compute_hash(
        direct_after_oig, build_index(direct_after_oig)
    ) == compute_hash(
        semantic_direct_after_oig,
        build_index(semantic_direct_after_oig),
    )


def test_direct_created_instance_draft_rejects_complex_descriptor_atomically() -> None:
    _bootstrap_models()

    class ComplexValue(ORMModel):
        payload: dict[str, str]

    payload_descriptor = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.mapping
    )
    payload_config = _attr(
        "ComplexValue",
        name="payload",
        is_required=True,
        type_descriptor=payload_descriptor,
        type_descriptor_id=payload_descriptor.id,
    )
    class_config = _cfg("ComplexValue")
    class_config.class_config_attribute_configs = [
        _edge(class_config, payload_config, position=0)
    ]
    ComplexValue.bind_class_config(class_config)
    source = ComplexValue(id=uuid4(), payload={"key": "value"})

    assert (
        _try_direct_class_instance_create_draft(
            object_instance_graph_id=uuid4(),
            class_config=class_config,
            source=source,
            relationship_attribute_config_ids=None,
            include_relationship_attribute_config_ids=None,
            enum_option_resolver=None,
            union_selections=None,
            created_at=datetime.now(UTC),
        )
        is None
    )


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


def test_relationship_context_skips_unchanged_reference_fields() -> None:
    """
    Relationship-context FK inference is needed for created objects and changed
    relationship fields only. Scalar-only updates must not scan unrelated
    reference lists on every changed object.
    """
    _bootstrap_models()

    class Child(ORMModel):
        name: str | None = None

    class Parent(ORMModel):
        name: str
        children: list[Child] = Field(default_factory=list, exclude=True)

        def try_field_value(self, name: str, *, include_unset: bool = False):
            if name == "children":
                raise AssertionError(
                    "unchanged relationship reference field must not be read"
                )
            return super().try_field_value(name, include_unset=include_unset)

    ocg_id = uuid4()
    opg_id = uuid4()

    parent_name_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    parent_name_cfg = _attr(
        "Parent",
        name="name",
        is_required=True,
        type_descriptor=parent_name_desc,
        type_descriptor_id=parent_name_desc.id,
    )
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
        _edge(parent_cfg, parent_name_cfg, position=0),
        _edge(parent_cfg, parent_children_cfg, position=1),
    ]

    child_name_desc = AttributeTypeDescriptor(
        kind=AttributeTypeDescriptorKind.primitive
    )
    child_name_cfg = _attr(
        "Child",
        name="name",
        is_required=False,
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
        projection_hash="sha256:test:from-orm:context-skip-unchanged-ref",
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
    with set_session(session):
        parent = Parent(id=uuid4(), name="before")
        with scoped_change_collection() as collector:
            parent.name = "after"
            change_set = collector.snapshot()

    import aware_meta.graph.instance.diff_orm as diff_orm

    index = diff_orm._build_ocg_index(ocg=ocg, opg=opg)
    assert (
        diff_orm._relationship_context_values_by_object_id(
            change_set=change_set,
            index=index,
        )
        == {}
    )


def test_injected_runtime_index_derives_metadata_from_projection_closure() -> None:
    selected_config = _cfg("Selected")
    unrelated_config = _cfg("Unrelated")
    descriptor = AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)
    shared_attribute = _attr(
        "Selected",
        "name",
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
    )
    selected_config.class_config_attribute_configs = [
        _edge(selected_config, shared_attribute, position=0)
    ]
    unrelated_config.class_config_attribute_configs = [
        _edge(unrelated_config, shared_attribute, position=0)
    ]
    ocg_id = uuid4()
    opg_id = uuid4()
    ocg = ObjectConfigGraph.model_construct(
        id=ocg_id,
        object_config_graph_nodes=[],
        object_config_graph_relationships=[],
    )
    opg = ObjectProjectionGraph.model_construct(
        id=opg_id,
        object_config_graph_id=ocg_id,
        projection_hash="sha256:test:projection-closure",
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode.model_construct(
                object_projection_graph_id=opg_id,
                class_config_id=selected_config.id,
                is_root=True,
            )
        ],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )

    import aware_meta.graph.instance.diff_orm as diff_orm

    class_configs_by_id = {
        selected_config.id: selected_config,
        unrelated_config.id: unrelated_config,
    }
    relationships_by_id: dict[UUID, ClassConfigRelationship] = {}
    index = diff_orm._build_ocg_index(
        ocg=ocg,
        opg=opg,
        class_configs_by_id=class_configs_by_id,
        relationships_by_id=relationships_by_id,
    )
    cache = diff_orm.OrmChangeTranslationIndexCache(
        object_config_graph=ocg,
        class_configs_by_id=class_configs_by_id,
        relationships_by_id=relationships_by_id,
    )
    assert cache.get(ocg=ocg, opg=opg) is None
    assert cache.relationship_projection_context(ocg=ocg, opg=opg) is None
    cached_index = cache.build(ocg=ocg, opg=opg)

    assert index.opg_class_config_ids == frozenset({selected_config.id})
    assert index.owner_class_config_by_attribute_id == {
        shared_attribute.id: selected_config.id
    }
    assert unrelated_config.id in index.class_configs_by_id
    assert cached_index == index
    assert cache.get(ocg=ocg, opg=opg) is cached_index
    relationship_context = cache.relationship_projection_context(ocg=ocg, opg=opg)
    assert relationship_context is not None
    assert relationship_context.opg_class_config_ids == frozenset({selected_config.id})
    assert relationship_context.relationship_attribute_ids_by_cc_id == {
        selected_config.id: set()
    }
    assert relationship_context.include_relationship_attribute_ids_by_cc_id == {}
    copied_opg = opg.model_copy(deep=False)
    assert cache.get(ocg=ocg, opg=copied_opg) is cached_index
    changed_projection_opg = opg.model_copy(
        update={"projection_hash": "sha256:test:projection-closure:changed"},
        deep=False,
    )
    assert cache.get(ocg=ocg, opg=changed_projection_opg) is None
    assert (
        cache.relationship_projection_context(
            ocg=ocg,
            opg=changed_projection_opg,
        )
        is None
    )
    with pytest.raises(
        OrmChangeTranslationError,
        match="belongs to a different ObjectConfigGraph",
    ):
        cache.get(
            ocg=ocg.model_copy(deep=False),
            opg=opg,
        )


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

    recorder = CommitPerfTraceRecorder(
        default_category="meta.runtime.handler_execution"
    )
    with active_commit_perf_trace(recorder):
        changes = build_object_instance_graph_changes_from_orm_change_set(
            before_oig=before_oig,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            ocg=ocg,
            opg=opg,
            change_set=change_set,
        )

    trace_summary = summarize_commit_perf_events(recorder.snapshot_json())
    assert (
        trace_summary[
            "handler_execution.orm_change_translation."
            "class_instance_changes.candidate_pruned_relationship_only"
        ]["count"]
        == 1
    )
    assert (
        trace_summary[
            "handler_execution.orm_change_translation."
            "class_instance_changes.candidate_selected"
        ]["count"]
        == 1
    )
    assert all(not root.class_instance_changes for root in changes)

    index = diff_orm._build_ocg_index(ocg=ocg, opg=opg)
    before_by_source_id = {
        class_instance.source_object_id: class_instance
        for class_instance in before_oig.class_instances
    }
    relationship_only_selection = diff_orm._select_class_instance_change_candidates(
        change_set=change_set,
        index=index,
        before_by_source_id=before_by_source_id,
    )
    assert parent_id in relationship_only_selection.pruned_relationship_only_ids
    assert parent_id not in relationship_only_selection.selected_ids
    mixed_change_set = replace(
        change_set,
        scalar_fields_by_id={parent_id: {"name"}},
        scalar_baseline={(parent_id, "name"): "before"},
    )
    mixed_selection = diff_orm._select_class_instance_change_candidates(
        change_set=mixed_change_set,
        index=index,
        before_by_source_id=before_by_source_id,
    )
    assert parent_id in mixed_selection.selected_ids
    assert parent_id not in mixed_selection.pruned_relationship_only_ids
    unpruned_changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        ocg=ocg,
        opg=opg,
        change_set=mixed_change_set,
    )

    def _member_change_signatures(
        root_changes: list[ObjectInstanceGraphChange],
    ) -> tuple[set[tuple[ChangeType, UUID]], set[tuple[ChangeType, UUID, UUID, UUID]]]:
        return (
            {
                (class_change.change.type, class_change.class_instance_id)
                for root_change in root_changes
                for class_change in root_change.class_instance_changes
            },
            {
                (
                    relationship_change.change.type,
                    relationship_change.class_config_relationship_id,
                    relationship_change.source_class_instance_id,
                    relationship_change.target_class_instance_id,
                )
                for root_change in root_changes
                for relationship_change in (
                    root_change.class_instance_relationship_changes
                )
            },
        )

    assert _member_change_signatures(changes) == _member_change_signatures(
        unpruned_changes
    )
    pruned_replay = copy.deepcopy(before_oig)
    unpruned_replay = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=pruned_replay,
        changes=changes,
        attribute_configs_by_id=None,
    )
    apply_object_instance_graph_changes(
        graph=unpruned_replay,
        changes=unpruned_changes,
        attribute_configs_by_id=None,
    )
    assert compute_hash(pruned_replay, build_index(pruned_replay)) == compute_hash(
        unpruned_replay,
        build_index(unpruned_replay),
    )

    retained_index = replace(
        index,
        required_fk_include_relationship_attribute_ids_by_cc_id={
            parent_cfg.id: {children_cfg.id}
        },
    )
    retained_selection = diff_orm._select_class_instance_change_candidates(
        change_set=change_set,
        index=retained_index,
        before_by_source_id=before_by_source_id,
    )
    assert parent_id in retained_selection.selected_ids
    assert parent_id not in retained_selection.pruned_relationship_only_ids

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
    deleted_class_instance_ids = set()
    for root in changes:
        for class_change in root.class_instance_changes or []:
            if class_change.change.type == ChangeType.delete:
                deleted_class_instance_ids.add(class_change.class_instance_id)
        for rel_change in root.class_instance_relationship_changes or []:
            if rel_change.change.type == ChangeType.delete:
                deletes.append(rel_change)
    assert any(c.target_class_instance_id == child1_ci_id for c in deletes)
    assert deleted_class_instance_ids == {child1_ci_id}

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
    remaining_class_instance_ids = {
        class_instance.id for class_instance in after_oig.class_instances
    }
    assert child1_ci_id not in remaining_class_instance_ids
    assert child2_ci_id in remaining_class_instance_ids


def test_direct_relationship_closure_preserves_alternate_reachable_path() -> None:
    import aware_meta.graph.instance.diff_orm as diff_orm

    forward_relationship_id = uuid4()
    branch_relationship_id = uuid4()
    root_id = uuid4()
    left_id = uuid4()
    right_id = uuid4()
    child_id = uuid4()
    directions = {
        forward_relationship_id: ClassConfigRelationshipDirection.forward,
        branch_relationship_id: ClassConfigRelationshipDirection.forward,
    }
    relationship_keys = {
        (forward_relationship_id, root_id, left_id),
        (branch_relationship_id, root_id, right_id),
        (forward_relationship_id, left_id, child_id),
        (branch_relationship_id, right_id, child_id),
    }

    reachable = diff_orm._reachable_class_instance_ids(
        root_class_instance_id=root_id,
        relationship_keys=(
            relationship_keys - {(forward_relationship_id, left_id, child_id)}
        ),
        traversal_direction_by_relationship_id=directions,
    )

    assert child_id in reachable


def test_direct_relationship_closure_emits_complete_detached_subtree() -> None:
    import aware_meta.graph.instance.diff_orm as diff_orm

    ocg_id = uuid4()
    opg_id = uuid4()
    before_oig_id = uuid4()
    root_cfg = _cfg("Root")
    child_cfg = _cfg("Child")
    leaf_cfg = _cfg("Leaf")
    root_child_relationship_id = uuid4()
    child_leaf_relationship_id = uuid4()
    opg = ObjectProjectionGraph(
        id=opg_id,
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="sha256:test:detached-subtree",
        object_config_graph_id=ocg_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=root_cfg.id,
                is_root=True,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=child_cfg.id,
                is_root=False,
            ),
            ObjectProjectionGraphNode(
                object_projection_graph_id=opg_id,
                class_config_id=leaf_cfg.id,
                is_root=False,
            ),
        ],
        object_projection_graph_edges=[
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=root_child_relationship_id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
            ObjectProjectionGraphEdge(
                object_projection_graph_id=opg_id,
                class_config_relationship_id=child_leaf_relationship_id,
                traversal_direction=ClassConfigRelationshipDirection.forward,
            ),
        ],
    )
    root_source_id = uuid4()
    child_source_id = uuid4()
    leaf_source_id = uuid4()
    root_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=root_cfg.id,
        source_object_id=root_source_id,
    )
    child_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=child_cfg.id,
        source_object_id=child_source_id,
    )
    leaf_id = _ci_id(
        graph_id=before_oig_id,
        class_config_id=leaf_cfg.id,
        source_object_id=leaf_source_id,
    )
    before_oig = _make_before_oig(
        ocg_id=ocg_id,
        opg=opg,
        root_class_config_id=root_cfg.id,
        root_source_object_id=root_source_id,
        before_oig_id=before_oig_id,
        class_instances=[
            ClassInstance(
                id=root_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=root_cfg.id,
                source_object_id=root_source_id,
                attributes=[],
            ),
            ClassInstance(
                id=child_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=child_cfg.id,
                source_object_id=child_source_id,
                attributes=[],
            ),
            ClassInstance(
                id=leaf_id,
                object_instance_graph_id=before_oig_id,
                class_config_id=leaf_cfg.id,
                source_object_id=leaf_source_id,
                attributes=[],
            ),
        ],
        class_instance_relationships=[
            ClassInstanceRelationship(
                object_instance_graph_id=before_oig_id,
                class_config_relationship_id=root_child_relationship_id,
                source_class_instance_id=root_id,
                target_class_instance_id=child_id,
            ),
            ClassInstanceRelationship(
                object_instance_graph_id=before_oig_id,
                class_config_relationship_id=child_leaf_relationship_id,
                source_class_instance_id=child_id,
                target_class_instance_id=leaf_id,
            ),
        ],
    )
    with disable_autobind():
        delete_change = Change(
            key="relationship:root-child:delete",
            type=ChangeType.delete,
            change_deltas=[],
            created_at=datetime.now(UTC),
        )
        relationship_change = ClassInstanceRelationshipChange(
            change=delete_change,
            change_id=delete_change.id,
            class_config_relationship_id=root_child_relationship_id,
            source_class_instance_id=root_id,
            target_class_instance_id=child_id,
        )

    closure_changes = diff_orm._build_detached_class_instance_delete_changes(
        before_oig=before_oig,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        opg=opg,
        relationship_changes=[relationship_change],
        created_at=datetime.now(UTC),
    )
    deleted_class_instance_ids = {
        class_change.class_instance_id
        for root_change in closure_changes
        for class_change in root_change.class_instance_changes
        if class_change.change.type == ChangeType.delete
    }
    deleted_relationship_keys = {
        (
            relationship.class_config_relationship_id,
            relationship.source_class_instance_id,
            relationship.target_class_instance_id,
        )
        for root_change in closure_changes
        for relationship in root_change.class_instance_relationship_changes
        if relationship.change.type == ChangeType.delete
    }
    assert deleted_class_instance_ids == {child_id, leaf_id}
    assert deleted_relationship_keys == {
        (root_child_relationship_id, root_id, child_id),
        (child_leaf_relationship_id, child_id, leaf_id),
    }

    replay_oig = copy.deepcopy(before_oig)
    apply_object_instance_graph_changes(
        graph=replay_oig,
        changes=closure_changes,
        attribute_configs_by_id=None,
    )
    assert {class_instance.id for class_instance in replay_oig.class_instances} == {
        root_id
    }
    assert replay_oig.class_instance_relationships == []


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
            changes = build_object_instance_graph_changes_from_orm_change_set(
                before_oig=before_oig,
                object_instance_graph_identity_id=_TEST_OIGI_ID,
                ocg=ocg,
                opg=opg,
                change_set=change_set,
            )
            after_translation_change_set = collector.snapshot()

    assert stable_child_id in change_set.created_ids
    assert provisional_child_id not in change_set.created_ids
    assert after_translation_change_set == change_set

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
