from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from aware_orm.db import DBBootExecutionError
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)
from aware_orm.filters import EqFilter, GteFilter, SortOrder
from aware_orm.models.query_mixin import QueryMixin
from aware_orm.query_spec import QueryOrder, QueryPage, QuerySpec, and_, or_
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    clear_sql_metadata_registry,
    register_sql_metadata,
)
from aware_orm.session.backends import SqlitePersistenceConfig
from aware_orm.session.session import Session
from aware_orm.sql_generator import SQLGenerator


ORDER_FQN = "tests.service_state.Order"
SCHEMA = "commerce"


class ServiceOrder(QueryMixin):
    pass


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_service_state_registry(*, tmp_path: Path, environment_id: UUID) -> tuple[Path, Path, str]:
    db_root = tmp_path / "sqlite"
    schema_dir = db_root / SCHEMA
    _write(
        schema_dir / "customers.sql",
        """
CREATE TABLE customers (
  id TEXT PRIMARY KEY NOT NULL,
  region TEXT NOT NULL
);
""".strip()
        + "\n",
    )
    _write(
        schema_dir / "orders.sql",
        """
CREATE TABLE orders (
  id TEXT PRIMARY KEY NOT NULL,
  customer_id TEXT NOT NULL,
  status TEXT NOT NULL,
  total INTEGER NOT NULL,
  branch_id TEXT NOT NULL,
  note TEXT
);
""".strip()
        + "\n",
    )
    _write(
        schema_dir / "order_events.sql",
        """
CREATE TABLE order_events (
  id TEXT PRIMARY KEY NOT NULL,
  order_id TEXT NOT NULL,
  event_type TEXT NOT NULL
);
""".strip()
        + "\n",
    )

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=db_root,
        source_label="commerce-service-state",
        relative_to=registry_path.parent,
    )
    registry_hash = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[entry]),
    )
    return registry_path, db_root, registry_hash


def _orders_metadata() -> SQLRuntimeMetadata:
    return SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema=SCHEMA,
        table_name="orders",
        column_by_attribute={
            "id": "id",
            "customer_id": "customer_id",
            "status": "status",
            "total": "total",
            "branch_id": "branch_id",
            "note": "note",
        },
        persisted_attributes=frozenset({"id", "customer_id", "status", "total", "branch_id", "note"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )


def _install_metadata() -> SQLRuntimeMetadata:
    clear_sql_metadata_registry()
    metadata = _orders_metadata()
    register_sql_metadata(metadata, class_fqn=ORDER_FQN)
    return metadata


def _service_session(*, database_path: Path, registry_path: Path, environment_id: UUID) -> Session:
    return Session(
        skip_db=False,
        backend_name="sqlite",
        sqlite_backend_config=SqlitePersistenceConfig(
            database_path=database_path,
            registry_path=registry_path,
            environment_id=environment_id,
        ),
    )


async def _seed_service_state(session: Session) -> None:
    for values in (("c1", "east"), ("c2", "west")):
        session.add_insert(f"INSERT INTO {SCHEMA}.customers(id, region) VALUES($1, $2)", values)

    for values in (
        ("o1", "c1", "open", 75, "main", "rush"),
        ("o2", "c1", "pending", 120, "main", None),
        ("o3", "c2", "open", 40, "main", "small"),
        ("o4", "c2", "closed", 200, "archive", "gift"),
    ):
        session.add_insert(
            f"""
INSERT INTO {SCHEMA}.orders(id, customer_id, status, total, branch_id, note)
VALUES($1, $2, $3, $4, $5, $6)
""".strip(),
            values,
        )

    for values in (("evt-1", "o1", "created"), ("evt-2", "o2", "paid"), ("evt-3", "o4", "archived")):
        session.add_insert(
            f"INSERT INTO {SCHEMA}.order_events(id, order_id, event_type) VALUES($1, $2, $3)",
            values,
        )
    await session.commit()


async def _query_receipt(
    *,
    session: Session,
    metadata: SQLRuntimeMetadata,
    registry_hash: str,
    environment_id: UUID,
) -> dict[str, Any]:
    query_spec = QuerySpec(
        where=and_(
            or_(
                EqFilter(column="status", value="open"),
                EqFilter(column="status", value="pending"),
            ),
            GteFilter(column="total", value=50),
            EqFilter(column="branch_id", value="main"),
        ),
        order_by=(QueryOrder(column="total", direction=SortOrder.DESC),),
        page=QueryPage(limit=2),
    )
    sql, params = SQLGenerator.generate_select_for_spec(
        sql_metadata=metadata,
        query_spec=query_spec,
        source_class_fqn=ORDER_FQN,
    )
    rows = await session.execute_query(sql, *params)

    count_sql, count_params = SQLGenerator.generate_count_for_spec(
        sql_metadata=metadata,
        query_spec=QuerySpec(where=EqFilter(column="branch_id", value="main")),
        source_class_fqn=ORDER_FQN,
    )
    count_rows = await session.execute_query(count_sql, *count_params)

    table_rows = await session.execute_query(
        "SELECT name FROM sqlite_master WHERE type = $1 ORDER BY name",
        "table",
    )
    marker_rows = await session.execute_query(
        "SELECT environment_id, ocg_hash FROM aware_bootstrap_marker WHERE environment_id = $1",
        environment_id,
    )

    return {
        "environment_id": str(environment_id),
        "installed_tables": tuple(row["name"] for row in table_rows),
        "marker_environment_id": marker_rows[0]["environment_id"],
        "marker_ocg_hash": marker_rows[0]["ocg_hash"],
        "expected_ocg_hash": registry_hash,
        "query_ids": tuple(row["id"] for row in rows),
        "branch_main_count": int(count_rows[0]["count"]),
    }


@pytest.mark.asyncio
async def test_service_state_e2e_installs_queries_and_reports_health_and_drift(tmp_path: Path) -> None:
    environment_id = uuid4()
    registry_path, db_root, registry_hash = _write_service_state_registry(
        tmp_path=tmp_path,
        environment_id=environment_id,
    )
    database_path = tmp_path / "state" / "commerce.sqlite"
    metadata = _install_metadata()
    session = _service_session(
        database_path=database_path,
        registry_path=registry_path,
        environment_id=environment_id,
    )

    await _seed_service_state(session)
    receipt = await _query_receipt(
        session=session,
        metadata=metadata,
        registry_hash=registry_hash,
        environment_id=environment_id,
    )

    assert set(receipt["installed_tables"]) >= {
        "aware_bootstrap_marker",
        "customers",
        "order_events",
        "orders",
    }
    assert receipt["marker_environment_id"] == receipt["environment_id"]
    assert receipt["marker_ocg_hash"] == receipt["expected_ocg_hash"]
    assert receipt["query_ids"] == ("o2", "o1")
    assert receipt["branch_main_count"] == 3

    assert ServiceOrder._graph_queries_supported_for_session(session) is False
    with pytest.raises(RuntimeError, match="GraphSQL eager loading is not supported for backend 'sqlite'"):
        ServiceOrder._raise_if_graph_queries_unsupported(session)

    _write(
        db_root / SCHEMA / "orders.sql",
        """
CREATE TABLE orders (
  id TEXT PRIMARY KEY NOT NULL,
  customer_id TEXT NOT NULL,
  status TEXT NOT NULL,
  total INTEGER NOT NULL,
  branch_id TEXT NOT NULL,
  priority TEXT,
  note TEXT
);
""".strip()
        + "\n",
    )
    drift_entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=db_root,
        source_label="commerce-service-state",
        relative_to=registry_path.parent,
    )
    drift_hash = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[drift_entry]),
    )
    assert drift_hash != registry_hash

    drift_session = _service_session(
        database_path=database_path,
        registry_path=registry_path,
        environment_id=environment_id,
    )
    with pytest.raises(DBBootExecutionError, match="different ocg_hash") as exc_info:
        _ = await drift_session.execute_query(f"SELECT * FROM {SCHEMA}.orders")

    drift_receipt = {
        "environment_id": str(environment_id),
        "drift_detected": True,
        "previous_ocg_hash": registry_hash,
        "requested_ocg_hash": drift_hash,
        "error": str(exc_info.value),
    }
    assert drift_receipt["drift_detected"] is True
    assert drift_receipt["previous_ocg_hash"] in drift_receipt["error"]
    assert drift_receipt["requested_ocg_hash"] in drift_receipt["error"]
