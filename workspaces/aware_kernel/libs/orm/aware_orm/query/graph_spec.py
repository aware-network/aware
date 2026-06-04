from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from aware_orm.filters import EqFilter
from aware_orm.graph.config_registry import GraphConfigRegistry
from aware_orm.graph.plan_cache import GraphPlan, PlanStep


GraphCardinality = Literal["one", "many"]
GraphCyclePolicy = Literal["reject", "skip"]


class GraphRetrievalContractError(ValueError):
    """Raised when a GraphSpec cannot be honored by the current graph plan."""


class UnsupportedGraphBackendError(GraphRetrievalContractError):
    """Raised when a backend is not supported by the GraphSQL emitter."""


@dataclass(frozen=True)
class GraphScopeFilter:
    """Metadata-bound equality scope applied to the graph root table."""

    column: str
    value: Any

    def __post_init__(self) -> None:
        if not self.column:
            raise ValueError("GraphScopeFilter column is required")

    def to_filter(self) -> EqFilter:
        return EqFilter(column=self.column, value=self.value)


@dataclass(frozen=True)
class GraphInclude:
    """Declared relationship include in a graph retrieval contract."""

    path: str
    table_key: str
    cardinality: GraphCardinality
    children: tuple["GraphInclude", ...] = ()

    @property
    def depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(child.depth for child in self.children)


@dataclass(frozen=True)
class GraphSpec:
    """
    Public graph retrieval contract.

    `aware-orm` currently emits GraphSQL through PostgreSQL JSON functions.
    Unsupported backends fail fast; SQLite/default reads use non-eager row
    queries through QueryMixin until a backend-specific graph emitter lands.
    """

    max_depth: int = 2
    cycle_policy: GraphCyclePolicy = "reject"
    identity_map_reuse: bool = True
    supported_backends: tuple[str, ...] = ("postgres", "postgresql")
    branch_id: Any | None = None
    branch_column: str = "branch_id"
    projection_scope: tuple[GraphScopeFilter, ...] = ()

    def __post_init__(self) -> None:
        if self.max_depth < 0:
            raise ValueError("GraphSpec max_depth must be non-negative")
        if self.cycle_policy not in {"reject", "skip"}:
            raise ValueError("GraphSpec cycle_policy must be 'reject' or 'skip'")
        object.__setattr__(
            self,
            "supported_backends",
            tuple(backend.strip().lower() for backend in self.supported_backends if backend.strip()),
        )
        object.__setattr__(self, "projection_scope", tuple(self.projection_scope))

    def validate_backend(self, backend_name: str | None) -> None:
        backend = (backend_name or "").strip().lower()
        if backend and backend in self.supported_backends:
            return
        raise UnsupportedGraphBackendError(
            f"Graph retrieval is not supported for backend {backend_name!r}; "
            f"supported backends: {', '.join(self.supported_backends)}"
        )

    def root_scope_filters(self) -> tuple[EqFilter, ...]:
        filters: list[EqFilter] = []
        if self.branch_id is not None:
            filters.append(EqFilter(column=self.branch_column, value=self.branch_id))
        filters.extend(scope_filter.to_filter() for scope_filter in self.projection_scope)
        return tuple(filters)

    def validate_contract(self, contract: "GraphRetrievalContract") -> None:
        if contract.max_depth > self.max_depth:
            raise GraphRetrievalContractError(
                f"Graph plan depth {contract.max_depth} exceeds GraphSpec max_depth {self.max_depth}"
            )
        if self.cycle_policy == "reject" and contract.has_cycle:
            raise GraphRetrievalContractError("Graph plan contains a cycle and GraphSpec cycle_policy is reject")


@dataclass(frozen=True)
class GraphRetrievalContract:
    """Resolved graph retrieval contract derived from a GraphPlan."""

    root_table_key: str
    includes: tuple[GraphInclude, ...]
    max_depth: int
    has_cycle: bool
    identity_map_reuse: bool
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_plan(
        cls,
        plan: GraphPlan,
        registry: GraphConfigRegistry,
        *,
        graph_spec: GraphSpec | None = None,
    ) -> "GraphRetrievalContract":
        spec = graph_spec or GraphSpec()
        steps_by_parent: dict[str, list[PlanStep]] = {}
        for step in plan.steps:
            parent = step.parent_table_key or plan.root_table_key
            steps_by_parent.setdefault(parent, []).append(step)

        has_cycle = False

        def build(parent_table_key: str, *, prefix: str, path: tuple[str, ...]) -> tuple[GraphInclude, ...]:
            nonlocal has_cycle
            includes: list[GraphInclude] = []
            for step in steps_by_parent.get(parent_table_key, []):
                descriptor = registry.require(step.table_key)
                child_path = f"{prefix}.{descriptor.table_name}" if prefix else descriptor.table_name
                if step.table_key in path:
                    has_cycle = True
                    if spec.cycle_policy == "reject":
                        continue
                children = build(step.table_key, prefix=child_path, path=path + (step.table_key,))
                includes.append(
                    GraphInclude(
                        path=child_path,
                        table_key=step.table_key,
                        cardinality="many" if step.uses_collection else "one",
                        children=children,
                    )
                )
            return tuple(includes)

        includes = build(plan.root_table_key, prefix="", path=(plan.root_table_key,))
        max_depth = max((include.depth for include in includes), default=0)
        contract = cls(
            root_table_key=plan.root_table_key,
            includes=includes,
            max_depth=max_depth,
            has_cycle=has_cycle or any(diagnostic.startswith("cycle_detected:") for diagnostic in plan.diagnostics),
            identity_map_reuse=spec.identity_map_reuse,
            diagnostics=plan.diagnostics,
        )
        spec.validate_contract(contract)
        return contract


__all__ = [
    "GraphCardinality",
    "GraphCyclePolicy",
    "GraphInclude",
    "GraphRetrievalContract",
    "GraphRetrievalContractError",
    "GraphScopeFilter",
    "GraphSpec",
    "UnsupportedGraphBackendError",
]
