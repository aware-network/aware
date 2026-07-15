from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from aware_orm.db.boot import (
    DBBootPlanError,
    build_local_plugin_sqlite_boot_plan_from_registry,
)
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    DBSchemaRegistryResolutionError,
    build_db_schema_registry_entry,
    compute_sql_root_source_hash,
    load_db_schema_registry,
    resolve_db_schema_registry_sql_roots,
    write_db_schema_registry,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_schema_registry_write_and_load_roundtrip(tmp_path: Path) -> None:
    env_id = uuid4()
    sql_root = tmp_path / "sql" / "a"
    _write(sql_root / "t.sql", 'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL);\n')

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="ontology",
        backend_targets=("postgres",),
        sql_root=sql_root,
        source_label="module:a",
        relative_to=registry_path.parent,
    )
    payload_hash = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=env_id, entries=[entry]),
    )

    assert payload_hash.startswith("sha256:")
    loaded = load_db_schema_registry(path=registry_path)
    assert loaded.environment_id == env_id
    assert len(loaded.entries) == 1
    assert loaded.entries[0].source_hash == compute_sql_root_source_hash(sql_root=sql_root)


def test_schema_registry_resolve_filters_and_validates(tmp_path: Path) -> None:
    env_id = uuid4()
    sql_root = tmp_path / "sql" / "a"
    _write(sql_root / "t.sql", 'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL);\n')

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="ontology",
        backend_targets=("postgres",),
        sql_root=sql_root,
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=env_id, entries=[entry]),
    )

    roots = resolve_db_schema_registry_sql_roots(
        registry_path=registry_path,
        environment_id=env_id,
        package_kind="ontology",
        backend_target="postgres",
    )
    assert roots == (sql_root.resolve(),)

    with pytest.raises(DBSchemaRegistryResolutionError, match="filter returned no entries"):
        _ = resolve_db_schema_registry_sql_roots(
            registry_path=registry_path,
            environment_id=env_id,
            package_kind="state",
            backend_target="sqlite",
        )


def test_schema_registry_resolve_fails_on_hash_mismatch(tmp_path: Path) -> None:
    env_id = uuid4()
    sql_root = tmp_path / "sql" / "a"
    sql_file = sql_root / "t.sql"
    _write(sql_file, 'CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL);\n')

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="ontology",
        backend_targets=("postgres",),
        sql_root=sql_root,
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=env_id, entries=[entry]),
    )

    # Drift after compile should fail closed.
    sql_file.write_text('CREATE TABLE "t" (id UUID PRIMARY KEY NOT NULL, x INT);\n', encoding="utf-8")

    with pytest.raises(DBSchemaRegistryResolutionError, match="source hash mismatch"):
        _ = resolve_db_schema_registry_sql_roots(
            registry_path=registry_path,
            environment_id=env_id,
            package_kind="ontology",
            backend_target="postgres",
        )


def test_local_plugin_sqlite_boot_plan_uses_state_sqlite_filter(tmp_path: Path) -> None:
    env_id = uuid4()
    ontology_root = tmp_path / "sql" / "ontology"
    db_root = tmp_path / "sql" / "interface_db"
    _write(
        ontology_root / "actor" / "environment.sql",
        'CREATE TABLE "environment" (id UUID PRIMARY KEY NOT NULL);\n',
    )
    _write(
        db_root / "workspace" / "window_layout.sql",
        'CREATE TABLE "window_layout" (id TEXT PRIMARY KEY NOT NULL);\n',
    )

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entries = [
        build_db_schema_registry_entry(
            package_kind="ontology",
            backend_targets=("postgres",),
            sql_root=ontology_root,
            source_label="ontology",
            relative_to=registry_path.parent,
        ),
        build_db_schema_registry_entry(
            package_kind="state",
            backend_targets=("sqlite",),
            sql_root=db_root,
            source_label="interface-db",
            relative_to=registry_path.parent,
        ),
    ]
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=env_id, entries=entries),
    )

    plan = build_local_plugin_sqlite_boot_plan_from_registry(
        registry_path=registry_path,
        environment_id=env_id,
    )

    assert plan.sql_roots == (db_root.resolve(),)
    assert len(plan.steps) == 1
    assert plan.steps[0].kind == "table"
    assert plan.steps[0].schema == "workspace"


def test_local_plugin_sqlite_boot_plan_fails_without_state_sqlite_entries(tmp_path: Path) -> None:
    env_id = uuid4()
    ontology_root = tmp_path / "sql" / "ontology"
    _write(
        ontology_root / "actor" / "environment.sql",
        'CREATE TABLE "environment" (id UUID PRIMARY KEY NOT NULL);\n',
    )

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="ontology",
        backend_targets=("postgres",),
        sql_root=ontology_root,
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=env_id, entries=[entry]),
    )

    with pytest.raises(DBBootPlanError, match="package_kind=state backend_target=sqlite"):
        _ = build_local_plugin_sqlite_boot_plan_from_registry(
            registry_path=registry_path,
            environment_id=env_id,
        )
