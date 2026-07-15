from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_code.package import snapshot_replay
from aware_meta.graph.instance.commit.state_index import (
    CommitStateIndex,
    CommitStateRow,
)


@pytest.mark.asyncio
async def test_snapshot_replay_loads_canonical_segmented_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    object_instance_graph_id = uuid4()
    code_package_id = uuid4()
    root_class_instance_id = uuid4()
    child_class_instance_id = uuid4()
    relationship_id = uuid4()
    projection_hash = "code-package-projection"
    graph_hash = "graph-hash"
    segments = (
        SimpleNamespace(kind="CLASS", key=f"class:{root_class_instance_id}"),
        SimpleNamespace(kind="CLASS", key=f"class:{child_class_instance_id}"),
        SimpleNamespace(
            kind="EDGE",
            key=(
                f"edge:{relationship_id}:{root_class_instance_id}"
                f"->{child_class_instance_id}"
            ),
        ),
    )
    metadata = SimpleNamespace(
        object_instance_graph_id=object_instance_graph_id,
        graph_hash=graph_hash,
        payload={
            "graph": {
                "id": str(object_instance_graph_id),
                "root_class_instance_id": str(root_class_instance_id),
                "root_source_object_id": str(code_package_id),
                "hash": graph_hash,
            }
        },
        witness_ref=SimpleNamespace(segments=segments),
        witness_cursor_summary=SimpleNamespace(cursor_hash=graph_hash),
    )
    selection = SimpleNamespace(
        class_segments_by_id={
            root_class_instance_id: SimpleNamespace(
                snapshot_payload={
                    "id": str(root_class_instance_id),
                    "source_object_id": str(code_package_id),
                }
            ),
            child_class_instance_id: SimpleNamespace(
                snapshot_payload={"id": str(child_class_instance_id)}
            ),
        }
    )

    class FakeSnapshotStore:
        async def get_snapshot_state_rows(self, **_kwargs: object) -> None:
            return None

        def snapshot_state_class_segment_index_metadata(
            self,
            **_kwargs: object,
        ) -> object:
            return metadata

        async def get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
            self,
            **_kwargs: object,
        ) -> object:
            return selection

    monkeypatch.setattr(
        snapshot_replay,
        "FSSnapshotStore",
        lambda **_kwargs: FakeSnapshotStore(),
    )

    payload = await snapshot_replay.load_code_package_text_snapshot_payload_at_commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        code_package_id=code_package_id,
        commit_id=commit_id,
        object_instance_graph_id=object_instance_graph_id,
        graph_hash_post=graph_hash,
    )

    assert payload is not None
    assert payload["root_class_instance"]["id"] == str(root_class_instance_id)
    assert payload["class_instance_relationships"] == [
        {
            "class_config_relationship_id": str(relationship_id),
            "source_class_instance_id": str(root_class_instance_id),
            "target_class_instance_id": str(child_class_instance_id),
        }
    ]


@pytest.mark.asyncio
async def test_snapshot_replay_reconstructs_segmented_state_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    object_instance_graph_id = uuid4()
    root_class_instance_id = uuid4()
    child_class_instance_id = uuid4()
    root_class_config_id = uuid4()
    child_class_config_id = uuid4()
    root_source_object_id = uuid4()
    child_source_object_id = uuid4()
    relationship_id = uuid4()
    projection_hash = "code-package-projection"
    graph_hash = "graph-hash"
    root_rows = (
        CommitStateRow(
            kind="NODE",
            key=str(root_class_config_id),
            value=str(root_class_instance_id),
        ),
    )
    child_rows = (
        CommitStateRow(
            kind="NODE",
            key=str(child_class_config_id),
            value=str(child_class_instance_id),
        ),
    )
    edge_row = CommitStateRow(
        kind="EDGE",
        key=str(relationship_id),
        value=f"{root_class_instance_id}->{child_class_instance_id}",
    )
    state_rows = (*root_rows, *child_rows, edge_row)
    segments = (
        SimpleNamespace(kind="CLASS", key=f"class:{root_class_instance_id}"),
        SimpleNamespace(kind="CLASS", key=f"class:{child_class_instance_id}"),
        SimpleNamespace(
            kind="EDGE",
            key=(
                f"edge:{relationship_id}:{root_class_instance_id}"
                f"->{child_class_instance_id}"
            ),
        ),
    )
    metadata = SimpleNamespace(
        object_instance_graph_id=object_instance_graph_id,
        graph_hash=graph_hash,
        state_hash=CommitStateIndex(rows=state_rows).compute_hash(),
        payload={
            "graph": {
                "id": str(object_instance_graph_id),
                "root_class_instance_id": str(root_class_instance_id),
                "root_source_object_id": str(root_source_object_id),
                "hash": graph_hash,
            }
        },
        witness_ref=SimpleNamespace(segments=segments),
        witness_cursor_summary=SimpleNamespace(cursor_hash="cursor-hash"),
    )
    class_segments_by_id = {
        root_class_instance_id: SimpleNamespace(
            rows_text=(f"NODE\t{root_class_config_id}\t{root_class_instance_id}\n"),
            snapshot_payload={
                "id": str(root_class_instance_id),
                "source_object_id": str(root_source_object_id),
                "object_instance_graph_id": str(object_instance_graph_id),
                "class_config_id": str(root_class_config_id),
            },
        ),
        child_class_instance_id: SimpleNamespace(
            rows_text=(f"NODE\t{child_class_config_id}\t{child_class_instance_id}\n"),
            snapshot_payload={
                "id": str(child_class_instance_id),
                "source_object_id": str(child_source_object_id),
                "object_instance_graph_id": str(object_instance_graph_id),
                "class_config_id": str(child_class_config_id),
            },
        ),
    }

    class FakeSnapshotStore:
        def snapshot_state_class_segment_index_metadata(
            self,
            **_kwargs: object,
        ) -> object:
            return metadata

        async def get_snapshot_state_indexed_raw_class_segments_by_witness_cursor(
            self,
            **_kwargs: object,
        ) -> object:
            return SimpleNamespace(class_segments_by_id=class_segments_by_id)

    monkeypatch.setattr(
        snapshot_replay,
        "FSSnapshotStore",
        lambda **_kwargs: FakeSnapshotStore(),
    )

    selection = (
        await snapshot_replay.load_code_package_text_snapshot_state_selection_at_commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            commit_id=commit_id,
            class_instance_ids=(root_class_instance_id,),
            object_instance_graph_id=object_instance_graph_id,
            graph_hash_post=graph_hash,
            include_state_row_maps=True,
        )
    )

    assert selection is not None
    assert selection.state_rows == state_rows
    assert set(selection.class_instances_by_id) == {root_class_instance_id}
    assert selection.state_row_maps is not None
    assert selection.state_row_maps.relationship_keys == frozenset(
        {(relationship_id, root_class_instance_id, child_class_instance_id)}
    )
    assert selection.payload["state_hash"] == metadata.state_hash
