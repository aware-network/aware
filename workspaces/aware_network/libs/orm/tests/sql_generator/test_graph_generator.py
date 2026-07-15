from __future__ import annotations

from uuid import uuid4

import pytest

from aware_orm.graph.config_registry import GraphConfigRegistry, TableDescriptor
from aware_orm.graph.plan_cache import GraphPlan, PlanStep
from aware_orm.query.graph_spec import (
    GraphRetrievalContract,
    GraphRetrievalContractError,
    GraphSpec,
    UnsupportedGraphBackendError,
)


def test_graph_spec_rejects_unsupported_backend() -> None:
    with pytest.raises(UnsupportedGraphBackendError, match="not supported"):
        GraphSpec().validate_backend("sqlite")


def test_graph_spec_rejects_plan_deeper_than_declared_depth() -> None:
    plan = GraphPlan(
        root_table_key="public.users",
        steps=(
            PlanStep(
                table_key="public.profiles",
                via_relationship_id=None,
                parent_table_key="public.users",
                depth=1,
            ),
            PlanStep(
                table_key="public.avatars",
                via_relationship_id=None,
                parent_table_key="public.profiles",
                depth=2,
            ),
        ),
    )
    registry = GraphConfigRegistry(
        [
            TableDescriptor(uuid4(), "public", "users", ("id",)),
            TableDescriptor(uuid4(), "public", "profiles", ("id",)),
            TableDescriptor(uuid4(), "public", "avatars", ("id",)),
        ]
    )

    with pytest.raises(GraphRetrievalContractError, match="exceeds GraphSpec max_depth"):
        GraphSpec(max_depth=1).validate_contract(
            GraphRetrievalContract.from_plan(plan, registry, graph_spec=GraphSpec(max_depth=2))
        )
