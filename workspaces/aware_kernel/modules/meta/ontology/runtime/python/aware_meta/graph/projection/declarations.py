from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectionObservableDeclaration:
    key: str
    kind: str
    is_default: bool
    description: str | None
    position: int


@dataclass(frozen=True, slots=True)
class ProjectionDeclaration:
    projection_name: str
    label: str | None
    description: str | None
    is_branchable: bool
    observables: tuple[ProjectionObservableDeclaration, ...]


__all__ = [
    "ProjectionDeclaration",
    "ProjectionObservableDeclaration",
]
