from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_interface import (
    InterfaceLaneStores,
    InterfaceLocalDb,
    InterfaceLocalDbConfig,
    LocalCommitActionRecord,
    LocalCommitRecord,
    LocalLaneCommitRecord,
    LocalLaneHeadRecord,
    LocalProjectionCursorRecord,
    LocalSnapshotRecord,
)
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)


_REPO_ROOT = Path(__file__).resolve().parents[8]
_INTERFACE_DB_SQL_ROOT = _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "interface" / "services" / "interface" / "db" / "sqlite"


def _write_registry(*, tmp_path: Path, environment_id: UUID) -> Path:
    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=_INTERFACE_DB_SQL_ROOT,
        source_label="interface-db",
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[entry]),
    )
    return registry_path


def _build_stores(tmp_path: Path) -> tuple[InterfaceLocalDb, InterfaceLaneStores]:
    environment_id = uuid4()
    registry_path = _write_registry(tmp_path=tmp_path, environment_id=environment_id)
    db = InterfaceLocalDb(
        config=InterfaceLocalDbConfig(
            database_path=tmp_path / "state" / "interface.sqlite",
            registry_path=registry_path,
            environment_id=environment_id,
        )
    )
    return db, InterfaceLaneStores(db=db)


@pytest.mark.asyncio
async def test_interface_lane_stores_round_trip_all_canonical_tables(
    tmp_path: Path,
) -> None:
    _, stores = _build_stores(tmp_path)

    branch_id = str(uuid4())
    projection_hash = "projection-main"
    commit_id = str(uuid4())
    action_id = str(uuid4())
    lane_commit_id = str(uuid4())
    lane_id = str(uuid4())
    cursor_id = str(uuid4())
    snapshot_id = str(uuid4())

    commit = LocalCommitRecord(
        branch_id=branch_id,
        id=commit_id,
        commit_id=commit_id,
        projection_hash=projection_hash,
        parent_commit_id=None,
        graph_hash_pre="graph-pre",
        graph_hash_post="graph-post",
        object_instance_graph_id=str(uuid4()),
        object_instance_graph_commit_id=str(uuid4()),
        payload_json='{"kind":"commit"}',
    )
    action = LocalCommitActionRecord(
        id=action_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        operation_label="Workspace.ensure_snapshot",
        call_target="instance",
        function_id=str(uuid4()),
        object_id=str(uuid4()),
        class_instance_identity_id=str(uuid4()),
        actor_id=str(uuid4()),
    )
    lane_commit = LocalLaneCommitRecord(
        id=lane_commit_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    )
    lane_head = LocalLaneHeadRecord(
        id=lane_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        head_commit_id=commit_id,
        graph_hash_post="graph-post",
        object_instance_graph_id=commit.object_instance_graph_id,
        root_object_instance_id=str(uuid4()),
        v=2,
    )
    projection_cursor = LocalProjectionCursorRecord(
        id=cursor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        head_commit_id=commit_id,
        projector_id="workspace.sqlite.projector",
        graph_hash_post="graph-post",
        v=3,
    )
    snapshot = LocalSnapshotRecord(
        id=snapshot_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        oig_json='{"objects":[]}',
        indexes_json='{"byId":{}}',
        v=4,
    )

    await stores.save_commit(commit)
    await stores.save_commit_action(action)
    await stores.save_lane_commit(lane_commit)
    await stores.save_lane_head(lane_head)
    await stores.save_projection_cursor(projection_cursor)
    await stores.save_snapshot(snapshot)

    assert (
        await stores.load_commit(
            branch_id=branch_id, commit_id=commit_id, projection_hash=projection_hash
        )
        == commit
    )
    assert (
        await stores.load_commit_action(
            branch_id=branch_id,
            action_id=action_id,
            projection_hash=projection_hash,
        )
        == action
    )
    assert (
        await stores.load_lane_commit(
            branch_id=branch_id,
            lane_commit_id=lane_commit_id,
            projection_hash=projection_hash,
        )
        == lane_commit
    )
    assert (
        await stores.load_lane_head(
            branch_id=branch_id, lane_id=lane_id, projection_hash=projection_hash
        )
        == lane_head
    )
    assert (
        await stores.load_projection_cursor(
            branch_id=branch_id,
            cursor_id=cursor_id,
            projection_hash=projection_hash,
        )
        == projection_cursor
    )
    assert (
        await stores.load_snapshot(
            branch_id=branch_id,
            snapshot_id=snapshot_id,
            projection_hash=projection_hash,
        )
        == snapshot
    )

    assert await stores.list_commits(
        branch_id=branch_id, projection_hash=projection_hash
    ) == (commit,)
    assert await stores.list_commit_actions(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    ) == (action,)
    assert await stores.list_lane_commits(
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
    ) == (lane_commit,)
    assert await stores.list_lane_heads(
        branch_id=branch_id, projection_hash=projection_hash
    ) == (lane_head,)
    assert await stores.list_projection_cursors(
        branch_id=branch_id,
        projection_hash=projection_hash,
        projector_id="workspace.sqlite.projector",
    ) == (projection_cursor,)
    assert await stores.list_snapshots(
        branch_id=branch_id, projection_hash=projection_hash
    ) == (snapshot,)


@pytest.mark.asyncio
async def test_interface_lane_stores_commit_upsert_preserves_dependent_rows(
    tmp_path: Path,
) -> None:
    db, stores = _build_stores(tmp_path)

    branch_id = str(uuid4())
    projection_hash = "projection-main"
    commit_id = str(uuid4())
    action_id = str(uuid4())

    initial_commit = LocalCommitRecord(
        branch_id=branch_id,
        id=commit_id,
        commit_id=commit_id,
        projection_hash=projection_hash,
        graph_hash_post="graph-post-v1",
        payload_json='{"kind":"v1"}',
    )
    updated_commit = LocalCommitRecord(
        branch_id=branch_id,
        id=commit_id,
        commit_id=commit_id,
        projection_hash=projection_hash,
        graph_hash_post="graph-post-v2",
        payload_json='{"kind":"v2"}',
    )
    action = LocalCommitActionRecord(
        id=action_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        commit_id=commit_id,
        operation_label="Workspace.refresh",
    )

    await stores.save_commit(initial_commit)
    await stores.save_commit_action(action)
    await stores.save_commit(updated_commit)

    assert (
        await stores.load_commit(
            branch_id=branch_id, commit_id=commit_id, projection_hash=projection_hash
        )
        == updated_commit
    )
    assert (
        await stores.load_commit_action(
            branch_id=branch_id,
            action_id=action_id,
            projection_hash=projection_hash,
        )
        == action
    )

    rows = await db.execute_query(
        """
        SELECT COUNT(*) AS row_count
        FROM commit_store.local_oig_commit
        WHERE branch_id = $1 AND id = $2 AND projection_hash = $3
        """,
        branch_id,
        commit_id,
        projection_hash,
    )

    assert rows == [{"row_count": 1}]
