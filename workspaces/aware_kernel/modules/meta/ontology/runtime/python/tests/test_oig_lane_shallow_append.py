from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from _pytest.monkeypatch import MonkeyPatch

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_history_ontology.change.change_enums import ChangeType
from aware_history_ontology.lane.lane import Lane
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind as Kind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_meta_ontology.graph.config.object_config_graph_node import (
    ObjectConfigGraphNode,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_enums import (
    ObjectProjectionGraphNodeSelection,
)
from aware_meta_ontology.graph.projection.object_projection_graph_node import (
    ObjectProjectionGraphNode,
)

from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_object_instance_graph_from_class_instances,
)
from aware_meta.graph.instance.commit import committer as committer_module
from aware_meta.graph.instance.commit.body_codec import (
    OIG_COMMIT_BODY_CONTRACT,
    OigCommitBodyDraft,
    OigCommitBodyRootChangeDraft,
    oig_commit_body_change_ref_draft_from_change,
    oig_commit_body_class_instance_change_draft_from_change,
    oig_commit_body_relationship_change_draft_from_change,
)
from aware_meta.graph.instance.commit.builder import (
    extract_object_instance_graph_commit_root_metadata,
)
from aware_meta.graph.instance.commit.contract import (
    ObjectInstanceGraphCommitPreStateEvidence,
)
from aware_meta.graph.instance.commit.committer import (
    FSLaneCommitter,
    LaneCommitError,
    LaneStateIndexPreHashMismatchError,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.graph.instance.commit.perf_trace import (
    CommitPerfTraceRecorder,
    active_commit_perf_trace,
)
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    build_commit_state_index,
)
from aware_meta.graph.instance.diff import diff_object_instance_graph_changes
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_meta.test_support import (
    make_attribute_config,
    make_class_attribute_edge,
    make_class_config,
    make_rooted_object_instance_graph,
    test_class_fqn,
)


_USER_FQN = test_class_fqn("ShallowCommitUser")
_TEST_OIGI_ID = uuid4()


def _body_draft_from_changes(
    changes: list[ObjectInstanceGraphChange],
) -> OigCommitBodyDraft:
    roots: list[OigCommitBodyRootChangeDraft] = []
    for change in changes:
        roots.append(
            OigCommitBodyRootChangeDraft(
                id=change.id,
                type=change.type,
                change=oig_commit_body_change_ref_draft_from_change(
                    change.change,
                    fields=change.change.change_deltas,
                ),
                class_instance_changes=tuple(
                    oig_commit_body_class_instance_change_draft_from_change(item)
                    for item in change.class_instance_changes
                ),
                class_instance_relationship_changes=tuple(
                    oig_commit_body_relationship_change_draft_from_change(item)
                    for item in change.class_instance_relationship_changes
                ),
            )
        )
    return OigCommitBodyDraft(roots=tuple(roots))


def _primitive_desc() -> AttributeTypeDescriptor:
    return AttributeTypeDescriptor(kind=Kind.primitive, child_links=[])


def _make_ocg_and_opg(
    *,
    name_cfg: AttributeConfig,
) -> tuple[ObjectConfigGraph, ObjectProjectionGraph, ClassConfig]:
    user_cc = make_class_config(
        "ShallowCommitUser",
        class_fqn=_USER_FQN,
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
            node_key=user_cc.class_fqn,
            class_config=user_cc,
            object_config_graph_id=ocg.id,
        ),
    ]

    opg = ObjectProjectionGraph(
        name="test-opg",
        description=None,
        language=CodeLanguage.python,
        projection_hash="lane",
        supports_virtual_build=True,
        object_config_graph_id=ocg.id,
        object_projection_graph_nodes=[],
        object_projection_graph_edges=[],
        object_projection_graph_relationships=[],
    )
    opg.object_projection_graph_nodes = [
        ObjectProjectionGraphNode(
            class_config_id=user_cc.id,
            object_projection_graph_id=opg.id,
            is_root=True,
            selection=ObjectProjectionGraphNodeSelection.one,
        ),
    ]

    return ocg, opg, user_cc


@pytest.mark.asyncio
async def test_lane_shallow_append_uses_state_index_without_before_oig(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    changes = diff_object_instance_graph_changes(
        old=g0,
        new=g1,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    pre_state_index = build_commit_state_index(g0)
    graph_hash_pre = pre_state_index.compute_hash()
    graph_hash_post = compute_hash(g1, index=build_index(g1))
    root_metadata = extract_object_instance_graph_commit_root_metadata(graph=g0)

    def _fail_full_oig_hash(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("shallow append must not hash a hydrated before_oig")

    monkeypatch.setattr(
        committer_module,
        "compute_oig_lane_hash_state",
        _fail_full_oig_hash,
    )

    store = FSCommitStore(root_dir=tmp_path)
    committer = FSLaneCommitter(store=store)
    commit_id = uuid4()
    commit = await committer.commit_to_lane_shallow(
        lane=Lane(branch_id=branch_id, lane_hash=opg.projection_hash),
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        pre_state_index=pre_state_index,
        root_metadata=root_metadata,
        changes=changes,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        commit_id=commit_id,
        source_language=ocg.language,
    )

    assert commit is not None
    assert commit.commit.id == commit_id
    assert commit.commit.commit_parents == []
    assert commit.object_instance_graph_changes == changes
    assert commit.object_instance_graph_key == root_metadata.object_instance_graph_key
    assert commit.root_source_object_id == root_metadata.root_source_object_id
    assert commit.graph_hash_pre == graph_hash_pre
    assert commit.graph_hash_post == graph_hash_post
    perf = committer.last_commit_perf_profile_snapshot()
    assert perf.get("state_index_hash_ms", -1) >= 0
    assert perf.get("head_resolve_ms", -1) >= 0
    assert perf.get("build_commit_payload_ms", -1) >= 0
    assert perf.get("validate_commit_payload_ms", -1) >= 0
    assert perf.get("append_ms", -1) >= 0

    head = await store.head(branch_id=branch_id, projection_hash=opg.projection_hash)
    assert head is not None
    assert head["commit_id"] == str(commit_id)
    assert head["graph_hash_post"] == graph_hash_post
    assert head["object_instance_graph_id"] == str(graph_id)

    record_store = FSCommitStore(root_dir=tmp_path / "record")
    record_committer = FSLaneCommitter(store=record_store)
    record_commit_id = uuid4()
    record = await record_committer.commit_record_shallow(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        pre_state_index=pre_state_index,
        root_metadata=root_metadata,
        changes=changes,
        graph_hash_pre=graph_hash_pre,
        graph_hash_post=graph_hash_post,
        author_id=author_id,
        commit_id=record_commit_id,
        source_language=ocg.language,
    )

    assert record.commit_id == record_commit_id
    assert record.envelope.parent_commit_ids == ()
    assert record.envelope.object_instance_graph_key == (
        root_metadata.object_instance_graph_key
    )
    assert record.body.commit_id == record_commit_id
    record_perf = record_committer.last_commit_perf_profile_snapshot()
    assert record_perf.get("build_commit_record_ms", -1) >= 0
    assert record_perf.get("validate_commit_record_ms", -1) >= 0
    assert record_perf.get("append_record_ms", -1) >= 0
    assert "build_commit_payload_ms" not in record_perf
    record_envelope_commit = await record_store.get_commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=record_commit_id,
    )
    assert record_envelope_commit is not None
    assert record_envelope_commit.commit.id == record_commit_id
    assert record_envelope_commit.graph_hash_pre == graph_hash_pre
    assert record_envelope_commit.graph_hash_post == graph_hash_post

    snapshots_dir = (
        tmp_path
        / "record"
        / ".aware"
        / "oig"
        / str(branch_id)
        / opg.projection_hash
        / "snapshots"
    )
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    async def _fail_full_commit_read(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("snapshot lookup must walk shallow envelopes")

    monkeypatch.setattr(FSCommitStore, "get_commit", _fail_full_commit_read)

    assert (
        await FSSnapshotStore(root_dir=tmp_path / "record").nearest_at_or_before(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            commit_id=record_commit_id,
        )
        is None
    )

    evidence_store = FSCommitStore(root_dir=tmp_path / "evidence")
    evidence_committer = FSLaneCommitter(store=evidence_store)
    evidence_commit_id = uuid4()
    evidence_body_draft = _body_draft_from_changes(changes)
    evidence_trace = CommitPerfTraceRecorder()
    with active_commit_perf_trace(evidence_trace):
        evidence_record = (
            await evidence_committer.commit_record_shallow_from_pre_state_evidence(
                branch_id=branch_id,
                projection_hash=opg.projection_hash,
                object_instance_graph_identity_id=_TEST_OIGI_ID,
                object_instance_graph_id=graph_id,
                pre_state_evidence=ObjectInstanceGraphCommitPreStateEvidence(
                    state_hash=graph_hash_pre,
                    witness_hash="test-witness-hash",
                    row_count=len(pre_state_index.rows),
                    source_contract="test.pre_state_hash_evidence.v1",
                    source_ref="state-witness.json",
                ),
                root_metadata=root_metadata,
                changes=changes,
                body_draft=evidence_body_draft,
                graph_hash_pre=graph_hash_pre,
                graph_hash_post=graph_hash_post,
                author_id=author_id,
                commit_id=evidence_commit_id,
                source_language=ocg.language,
                write_health_index=False,
            )
        )

    assert evidence_record.commit_id == evidence_commit_id
    assert evidence_record.envelope.parent_commit_ids == ()
    assert evidence_record.envelope.graph_hash_pre == graph_hash_pre
    assert evidence_record.envelope.graph_hash_post == graph_hash_post
    assert evidence_record.body.payload["c"] == OIG_COMMIT_BODY_CONTRACT
    evidence_perf = evidence_committer.last_commit_perf_profile_snapshot()
    assert evidence_perf["pre_state_hash_evidence_hit"] == 1
    assert evidence_perf["pre_state_witness_hash_evidence_hit"] == 1
    assert evidence_perf["pre_state_evidence_row_count"] == len(pre_state_index.rows)
    assert evidence_perf["build_commit_record_from_body_draft"] == 1
    assert evidence_perf["body_draft_root_count"] == len(evidence_body_draft.roots)
    assert evidence_perf["body_draft_class_instance_change_count"] >= 1
    assert evidence_perf["body_draft_attribute_change_count"] >= 1
    assert evidence_perf["body_draft_attribute_value_change_count"] >= 1
    assert evidence_perf.get("build_body_draft_commit_record_ms", -1) >= 0
    assert "state_index_hash_ms" not in evidence_perf
    assert evidence_perf.get("build_commit_record_ms", -1) >= 0
    assert evidence_perf.get("validate_commit_record_ms", -1) >= 0
    assert evidence_perf.get("append_record_ms", -1) >= 0
    assert evidence_perf["append_append_record_count"] == 1
    assert evidence_perf["append_durable_body_write_count"] == 1
    assert evidence_perf["append_durable_envelope_write_count"] == 1
    assert evidence_perf["append_durable_meta_skip_count"] == 1
    assert evidence_perf["append_durable_head_write_count"] == 1
    assert evidence_perf["append_durable_write_count"] == 3
    assert evidence_perf["append_grouped_durable_transaction_write_count"] == 3
    assert evidence_perf["append_independent_durable_write_count"] == 0
    assert evidence_perf["append_grouped_durable_transaction_count"] == 1
    assert evidence_perf["append_grouped_durable_transaction_syncfs_count"] in (0, 1)
    if evidence_perf["append_grouped_durable_transaction_syncfs_count"] == 0:
        assert evidence_perf["append_grouped_durable_transaction_file_fsync_count"] == 3
    assert evidence_perf["append_write_health_index_deferred_count"] == 1
    assert (
        await evidence_store.get_commit_health_metadata(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            commit_id=evidence_commit_id,
        )
        is None
    )
    evidence_trace_phases = {event.phase for event in evidence_trace.snapshot()}
    assert {
        "oig_lane_committer.record_shallow_pre_state_evidence."
        "pre_state_evidence_check",
        "oig_lane_committer.record_shallow_pre_state_evidence.head_resolve",
        "oig_lane_committer.record_shallow_pre_state_evidence."
        "build_body_draft_commit_record",
        "oig_lane_committer.record_shallow_pre_state_evidence.build_commit_record",
        "oig_lane_committer.record_shallow_pre_state_evidence.validate_commit_record",
        "oig_lane_committer.record_shallow_pre_state_evidence.append_record",
        "oig_commit_store.append_record.lock_wait",
        "oig_commit_store.append_record.head_read",
        "oig_commit_store.append_record.validation",
        "oig_commit_store.append_record.put_commit_record",
        "oig_commit_store.put_commit_record.write_or_validate_body",
        "oig_commit_store.put_commit_record.durable_body_written",
        "oig_commit_store.put_commit_record.write_or_validate_envelope",
        "oig_commit_store.put_commit_record.durable_envelope_written",
        "oig_commit_store.put_commit_record.write_or_validate_meta",
        "oig_commit_store.put_commit_record.durable_meta_skipped",
        "oig_commit_store.put_commit_record.write_ref_index",
        "oig_commit_store.put_commit_record.write_envelope_index",
        "oig_commit_store.put_commit_record.write_identity_sidecar_index",
        "oig_commit_store.put_commit_record.defer_health_index",
        "oig_commit_store.append_record.write_head",
        "oig_commit_store.append_record.durable_head_written",
        "oig_commit_store.append_record.grouped_durable_transaction_write",
        "oig_commit_store.append_record.grouped_durable_transaction_committed",
        "oig_commit_store.append_record.grouped_durable_transaction",
        "oig_commit_store.append_record.dispatch_watchers",
        "oig_commit_store.append_record.lock_hold",
        "oig_commit_store.append_record.total",
    } <= evidence_trace_phases

    witness_hash_pre = "test-pre-witness-hash"
    witness_hash_post = "test-post-witness-hash"
    witness_evidence_store = FSCommitStore(root_dir=tmp_path / "witness-evidence")
    witness_evidence_committer = FSLaneCommitter(store=witness_evidence_store)
    witness_evidence_commit_id = uuid4()
    witness_evidence_record = (
        await witness_evidence_committer.commit_record_shallow_from_pre_state_evidence(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            pre_state_evidence=ObjectInstanceGraphCommitPreStateEvidence(
                graph_hash_source="witness_hash",
                witness_hash=witness_hash_pre,
                row_count=len(pre_state_index.rows),
                source_contract="test.pre_state_witness_hash_evidence.v1",
                source_ref="state-witness-ref.json",
            ),
            root_metadata=root_metadata,
            changes=changes,
            graph_hash_pre=witness_hash_pre,
            graph_hash_post=witness_hash_post,
            author_id=author_id,
            commit_id=witness_evidence_commit_id,
            source_language=ocg.language,
        )
    )

    assert witness_evidence_record.commit_id == witness_evidence_commit_id
    assert witness_evidence_record.envelope.graph_hash_pre == witness_hash_pre
    assert witness_evidence_record.envelope.graph_hash_post == witness_hash_post
    assert witness_evidence_record.envelope.graph_hash_source == "witness_hash"
    stored_witness_record = await witness_evidence_store.get_commit_record(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=witness_evidence_commit_id,
    )
    assert stored_witness_record is not None
    assert stored_witness_record.envelope.graph_hash_source == "witness_hash"
    witness_head = await witness_evidence_store.head(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
    )
    assert witness_head is not None
    assert witness_head["graph_hash_source"] == "witness_hash"
    witness_evidence_perf = (
        witness_evidence_committer.last_commit_perf_profile_snapshot()
    )
    assert witness_evidence_perf["pre_state_hash_evidence_hit"] == 1
    assert witness_evidence_perf["pre_state_witness_hash_evidence_hit"] == 1
    assert witness_evidence_perf["pre_state_graph_hash_source_witness_hash_hit"] == 1
    assert "state_index_hash_ms" not in witness_evidence_perf


@pytest.mark.asyncio
async def test_lane_seed_append_uses_record_body_without_legacy_commit(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()
    ci = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="seed"),
    )
    seed_graph = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci,
        class_instances=[ci],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    pre_state_index = build_commit_state_index(seed_graph)
    graph_hash = pre_state_index.compute_hash()
    root_metadata = extract_object_instance_graph_commit_root_metadata(
        graph=seed_graph,
    )

    def _fail_full_oig_hash(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("seed append must not hash a hydrated before_oig")

    monkeypatch.setattr(
        committer_module,
        "compute_oig_lane_hash_state",
        _fail_full_oig_hash,
    )

    store = FSCommitStore(root_dir=tmp_path)
    committer = FSLaneCommitter(store=store)
    commit_id = uuid4()
    record = await committer.commit_record_seed(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
        object_instance_graph_id=graph_id,
        pre_state_index=pre_state_index,
        root_metadata=root_metadata,
        graph_hash_pre=graph_hash,
        graph_hash_post=graph_hash,
        author_id=author_id,
        commit_id=commit_id,
        source_language=ocg.language,
    )

    assert record.commit_id == commit_id
    assert record.envelope.parent_commit_ids == ()
    assert record.envelope.body_contract == OIG_COMMIT_BODY_CONTRACT
    assert record.envelope.body_ref == f"{commit_id}.body.json"
    assert record.envelope.body_size_bytes == len(record.body.canonical_bytes)
    assert record.envelope.body_sha256 == record.body.sha256
    assert record.body.payload["r"] == []
    assert record.body.commit_id == commit_id
    assert record.body.object_instance_graph_id == graph_id
    assert record.body.object_instance_graph_identity_id == _TEST_OIGI_ID
    perf = committer.last_commit_perf_profile_snapshot()
    assert perf.get("state_index_hash_ms", -1) >= 0
    assert perf.get("build_commit_record_ms", -1) >= 0
    assert perf.get("validate_commit_record_ms", -1) >= 0
    assert perf.get("append_record_ms", -1) >= 0
    assert "build_commit_payload_ms" not in perf

    head = await store.head(branch_id=branch_id, projection_hash=opg.projection_hash)
    assert head is not None
    assert head["commit_id"] == str(commit_id)
    assert head["graph_hash_post"] == graph_hash
    assert head["object_instance_graph_id"] == str(graph_id)

    stored_record = await store.get_commit_record(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit_id,
    )
    assert stored_record is not None
    assert stored_record.body.payload["r"] == []
    seed_envelope_commit = await store.get_commit(
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit_id,
    )
    assert seed_envelope_commit is not None
    assert seed_envelope_commit.commit.id == commit_id
    assert seed_envelope_commit.graph_hash_pre == graph_hash
    assert seed_envelope_commit.graph_hash_post == graph_hash


@pytest.mark.asyncio
async def test_lane_shallow_append_rejects_state_index_prehash_mismatch(
    tmp_path: Path,
) -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()
    g0 = make_rooted_object_instance_graph(
        object_config_graph=ocg,
        object_projection_graph=opg,
        root_source_object_id=user_id,
        root_class_config_id=user_cc.id,
        oig_id=graph_id,
        key="g",
        name="g",
        description="d",
    )
    ci1 = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="a"),
    )
    g1 = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci1,
        class_instances=[ci1],
        class_instance_relationships=[],
        oig_id=graph_id,
    )

    with pytest.raises(LaneStateIndexPreHashMismatchError) as exc:
        _ = await FSLaneCommitter(
            store=FSCommitStore(root_dir=tmp_path)
        ).commit_shallow(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            pre_state_index=CommitStateIndex(rows=()),
            root_metadata=extract_object_instance_graph_commit_root_metadata(graph=g0),
            changes=diff_object_instance_graph_changes(
                old=g0,
                new=g1,
                object_instance_graph_identity_id=_TEST_OIGI_ID,
            ),
            graph_hash_pre=build_commit_state_index(g0).compute_hash(),
            graph_hash_post=compute_hash(g1, index=build_index(g1)),
            author_id=uuid4(),
            source_language=ocg.language,
        )

    assert exc.value.details.branch_id == branch_id
    assert exc.value.details.projection_hash == opg.projection_hash
    assert exc.value.details.object_instance_graph_id == graph_id
    assert (
        exc.value.details.state_index_hash == CommitStateIndex(rows=()).compute_hash()
    )

    with pytest.raises(LaneStateIndexPreHashMismatchError) as evidence_exc:
        _ = await FSLaneCommitter(
            store=FSCommitStore(root_dir=tmp_path / "evidence")
        ).commit_record_shallow_from_pre_state_evidence(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            pre_state_evidence=ObjectInstanceGraphCommitPreStateEvidence(
                state_hash="wrong-pre-state-hash",
                witness_hash="wrong-witness-hash",
            ),
            root_metadata=extract_object_instance_graph_commit_root_metadata(graph=g0),
            changes=diff_object_instance_graph_changes(
                old=g0,
                new=g1,
                object_instance_graph_identity_id=_TEST_OIGI_ID,
            ),
            graph_hash_pre=build_commit_state_index(g0).compute_hash(),
            graph_hash_post=compute_hash(g1, index=build_index(g1)),
            author_id=uuid4(),
            source_language=ocg.language,
        )

    assert evidence_exc.value.details.branch_id == branch_id
    assert evidence_exc.value.details.projection_hash == opg.projection_hash
    assert evidence_exc.value.details.object_instance_graph_id == graph_id
    assert evidence_exc.value.details.state_index_hash == "wrong-pre-state-hash"


@pytest.mark.asyncio
async def test_shallow_pre_state_evidence_rejects_body_draft_existing_attribute_create(
    tmp_path: Path,
) -> None:
    name_cfg = make_attribute_config(
        owner_key=_USER_FQN,
        name="name",
        is_required=True,
        type_descriptor=_primitive_desc(),
    )
    ocg, opg, user_cc = _make_ocg_and_opg(name_cfg=name_cfg)

    from aware_orm.models.base_model import BaseORMModel

    class User(BaseORMModel):
        name: str

    author_id = uuid4()
    branch_id = uuid4()
    graph_id: UUID = uuid4()
    user_id: UUID = uuid4()

    ci_before = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="before"),
    )
    before = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci_before,
        class_instances=[ci_before],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    ci_after = build_class_instance(
        object_instance_graph_id=graph_id,
        class_config=user_cc,
        source=User(id=user_id, name="after"),
    )
    after = build_object_instance_graph_from_class_instances(
        name="g",
        description="d",
        object_config_graph_id=ocg.id,
        object_projection_graph_id=opg.id,
        root_class_instance=ci_after,
        class_instances=[ci_after],
        class_instance_relationships=[],
        oig_id=graph_id,
    )
    changes = diff_object_instance_graph_changes(
        old=before,
        new=after,
        object_instance_graph_identity_id=_TEST_OIGI_ID,
    )
    body_draft = _body_draft_from_changes(changes)
    root = body_draft.roots[0]
    class_change = root.class_instance_changes[0]
    attribute_change = class_change.attribute_changes[0]
    corrupted_body_draft = replace(
        body_draft,
        roots=(
            replace(
                root,
                class_instance_changes=(
                    replace(
                        class_change,
                        attribute_changes=(
                            replace(
                                attribute_change,
                                change=replace(
                                    attribute_change.change,
                                    type=ChangeType.create,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )

    pre_state_index = build_commit_state_index(before)
    graph_hash_pre = pre_state_index.compute_hash()
    graph_hash_post = compute_hash(after, index=build_index(after))
    store = FSCommitStore(root_dir=tmp_path)

    with pytest.raises(LaneCommitError, match="cannot CREATE existing Attribute"):
        _ = await FSLaneCommitter(
            store=store,
        ).commit_record_shallow_from_pre_state_evidence(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
            object_instance_graph_identity_id=_TEST_OIGI_ID,
            object_instance_graph_id=graph_id,
            pre_state_evidence=ObjectInstanceGraphCommitPreStateEvidence(
                state_hash=graph_hash_pre,
                row_count=len(pre_state_index.rows),
                source_contract="test.pre_state_hash_evidence.v1",
                source_ref="state-witness.json",
            ),
            pre_state_index=pre_state_index,
            root_metadata=extract_object_instance_graph_commit_root_metadata(
                graph=before,
            ),
            changes=changes,
            body_draft=corrupted_body_draft,
            graph_hash_pre=graph_hash_pre,
            graph_hash_post=graph_hash_post,
            author_id=author_id,
            source_language=ocg.language,
        )

    assert (
        await store.head(
            branch_id=branch_id,
            projection_hash=opg.projection_hash,
        )
        is None
    )
