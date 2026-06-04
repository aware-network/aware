from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_orm.runtime.db_boot import DBBootExecutionError
from aware_orm.runtime.ocg_migrations import apply_ocg_sql_migrations


COMMIT_1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
COMMIT_2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
COMMIT_3 = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class _FakeTransaction:
    def __init__(self, conn: "_FakeConnection") -> None:
        self._conn = conn

    async def __aenter__(self) -> object:
        self._conn.executed.append(("BEGIN", ()))
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> object:
        if exc_type is None:
            self._conn.executed.append(("COMMIT", ()))
        else:
            self._conn.executed.append(("ROLLBACK", ()))
        return False


class _FakeConnection:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []
        self._marker_by_env: dict[UUID, dict[str, object]] = {}

    def transaction(self) -> _FakeTransaction:
        return _FakeTransaction(self)

    async def execute(self, query: str, *args: object) -> object:
        sql = query.strip()
        self.executed.append((sql, args))
        if sql.lower().startswith("insert into public.aware_bootstrap_marker"):
            env_id = args[0]
            ocg_hash = args[1]
            ocg_head_commit_id = args[2]
            assert isinstance(env_id, UUID)
            assert isinstance(ocg_hash, str)
            assert ocg_head_commit_id is None or isinstance(ocg_head_commit_id, UUID)
            self._marker_by_env[env_id] = {
                "ocg_hash": ocg_hash,
                "ocg_head_commit_id": ocg_head_commit_id,
            }
        return "OK"

    async def fetchrow(self, query: str, *args: object) -> dict[str, object] | None:
        sql = query.strip()
        self.executed.append((sql, args))
        env_id = args[0]
        assert isinstance(env_id, UUID)
        marker = self._marker_by_env.get(env_id)
        if marker is None:
            return None
        return dict(marker)


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


@pytest.mark.asyncio
async def test_apply_ocg_sql_migrations_applies_range_and_updates_marker(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"
    env_id = uuid4()

    lane_json_path = _write_lane_json(
        migrations_root=migrations_root,
        env_id=env_id,
        commits=[COMMIT_1, COMMIT_2, COMMIT_3],
    )

    _write(
        migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql",
        'ALTER TABLE "a"."t" ADD COLUMN "x" INT;\n',
    )
    _write(
        migrations_root / "sql" / "commits" / f"{COMMIT_3}.sql",
        'ALTER TABLE "a"."t" ADD COLUMN "y" INT;\n',
    )

    conn = _FakeConnection()
    conn._marker_by_env[env_id] = {
        "ocg_hash": "sha256:old",
        "ocg_head_commit_id": COMMIT_1,
    }

    res = await apply_ocg_sql_migrations(
        connection=conn,
        lane_json_path=lane_json_path,
        environment_id=env_id,
        desired_ocg_hash="sha256:new",
    )

    assert res.applied is True
    assert res.from_commit_id == COMMIT_1
    assert res.to_commit_id == COMMIT_3
    assert res.applied_commit_ids == (COMMIT_2, COMMIT_3)
    assert conn._marker_by_env[env_id]["ocg_hash"] == "sha256:new"
    assert conn._marker_by_env[env_id]["ocg_head_commit_id"] == COMMIT_3

    executed_sql = [sql for sql, _args in conn.executed]
    assert any('ALTER TABLE "a"."t" ADD COLUMN "x" INT;' in sql for sql in executed_sql)
    assert any('ALTER TABLE "a"."t" ADD COLUMN "y" INT;' in sql for sql in executed_sql)


@pytest.mark.asyncio
async def test_apply_ocg_sql_migrations_routes_do_block_by_table_reference(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"
    env_id = uuid4()

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(
        migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql",
        "\n".join(
            [
                "DO $$",
                "BEGIN",
                '  IF EXISTS (SELECT 1 FROM "thing" LIMIT 1) THEN',
                "    RAISE EXCEPTION 'blocked';",
                "  END IF;",
                '  EXECUTE \'ALTER TABLE "thing" ADD COLUMN "x" INT NOT NULL;\';',
                "END;",
                "$$;",
                "",
            ]
        ),
    )

    sql_root = tmp_path / "sql"
    _write(
        sql_root / "a" / "thing.sql",
        "CREATE TABLE thing (\n"
        "  branch_id UUID NOT NULL,\n"
        "  projection_hash TEXT NOT NULL,\n"
        "  id UUID NOT NULL,\n"
        "  PRIMARY KEY (branch_id, projection_hash, id)\n"
        ");\n",
    )

    conn = _FakeConnection()
    conn._marker_by_env[env_id] = {
        "ocg_hash": "sha256:old",
        "ocg_head_commit_id": COMMIT_1,
    }

    res = await apply_ocg_sql_migrations(
        connection=conn,
        lane_json_path=lane_json_path,
        environment_id=env_id,
        desired_ocg_hash="sha256:new",
        sql_roots=(sql_root,),
    )

    assert res.applied is True
    executed_sql = [sql for sql, _args in conn.executed]
    assert any('SET LOCAL search_path TO "a", "public";' in sql for sql in executed_sql)
    assert any(sql.startswith("DO $$") for sql in executed_sql)


@pytest.mark.asyncio
async def test_apply_ocg_sql_migrations_noop_when_up_to_date(tmp_path: Path) -> None:
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"
    env_id = uuid4()

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql", "-- noop\n")

    conn = _FakeConnection()
    conn._marker_by_env[env_id] = {
        "ocg_hash": "sha256:same",
        "ocg_head_commit_id": COMMIT_2,
    }
    before = list(conn.executed)

    res = await apply_ocg_sql_migrations(
        connection=conn,
        lane_json_path=lane_json_path,
        environment_id=env_id,
        desired_ocg_hash="sha256:same",
    )

    assert res.applied is False
    assert conn.executed != before  # marker table read/ensure still occurs
    executed_sql = [sql for sql, _args in conn.executed]
    assert not any('ALTER TABLE "a"."t"' in sql for sql in executed_sql)


@pytest.mark.asyncio
async def test_apply_ocg_sql_migrations_requires_existing_marker(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"
    env_id = uuid4()

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql", "-- noop\n")

    conn = _FakeConnection()

    with pytest.raises(DBBootExecutionError):
        await apply_ocg_sql_migrations(
            connection=conn,
            lane_json_path=lane_json_path,
            environment_id=env_id,
            desired_ocg_hash="sha256:new",
        )


@pytest.mark.asyncio
async def test_apply_ocg_sql_migrations_fails_when_head_not_in_lane(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / ".aware" / "environment" / "runtime"
    migrations_root = runtime_dir / "migrations"
    env_id = uuid4()

    lane_json_path = _write_lane_json(migrations_root=migrations_root, env_id=env_id, commits=[COMMIT_1, COMMIT_2])
    _write(migrations_root / "sql" / "commits" / f"{COMMIT_2}.sql", "-- noop\n")

    conn = _FakeConnection()
    other = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
    conn._marker_by_env[env_id] = {
        "ocg_hash": "sha256:old",
        "ocg_head_commit_id": other,
    }

    with pytest.raises(DBBootExecutionError):
        await apply_ocg_sql_migrations(
            connection=conn,
            lane_json_path=lane_json_path,
            environment_id=env_id,
            desired_ocg_hash="sha256:new",
        )
