from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LaneAddress:
    branch_id: UUID
    projection_hash: str

    def __post_init__(self) -> None:
        projection_hash = (self.projection_hash or "").strip()
        if not projection_hash:
            raise ValueError("projection_hash must be non-empty")
        object.__setattr__(self, "projection_hash", projection_hash)


@dataclass(frozen=True, slots=True)
class LaneMaterialization:
    lane: LaneAddress
    commit_id: UUID
    graph_hash_post: str | None = None
    object_instance_graph_id: UUID | None = None
    root_object_id: UUID | None = None
    head_version: int | None = None
    commit_payload: dict[str, object] | None = None
    emitted_at_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LaneMaterializationSource(Protocol):
    async def load_latest(self, *, lane: LaneAddress) -> LaneMaterialization | None:
        """Load the latest commit-backed materialization for a lane."""
        ...

    def watch_lane(
        self,
        *,
        lane: LaneAddress,
        include_initial: bool = True,
    ) -> AsyncIterator[LaneMaterialization]:
        """Stream commit-backed lane materializations as lane HEAD moves."""
        ...

