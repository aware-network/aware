from __future__ import annotations

from pathlib import Path

import pytest

from aware_orm.runtime.db_boot import (
    DBBootPlanError,
    build_sql_boot_plan,
    build_sql_boot_plan_multi,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_sql_boot_plan_orders_types_then_tables(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"

    # Schema "a" defines the enum + base table.
    _write(
        sql_root / "domain" / "a" / "status.sql",
        "CREATE TYPE status AS ENUM ('x');",
    )
    _write(
        sql_root / "domain" / "a" / "t1.sql",
        "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL);",
    )

    # Schema "b" defines a dependent table referencing t1 + using the enum.
    _write(
        sql_root / "domain" / "b" / "t2.sql",
        """
CREATE TABLE t2 (
  id UUID PRIMARY KEY NOT NULL,
  t1_id UUID REFERENCES t1(id),
  status status NOT NULL
);
""".strip(),
    )

    plan = build_sql_boot_plan(sql_root=sql_root)
    assert plan.schemas == ("a", "b")
    assert [s.kind for s in plan.steps[:1]] == ["type"]
    assert plan.steps[0].path.name == "status.sql"

    # t1 must precede t2 because t2 REFERENCES t1.
    table_steps = [s for s in plan.steps if s.kind == "table"]
    assert [s.path.name for s in table_steps] == ["t1.sql", "t2.sql"]


def test_build_sql_boot_plan_allows_cyclic_foreign_keys(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "d" / "a" / "t1.sql",
        "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL, t2_id UUID REFERENCES t2(id));",
    )
    _write(
        sql_root / "d" / "b" / "t2.sql",
        "CREATE TABLE t2 (id UUID PRIMARY KEY NOT NULL, t1_id UUID REFERENCES t1(id));",
    )

    plan = build_sql_boot_plan(sql_root=sql_root)
    assert [s.kind for s in plan.steps] == ["table", "table"]


def test_build_sql_boot_plan_rejects_duplicate_table_names(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "d" / "a" / "t.sql",
        "CREATE TABLE dup (id UUID PRIMARY KEY NOT NULL);",
    )
    _write(
        sql_root / "d" / "b" / "t.sql",
        "CREATE TABLE dup (id UUID PRIMARY KEY NOT NULL);",
    )

    with pytest.raises(DBBootPlanError):
        build_sql_boot_plan(sql_root=sql_root)


def test_build_sql_boot_plan_accepts_generated_multi_table_files(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "hub" / "hub_artifact.sql",
        """
CREATE TABLE hub_artifact (
  id UUID PRIMARY KEY NOT NULL
);

CREATE TABLE hub_artifact_revision (
  id UUID PRIMARY KEY NOT NULL,
  hub_artifact_id UUID REFERENCES hub_artifact(id)
);
""".strip(),
    )

    plan = build_sql_boot_plan(sql_root=sql_root)

    table_steps = [step for step in plan.steps if step.kind == "table"]
    assert len(table_steps) == 1
    assert table_steps[0].path.name == "hub_artifact.sql"


def test_build_sql_boot_plan_accepts_generated_mixed_type_table_files(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "workspace" / "workspace.sql",
        "CREATE TABLE workspace (id UUID PRIMARY KEY NOT NULL);",
    )
    _write(
        sql_root / "workspace" / "workspace_build.sql",
        """
CREATE TYPE workspace_build_lifecycle AS ENUM ('idle', 'running');

CREATE TABLE workspace_build (
  id UUID PRIMARY KEY NOT NULL,
  workspace_id UUID REFERENCES workspace(id),
  status workspace_build_lifecycle NOT NULL
);
""".strip(),
    )

    plan = build_sql_boot_plan(sql_root=sql_root)

    type_steps = [step for step in plan.steps if step.kind == "type"]
    table_steps = [step for step in plan.steps if step.kind == "table"]
    assert [step.path.name for step in type_steps] == ["workspace_build.sql"]
    assert [step.path.name for step in table_steps] == [
        "workspace.sql",
        "workspace_build.sql",
    ]


def test_build_sql_boot_plan_accepts_schema_only_layout(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"
    _write(sql_root / "a" / "t1.sql", "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL);")
    _write(
        sql_root / "b" / "t2.sql",
        "CREATE TABLE t2 (id UUID PRIMARY KEY NOT NULL, t1_id UUID REFERENCES t1(id));",
    )

    plan = build_sql_boot_plan(sql_root=sql_root)
    assert plan.schemas == ("a", "b")


def test_build_sql_boot_plan_accepts_nested_domain_layout(tmp_path: Path) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "domain" / "a" / "nested" / "t1.sql",
        "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL);",
    )

    plan = build_sql_boot_plan(sql_root=sql_root)
    assert plan.schemas == ("a",)


def test_build_sql_boot_plan_rejects_duplicate_types_when_file_defines_multiple_types(
    tmp_path: Path,
) -> None:
    sql_root = tmp_path / "sql"
    _write(
        sql_root / "a" / "types.sql",
        "CREATE TYPE t1 AS ENUM ('x');\nCREATE TYPE dup AS ENUM ('y');\n",
    )
    _write(
        sql_root / "b" / "dup.sql",
        "CREATE TYPE dup AS ENUM ('z');\n",
    )

    with pytest.raises(DBBootPlanError):
        build_sql_boot_plan(sql_root=sql_root)


def test_build_sql_boot_plan_multi_unions_roots(tmp_path: Path) -> None:
    r1 = tmp_path / "sql1"
    r2 = tmp_path / "sql2"
    _write(r1 / "a" / "t1.sql", "CREATE TABLE t1 (id UUID PRIMARY KEY NOT NULL);")
    _write(
        r2 / "b" / "t2.sql",
        "CREATE TABLE t2 (id UUID PRIMARY KEY NOT NULL, t1_id UUID REFERENCES t1(id));",
    )

    plan = build_sql_boot_plan_multi(sql_roots=(r1, r2))
    assert plan.schemas == ("a", "b")
    assert any(step.path.name == "t1.sql" for step in plan.steps)
    assert any(step.path.name == "t2.sql" for step in plan.steps)
