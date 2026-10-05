"""Authored neutral GoalDependency contract; not generated ORM objects.

This module validates declarations only. It does not resolve endpoints, infer
edges, assess satisfaction, persist mutations, or authorize execution.
"""

from dataclasses import dataclass
from enum import StrEnum

from .identity import normalize_goal_tag, required_text, required_token, unique_tokens


class GoalDependencyRelation(StrEnum):
    REQUIRES_COMPLETION = "requires_completion"
    REQUIRES_ACCEPTANCE = "requires_acceptance"


@dataclass(frozen=True, slots=True)
class GoalRowCoordinate:
    goal_tag: str
    lane_key: str
    row_key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "goal_tag", normalize_goal_tag(self.goal_tag))
        for field in ("lane_key", "row_key"):
            object.__setattr__(self, field, required_token(getattr(self, field), field))


@dataclass(frozen=True, slots=True)
class GoalDependency:
    owner_goal_tag: str
    dependency_key: str
    dependent_lane_key: str
    dependent_row_key: str
    prerequisite_goal_tag: str
    prerequisite_lane_key: str
    prerequisite_row_key: str
    relation: GoalDependencyRelation
    reason: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in ("owner_goal_tag", "prerequisite_goal_tag"):
            object.__setattr__(self, field, normalize_goal_tag(getattr(self, field)))
        for field in (
            "dependency_key", "dependent_lane_key", "dependent_row_key",
            "prerequisite_lane_key", "prerequisite_row_key",
        ):
            object.__setattr__(self, field, required_token(getattr(self, field), field))
        if not isinstance(self.relation, GoalDependencyRelation):
            raise TypeError("relation must be GoalDependencyRelation")
        object.__setattr__(self, "reason", required_text(self.reason, "reason"))
        if not isinstance(self.evidence_refs, tuple):
            raise TypeError("evidence_refs must be a tuple")
        object.__setattr__(self, "evidence_refs", unique_tokens(self.evidence_refs, "evidence_refs"))
        if self.dependent == self.prerequisite:
            raise ValueError("GoalDependency cannot depend on its own row")

    @property
    def dependent(self) -> GoalRowCoordinate:
        return GoalRowCoordinate(self.owner_goal_tag, self.dependent_lane_key, self.dependent_row_key)

    @property
    def prerequisite(self) -> GoalRowCoordinate:
        return GoalRowCoordinate(self.prerequisite_goal_tag, self.prerequisite_lane_key, self.prerequisite_row_key)

    def to_wire(self) -> dict[str, object]:
        return {
            "owner_goal_tag": self.owner_goal_tag,
            "dependency_key": self.dependency_key,
            "dependent_lane_key": self.dependent_lane_key,
            "dependent_row_key": self.dependent_row_key,
            "prerequisite_goal_tag": self.prerequisite_goal_tag,
            "prerequisite_lane_key": self.prerequisite_lane_key,
            "prerequisite_row_key": self.prerequisite_row_key,
            "relation": self.relation.value,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
        }


def validate_dependency_set(dependencies: tuple[GoalDependency, ...]) -> None:
    """Reject duplicate declarations and cycles in the supplied bounded set.

    Missing endpoints remain unresolved, never deleted or treated as satisfied.
    A successful check makes no assertion about an unseen cross-Goal graph.
    """
    identities: set[tuple[str, str]] = set()
    edges: set[tuple[GoalRowCoordinate, GoalRowCoordinate, GoalDependencyRelation]] = set()
    adjacency: dict[GoalRowCoordinate, set[GoalRowCoordinate]] = {}
    for dependency in dependencies:
        identity = (dependency.owner_goal_tag, dependency.dependency_key)
        edge = (dependency.dependent, dependency.prerequisite, dependency.relation)
        if identity in identities or edge in edges:
            raise ValueError("duplicate GoalDependency identity or edge")
        identities.add(identity)
        edges.add(edge)
        adjacency.setdefault(dependency.dependent, set()).add(dependency.prerequisite)
    visiting: set[GoalRowCoordinate] = set()
    visited: set[GoalRowCoordinate] = set()

    def visit(row: GoalRowCoordinate) -> None:
        if row in visiting:
            raise ValueError("GoalDependency cycle in supplied declarations")
        if row in visited:
            return
        visiting.add(row)
        for prerequisite in adjacency.get(row, ()):
            visit(prerequisite)
        visiting.remove(row)
        visited.add(row)

    for row in adjacency:
        visit(row)
