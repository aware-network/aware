from __future__ import annotations

from pathlib import Path
import re
from uuid import UUID, uuid4

import pytest

from aware_orm.runtime.db_boot import (
    DBBootExecutionError,
    ensure_db_schema_installed,
    ensure_db_schema_installed_multi,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _pg_ident(name: str) -> str:
    encoded = name.encode("utf-8")
    return encoded[:63].decode("utf-8", errors="ignore")


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
        self._current_schema: str | None = None
        self._types: set[tuple[str, str]] = set()
        self._tables: set[tuple[str, str]] = set()

    def transaction(self) -> _FakeTransaction:
        return _FakeTransaction(self)

    async def execute(self, query: str, *args: object) -> object:
        sql = query.strip()
        self.executed.append((sql, args))
        search_path_match = re.match(r'SET LOCAL search_path TO "([^"]+)"', sql)
        if search_path_match is not None:
            self._current_schema = search_path_match.group(1)
        if "aware_bootstrap_marker" not in sql:
            schema = self._current_schema
            for type_match in re.finditer(
                r"CREATE\s+TYPE\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?([a-zA-Z0-9_]+)\"?",
                sql,
                flags=re.IGNORECASE,
            ):
                if schema is not None:
                    self._types.add((schema, _pg_ident(type_match.group(1))))
            for table_match in re.finditer(
                r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?([a-zA-Z0-9_]+)\"?",
                sql,
                flags=re.IGNORECASE,
            ):
                if schema is not None:
                    self._tables.add((schema, _pg_ident(table_match.group(1))))
        if sql.lower().startswith("insert into public.aware_bootstrap_marker"):
            if len(args) != 3:
                raise AssertionError(f"Unexpected marker args: {args}")
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
        lowered = sql.lower()
        if "from public.aware_bootstrap_marker" in lowered:
            if len(args) != 1:
                raise AssertionError(f"Unexpected fetchrow args: {args}")
            env_id = args[0]
            assert isinstance(env_id, UUID)
            marker = self._marker_by_env.get(env_id)
            if marker is None:
                return None
            return dict(marker)
        if "from pg_type" in lowered:
            if len(args) != 2:
                raise AssertionError(f"Unexpected pg_type args: {args}")
            return {"exists": 1} if (str(args[0]), str(args[1])) in self._types else None
        if "from pg_class" in lowered:
            if len(args) != 2:
                raise AssertionError(f"Unexpected table args: {args}")
            return {"exists": 1} if (str(args[0]), str(args[1])) in self._tables else None
        raise AssertionError(f"Unexpected fetchrow query: {sql}")


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_applies_plan_and_sets_marker(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(sql_root / "domain" / "a" / "status.sql", "CREATE TYPE status AS ENUM ('x');\n")
    _write(
        sql_root / "domain" / "a" / "t1.sql",
        "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL);\n",
    )
    _write(
        sql_root / "domain" / "b" / "t2.sql",
        """
CREATE TABLE t2 (
  id UUID PRIMARY KEY NOT NULL,
  t1_id UUID REFERENCES t1(id),
  status status NOT NULL
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    res = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert res.installed is True
    assert conn._marker_by_env[env_id]["ocg_hash"] == ocg_hash

    executed_sql = [sql for sql, _args in conn.executed]
    assert any("CREATE SCHEMA IF NOT EXISTS" in sql for sql in executed_sql)
    assert any("SET LOCAL search_path TO" in sql for sql in executed_sql)
    assert any("CREATE TYPE status" in sql for sql in executed_sql)
    assert any("CREATE TABLE t1" in sql for sql in executed_sql)
    assert any("CREATE TABLE t2" in sql for sql in executed_sql)
    assert any('"a"."status"' in sql for sql in executed_sql)
    assert any(
        'ALTER TABLE "b"."t2" ADD FOREIGN KEY ("t1_id") REFERENCES "a"."t1" ("id");' == sql for sql in executed_sql
    )

    # Search-path ordering is schema-first, then other schemas, then public.
    assert any('SET LOCAL search_path TO "a", "b", "public";' == sql for sql in executed_sql)
    assert any('SET LOCAL search_path TO "b", "a", "public";' == sql for sql in executed_sql)


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_is_idempotent_when_marker_matches(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "d" / "a" / "t.sql",
        "CREATE TABLE t (id UUID PRIMARY KEY NOT NULL);\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    first = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )
    assert first.installed is True
    first_exec_count = len(conn.executed)

    second = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )
    assert second.installed is False

    # Second run should only touch the marker table, marker read, and object-existence
    # reconciliation queries (no DDL plan execution).
    new_sql = [sql for sql, _args in conn.executed[first_exec_count:]]
    assert any("CREATE TABLE IF NOT EXISTS public.aware_bootstrap_marker" in sql for sql in new_sql)
    assert any("ALTER TABLE public.aware_bootstrap_marker" in sql for sql in new_sql)
    assert any("SELECT ocg_hash, ocg_head_commit_id FROM public.aware_bootstrap_marker" in sql for sql in new_sql)
    assert any("FROM pg_class" in sql for sql in new_sql)
    assert not any(sql.startswith("SET LOCAL search_path TO") for sql in new_sql)
    assert not any(sql.startswith("CREATE TABLE t") for sql in new_sql)


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_reconciles_truncated_postgres_identifiers(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    long_table_name = "class_config_relationship_class_config_relationship_attribute_join"
    assert len(long_table_name) > 63
    _write(
        sql_root / "class_" / f"{long_table_name}.sql",
        f"CREATE TABLE {long_table_name} (id UUID PRIMARY KEY NOT NULL);\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    first = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )
    assert first.installed is True
    first_exec_count = len(conn.executed)

    second = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert second.installed is False
    assert ("class", _pg_ident(long_table_name)) in conn._tables

    new_sql = [sql for sql, _args in conn.executed[first_exec_count:]]
    assert any("FROM pg_class" in sql for sql in new_sql)
    assert not any(sql.startswith(f"CREATE TABLE {long_table_name}") for sql in new_sql)


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_fails_on_ocg_hash_mismatch(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "d" / "a" / "t.sql",
        "CREATE TABLE t (id UUID PRIMARY KEY NOT NULL);\n",
    )

    env_id = uuid4()
    conn = _FakeConnection()
    conn._marker_by_env[env_id] = {"ocg_hash": "sha256:old", "ocg_head_commit_id": None}

    with pytest.raises(DBBootExecutionError):
        await ensure_db_schema_installed(
            connection=conn,
            sql_root=sql_root,
            environment_id=env_id,
            ocg_hash="sha256:new",
        )

    executed_sql = [sql for sql, _args in conn.executed]
    assert any("SELECT ocg_hash, ocg_head_commit_id FROM public.aware_bootstrap_marker" in sql for sql in executed_sql)
    assert not any("CREATE SCHEMA IF NOT EXISTS" in sql for sql in executed_sql)


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_qualifies_types_from_multi_type_files(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "a" / "types.sql",
        "CREATE TYPE t1 AS ENUM ('x');\nCREATE TYPE t2 AS ENUM ('y');\n",
    )
    _write(
        sql_root / "b" / "t.sql",
        """
CREATE TABLE t (
  id UUID PRIMARY KEY NOT NULL,
  kind t2 NOT NULL
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    res = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert res.installed is True

    executed_sql = [sql for sql, _args in conn.executed]
    assert any('kind "a"."t2" NOT NULL' in sql for sql in executed_sql)


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_rewrites_multi_table_files(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(sql_root / "enum" / "status.sql", "CREATE TYPE status AS ENUM ('draft');\n")
    _write(sql_root / "hub" / "producer.sql", "CREATE TABLE producer (id UUID PRIMARY KEY NOT NULL);\n")
    _write(
        sql_root / "hub" / "artifact.sql",
        """
CREATE TABLE artifact (
  id UUID PRIMARY KEY NOT NULL
);

CREATE TABLE artifact_revision (
  id UUID PRIMARY KEY NOT NULL,
  artifact_id UUID REFERENCES artifact(id),
  producer_id UUID REFERENCES producer(id),
  status status NOT NULL
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    res = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert res.installed is True

    executed_sql = [sql for sql, _args in conn.executed]
    create_artifact = next(sql for sql in executed_sql if "CREATE TABLE artifact_revision" in sql)
    assert 'status "enum"."status" NOT NULL' in create_artifact
    assert "REFERENCES artifact" not in create_artifact
    assert "REFERENCES producer" not in create_artifact
    assert (
        'ALTER TABLE "hub"."artifact_revision" ADD FOREIGN KEY ("artifact_id") '
        'REFERENCES "hub"."artifact" ("id");'
    ) in executed_sql
    assert (
        'ALTER TABLE "hub"."artifact_revision" ADD FOREIGN KEY ("producer_id") '
        'REFERENCES "hub"."producer" ("id");'
    ) in executed_sql


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_skips_comment_only_files(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "a" / "noop.sql",
        "-- coverage:ignore-file\n-- GENERATED CODE - DO NOT MODIFY BY HAND\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    res = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert res.installed is True

    executed_sql = [sql for sql, _args in conn.executed]
    assert not any("SET LOCAL search_path TO" in sql for sql in executed_sql)
    assert not any("GENERATED CODE - DO NOT MODIFY BY HAND" in sql for sql in executed_sql)


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_multi_unions_sql_roots(
    tmp_path: Path,
) -> None:
    sql1 = tmp_path / "sql1"
    sql2 = tmp_path / "sql2"
    _write(sql1 / "a" / "t1.sql", "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL);\n")
    _write(
        sql2 / "b" / "t2.sql",
        """
CREATE TABLE t2 (
  id UUID PRIMARY KEY NOT NULL,
  t1_id UUID REFERENCES t1(id)
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    res = await ensure_db_schema_installed_multi(
        connection=conn,
        sql_roots=(sql1, sql2),
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert res.installed is True
    assert conn._marker_by_env[env_id]["ocg_hash"] == ocg_hash

    executed_sql = [sql for sql, _args in conn.executed]
    assert any("CREATE TABLE t1" in sql for sql in executed_sql)
    assert any("CREATE TABLE t2" in sql for sql in executed_sql)
    assert any(
        'ALTER TABLE "b"."t2" ADD FOREIGN KEY ("t1_id") REFERENCES "a"."t1" ("id");' == sql for sql in executed_sql
    )


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_reconciles_missing_sql_roots_when_marker_matches(
    tmp_path: Path,
) -> None:
    sql1 = tmp_path / "sql1"
    sql2 = tmp_path / "sql2"
    _write(sql1 / "a" / "t1.sql", "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL);\n")
    _write(
        sql2 / "b" / "t2.sql",
        """
CREATE TABLE t2 (
  id UUID PRIMARY KEY NOT NULL,
  t1_id UUID REFERENCES t1(id)
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    first = await ensure_db_schema_installed_multi(
        connection=conn,
        sql_roots=(sql1,),
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )
    assert first.installed is True
    first_exec_count = len(conn.executed)

    second = await ensure_db_schema_installed_multi(
        connection=conn,
        sql_roots=(sql1, sql2),
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert second.installed is True
    assert second.step_count == 1

    new_sql = [sql for sql, _args in conn.executed[first_exec_count:]]
    assert any("FROM pg_class" in sql for sql in new_sql)
    assert not any(sql.startswith("CREATE TABLE t1") for sql in new_sql)
    assert any(sql.startswith("CREATE TABLE t2") for sql in new_sql)
    assert (
        'ALTER TABLE "b"."t2" ADD FOREIGN KEY ("t1_id") REFERENCES "a"."t1" ("id");'
    ) in new_sql


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_strips_table_level_composite_foreign_keys(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "actor" / "actor.sql",
        """
CREATE TABLE actor (
  -- PRIMARY KEY
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  -- RELATIONSHIPS
  identity_id UUID NOT NULL,
  -- CONSTRAINTS
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, identity_id) REFERENCES identity(branch_id, projection_hash, id)
);
""".strip()
        + "\n",
    )
    _write(
        sql_root / "identity" / "identity.sql",
        """
CREATE TABLE identity (
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  PRIMARY KEY (branch_id, projection_hash, id)
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    res = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert res.installed is True

    executed_sql = [sql for sql, _args in conn.executed]
    create_actor = next(sql for sql in executed_sql if sql.startswith("CREATE TABLE actor"))
    assert "FOREIGN KEY" not in create_actor
    assert "REFERENCES identity" not in create_actor
    assert "PRIMARY KEY (branch_id, projection_hash, id)," not in create_actor

    assert (
        'ALTER TABLE "actor"."actor" ADD FOREIGN KEY ("branch_id", "projection_hash", "identity_id") '
        'REFERENCES "identity"."identity" ("branch_id", "projection_hash", "id");'
    ) in executed_sql


@pytest.mark.asyncio
async def test_ensure_db_schema_installed_adds_runtime_identity_index_before_composite_fk(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "code" / "code_section.sql",
        """
CREATE TABLE code_section (
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  section_key TEXT NOT NULL,
  type_ TEXT NOT NULL,
  PRIMARY KEY (branch_id, projection_hash, id, section_key, type_)
);
""".strip()
        + "\n",
    )
    _write(
        sql_root / "annotation" / "code_section_annotation.sql",
        """
CREATE TABLE code_section_annotation (
  branch_id UUID NOT NULL,
  projection_hash TEXT NOT NULL,
  id UUID NOT NULL,
  code_section_id UUID NOT NULL,
  PRIMARY KEY (branch_id, projection_hash, id),
  FOREIGN KEY (branch_id, projection_hash, code_section_id) REFERENCES code_section(branch_id, projection_hash, id)
);
""".strip()
        + "\n",
    )

    env_id = uuid4()
    ocg_hash = "sha256:test"
    conn = _FakeConnection()

    res = await ensure_db_schema_installed(
        connection=conn,
        sql_root=sql_root,
        environment_id=env_id,
        ocg_hash=ocg_hash,
    )

    assert res.installed is True

    executed_sql = [sql for sql, _args in conn.executed]
    index_idx = next(
        idx
        for idx, sql in enumerate(executed_sql)
        if 'ON "code"."code_section" ("branch_id", "projection_hash", "id");' in sql
    )
    fk_sql = (
        'ALTER TABLE "annotation"."code_section_annotation" '
        'ADD FOREIGN KEY ("branch_id", "projection_hash", "code_section_id") '
        'REFERENCES "code"."code_section" ("branch_id", "projection_hash", "id");'
    )
    fk_idx = executed_sql.index(fk_sql)

    assert executed_sql[index_idx].startswith('CREATE UNIQUE INDEX IF NOT EXISTS "aware_oid_')
    assert index_idx < fk_idx
