from __future__ import annotations

from aware_orm.db import boot as owner_boot
from aware_orm.runtime import db_boot as runtime_boot


def test_runtime_db_boot_reexports_owner_boot_functions() -> None:
    assert runtime_boot.discover_sql_files is owner_boot.discover_sql_files
    assert runtime_boot.build_sql_boot_plan is owner_boot.build_sql_boot_plan
    assert runtime_boot.build_sql_boot_plan_multi is owner_boot.build_sql_boot_plan_multi
    assert runtime_boot.resolve_db_boot_adapter is owner_boot.resolve_db_boot_adapter
    assert runtime_boot.ensure_db_bootstrap_marker_table is owner_boot.ensure_db_bootstrap_marker_table
    assert runtime_boot.fetch_db_bootstrap_marker is owner_boot.fetch_db_bootstrap_marker
    assert runtime_boot.upsert_db_bootstrap_marker is owner_boot.upsert_db_bootstrap_marker
    assert runtime_boot.ensure_db_schema_installed is owner_boot.ensure_db_schema_installed
    assert runtime_boot.ensure_db_schema_installed_multi is owner_boot.ensure_db_schema_installed_multi
