# @code-under-test: ../../aware_orm/graph/config_registry.py
# @code-under-test: ../../aware_orm/graph/overlay_bridge_registry.py
# @code-under-test: ../../aware_orm/graph/plan_cache.py
# @code-under-test: ../../aware_orm/graph/plan_compiler.py
# @code-under-test: ../../aware_orm/graph/query_executor.py

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID, uuid4

import pytest

from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.plan_cache import GraphPlan, GraphPlanCache, PlanStep
from aware_orm.graph.plan_compiler import GraphPlanCompiler, RelationshipDescriptor
from aware_orm.graph.query_executor import GraphQueryExecutor, PlanAwareGenerator


def test_config_registry_basic_operations():
    descriptor = TableDescriptor(uuid4(), "public", "users", ("id", "name"))
    registry = GraphConfigRegistry([descriptor])
    assert registry.require("public.users").table_name == "users"
    with pytest.raises(KeyError):
        registry.require("missing.table")


def test_plan_cache_register_and_retrieve():
    plan = GraphPlan(
        root_table_key="public.users",
        steps=(
            PlanStep(
                "public.profiles",
                None,
                join_condition="public.users.profile_id = public.profiles.id",
                projection_fields=("id", "name"),
            ),
        ),
        root_projection_fields=("id", "profile_id"),
    )
    cache = GraphPlanCache([plan])
    assert cache.require("public.users").steps[0].table_key == "public.profiles"
    assert cache.require("public.users").steps[0].projection_fields == ("id", "name")


def test_plan_compiler_compiles_steps_from_relationship_descriptors():
    registry = GraphConfigRegistry(
        [
            TableDescriptor(uuid4(), "public", "users", ("id", "profile_id")),
            TableDescriptor(uuid4(), "public", "profiles", ("id", "name")),
        ]
    )
    canonical_id = uuid4()
    rel = RelationshipDescriptor(
        canonical_relationship_id=canonical_id,
        source_table_key="public.users",
        target_table_key="public.profiles",
        join_condition="public.users.profile_id = public.profiles.id",
    )
    compiler = GraphPlanCompiler(registry)
    plan = compiler.compile_plan("public.users", [rel])
    assert plan.steps[0].via_relationship_id == canonical_id
    assert plan.diagnostics == ()
    assert plan.steps[0].projection_fields == ("id", "name")
    assert plan.steps[0].join_condition == "public.users.profile_id = public.profiles.id"
    assert plan.steps[0].parent_table_key == "public.users"
    assert plan.steps[0].depth == 1
    assert plan.root_projection_fields == ("id", "profile_id")


class StubGenerator(PlanAwareGenerator):
    def __init__(self, plan: GraphPlan):
        self.plan = plan

    def build_select_by_id(self, obj_id: UUID) -> tuple[str, tuple[Any, ...]]:
        return ("SELECT graph FROM stub", (obj_id,))

    def build_select_many(self, limit: int = 10, offset: int = 0) -> tuple[str, tuple[Any, ...]]:
        return ("SELECT list FROM stub", (limit, offset))


@dataclass
class StubSession:
    rows: Iterable[dict[str, Any]]

    async def execute_query(self, sql: str, *params: Any):
        self.last_sql = sql
        self.last_params = params
        return list(self.rows)


def stub_generator_factory(plan: GraphPlan) -> StubGenerator:
    return StubGenerator(plan)


def hydrate_single(rows: Iterable[dict[str, Any]], plan: GraphPlan):
    return {"plan_root": plan.root_table_key, "rows": list(rows)}


@pytest.mark.asyncio
async def test_graph_query_executor_fetch_by_id():
    plan = GraphPlan(root_table_key="public.users", steps=())
    cache = GraphPlanCache([plan])
    executor = GraphQueryExecutor(cache)
    session = StubSession([{"graph": {"id": "1"}}])
    result = await executor.fetch_by_id(session, "public.users", uuid4(), stub_generator_factory, hydrate_single)
    assert result["plan_root"] == "public.users"
    assert session.last_sql == "SELECT graph FROM stub"


@pytest.mark.asyncio
async def test_graph_query_executor_fetch_list():
    plan = GraphPlan(root_table_key="public.users", steps=())
    cache = GraphPlanCache([plan])
    executor = GraphQueryExecutor(cache)
    session = StubSession([{"graph": []}])
    result = await executor.fetch_list(
        session,
        "public.users",
        stub_generator_factory,
        hydrate_single,
        limit=5,
        offset=2,
    )
    assert session.last_params == (5, 2)
    assert result["rows"] == [{"graph": []}]
