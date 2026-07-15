from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_interface.local_db import InterfaceLocalDb, InterfaceLocalDbConfig
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


@pytest.mark.asyncio
async def test_interface_local_db_ensure_ready_installs_generated_schema(
    tmp_path: Path,
) -> None:
    environment_id = uuid4()
    registry_path = _write_registry(tmp_path=tmp_path, environment_id=environment_id)
    db = InterfaceLocalDb(
        config=InterfaceLocalDbConfig(
            database_path=tmp_path / "state" / "interface.sqlite",
            registry_path=registry_path,
            environment_id=environment_id,
        )
    )

    await db.ensure_ready()

    assert Path(db.database_target).exists()
    tables = await db.list_tables()
    assert "local_oig_commit" in tables
    assert "local_oig_lane_head" in tables
    assert "local_oig_projection_cursor" in tables
    assert await db.table_exists("local_oig_snapshot") is True


@pytest.mark.asyncio
async def test_interface_local_db_session_can_write_generated_tables(
    tmp_path: Path,
) -> None:
    environment_id = uuid4()
    registry_path = _write_registry(tmp_path=tmp_path, environment_id=environment_id)
    db = InterfaceLocalDb(
        config=InterfaceLocalDbConfig(
            database_path=tmp_path / "state" / "interface.sqlite",
            registry_path=registry_path,
            environment_id=environment_id,
        )
    )

    branch_id = str(uuid4())
    commit_id = str(uuid4())
    projection_hash = "projection-test"
    payload_json = '{"kind":"bootstrap"}'

    session = db.new_session()
    try:
        session.add_insert(
            """
            INSERT INTO commit_store.local_oig_commit(
              branch_id,
              id,
              commit_id,
              projection_hash,
              graph_hash_pre,
              graph_hash_post,
              object_instance_graph_id,
              object_instance_graph_commit_id,
              payload_json
            ) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            (
                branch_id,
                commit_id,
                commit_id,
                projection_hash,
                None,
                "hash-post",
                str(uuid4()),
                str(uuid4()),
                payload_json,
            ),
        )
        await session.commit()
    finally:
        db.close_session(session)

    rows = await db.execute_query(
        """
        SELECT payload_json, graph_hash_post
        FROM commit_store.local_oig_commit
        WHERE branch_id = $1 AND id = $2 AND projection_hash = $3
        """,
        branch_id,
        commit_id,
        projection_hash,
    )

    assert rows == [{"payload_json": payload_json, "graph_hash_post": "hash-post"}]
