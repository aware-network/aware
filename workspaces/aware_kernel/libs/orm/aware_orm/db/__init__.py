"""Canonical DB installer contracts (owner rail).

This package is the long-term owner for ORM DB installer primitives.
Runtime-facing modules should import contracts from here and keep runtime
modules as adapters/shims.
"""

from .contracts import (
    DBBootConnection,
    DBBootExecutionError,
    DBBootPlanError,
    DBBootResult,
    DBBootstrapMarker,
    SQLBootPlan,
    SQLBootStep,
)
from .boot import (
    build_local_plugin_sqlite_boot_plan_from_registry,
    build_sql_boot_plan,
    build_sql_boot_plan_from_registry,
    build_sql_boot_plan_multi,
    discover_sql_files,
    ensure_db_bootstrap_marker_table,
    ensure_db_schema_installed,
    ensure_db_schema_installed_multi,
    ensure_local_plugin_sqlite_schema_installed_from_registry,
    fetch_db_bootstrap_marker,
    upsert_db_bootstrap_marker,
)
from .adapters import (
    DBBootAdapter,
    DBBootAdapterName,
    POSTGRES_DB_BOOT_ADAPTER,
    SQLITE_DB_BOOT_ADAPTER,
    resolve_db_boot_adapter,
)
from .schema_registry import (
    DBBackendTarget,
    DBPackageKind,
    DBSchemaRegistry,
    DBSchemaRegistryEntry,
    DBSchemaRegistryError,
    DBSchemaRegistryNotFoundError,
    DBSchemaRegistryResolutionError,
    DBSchemaRegistryValidationError,
    build_db_schema_registry_entry,
    compute_db_schema_registry_payload_hash,
    compute_sql_root_source_hash,
    iter_registry_sql_files,
    load_db_schema_registry,
    resolve_db_schema_registry_sql_roots,
    write_db_schema_registry,
)

__all__ = [
    "DBBootConnection",
    "DBBootAdapter",
    "DBBootAdapterName",
    "DBBootExecutionError",
    "DBBootPlanError",
    "DBBootResult",
    "DBBootstrapMarker",
    "SQLBootPlan",
    "SQLBootStep",
    "DBBackendTarget",
    "DBPackageKind",
    "DBSchemaRegistry",
    "DBSchemaRegistryEntry",
    "DBSchemaRegistryError",
    "DBSchemaRegistryNotFoundError",
    "DBSchemaRegistryResolutionError",
    "DBSchemaRegistryValidationError",
    "build_sql_boot_plan",
    "build_sql_boot_plan_from_registry",
    "build_sql_boot_plan_multi",
    "build_local_plugin_sqlite_boot_plan_from_registry",
    "build_db_schema_registry_entry",
    "compute_db_schema_registry_payload_hash",
    "compute_sql_root_source_hash",
    "discover_sql_files",
    "ensure_db_bootstrap_marker_table",
    "ensure_db_schema_installed",
    "ensure_db_schema_installed_multi",
    "ensure_local_plugin_sqlite_schema_installed_from_registry",
    "fetch_db_bootstrap_marker",
    "POSTGRES_DB_BOOT_ADAPTER",
    "iter_registry_sql_files",
    "load_db_schema_registry",
    "resolve_db_schema_registry_sql_roots",
    "upsert_db_bootstrap_marker",
    "write_db_schema_registry",
    "resolve_db_boot_adapter",
    "SQLITE_DB_BOOT_ADAPTER",
]
