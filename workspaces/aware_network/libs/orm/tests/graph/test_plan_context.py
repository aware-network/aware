from uuid import uuid4

from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.plan_cache import GraphPlan, PlanStep
from aware_orm.graph.plan_context import PlanContext


def test_plan_context_iterators():
    plan = GraphPlan(
        root_table_key="public.users",
        steps=(
            PlanStep(
                table_key="public.profiles",
                via_relationship_id=None,
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
    assert context.root_descriptor().table_name == "users"
    steps = list(context.iter_step_descriptors())
    assert steps[0][0].table_key == "public.profiles"
    assert steps[0][1].table_name == "profiles"
