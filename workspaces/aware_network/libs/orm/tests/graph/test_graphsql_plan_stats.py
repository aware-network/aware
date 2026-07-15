from __future__ import annotations

from uuid import uuid4

from aware_orm.graph.plan_cache import GraphPlan, GraphPlanCache
from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.runtime import GraphSQLRuntime


def test_plan_stats_hit_and_miss():
    GraphSQLRuntime.reset()
    plan = GraphPlan(root_table_key="public.sample")
    cache = GraphPlanCache([plan])
    registry = GraphConfigRegistry([TableDescriptor(uuid4(), "public", "sample", ("id",))])

    GraphSQLRuntime.install(cache, registry)

    # First hit
    assert GraphSQLRuntime.get_plan("public.sample") is not None
    stats = GraphSQLRuntime.plan_stats()
    assert stats["hits"]["public.sample"] == 1

    # Miss
    assert GraphSQLRuntime.get_plan("public.other") is None
    stats = GraphSQLRuntime.plan_stats()
    assert stats["misses"]["public.other"] == 1
