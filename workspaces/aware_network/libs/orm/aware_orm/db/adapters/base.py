"""Shared DB boot adapter contracts.

Adapters own backend-specific execution semantics (postgres/sqlite/etc).
The owner boot module (`aware_orm.db.boot`) remains planner/environment only.
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable
from uuid import UUID

from aware_orm.db.contracts import DBBootResult, SQLBootPlan


DBBootAdapterName = Literal["postgres", "sqlite"]


@runtime_checkable
class DBBootAdapter(Protocol):
    """Backend-specific DB install execution adapter."""

    @property
    def name(self) -> DBBootAdapterName: ...

    async def ensure_schema_installed(
        self,
        *,
        connection: object,
        plan: SQLBootPlan,
        environment_id: UUID,
        ocg_hash: str,
        ocg_head_commit_id: UUID | None = None,
    ) -> DBBootResult:
        """Apply a SQL boot plan and return install result."""
        ...


__all__ = [
    "DBBootAdapter",
    "DBBootAdapterName",
]
