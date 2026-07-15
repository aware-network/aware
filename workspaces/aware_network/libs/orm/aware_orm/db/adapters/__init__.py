"""DB boot adapter registry and resolver."""

from __future__ import annotations

from aware_orm.db.contracts import DBBootPlanError

from .base import DBBootAdapter, DBBootAdapterName
from .postgres import POSTGRES_DB_BOOT_ADAPTER
from .sqlite import SQLITE_DB_BOOT_ADAPTER


def resolve_db_boot_adapter(adapter: object | None = None) -> DBBootAdapter:
    """Resolve backend adapter by explicit name or custom adapter instance."""
    if adapter is None:
        return POSTGRES_DB_BOOT_ADAPTER

    if isinstance(adapter, str):
        if adapter == "postgres":
            return POSTGRES_DB_BOOT_ADAPTER
        if adapter == "sqlite":
            return SQLITE_DB_BOOT_ADAPTER
        raise DBBootPlanError(f"Unsupported DB boot adapter: {adapter!r}")

    # runtime_checkable protocol in `base.py` allows structural instance checks.
    if isinstance(adapter, DBBootAdapter):
        return adapter

    raise DBBootPlanError(f"Invalid DB boot adapter type: {type(adapter)!r}")


__all__ = [
    "DBBootAdapter",
    "DBBootAdapterName",
    "POSTGRES_DB_BOOT_ADAPTER",
    "SQLITE_DB_BOOT_ADAPTER",
    "resolve_db_boot_adapter",
]
