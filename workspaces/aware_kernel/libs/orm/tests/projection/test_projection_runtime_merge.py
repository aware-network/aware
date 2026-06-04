from __future__ import annotations

import pytest

from aware_orm.projection.plan import ProjectionPlan, ProjectionPlanCache
from aware_orm.projection.runtime import ProjectionRuntime


def _plan(*, dialect: str, projection_hash: str) -> ProjectionPlan:
    return ProjectionPlan(
        projection_hash=projection_hash,
        opg_name=f"opg:{projection_hash}",
        dialect=dialect,  # type: ignore[arg-type]
        tables=tuple(),
        associations=tuple(),
    )


def test_projection_runtime_extend_merges_module_caches() -> None:
    ProjectionRuntime.reset()

    cache_a = ProjectionPlanCache([_plan(dialect="postgres", projection_hash="h1")])
    cache_b = ProjectionPlanCache([_plan(dialect="postgres", projection_hash="h2")])

    ProjectionRuntime.install(cache_a)
    ProjectionRuntime.extend(cache_b)

    assert ProjectionRuntime.require_plan(dialect="postgres", projection_hash="h1").projection_hash == "h1"
    assert ProjectionRuntime.require_plan(dialect="postgres", projection_hash="h2").projection_hash == "h2"


def test_projection_runtime_extend_installs_when_empty() -> None:
    ProjectionRuntime.reset()

    cache = ProjectionPlanCache([_plan(dialect="postgres", projection_hash="h1")])
    ProjectionRuntime.extend(cache)

    assert ProjectionRuntime.require_plan(dialect="postgres", projection_hash="h1").projection_hash == "h1"


def test_projection_runtime_extend_does_not_backfill_missing() -> None:
    ProjectionRuntime.reset()

    ProjectionRuntime.install(ProjectionPlanCache())
    with pytest.raises(KeyError):
        ProjectionRuntime.require_plan(dialect="postgres", projection_hash="missing")
