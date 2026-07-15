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
    build_oig_commit_body_from_draft,
    build_oig_commit_body_from_changes,
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
    upsert_object_instance_graph_identity_history_from_domain_commit,
)
from aware_meta.test_support import make_attribute_config, make_class_attribute_edge
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
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.class_.class_instance_relationship import (
    ClassInstanceRelationship,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
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
    changes = change_projection.changes
    after_oig = change_projection.after_oig
    assert after_oig is not None

    class_change_types = [
        class_change.change.type
        for root_change in changes
        for class_change in root_change.class_instance_changes
    ]
    relationship_change_types = [
        relationship_change.change.type
        for root_change in changes
        for relationship_change in root_change.class_instance_relationship_changes
    ]
    assert class_change_types == [ChangeType.create, ChangeType.delete]
    assert relationship_change_types == [ChangeType.delete]
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
    assert len(draft_changes) == len(changes)
    assert perf_ms["test_row_shaped_change_fallback_count"] == 0

    replayed_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
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
        return original_relationship_builder(**kwargs)  # pyright: ignore[reportArgumentType]

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
    changes = change_projection.changes
    after_oig = change_projection.after_oig
    assert after_oig is not None
    body = build_oig_commit_body_from_changes(
        commit_id=uuid4(),
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        changes=changes,
    )
    assert change_projection.body_draft is not None
    draft_body = build_oig_commit_body_from_draft(
        commit_id=body.commit_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_id=object_instance_graph_id,
        draft=change_projection.body_draft,
    )
    assert draft_body.payload == body.payload
    decoded_changes = object_instance_graph_changes_from_body(body)

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
    assert perf_ms["test_source_row_model_free_primitive_change_draft_count"] == 1
    assert (
        perf_ms[
            "test_source_row_model_free_primitive_change_draft_assembled_count"
        ]
        == 1
    )
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


def test_oigi_history_direct_projection_falls_back_for_unreplayable_new_attribute_rows() -> (
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


def test_oigi_history_direct_projection_replays_union_attribute_create() -> None:
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

    changes = change_projection.changes
    after_oig = change_projection.after_oig
    assert after_oig is not None
    assert change_projection.body_draft is not None
    assert perf_ms["test_row_shaped_change_builder_count"] == 1
    assert perf_ms["test_row_shaped_change_fallback_count"] == 0
    assert perf_ms["test_row_shaped_body_draft_count"] == 1
    assert perf_ms["test_source_row_generic_attribute_builder_count"] == 1
    assert perf_ms["test_source_row_built_attribute_count"] == 1
    assert perf_ms["test_source_row_attribute_change_count"] == 1
    assert perf_ms["test_source_row_state_row_count"] == 2
    assert perf_ms["test_direct_post_graph_cache_trusted_hash_count"] == 1
    assert perf_ms["test_direct_post_graph_cache_row_backed_graph_count"] == 1
    assert perf_ms.get("test_source_row_projection_fallback_count", 0) == 0
    assert not any(
        item.phase.endswith("direct_source_row_projection_fallback")
        for item in recorder.snapshot()
    )

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


def test_oigi_history_direct_projection_emits_attribute_update_rows() -> None:
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

    changes = change_projection.changes
    after_oig = change_projection.after_oig
    assert after_oig is not None
    assert change_projection.body_draft is not None
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
    assert perf_ms["test_source_row_model_free_primitive_change_draft_count"] == 1
    assert perf_ms["test_source_row_primitive_body_draft_direct_count"] == 1
    assert perf_ms["test_source_row_class_instance_body_draft_direct_count"] == 1
    assert (
        perf_ms[
            "test_source_row_model_free_primitive_change_draft_assembled_count"
        ]
        == 1
    )
    assert perf_ms.get("test_source_row_model_free_primitive_no_change_count", 0) == 0
    assert perf_ms.get("test_source_row_direct_attribute_link_count", 0) == 0
    assert perf_ms.get("test_source_row_link_attribute_fallback_count", 0) == 0
    assert perf_ms.get("test_source_row_built_attribute_count", 0) == 0
    assert perf_ms["test_source_row_state_row_count"] == 2
    assert perf_ms["test_source_row_attribute_change_count"] == 1
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
    expected_child_phases = {
        f"{source_row_phase}.before_attribute_fingerprints",
        f"{source_row_phase}.before_attribute_index",
        f"{source_row_phase}.attribute_plan_iteration",
        f"{source_row_phase}.source_value_resolution",
        f"{source_row_phase}.emit_primitive_leaf_source_row",
        f"{source_row_phase}.assemble_primitive_leaf_change_drafts",
        f"{source_row_phase}.sort_rows_changes",
    }
    assert expected_child_phases <= phases
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


def test_oigi_history_direct_projection_reuses_unchanged_primitive_fingerprint() -> None:
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
        perf_ms.get("test_source_row_model_free_primitive_change_draft_count", 0)
        == 0
    )
    assert (
        perf_ms["test_source_row_model_free_primitive_change_draft_assembled_count"]
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
