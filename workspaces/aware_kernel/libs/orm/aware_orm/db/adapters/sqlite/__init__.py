"""SQLite DB boot adapter rail.

Owns sqlite-specific schema install semantics and bootstrap marker handling.
"""

from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass
import inspect
from typing import Any, cast
from uuid import UUID

from aware_orm.db.contracts import DBBootExecutionError, DBBootResult, DBBootstrapMarker, SQLBootPlan

from ..base import DBBootAdapterName


_MARKER_TABLE_NAME = "aware_bootstrap_marker"
_MARKER_TABLE_CREATE_SQL = f"""
CREATE TABLE IF NOT EXISTS {_MARKER_TABLE_NAME} (
  environment_id TEXT PRIMARY KEY NOT NULL,
  ocg_hash TEXT NOT NULL,
  ocg_head_commit_id TEXT,
  installed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""".strip()


def _parse_uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return UUID(value)
        except Exception:
            return None
    return None


def _is_effective_sql_empty(sql_text: str) -> bool:
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        return False
    return True


def _is_sqlite_boot_connection(connection: object) -> bool:
    return all(callable(getattr(connection, attr, None)) for attr in ("execute", "commit", "rollback"))


async def _maybe_await(value: object) -> object:
    if inspect.isawaitable(value):
        return await cast(Awaitable[object], value)
    return value


async def _execute(connection: object, sql: str, params: tuple[object, ...] = ()) -> object:
    execute = getattr(connection, "execute", None)
    if not callable(execute):  # pragma: no cover - guarded by connection check
        raise DBBootExecutionError("SQLite connection does not expose execute(...)")
    return await _maybe_await(execute(sql, params))


async def _executescript(connection: object, sql_text: str) -> object:
    executescript = getattr(connection, "executescript", None)
    if callable(executescript):
        return await _maybe_await(executescript(sql_text))
    return await _execute(connection, sql_text)


async def _fetchone(cursor: object) -> object | None:
    fetchone = getattr(cursor, "fetchone", None)
    if callable(fetchone):
        return await _maybe_await(fetchone())
    return None


def _extract_marker_fields(row: object) -> tuple[str | None, str | None]:
    if isinstance(row, tuple):
        if not row:
            return None, None
        ocg_hash = row[0] if len(row) > 0 else None
        head = row[1] if len(row) > 1 else None
        return cast(str | None, ocg_hash), cast(str | None, head)

    get = getattr(row, "get", None)
    if callable(get):
        ocg_hash = get("ocg_hash")
        head = get("ocg_head_commit_id")
        return cast(str | None, ocg_hash), cast(str | None, head)

    try:
        ocg_hash = cast(Any, row)["ocg_hash"]
        head = cast(Any, row)["ocg_head_commit_id"]
        return cast(str | None, ocg_hash), cast(str | None, head)
    except Exception:
        return None, None


async def ensure_db_bootstrap_marker_table(*, connection: object) -> None:
    _ = await _execute(connection, _MARKER_TABLE_CREATE_SQL)


async def fetch_db_bootstrap_marker(
    *,
    connection: object,
    environment_id: UUID,
) -> DBBootstrapMarker | None:
    cursor = await _execute(
        connection,
        f"SELECT ocg_hash, ocg_head_commit_id FROM {_MARKER_TABLE_NAME} WHERE environment_id = ?",
        (str(environment_id),),
    )
    row = await _fetchone(cursor)
    if row is None:
        return None

    ocg_hash, ocg_head_commit_id = _extract_marker_fields(row)
    if not isinstance(ocg_hash, str) or not ocg_hash.strip():
        return None
    return DBBootstrapMarker(
        environment_id=environment_id,
        ocg_hash=ocg_hash,
        ocg_head_commit_id=_parse_uuid_or_none(ocg_head_commit_id),
    )


async def upsert_db_bootstrap_marker(
    *,
    connection: object,
    environment_id: UUID,
    ocg_hash: str,
    ocg_head_commit_id: UUID | None,
) -> None:
    _ = await _execute(
        connection,
        f"""
INSERT INTO {_MARKER_TABLE_NAME} (environment_id, ocg_hash, ocg_head_commit_id, installed_at)
VALUES (?, ?, ?, CURRENT_TIMESTAMP)
ON CONFLICT(environment_id) DO UPDATE SET
  ocg_hash=excluded.ocg_hash,
  ocg_head_commit_id=excluded.ocg_head_commit_id,
  installed_at=CURRENT_TIMESTAMP;
""".strip(),
        (str(environment_id), ocg_hash, str(ocg_head_commit_id) if ocg_head_commit_id is not None else None),
    )


@dataclass(frozen=True, slots=True)
class SQLiteDBBootAdapter:
    """SQLite DB install execution adapter."""

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
        if not _is_sqlite_boot_connection(connection):
            raise DBBootExecutionError(
                "SQLite DB boot adapter requires connection implementing execute/commit/rollback"
            )
        if not plan.sql_roots:
            raise DBBootExecutionError("sql_roots must be non-empty")

        await ensure_db_bootstrap_marker_table(connection=connection)
        marker = await fetch_db_bootstrap_marker(connection=connection, environment_id=environment_id)
        if marker is not None:
            if marker.ocg_hash == ocg_hash:
                return DBBootResult(
                    installed=False,
                    environment_id=environment_id,
                    ocg_hash=ocg_hash,
                    ocg_head_commit_id=marker.ocg_head_commit_id,
                    sql_roots=plan.sql_roots,
                    schema_count=0,
                    step_count=0,
                )
            raise DBBootExecutionError(
                "DB already bootstrapped with a different ocg_hash; migrations are not implemented. "
                f"environment_id={environment_id} existing_ocg_hash={marker.ocg_hash} requested_ocg_hash={ocg_hash}"
            )

        _ = await _execute(connection, "BEGIN")
        try:
            for step in plan.steps:
                sql_text = step.path.read_text(encoding="utf-8")
                if _is_effective_sql_empty(sql_text):
                    continue
                try:
                    _ = await _executescript(connection, sql_text)
                except Exception as exc:
                    raise DBBootExecutionError(
                        "Failed to execute sqlite DDL step "
                        f"(kind={step.kind} schema={step.schema} file={step.path}): {exc}"
                    ) from exc

            await upsert_db_bootstrap_marker(
                connection=connection,
                environment_id=environment_id,
                ocg_hash=ocg_hash,
                ocg_head_commit_id=ocg_head_commit_id,
            )
            _ = await _maybe_await(getattr(connection, "commit")())
        except Exception as exc:
            try:
                _ = await _maybe_await(getattr(connection, "rollback")())
            except Exception:
                pass
            if isinstance(exc, DBBootExecutionError):
                raise
            raise DBBootExecutionError(f"SQLite schema install transaction failed: {exc}") from exc

        return DBBootResult(
            installed=True,
            environment_id=environment_id,
            ocg_hash=ocg_hash,
            ocg_head_commit_id=ocg_head_commit_id,
            sql_roots=plan.sql_roots,
            schema_count=len(plan.schemas),
            step_count=len(plan.steps),
        )


SQLITE_DB_BOOT_ADAPTER = SQLiteDBBootAdapter()


__all__ = [
    "ensure_db_bootstrap_marker_table",
    "fetch_db_bootstrap_marker",
    "SQLITE_DB_BOOT_ADAPTER",
    "SQLiteDBBootAdapter",
    "upsert_db_bootstrap_marker",
]
