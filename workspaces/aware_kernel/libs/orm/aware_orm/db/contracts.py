"""Canonical DB installer contracts.

Ownership:
- `aware_orm.db` owns DB installer contracts.
- `aware_orm.runtime.db_boot` is kept as a compatibility shim/adaptor.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Protocol
from uuid import UUID


class DBBootPlanError(ValueError):
    """Raised when SQL discovery/planning cannot produce a valid install plan."""


class DBBootExecutionError(RuntimeError):
    """Raised when applying a DB install plan fails."""


@dataclass(frozen=True, slots=True)
class SQLBootStep:
    """Single DDL application step."""

    schema: str
    path: Path
    kind: str  # "type" | "table" | "other"

    @property
    def search_path(self) -> str:
        return self.schema


@dataclass(frozen=True, slots=True)
class SQLBootPlan:
    """Deterministic DB schema install plan from generated SQL files."""

    sql_roots: tuple[Path, ...]
    schemas: tuple[str, ...]
    steps: tuple[SQLBootStep, ...]


@dataclass(frozen=True, slots=True)
class DBBootResult:
    """Outcome of ensuring the DB schema is installed."""

    installed: bool
    environment_id: UUID
    ocg_hash: str
    ocg_head_commit_id: UUID | None
    sql_roots: tuple[Path, ...]
    schema_count: int
    step_count: int


@dataclass(frozen=True, slots=True)
class DBBootstrapMarker:
    """Persisted marker identifying installed schema lineage for one environment."""

    environment_id: UUID
    ocg_hash: str
    ocg_head_commit_id: UUID | None


class _DBBootTransaction(Protocol):
    async def __aenter__(self) -> object: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> object: ...


class DBBootConnection(Protocol):
    """Minimal async DB API contract required by DB boot/install executors.

    `asyncpg.Connection` satisfies this protocol.
    """

    def transaction(self) -> _DBBootTransaction: ...

    async def execute(self, query: str, *args: object) -> object: ...

    async def fetchrow(self, query: str, *args: object) -> Mapping[str, object] | None: ...


__all__ = [
    "DBBootConnection",
    "DBBootExecutionError",
    "DBBootPlanError",
    "DBBootResult",
    "DBBootstrapMarker",
    "SQLBootPlan",
    "SQLBootStep",
]
