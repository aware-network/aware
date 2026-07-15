from __future__ import annotations

from pathlib import Path
import sqlite3
from uuid import UUID
from uuid import uuid4

import pytest

from aware_orm.db.adapters import (
    DBBootAdapterName,
    POSTGRES_DB_BOOT_ADAPTER,
    SQLITE_DB_BOOT_ADAPTER,
    resolve_db_boot_adapter,
)
from aware_orm.db.boot import ensure_db_schema_installed
from aware_orm.db.contracts import (
    DBBootExecutionError,
    DBBootPlanError,
    DBBootResult,
    SQLBootPlan,
)


class _CustomAdapter:
    name: DBBootAdapterName = "sqlite"

    async def ensure_schema_installed(
        self,
        *,
        connection: object,
        plan: SQLBootPlan,
        environment_id: UUID,
        ocg_hash: str,
        ocg_head_commit_id: UUID | None = None,
    ) -> DBBootResult:
        _ = connection
        return DBBootResult(
            installed=False,
            environment_id=environment_id,
            ocg_hash=ocg_hash,
            ocg_head_commit_id=ocg_head_commit_id,
            sql_roots=plan.sql_roots,
            schema_count=0,
            step_count=0,
        )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolve_db_boot_adapter_default_and_named() -> None:
    assert resolve_db_boot_adapter() is POSTGRES_DB_BOOT_ADAPTER
    assert resolve_db_boot_adapter("postgres") is POSTGRES_DB_BOOT_ADAPTER
    assert resolve_db_boot_adapter("sqlite") is SQLITE_DB_BOOT_ADAPTER


def test_resolve_db_boot_adapter_accepts_structural_custom_adapter() -> None:
    adapter = _CustomAdapter()
    assert resolve_db_boot_adapter(adapter) is adapter


def test_resolve_db_boot_adapter_rejects_invalid_name() -> None:
    with pytest.raises(DBBootPlanError, match="Unsupported DB boot adapter"):
        _ = resolve_db_boot_adapter("mysql")


@pytest.mark.asyncio
async def test_sqlite_boot_adapter_validates_connection_shape() -> None:
    with pytest.raises(DBBootExecutionError, match="execute/commit/rollback"):
        _ = await SQLITE_DB_BOOT_ADAPTER.ensure_schema_installed(
            connection=object(),
            plan=SQLBootPlan(sql_roots=(Path("/tmp"),), schemas=(), steps=()),
            environment_id=uuid4(),
            ocg_hash="sha256:test",
        )


@pytest.mark.asyncio
async def test_sqlite_boot_adapter_applies_plan_and_is_idempotent(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "workspace" / "window_layout.sql",
        """
CREATE TABLE window_layout (
  id TEXT PRIMARY KEY NOT NULL,
  profile TEXT NOT NULL
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    conn = sqlite3.connect(":memory:")
    try:
        first = await ensure_db_schema_installed(
            connection=conn,
            sql_root=sql_root,
            environment_id=env_id,
            ocg_hash="sha256:test",
            adapter="sqlite",
        )
        assert first.installed is True

        marker = conn.execute(
            "SELECT ocg_hash FROM aware_bootstrap_marker WHERE environment_id = ?",
            (str(env_id),),
        ).fetchone()
        assert marker is not None
        assert marker[0] == "sha256:test"

        _ = conn.execute(
            "INSERT INTO window_layout (id, profile) VALUES (?, ?)",
            ("pane-main", "default"),
        )
        row = conn.execute("SELECT profile FROM window_layout WHERE id = ?", ("pane-main",)).fetchone()
        assert row is not None
        assert row[0] == "default"

        second = await ensure_db_schema_installed(
            connection=conn,
            sql_root=sql_root,
            environment_id=env_id,
            ocg_hash="sha256:test",
            adapter="sqlite",
        )
        assert second.installed is False
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_sqlite_boot_adapter_fails_on_ocg_hash_mismatch(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"
    _write(sql_root / "workspace" / "state.sql", "CREATE TABLE state (id TEXT PRIMARY KEY NOT NULL);\n")

    env_id = uuid4()
    conn = sqlite3.connect(":memory:")
    try:
        _ = await ensure_db_schema_installed(
            connection=conn,
            sql_root=sql_root,
            environment_id=env_id,
            ocg_hash="sha256:old",
            adapter="sqlite",
        )
        with pytest.raises(DBBootExecutionError, match="different ocg_hash"):
            _ = await ensure_db_schema_installed(
                connection=conn,
                sql_root=sql_root,
                environment_id=env_id,
                ocg_hash="sha256:new",
                adapter="sqlite",
            )
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_postgres_boot_adapter_validates_connection_shape() -> None:
    with pytest.raises(DBBootExecutionError, match="transaction/execute/fetchrow"):
        _ = await POSTGRES_DB_BOOT_ADAPTER.ensure_schema_installed(
            connection=object(),
            plan=SQLBootPlan(sql_roots=(Path("/tmp"),), schemas=(), steps=()),
            environment_id=uuid4(),
            ocg_hash="sha256:test",
        )
