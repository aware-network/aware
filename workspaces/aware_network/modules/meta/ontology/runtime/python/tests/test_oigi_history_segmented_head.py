from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
)
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime.commit import identity_history
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)


@pytest.mark.asyncio
async def test_oigi_segmented_head_uses_derived_post_state(monkeypatch) -> None:
    graph_id = uuid4()
    class_config_id = uuid4()
    class_instance_id = uuid4()
    source_object_id = uuid4()
    projection_graph_id = uuid4()
    commit_id = uuid4()
    root = ClassInstance.model_construct(
        id=class_instance_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
        attributes=[],
    )
    graph = ObjectInstanceGraph.model_construct(
        id=graph_id,
        key="oigi",
        name="OIGI",
        description=None,
        object_projection_graph_id=projection_graph_id,
        root_class_instance_id=class_instance_id,
        root_class_instance=root,
        class_instances=[root],
        class_instance_relationships=[],
        hash="post-state-hash",
    )
    state_index = CommitStateIndex(
        rows=(
            CommitStateRow(
                kind="NODE",
                key=str(class_config_id),
                value=str(class_instance_id),
            ),
        )
    )
    put_state_snapshot_rows = AsyncMock()
    snapshot_store = SimpleNamespace(
        put_state_snapshot_rows=put_state_snapshot_rows,
    )
    snapshot_store_factory = lambda **_kwargs: snapshot_store
    monkeypatch.setattr(
        identity_history,
        "FSSnapshotStore",
        snapshot_store_factory,
    )
    perf_ms: dict[str, int] = {}

    await identity_history._publish_oigi_segmented_head_snapshot(
        store=SimpleNamespace(aware_root=Path("/tmp/aware-test")),
        branch_id=graph_id,
        projection_hash="oigi-projection",
        commit_id=commit_id,
        graph=graph,
        state_index=state_index,
        perf_ms=perf_ms,
        perf_metric_prefix="test_oigi",
    )

    put_state_snapshot_rows.assert_awaited_once()
    call = put_state_snapshot_rows.await_args.kwargs
    assert call["commit_id"] == commit_id
    assert call["object_instance_graph_id"] == graph_id
    assert call["graph_hash"] == "post-state-hash"
    assert call["state_index"] is state_index
    assert call["write_state_witness"] is True
    assert call["write_state_class_segment_index"] is True
    assert perf_ms["test_oigi_segmented_head_snapshot_written_count"] == 1


@pytest.mark.asyncio
async def test_oigi_segmented_head_skips_without_post_state(monkeypatch) -> None:
    snapshot_store_factory = AsyncMock()
    monkeypatch.setattr(
        identity_history,
        "FSSnapshotStore",
        snapshot_store_factory,
    )
    perf_ms: dict[str, int] = {}

    await identity_history._publish_oigi_segmented_head_snapshot(
        store=SimpleNamespace(aware_root=Path("/tmp/aware-test")),
        branch_id=uuid4(),
        projection_hash="oigi-projection",
        commit_id=uuid4(),
        graph=SimpleNamespace(),
        state_index=None,
        perf_ms=perf_ms,
        perf_metric_prefix="test_oigi",
    )

    snapshot_store_factory.assert_not_awaited()
    assert perf_ms["test_oigi_segmented_head_snapshot_unavailable_count"] == 1


@pytest.mark.asyncio
async def test_state_graph_returns_validated_state_evidence(tmp_path: Path) -> None:
    graph_id = uuid4()
    class_config_id = uuid4()
    class_instance_id = uuid4()
    source_object_id = uuid4()
    projection_graph_id = uuid4()
    commit_id = uuid4()
    branch_id = uuid4()
    root = ClassInstance.model_construct(
        id=class_instance_id,
        class_config_id=class_config_id,
        source_object_id=source_object_id,
        object_instance_graph_id=graph_id,
        class_instance_attributes=[],
        attributes=[],
    )
    state_index = CommitStateIndex(
        rows=(
            CommitStateRow(
                kind="NODE",
                key=str(class_config_id),
                value=str(class_instance_id),
            ),
        )
    )
    graph = ObjectInstanceGraph.model_construct(
        id=graph_id,
        key="oigi",
        name="OIGI",
        description=None,
        object_projection_graph_id=projection_graph_id,
        root_class_instance_id=class_instance_id,
        root_class_instance=root,
        class_instances=[root],
        class_instance_relationships=[],
        hash=state_index.compute_hash(),
    )
    store = FSSnapshotStore(root_dir=tmp_path)
    await store.put_state_snapshot_rows(
        branch_id=branch_id,
        projection_hash="oigi-projection",
        commit_id=commit_id,
        object_instance_graph_id=graph_id,
        graph_hash=graph.hash,
        graph_meta={
            "id": graph_id,
            "key": graph.key,
            "name": graph.name,
            "object_projection_graph_id": projection_graph_id,
            "root_class_instance_id": class_instance_id,
            "root_source_object_id": source_object_id,
            "hash": graph.hash,
        },
        class_instances=graph.class_instances,
        class_instance_relationships=graph.class_instance_relationships,
        state_index=state_index,
    )

    loaded = await store.get_snapshot_state_graph(
        branch_id=branch_id,
        projection_hash="oigi-projection",
        commit_id=commit_id,
        expected_object_instance_graph_id=graph_id,
        expected_graph_hash=graph.hash,
    )

    assert loaded is not None
    _loaded_graph, indexes = loaded
    assert indexes["commit_state_hash"] == state_index.compute_hash()
    assert indexes["commit_state_index"] == state_index
