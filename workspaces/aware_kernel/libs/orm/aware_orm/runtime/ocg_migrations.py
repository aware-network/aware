from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence
from uuid import UUID

from aware_orm.runtime.db_boot import (
    DBBootConnection,
    DBBootExecutionError,
    build_sql_boot_plan_multi,
    ensure_db_bootstrap_marker_table,
    fetch_db_bootstrap_marker,
    upsert_db_bootstrap_marker,
)


@dataclass(frozen=True, slots=True)
class OcgLaneCommit:
    commit_id: UUID
    parent_commit_id: UUID | None
    graph_hash_pre: str | None
    graph_hash_post: str | None
    delta_file: str | None
    sql_file: str | None


@dataclass(frozen=True, slots=True)
class OcgLaneIndex:
    lane_json_path: Path
    migrations_root: Path
    branch_id: UUID
    projection_hash: str
    head_commit_id: UUID
    commits: tuple[OcgLaneCommit, ...]


@dataclass(frozen=True, slots=True)
class OcgSqlMigrationApplyResult:
    applied: bool
    environment_id: UUID
    from_commit_id: UUID
    to_commit_id: UUID
    applied_commit_ids: tuple[UUID, ...]
    applied_sql_files: tuple[Path, ...]


def _load_json(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid JSON object at {path}")
    return raw


def _parse_uuid(value: object, *, field: str) -> UUID:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing {field}")
    try:
        return UUID(value)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"Invalid {field}={value!r}") from exc


def _resolve_migrations_root(lane_json_path: Path) -> Path:
    # `<runtime_dir>/migrations/ocg/lane.json` -> `<runtime_dir>/migrations`
    if lane_json_path.name != "lane.json":
        raise ValueError(f"Expected lane.json file, got: {lane_json_path}")
    return lane_json_path.parent.parent


def load_ocg_lane_index(*, lane_json_path: Path) -> OcgLaneIndex:
    lane_json_path = Path(lane_json_path).expanduser().resolve()
    raw = _load_json(lane_json_path)

    branch_id = _parse_uuid(raw.get("branch_id"), field="branch_id")
    projection_hash = str(raw.get("projection_hash") or "").strip()
    if not projection_hash:
        raise ValueError("Missing projection_hash")

    head_commit_id = _parse_uuid(raw.get("head_commit_id"), field="head_commit_id")

    commits_raw = raw.get("commits")
    if not isinstance(commits_raw, list):
        raise ValueError("lane.json missing commits[]")

    commits: list[OcgLaneCommit] = []
    for idx, item in enumerate(commits_raw):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid commits[{idx}] entry type: {type(item)}")
        commit_id = _parse_uuid(item.get("commit_id"), field=f"commits[{idx}].commit_id")
        parent_raw = item.get("parent_commit_id")
        parent_commit_id = None
        if isinstance(parent_raw, str) and parent_raw.strip():
            parent_commit_id = _parse_uuid(parent_raw, field=f"commits[{idx}].parent_commit_id")

        commits.append(
            OcgLaneCommit(
                commit_id=commit_id,
                parent_commit_id=parent_commit_id,
                graph_hash_pre=(str(item.get("graph_hash_pre")) if item.get("graph_hash_pre") is not None else None),
                graph_hash_post=(str(item.get("graph_hash_post")) if item.get("graph_hash_post") is not None else None),
                delta_file=(str(item.get("delta_file")) if item.get("delta_file") is not None else None),
                sql_file=(str(item.get("sql_file")) if item.get("sql_file") is not None else None),
            )
        )

    migrations_root = _resolve_migrations_root(lane_json_path)
    return OcgLaneIndex(
        lane_json_path=lane_json_path,
        migrations_root=migrations_root,
        branch_id=branch_id,
        projection_hash=projection_hash,
        head_commit_id=head_commit_id,
        commits=tuple(commits),
    )


def _required_commit_range(*, lane: OcgLaneIndex, from_commit_id: UUID) -> tuple[OcgLaneCommit, ...]:
    if from_commit_id == lane.head_commit_id:
        return ()
    index_by_id = {c.commit_id: idx for idx, c in enumerate(lane.commits)}
    idx = index_by_id.get(from_commit_id)
    if idx is None:
        raise DBBootExecutionError(
            "DB schema head commit id is not part of the bundle lane index (diverged history). "
            f"from_commit_id={from_commit_id} lane_head_commit_id={lane.head_commit_id} lane_json={lane.lane_json_path}"
        )
    return lane.commits[idx + 1 :]


def _pg_advisory_xact_lock_pair(environment_id: UUID) -> tuple[int, int]:
    """Stable 2x int32 lock key for `pg_advisory_xact_lock(key1, key2)`."""
    return struct.unpack("!ii", environment_id.bytes[0:8])


_RE_DO_DOLLAR_BLOCK = re.compile(r"^\s*DO\s+\$\$", re.IGNORECASE | re.MULTILINE)
_RE_CREATE_TABLE_STMT = re.compile(
    r"^\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:(\"?[a-zA-Z0-9_]+\"?)\.)?\"?([a-zA-Z0-9_]+)\"?\s*\(",
    re.IGNORECASE | re.MULTILINE,
)
_RE_ALTER_TABLE_STMT = re.compile(
    r"^\s*ALTER\s+TABLE\s+(?:(\"?[a-zA-Z0-9_]+\"?)\.)?\"?([a-zA-Z0-9_]+)\"?\b",
    re.IGNORECASE | re.MULTILINE,
)
_RE_CREATE_TYPE_STMT = re.compile(
    r"^\s*CREATE\s+TYPE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:(\"?[a-zA-Z0-9_]+\"?)\.)?\"?([a-zA-Z0-9_]+)\"?\b",
    re.IGNORECASE | re.MULTILINE,
)
_RE_CREATE_INDEX_STMT = re.compile(
    r"^\s*CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?[a-zA-Z0-9_]+\"?\s+ON\s+(?:(\"?[a-zA-Z0-9_]+\"?)\.)?\"?([a-zA-Z0-9_]+)\"?\b",
    re.IGNORECASE | re.MULTILINE,
)
_RE_ALTER_TYPE_STMT = re.compile(
    r"^\s*ALTER\s+TYPE\s+(?:(\"?[a-zA-Z0-9_]+\"?)\.)?\"?([a-zA-Z0-9_]+)\"?\b",
    re.IGNORECASE | re.MULTILINE,
)
_RE_DO_TABLE_REF = re.compile(
    r"\b(?:FROM|ALTER\s+TABLE)\s+(?:(\"?[a-zA-Z0-9_]+\"?)\.)?\"?([a-zA-Z0-9_]+)\"?\b",
    re.IGNORECASE,
)


def _quote_ident(name: str) -> str:
    if not name:
        raise ValueError("Empty identifier is not allowed")
    return '"' + name.replace('"', '""') + '"'


def _normalize_ident(token: str) -> str:
    t = token.strip()
    if t.startswith('"') and t.endswith('"') and len(t) >= 2:
        return t[1:-1].replace('""', '"')
    return t


def _search_path_for_schema(*, schema: str, all_schemas: tuple[str, ...]) -> str:
    ordered = [schema, *[s for s in all_schemas if s != schema], "public"]
    return ", ".join(_quote_ident(s) for s in ordered)


def _split_sql_statements(sql_text: str) -> list[str]:
    """Split a SQL script into individual statements.

    v0 migrations are compiler-emitted, statement-per-line DDL. We intentionally avoid trying to
    fully parse SQL; this splitter is conservative:
    - If a dollar-quoted DO block is detected, return the entire script as a single statement.
    """
    if _RE_DO_DOLLAR_BLOCK.search(sql_text):
        return [sql_text]

    parts = sql_text.split(";")
    # `split(';')` drops terminators; add `;` back so callers (tests/fakes) can observe the
    # original statement boundary clearly. Most drivers accept trailing semicolons.
    return [p.strip() + ";" for p in parts if p.strip()]


def _is_effective_sql_empty(sql_text: str) -> bool:
    """Return True when SQL contains no executable statements (comments/whitespace only)."""
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("--"):
            continue
        return False
    return True


def _schema_for_statement(
    stmt: str,
    *,
    table_schema_by_name: dict[str, str],
    type_schema_by_name: dict[str, str],
) -> str | None:
    """Return the owning schema for the statement (when determinable)."""
    m = _RE_CREATE_TABLE_STMT.search(stmt) or _RE_ALTER_TABLE_STMT.search(stmt)
    if m:
        schema_raw, table_raw = m.group(1), m.group(2)
        if schema_raw:
            return _normalize_ident(schema_raw)
        table = _normalize_ident(table_raw)
        return table_schema_by_name.get(table)

    m = _RE_CREATE_INDEX_STMT.search(stmt)
    if m:
        schema_raw, table_raw = m.group(1), m.group(2)
        if schema_raw:
            return _normalize_ident(schema_raw)
        table = _normalize_ident(table_raw)
        return table_schema_by_name.get(table)

    m = _RE_CREATE_TYPE_STMT.search(stmt) or _RE_ALTER_TYPE_STMT.search(stmt)
    if m:
        schema_raw, type_raw = m.group(1), m.group(2)
        if schema_raw:
            return _normalize_ident(schema_raw)
        type_name = _normalize_ident(type_raw)
        return type_schema_by_name.get(type_name)

    # Compiler-emitted guarded DDL may be wrapped in DO $$ blocks. Those statements do not match
    # regular ALTER/CREATE regexes above, so infer schema from referenced table names.
    if _RE_DO_DOLLAR_BLOCK.search(stmt):
        inferred: set[str] = set()
        for match in _RE_DO_TABLE_REF.finditer(stmt):
            schema_raw, table_raw = match.group(1), match.group(2)
            if schema_raw:
                inferred.add(_normalize_ident(schema_raw))
                continue
            table_name = _normalize_ident(table_raw)
            schema = table_schema_by_name.get(table_name)
            if schema:
                inferred.add(schema)
        if len(inferred) == 1:
            return next(iter(inferred))

    return None


def _load_sql_base_mappings(
    *,
    migrations_root: Path,
    sql_roots: Sequence[Path] | None = None,
) -> tuple[tuple[str, ...], dict[str, str], dict[str, str]]:
    """Return (schemas, table_schema_by_name, type_schema_by_name) for routing unqualified DDL.

    Preferred input is the compiler-emitted baseline under `migrations/sql/base/**.sql`.

    Fallback: when the baseline is missing (common for composed bundles), callers may pass the
    environment SQL roots (same inputs used by schema install) so routing matches DB boot.
    """
    base_root = (migrations_root / "sql" / "base").resolve()
    base_sql_roots: tuple[Path, ...] | None = None
    if base_root.is_dir():
        base_sql_roots = (base_root,)
    elif sql_roots:
        # Best-effort: callers may pass placeholder paths in unit tests when only schema-qualified
        # DDL is applied. Only use valid directories here; otherwise fall back to "no baseline"
        # mode and require explicit schema qualification in migration SQL.
        resolved: list[Path] = []
        for p in sql_roots:
            pr = Path(p).expanduser().resolve()
            if pr.is_dir():
                resolved.append(pr)
        if resolved:
            base_sql_roots = tuple(resolved)
    if not base_sql_roots:
        return (), {}, {}

    plan = build_sql_boot_plan_multi(sql_roots=base_sql_roots)
    schemas = plan.schemas

    # Build name→schema mapping for routing unqualified DDL statements.
    # Reuse db_boot's regex helpers to stay aligned with the SQL renderer.
    from aware_orm.db import boot as db_boot_mod

    table_schema_by_name: dict[str, str] = {}
    type_schema_by_name: dict[str, str] = {}

    for step in plan.steps:
        sql_text = step.path.read_text(encoding="utf-8")

        for table in db_boot_mod._created_table_names(sql_text):  # pyright: ignore[reportPrivateUsage]
            prev = table_schema_by_name.get(table)
            if prev is not None and prev != step.schema:
                raise DBBootExecutionError(
                    "Ambiguous table schema mapping in SQL baseline (name collision across schemas). "
                    f"table={table} schemas=({prev}, {step.schema}) base_root={base_root}"
                )
            table_schema_by_name[table] = step.schema

        for typ in db_boot_mod._created_type_names(sql_text):  # pyright: ignore[reportPrivateUsage]
            prev = type_schema_by_name.get(typ)
            if prev is not None and prev != step.schema:
                raise DBBootExecutionError(
                    "Ambiguous type schema mapping in SQL baseline (name collision across schemas). "
                    f"type={typ} schemas=({prev}, {step.schema}) base_root={base_root}"
                )
            type_schema_by_name[typ] = step.schema

    return schemas, table_schema_by_name, type_schema_by_name


async def apply_ocg_sql_migrations(
    *,
    connection: DBBootConnection,
    lane_json_path: Path,
    environment_id: UUID,
    desired_ocg_hash: str,
    sql_roots: Sequence[Path] | None = None,
) -> OcgSqlMigrationApplyResult:
    """Apply compiler-emitted SQL migrations for the OCG lane and advance the DB bootstrap marker.

    Contract:
    - The DB must already be bootstrapped (marker row exists).
    - The marker must include `ocg_head_commit_id` so we know where to start in the lane.
    - SQL files are executed in commit lineage order (lane.json order) and then the marker is updated.
    """
    lane = load_ocg_lane_index(lane_json_path=lane_json_path)
    base_schemas, table_schema_by_name, type_schema_by_name = _load_sql_base_mappings(
        migrations_root=lane.migrations_root,
        sql_roots=sql_roots,
    )
    await ensure_db_bootstrap_marker_table(connection=connection)
    marker = None
    from_commit_id = None

    applied_commit_ids: list[UUID] = []
    applied_sql_files: list[Path] = []

    async with connection.transaction():
        # Serialize migration apply per environment id so concurrent boots cannot race on DDL.
        k1, k2 = _pg_advisory_xact_lock_pair(environment_id)
        await connection.execute(f"SELECT pg_advisory_xact_lock({k1}, {k2});")

        # Ensure schemas exist before `SET LOCAL search_path` (important for new schemas).
        if base_schemas:
            for schema in base_schemas:
                if schema == "public":
                    continue
                await connection.execute(f"CREATE SCHEMA IF NOT EXISTS {_quote_ident(schema)};")

        marker = await fetch_db_bootstrap_marker(connection=connection, environment_id=environment_id)
        if marker is None:
            raise DBBootExecutionError(
                "DB is not bootstrapped (missing bootstrap marker row); run schema install first. "
                f"environment_id={environment_id}"
            )
        if marker.ocg_head_commit_id is None:
            raise DBBootExecutionError(
                "DB bootstrap marker missing ocg_head_commit_id; cannot apply incremental migrations. "
                f"environment_id={environment_id} existing_ocg_hash={marker.ocg_hash}"
            )

        from_commit_id = marker.ocg_head_commit_id
        required = _required_commit_range(lane=lane, from_commit_id=from_commit_id)
        if not required and marker.ocg_hash == desired_ocg_hash:
            return OcgSqlMigrationApplyResult(
                applied=False,
                environment_id=environment_id,
                from_commit_id=from_commit_id,
                to_commit_id=lane.head_commit_id,
                applied_commit_ids=(),
                applied_sql_files=(),
            )

        for entry in required:
            if not entry.sql_file:
                raise DBBootExecutionError(f"lane.json missing sql_file for commit_id={entry.commit_id}")
            sql_path = (lane.migrations_root / entry.sql_file).resolve()
            if not sql_path.is_file():
                raise DBBootExecutionError(
                    "Missing SQL migration file for commit in bundle: "
                    f"commit_id={entry.commit_id} sql_file={entry.sql_file} migrations_root={lane.migrations_root}"
                )

            sql_text = sql_path.read_text(encoding="utf-8")
            if _is_effective_sql_empty(sql_text):
                applied_commit_ids.append(entry.commit_id)
                applied_sql_files.append(sql_path)
                continue

            if sql_text.strip():
                statements = _split_sql_statements(sql_text)
                for stmt in statements:
                    schema = _schema_for_statement(
                        stmt,
                        table_schema_by_name=table_schema_by_name,
                        type_schema_by_name=type_schema_by_name,
                    )
                    if schema is None:
                        # Allow compiler-emitted DO $$ blocks (failfast scripts / future backfills)
                        # to run even when a baseline search_path mapping exists.
                        if _RE_DO_DOLLAR_BLOCK.search(stmt):
                            await connection.execute(stmt)
                            continue
                        if base_schemas:
                            raise DBBootExecutionError(
                                "Unable to route migration statement to a schema; statement must target a "
                                "known table/type from the SQL baseline or use explicit schema qualification. "
                                f"commit_id={entry.commit_id} sql_file={sql_path}"
                            )
                        # No baseline: only safe option is to run as-is and rely on explicit qualification.
                        await connection.execute(stmt)
                        continue

                    if base_schemas:
                        search_path = _search_path_for_schema(schema=schema, all_schemas=base_schemas)
                        await connection.execute(f"SET LOCAL search_path TO {search_path};")
                    else:
                        # Best-effort: create explicitly referenced schema for schema-qualified statements.
                        if schema != "public":
                            await connection.execute(f"CREATE SCHEMA IF NOT EXISTS {_quote_ident(schema)};")
                    await connection.execute(stmt)
            applied_commit_ids.append(entry.commit_id)
            applied_sql_files.append(sql_path)

        await upsert_db_bootstrap_marker(
            connection=connection,
            environment_id=environment_id,
            ocg_hash=desired_ocg_hash,
            ocg_head_commit_id=lane.head_commit_id,
        )

    assert marker is not None
    assert from_commit_id is not None
    return OcgSqlMigrationApplyResult(
        applied=bool(applied_commit_ids) or marker.ocg_hash != desired_ocg_hash,
        environment_id=environment_id,
        from_commit_id=from_commit_id,
        to_commit_id=lane.head_commit_id,
        applied_commit_ids=tuple(applied_commit_ids),
        applied_sql_files=tuple(applied_sql_files),
    )


__all__ = [
    "OcgLaneCommit",
    "OcgLaneIndex",
    "OcgSqlMigrationApplyResult",
    "apply_ocg_sql_migrations",
    "load_ocg_lane_index",
]
