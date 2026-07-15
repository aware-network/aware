from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol
from uuid import UUID


class IdentityMetaRuntimeLane(Protocol):
    @property
    def branch_id(self) -> UUID: ...

    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> AbstractContextManager[object]: ...


class IdentityMetaRuntimeLaneBinder(Protocol):
    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> IdentityMetaRuntimeLane: ...


__all__ = [
    "IdentityMetaRuntimeLane",
    "IdentityMetaRuntimeLaneBinder",
]
