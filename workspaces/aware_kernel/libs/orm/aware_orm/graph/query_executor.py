"""High-level orchestrator for executing GraphSQL plans."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Iterable
from uuid import UUID

from .plan_cache import GraphPlan, GraphPlanCache


GeneratorFactory = Callable[[GraphPlan], "PlanAwareGenerator"]
Hydrator = Callable[[Iterable[dict[str, Any]], GraphPlan], Any]


class PlanAwareGenerator:
    """Protocol-like base class for generator factories used in tests."""

    def build_select_by_id(self, obj_id: UUID) -> tuple[str, tuple[Any, ...]]:
        raise NotImplementedError

    def build_select_many(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> tuple[str, tuple[Any, ...]]:
        raise NotImplementedError


class GraphQueryExecutor:
    def __init__(self, plan_cache: GraphPlanCache) -> None:
        self._plan_cache = plan_cache

    async def fetch_by_id(
        self,
        session: "AsyncSessionLike",
        root_table_key: str,
        obj_id: UUID,
        generator_factory: GeneratorFactory,
        hydrator: Hydrator,
    ) -> Any:
        plan = self._plan_cache.require(root_table_key)
        generator = generator_factory(plan)
        sql, params = generator.build_select_by_id(obj_id)
        rows = await session.execute_query(sql, *params)
        return hydrator(rows, plan)

    async def fetch_list(
        self,
        session: "AsyncSessionLike",
        root_table_key: str,
        generator_factory: GeneratorFactory,
        hydrator: Hydrator,
        **generator_kwargs: Any,
    ) -> Any:
        plan = self._plan_cache.require(root_table_key)
        generator = generator_factory(plan)
        sql, params = generator.build_select_many(**generator_kwargs)
        rows = await session.execute_query(sql, *params)
        return hydrator(rows, plan)


class AsyncSessionLike:
    """Minimal session protocol for tests."""

    async def execute_query(self, sql: str, *params: Any) -> Iterable[dict[str, Any]]:  # pragma: no cover - protocol
        raise NotImplementedError
