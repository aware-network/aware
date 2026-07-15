from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.change.change_enums import ChangeType
from aware_history.stable_ids import stable_lane_id
from aware_history_ontology.stable_ids import stable_commit_id
from aware_meta.graph.config.stable_ids import stable_class_instance_id
from aware_meta.graph.instance.commit.contract import (
    ObjectInstanceGraphCommitEnvelope,
    ObjectInstanceGraphCommitIdentitySidecar,
    OigiHistoryDomainCommitProjection,
)
from aware_meta.graph.instance.commit.body_codec import (
    OigCommitBodyChangeRefDraft,
    OigCommitBodyClassInstanceChangeDraft,
    OigCommitBodyDraft,
    OigCommitBodyRootChangeDraft,
    build_oig_commit_body_from_draft,
    object_instance_graph_changes_from_body,
)
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
)
from aware_meta.attribute.instance.builder import build_attribute
from aware_meta.attribute.instance.value.builder import fingerprint_attribute_value
from aware_meta.class_.instance.handlers import link_attribute
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.commit import identity_history as identity_history_module
from aware_meta.runtime.commit.identity_history import (
    _build_oigi_history_changes_from_projection,
    _OIGI_STATIC_DIRECT_CONTEXT_CACHE,
    _OigiHistoryDirectProjectionUnsupported,
    _OigiHistoryProjectionResult,
    _oigi_primitive_leaf_payload_parts,
    _oigi_primitive_leaf_value_fingerprint,
    _project_oigi_history_projection,
    _record_oigi_direct_state_row_replay_mismatch_diagnostics,
    _try_build_oigi_enum_union_create_body_draft,
    upsert_object_instance_graph_identity_history_from_domain_commit,
)
from aware_meta.test_support import make_attribute_config, make_class_attribute_edge
from aware_meta_ontology.attribute.attribute import Attribute
from aware_meta_ontology.attribute.attribute_enums import AttributeCollectionType
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
    AttributeTypeDescriptorRole as Role,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_link import (
    AttributeTypeDescriptorLink,
)
from aware_meta_ontology.attribute.attribute_value import AttributeValue
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_branch_id,
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_lane_id,
)
from aware_orm.models.introspection import MappingModelSource
from aware_orm.session.change_collector import ORMChangeSet


def _change_set(
    *,
    created_ids: frozenset[UUID] = frozenset(),
    touched_ids: frozenset[UUID] = frozenset(),
    deleted_ids: frozenset[UUID] = frozenset(),
    objects_by_id: dict[UUID, object] | None = None,
) -> ORMChangeSet:
    return ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=created_ids,
        touched_ids=touched_ids,
        deleted_ids=deleted_ids,
        objects_by_id=objects_by_id or {},
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )


def test_oigi_history_changed_targets_reuse_attribute_plan_per_class(
    monkeypatch,
) -> None:
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_test.Thing",
        name="Thing",
    )
    source_ids = (uuid4(), uuid4())
    projection = _OigiHistoryProjectionResult(
        change_set=_change_set(
            touched_ids=frozenset(source_ids),
            objects_by_id={
                source_id: MappingModelSource(
                    id=source_id,
                    class_config_id=class_config.id,
                    values={},
                )
                for source_id in source_ids
            },
        ),
        session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
        root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    context = identity_history_module._OigiHistoryDirectProjectionContext(
        class_configs_by_id={class_config.id: class_config},
        relationship_attribute_ids_by_cc_id={},
        include_relationship_attribute_ids_by_cc_id={},
        opg_class_config_ids=frozenset({class_config.id}),
        before_class_instances_by_id={},
        attribute_plans_by_class_config_id={},
    )
    before_oig = ObjectInstanceGraph.model_construct(
        id=uuid4(),
        class_instances=[],
    )
    planner_calls = 0
    original_planner = identity_history_module.plan_class_instance_attribute_links

    def _record_planner(**kwargs):
        nonlocal planner_calls
        planner_calls += 1
        return original_planner(**kwargs)

    monkeypatch.setattr(
        identity_history_module,
        "plan_class_instance_attribute_links",
        _record_planner,
    )

    targets = (
        identity_history_module._build_oigi_history_changed_class_instance_targets(
            context=context,
            before_oig=before_oig,
            projection=projection,
        )
    )

    assert len(targets.changed_targets) == 2
    assert planner_calls == 1
    assert (
        targets.changed_targets[0].attribute_plan
        is targets.changed_targets[1].attribute_plan
    )
    assert context.attribute_plans_by_class_config_id == {
        class_config.id: targets.changed_targets[0].attribute_plan
    }


def test_oigi_history_head_state_hash_uses_materialized_index(monkeypatch) -> None:
    graph = ObjectInstanceGraph.model_construct(
        hash="sha256:test:indexed-state",
        class_instances=[],
        class_instance_relationships=[],
    )

    def _fail_state_index_rebuild(_graph):
        raise AssertionError("state index rebuild should not run")

    monkeypatch.setattr(
        identity_history_module,
        "build_commit_state_index",
        _fail_state_index_rebuild,
    )

    mismatch = identity_history_module._oigi_history_head_state_hash_mismatch(
        before_oig=graph,
        materialized_indexes={
            identity_history_module.COMMIT_STATE_HASH_INDEX_KEY: (
                "sha256:test:indexed-state"
            ),
        },
    )

    assert mismatch is None


@pytest.mark.asyncio
async def test_oigi_history_minimal_change_set_skips_session_reification() -> None:
    object_config_graph_id = uuid4()
    root_class_config = ClassConfig(
        id=uuid4(),
        class_fqn="aware_meta.graph.instance.ObjectInstanceGraphIdentity",
        name="ObjectInstanceGraphIdentity",
    )
    domain_oig_id = uuid4()
    oigi_id = uuid4()
    object_projection_graph_identity_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    parent_domain_commit_id = uuid4()
    head_domain_commit_id = uuid4()
    parent_wrapper_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=oigi_id,
        commit_id=parent_domain_commit_id,
    )
    oigb_id = stable_object_instance_graph_branch_id(
        object_instance_graph_identity_id=oigi_id,
        branch_id=domain_branch_id,
    )
    oigl_id = stable_object_instance_graph_lane_id(
        object_instance_graph_branch_id=oigb_id,
        lane_id=lane_id,
    )
    root_class_instance = _class_instance(
        object_instance_graph_id=oigi_id,
        class_config_id=root_class_config.id,
        source_object_id=oigi_id,
    )
    branch_class_instance = _class_instance(
        object_instance_graph_id=oigi_id,
        class_config_id=uuid4(),
        source_object_id=domain_branch_id,
    )
    lane_class_instance = _class_instance(
        object_instance_graph_id=oigi_id,
        class_config_id=uuid4(),
        source_object_id=lane_id,
    )
    oigb_class_instance = _class_instance(
        object_instance_graph_id=oigi_id,
        class_config_id=uuid4(),
        source_object_id=oigb_id,
    )
    oigl_class_instance = _class_instance(
        object_instance_graph_id=oigi_id,
        class_config_id=uuid4(),
        source_object_id=oigl_id,
    )
    parent_wrapper_class_instance = _class_instance(
        object_instance_graph_id=oigi_id,
        class_config_id=uuid4(),
        source_object_id=parent_wrapper_id,
    )
    before_oig = ObjectInstanceGraph(
        id=oigi_id,
        key="ObjectInstanceGraphIdentity",
        name="ObjectInstanceGraphIdentity",
        hash="sha256:test:oigi-before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[
            root_class_instance,
            branch_class_instance,
            lane_class_instance,
            oigb_class_instance,
            oigl_class_instance,
            parent_wrapper_class_instance,
        ],
        class_instance_relationships=[],
    )
    class_instance_ids = (uuid4(), uuid4())
    head_wrapper_id = stable_object_instance_graph_commit_id(
        object_instance_graph_identity_id=oigi_id,
        commit_id=head_domain_commit_id,
    )
    head_envelope = ObjectInstanceGraphCommitEnvelope(
        commit_id=head_domain_commit_id,
        lane_id=lane_id,
        key=str(head_domain_commit_id),
        author_id=uuid4(),
        created_at=datetime.now(UTC),
        status="local",
        parent_commit_ids=(parent_domain_commit_id,),
        object_instance_graph_commit_id=head_wrapper_id,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:domain-pre",
        graph_hash_post="sha256:test:domain-post",
        projection_hash=domain_projection_hash,
        source_language="aware",
    )

    class _Store:
        envelope_calls: list[UUID] = []

        async def get_commit_envelope(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            commit_id: UUID,
        ) -> ObjectInstanceGraphCommitEnvelope | None:
            self.envelope_calls.append(commit_id)
            return None

        async def get_commit(self, **_: object) -> None:
            raise AssertionError("minimal path must not read full commit bodies")

        async def get_commit_identity_sidecar(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            commit_id: UUID,
        ) -> ObjectInstanceGraphCommitIdentitySidecar | None:
            assert branch_id == domain_branch_id
            assert projection_hash == domain_projection_hash
            assert commit_id == head_domain_commit_id
            return ObjectInstanceGraphCommitIdentitySidecar(
                commit_id=head_domain_commit_id,
                object_instance_graph_identity_id=oigi_id,
                object_instance_graph_id=domain_oig_id,
                parent_commit_ids=(parent_domain_commit_id,),
                class_instance_ids=class_instance_ids,
            )

    perf_ms: dict[str, int] = {}
    store = _Store()
    recorder = CommitPerfTraceRecorder()
    with active_commit_perf_trace(recorder):
        projection = await _project_oigi_history_projection(
            index=SimpleNamespace(
                class_configs_by_id={root_class_config.id: root_class_config},
            ),  # pyright: ignore[reportArgumentType]
            before_oig=before_oig,
            oigi_opg=_minimal_projection_graph(
                class_config=root_class_config,
                object_config_graph_id=object_config_graph_id,
            ),
            root_class_config_id=root_class_config.id,
            object_projection_graph_identity_id=object_projection_graph_identity_id,
            object_instance_graph_identity_id=oigi_id,
            domain_oig_id=domain_oig_id,
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            lane_id=lane_id,
            head_commit_id=head_domain_commit_id,
            store=store,  # pyright: ignore[reportArgumentType]
            domain_commit_envelope=head_envelope,
            perf_ms=perf_ms,
            perf_metric_prefix="test",
        )

    history_head_commit_id = stable_commit_id(
        lane_id=lane_id,
        key=str(head_domain_commit_id),
    )
    assert projection.session is None
    assert store.envelope_calls == []
    assert perf_ms["test_minimal_projection_fast_path_count"] == 1
    assert perf_ms["test_minimal_projection_fallback_count"] == 0
    assert perf_ms["test_minimal_projection_object_count"] >= 8
    assert history_head_commit_id in projection.change_set.created_ids
    assert head_wrapper_id in projection.change_set.created_ids
    assert projection.change_set.touched_ids == frozenset({lane_id})
    assert lane_id in projection.change_set.touched_ids
    assert oigi_id not in projection.change_set.touched_ids
    assert domain_branch_id not in projection.change_set.touched_ids
    assert oigb_id not in projection.change_set.touched_ids
    assert oigl_id not in projection.change_set.touched_ids
    assert oigi_id not in projection.change_set.created_ids
    assert domain_branch_id not in projection.change_set.created_ids
    assert oigb_id not in projection.change_set.created_ids
    assert oigl_id not in projection.change_set.created_ids
    assert parent_wrapper_id not in projection.change_set.created_ids
    assert parent_wrapper_id not in projection.change_set.touched_ids
    projected_class_instance_identity_count = sum(
        1
        for source in projection.change_set.objects_by_id.values()
        if type(source).__name__ == "ClassInstanceIdentity"
    )
    assert projected_class_instance_identity_count == len(class_instance_ids)

    phases = {event.phase for event in recorder.snapshot()}
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "project_history_minimal_change_set"
    ) in phases
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "reify_oigi_session"
    ) not in phases
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "project_history_direct"
    ) not in phases


def _minimal_projection_graph(
    *,
    class_config: ClassConfig,
    object_config_graph_id: UUID,
) -> ObjectProjectionGraph:
    opg_id = uuid4()
    return ObjectProjectionGraph(
        id=opg_id,
        language=CodeLanguage.aware,
        name="ObjectInstanceGraphIdentity",
        projection_hash="sha256:test:oigi",
        object_config_graph_id=object_config_graph_id,
        object_projection_graph_nodes=[
            ObjectProjectionGraphNode(
                id=uuid4(),
                is_root=False,
                object_projection_graph_id=opg_id,
                class_config_id=class_config.id,
                class_config=class_config,
            )
        ],
    )


def _class_instance(
    *,
    object_instance_graph_id: UUID,
    class_config_id: UUID,
    source_object_id: UUID,
) -> ClassInstance:
    return ClassInstance(
        id=stable_class_instance_id(
            object_instance_graph_id=object_instance_graph_id,
            class_config_id=class_config_id,
            source_object_id=source_object_id,
        ),
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
    )


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _list_of_primitives_desc() -> AttributeTypeDescriptor:
    element = _primitive_desc()
    parent = AttributeTypeDescriptor(
        kind=Kind.collection,
        collection_kind=AttributeCollectionType.list,
        child_links=[],
    )
    parent.child_links = [
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=parent.id,
            child=element,
            child_id=element.id,
            role=Role.element,
        )
    ]
    return parent


def _union_of_primitive_desc() -> AttributeTypeDescriptor:
    member = _primitive_desc()
    parent = AttributeTypeDescriptor(kind=Kind.union, child_links=[])
    parent.child_links = [
        AttributeTypeDescriptorLink(
            attribute_type_descriptor_id=parent.id,
            child=member,
            child_id=member.id,
            role=Role.member,
            position=0,
        )
    ]
    return parent


def _primitive_payload(value: object) -> object:
    if isinstance(value, dict) and set(value) == {"value"}:
        return value["value"]
    return value


def test_oigi_enum_create_body_draft_uses_built_value_ids_and_fields() -> None:
    descriptor = AttributeTypeDescriptor(kind=Kind.enum, child_links=[])
    attribute_config = make_attribute_config(
        owner_key="test.Thing",
        name="status",
        is_required=True,
        type_descriptor=descriptor,
    )
    attribute_id = uuid4()
    value_id = uuid4()
    enum_option_id = uuid4()
    owner_key = uuid4()
    value_root = AttributeValue(
        id=value_id,
        type_descriptor=descriptor,
        type_descriptor_id=descriptor.id,
        enum_option_id=enum_option_id,
        child_links=[],
    )
    attribute = Attribute(
        id=attribute_id,
        owner_key=owner_key,
        attribute_config=attribute_config,
        attribute_config_id=attribute_config.id,
        value_root=value_root,
        value_root_id=value_id,
    )

    created_at = datetime.now(UTC)
    draft = _try_build_oigi_enum_union_create_body_draft(
        attribute=attribute,
        created_at=created_at,
    )

    assert draft is not None
    assert draft.attribute_id == attribute_id
    assert draft.change.key == f"attribute:attr:{attribute_config.id}:create"
    assert draft.change.type == ChangeType.create
    assert [
        (field.position, field.property, field.payload) for field in draft.change.fields
    ] == [(0, "attribute_config_id", {"value": str(attribute_config.id)})]
    value_draft = draft.value_root_change
    assert value_draft is not None
    assert value_draft.attribute_value_id == value_id
    assert value_draft.change.key == "attribute_value:value:create"
    assert [
        (field.position, field.property, field.payload)
        for field in value_draft.change.fields
    ] == [(0, "enum_option_id", {"value": str(enum_option_id)})]
    assert value_draft.attribute_value_link_changes == ()

    class_instance_id = uuid4()
    body = build_oig_commit_body_from_draft(
        commit_id=uuid4(),
        object_instance_graph_identity_id=uuid4(),
        object_instance_graph_id=uuid4(),
        draft=OigCommitBodyDraft(
            roots=(
                OigCommitBodyRootChangeDraft(
                    id=uuid4(),
                    type=ObjectInstanceGraphChangeType.object_instance,
                    change=OigCommitBodyChangeRefDraft(
                        id=uuid4(),
                        key="root:object_instance:update",
                        type=ChangeType.update,
                        created_at=created_at,
                    ),
                    class_instance_changes=(
                        OigCommitBodyClassInstanceChangeDraft(
                            id=uuid4(),
                            class_instance_id=class_instance_id,
                            change=OigCommitBodyChangeRefDraft(
                                id=uuid4(),
                                key="class_instance:test:create",
                                type=ChangeType.create,
                                created_at=created_at,
                            ),
                            attribute_changes=(draft,),
                        ),
                    ),
                ),
            ),
        ),
    )
    decoded_attribute_change = (
        object_instance_graph_changes_from_body(body)[0]
        .class_instance_changes[0]
        .attribute_changes[0]
    )
    decoded_value_change = decoded_attribute_change.value_root_change
    assert decoded_value_change is not None
    decoded_delta = decoded_value_change.change.change_deltas[0]
    assert decoded_delta.property == "enum_option_id"
    assert decoded_delta.payload == {"value": str(enum_option_id)}


def test_oigi_model_free_enum_create_matches_canonical_fingerprint() -> None:
    descriptor = AttributeTypeDescriptor(kind=Kind.enum, child_links=[])
    attribute_config = make_attribute_config(
        owner_key="test.Thing",
        name="status",
        is_required=True,
        type_descriptor=descriptor,
    )
    owner_key = uuid4()
    enum_option_id = uuid4()
    canonical_attribute = build_attribute(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value=enum_option_id,
        enum_option_resolver=identity_history_module.default_meta_enum_option_resolver,
    )

    emission = identity_history_module._try_emit_oigi_model_free_enum_union_create(
        owner_key=owner_key,
        attribute_config=attribute_config,
        value=enum_option_id,
        before_attributes_by_id={},
        before_attribute_fingerprints_by_config_id={},
        created_at=datetime.now(UTC),
    )

    assert emission is not None
    assert emission.attribute_id == canonical_attribute.id
    assert emission.value_fingerprint == fingerprint_attribute_value(
        canonical_attribute.value_root
    )
    assert emission.attribute_change_draft.value_root_change is not None
    assert (
        emission.attribute_change_draft.value_root_change.attribute_value_id
        == canonical_attribute.value_root.id
    )
    assert (
        identity_history_module._try_emit_oigi_model_free_enum_union_create(
            owner_key=owner_key,
            attribute_config=attribute_config,
            value=enum_option_id,
            before_attributes_by_id={},
            before_attribute_fingerprints_by_config_id={
                attribute_config.id: emission.value_fingerprint
            },
            created_at=datetime.now(UTC),
        )
        is None
    )


def test_oigi_primitive_leaf_payload_parts_match_envelope_fingerprint_shape() -> None:
    scalar_parts = _oigi_primitive_leaf_payload_parts("new")
    assert scalar_parts.primitive_payload == "new"
    assert scalar_parts.fingerprint_primitive_value == {"value": "new"}

    mapping_parts = _oigi_primitive_leaf_payload_parts({"name": "new"})
    assert mapping_parts.primitive_payload == {"name": "new"}
    assert mapping_parts.fingerprint_primitive_value == {"name": "new"}


def test_oigi_model_free_primitive_leaf_fingerprint_matches_attribute_value() -> None:
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
    )
    label_config = make_attribute_config(
        owner_key=class_config.class_fqn,
        name="label",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    attribute = build_attribute(
        owner_key=uuid4(),
        attribute_config=label_config,
        value={"value": "new"},
        class_configs_by_id={class_config.id: class_config},
    )

    assert attribute.value_root is not None
    fast_fingerprint = _oigi_primitive_leaf_value_fingerprint(
        type_descriptor=label_config.type_descriptor,
        primitive_value=attribute.value_root.primitive_value,
    )

    assert fast_fingerprint == fingerprint_attribute_value(attribute.value_root)


@pytest.mark.asyncio
async def test_oigi_history_upsert_projection_index_hit_skips_head_materialization() -> (
    None
):
    domain_oig_id = uuid4()
    oigi_id = uuid4()
    domain_branch_id = uuid4()
    domain_projection_hash = "sha256:test:domain"
    oigi_projection_hash = "sha256:test:oigi"
    domain_commit_id = uuid4()
    oigi_lane_commit_id = uuid4()
    oigi_graph_hash_post = "sha256:test:oigi-head"
    lane_id = stable_lane_id(
        branch_id=domain_branch_id,
        lane_hash=domain_projection_hash,
    )
    history_commit_id = stable_commit_id(
        lane_id=lane_id,
        key=str(domain_commit_id),
    )
    envelope = ObjectInstanceGraphCommitEnvelope(
        commit_id=domain_commit_id,
        lane_id=lane_id,
        key=str(domain_commit_id),
        author_id=uuid4(),
        created_at=datetime.now(UTC),
        status="local",
        parent_commit_ids=(),
        object_instance_graph_commit_id=uuid4(),
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        object_instance_graph_key="domain",
        object_instance_graph_name="Domain",
        object_instance_graph_description=None,
        root_class_config_id=uuid4(),
        root_source_object_id=uuid4(),
        graph_hash_pre="sha256:test:pre",
        graph_hash_post="sha256:test:post",
        projection_hash=domain_projection_hash,
        source_language="aware",
    )
    projection = OigiHistoryDomainCommitProjection(
        domain_commit_id=domain_commit_id,
        domain_branch_id=domain_branch_id,
        domain_projection_hash=domain_projection_hash,
        domain_lane_id=lane_id,
        history_commit_id=history_commit_id,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        oigi_projection_hash=oigi_projection_hash,
        oigi_lane_commit_id=oigi_lane_commit_id,
        oigi_graph_hash_post=oigi_graph_hash_post,
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=[
                SimpleNamespace(
                    name="ObjectInstanceGraphIdentity",
                    projection_hash=oigi_projection_hash,
                )
            ]
        )
    )

    class _Store:
        head_call_count = 0
        projection_read_count = 0

        async def head(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
        ) -> dict[str, object]:
            assert branch_id == domain_oig_id
            assert projection_hash == oigi_projection_hash
            self.head_call_count += 1
            return {
                "commit_id": str(oigi_lane_commit_id),
                "graph_hash_post": oigi_graph_hash_post,
                "object_instance_graph_id": str(oigi_id),
            }

        async def get_oigi_history_domain_commit_projection(
            self,
            *,
            branch_id: UUID,
            projection_hash: str,
            domain_commit_id: UUID,
        ) -> OigiHistoryDomainCommitProjection | None:
            assert branch_id == domain_oig_id
            assert projection_hash == oigi_projection_hash
            assert domain_commit_id == projection.domain_commit_id
            self.projection_read_count += 1
            return projection

    class _Materializer:
        async def get(self, **_: object) -> object:
            raise AssertionError(
                "projection-index fast path must not materialize OIGI head"
            )

    store = _Store()
    perf_ms: dict[str, int] = {}

    recorder = CommitPerfTraceRecorder()
    with active_commit_perf_trace(recorder):
        result = await upsert_object_instance_graph_identity_history_from_domain_commit(
            index=index,  # pyright: ignore[reportArgumentType]
            actor_id=uuid4(),
            domain_branch_id=domain_branch_id,
            domain_projection_hash=domain_projection_hash,
            domain_commit_envelope=envelope,
            perf_ms=perf_ms,
            store=store,  # pyright: ignore[reportArgumentType]
            lane_materializer=_Materializer(),  # pyright: ignore[reportArgumentType]
        )

    assert result == oigi_id
    assert store.head_call_count == 1
    assert store.projection_read_count == 1
    assert perf_ms["run_commit_reaction_oigi_projection_index_head_hit_count"] == 1
    assert perf_ms["run_commit_reaction_oigi_projection_index_fast_path_count"] == 1
    assert "run_commit_reaction_oigi_materialize_head_ms" not in perf_ms
    phases = {event.phase for event in recorder.snapshot()}
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history.head_read"
        in phases
    )
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "projection_index_check" in phases
    )
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "projection_index_read" in phases
    )
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "projection_index_validate" in phases
    )
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "materialize_head" not in phases
    )


def test_oigi_history_direct_projection_emits_create_delete_rows() -> None:
    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
    )
    root_source_id = uuid4()
    deleted_source_id = uuid4()
    created_source_id = uuid4()
    root_class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=root_source_id,
    )
    deleted_class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=deleted_source_id,
    )
    relationship = ClassInstanceRelationship(
        id=uuid4(),
        object_instance_graph_id=object_instance_graph_id,
        class_config_relationship_id=uuid4(),
        source_class_instance_id=deleted_class_instance.id,
        target_class_instance_id=root_class_instance.id,
    )
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance, deleted_class_instance],
        class_instance_relationships=[relationship],
    )
    projection = _OigiHistoryProjectionResult(
        change_set=_change_set(
            created_ids=frozenset({created_source_id}),
            deleted_ids=frozenset({deleted_source_id}),
            objects_by_id={
                created_source_id: MappingModelSource(
                    id=created_source_id,
                    class_config_id=class_config.id,
                    values={},
                )
            },
        ),
        session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
        root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    perf_ms: dict[str, int] = {}

    change_projection = _build_oigi_history_changes_from_projection(
        index=SimpleNamespace(
            class_configs_by_id={class_config.id: class_config},
            relationships_by_id={},
            attribute_configs_by_id={},
        ),  # pyright: ignore[reportArgumentType]
        before_oig=before_oig,
        oigi_opg=_minimal_projection_graph(
            class_config=class_config,
            object_config_graph_id=object_config_graph_id,
        ),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        projection=projection,
        perf_ms=perf_ms,
        perf_metric_prefix="test",
    )
    after_oig = change_projection.after_oig
    assert after_oig is not None
    assert change_projection.changes == []
    assert perf_ms["test_row_shaped_change_builder_count"] == 1
    assert perf_ms["test_row_shaped_body_draft_count"] == 1
    assert change_projection.body_draft is not None
    assert change_projection.pre_state_evidence is not None
    assert change_projection.pre_state_evidence.state_hash == before_oig.hash
    assert change_projection.pre_state_evidence.source_contract == (
        "aware.meta.oigi.direct_projection.pre_state.v1"
    )
    draft_body = build_oig_commit_body_from_draft(
        commit_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        draft=change_projection.body_draft,
    )
    draft_changes = object_instance_graph_changes_from_body(draft_body)
    class_change_types = [
        class_change.change.type
        for root_change in draft_changes
        for class_change in root_change.class_instance_changes
    ]
    relationship_change_types = [
        relationship_change.change.type
        for root_change in draft_changes
        for relationship_change in root_change.class_instance_relationship_changes
    ]
    assert class_change_types == [ChangeType.create, ChangeType.delete]
    assert relationship_change_types == [ChangeType.delete]
    assert perf_ms["test_row_shaped_change_fallback_count"] == 0

    replayed_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=draft_changes,
        attribute_configs_by_id={},
        class_configs_by_id={class_config.id: class_config},
    )
    assert replayed_oig.hash == change_projection.graph_hash_post
    assert replayed_oig.hash == after_oig.hash
    replayed_source_ids = {
        class_instance.source_object_id
        for class_instance in replayed_oig.class_instances
    }
    assert replayed_source_ids == {root_source_id, created_source_id}
    after_source_ids = {
        class_instance.source_object_id for class_instance in after_oig.class_instances
    }
    assert after_source_ids == replayed_source_ids
    assert replayed_oig.class_instance_relationships == []
    assert change_projection.direct_projection_context is not None
    assert change_projection.pre_state_rows_by_class_instance_id is not None
    assert change_projection.post_state_rows_by_changed_class_instance_id is not None
    assert change_projection.changed_class_instances_by_id is not None
    advanced_context, advanced_rows = (
        identity_history_module._advance_oigi_history_direct_projection_batch_state(
            context=change_projection.direct_projection_context,
            pre_state_rows_by_class_instance_id=(
                change_projection.pre_state_rows_by_class_instance_id
            ),
            changed_class_instances_by_id=(
                change_projection.changed_class_instances_by_id
            ),
            post_state_rows_by_changed_class_instance_id=(
                change_projection.post_state_rows_by_changed_class_instance_id
            ),
            deleted_class_instance_ids=change_projection.deleted_class_instance_ids,
        )
    )
    assert (
        deleted_class_instance.id not in advanced_context.before_class_instances_by_id
    )
    assert deleted_class_instance.id not in advanced_rows
    created_class_instance_id = stable_class_instance_id(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=created_source_id,
    )
    assert created_class_instance_id in advanced_context.before_class_instances_by_id
    assert created_class_instance_id in advanced_rows


def test_oigi_history_direct_projection_reuses_static_projection_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _OIGI_STATIC_DIRECT_CONTEXT_CACHE.clear()
    relationship_build_count = 0
    include_build_count = 0
    original_relationship_builder = (
        identity_history_module.build_relationship_attribute_config_ids_by_class_config_id
    )
    original_include_builder = (
        identity_history_module.build_include_relationship_attribute_config_ids_by_class_config_id
    )

    def _relationship_builder(**kwargs: object) -> dict[UUID, set[UUID]]:
        nonlocal relationship_build_count
        relationship_build_count += 1
        return original_relationship_builder(
            **kwargs
        )  # pyright: ignore[reportArgumentType]

    def _include_builder(**kwargs: object) -> dict[UUID, set[UUID]]:
        nonlocal include_build_count
        include_build_count += 1
        return original_include_builder(**kwargs)  # pyright: ignore[reportArgumentType]

    monkeypatch.setattr(
        identity_history_module,
        "build_relationship_attribute_config_ids_by_class_config_id",
        _relationship_builder,
    )
    monkeypatch.setattr(
        identity_history_module,
        "build_include_relationship_attribute_config_ids_by_class_config_id",
        _include_builder,
    )

    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
    )
    root_class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=uuid4(),
    )
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )
    index = SimpleNamespace(
        class_configs_by_id={class_config.id: class_config},
        relationships_by_id={},
        attribute_configs_by_id={},
    )
    opg = _minimal_projection_graph(
        class_config=class_config,
        object_config_graph_id=object_config_graph_id,
    )

    recorder = CommitPerfTraceRecorder()
    with active_commit_perf_trace(recorder):
        for _ in range(2):
            change_projection = _build_oigi_history_changes_from_projection(
                index=index,  # pyright: ignore[reportArgumentType]
                before_oig=before_oig,
                oigi_opg=opg,
                object_instance_graph_identity_id=object_instance_graph_identity_id,
                projection=_OigiHistoryProjectionResult(
                    change_set=_change_set(),
                    session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
                    root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
                ),
                perf_ms={},
                perf_metric_prefix="test",
            )
            assert change_projection.changes == []

    assert relationship_build_count == 1
    assert include_build_count == 1
    phase_prefix = (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "build_direct_projection_context"
    )
    phase_counts: dict[str, int] = {}
    for event in recorder.snapshot():
        phase_counts[event.phase] = phase_counts.get(event.phase, 0) + 1
    assert phase_counts[f"{phase_prefix}.opg_class_config_ids"] == 2
    assert phase_counts[f"{phase_prefix}.static_cache_key"] == 2
    assert phase_counts[f"{phase_prefix}.static_cache_lookup"] == 2
    assert phase_counts[f"{phase_prefix}.static_cache_miss_build"] == 1
    assert phase_counts[f"{phase_prefix}.static_cache_hit"] == 1
    assert phase_counts[f"{phase_prefix}.before_class_instances_index"] == 2
    assert phase_counts[f"{phase_prefix}.context_assembly"] == 2

    _OIGI_STATIC_DIRECT_CONTEXT_CACHE.clear()
    warm_recorder = CommitPerfTraceRecorder()
    with active_commit_perf_trace(warm_recorder):
        warm_projection = _build_oigi_history_changes_from_projection(
            index=index,  # pyright: ignore[reportArgumentType]
            before_oig=before_oig,
            oigi_opg=opg,
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            projection=_OigiHistoryProjectionResult(
                change_set=_change_set(),
                session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
                root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
            ),
            relationship_projection_context=(
                identity_history_module.OrmChangeTranslationRelationshipProjectionContext(
                    relationship_attribute_ids_by_cc_id={},
                    include_relationship_attribute_ids_by_cc_id={},
                    opg_class_config_ids=frozenset({class_config.id}),
                )
            ),
            perf_ms={},
            perf_metric_prefix="test_warm",
        )
    assert warm_projection.changes == []
    assert relationship_build_count == 1
    assert include_build_count == 1
    warm_phases = {event.phase for event in warm_recorder.snapshot()}
    assert f"{phase_prefix}.warmed_projection_context_reuse" in warm_phases
    assert f"{phase_prefix}.static_cache_miss_build" not in warm_phases
    foreign_view = identity_history_module.MetaGraphRuntimeIndexView(
        index=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    with pytest.raises(ValueError, match="belongs to a different runtime index"):
        identity_history_module._oigi_history_warmed_relationship_projection_context(
            index=index,  # pyright: ignore[reportArgumentType]
            index_view=foreign_view,
            oigi_opg=opg,
        )
    _OIGI_STATIC_DIRECT_CONTEXT_CACHE.clear()


def test_oigi_history_direct_projection_compact_body_replay_parity_for_create_attributes() -> (
    None
):
    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
        class_config_attribute_configs=[],
    )
    label_config = make_attribute_config(
        owner_key=class_config.class_fqn,
        name="label",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=class_config.id,
            attribute_config=label_config,
            name=label_config.name,
            position=0,
        )
    ]
    root_source_id = uuid4()
    created_source_id = uuid4()
    root_class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=root_source_id,
    )
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )
    projection = _OigiHistoryProjectionResult(
        change_set=_change_set(
            created_ids=frozenset({created_source_id}),
            objects_by_id={
                created_source_id: MappingModelSource(
                    id=created_source_id,
                    class_config_id=class_config.id,
                    values={"label": "new"},
                )
            },
        ),
        session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
        root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    perf_ms: dict[str, int] = {}

    change_projection = _build_oigi_history_changes_from_projection(
        index=SimpleNamespace(
            class_configs_by_id={class_config.id: class_config},
            relationships_by_id={},
            attribute_configs_by_id={label_config.id: label_config},
        ),  # pyright: ignore[reportArgumentType]
        before_oig=before_oig,
        oigi_opg=_minimal_projection_graph(
            class_config=class_config,
            object_config_graph_id=object_config_graph_id,
        ),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        projection=projection,
        perf_ms=perf_ms,
        perf_metric_prefix="test",
    )
    after_oig = change_projection.after_oig
    assert after_oig is not None
    assert change_projection.changes == []
    assert change_projection.body_draft is not None
    draft_body = build_oig_commit_body_from_draft(
        commit_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        draft=change_projection.body_draft,
    )
    decoded_changes = object_instance_graph_changes_from_body(draft_body)

    replayed_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=decoded_changes,
        attribute_configs_by_id={label_config.id: label_config},
        class_configs_by_id={class_config.id: class_config},
    )

    assert replayed_oig.hash == change_projection.graph_hash_post
    assert replayed_oig.hash == after_oig.hash
    assert len(replayed_oig.class_instances) == 2
    assert perf_ms["test_source_row_model_free_primitive_attribute_count"] == 1
    assert perf_ms["test_source_row_model_free_primitive_body_draft_fused_count"] == 1
    created_replay = next(
        item
        for item in replayed_oig.class_instances
        if item.source_object_id == created_source_id
    )
    assert len(created_replay.attributes) == 1
    assert (
        _primitive_payload(created_replay.attributes[0].value_root.primitive_value)
        == "new"
    )


def test_oigi_history_direct_projection_falls_back_for_unreplayable_new_attribute_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
        class_config_attribute_configs=[],
    )
    tags_config = make_attribute_config(
        owner_key=class_config.class_fqn,
        name="tags",
        is_required=True,
        type_descriptor=_list_of_primitives_desc(),
    )
    class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=class_config.id,
            attribute_config=tags_config,
            name=tags_config.name,
            position=0,
        )
    ]
    root_source_id = uuid4()
    created_source_id = uuid4()
    root_class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=root_source_id,
    )
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )
    projection = _OigiHistoryProjectionResult(
        change_set=_change_set(
            created_ids=frozenset({created_source_id}),
            objects_by_id={
                created_source_id: MappingModelSource(
                    id=created_source_id,
                    class_config_id=class_config.id,
                    values={"tags": ["new", "delta"]},
                )
            },
        ),
        session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
        root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    perf_ms: dict[str, int] = {}
    recorder = CommitPerfTraceRecorder()
    compatibility_header_calls = 0
    original_compatibility_header = (
        identity_history_module._build_oigi_history_class_instance_change_header
    )

    def _record_compatibility_header(
        *,
        before_class_instance: ClassInstance | None,
        class_instance: ClassInstance,
        created_at: datetime,
    ) -> object:
        nonlocal compatibility_header_calls
        compatibility_header_calls += 1
        return original_compatibility_header(
            before_class_instance=before_class_instance,
            class_instance=class_instance,
            created_at=created_at,
        )

    monkeypatch.setattr(
        identity_history_module,
        "_build_oigi_history_class_instance_change_header",
        _record_compatibility_header,
    )

    with active_commit_perf_trace(recorder):
        change_projection = _build_oigi_history_changes_from_projection(
            index=SimpleNamespace(
                class_configs_by_id={class_config.id: class_config},
                relationships_by_id={},
                attribute_configs_by_id={tags_config.id: tags_config},
            ),  # pyright: ignore[reportArgumentType]
            before_oig=before_oig,
            oigi_opg=_minimal_projection_graph(
                class_config=class_config,
                object_config_graph_id=object_config_graph_id,
            ),
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            projection=projection,
            perf_ms=perf_ms,
            perf_metric_prefix="test",
        )
    changes = change_projection.changes
    after_oig = change_projection.after_oig
    assert after_oig is not None

    assert perf_ms["test_row_shaped_change_builder_count"] == 0
    assert perf_ms["test_row_shaped_change_fallback_count"] == 1
    assert perf_ms["test_row_shaped_body_draft_count"] == 0
    assert change_projection.body_draft is None
    assert perf_ms["test_source_row_unreplayable_attribute_row_fallback_count"] == 1
    assert perf_ms["test_source_row_projection_fallback_count"] == 1
    assert perf_ms.get("test_direct_post_graph_cache_trusted_hash_count", 0) == 0
    assert compatibility_header_calls == 1
    assert perf_ms["test_source_row_compat_class_header_count"] == 1
    assert perf_ms.get("test_source_row_draft_native_class_header_count", 0) == 0
    fallback_event = next(
        item
        for item in recorder.snapshot()
        if item.phase.endswith("direct_source_row_projection_fallback")
    )
    assert fallback_event.metadata["reason"] == "unreplayable_attribute_row"
    assert fallback_event.metadata["class_name"] == "Thing"
    assert fallback_event.metadata["attribute_name"] == "tags"
    assert fallback_event.metadata["attribute_type_kind"] == "collection"

    replayed_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id={tags_config.id: tags_config},
        class_configs_by_id={class_config.id: class_config},
    )

    assert replayed_oig.hash == change_projection.graph_hash_post
    created_replay = next(
        item
        for item in replayed_oig.class_instances
        if item.source_object_id == created_source_id
    )
    assert len(created_replay.attributes) == 1
    assert len(created_replay.attributes[0].value_root.child_links) == 2


def test_oigi_history_direct_projection_replays_union_attribute_create(
    monkeypatch,
) -> None:
    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
        class_config_attribute_configs=[],
    )
    payload_config = make_attribute_config(
        owner_key=class_config.class_fqn,
        name="payload",
        is_required=True,
        type_descriptor=_union_of_primitive_desc(),
    )
    class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=class_config.id,
            attribute_config=payload_config,
            name=payload_config.name,
            position=0,
        )
    ]
    root_source_id = uuid4()
    created_source_id = uuid4()
    root_class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=root_source_id,
    )
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )
    projection = _OigiHistoryProjectionResult(
        change_set=_change_set(
            created_ids=frozenset({created_source_id}),
            objects_by_id={
                created_source_id: MappingModelSource(
                    id=created_source_id,
                    class_config_id=class_config.id,
                    values={"payload": "delta"},
                )
            },
        ),
        session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
        root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    perf_ms: dict[str, int] = {}
    recorder = CommitPerfTraceRecorder()

    def _unexpected_attribute_builder(**_: object) -> object:
        raise AssertionError("model-free union create built a full Attribute tree")

    monkeypatch.setattr(
        identity_history_module,
        "build_attribute",
        _unexpected_attribute_builder,
    )

    with active_commit_perf_trace(recorder):
        change_projection = _build_oigi_history_changes_from_projection(
            index=SimpleNamespace(
                class_configs_by_id={class_config.id: class_config},
                relationships_by_id={},
                attribute_configs_by_id={payload_config.id: payload_config},
            ),  # pyright: ignore[reportArgumentType]
            before_oig=before_oig,
            oigi_opg=_minimal_projection_graph(
                class_config=class_config,
                object_config_graph_id=object_config_graph_id,
            ),
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            projection=projection,
            perf_ms=perf_ms,
            perf_metric_prefix="test",
        )

    after_oig = change_projection.after_oig
    assert after_oig is not None
    assert change_projection.body_draft is not None
    assert change_projection.changes == []
    draft_body = build_oig_commit_body_from_draft(
        commit_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        draft=change_projection.body_draft,
    )
    changes = object_instance_graph_changes_from_body(draft_body)
    assert perf_ms["test_row_shaped_change_builder_count"] == 1
    assert perf_ms["test_row_shaped_change_fallback_count"] == 0
    assert perf_ms["test_row_shaped_body_draft_count"] == 1
    assert perf_ms.get("test_source_row_generic_attribute_builder_count", 0) == 0
    assert perf_ms.get("test_source_row_built_attribute_count", 0) == 0
    assert perf_ms["test_source_row_attribute_change_count"] == 0
    assert perf_ms["test_source_row_model_free_enum_union_create_count"] == 1
    assert perf_ms.get("test_source_row_enum_union_direct_body_draft_count", 0) == 0
    assert perf_ms["test_source_row_state_row_count"] == 2
    assert perf_ms["test_direct_post_graph_cache_trusted_hash_count"] == 1
    assert perf_ms["test_direct_post_graph_cache_row_backed_graph_count"] == 1
    assert perf_ms.get("test_source_row_projection_fallback_count", 0) == 0
    assert not any(
        item.phase.endswith("direct_source_row_projection_fallback")
        for item in recorder.snapshot()
    )
    phases = {item.phase for item in recorder.snapshot()}
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "build_direct_source_state_rows.build_enum_union_direct_body_draft"
    ) not in phases

    attribute_changes = [
        attribute_change
        for root_change in changes
        for class_change in root_change.class_instance_changes
        for attribute_change in class_change.attribute_changes
    ]
    assert [change.change.type for change in attribute_changes] == [ChangeType.create]
    value_root_change = attribute_changes[0].value_root_change
    assert value_root_change is not None
    assert value_root_change.change.type == ChangeType.create
    assert len(value_root_change.attribute_value_link_changes) == 1
    link_change = value_root_change.attribute_value_link_changes[0]
    assert link_change.change.type == ChangeType.create
    assert link_change.child_attribute_value_change is not None
    assert link_change.child_attribute_value_change.change.type == ChangeType.create

    replayed_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id={payload_config.id: payload_config},
        class_configs_by_id={class_config.id: class_config},
    )

    assert replayed_oig.hash == change_projection.graph_hash_post
    assert replayed_oig.hash == after_oig.hash
    created_replay = next(
        item
        for item in replayed_oig.class_instances
        if item.source_object_id == created_source_id
    )
    replayed_attribute = created_replay.attributes[0]
    replayed_root = replayed_attribute.value_root
    assert replayed_root is not None
    assert len(replayed_root.child_links) == 1
    replayed_child = replayed_root.child_links[0].child
    assert _primitive_payload(replayed_child.primitive_value) == "delta"


def test_oigi_history_direct_projection_emits_attribute_update_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
        class_config_attribute_configs=[],
    )
    label_config = make_attribute_config(
        owner_key=class_config.class_fqn,
        name="label",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=class_config.id,
            attribute_config=label_config,
            name=label_config.name,
            position=0,
        )
    ]
    source_id = uuid4()
    class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=source_id,
    )
    old_attribute = build_attribute(
        owner_key=source_id,
        attribute_config=label_config,
        value="old",
        class_configs_by_id={class_config.id: class_config},
    )
    _ = link_attribute(class_instance, old_attribute)
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=class_instance.id,
        root_class_instance=class_instance,
        class_instances=[class_instance],
        class_instance_relationships=[],
    )
    projection = _OigiHistoryProjectionResult(
        change_set=_change_set(
            touched_ids=frozenset({source_id}),
            objects_by_id={
                source_id: MappingModelSource(
                    id=source_id,
                    class_config_id=class_config.id,
                    values={"label": "new"},
                )
            },
        ),
        session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
        root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    perf_ms: dict[str, int] = {}

    def _unexpected_compatibility_header(**_: object) -> object:
        raise AssertionError("direct primitive projection built compatibility header")

    monkeypatch.setattr(
        identity_history_module,
        "_build_oigi_history_class_instance_change_header",
        _unexpected_compatibility_header,
    )

    recorder = CommitPerfTraceRecorder()
    with active_commit_perf_trace(recorder):
        change_projection = _build_oigi_history_changes_from_projection(
            index=SimpleNamespace(
                class_configs_by_id={class_config.id: class_config},
                relationships_by_id={},
                attribute_configs_by_id={label_config.id: label_config},
            ),  # pyright: ignore[reportArgumentType]
            before_oig=before_oig,
            oigi_opg=_minimal_projection_graph(
                class_config=class_config,
                object_config_graph_id=object_config_graph_id,
            ),
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            projection=projection,
            perf_ms=perf_ms,
            perf_metric_prefix="test",
        )

    after_oig = change_projection.after_oig
    assert after_oig is not None
    assert change_projection.body_draft is not None
    assert change_projection.changes == []
    draft_body = build_oig_commit_body_from_draft(
        commit_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        draft=change_projection.body_draft,
    )
    changes = object_instance_graph_changes_from_body(draft_body)
    assert change_projection.pre_state_evidence is not None
    assert change_projection.pre_state_evidence.state_hash == before_oig.hash
    attribute_changes = [
        attribute_change
        for root_change in changes
        for class_change in root_change.class_instance_changes
        for attribute_change in class_change.attribute_changes
    ]
    assert [change.change.type for change in attribute_changes] == [ChangeType.update]
    assert perf_ms["test_row_shaped_change_builder_count"] == 1
    assert perf_ms["test_row_shaped_change_fallback_count"] == 0
    assert perf_ms["test_row_shaped_body_draft_count"] == 1
    assert perf_ms["test_row_native_body_draft_root_count"] == 1
    assert perf_ms["test_row_native_body_draft_class_instance_count"] == 1
    assert perf_ms["test_direct_post_graph_cache_row_backed_graph_count"] == 1
    assert perf_ms["test_source_row_attribute_link_count"] == 1
    assert perf_ms["test_source_row_model_free_primitive_attribute_count"] == 1
    assert perf_ms["test_source_row_model_free_primitive_attribute_change_count"] == 1
    assert perf_ms["test_source_row_model_free_primitive_body_draft_fused_count"] == 1
    assert perf_ms["test_source_row_primitive_body_draft_direct_count"] == 1
    assert perf_ms["test_source_row_class_instance_body_draft_direct_count"] == 1
    assert perf_ms["test_source_row_draft_native_class_header_count"] == 1
    assert perf_ms.get("test_source_row_compat_class_header_count", 0) == 0
    assert perf_ms.get("test_source_row_model_free_primitive_no_change_count", 0) == 0
    assert perf_ms.get("test_source_row_direct_attribute_link_count", 0) == 0
    assert perf_ms.get("test_source_row_link_attribute_fallback_count", 0) == 0
    assert perf_ms.get("test_source_row_built_attribute_count", 0) == 0
    assert perf_ms["test_source_row_state_row_count"] == 2
    assert perf_ms["test_source_row_attribute_change_count"] == 0
    assert perf_ms.get("test_source_row_primitive_attribute_fast_path_count", 0) == 0
    assert perf_ms.get("test_source_row_generic_attribute_builder_count", 0) == 0
    assert (
        perf_ms.get("test_source_row_primitive_attribute_change_fast_path_count", 0)
        == 0
    )
    assert perf_ms.get("test_source_row_generic_attribute_change_builder_count", 0) == 0
    assert perf_ms["test_direct_post_graph_cache_trusted_hash_count"] == 1
    assert perf_ms.get("test_direct_state_row_replay_hash_mismatch_count", 0) == 0
    assert "test_build_direct_projection_context_ms" in perf_ms
    phases = {event.phase for event in recorder.snapshot()}
    source_row_phase = (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "build_direct_source_state_rows"
    )
    assert source_row_phase in phases
    assert not any(phase.startswith(f"{source_row_phase}.") for phase in phases)
    change_emit_phase = (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "emit_changed_class_instance_changes"
    )
    expected_change_emit_child_phases = {
        f"{change_emit_phase}.collect_changed_projection_changes",
        f"{change_emit_phase}.build_deleted_changes",
        f"{change_emit_phase}.build_deleted_relationship_changes",
        f"{change_emit_phase}.build_root_compat_change",
        f"{change_emit_phase}.build_root_body_draft",
    }
    assert expected_change_emit_child_phases <= phases
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "build_direct_projection_context"
    ) in phases

    replayed_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id={label_config.id: label_config},
        class_configs_by_id={class_config.id: class_config},
    )
    assert replayed_oig.hash == change_projection.graph_hash_post
    assert replayed_oig.hash == after_oig.hash
    replayed_attribute = replayed_oig.class_instances[0].attributes[0]
    assert replayed_attribute.value_root is not None
    assert _primitive_payload(replayed_attribute.value_root.primitive_value) == "new"

    assert change_projection.direct_projection_context is not None
    assert change_projection.pre_state_rows_by_class_instance_id is not None
    assert change_projection.post_state_rows_by_changed_class_instance_id is not None
    assert change_projection.changed_class_instances_by_id is not None
    direct_context, pre_state_rows_by_id = (
        identity_history_module._advance_oigi_history_direct_projection_batch_state(
            context=change_projection.direct_projection_context,
            pre_state_rows_by_class_instance_id=(
                change_projection.pre_state_rows_by_class_instance_id
            ),
            changed_class_instances_by_id=(
                change_projection.changed_class_instances_by_id
            ),
            post_state_rows_by_changed_class_instance_id=(
                change_projection.post_state_rows_by_changed_class_instance_id
            ),
            deleted_class_instance_ids=change_projection.deleted_class_instance_ids,
        )
    )
    second_perf_ms: dict[str, int] = {}
    second_recorder = CommitPerfTraceRecorder()
    with active_commit_perf_trace(second_recorder):
        second_projection = _build_oigi_history_changes_from_projection(
            index=SimpleNamespace(
                class_configs_by_id={class_config.id: class_config},
                relationships_by_id={},
                attribute_configs_by_id={label_config.id: label_config},
            ),  # pyright: ignore[reportArgumentType]
            before_oig=after_oig,
            oigi_opg=_minimal_projection_graph(
                class_config=class_config,
                object_config_graph_id=object_config_graph_id,
            ),
            object_instance_graph_identity_id=object_instance_graph_identity_id,
            projection=_OigiHistoryProjectionResult(
                change_set=_change_set(
                    touched_ids=frozenset({source_id}),
                    objects_by_id={
                        source_id: MappingModelSource(
                            id=source_id,
                            class_config_id=class_config.id,
                            values={"label": "newer"},
                        )
                    },
                ),
                session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
                root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
            ),
            materialized_pre_state_index=change_projection.post_state_index,
            direct_projection_context=direct_context,
            pre_state_rows_by_class_instance_id=pre_state_rows_by_id,
            perf_ms=second_perf_ms,
            perf_metric_prefix="test_second",
        )

    assert second_perf_ms["test_second_direct_projection_context_reuse_count"] == 1
    assert second_perf_ms["test_second_pre_state_row_maps_reuse_count"] == 1
    assert "test_second_direct_projection_context_build_count" not in second_perf_ms
    assert "test_second_pre_state_row_maps_build_count" not in second_perf_ms
    second_phases = {event.phase for event in second_recorder.snapshot()}
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "reuse_direct_projection_context"
    ) in second_phases
    assert (
        "runtime.invoke_function.required_commit_reactions.oigi_history."
        "reuse_direct_pre_state_row_maps"
    ) in second_phases
    assert second_projection.changes == []
    assert second_projection.body_draft is not None
    second_draft_body = build_oig_commit_body_from_draft(
        commit_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        draft=second_projection.body_draft,
    )
    second_replayed_oig = materialize_meta_oig_post(
        before_oig=replayed_oig,
        changes=object_instance_graph_changes_from_body(second_draft_body),
        attribute_configs_by_id={label_config.id: label_config},
        class_configs_by_id={class_config.id: class_config},
    )
    assert second_replayed_oig.hash == second_projection.graph_hash_post
    assert second_replayed_oig.hash == second_projection.after_oig.hash
    second_attribute = second_replayed_oig.class_instances[0].attributes[0]
    assert second_attribute.value_root is not None
    assert _primitive_payload(second_attribute.value_root.primitive_value) == "newer"


def test_oigi_history_direct_projection_reuses_unchanged_primitive_fingerprint() -> (
    None
):
    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    object_instance_graph_identity_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
        class_config_attribute_configs=[],
    )
    label_config = make_attribute_config(
        owner_key=class_config.class_fqn,
        name="label",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    class_config.class_config_attribute_configs = [
        make_class_attribute_edge(
            class_config_id=class_config.id,
            attribute_config=label_config,
            name=label_config.name,
            position=0,
        )
    ]
    source_id = uuid4()
    class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=source_id,
    )
    old_attribute = build_attribute(
        owner_key=source_id,
        attribute_config=label_config,
        value="old",
        class_configs_by_id={class_config.id: class_config},
    )
    _ = link_attribute(class_instance, old_attribute)
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=class_instance.id,
        root_class_instance=class_instance,
        class_instances=[class_instance],
        class_instance_relationships=[],
    )
    projection = _OigiHistoryProjectionResult(
        change_set=_change_set(
            touched_ids=frozenset({source_id}),
            objects_by_id={
                source_id: MappingModelSource(
                    id=source_id,
                    class_config_id=class_config.id,
                    values={"label": "old"},
                )
            },
        ),
        session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
        root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
    )
    perf_ms: dict[str, int] = {}

    change_projection = _build_oigi_history_changes_from_projection(
        index=SimpleNamespace(
            class_configs_by_id={class_config.id: class_config},
            relationships_by_id={},
            attribute_configs_by_id={label_config.id: label_config},
        ),  # pyright: ignore[reportArgumentType]
        before_oig=before_oig,
        oigi_opg=_minimal_projection_graph(
            class_config=class_config,
            object_config_graph_id=object_config_graph_id,
        ),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        projection=projection,
        perf_ms=perf_ms,
        perf_metric_prefix="test",
    )

    assert change_projection.changes == []
    assert change_projection.body_draft is not None
    assert change_projection.body_draft.roots == ()
    assert change_projection.after_oig is not None
    assert change_projection.graph_hash_post
    assert perf_ms["test_source_row_model_free_primitive_attribute_count"] == 1
    assert perf_ms["test_source_row_model_free_primitive_no_change_count"] == 1
    assert (
        perf_ms["test_source_row_model_free_primitive_reused_before_fingerprint_count"]
        == 1
    )
    assert (
        perf_ms.get("test_source_row_model_free_primitive_attribute_change_count", 0)
        == 0
    )
    assert (
        perf_ms.get("test_source_row_model_free_primitive_body_draft_fused_count", 0)
        == 0
    )
    assert perf_ms["test_source_row_state_row_count"] == 2
    assert perf_ms["test_source_row_attribute_change_count"] == 0
    assert perf_ms.get("test_direct_state_row_replay_hash_mismatch_count", 0) == 0
    assert perf_ms["test_row_shaped_change_builder_count"] == 1
    assert perf_ms["test_row_shaped_change_fallback_count"] == 0
    assert perf_ms["test_row_shaped_body_draft_count"] == 0


def test_oigi_history_direct_row_replay_mismatch_diagnostics_are_bounded() -> None:
    class_config_id = uuid4()
    class_instance_id = uuid4()
    object_instance_graph_id = uuid4()
    replay_root = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config_id,
        source_object_id=uuid4(),
    )
    direct_index = CommitStateIndex(
        rows=(
            CommitStateRow(
                kind="NODE",
                key=str(class_config_id),
                value=str(class_instance_id),
            ),
            CommitStateRow(
                kind="ATTR",
                key=str(class_instance_id),
                value=f"{uuid4()}:direct-only",
            ),
        )
    )
    replayed_after_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="replay-hash",
        object_projection_graph_id=uuid4(),
        root_class_instance=replay_root,
        root_class_instance_id=replay_root.id,
        class_instances=[replay_root],
        class_instance_relationships=[],
    )
    perf_ms: dict[str, int] = {}
    recorder = CommitPerfTraceRecorder()

    with active_commit_perf_trace(recorder):
        _record_oigi_direct_state_row_replay_mismatch_diagnostics(
            perf_ms=perf_ms,
            perf_metric_prefix="test",
            direct_post_state_index=direct_index,
            replayed_after_oig=replayed_after_oig,
            direct_state_hash_post="direct-hash",
            replay_graph_hash_post="replay-hash",
        )

    assert perf_ms["test_direct_state_row_replay_direct_row_count"] == 2
    assert perf_ms["test_direct_state_row_replay_replay_row_count"] == 1
    assert perf_ms["test_direct_state_row_replay_direct_only_row_count"] == 2
    assert perf_ms["test_direct_state_row_replay_replay_only_row_count"] == 1
    assert perf_ms["test_direct_state_row_replay_direct_only_node_row_count"] == 1
    assert perf_ms["test_direct_state_row_replay_direct_only_attr_row_count"] == 1
    assert perf_ms["test_direct_state_row_replay_replay_only_node_row_count"] == 1
    event = next(
        item
        for item in recorder.snapshot()
        if item.phase.endswith("direct_state_row_replay_mismatch")
    )
    assert event.metadata["direct_state_hash_post"] == "direct-hash"
    assert event.metadata["replay_graph_hash_post"] == "replay-hash"
    assert event.metadata["direct_only_row_count"] == 2
    assert "NODE|" in str(event.metadata["direct_only_sample"])
    assert "ATTR|" in str(event.metadata["direct_only_sample"])


def test_oigi_history_direct_projection_rejects_unresolved_delete() -> None:
    object_config_graph_id = uuid4()
    object_instance_graph_id = uuid4()
    class_config = ClassConfig(
        id=uuid4(),
        class_fqn="test.Thing",
        name="Thing",
    )
    root_class_instance = _class_instance(
        object_instance_graph_id=object_instance_graph_id,
        class_config_id=class_config.id,
        source_object_id=uuid4(),
    )
    before_oig = ObjectInstanceGraph(
        id=object_instance_graph_id,
        key="test",
        name="Test",
        hash="sha256:before",
        object_projection_graph_id=uuid4(),
        root_class_instance_id=root_class_instance.id,
        root_class_instance=root_class_instance,
        class_instances=[root_class_instance],
        class_instance_relationships=[],
    )

    with pytest.raises(_OigiHistoryDirectProjectionUnsupported):
        _build_oigi_history_changes_from_projection(
            index=SimpleNamespace(
                class_configs_by_id={class_config.id: class_config},
                relationships_by_id={},
                attribute_configs_by_id={},
            ),  # pyright: ignore[reportArgumentType]
            before_oig=before_oig,
            oigi_opg=_minimal_projection_graph(
                class_config=class_config,
                object_config_graph_id=object_config_graph_id,
            ),
            object_instance_graph_identity_id=uuid4(),
            projection=_OigiHistoryProjectionResult(
                change_set=_change_set(deleted_ids=frozenset({uuid4()})),
                session=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
                root_identity=SimpleNamespace(),  # pyright: ignore[reportArgumentType]
            ),
            perf_ms={},
            perf_metric_prefix="test",
        )
