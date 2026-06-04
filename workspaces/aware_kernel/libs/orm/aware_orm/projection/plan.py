"""Projection plan primitives (OIG → SQL index materialization).

Contract (canonical-only):
- OIG commits remain SSOT; SQL tables are rebuildable projections for retrieval.
- Projection plans are *derived metadata*, compiled from the SQL-lowered OCG + OPG.
- Plans must be deterministic and safe to rebuild/reinstall.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal
from uuid import UUID


ProjectionDialect = Literal["sqlite", "postgres"]

ProjectionColumnSource = Literal[
    # Primary key id from ClassInstance.id
    "id",
    # Lane scope (from projection context)
    "branch_id",
    "projection_hash",
    # Scalar attribute value from AttributeValue trees (AttributeConfigId)
    "attribute",
    # FK value derived from relationship edges (RelationshipId + direction)
    "fk_attribute",
]


@dataclass(frozen=True)
class ProjectionColumnPlan:
    column_name: str
    source: ProjectionColumnSource
    attribute_config_id: UUID | None = None
    relationship_id: UUID | None = None
    direction: Literal["forward", "reverse"] | None = None
    sql_type_hint: Literal["TEXT", "INTEGER", "REAL", "BLOB"] | None = None
    nullable: bool = True


@dataclass(frozen=True)
class ProjectionAssociationPlan:
    """Association / join-table projection derived from relationship edges."""

    association_table_key: str
    relationship_id: UUID
    source_fk_column: str
    target_fk_column: str


@dataclass(frozen=True)
class ProjectionTablePlan:
    table_key: str
    class_config_id: UUID | None = None
    primary_key: tuple[str, ...] = field(default_factory=tuple)
    columns: tuple[ProjectionColumnPlan, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProjectionPlan:
    projection_hash: str
    opg_name: str
    dialect: ProjectionDialect
    tables: tuple[ProjectionTablePlan, ...] = field(default_factory=tuple)
    associations: tuple[ProjectionAssociationPlan, ...] = field(default_factory=tuple)


class ProjectionPlanCache:
    """In-memory cache keyed by (dialect, projection_hash)."""

    def __init__(self, plans: Iterable[ProjectionPlan] | None = None) -> None:
        self._by_key: dict[tuple[str, str], ProjectionPlan] = {}
        if plans:
            for plan in plans:
                self.register(plan)

    def register(self, plan: ProjectionPlan) -> None:
        key = (plan.dialect, plan.projection_hash)
        self._by_key[key] = plan

    def get(self, *, dialect: ProjectionDialect, projection_hash: str) -> ProjectionPlan | None:
        return self._by_key.get((dialect, projection_hash))

    def require(self, *, dialect: ProjectionDialect, projection_hash: str) -> ProjectionPlan:
        plan = self.get(dialect=dialect, projection_hash=projection_hash)
        if plan is None:
            raise KeyError(f"ProjectionPlan missing for {dialect}:{projection_hash}")
        return plan

    def all(self) -> Iterable[ProjectionPlan]:
        return self._by_key.values()


__all__ = [
    "ProjectionAssociationPlan",
    "ProjectionColumnPlan",
    "ProjectionColumnSource",
    "ProjectionDialect",
    "ProjectionPlan",
    "ProjectionPlanCache",
    "ProjectionTablePlan",
]
