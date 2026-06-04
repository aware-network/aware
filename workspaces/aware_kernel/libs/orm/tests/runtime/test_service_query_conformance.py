from __future__ import annotations

import os
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)
from aware_orm.filters import (
    EqFilter,
    GteFilter,
    GtFilter,
    InFilter,
    IsNullFilter,
    LikeFilter,
    RelationPathFilter,
    SortFilter,
    SortOrder,
)
from aware_orm.query_spec import QueryOrder, QueryPage, QuerySpec, and_, or_
from aware_orm.runtime.relationship_strategies import (
    RelationshipMetadata,
    clear_relationship_metadata,
    register_relationship_metadata,
)
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    clear_sql_metadata_registry,
    register_sql_metadata,
)
from aware_orm.session.backends import SqlitePersistenceConfig
from aware_orm.session.session import Session
from aware_orm.sql_generator import SQLGenerator
from aware_orm.testing import db_test_database


ORDER_FQN = "tests.service_query.Order"
PRODUCT_FQN = "tests.service_query.Product"
SCHEMA = "service"


@dataclass(frozen=True)
class QueryCase:
    name: str
    filters: Sequence[Any]
    expected_ids: tuple[str, ...]
    limit: int | None = None
    offset: int | None = None


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _orders_metadata() -> SQLRuntimeMetadata:
    return SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema=SCHEMA,
        table_name="orders",
        column_by_attribute={
            "id": "id",
            "status": "status",
            "total": "total",
            "customer_id": "customer_id",
            "note": "note",
        },
        persisted_attributes=frozenset({"id", "status", "total", "customer_id", "note"}),
        fk_owner_by_attribute={"products": "source"},
        fk_columns_by_attribute={
            "products": (
                {
                    "owner": "source",
                    "table_schema": SCHEMA,
                    "table_name": "orders",
                    "column_name": "id",
                },
                {
                    "owner": "join",
                    "table_schema": SCHEMA,
                    "table_name": "order_products",
                    "column_name": "product_id",
                },
            )
        },
        join_chain_by_attribute={
            "products": (
                {
                    "ordinal": 0,
                    "table_hint": "order_products",
                    "from": {
                        "table_schema": SCHEMA,
                        "table_name": "orders",
                        "column_name": "id",
                    },
                    "to": {
                        "table_schema": SCHEMA,
                        "table_name": "order_products",
                        "column_name": "order_id",
                    },
                },
                {
                    "ordinal": 1,
                    "table_hint": None,
                    "from": {
                        "table_schema": SCHEMA,
                        "table_name": "order_products",
                        "column_name": "product_id",
                    },
                    "to": {
                        "table_schema": SCHEMA,
                        "table_name": "products",
                        "column_name": "id",
                    },
                },
            )
        },
    )


def _products_metadata() -> SQLRuntimeMetadata:
    return SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema=SCHEMA,
        table_name="products",
        column_by_attribute={"id": "id", "sku": "sku", "category": "category"},
        persisted_attributes=frozenset({"id", "sku", "category"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )


def _install_metadata() -> SQLRuntimeMetadata:
    clear_sql_metadata_registry()
    clear_relationship_metadata()

    orders_metadata = _orders_metadata()
    products_metadata = _products_metadata()
    register_sql_metadata(orders_metadata, class_fqn=ORDER_FQN)
    register_sql_metadata(products_metadata, class_fqn=PRODUCT_FQN)
    register_relationship_metadata(
        RelationshipMetadata(
            relationship_id=uuid4(),
            source_class_fqn=ORDER_FQN,
            target_class_fqn=PRODUCT_FQN,
            loading_strategy="lazy",
            source_attribute="products",
            target_attribute="id",
            relationship_type="MANY_TO_MANY",
            fk_columns=orders_metadata.fk_columns_by_attribute["products"],
            join_chain=orders_metadata.join_chain_by_attribute["products"],
        )
    )
    return orders_metadata


def _query_cases() -> tuple[QueryCase, ...]:
    return (
        QueryCase(
            name="equality",
            filters=[EqFilter(column="status", value="active"), SortFilter(column="id", order=SortOrder.ASC)],
            expected_ids=("o1", "o3"),
        ),
        QueryCase(
            name="range",
            filters=[GtFilter(column="total", value=100), SortFilter(column="total", order=SortOrder.ASC)],
            expected_ids=("o1", "o4"),
        ),
        QueryCase(
            name="like",
            filters=[LikeFilter(column="note", pattern="%gift%")],
            expected_ids=("o3",),
        ),
        QueryCase(
            name="in_and_gte",
            filters=[
                InFilter(column="status", values=["active", "pending"]),
                GteFilter(column="total", value=50),
                SortFilter(column="id", order=SortOrder.ASC),
            ],
            expected_ids=("o1", "o2"),
        ),
        QueryCase(
            name="is_null",
            filters=[IsNullFilter(column="note"), SortFilter(column="id", order=SortOrder.ASC)],
            expected_ids=("o2", "o4"),
        ),
        QueryCase(
            name="pagination",
            filters=[SortFilter(column="total", order=SortOrder.DESC)],
            expected_ids=("o1", "o2"),
            limit=2,
            offset=1,
        ),
        QueryCase(
            name="many_to_many_relation_path",
            filters=[
                RelationPathFilter(path="products", field="sku", operator="eq", value="ABC123"),
                SortFilter(column="id", order=SortOrder.ASC),
            ],
            expected_ids=("o1", "o3"),
        ),
    )


async def _assert_query_cases(
    *,
    execute: Callable[[str, tuple[Any, ...]], Awaitable[list[dict[str, Any]]]],
) -> None:
    metadata = _install_metadata()
    for case in _query_cases():
        sql, params = SQLGenerator.generate_select_many(
            sql_metadata=metadata,
            filters=list(case.filters),
            limit=case.limit,
            offset=case.offset,
            source_class_fqn=ORDER_FQN,
        )
        rows = await execute(sql, params)
        assert tuple(str(row["id"]) for row in rows) == case.expected_ids, case.name

    count_sql, count_params = SQLGenerator.generate_count_query(
        sql_metadata=metadata,
        filters=[RelationPathFilter(path="products", field="sku", operator="eq", value="ABC123")],
        source_class_fqn=ORDER_FQN,
    )
    count_rows = await execute(count_sql, count_params)
    assert int(count_rows[0]["count"]) == 2

    query_spec = QuerySpec(
        where=and_(
            or_(
                EqFilter(column="status", value="active"),
                EqFilter(column="status", value="pending"),
            ),
            GteFilter(column="total", value=50),
        ),
        order_by=(QueryOrder(column="id", direction=SortOrder.ASC),),
        page=QueryPage(limit=10),
    )
    spec_sql, spec_params = SQLGenerator.generate_select_for_spec(
        sql_metadata=metadata,
        query_spec=query_spec,
        source_class_fqn=ORDER_FQN,
    )
    spec_rows = await execute(spec_sql, spec_params)
    assert tuple(str(row["id"]) for row in spec_rows) == ("o1", "o2")


def _sqlite_registry(tmp_path: Path, *, environment_id) -> Path:
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
        schema_dir / "products.sql",
        """
CREATE TABLE products (
  id TEXT PRIMARY KEY NOT NULL,
  sku TEXT NOT NULL,
  category TEXT NOT NULL
);
""".strip()
        + "\n",
    )
    _write(
        schema_dir / "orders.sql",
        """
CREATE TABLE orders (
  id TEXT PRIMARY KEY NOT NULL,
  status TEXT NOT NULL,
  total INTEGER NOT NULL,
  customer_id TEXT NOT NULL,
  note TEXT
);
""".strip()
        + "\n",
    )
    _write(
        schema_dir / "order_products.sql",
        """
CREATE TABLE order_products (
  order_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  PRIMARY KEY (order_id, product_id)
);
""".strip()
        + "\n",
    )

    registry_path = tmp_path / "runtime" / "db.schema.registry.json"
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=db_root,
        source_label="service-query-conformance",
        relative_to=registry_path.parent,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[entry]),
    )
    return registry_path


async def _seed_sqlite(session: Session) -> None:
    for table, values in (
        ("customers", ("c1", "east")),
        ("customers", ("c2", "west")),
    ):
        session.add_insert(f"INSERT INTO {SCHEMA}.{table}(id, region) VALUES($1, $2)", values)
    for values in (("p1", "ABC123", "book"), ("p2", "DEF456", "tool")):
        session.add_insert(f"INSERT INTO {SCHEMA}.products(id, sku, category) VALUES($1, $2, $3)", values)
    for values in (
        ("o1", "active", 150, "c1", "priority"),
        ("o2", "pending", 80, "c1", None),
        ("o3", "active", 40, "c2", "gift"),
        ("o4", "archived", 220, "c2", None),
    ):
        session.add_insert(
            f"INSERT INTO {SCHEMA}.orders(id, status, total, customer_id, note) VALUES($1, $2, $3, $4, $5)",
            values,
        )
    for values in (("o1", "p1"), ("o1", "p2"), ("o2", "p2"), ("o3", "p1"), ("o4", "p2")):
        session.add_insert(f"INSERT INTO {SCHEMA}.order_products(order_id, product_id) VALUES($1, $2)", values)
    await session.commit()


@pytest.mark.asyncio
async def test_service_query_conformance_sqlite(tmp_path: Path) -> None:
    environment_id = uuid4()
    registry_path = _sqlite_registry(tmp_path, environment_id=environment_id)
    session = Session(
        skip_db=False,
        backend_name="sqlite",
        sqlite_backend_config=SqlitePersistenceConfig(
            database_path=":memory:",
            registry_path=registry_path,
            environment_id=environment_id,
        ),
    )
    await _seed_sqlite(session)

    async def _execute(sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        return await session.execute_query(sql, *params)

    await _assert_query_cases(execute=_execute)


async def _create_postgres_schema(conn) -> None:  # type: ignore[no-untyped-def]
    await conn.execute(f"CREATE SCHEMA {SCHEMA};")
    await conn.execute(f"CREATE TABLE {SCHEMA}.customers (id TEXT PRIMARY KEY NOT NULL, region TEXT NOT NULL);")
    await conn.execute(
        f"CREATE TABLE {SCHEMA}.products (id TEXT PRIMARY KEY NOT NULL, sku TEXT NOT NULL, category TEXT NOT NULL);"
    )
    await conn.execute(
        f"""
CREATE TABLE {SCHEMA}.orders (
  id TEXT PRIMARY KEY NOT NULL,
  status TEXT NOT NULL,
  total INTEGER NOT NULL,
  customer_id TEXT NOT NULL,
  note TEXT
);
""".strip()
    )
    await conn.execute(
        f"""
CREATE TABLE {SCHEMA}.order_products (
  order_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  PRIMARY KEY (order_id, product_id)
);
""".strip()
    )


async def _seed_postgres(conn) -> None:  # type: ignore[no-untyped-def]
    await conn.executemany(
        f"INSERT INTO {SCHEMA}.customers(id, region) VALUES($1, $2)",
        [("c1", "east"), ("c2", "west")],
    )
    await conn.executemany(
        f"INSERT INTO {SCHEMA}.products(id, sku, category) VALUES($1, $2, $3)",
        [("p1", "ABC123", "book"), ("p2", "DEF456", "tool")],
    )
    await conn.executemany(
        f"INSERT INTO {SCHEMA}.orders(id, status, total, customer_id, note) VALUES($1, $2, $3, $4, $5)",
        [
            ("o1", "active", 150, "c1", "priority"),
            ("o2", "pending", 80, "c1", None),
            ("o3", "active", 40, "c2", "gift"),
            ("o4", "archived", 220, "c2", None),
        ],
    )
    await conn.executemany(
        f"INSERT INTO {SCHEMA}.order_products(order_id, product_id) VALUES($1, $2)",
        [("o1", "p1"), ("o1", "p2"), ("o2", "p2"), ("o3", "p1"), ("o4", "p2")],
    )


def _skip_if_db_unavailable() -> str | None:
    if os.getenv("AWARE_DB_TEST_ADMIN_URL") or os.getenv("AWARE_DB_TEST_URL"):
        return None
    return "AWARE_DB_TEST_ADMIN_URL or AWARE_DB_TEST_URL is required for Postgres query conformance."


@pytest.mark.asyncio
@pytest.mark.db
async def test_service_query_conformance_postgres() -> None:
    reason = _skip_if_db_unavailable()
    if reason:
        pytest.skip(reason)

    asyncpg = pytest.importorskip("asyncpg")
    async with db_test_database() as db_url:
        conn = await asyncpg.connect(db_url)
        try:
            await _create_postgres_schema(conn)
            await _seed_postgres(conn)

            async def _execute(sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
                return [dict(row) for row in await conn.fetch(sql, *params)]

            await _assert_query_cases(execute=_execute)
        finally:
            await conn.close()
