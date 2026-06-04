from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_orm.runtime.db_boot import (
    ensure_db_schema_installed_multi,
    fetch_db_bootstrap_marker,
)
from aware_orm.runtime.ocg_migrations import apply_ocg_sql_migrations
from aware_orm.testing import db_test_database


COMMIT_1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
COMMIT_2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_lane_json(*, migrations_root: Path, env_id: UUID, commits: list[UUID]) -> Path:
    lane_json_path = migrations_root / "ocg" / "lane.json"
    lane_json_path.parent.mkdir(parents=True, exist_ok=True)
    lane_json_path.write_text(
        json.dumps(
            {
                "v": 1,
                "opg_name": "ObjectConfigGraph",
                "branch_id": str(env_id),
                "projection_hash": "sha256:test:opg",
                "head_commit_id": str(commits[-1]),
                "commits": [
                    {
                        "commit_id": str(c),
                        "parent_commit_id": (str(commits[i - 1]) if i > 0 else None),
                        "graph_hash_pre": None,
                        "graph_hash_post": None,
                        "delta_file": f"ocg/deltas/{c}.json",
                        "sql_file": f"sql/commits/{c}.sql",
                    }
                    for i, c in enumerate(commits)
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return lane_json_path


async def _schema_snapshot(asyncpg_conn) -> dict[str, tuple[tuple[str, ...], ...]]:  # type: ignore[no-untyped-def]
    # Compare only user schemas (exclude public marker table + system schemas).
    columns = await asyncpg_conn.fetch(
        """
SELECT
  table_schema,
  table_name,
  column_name,
  data_type,
  is_nullable,
  ordinal_position
FROM information_schema.columns
WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'public')
ORDER BY table_schema, table_name, ordinal_position;
""".strip()
    )
    primary_keys = await asyncpg_conn.fetch(
        """
SELECT
  tc.table_schema,
  tc.table_name,
  kcu.column_name,
  kcu.ordinal_position
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
 AND tc.table_name = kcu.table_name
WHERE tc.constraint_type='PRIMARY KEY'
  AND tc.table_schema NOT IN ('pg_catalog', 'information_schema', 'public')
ORDER BY tc.table_schema, tc.table_name, kcu.ordinal_position;
""".strip()
    )
    return {
        "columns": tuple(
            (
                str(r["table_schema"]),
                str(r["table_name"]),
                str(r["column_name"]),
                str(r["data_type"]),
                str(r["is_nullable"]),
            )
            for r in columns
        ),
        "primary_keys": tuple(
            (
                str(r["table_schema"]),
                str(r["table_name"]),
                str(r["column_name"]),
            )
            for r in primary_keys
        ),
    }


def _skip_if_db_unavailable() -> str | None:
    db_admin_url = os.getenv("AWARE_DB_TEST_ADMIN_URL") or os.getenv("AWARE_DB_TEST_URL")
    bootstrap_enabled = bool(os.getenv("AWARE_DB_TEST_BOOTSTRAP"))
    bootstrap_url = os.getenv("AWARE_DB_TEST_BOOTSTRAP_URL") or os.getenv("AWARE_DB_TEST_URL")
    if db_admin_url or (bootstrap_enabled and bootstrap_url):
        return None
    return (
        "AWARE_DB_TEST_ADMIN_URL is required for DB-backed migration tests "
        "(or set AWARE_DB_TEST_BOOTSTRAP=1 with AWARE_DB_TEST_BOOTSTRAP_URL)."
    )


@asynccontextmanager
async def _db_test_database_or_skip():
    try:
        async with db_test_database() as db_url:
            yield db_url
    except RuntimeError as exc:
        message = str(exc)
        if "Docker is required" in message or "docker daemon socket" in message or "operation not permitted" in message:
            pytest.skip(f"DB bootstrap requires docker access: {exc}")
        raise


@pytest.mark.asyncio
@pytest.mark.db
async def test_ocg_sql_migrations_equivalent_to_fresh_install(tmp_path: Path) -> None:
    reason = _skip_if_db_unavailable()
    if reason:
        pytest.skip(reason)

    asyncpg = pytest.importorskip("asyncpg")

    env_id = uuid4()
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(
        migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql",
        'ALTER TABLE "a"."t" ADD COLUMN "x" INTEGER;\n',
    )

    sql_v1 = tmp_path / "sql_v1"
    _write(sql_v1 / "a" / "t.sql", 'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL);\n')

    sql_v2 = tmp_path / "sql_v2"
    _write(
        sql_v2 / "a" / "t.sql",
        'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL, "x" INTEGER);\n',
    )

    async with _db_test_database_or_skip() as migrate_db_url:
        conn = await asyncpg.connect(migrate_db_url)
        try:
            await ensure_db_schema_installed_multi(
                connection=conn,
                sql_roots=[sql_v1],
                environment_id=env_id,
                ocg_hash="sha256:test:v1",
                ocg_head_commit_id=COMMIT_1,
            )
            await apply_ocg_sql_migrations(
                connection=conn,
                lane_json_path=lane_json_path,
                environment_id=env_id,
                desired_ocg_hash="sha256:test:v2",
            )
            migrated_snapshot = await _schema_snapshot(conn)
        finally:
            await conn.close()

        async with _db_test_database_or_skip() as fresh_db_url:
            conn = await asyncpg.connect(fresh_db_url)
            try:
                await ensure_db_schema_installed_multi(
                    connection=conn,
                    sql_roots=[sql_v2],
                    environment_id=env_id,
                    ocg_hash="sha256:test:v2",
                    ocg_head_commit_id=COMMIT_2,
                )
                fresh_snapshot = await _schema_snapshot(conn)
            finally:
                await conn.close()

    assert migrated_snapshot == fresh_snapshot


@pytest.mark.asyncio
@pytest.mark.db
async def test_ocg_sql_migrations_rollback_does_not_advance_marker(
    tmp_path: Path,
) -> None:
    reason = _skip_if_db_unavailable()
    if reason:
        pytest.skip(reason)

    asyncpg = pytest.importorskip("asyncpg")

    env_id = uuid4()
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(
        migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql",
        # DDL + a failing statement to force rollback.
        'ALTER TABLE "a"."t" ADD COLUMN "x" INTEGER;\nSELECT missing_column;\n',
    )

    sql_v1 = tmp_path / "sql_v1"
    _write(sql_v1 / "a" / "t.sql", 'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL);\n')

    async with _db_test_database_or_skip() as db_url:
        conn = await asyncpg.connect(db_url)
        try:
            await ensure_db_schema_installed_multi(
                connection=conn,
                sql_roots=[sql_v1],
                environment_id=env_id,
                ocg_hash="sha256:test:v1",
                ocg_head_commit_id=COMMIT_1,
            )

            with pytest.raises(Exception):
                await apply_ocg_sql_migrations(
                    connection=conn,
                    lane_json_path=lane_json_path,
                    environment_id=env_id,
                    desired_ocg_hash="sha256:test:v2",
                )

            marker = await fetch_db_bootstrap_marker(connection=conn, environment_id=env_id)
            assert marker is not None
            assert marker.ocg_hash == "sha256:test:v1"
            assert marker.ocg_head_commit_id == COMMIT_1

            cols = await conn.fetch(
                """
SELECT column_name
FROM information_schema.columns
WHERE table_schema='a' AND table_name='t'
ORDER BY ordinal_position;
""".strip()
            )
            assert [str(r["column_name"]) for r in cols] == ["id"]
        finally:
            await conn.close()


@pytest.mark.asyncio
@pytest.mark.db
async def test_ocg_sql_migrations_concurrent_apply_serializes(tmp_path: Path) -> None:
    reason = _skip_if_db_unavailable()
    if reason:
        pytest.skip(reason)

    asyncpg = pytest.importorskip("asyncpg")

    env_id = uuid4()
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(
        migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql",
        'ALTER TABLE "a"."t" ADD COLUMN "x" INTEGER;\n',
    )

    sql_v1 = tmp_path / "sql_v1"
    _write(sql_v1 / "a" / "t.sql", 'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL);\n')

    async with _db_test_database_or_skip() as db_url:
        bootstrap_conn = await asyncpg.connect(db_url)
        try:
            await ensure_db_schema_installed_multi(
                connection=bootstrap_conn,
                sql_roots=[sql_v1],
                environment_id=env_id,
                ocg_hash="sha256:test:v1",
                ocg_head_commit_id=COMMIT_1,
            )
        finally:
            await bootstrap_conn.close()

        conn_a = await asyncpg.connect(db_url)
        conn_b = await asyncpg.connect(db_url)
        try:
            res_a, res_b = await asyncio.gather(
                apply_ocg_sql_migrations(
                    connection=conn_a,
                    lane_json_path=lane_json_path,
                    environment_id=env_id,
                    desired_ocg_hash="sha256:test:v2",
                ),
                apply_ocg_sql_migrations(
                    connection=conn_b,
                    lane_json_path=lane_json_path,
                    environment_id=env_id,
                    desired_ocg_hash="sha256:test:v2",
                ),
            )
            assert sum(1 for res in (res_a, res_b) if res.applied) == 1

            marker = await fetch_db_bootstrap_marker(connection=conn_a, environment_id=env_id)
            assert marker is not None
            assert marker.ocg_hash == "sha256:test:v2"
            assert marker.ocg_head_commit_id == COMMIT_2

            cols = await conn_a.fetch(
                """
SELECT column_name
FROM information_schema.columns
WHERE table_schema='a' AND table_name='t'
ORDER BY ordinal_position;
""".strip()
            )
            assert [str(r["column_name"]) for r in cols] == ["id", "x"]
        finally:
            await conn_a.close()
            await conn_b.close()


@pytest.mark.asyncio
@pytest.mark.db
async def test_ocg_sql_migrations_idempotent_second_apply_is_noop(
    tmp_path: Path,
) -> None:
    reason = _skip_if_db_unavailable()
    if reason:
        pytest.skip(reason)

    asyncpg = pytest.importorskip("asyncpg")

    env_id = uuid4()
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(
        migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql",
        'ALTER TABLE "a"."t" ADD COLUMN "x" INTEGER;\n',
    )

    sql_v1 = tmp_path / "sql_v1"
    _write(sql_v1 / "a" / "t.sql", 'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL);\n')

    async with _db_test_database_or_skip() as db_url:
        conn = await asyncpg.connect(db_url)
        try:
            await ensure_db_schema_installed_multi(
                connection=conn,
                sql_roots=[sql_v1],
                environment_id=env_id,
                ocg_hash="sha256:test:v1",
                ocg_head_commit_id=COMMIT_1,
            )

            res_first = await apply_ocg_sql_migrations(
                connection=conn,
                lane_json_path=lane_json_path,
                environment_id=env_id,
                desired_ocg_hash="sha256:test:v2",
            )
            assert res_first.applied is True

            res_second = await apply_ocg_sql_migrations(
                connection=conn,
                lane_json_path=lane_json_path,
                environment_id=env_id,
                desired_ocg_hash="sha256:test:v2",
            )
            assert res_second.applied is False
            assert res_second.applied_commit_ids == ()

            marker = await fetch_db_bootstrap_marker(connection=conn, environment_id=env_id)
            assert marker is not None
            assert marker.ocg_hash == "sha256:test:v2"
            assert marker.ocg_head_commit_id == COMMIT_2

            cols = await conn.fetch(
                """
SELECT column_name
FROM information_schema.columns
WHERE table_schema='a' AND table_name='t'
ORDER BY ordinal_position;
""".strip()
            )
            assert [str(r["column_name"]) for r in cols] == ["id", "x"]
        finally:
            await conn.close()
