# @code-under-test: ../../aware_orm/graph/runtime.py

from __future__ import annotations

from aware_orm.graph.plan_cache import GraphPlanCache, GraphPlan, PlanStep
from aware_orm.graph.runtime import GraphSQLRuntime


def test_runtime_install_and_get_plan():
    cache = GraphPlanCache(
        [
            GraphPlan(
                root_table_key="public.users",
                steps=(PlanStep("public.profiles", None),),
            )
        ]
    )
    GraphSQLRuntime.install(cache)

    plan = GraphSQLRuntime.get_plan("public.users")
    assert plan is not None
    assert plan.steps[0].table_key == "public.profiles"

    GraphSQLRuntime.reset()
    assert GraphSQLRuntime.get_plan("public.users") is None
