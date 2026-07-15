"""
Protocol definitions for pluggable ORM persistence backends.

Backends are responsible for queueing write operations, executing reads, and
flushing/rolling back transactions for a Session. They should be lightweight
and stateless beyond per-session state.
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, Tuple, runtime_checkable
from uuid import UUID

from aware_orm.query_spec import QuerySpec
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata


QueryResult = List[Dict[str, Any]]
PendingSQLOperation = Tuple[str, Tuple[Any, ...]]


@runtime_checkable
class PersistenceBackendProtocol(Protocol):
    """Contract all persistence backends must implement."""

    def enqueue_insert(self, sql: str, params: Tuple[Any, ...]) -> None:
        """Queue an INSERT operation."""
        ...

    def enqueue_update(self, sql: str, params: Tuple[Any, ...]) -> None:
        """Queue an UPDATE operation."""
        ...

    def enqueue_delete(self, sql: str, params: Tuple[Any, ...]) -> None:
        """Queue a DELETE operation."""
        ...

    def has_pending_operations(self) -> bool:
        """Return True if there are pending queued write operations."""
        ...

    def get_pending_counts(self) -> Dict[str, int]:
        """Return counts of pending operations by type."""
        ...

    def clear_pending(self) -> None:
        """Clear all queued write operations without flushing them."""
        ...

    async def execute_read(self, sql: str, params: Tuple[Any, ...]) -> QueryResult:
        """Execute a read/select query and return result rows."""
        ...

    async def commit(self) -> None:
        """Flush queued operations."""
        ...

    async def rollback(self) -> None:
        """Rollback queued operations."""
        ...


@runtime_checkable
class QuerySpecBackendProtocol(Protocol):
    """Optional backend hook for structured QuerySpec execution."""

    async def execute_query_spec(
        self,
        *,
        sql_metadata: SQLRuntimeMetadata,
        query_spec: QuerySpec,
        source_class_fqn: str | None,
        count: bool = False,
    ) -> QueryResult:
        """Execute a structured QuerySpec without forcing callers through SQL strings."""
        ...


@runtime_checkable
class SessionBackendState(Protocol):
    """Minimal session surface required by persistence backends."""

    connection: object | None
    skip_db: bool
    _pending_inserts: List[PendingSQLOperation]
    _pending_updates: List[PendingSQLOperation]
    _pending_deletes: List[PendingSQLOperation]

    @property
    def branch_id(self) -> UUID:
        """Branch identifier for branch-scoped backends."""
        ...
