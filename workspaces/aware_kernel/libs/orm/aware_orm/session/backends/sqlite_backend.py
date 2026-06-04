"""SQLite-backed persistence backend for local/plugin session rails."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from typing import Any
from uuid import UUID

from aware_orm.db import ensure_local_plugin_sqlite_schema_installed_from_registry
from aware_orm._support import logger

from .protocol import PersistenceBackendProtocol, QueryResult, SessionBackendState


_RE_PLACEHOLDER = re.compile(r"\$\d+")
_RE_INSERT_INTO = re.compile(r'(\bINSERT\s+INTO\s+)(?:"?[A-Za-z0-9_]+"?\.)("?[A-Za-z0-9_]+"?)', re.IGNORECASE)
_RE_UPDATE = re.compile(r'(\bUPDATE\s+)(?:"?[A-Za-z0-9_]+"?\.)("?[A-Za-z0-9_]+"?)', re.IGNORECASE)
_RE_DELETE_FROM = re.compile(
    r'(\bDELETE\s+FROM\s+)(?:"?[A-Za-z0-9_]+"?\.)("?[A-Za-z0-9_]+"?)',
    re.IGNORECASE,
)
_RE_FROM_JOIN = re.compile(r'(\b(?:FROM|JOIN)\s+)(?:"?[A-Za-z0-9_]+"?\.)("?[A-Za-z0-9_]+"?)', re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SqlitePersistenceConfig:
    database_path: str | Path
    registry_path: Path
    environment_id: UUID

    def database_target(self) -> str:
        token = str(self.database_path).strip()
        if token == ":memory:":
            return token
        return str(Path(token).expanduser().resolve())

    def resolved_registry_path(self) -> Path:
        return Path(self.registry_path).expanduser().resolve()


class SqlitePersistenceBackend(PersistenceBackendProtocol):
    """Persistence backend using stdlib sqlite3 with registry-owned schema boot."""

    def __init__(self, session: SessionBackendState, *, config: SqlitePersistenceConfig):
        self._session: SessionBackendState = session
        self._config: SqlitePersistenceConfig = config
        self._connection: sqlite3.Connection | None = None
        self._owns_connection: bool = False
        self._schema_ready: bool = False

    def enqueue_insert(self, sql: str, params: tuple[Any, ...]) -> None:
        self._session._pending_inserts.append((sql, params))
        logger.debug("Queued SQLITE INSERT: %s... (%d params)", sql[:50], len(params))

    def enqueue_update(self, sql: str, params: tuple[Any, ...]) -> None:
        self._session._pending_updates.append((sql, params))
        logger.debug("Queued SQLITE UPDATE: %s... (%d params)", sql[:50], len(params))

    def enqueue_delete(self, sql: str, params: tuple[Any, ...]) -> None:
        self._session._pending_deletes.append((sql, params))
        logger.debug("Queued SQLITE DELETE: %s... (%d params)", sql[:50], len(params))

    def has_pending_operations(self) -> bool:
        return bool(self._session._pending_inserts or self._session._pending_updates or self._session._pending_deletes)

    def get_pending_counts(self) -> dict[str, int]:
        return {
            "inserts": len(self._session._pending_inserts),
            "updates": len(self._session._pending_updates),
            "deletes": len(self._session._pending_deletes),
        }

    def clear_pending(self) -> None:
        self._session._pending_inserts.clear()
        self._session._pending_updates.clear()
        self._session._pending_deletes.clear()

    async def execute_read(self, sql: str, params: tuple[Any, ...]) -> QueryResult:
        if self._session.skip_db:
            logger.warning("Skipping sqlite read in offline mode (skip_db=True)")
            return []

        connection = await self._ensure_connection()
        cursor = connection.execute(self._normalize_sql(sql), self._normalize_params(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    async def commit(self) -> None:
        if self._session.skip_db:
            logger.warning("Skipping sqlite commit in offline mode (skip_db=True)")
            return
        if not self.has_pending_operations():
            logger.debug("No pending sqlite operations to commit")
            return

        connection = await self._ensure_connection()
        try:
            self._execute_grouped(connection, self._session._pending_deletes, "DELETE")
            self._execute_grouped(connection, self._session._pending_inserts, "INSERT")
            self._execute_grouped(connection, self._session._pending_updates, "UPDATE")
            connection.commit()
            self.clear_pending()
            logger.debug("Session committed successfully via sqlite")
        except Exception:
            connection.rollback()
            self.clear_pending()
            raise

    async def rollback(self) -> None:
        if self._connection is not None:
            try:
                self._connection.rollback()
            except Exception:
                pass
        self.clear_pending()
        logger.debug("Session rolled back (sqlite backend)")

    async def _ensure_connection(self) -> sqlite3.Connection:
        if isinstance(self._session.connection, sqlite3.Connection):
            connection = self._session.connection
            self._connection = connection
        elif self._connection is not None:
            connection = self._connection
        else:
            target = self._config.database_target()
            if target != ":memory:":
                Path(target).parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(target)
            self._connection = connection
            self._owns_connection = True
            self._session.connection = connection

        connection.row_factory = sqlite3.Row
        if not self._schema_ready:
            await ensure_local_plugin_sqlite_schema_installed_from_registry(
                connection=connection,
                registry_path=self._config.resolved_registry_path(),
                environment_id=self._config.environment_id,
            )
            self._schema_ready = True
        return connection

    def _execute_grouped(
        self,
        connection: sqlite3.Connection,
        operations: list[tuple[str, tuple[Any, ...]]],
        op_name: str,
    ) -> None:
        if not operations:
            return

        index = 0
        while index < len(operations):
            sql, _ = operations[index]
            batch_params: list[tuple[Any, ...]] = []
            while index < len(operations) and operations[index][0] == sql:
                batch_params.append(self._normalize_params(operations[index][1]))
                index += 1

            normalized_sql = self._normalize_sql(sql)
            if len(batch_params) == 1:
                connection.execute(normalized_sql, batch_params[0])
            else:
                connection.executemany(normalized_sql, batch_params)
            logger.debug("Executed SQLITE %s: %s... x%d", op_name, normalized_sql[:50], len(batch_params))

    @classmethod
    def _normalize_sql(cls, sql: str) -> str:
        normalized = _RE_PLACEHOLDER.sub("?", sql)
        normalized = _RE_INSERT_INTO.sub(r"\1\2", normalized)
        normalized = _RE_UPDATE.sub(r"\1\2", normalized)
        normalized = _RE_DELETE_FROM.sub(r"\1\2", normalized)
        normalized = _RE_FROM_JOIN.sub(r"\1\2", normalized)
        return normalized

    @staticmethod
    def _normalize_params(params: tuple[Any, ...]) -> tuple[Any, ...]:
        normalized: list[Any] = []
        for value in params:
            if isinstance(value, UUID):
                normalized.append(str(value))
                continue
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                normalized.append(value.isoformat())
                continue
            enum_value = getattr(value, "value", None)
            if enum_value is not None:
                normalized.append(enum_value)
                continue
            normalized.append(value)
        return tuple(normalized)


__all__ = [
    "SqlitePersistenceBackend",
    "SqlitePersistenceConfig",
]
