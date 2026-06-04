"""
SQL Generator for automatic SQL statement generation.

This module leverages SQL Runtime Metadata to automatically generate
SQL statements for ORMModel operations without hand-writing SQL.

Enhanced to provide unified SQL generation for both read and write operations.
"""

from __future__ import annotations
from typing import Any
import json
from uuid import UUID

from aware_orm.filters import FilterType
from aware_orm.query_spec import QuerySpec
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata
from aware_orm.sql_generator._filter_translator import _SQLFilterTranslator

from aware_orm._support import logger


class SQLGenerator:
    """
    Generates SQL statements based on SQL Runtime Metadata.

    This class automatically creates INSERT, UPDATE, DELETE, and SELECT statements
    by introspecting the SQL Runtime Metadata for table schema, column names, and types.

    Provides unified SQL generation for all ORM operations:
    - Write operations: INSERT, UPDATE, DELETE, UPSERT
    - Read operations: SELECT by ID, SELECT many with filters, COUNT
    """

    # ==================== Write Operations (existing) ====================

    @staticmethod
    def generate_insert(sql_metadata: SQLRuntimeMetadata, model_data: dict[str, Any]) -> tuple[str, tuple[Any, ...]]:
        """
        Generate an INSERT statement for a model.

        Args:
            sql_metadata: SQLRuntimeMetadata containing table metadata
            model_data: Dictionary of field values from the model

        Returns:
            Tuple of (SQL string, parameters tuple)
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name

        if not model_data:
            raise ValueError(f"No data to insert for {schema}.{table}")

        # Generate column list and parameter placeholders
        columns = list(model_data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = tuple(SQLGenerator._normalize_value(model_data[col]) for col in columns)

        # Build the SQL
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(placeholders)

        sql = f"INSERT INTO {schema}.{table} ({columns_str}) VALUES ({placeholders_str})"
        return sql, values

    @staticmethod
    def generate_update(
        sql_metadata: SQLRuntimeMetadata,
        model_data: dict[str, Any],
        pk_field: str = "id",
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate an UPDATE statement for a model.

        Args:
            sql_metadata: SQLRuntimeMetadata containing table metadata
            model_data: Dictionary of field values from the model
            pk_field: Primary key field name (default: "id")

        Returns:
            Tuple of (SQL string, parameters tuple)
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name

        # Get the primary key value
        pk_value = model_data.get(pk_field)
        if pk_value is None:
            raise ValueError(f"Primary key {pk_field} is required for UPDATE, model data: {model_data}")

        # Filter out None values and the primary key from update data
        if pk_field in model_data:
            model_data.pop(pk_field)  # Don't update the PK

        if not model_data:
            logger.debug(f"No fields to update for {schema}.{table} id={pk_value}")
            # Return a no-op statement
            return (
                f"SELECT 1 WHERE FALSE -- No fields to update for {schema}.{table}",
                (),
            )

        # Generate SET clauses
        set_clauses = []
        values = []
        param_index = 1

        for column, value in model_data.items():
            set_clauses.append(f"{column} = ${param_index}")
            values.append(SQLGenerator._normalize_value(value))
            param_index += 1

        # Add WHERE clause parameter
        values.append(pk_value)
        where_clause = f"{pk_field} = ${param_index}"

        # Build the SQL
        set_clause_str = ", ".join(set_clauses)
        sql = f"UPDATE {schema}.{table} SET {set_clause_str} WHERE {where_clause}"

        logger.debug(f"Generated UPDATE: {sql}")
        logger.debug(f"Parameters: {tuple(values)}")

        return sql, tuple(values)

    @staticmethod
    def generate_upsert(
        sql_metadata: SQLRuntimeMetadata,
        model_data: dict[str, Any],
        pk_field: str = "id",
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate an INSERT ... ON CONFLICT ... DO UPDATE statement (upsert).

        Args:
            sql_metadata: SQLRuntimeMetadata containing table metadata
            model_data: Dictionary of field values from the model
            pk_field: Primary key field name (default: "id")

        Returns:
            Tuple of (SQL string, parameters tuple)
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name

        if not model_data:
            raise ValueError(f"No data to upsert for {schema}.{table}")

        # Generate INSERT part
        columns = list(model_data.keys())
        insert_placeholders = [f"${i+1}" for i in range(len(columns))]
        insert_values = tuple(SQLGenerator._normalize_value(model_data[col]) for col in columns)

        # Generate UPDATE part (exclude PK from SET clause)
        update_columns = [col for col in columns if col != pk_field]
        update_set_clauses = [f"{col} = EXCLUDED.{col}" for col in update_columns]

        # Build the SQL
        columns_str = ", ".join(columns)
        insert_placeholders_str = ", ".join(insert_placeholders)
        update_set_str = ", ".join(update_set_clauses) if update_set_clauses else f"{pk_field} = EXCLUDED.{pk_field}"

        sql = (
            f"INSERT INTO {schema}.{table} ({columns_str}) VALUES ({insert_placeholders_str}) "
            f"ON CONFLICT ({pk_field}) DO UPDATE SET {update_set_str}"
        )

        logger.debug(f"Generated UPSERT: {sql}")
        logger.debug(f"Parameters: {insert_values}")

        return sql, insert_values

    @staticmethod
    def generate_delete(
        sql_metadata: SQLRuntimeMetadata, pk_value: Any, pk_field: str = "id"
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate a DELETE statement for a model.

        Args:
            sql_metadata: SQLRuntimeMetadata containing table metadata
            pk_value: Primary key value to delete
            pk_field: Primary key field name (default: "id")

        Returns:
            Tuple of (SQL string, parameters tuple)
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name

        if pk_value is None:
            raise ValueError(f"Primary key {pk_field} is required for DELETE")

        sql = f"DELETE FROM {schema}.{table} WHERE {pk_field} = $1"
        params = (pk_value,)

        logger.debug(f"Generated DELETE: {sql}")
        logger.debug(f"Parameters: {params}")

        return sql, params

    # ==================== Read Operations (new) ====================

    @staticmethod
    def generate_select_by_id(
        sql_metadata: SQLRuntimeMetadata,
        obj_id: UUID,
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate a SELECT by ID statement for a model.

        Args:
            sql_metadata: SQLRuntimeMetadata containing table metadata
            obj_id: The object ID to select

        Returns:
            Tuple of (SQL string, parameters tuple)
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name

        sql = f"SELECT * FROM {schema}.{table} WHERE id = $1"
        params = (str(obj_id),)

        logger.debug(f"Generated SELECT by ID: {sql}")
        logger.debug(f"Parameters: {params}")

        return sql, params

    @staticmethod
    def generate_select_many(
        sql_metadata: SQLRuntimeMetadata,
        filters: list[FilterType] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        *,
        source_class_fqn: str | None = None,
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate a SELECT statement with filters, pagination, and sorting.

        Args:
            sql_metadata: SQLRuntimeMetadata containing table metadata
            filters: List of FilterType objects to apply
            limit: Optional limit for results
            offset: Optional offset for pagination

        Returns:
            Tuple of (SQL string, parameters tuple)
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name

        # Build base query
        sql = f"SELECT * FROM {schema}.{table}"

        # Use internal filter translator
        translator = _SQLFilterTranslator(sql_metadata=sql_metadata, source_class_fqn=source_class_fqn)
        where_sql, params = translator.translate_filters_to_where_clause(filters or [])
        order_sql = translator.translate_filters_to_order_clause(filters or [])

        # Add WHERE clause
        if where_sql:
            sql += f" {where_sql}"

        # Add ORDER BY clause
        if order_sql:
            sql += f" {order_sql}"

        # Add LIMIT and OFFSET
        if limit is not None:
            sql += f" LIMIT {translator._next_param()}"
            params.append(limit)
        if offset is not None:
            sql += f" OFFSET {translator._next_param()}"
            params.append(offset)

        logger.debug(f"Generated SELECT many: {sql}")
        logger.debug(f"Parameters: {tuple(params)}")

        return sql, tuple(params)

    @staticmethod
    def generate_count_query(
        sql_metadata: SQLRuntimeMetadata,
        filters: list[FilterType] | None = None,
        *,
        source_class_fqn: str | None = None,
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate a COUNT query with filters.

        Args:
            sql_metadata: SQLRuntimeMetadata containing table metadata
            filters: List of FilterType objects to apply

        Returns:
            Tuple of (SQL string, parameters tuple)
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name

        # Build base query
        sql = f"SELECT COUNT(*) as count FROM {schema}.{table}"

        # Use internal filter translator, but exclude sort filters for count queries
        translator = _SQLFilterTranslator(sql_metadata=sql_metadata, source_class_fqn=source_class_fqn)

        # Filter out SortFilter objects since they don't affect count
        non_sort_filters = []
        if filters:
            for f in filters:
                if not f.__class__.__name__ == "SortFilter":
                    non_sort_filters.append(f)

        where_sql, params = translator.translate_filters_to_where_clause(non_sort_filters)

        # Add WHERE clause
        if where_sql:
            sql += f" {where_sql}"

        logger.debug(f"Generated COUNT: {sql}")
        logger.debug(f"Parameters: {tuple(params)}")

        return sql, tuple(params)

    @staticmethod
    def generate_select_for_spec(
        sql_metadata: SQLRuntimeMetadata,
        query_spec: QuerySpec,
        *,
        source_class_fqn: str | None = None,
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate a SELECT statement from the strict public QuerySpec contract.

        QuerySpec uses metadata-bound identifiers and explicit boolean grouping.
        Unsupported predicates/operators fail instead of being silently skipped.
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name
        sql = f"SELECT * FROM {schema}.{table}"

        translator = _SQLFilterTranslator(
            sql_metadata=sql_metadata,
            source_class_fqn=source_class_fqn,
            strict=True,
        )
        where_sql, params = translator.translate_predicate_to_where_clause(query_spec.where)
        order_sql = translator.translate_order_specs_to_order_clause(query_spec.order_by)

        if where_sql:
            sql += f" {where_sql}"
        if order_sql:
            sql += f" {order_sql}"

        if query_spec.page is not None:
            if query_spec.page.limit is not None:
                sql += f" LIMIT {translator._next_param()}"
                params.append(query_spec.page.limit)
            if query_spec.page.offset is not None:
                sql += f" OFFSET {translator._next_param()}"
                params.append(query_spec.page.offset)

        logger.debug(f"Generated QuerySpec SELECT: {sql}")
        logger.debug(f"Parameters: {tuple(params)}")
        return sql, tuple(params)

    @staticmethod
    def generate_count_for_spec(
        sql_metadata: SQLRuntimeMetadata,
        query_spec: QuerySpec,
        *,
        source_class_fqn: str | None = None,
    ) -> tuple[str, tuple[Any, ...]]:
        """
        Generate a COUNT query from QuerySpec WHERE semantics.

        Ordering and pagination are intentionally ignored for counts.
        """
        schema = sql_metadata.table_schema
        table = sql_metadata.table_name
        sql = f"SELECT COUNT(*) as count FROM {schema}.{table}"

        translator = _SQLFilterTranslator(
            sql_metadata=sql_metadata,
            source_class_fqn=source_class_fqn,
            strict=True,
        )
        where_sql, params = translator.translate_predicate_to_where_clause(query_spec.where)
        if where_sql:
            sql += f" {where_sql}"

        logger.debug(f"Generated QuerySpec COUNT: {sql}")
        logger.debug(f"Parameters: {tuple(params)}")
        return sql, tuple(params)

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        """Ensure values are database serializable."""
        # Handle UUIDs
        try:
            from uuid import UUID as _UUID

            if isinstance(value, _UUID):
                return str(value)
        except Exception:
            pass

        # Handle Enums
        try:
            from enum import Enum as _Enum

            if isinstance(value, _Enum):
                return value.value
        except Exception:
            pass

        # For dicts, serialize as JSON text (assumed json/jsonb columns)
        if isinstance(value, dict):
            return json.dumps({k: SQLGenerator._normalize_value(v) for k, v in value.items()})

        # For arrays (list/tuple/set), pass as Python lists for asyncpg arrays
        if isinstance(value, (list, tuple, set)):
            # Normalize items (UUIDs/enums/etc.)
            normalized_items = [SQLGenerator._normalize_value(item) for item in list(value)]
            return normalized_items

        # Leave primitives as-is
        return value
