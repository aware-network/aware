"""Graph plan cache primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID


@dataclass(frozen=True)
class PlanStep:
    """Single step within a GraphPlan (CTE alias, relationship metadata)."""

    table_key: str
    via_relationship_id: UUID | None
    uses_collection: bool = False
    join_condition: str | None = None
    projection_fields: tuple[str, ...] = field(default_factory=tuple)
    parent_table_key: str | None = None
    depth: int = 1


@dataclass(frozen=True)
class GraphPlan:
    root_table_key: str
    steps: tuple[PlanStep, ...] = field(default_factory=tuple)
    diagnostics: tuple[str, ...] = field(default_factory=tuple)
    root_projection_fields: tuple[str, ...] = field(default_factory=tuple)

    def with_step(self, step: PlanStep) -> "GraphPlan":
        return GraphPlan(
            root_table_key=self.root_table_key,
            steps=self.steps + (step,),
            diagnostics=self.diagnostics,
            root_projection_fields=self.root_projection_fields,
        )


class GraphPlanCache:
    """In-memory plan cache keyed by table key."""

    def __init__(self, plans: Iterable[GraphPlan] | None = None) -> None:
        self._by_table: dict[str, GraphPlan] = {}
        if plans:
            for plan in plans:
                self.register(plan)

    def register(self, plan: GraphPlan) -> None:
        self._by_table[plan.root_table_key] = plan

    def get(self, table_key: str) -> GraphPlan | None:
        return self._by_table.get(table_key)

    def require(self, table_key: str) -> GraphPlan:
        plan = self.get(table_key)
        if plan is None:
            raise KeyError(f"Graph plan missing for {table_key}")
        return plan

    def all(self) -> Iterable[GraphPlan]:
        return self._by_table.values()
