from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from aware_history_ontology.change.change import Change
from aware_history_ontology.change.change_enums import ChangeType
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta.graph.instance.commit.builder import (
    build_object_instance_graph_commit_from_changes,
)
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
    LaneHeadCommitReceipt,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change import (
    ObjectInstanceGraphChange,
)
from aware_meta_ontology.graph.instance.object_instance_graph_change_enums import (
    ObjectInstanceGraphChangeType,
)
from aware_meta_ontology.stable_ids import stable_class_instance_id
from aware_meta.graph.instance.hash import compute_hash
from aware_meta.graph.instance.index import build_index
from aware_orm.session.autobind import disable_autobind


def _make_before_oig(*, oig_id, root_object_id) -> ObjectInstanceGraph:
    root_class_config_id = uuid4()
    root_class_instance_id = stable_class_instance_id(
        object_instance_graph_id=oig_id,
        class_config_id=root_class_config_id,
        source_object_id=root_object_id,
    )
    with disable_autobind():
        root = ClassInstance(
            id=root_class_instance_id,
            object_instance_graph_id=oig_id,
            class_config_id=root_class_config_id,
            source_object_id=root_object_id,
            attributes=[],
        )
        graph = ObjectInstanceGraph(
            id=oig_id,
            key="watch",
            name="watch",
            description=None,
            object_projection_graph_id=uuid4(),
            root_class_instance_id=root.id,
            root_class_instance=root,
            class_instances=[root],
            class_instance_relationships=[],
            hash="",
        )
    graph.hash = compute_hash(graph, index=build_index(graph))
    return graph


@pytest.mark.asyncio
async def test_fs_commit_store_emits_lane_head_receipt(tmp_path) -> None:
    store = FSCommitStore(root_dir=tmp_path)

    received: list[LaneHeadCommitReceipt] = []
    event = asyncio.Event()

    async def watcher(receipt: LaneHeadCommitReceipt) -> None:
        received.append(receipt)
        event.set()

    FSCommitStore.register_lane_head_watcher(watcher)
    try:
        branch_id = uuid4()
        projection_hash = "sha256:test:lane"
        oigi_id = uuid4()
        oig_id = uuid4()
        root_object_id = uuid4()

        with disable_autobind():
            change = Change(
                id=uuid4(),
                key="watch-root",
                change_deltas=[],
                type=ChangeType.update,
                created_at=datetime.now(timezone.utc),
            )
            oig_change = ObjectInstanceGraphChange(
                id=uuid4(),
                object_instance_graph_identity_id=oigi_id,
                change=change,
                change_id=change.id,
                class_instance_changes=[],
                class_instance_relationship_changes=[],
                type=ObjectInstanceGraphChangeType.object_instance,
                object_instance_graph_id=oig_id,
            )

        author_id = uuid4()
        before_oig = _make_before_oig(oig_id=oig_id, root_object_id=root_object_id)
        commit = build_object_instance_graph_commit_from_changes(
            before_oig=before_oig,
            changes=[oig_change],
            branch_id=branch_id,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=oig_id,
            projection_hash=projection_hash,
            graph_hash_pre="0" * 64,
            graph_hash_post="1" * 64,
            author_id=author_id,
        )

        await store.append(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
            root_object_id=root_object_id,
        )

        await asyncio.wait_for(event.wait(), timeout=1.0)
        assert received
        receipt = received[0]
        assert receipt.branch_id == branch_id
        assert receipt.projection_hash == projection_hash
        assert receipt.commit_id == commit.commit.id
        assert receipt.graph_hash_post == commit.graph_hash_post
        assert receipt.object_instance_graph_id == oig_id
        assert receipt.root_object_id == root_object_id
        assert receipt.author_id == author_id
        assert receipt.class_instance_identity_id is None
    finally:
        FSCommitStore.unregister_lane_head_watcher(watcher)


@pytest.mark.asyncio
async def test_fs_commit_store_receipt_includes_class_instance_identity_id(
    tmp_path,
) -> None:
    store = FSCommitStore(root_dir=tmp_path)

    received: list[LaneHeadCommitReceipt] = []
    event = asyncio.Event()

    async def watcher(receipt: LaneHeadCommitReceipt) -> None:
        received.append(receipt)
        event.set()

    FSCommitStore.register_lane_head_watcher(watcher)
    try:
        branch_id = uuid4()
        projection_hash = "sha256:test:lane"
        oigi_id = uuid4()
        oig_id = uuid4()
        class_instance_identity_id = uuid4()
        root_object_id = uuid4()

        with disable_autobind():
            change = Change(
                id=uuid4(),
                key="watch-root",
                change_deltas=[],
                type=ChangeType.update,
                created_at=datetime.now(timezone.utc),
            )
            oig_change = ObjectInstanceGraphChange(
                id=uuid4(),
                object_instance_graph_identity_id=oigi_id,
                change=change,
                change_id=change.id,
                class_instance_changes=[],
                class_instance_relationship_changes=[],
                type=ObjectInstanceGraphChangeType.object_instance,
                object_instance_graph_id=oig_id,
            )

        author_id = uuid4()
        before_oig = _make_before_oig(oig_id=oig_id, root_object_id=root_object_id)
        commit = build_object_instance_graph_commit_from_changes(
            before_oig=before_oig,
            changes=[oig_change],
            branch_id=branch_id,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=oig_id,
            projection_hash=projection_hash,
            graph_hash_pre="0" * 64,
            graph_hash_post="1" * 64,
            author_id=author_id,
        )

        await store.append(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit=commit,
            commit_action=CommitActionDescriptor(
                operation_label="Identity.signup_via_profile",
                class_instance_identity_id=class_instance_identity_id,
            ),
        )

        await asyncio.wait_for(event.wait(), timeout=1.0)
        assert received
        receipt = received[0]
        assert receipt.class_instance_identity_id == class_instance_identity_id
        assert receipt.commit_action is not None
        assert (
            receipt.commit_action.class_instance_identity_id
            == class_instance_identity_id
        )
    finally:
        FSCommitStore.unregister_lane_head_watcher(watcher)
