"""Plan-aware GraphSQL generator that consumes precompiled plans."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence, Tuple, TYPE_CHECKING

from aware_orm._support import logger

from aware_orm.graph.config_registry import GraphConfigRegistry
from aware_orm.graph.plan_cache import GraphPlan, PlanStep
from aware_orm.graph.plan_context import PlanContext
from aware_orm.graph.runtime import GraphSQLRuntime
from aware_orm.query.graph_spec import GraphRetrievalContract, GraphSpec
from aware_orm.sql_generator._filter_translator import _SQLFilterTranslator

if TYPE_CHECKING:  # pragma: no cover
    from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata

_logged_plan_fallbacks: set[str] = set()


class PlanAwareGraphSQLGenerator:
    """Generate GraphSQL using a precompiled plan."""

    def __init__(
        self,
        sql_metadata: SQLRuntimeMetadata,
        plan: GraphPlan,
        config_registry: GraphConfigRegistry,
        *,
        source_class_fqn: str | None = None,
        graph_spec: GraphSpec | None = None,
    ) -> None:
        self.sql_metadata = sql_metadata
        self.plan = plan
        self.config_registry = config_registry
        self.source_class_fqn = source_class_fqn
        self.graph_spec = graph_spec or GraphSpec()
        self.contract = GraphRetrievalContract.from_plan(plan, config_registry, graph_spec=self.graph_spec)
        self.context = PlanContext(plan, config_registry)
        self.root_schema, self.root_table = self._split_table_key(plan.root_table_key)
        self._steps_by_parent: dict[str, list[tuple[int, PlanStep]]] = defaultdict(list)
        for index, step in enumerate(plan.steps, start=1):
            parent = step.parent_table_key or plan.root_table_key
            self._steps_by_parent[parent].append((index, step))

    def generate_select_by_id(self, obj_id: Any) -> Tuple[str, Tuple[str]]:
        params: list[Any] = [str(obj_id)]
        where_clause = self._append_scope_conditions("roots.id = $1", params)
        sql = self._compose_query(where_clause=where_clause)
        logger.debug("Plan-aware GraphSQL SELECT by id: %s", sql)
        return sql, tuple(params)

    def generate_select_many(self, filters, limit, offset) -> Tuple[str, Tuple[Any, ...]]:
        filter_sql, filter_params = self._translate_filters(filters)
        params = list(filter_params)
        where_clause = self._append_scope_conditions(filter_sql, params)
        inner_sql = self._compose_query(where_clause=where_clause)
        if limit is not None:
            inner_sql += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        if offset is not None:
            inner_sql += f" OFFSET ${len(params) + 1}"
            params.append(offset)
        sql = f"SELECT COALESCE(json_agg(graph), '[]'::json) AS graph FROM ({inner_sql}) graph_rows"
        logger.debug("Plan-aware GraphSQL SELECT many: %s", sql)
        return sql, tuple(params)

    def _compose_query(self, *, where_clause: str | None) -> str:
        projection = self._build_projection()
        sql = f"SELECT {projection} AS graph FROM {self.root_schema}.{self.root_table} roots"
        if where_clause:
            sql += f" WHERE {where_clause}"
        return sql

    def _translate_filters(self, filters) -> tuple[str | None, Sequence[Any]]:
        if not filters:
            return None, []

        translator = _SQLFilterTranslator(
            table_alias="roots",
            sql_metadata=self.sql_metadata,
            source_class_fqn=self.source_class_fqn,
        )
        translator.param_counter = 0
        where_sql, filter_params = translator.translate_filters_to_where_clause(filters)
        if where_sql:
            clause = where_sql.replace("WHERE ", "").strip()
            for flt in filters:
                column = getattr(flt, "column", None)
                if column and f"{column}" in clause and f"{column}." not in clause and f"{column} " in clause:
                    clause = clause.replace(column, f"roots.{column}")
                elif column and f"{column} =" in clause and f"roots.{column}" not in clause:
                    clause = clause.replace(column, f"roots.{column}")
            clause = clause.replace(f"{self.root_schema}.{self.root_table}", "roots")
            return clause, filter_params
        return None, filter_params

    def _append_scope_conditions(self, where_clause: str | None, params: list[Any]) -> str | None:
        scope_filters = self.graph_spec.root_scope_filters()
        if not scope_filters:
            return where_clause

        translator = _SQLFilterTranslator(
            table_alias="roots",
            sql_metadata=self.sql_metadata,
            source_class_fqn=self.source_class_fqn,
            strict=True,
        )
        translator.param_counter = len(params)

        conditions = [where_clause] if where_clause else []
        for scope_filter in scope_filters:
            condition, condition_params = translator.translate_predicate(scope_filter)
            if condition:
                conditions.append(condition)
                params.extend(condition_params)
        if not conditions:
            return None
        return " AND ".join(conditions)

    def _build_projection(self) -> str:
        return self._build_object_projection(
            table_key=self.plan.root_table_key,
            table_alias="roots",
            fields=self.plan.root_projection_fields or self.context.root_descriptor().attributes or ("id",),
        )

    def _build_object_projection(self, *, table_key: str, table_alias: str, fields: Sequence[str]) -> str:
        object_fields = []
        for field in fields:
            if field:
                object_fields.append(f"'{field}', {table_alias}.{field}")
        object_fields.extend(self._build_step_fields(parent_table_key=table_key, parent_alias=table_alias))
        return f"json_build_object({', '.join(object_fields)})"

    def _build_step_fields(self, *, parent_table_key: str, parent_alias: str) -> Sequence[str]:
        projections = []
        for index, step in self._steps_by_parent.get(parent_table_key, []):
            descriptor = self.config_registry.require(step.table_key)
            step_schema, step_table = self._split_table_key(step.table_key)
            alias = f"step_{index}"
            fields = step.projection_fields or descriptor.attributes or ("id",)
            child_projection = self._build_object_projection(
                table_key=step.table_key,
                table_alias=alias,
                fields=fields,
            )
            from_clause = f"FROM {step_schema}.{step_table} {alias}"
            where_clause = ""
            if step.join_condition:
                condition = self._alias_join_condition(
                    step.join_condition,
                    parent_table_key,
                    parent_alias,
                    step.table_key,
                    alias,
                )
                where_clause = f" WHERE {condition}"
            if step.uses_collection:
                collection_subselect = f"SELECT json_agg({child_projection}) {from_clause}{where_clause}"
                projections.append(f"'{descriptor.table_name}', COALESCE(({collection_subselect}), '[]'::json)")
            else:
                subselect = f"SELECT {child_projection} {from_clause}{where_clause}"
                projections.append(f"'{descriptor.table_name}', ({subselect} LIMIT 1)")
        return projections

    def _alias_join_condition(
        self,
        condition: str,
        parent_table_key: str,
        parent_alias: str,
        step_table_key: str,
        step_alias: str,
    ) -> str:
        condition = condition.replace(parent_table_key, parent_alias)
        condition = condition.replace(step_table_key, step_alias)
        return condition

    def _split_table_key(self, table_key: str) -> Tuple[str, str]:
        schema, table = table_key.split(".", 1)
        return schema, table


def get_graphsql_generator(
    sql_metadata: SQLRuntimeMetadata,
    *,
    source_class_fqn: str | None = None,
    graph_spec: GraphSpec | None = None,
) -> PlanAwareGraphSQLGenerator:
    plan = GraphSQLRuntime.get_plan(sql_metadata.table_key)
    if plan is None:
        raise RuntimeError(f"No plan found for table {sql_metadata.table_key}")
    registry = GraphSQLRuntime.get_config_registry(sql_metadata)
    return PlanAwareGraphSQLGenerator(
        sql_metadata,
        plan,
        registry,
        source_class_fqn=source_class_fqn,
        graph_spec=graph_spec,
    )
