from uuid import uuid4

from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.plan_cache import GraphPlan, PlanStep
from aware_orm.graph.plan_context import PlanContext
from aware_orm.graph.projection_builder import ProjectionBuilder


def test_projection_builder_outputs_json_fields():
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
    builder = ProjectionBuilder(context)

    root_proj = builder.build_root_projection()
    assert "json_build_object" in root_proj
    assert "roots.id" in root_proj

    step_proj = builder.build_step_projection()
    assert "json_agg" in step_proj[0]
    assert "cte_1" in step_proj[0]
    assert "public.profiles" not in step_proj[0]
