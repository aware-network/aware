"""Runtime access to ProjectionPlan caches installed from `.aware` bundles."""

from __future__ import annotations

from aware_orm.projection.plan import (
    ProjectionDialect,
    ProjectionPlan,
    ProjectionPlanCache,
)

__all__ = ["ProjectionRuntime"]


class ProjectionRuntime:
    _plan_cache: ProjectionPlanCache | None = None
    _hits: dict[tuple[str, str], int] = {}
    _misses: dict[tuple[str, str], int] = {}

    @classmethod
    def install(cls, plan_cache: ProjectionPlanCache) -> None:
        # Install a fresh cache instance so subsequent merges don't mutate the caller's object.
        merged = ProjectionPlanCache()
        for plan in plan_cache.all():
            merged.register(plan)
        cls._plan_cache = merged
        cls._hits.clear()
        cls._misses.clear()

    @classmethod
    def extend(cls, plan_cache: ProjectionPlanCache) -> None:
        """Merge additional projection plans into the installed cache.

        Composition manifests load multiple module bundles; projection plans are per-module.
        Runtime needs a unified cache so any projection_hash can be staged without re-compiling.
        """
        if cls._plan_cache is None:
            cls.install(plan_cache)
            return
        for plan in plan_cache.all():
            cls._plan_cache.register(plan)

    @classmethod
    def reset(cls) -> None:
        cls._plan_cache = None
        cls._hits.clear()
        cls._misses.clear()

    @classmethod
    def get_plan(cls, *, dialect: ProjectionDialect, projection_hash: str) -> ProjectionPlan | None:
        cache = cls._plan_cache
        key = (dialect, projection_hash)
        if cache is None:
            cls._misses[key] = cls._misses.get(key, 0) + 1
            return None
        plan = cache.get(dialect=dialect, projection_hash=projection_hash)
        if plan is None:
            cls._misses[key] = cls._misses.get(key, 0) + 1
            return None
        cls._hits[key] = cls._hits.get(key, 0) + 1
        return plan

    @classmethod
    def require_plan(cls, *, dialect: ProjectionDialect, projection_hash: str) -> ProjectionPlan:
        plan = cls.get_plan(dialect=dialect, projection_hash=projection_hash)
        if plan is None:
            raise KeyError(f"ProjectionPlan missing for {dialect}:{projection_hash}")
        return plan

    @classmethod
    def plan_stats(cls) -> dict[str, dict[str, int]]:
        hits = {f"{k[0]}:{k[1]}": v for k, v in cls._hits.items()}
        misses = {f"{k[0]}:{k[1]}": v for k, v in cls._misses.items()}
        return {"hits": hits, "misses": misses}
