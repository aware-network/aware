"""Compile GraphPlan objects from configuration + overlay data."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List, Sequence
from uuid import UUID

from .config_registry import GraphConfigRegistry
from .plan_cache import GraphPlan, PlanStep


@dataclass(frozen=True)
class RelationshipDescriptor:
    """Minimal relationship metadata required for plan compilation."""

    canonical_relationship_id: UUID
    source_table_key: str
    target_table_key: str
    join_condition: str | None = None
    uses_collection: bool = False


class GraphPlanCompiler:
    """Compile deterministic GraphPlan instances using registry + overlay bridges."""

    def __init__(
        self,
        config_registry: GraphConfigRegistry,
        *,
        max_depth: int = 2,
        cycle_policy: str = "reject",
    ) -> None:
        self._config_registry = config_registry
        self._max_depth = max_depth
        self._cycle_policy = cycle_policy

    def compile_plan(
        self,
        root_table_key: str,
        relationships: Sequence[RelationshipDescriptor],
    ) -> GraphPlan:
        # Ensure root descriptor exists (raises if missing)
        self._config_registry.require(root_table_key)
        steps: List[PlanStep] = []
        diagnostics: List[str] = []

        relationships_by_source: dict[str, list[RelationshipDescriptor]] = defaultdict(list)
        for relationship in relationships:
            relationships_by_source[relationship.source_table_key].append(relationship)

        def walk(source_table_key: str, *, depth: int, path: tuple[str, ...]) -> None:
            if depth > self._max_depth:
                return
            for rel in relationships_by_source.get(source_table_key, []):
                if rel.target_table_key in path:
                    diagnostic = (
                        "cycle_detected:"
                        f"{'->'.join(path + (rel.target_table_key,))}:"
                        f"{rel.canonical_relationship_id}"
                    )
                    diagnostics.append(diagnostic)
                    if self._cycle_policy == "reject":
                        continue

                steps.append(
                    PlanStep(
                        table_key=rel.target_table_key,
                        via_relationship_id=rel.canonical_relationship_id,
                        uses_collection=bool(rel.uses_collection),
                        join_condition=rel.join_condition,
                        projection_fields=tuple(self._config_registry.require(rel.target_table_key).attributes),
                        parent_table_key=source_table_key,
                        depth=depth,
                    )
                )
                walk(rel.target_table_key, depth=depth + 1, path=path + (rel.target_table_key,))

        walk(root_table_key, depth=1, path=(root_table_key,))
        root_fields = tuple(self._config_registry.require(root_table_key).attributes)
        return GraphPlan(
            root_table_key=root_table_key,
            steps=tuple(steps),
            diagnostics=tuple(diagnostics),
            root_projection_fields=root_fields,
        )

    def compile_many(
        self,
        root_table_key: str,
        relationships: Iterable[RelationshipDescriptor],
    ) -> GraphPlan:
        rel_list = list(relationships)
        return self.compile_plan(root_table_key, rel_list)
