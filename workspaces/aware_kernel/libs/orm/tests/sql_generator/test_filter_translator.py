from __future__ import annotations

from uuid import uuid4

from aware_orm.filters import EqFilter, InFilter, RelationPathFilter
from aware_orm.sql_generator import SQLGenerator
from aware_orm.runtime.sql_metadata import (
    SQLRuntimeMetadata,
    register_sql_metadata,
    clear_sql_metadata_registry,
)
from aware_orm.runtime.relationship_strategies import (
    RelationshipMetadata,
    register_relationship_metadata,
    clear_relationship_metadata,
)


def test_generate_select_many_uses_sql_metadata_columns() -> None:
    metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="sample",
        column_by_attribute={"displayname": "display_name", "status": "status"},
        persisted_attributes=frozenset({"displayname", "status"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )

    sql, params = SQLGenerator.generate_select_many(
        sql_metadata=metadata,
        filters=[EqFilter(column="displayname", value="Alice")],
        limit=10,
        offset=5,
        source_class_fqn="tests.Stub",
    )

    assert "display_name" in sql
    assert sql.strip().startswith("SELECT * FROM public.sample WHERE")
    assert params == ("Alice", 10, 5)


def test_generate_count_query_uses_sql_metadata_columns() -> None:
    metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="sample",
        column_by_attribute={"status": "status_code"},
        persisted_attributes=frozenset({"status"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )

    sql, params = SQLGenerator.generate_count_query(
        sql_metadata=metadata,
        filters=[InFilter(column="status", values=["active", "pending"])],
        source_class_fqn="tests.Stub",
    )

    assert "status_code" in sql
    assert params == ("active", "pending")


def test_relation_path_filter_maps_to_foreign_key() -> None:
    clear_relationship_metadata()
    clear_sql_metadata_registry()

    metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="orders",
        column_by_attribute={"customer_id": "customer_id"},
        persisted_attributes=frozenset({"customer_id"}),
        fk_owner_by_attribute={"customer_id": "source"},
        fk_columns_by_attribute={
            "customer_id": (
                {
                    "owner": "source",
                    "table_schema": "public",
                    "table_name": "orders",
                    "column_name": "customer_id",
                },
            )
        },
        join_chain_by_attribute={
            "customer_id": (
                {
                    "ordinal": 0,
                    "table_hint": None,
                    "from": {
                        "table_schema": "public",
                        "table_name": "orders",
                        "column_name": "customer_id",
                    },
                    "to": {
                        "table_schema": "public",
                        "table_name": "customers",
                        "column_name": "id",
                    },
                },
            )
        },
    )
    register_relationship_metadata(
        RelationshipMetadata(
            relationship_id=uuid4(),
            source_class_fqn="tests.Order",
            target_class_fqn="tests.Customer",
            loading_strategy="lazy",
            source_attribute="customer_id",
            target_attribute="id",
            relationship_type="ONE_TO_MANY",
            fk_columns=metadata.fk_columns_by_attribute.get("customer_id", ()),
            join_chain=(),
        )
    )

    register_sql_metadata(metadata, class_fqn="tests.Order")

    relation_filter = RelationPathFilter(path="customer_id", field="id", operator="eq", value="abc")

    sql, params = SQLGenerator.generate_select_many(
        sql_metadata=metadata,
        filters=[relation_filter],
        limit=None,
        offset=None,
        source_class_fqn="tests.Order",
    )

    assert "customer_id" in sql
    assert params == ("abc",)


def test_relation_path_filter_two_hops() -> None:
    clear_relationship_metadata()
    clear_sql_metadata_registry()

    order_metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="orders",
        column_by_attribute={"customer_id": "customer_id"},
        persisted_attributes=frozenset({"customer_id"}),
        fk_owner_by_attribute={"customer_id": "source"},
        fk_columns_by_attribute={
            "customer_id": (
                {
                    "owner": "source",
                    "table_schema": "public",
                    "table_name": "orders",
                    "column_name": "customer_id",
                },
            )
        },
        join_chain_by_attribute={
            "customer_id": (
                {
                    "ordinal": 0,
                    "table_hint": None,
                    "from": {
                        "table_schema": "public",
                        "table_name": "orders",
                        "column_name": "customer_id",
                    },
                    "to": {
                        "table_schema": "public",
                        "table_name": "customers",
                        "column_name": "id",
                    },
                },
            )
        },
    )
    customer_metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="customers",
        column_by_attribute={"identity_id": "identity_id"},
        persisted_attributes=frozenset({"identity_id"}),
        fk_owner_by_attribute={"identity_id": "source"},
        fk_columns_by_attribute={
            "identity_id": (
                {
                    "owner": "source",
                    "table_schema": "public",
                    "table_name": "customers",
                    "column_name": "identity_id",
                },
            )
        },
        join_chain_by_attribute={
            "identity_id": (
                {
                    "ordinal": 0,
                    "table_hint": None,
                    "from": {
                        "table_schema": "public",
                        "table_name": "customers",
                        "column_name": "identity_id",
                    },
                    "to": {
                        "table_schema": "public",
                        "table_name": "identities",
                        "column_name": "id",
                    },
                },
            )
        },
    )
    identity_metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="identities",
        column_by_attribute={"id": "id"},
        persisted_attributes=frozenset({"id"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )

    register_sql_metadata(order_metadata, class_fqn="tests.Order")
    register_sql_metadata(customer_metadata, class_fqn="tests.Customer")
    register_sql_metadata(identity_metadata, class_fqn="tests.Identity")

    register_relationship_metadata(
        RelationshipMetadata(
            relationship_id=uuid4(),
            source_class_fqn="tests.Order",
            target_class_fqn="tests.Customer",
            loading_strategy="lazy",
            source_attribute="customer",
            target_attribute="id",
            relationship_type="ONE_TO_MANY",
            fk_columns=order_metadata.fk_columns_by_attribute.get("customer_id", ()),
            join_chain=order_metadata.join_chain_by_attribute.get("customer_id", ()),
        )
    )

    register_relationship_metadata(
        RelationshipMetadata(
            relationship_id=uuid4(),
            source_class_fqn="tests.Customer",
            target_class_fqn="tests.Identity",
            loading_strategy="lazy",
            source_attribute="identity",
            target_attribute="id",
            relationship_type="MANY_TO_ONE",
            fk_columns=customer_metadata.fk_columns_by_attribute.get("identity_id", ()),
            join_chain=customer_metadata.join_chain_by_attribute.get("identity_id", ()),
        )
    )

    relation_filter = RelationPathFilter(path="customer.identity", field="id", operator="eq", value="abc")

    sql, params = SQLGenerator.generate_select_many(
        sql_metadata=order_metadata,
        filters=[relation_filter],
        limit=None,
        offset=None,
        source_class_fqn="tests.Order",
    )

    assert "EXISTS" in sql
    assert "rel1" in sql
    assert params == ("abc",)


def test_relation_path_filter_many_to_many_join_table() -> None:
    clear_relationship_metadata()
    clear_sql_metadata_registry()

    order_metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="orders",
        column_by_attribute={"id": "id"},
        persisted_attributes=frozenset({"id"}),
        fk_owner_by_attribute={"products": "source"},
        fk_columns_by_attribute={
            "products": (
                {
                    "owner": "source",
                    "table_schema": "public",
                    "table_name": "orders",
                    "column_name": "id",
                },
                {
                    "owner": "join",
                    "table_schema": "public",
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
                        "table_schema": "public",
                        "table_name": "orders",
                        "column_name": "id",
                    },
                    "to": {
                        "table_schema": "public",
                        "table_name": "order_products",
                        "column_name": "order_id",
                    },
                },
                {
                    "ordinal": 1,
                    "table_hint": None,
                    "from": {
                        "table_schema": "public",
                        "table_name": "order_products",
                        "column_name": "product_id",
                    },
                    "to": {
                        "table_schema": "public",
                        "table_name": "products",
                        "column_name": "id",
                    },
                },
            )
        },
    )

    order_item_metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="order_products",
        column_by_attribute={"product_id": "product_id"},
        persisted_attributes=frozenset({"product_id"}),
        fk_owner_by_attribute={"product_id": "source"},
        fk_columns_by_attribute={
            "product_id": (
                {
                    "owner": "source",
                    "table_schema": "public",
                    "table_name": "order_products",
                    "column_name": "product_id",
                },
            )
        },
        join_chain_by_attribute={
            "product_id": (
                {
                    "ordinal": 0,
                    "table_hint": None,
                    "from": {
                        "table_schema": "public",
                        "table_name": "order_products",
                        "column_name": "product_id",
                    },
                    "to": {
                        "table_schema": "public",
                        "table_name": "products",
                        "column_name": "id",
                    },
                },
            )
        },
    )

    product_metadata = SQLRuntimeMetadata(
        class_config_id=uuid4(),
        table_schema="public",
        table_name="products",
        column_by_attribute={"sku": "sku"},
        persisted_attributes=frozenset({"sku"}),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )

    register_sql_metadata(order_metadata, class_fqn="tests.Order")
    register_sql_metadata(order_item_metadata, class_fqn="tests.OrderProduct")
    register_sql_metadata(product_metadata, class_fqn="tests.Product")

    register_relationship_metadata(
        RelationshipMetadata(
            relationship_id=uuid4(),
            source_class_fqn="tests.Order",
            target_class_fqn="tests.Product",
            loading_strategy="lazy",
            source_attribute="products",
            target_attribute="id",
            relationship_type="MANY_TO_MANY",
            fk_columns=order_metadata.fk_columns_by_attribute.get("products", ()),
            join_chain=order_metadata.join_chain_by_attribute.get("products", ()),
        )
    )

    relation_filter = RelationPathFilter(path="products", field="sku", operator="eq", value="ABC123")

    sql, params = SQLGenerator.generate_select_many(
        sql_metadata=order_metadata,
        filters=[relation_filter],
        limit=None,
        offset=None,
        source_class_fqn="tests.Order",
    )

    assert "EXISTS" in sql
    assert "SELECT 1 FROM public.order_products" in sql
    assert "JOIN public.products" in sql
    assert params == ("ABC123",)
