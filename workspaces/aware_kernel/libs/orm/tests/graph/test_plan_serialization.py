# @code-under-test: ../../aware_orm/graph/serialization.py

from __future__ import annotations

from uuid import uuid4

from aware_orm.graph.plan_cache import GraphPlan, PlanStep
from aware_orm.graph.serialization import deserialize_plans, serialize_plans, sha256_hex


def test_serialize_and_deserialize_round_trip():
    plan = GraphPlan(
        root_table_key="public.users",
        steps=(
            PlanStep(
                "public.profiles",
                uuid4(),
                uses_collection=False,
                join_condition="public.users.profile_id = public.profiles.id",
                projection_fields=("id", "name"),
            ),
        ),
        diagnostics=("ok",),
        root_projection_fields=("id", "profile_id"),
    )
    payload = serialize_plans([plan])
    restored = deserialize_plans(payload)
    assert restored[0].root_table_key == plan.root_table_key
    assert restored[0].diagnostics == plan.diagnostics
    restored_step = restored[0].steps[0]
    assert restored_step.table_key == plan.steps[0].table_key
    assert restored_step.join_condition == plan.steps[0].join_condition
    assert restored_step.projection_fields == plan.steps[0].projection_fields
    assert restored_step.parent_table_key == plan.steps[0].parent_table_key
    assert restored_step.depth == plan.steps[0].depth
    assert restored[0].root_projection_fields == plan.root_projection_fields


def test_sha256_hex_consistent():
    plan = GraphPlan(root_table_key="public.users")
    payload = serialize_plans([plan])
    digest = sha256_hex(payload)
    assert len(digest) == 64
