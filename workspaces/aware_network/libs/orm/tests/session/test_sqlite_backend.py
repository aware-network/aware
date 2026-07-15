from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_orm.db import DBBootExecutionError
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)
from aware_orm.session.backends import SqlitePersistenceConfig
from aware_orm.session.session import Session


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_registry(*, tmp_path: Path, environment_id, table_sql: str) -> tuple[Path, Path]:
    sql_root = tmp_path / "sqlite" / "kernel"
    _write(sql_root / "window_layout_state.sql", table_sql)

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=sql_root.parent,
        source_label="kernel-interface-db",
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[entry]),
    )
    return registry_path, sql_root.parent


@pytest.mark.asyncio
async def test_sqlite_backend_requires_explicit_config() -> None:
    with pytest.raises(ValueError, match="sqlite_backend_config"):
        _ = Session(skip_db=False, backend_name="sqlite")


@pytest.mark.asyncio
async def test_sqlite_backend_commits_reads_updates_and_deletes(tmp_path: Path) -> None:
    environment_id = uuid4()
    registry_path, _sql_root = _write_registry(
        tmp_path=tmp_path,
        environment_id=environment_id,
        table_sql="""
CREATE TABLE window_layout_state (
  id TEXT PRIMARY KEY NOT NULL,
  actor_id TEXT NOT NULL,
  layout_profile TEXT NOT NULL
);
""".strip()
        + "\n",
    )
    config = SqlitePersistenceConfig(
        database_path=tmp_path / "state" / "kernel.sqlite",
        registry_path=registry_path,
        environment_id=environment_id,
    )
    session = Session(skip_db=False, backend_name="sqlite", sqlite_backend_config=config)

    session.add_insert(
        "INSERT INTO kernel.window_layout_state(id, actor_id, layout_profile) VALUES($1, $2, $3)",
        ("pane-main", "actor-1", "default"),
    )
    await session.commit()

    rows = await session.execute_query(
        "SELECT * FROM kernel.window_layout_state WHERE id = $1",
        "pane-main",
    )
    assert rows == [{"id": "pane-main", "actor_id": "actor-1", "layout_profile": "default"}]

    session.add_update(
        "UPDATE kernel.window_layout_state SET layout_profile = $1 WHERE id = $2",
        ("focus", "pane-main"),
    )
    await session.commit()

    updated = await session.execute_query(
        "SELECT * FROM kernel.window_layout_state WHERE id = $1",
        "pane-main",
    )
    assert updated[0]["layout_profile"] == "focus"

    session.add_delete(
        "DELETE FROM kernel.window_layout_state WHERE id = $1",
        ("pane-main",),
    )
    await session.commit()

    assert await session.execute_query(
        "SELECT * FROM kernel.window_layout_state WHERE id = $1",
        "pane-main",
    ) == []


@pytest.mark.asyncio
async def test_sqlite_backend_supports_memory_database(tmp_path: Path) -> None:
    environment_id = uuid4()
    registry_path, _sql_root = _write_registry(
        tmp_path=tmp_path,
        environment_id=environment_id,
        table_sql='CREATE TABLE window_layout_state (id TEXT PRIMARY KEY NOT NULL, layout_profile TEXT NOT NULL);\n',
    )
    config = SqlitePersistenceConfig(
        database_path=":memory:",
        registry_path=registry_path,
        environment_id=environment_id,
    )
    session = Session(skip_db=False, backend_name="sqlite", sqlite_backend_config=config)

    session.add_insert(
        "INSERT INTO kernel.window_layout_state(id, layout_profile) VALUES($1, $2)",
        ("pane-main", "default"),
    )
    await session.commit()

    rows = await session.execute_query(
        "SELECT * FROM kernel.window_layout_state WHERE id = $1",
        "pane-main",
    )
    assert rows[0]["layout_profile"] == "default"


@pytest.mark.asyncio
async def test_sqlite_backend_rollback_clears_pending_operations(tmp_path: Path) -> None:
    environment_id = uuid4()
    registry_path, _sql_root = _write_registry(
        tmp_path=tmp_path,
        environment_id=environment_id,
        table_sql='CREATE TABLE window_layout_state (id TEXT PRIMARY KEY NOT NULL, layout_profile TEXT NOT NULL);\n',
    )
    config = SqlitePersistenceConfig(
        database_path=":memory:",
        registry_path=registry_path,
        environment_id=environment_id,
    )
    session = Session(skip_db=False, backend_name="sqlite", sqlite_backend_config=config)

    session.add_insert(
        "INSERT INTO kernel.window_layout_state(id, layout_profile) VALUES($1, $2)",
        ("pane-main", "default"),
    )
    assert session.get_pending_operations_count()["inserts"] == 1

    await session.rollback()
    assert session.get_pending_operations_count()["total"] == 0
    assert await session.execute_query("SELECT * FROM kernel.window_layout_state") == []


@pytest.mark.asyncio
async def test_sqlite_backend_fails_closed_on_registry_payload_drift(tmp_path: Path) -> None:
    environment_id = uuid4()
    registry_path, db_root = _write_registry(
        tmp_path=tmp_path,
        environment_id=environment_id,
        table_sql='CREATE TABLE window_layout_state (id TEXT PRIMARY KEY NOT NULL, layout_profile TEXT NOT NULL);\n',
    )
    database_path = tmp_path / "state" / "kernel.sqlite"

    first_session = Session(
        skip_db=False,
        backend_name="sqlite",
        sqlite_backend_config=SqlitePersistenceConfig(
            database_path=database_path,
            registry_path=registry_path,
            environment_id=environment_id,
        ),
    )
    _ = await first_session.execute_query("SELECT * FROM kernel.window_layout_state")

    _write(
        db_root / "kernel" / "window_layout_state.sql",
        """
CREATE TABLE window_layout_state (
  id TEXT PRIMARY KEY NOT NULL,
  layout_profile TEXT NOT NULL,
  actor_id TEXT
);
""".strip()
        + "\n",
    )
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=db_root,
        source_label="kernel-interface-db",
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[entry]),
    )

    second_session = Session(
        skip_db=False,
        backend_name="sqlite",
        sqlite_backend_config=SqlitePersistenceConfig(
            database_path=database_path,
            registry_path=registry_path,
            environment_id=environment_id,
        ),
    )
    with pytest.raises(DBBootExecutionError, match="different ocg_hash"):
        _ = await second_session.execute_query("SELECT * FROM kernel.window_layout_state")
