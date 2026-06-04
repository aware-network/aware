"""
Database-backed persistence backend using asyncpg or provided connections.
"""

# @doc-ref: ../../../docs/session/runtime.md
# @test-ref: ../../../tests/session/test_backends.py

from __future__ import annotations

import os
import json
from contextlib import AbstractAsyncContextManager
from collections.abc import Mapping, Sequence
from typing import Any, List, Protocol, Tuple, runtime_checkable

from aware_orm._support import logger

from .protocol import PersistenceBackendProtocol, QueryResult, SessionBackendState

asyncpg: Any | None = None


def _require_asyncpg() -> Any:
    global asyncpg
    if asyncpg is not None:
        return asyncpg
    try:
        import asyncpg as asyncpg_module
    except ModuleNotFoundError as exc:
        raise RuntimeError("asyncpg is required for the PostgreSQL ORM backend; install aware-orm[postgres]") from exc
    asyncpg = asyncpg_module
    return asyncpg_module


@runtime_checkable
class AsyncDatabaseConnection(Protocol):
    async def fetch(
        self,
        query: str,
        *args: Any,
        timeout: float | None = None,
        record_class: type[object] | None = None,
    ) -> Sequence[Mapping[str, object]]:
        ...

    def transaction(
        self,
        *,
        isolation: object | None = None,
        readonly: bool = False,
        deferrable: bool = False,
    ) -> AbstractAsyncContextManager[object]:
        ...

    async def execute(self, query: str, *args: Any, timeout: float | None = None) -> object:
        ...

    async def executemany(self, command: str, args: object, *, timeout: float | None = None) -> object:
        ...


class DatabasePersistenceBackend(PersistenceBackendProtocol):
    """Persistence backend that mirrors the prior Session SQL behaviour."""

    def __init__(self, session: SessionBackendState):
        self._session: SessionBackendState = session

    @staticmethod
    def _require_async_connection(connection: object | None) -> AsyncDatabaseConnection:
        if connection is None:
            raise RuntimeError("No connection available for database backend")
        if not isinstance(connection, AsyncDatabaseConnection):
            raise TypeError("Provided connection does not implement the async DB connection contract")
        return connection

    async def _configure_asyncpg_json_codecs(self, connection: object) -> None:
        set_type_codec = getattr(connection, "set_type_codec", None)
        if set_type_codec is None:
            return

        def _encode(value: Any) -> str:
            # asyncpg treats JSON/JSONB params as text in `executemany()`; callers may pass
            # either rich Python objects (dict/list) or pre-serialized JSON strings.
            #
            # - dict/list/etc → stable JSON string
            # - str → treated as already-serialized JSON (avoid double-encoding)
            if isinstance(value, str):
                return value
            return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)

        def _decode(value: str) -> str:
            # Preserve the prior "JSON as string" behavior on reads.
            return value

        await set_type_codec("json", encoder=_encode, decoder=_decode, schema="pg_catalog")
        await set_type_codec("jsonb", encoder=_encode, decoder=_decode, schema="pg_catalog")

    # ---------- Queue management ----------

    def enqueue_insert(self, sql: str, params: Tuple[Any, ...]) -> None:
        self._session._pending_inserts.append((sql, params))
        logger.debug(f"Queued INSERT: {sql[:50]}... ({len(params)} params)")

    def enqueue_update(self, sql: str, params: Tuple[Any, ...]) -> None:
        self._session._pending_updates.append((sql, params))
        logger.debug(f"Queued UPDATE: {sql[:50]}... ({len(params)} params)")

    def enqueue_delete(self, sql: str, params: Tuple[Any, ...]) -> None:
        self._session._pending_deletes.append((sql, params))
        logger.debug(f"Queued DELETE: {sql[:50]}... ({len(params)} params)")

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

    # ---------- Read operations ----------

    async def execute_read(self, sql: str, params: Tuple[Any, ...]) -> QueryResult:
        if self._session.skip_db:
            logger.warning("Skipping query in offline mode (skip_db=True) - returning empty list")
            return []

        if self._session.connection:
            return await self._execute_query_via_connection(sql, params)
        return await self._execute_query_via_asyncpg(sql, params)

    async def _execute_query_via_connection(self, sql: str, params: Tuple[Any, ...]) -> QueryResult:
        connection = self._require_async_connection(self._session.connection)

        try:
            logger.debug(f"Executing query via connection: {sql[:100]}...")
            result = await connection.fetch(sql, *params)
            return [dict(record) for record in result]
        except Exception as exc:
            logger.error(f"Query execution failed via connection: {exc}")
            raise

    async def _execute_query_via_asyncpg(self, sql: str, params: Tuple[Any, ...]) -> QueryResult:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required for asyncpg connections")

        asyncpg_module = _require_asyncpg()
        connection: Any | None = None
        try:
            logger.debug(f"Executing query via asyncpg: {sql[:100]}...")
            connection = await asyncpg_module.connect(database_url)
            if connection is None:
                raise RuntimeError("Failed to connect to database via asyncpg")
            await self._configure_asyncpg_json_codecs(connection)
            result = await connection.fetch(sql, *params)
            return [dict(record) for record in result]
        except Exception as exc:
            logger.error(f"Query execution failed via asyncpg: {exc}")
            raise
        finally:
            if connection:
                close_connection = getattr(connection, "close", None)
                if close_connection is not None:
                    await close_connection()

    # ---------- Transaction handling ----------

    async def commit(self) -> None:
        if self._session.skip_db:
            logger.warning("Skipping commit in offline mode (skip_db=True) - operations remain queued")
            return

        if not self.has_pending_operations():
            logger.debug("No pending operations to commit")
            return

        if self._session.connection:
            await self._commit_via_connection()
        else:
            await self._commit_via_asyncpg()

    async def rollback(self) -> None:
        self.clear_pending()
        logger.debug("Session rolled back (database backend)")

    async def _commit_via_asyncpg(self) -> None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required for asyncpg connections")

        asyncpg_module = _require_asyncpg()
        connection: Any | None = None
        try:
            inserts = len(self._session._pending_inserts)
            updates = len(self._session._pending_updates)
            deletes = len(self._session._pending_deletes)

            logger.debug(f"Committing session via asyncpg: {deletes} deletes, {inserts} inserts, {updates} updates")

            connection = await asyncpg_module.connect(database_url)
            if connection is None:
                raise RuntimeError("Failed to connect to database via asyncpg")
            await self._configure_asyncpg_json_codecs(connection)
            async with connection.transaction():
                await self._execute_grouped(connection, self._session._pending_deletes, "DELETE")
                await self._execute_grouped(connection, self._session._pending_inserts, "INSERT")
                await self._execute_grouped(connection, self._session._pending_updates, "UPDATE")

            self.clear_pending()
            logger.debug("Session committed successfully via asyncpg")
        except Exception as exc:
            logger.error(f"Session commit failed via asyncpg: {exc}")
            self.clear_pending()
            raise
        finally:
            if connection:
                close_connection = getattr(connection, "close", None)
                if close_connection is not None:
                    await close_connection()

    async def _commit_via_connection(self) -> None:
        connection = self._require_async_connection(self._session.connection)

        if not self.has_pending_operations():
            return

        try:
            await self._configure_asyncpg_json_codecs(connection)

            inserts = len(self._session._pending_inserts)
            updates = len(self._session._pending_updates)
            deletes = len(self._session._pending_deletes)
            logger.debug(
                f"Committing session via provided connection: {deletes} deletes, {inserts} inserts, {updates} updates"
            )

            async with connection.transaction():
                await self._execute_grouped(connection, self._session._pending_deletes, "DELETE")
                await self._execute_grouped(connection, self._session._pending_inserts, "INSERT")
                await self._execute_grouped(connection, self._session._pending_updates, "UPDATE")

            self.clear_pending()
            logger.debug("Session committed successfully via provided connection")
        except Exception as exc:
            logger.error(f"Session commit failed via provided connection: {exc}")
            self.clear_pending()
            raise

    async def _execute_grouped(
        self,
        connection: Any,
        operations: List[Tuple[str, Tuple[Any, ...]]],
        op_name: str,
    ) -> None:
        if not operations:
            return
        i = 0
        while i < len(operations):
            sql, _ = operations[i]
            batch: List[Tuple[Any, ...]] = []
            while i < len(operations) and operations[i][0] == sql:
                batch.append(operations[i][1])
                i += 1

            try:
                if len(batch) == 1:
                    await connection.execute(sql, *batch[0])
                else:
                    await connection.executemany(sql, batch)
            except Exception as exc:
                sample_params: object = batch[0] if len(batch) == 1 else batch[:3]
                logger.error(
                    "Failed %s SQL during session commit: sql=%s params=%s error=%s",
                    op_name,
                    sql,
                    sample_params,
                    exc,
                )
                raise
            logger.debug(f"Executed {op_name}: {sql[:50]}... x{len(batch)}")
