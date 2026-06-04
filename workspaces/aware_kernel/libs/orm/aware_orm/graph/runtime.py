"""Runtime access to GraphSQL plan caches installed from kernel-lite."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aware_orm.graph.plan_cache import GraphPlanCache, GraphPlan
from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata

if TYPE_CHECKING:  # pragma: no cover
    from aware_orm.runtime.plan_registry import GraphSQLPlanRegistry

__all__ = ["GraphSQLRuntime"]


class GraphSQLRuntime:
    _plan_cache: GraphPlanCache | None = None
    _config_registry: GraphConfigRegistry | None = None
    _plan_hits: dict[str, int] = {}
    _plan_misses: dict[str, int] = {}
    _plan_registry: GraphSQLPlanRegistry | None = None
    _planner_version: str | None = None

    @classmethod
    def install(
        cls,
        plan_cache: GraphPlanCache,
        config_registry: GraphConfigRegistry | None = None,
        plan_registry: GraphSQLPlanRegistry | None = None,
    ) -> None:
        cls._plan_cache = plan_cache
        cls._plan_hits.clear()
        cls._plan_misses.clear()
        cls._config_registry = config_registry
        cls._plan_registry = plan_registry
        cls._planner_version = plan_registry.planner_version if plan_registry else None

    @classmethod
    def reset(cls) -> None:
        cls._plan_cache = None
        cls._config_registry = None
        cls._plan_hits.clear()
        cls._plan_misses.clear()
        cls._plan_registry = None
        cls._planner_version = None

    @classmethod
    def get_plan(cls, root_table_key: str) -> GraphPlan | None:
        cache = cls._plan_cache
        table_key = root_table_key.lower()
        if cache is None:
            cls._plan_misses[table_key] = cls._plan_misses.get(table_key, 0) + 1
            return None
        plan = cache.get(root_table_key) or cache.get(table_key)
        if plan is None:
            cls._plan_misses[table_key] = cls._plan_misses.get(table_key, 0) + 1
            return None
        cls._plan_hits[table_key] = cls._plan_hits.get(table_key, 0) + 1
        return plan

    @classmethod
    def get_config_registry(cls, sql_metadata: SQLRuntimeMetadata) -> GraphConfigRegistry:
        registry = cls._config_registry
        if registry:
            return registry
        columns: list[str] = []
        seen: set[str] = set()
        for col in (sql_metadata.column_by_attribute or {}).values():
            if not col:
                continue
            key = str(col)
            if key in seen:
                continue
            seen.add(key)
            columns.append(key)
        root_descriptor = TableDescriptor(
            class_config_id=sql_metadata.class_config_id,
            table_schema=sql_metadata.table_schema,
            table_name=sql_metadata.table_name,
            attributes=tuple(columns),
        )
        return GraphConfigRegistry([root_descriptor])

    @classmethod
    def plan_stats(cls) -> dict[str, dict[str, int]]:
        return {
            "hits": dict(cls._plan_hits),
            "misses": dict(cls._plan_misses),
        }

    @classmethod
    def get_plan_registry(cls) -> GraphSQLPlanRegistry | None:
        return cls._plan_registry

    @classmethod
    def planner_version(cls) -> str | None:
        return cls._planner_version
