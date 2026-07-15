from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import AbstractContextManager, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, cast
from uuid import UUID

from aware_economy.meta_runtime import (
    EconomyMetaRuntimeLane,
    EconomyMetaRuntimeLaneBinder,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    require_service_ontology_replica_commit_sink,
)


@dataclass(frozen=True, slots=True)
class _CommittedLane:
    branch_id: UUID
    projection_hash: str
    actor_id: UUID | None


@dataclass(slots=True)
class _ReplicaMirroringLaneBinder(EconomyMetaRuntimeLaneBinder):
    inner: EconomyMetaRuntimeLaneBinder
    committed_lanes: set[_CommittedLane] = field(default_factory=set)

    def bind(
        self,
        *,
        projection: str,
        branch_id: UUID,
        actor_id: UUID | None = None,
    ) -> EconomyMetaRuntimeLane:
        normalized_projection = str(projection or "").strip()
        if not normalized_projection:
            raise ValueError("Economy committed lane projection must be non-empty")
        return _ReplicaMirroringLane(
            inner=self.inner.bind(
                projection=normalized_projection,
                branch_id=branch_id,
                actor_id=actor_id,
            ),
            owner=self,
            committed_lane=_CommittedLane(
                branch_id=branch_id,
                projection_hash=normalized_projection,
                actor_id=actor_id,
            ),
        )


@dataclass(frozen=True, slots=True)
class _ReplicaMirroringLane(EconomyMetaRuntimeLane):
    inner: EconomyMetaRuntimeLane
    owner: _ReplicaMirroringLaneBinder
    committed_lane: _CommittedLane

    @property
    def branch_id(self) -> UUID:
        return self.inner.branch_id

    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> AbstractContextManager[object]:
        @contextmanager
        def _activation() -> object:
            with self.inner.activate(commit=commit, publish=publish) as activated:
                yield activated
            if commit:
                self.owner.committed_lanes.add(self.committed_lane)

        return _activation()


@dataclass(frozen=True, slots=True)
class _MaterializationWithLaneBinder:
    inner: object
    runtime: EconomyMetaRuntimeLaneBinder

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)


@asynccontextmanager
async def mirror_economy_materialization_commits(
    *,
    materialization: object,
) -> AsyncIterator[object]:
    tracked = _ReplicaMirroringLaneBinder(
        inner=cast(
            EconomyMetaRuntimeLaneBinder,
            getattr(materialization, "runtime", None),
        )
    )
    try:
        yield _MaterializationWithLaneBinder(
            inner=materialization,
            runtime=tracked,
        )
    finally:
        if tracked.committed_lanes:
            sink = require_service_ontology_replica_commit_sink()
            for lane in sorted(
                tracked.committed_lanes,
                key=lambda value: (
                    str(value.branch_id),
                    value.projection_hash,
                    str(value.actor_id or ""),
                ),
            ):
                await sink.mirror_committed_lane(
                    branch_id=lane.branch_id,
                    projection_hash=lane.projection_hash,
                    actor_id=lane.actor_id,
                )


__all__ = ["mirror_economy_materialization_commits"]
