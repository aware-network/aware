from __future__ import annotations

from uuid import uuid4

import pytest

from aware_orm.filters import EqFilter, GteFilter, IsNullFilter, RelationPathFilter, SortFilter, SortOrder
from aware_orm.query_spec import QueryOrder, QueryPage, QuerySpec, and_, or_
from aware_orm.runtime.relationship_strategies import (
    RelationshipMetadata,
    clear_relationship_metadata,
    register_relationship_metadata,
)
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata, clear_sql_metadata_registry, register_sql_metadata
from aware_orm.sql_generator import SQLGenerator


def _orders_metadata() -> SQLRuntimeMetadata:
    return SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="orders",
        column_by_attribute={
            "id": "id",
            "status": "status",
            "total": "total",
            "customer_id": "customer_id",
            "note": "note",
        },
        persisted_attributes=frozenset({"id", "status", "total", "customer_id", "note"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )


def test_query_spec_compiles_boolean_grouping_sorting_and_pagination() -> None:
    metadata = _orders_metadata()
    spec = QuerySpec(
        where=and_(
            or_(
                EqFilter(column="status", value="active"),
                EqFilter(column="status", value="pending"),
            ),
            GteFilter(column="total", value=50),
            IsNullFilter(column="note", is_null=False),
        ),
        order_by=(QueryOrder(column="id", direction=SortOrder.ASC),),
        page=QueryPage(limit=10, offset=5),
    )

    sql, params = SQLGenerator.generate_select_for_spec(
        sql_metadata=metadata,
        query_spec=spec,
        source_class_fqn="tests.Order",
    )

    assert "WHERE ((status = $1 OR status = $2) AND total >= $3 AND note IS NOT NULL)" in sql
    assert "ORDER BY id ASC LIMIT $4 OFFSET $5" in sql
    assert params == ("active", "pending", 50, 10, 5)


def test_query_spec_from_legacy_filters_preserves_flat_filter_semantics() -> None:
    metadata = _orders_metadata()
    spec = QuerySpec.from_filters(
        [
            EqFilter(column="status", value="active"),
            SortFilter(column="id", order=SortOrder.DESC),
        ],
        limit=2,
    )

    sql, params = SQLGenerator.generate_select_for_spec(
        sql_metadata=metadata,
        query_spec=spec,
        source_class_fqn="tests.Order",
    )

    assert sql == "SELECT * FROM public.orders WHERE status = $1 ORDER BY id DESC LIMIT $2"
    assert params == ("active", 2)


def test_query_spec_count_uses_where_and_ignores_ordering_and_pagination() -> None:
    metadata = _orders_metadata()
    spec = QuerySpec(
        where=or_(
            EqFilter(column="status", value="active"),
            EqFilter(column="status", value="pending"),
        ),
        order_by=(QueryOrder(column="id", direction=SortOrder.DESC),),
        page=QueryPage(limit=1, offset=1),
    )

    sql, params = SQLGenerator.generate_count_for_spec(
        sql_metadata=metadata,
        query_spec=spec,
        source_class_fqn="tests.Order",
    )

    assert sql == "SELECT COUNT(*) as count FROM public.orders WHERE (status = $1 OR status = $2)"
    assert params == ("active", "pending")


def test_query_spec_rejects_columns_outside_sql_metadata() -> None:
    metadata = _orders_metadata()
    spec = QuerySpec(where=EqFilter(column="status; DROP TABLE orders", value="active"))

    with pytest.raises(ValueError, match="not declared in SQL metadata"):
        SQLGenerator.generate_select_for_spec(
            sql_metadata=metadata,
            query_spec=spec,
            source_class_fqn="tests.Order",
        )


def test_query_spec_relation_path_unsupported_operator_fails_explicitly() -> None:
    clear_relationship_metadata()
    clear_sql_metadata_registry()

    metadata = _orders_metadata()
    register_sql_metadata(metadata, class_fqn="tests.Order")
    register_relationship_metadata(
        RelationshipMetadata(
            relationship_id=uuid4(),
            source_class_fqn="tests.Order",
            target_class_fqn="tests.Customer",
            loading_strategy="lazy",
            source_attribute="customer",
            target_attribute="id",
            relationship_type="MANY_TO_ONE",
            fk_columns=(
                {
                    "owner": "source",
                    "table_schema": "public",
                    "table_name": "orders",
                    "column_name": "customer_id",
                },
            ),
            join_chain=(),
        )
    )
    spec = QuerySpec(
        where=RelationPathFilter(path="customer", field="id", operator="like", value="%east%"),
    )

    with pytest.raises(ValueError, match="operator not supported"):
        SQLGenerator.generate_select_for_spec(
            sql_metadata=metadata,
            query_spec=spec,
            source_class_fqn="tests.Order",
        )
