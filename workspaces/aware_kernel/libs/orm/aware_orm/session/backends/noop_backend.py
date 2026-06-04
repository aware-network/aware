"""
No-op persistence backend used when sessions run in skip_db mode.

This backend preserves the previous Session behaviour where SQL operations
are collected but never executed. It is ideal for bootstrap and grammar tests
that operate without a database or alternate persistence target.
"""

# @doc-ref: ../../../docs/session/runtime.md
# @test-ref: ../../../tests/session/test_backends.py

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from aware_orm._support import logger

from .protocol import PersistenceBackendProtocol, QueryResult, SessionBackendState


class NoopPersistenceBackend(PersistenceBackendProtocol):
    """Collect operations without executing them."""

    def __init__(self, session: SessionBackendState):
        self._session = session

    # ---------- Queue management ----------

    def enqueue_insert(self, sql: str, params: Tuple[Any, ...]) -> None:
        self._session._pending_inserts.append((sql, params))
        logger.debug("noop backend: captured INSERT (skip_db)")

    def enqueue_update(self, sql: str, params: Tuple[Any, ...]) -> None:
        self._session._pending_updates.append((sql, params))
        logger.debug("noop backend: captured UPDATE (skip_db)")

    def enqueue_delete(self, sql: str, params: Tuple[Any, ...]) -> None:
        self._session._pending_deletes.append((sql, params))
        logger.debug("noop backend: captured DELETE (skip_db)")

    def has_pending_operations(self) -> bool:
        return bool(self._session._pending_inserts or self._session._pending_updates or self._session._pending_deletes)

    def get_pending_counts(self) -> Dict[str, int]:
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
        logger.debug("noop backend: execute_read skipped for %s", sql[:100])
        return []

    # ---------- Transaction handling ----------

    async def commit(self) -> None:
        logger.debug("noop backend: commit skipped (skip_db=True)")

    async def rollback(self) -> None:
        self.clear_pending()
        logger.debug("noop backend: rollback cleared pending operations")
