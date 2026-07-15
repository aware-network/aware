"""
Internal SQL Filter Translator - Convert Filters to SQL WHERE Clauses

This is an internal helper module for SQLGenerator.
Do not import directly - use SQLGenerator instead.

This module translates FilterType objects from the filters.py system into
SQL WHERE clauses that can be used with session-based SQL generation.
"""

from __future__ import annotations

from typing import List, Tuple, Any, Optional, Sequence, TYPE_CHECKING
from aware_orm.filters import (
    FilterType,
    EqFilter,
    NeqFilter,
    GtFilter,
    GteFilter,
    LtFilter,
    LteFilter,
    InFilter,
    LikeFilter,
    IsNullFilter,
    SortFilter,
    RelationPathFilter,
)
from aware_orm.query_spec import Predicate, PredicateGroup, QueryOrder
from aware_orm._support import logger

if TYPE_CHECKING:  # pragma: no cover
    from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata

# Internal module - not for external import
__all__ = []


class _SQLFilterTranslator:
    """
    Internal helper that translates filter objects to SQL WHERE clauses and ORDER BY clauses.

    This class provides methods to convert FilterType objects into SQL strings
    with parameterized queries for safe execution through asyncpg.

    NOTE: This is an internal helper. Use SQLGenerator.generate_select_* methods instead.
    """

    def __init__(
        self,
        table_alias: Optional[str] = None,
        sql_metadata: Optional["SQLRuntimeMetadata"] = None,
        source_class_fqn: Optional[str] = None,
        *,
        strict: bool = False,
    ) -> None:
        """
        Initialize SQL filter translator.

        Args:
            table_alias: Optional table alias to prefix column names
        """
        self.table_alias = table_alias
        self.param_counter = 0
        self._sql_metadata = sql_metadata
        self._source_class_fqn = source_class_fqn
        self._strict = strict
        self._column_map = {}
        self._allowed_columns = set()
        if sql_metadata:
            self._column_map = {
                attr.lower(): column for attr, column in (sql_metadata.column_by_attribute or {}).items() if column
            }
            for attr, column in (sql_metadata.column_by_attribute or {}).items():
                if attr:
                    self._allowed_columns.add(str(attr).lower())
                if column:
                    self._allowed_columns.add(str(column).lower())

    def reset_params(self):
        """Reset parameter counter for new query."""
        self.param_counter = 0

    def _next_param(self) -> str:
        """Get next parameter placeholder."""
        self.param_counter += 1
        return f"${self.param_counter}"

    def _qualify_column(self, column: str) -> str:
        """Add table alias to column name if configured."""
        prefix = None
        base = column
        if "." in column:
            prefix, base = column.rsplit(".", 1)
        resolved_base = self._resolve_column_base(base)
        if prefix:
            return f"{prefix}.{resolved_base}"
        if self.table_alias:
            return f"{self.table_alias}.{resolved_base}"
        return resolved_base

    def _resolve_column_base(self, column: str) -> str:
        if self._strict and self._sql_metadata is None:
            raise ValueError("Strict QuerySpec translation requires SQL runtime metadata")

        if not self._column_map:
            if self._strict and column.lower() not in self._allowed_columns:
                self._raise_metadata_column_error(column)
            return column

        resolved_column = self._column_map.get(column.lower())
        if resolved_column:
            return resolved_column
        if column.lower() in self._allowed_columns:
            return column
        if self._strict:
            self._raise_metadata_column_error(column)
        return column

    def _raise_metadata_column_error(self, column: str) -> None:
        metadata = self._sql_metadata
        if metadata is None:
            raise ValueError(f"Column '{column}' cannot be resolved without SQL runtime metadata")
        raise ValueError(
            f"Column '{column}' is not declared in SQL metadata for {metadata.table_schema}.{metadata.table_name}"
        )

    def _ignore_or_raise(self, message: str, *args: Any) -> Tuple[str, List[Any]]:
        if self._strict:
            raise ValueError(message % args if args else message)
        logger.warning(message, *args)
        return "", []

    def _translate_relation_filter(self, filter_obj: RelationPathFilter) -> Tuple[str, List[Any]]:
        from aware_orm.runtime.relationship_strategies import (
            get_relationship_metadata_by_source,
        )

        if not self._source_class_fqn:
            return self._ignore_or_raise("RelationPathFilter requires source class FQN: %s", filter_obj)

        segments = filter_obj.get_path_segments()
        if not segments:
            return self._ignore_or_raise("RelationPathFilter missing path segments: %s", filter_obj)

        metadata_chain = []
        current_class = self._source_class_fqn
        for segment in segments:
            metadata = get_relationship_metadata_by_source(current_class, segment)
            if metadata is None:
                return self._ignore_or_raise(
                    "RelationPathFilter metadata missing for %s.%s",
                    current_class,
                    segment,
                )
            metadata_chain.append(metadata)
            current_class = metadata.target_class_fqn

        if len(metadata_chain) == 1:
            return self._translate_relation_filter_single(filter_obj, metadata_chain[0])

        return self._translate_relation_filter_multi(filter_obj, metadata_chain)

    def _translate_relation_filter_single(
        self,
        filter_obj: RelationPathFilter,
        metadata,
    ) -> Tuple[str, List[Any]]:
        chain = metadata.join_chain or []

        if len(chain) > 1:
            return self._build_relation_exists_query(filter_obj, [metadata])

        if not chain:
            source_fk = metadata.get_source_fk_column()
            if not source_fk or not source_fk.get("column_name"):
                return self._ignore_or_raise(
                    "RelationPathFilter missing source FK column metadata for %s",
                    self._source_class_fqn,
                )
            column_expr = self._qualify_column(source_fk["column_name"])
        else:
            column_expr = self._qualify_relation_column(None, chain[0].get("from"))

        if not column_expr:
            return "", []
        return self._apply_simple_relation_operator(column_expr, filter_obj)

    def _translate_relation_filter_multi(
        self,
        filter_obj: RelationPathFilter,
        metadata_chain,
    ) -> Tuple[str, List[Any]]:
        return self._build_relation_exists_query(filter_obj, metadata_chain)

    def _apply_simple_relation_operator(
        self, column_expr: str, filter_obj: RelationPathFilter
    ) -> Tuple[str, List[Any]]:
        operator = filter_obj.operator
        if operator == "eq":
            param = self._next_param()
            return f"{column_expr} = {param}", [filter_obj.value]
        if operator == "neq":
            param = self._next_param()
            return f"{column_expr} != {param}", [filter_obj.value]
        if operator == "in":
            values = filter_obj.value or []
            if not isinstance(values, list) or not values:
                return "FALSE", []
            params = []
            placeholders = []
            for value in values:
                param = self._next_param()
                placeholders.append(param)
                params.append(value)
            return f"{column_expr} IN ({', '.join(placeholders)})", params
        if operator == "is_null":
            return (f"{column_expr} IS NULL", []) if filter_obj.value else (f"{column_expr} IS NOT NULL", [])

        return self._ignore_or_raise("RelationPathFilter operator not supported: %s", operator)

    def _build_relation_exists_query(
        self,
        filter_obj: RelationPathFilter,
        metadata_chain,
    ) -> Tuple[str, List[Any]]:
        from aware_orm.runtime.sql_metadata import get_sql_metadata_for_class

        operator = filter_obj.operator
        if operator not in {"eq", "neq", "in", "is_null"}:
            return self._ignore_or_raise("RelationPathFilter operator not supported in multi-hop: %s", operator)

        select_clause: Optional[str] = None
        join_clauses: List[str] = []
        where_clauses: List[str] = []
        params: List[Any] = []

        current_alias: Optional[str] = None
        alias_counter = 0

        for segment_metadata in metadata_chain:
            chain = segment_metadata.join_chain or []
            if not chain:
                return self._ignore_or_raise(
                    "RelationPathFilter missing join metadata for %s",
                    segment_metadata.source_class_fqn,
                )

            for hop in chain:
                alias = f"rel{alias_counter}"
                alias_counter += 1
                target_table = self._format_table_from_column(hop.get("to"))
                left_expr = self._qualify_relation_column(current_alias, hop.get("from"))
                right_column = hop.get("to", {}).get("column_name")
                if not target_table or not left_expr or not right_column:
                    return self._ignore_or_raise("RelationPathFilter join hop missing metadata: %s", hop)

                right_expr = f"{alias}.{right_column}"
                if select_clause is None:
                    select_clause = f"SELECT 1 FROM {target_table} {alias}"
                    where_clauses.append(f"{left_expr} = {right_expr}")
                else:
                    join_clauses.append(f"JOIN {target_table} {alias} ON {left_expr} = {right_expr}")
                current_alias = alias

        final_metadata = metadata_chain[-1]
        target_sql_metadata = get_sql_metadata_for_class(final_metadata.target_class_fqn)
        target_column = self._resolve_target_column(target_sql_metadata, filter_obj.field)
        if not target_column:
            return self._ignore_or_raise(
                "Unable to resolve target column for %s.%s",
                final_metadata.target_class_fqn,
                filter_obj.field,
            )

        final_expr = f"{current_alias}.{target_column}" if current_alias else target_column
        if operator == "eq":
            param = self._next_param()
            where_clauses.append(f"{final_expr} = {param}")
            params.append(filter_obj.value)
        elif operator == "neq":
            param = self._next_param()
            where_clauses.append(f"{final_expr} != {param}")
            params.append(filter_obj.value)
        elif operator == "in":
            values = filter_obj.value or []
            if not isinstance(values, list) or not values:
                return "FALSE", []
            placeholders = []
            for value in values:
                param = self._next_param()
                placeholders.append(param)
                params.append(value)
            where_clauses.append(f"{final_expr} IN ({', '.join(placeholders)})")
        elif operator == "is_null":
            where_clauses.append(f"{final_expr} IS {'NULL' if filter_obj.value else 'NOT NULL'}")

        subquery = select_clause or ""
        if join_clauses:
            subquery = f"{subquery} {' '.join(join_clauses)}"
        if where_clauses:
            subquery = f"{subquery} WHERE {' AND '.join(where_clauses)}"
        if not subquery:
            return "", []
        return f"EXISTS ({subquery})", params

    def _qualify_relation_column(self, current_alias: Optional[str], column: Optional[dict]) -> Optional[str]:
        if not column or not column.get("column_name"):
            return None
        column_name = column["column_name"]
        if current_alias is None:
            table_name = column.get("table_name")
            if table_name:
                return f"{table_name}.{column_name}"
            return self._qualify_column(column_name)
        return f"{current_alias}.{column_name}"

    @staticmethod
    def _format_table_from_column(column: Optional[dict]) -> Optional[str]:
        if not column:
            return None
        table_name = column.get("table_name")
        schema = column.get("table_schema")
        if table_name and schema:
            return f"{schema}.{table_name}"
        return table_name

    def _resolve_target_column(self, metadata: Optional["SQLRuntimeMetadata"], attribute: str) -> Optional[str]:
        if metadata is None:
            if self._strict:
                raise ValueError(f"SQL metadata is not registered for relation target column '{attribute}'")
            return attribute
        mapping = metadata.column_by_attribute or {}
        column = mapping.get(attribute) or mapping.get(attribute.lower())
        if column:
            return column
        allowed = {str(key).lower() for key in mapping}
        allowed.update(str(value).lower() for value in mapping.values())
        if self._strict and attribute.lower() not in allowed:
            raise ValueError(
                f"Column '{attribute}' is not declared in SQL metadata for "
                f"{metadata.table_schema}.{metadata.table_name}"
            )
        return attribute

    def translate_predicate_to_where_clause(self, predicate: Predicate | None) -> Tuple[str, List[Any]]:
        """Convert a QuerySpec predicate tree to a SQL WHERE clause."""

        if predicate is None:
            return "", []

        condition, parameters = self.translate_predicate(predicate)
        if not condition:
            return "", []
        return f"WHERE {condition}", parameters

    def translate_predicate(self, predicate: Predicate) -> Tuple[str, List[Any]]:
        """Convert a QuerySpec predicate tree to SQL condition text and parameters."""

        if isinstance(predicate, PredicateGroup):
            conditions = []
            parameters: List[Any] = []
            for child in predicate.predicates:
                condition, params = self.translate_predicate(child)
                if condition:
                    conditions.append(condition)
                    parameters.extend(params)

            if not conditions:
                if self._strict:
                    raise ValueError("QuerySpec predicate group did not produce a SQL condition")
                return "", []

            joiner = f" {predicate.op.upper()} "
            return f"({joiner.join(conditions)})", parameters

        return self._translate_single_filter(predicate)

    def translate_filters_to_where_clause(self, filters: List[FilterType]) -> Tuple[str, List[Any]]:
        """
        Convert a list of filters to a SQL WHERE clause.

        Args:
            filters: List of FilterType objects to convert

        Returns:
            Tuple of (WHERE clause SQL, list of parameter values)
        """
        if not filters:
            return "", []

        where_conditions = []
        parameters = []

        for filter_obj in filters:
            condition, params = self._translate_single_filter(filter_obj)
            if condition:  # Skip empty conditions
                where_conditions.append(condition)
                parameters.extend(params)

        if not where_conditions:
            return "", []

        where_clause = "WHERE " + " AND ".join(where_conditions)
        return where_clause, parameters

    def translate_filters_to_order_clause(self, filters: List[FilterType]) -> str:
        """
        Extract ORDER BY clauses from SortFilter objects.

        Args:
            filters: List of FilterType objects to check for sort filters

        Returns:
            ORDER BY clause SQL (empty string if no sort filters)
        """
        sort_clauses = []

        for filter_obj in filters:
            if isinstance(filter_obj, SortFilter):
                column = self._qualify_column(filter_obj.column)
                direction = "DESC" if filter_obj.order.value.upper() == "DESC" else "ASC"
                sort_clauses.append(f"{column} {direction}")

        if not sort_clauses:
            return ""

        return "ORDER BY " + ", ".join(sort_clauses)

    def translate_order_specs_to_order_clause(self, order_specs: Sequence[QueryOrder]) -> str:
        """Convert QuerySpec order specs to an ORDER BY clause."""

        sort_clauses = []
        for order in order_specs:
            column = self._qualify_column(order.column)
            direction = "DESC" if order.direction.value.upper() == "DESC" else "ASC"
            sort_clauses.append(f"{column} {direction}")

        if not sort_clauses:
            return ""

        return "ORDER BY " + ", ".join(sort_clauses)

    def _translate_single_filter(self, filter_obj: FilterType) -> Tuple[str, List[Any]]:
        """
        Translate a single filter to SQL condition.

        Args:
            filter_obj: Single FilterType object to translate

        Returns:
            Tuple of (SQL condition, list of parameter values)
        """
        try:
            if isinstance(filter_obj, EqFilter):
                return self._translate_eq_filter(filter_obj)
            elif isinstance(filter_obj, NeqFilter):
                return self._translate_neq_filter(filter_obj)
            elif isinstance(filter_obj, GtFilter):
                return self._translate_gt_filter(filter_obj)
            elif isinstance(filter_obj, GteFilter):
                return self._translate_gte_filter(filter_obj)
            elif isinstance(filter_obj, LtFilter):
                return self._translate_lt_filter(filter_obj)
            elif isinstance(filter_obj, LteFilter):
                return self._translate_lte_filter(filter_obj)
            elif isinstance(filter_obj, InFilter):
                return self._translate_in_filter(filter_obj)
            elif isinstance(filter_obj, LikeFilter):
                return self._translate_like_filter(filter_obj)
            elif isinstance(filter_obj, IsNullFilter):
                return self._translate_is_null_filter(filter_obj)
            elif isinstance(filter_obj, SortFilter):
                # Sort filters are handled separately in translate_filters_to_order_clause
                return "", []
            elif isinstance(filter_obj, RelationPathFilter):
                return self._translate_relation_filter(filter_obj)
            else:
                if self._strict:
                    raise TypeError(f"Unknown filter type: {type(filter_obj).__name__}")
                logger.warning(f"Unknown filter type: {type(filter_obj)}")
                return "", []

        except Exception as e:
            if self._strict:
                raise
            logger.error(f"Error translating filter {filter_obj}: {e}")
            return "", []

    def _translate_eq_filter(self, filter_obj: EqFilter) -> Tuple[str, List[Any]]:
        """Translate equality filter."""
        column = self._qualify_column(filter_obj.column)
        param = self._next_param()
        return f"{column} = {param}", [filter_obj.value]

    def _translate_neq_filter(self, filter_obj: NeqFilter) -> Tuple[str, List[Any]]:
        """Translate inequality filter."""
        column = self._qualify_column(filter_obj.column)
        param = self._next_param()
        return f"{column} != {param}", [filter_obj.value]

    def _translate_gt_filter(self, filter_obj: GtFilter) -> Tuple[str, List[Any]]:
        """Translate greater than filter."""
        column = self._qualify_column(filter_obj.column)
        param = self._next_param()
        return f"{column} > {param}", [filter_obj.value]

    def _translate_gte_filter(self, filter_obj: GteFilter) -> Tuple[str, List[Any]]:
        """Translate greater than or equal filter."""
        column = self._qualify_column(filter_obj.column)
        param = self._next_param()
        return f"{column} >= {param}", [filter_obj.value]

    def _translate_lt_filter(self, filter_obj: LtFilter) -> Tuple[str, List[Any]]:
        """Translate less than filter."""
        column = self._qualify_column(filter_obj.column)
        param = self._next_param()
        return f"{column} < {param}", [filter_obj.value]

    def _translate_lte_filter(self, filter_obj: LteFilter) -> Tuple[str, List[Any]]:
        """Translate less than or equal filter."""
        column = self._qualify_column(filter_obj.column)
        param = self._next_param()
        return f"{column} <= {param}", [filter_obj.value]

    def _translate_in_filter(self, filter_obj: InFilter) -> Tuple[str, List[Any]]:
        """Translate IN filter."""
        if not filter_obj.values:
            return "FALSE", []  # Empty IN clause should match nothing

        column = self._qualify_column(filter_obj.column)
        params = []
        param_placeholders = []

        for value in filter_obj.values:
            param = self._next_param()
            params.append(value)
            param_placeholders.append(param)

        placeholders_str = ", ".join(param_placeholders)
        return f"{column} IN ({placeholders_str})", params

    def _translate_like_filter(self, filter_obj: LikeFilter) -> Tuple[str, List[Any]]:
        """Translate LIKE filter."""
        column = self._qualify_column(filter_obj.column)
        param = self._next_param()
        return f"{column} LIKE {param}", [filter_obj.pattern]

    def _translate_is_null_filter(self, filter_obj: IsNullFilter) -> Tuple[str, List[Any]]:
        """Translate IS NULL filter."""
        column = self._qualify_column(filter_obj.column)
        if filter_obj.is_null:
            return f"{column} IS NULL", []
        else:
            return f"{column} IS NOT NULL", []
