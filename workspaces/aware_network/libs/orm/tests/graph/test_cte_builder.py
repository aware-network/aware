from uuid import uuid4

from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.plan_cache import GraphPlan, PlanStep
from aware_orm.graph.plan_context import PlanContext
from aware_orm.graph.cte_builder import CTEBuilder


def test_cte_builder_generates_aliases():
    plan = GraphPlan(
        root_table_key="public.users",
        steps=(
            PlanStep(
                table_key="public.profiles",
                via_relationship_id=None,
                join_condition="public.users.profile_id = public.profiles.id",
                projection_fields=("id", "name"),
            ),
        ),
    )
    registry = GraphConfigRegistry(
        [
            TableDescriptor(uuid4(), "public", "users", ("id", "profile_id")),
            TableDescriptor(uuid4(), "public", "profiles", ("id", "name")),
        ]
    )
    context = PlanContext(plan, registry)
    builder = CTEBuilder(context)
    ctes = builder.build()
    assert "cte_1" in ctes[0]
    assert "public.profiles" in ctes[0]
    assert "public.users.profile_id = public.profiles.id" in ctes[0]
