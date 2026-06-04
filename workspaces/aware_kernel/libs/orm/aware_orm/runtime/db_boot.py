"""Runtime compatibility shim for ORM DB boot helpers.

Owner rail:
- Canonical DB boot planning/execution surface now lives in ``aware_orm.db.boot``.

Compatibility contract:
- Runtime callsites may keep importing ``aware_orm.runtime.db_boot`` during migration.
- This module re-exports the owner symbols unchanged.
"""

from __future__ import annotations

from aware_orm.db.boot import (
    DBBootAdapter,
    DBBootAdapterName,
    DBBootConnection,
    DBBootExecutionError,
    DBBootPlanError,
    DBBootResult,
    DBBootstrapMarker,
    SQLBootPlan,
    SQLBootStep,
    build_sql_boot_plan,
    build_sql_boot_plan_multi,
    discover_sql_files,
    ensure_db_bootstrap_marker_table,
    ensure_db_schema_installed,
    ensure_db_schema_installed_multi,
    fetch_db_bootstrap_marker,
    resolve_db_boot_adapter,
    upsert_db_bootstrap_marker,
)

__all__ = [
    "DBBootAdapter",
    "DBBootAdapterName",
    "DBBootConnection",
    "DBBootExecutionError",
    "DBBootPlanError",
    "DBBootResult",
    "DBBootstrapMarker",
    "SQLBootPlan",
    "SQLBootStep",
    "build_sql_boot_plan",
    "build_sql_boot_plan_multi",
    "discover_sql_files",
    "ensure_db_bootstrap_marker_table",
    "ensure_db_schema_installed",
    "ensure_db_schema_installed_multi",
    "fetch_db_bootstrap_marker",
    "resolve_db_boot_adapter",
    "upsert_db_bootstrap_marker",
]
