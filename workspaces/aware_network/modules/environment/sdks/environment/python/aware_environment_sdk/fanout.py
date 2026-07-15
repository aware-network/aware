from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
import inspect
from typing import Protocol
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)


class EnvironmentCommitReceiptSource(Protocol):
    """Environment SDK fanout source for canonical lane commit receipts."""

    def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: UUID | None = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]: ...


class EnvironmentCommitReceiptSdkClient(Protocol):
    """Environment SDK client port that receives lane commit receipt fanout."""

    def subscribe_lane_commit_receipts(
        self,
        *,
        watcher: Callable[
            [LaneCommitReceiptNotification],
            Awaitable[None] | None,
        ],
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> Callable[[], None]: ...


@dataclass(frozen=True, slots=True)
class EnvironmentSdkCommitReceiptSource:
    """Adapts Environment SDK callback fanout into an async receipt stream."""

    client: EnvironmentCommitReceiptSdkClient
    branch_id: UUID | None = None
    projection_hash: str | None = None

    def __post_init__(self) -> None:
        if (self.branch_id is None) != (self.projection_hash is None):
            raise ValueError(
                "Environment SDK receipt source requires both branch_id and "
                "projection_hash, or neither."
            )
        projection_hash = (self.projection_hash or "").strip()
        if self.branch_id is not None and not projection_hash:
            raise ValueError(
                "Environment SDK receipt source requires non-empty projection_hash."
            )
        object.__setattr__(self, "projection_hash", projection_hash or None)

    async def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: UUID | None = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]:
        _ = subscriber_id
        queue: asyncio.Queue[LaneCommitReceiptNotification] = asyncio.Queue()
        closed = False
        resume_seen = resume_after_commit_id is None

        async def _watcher(receipt: LaneCommitReceiptNotification) -> None:
            nonlocal resume_seen
            if closed or not self._matches_lane(receipt):
                return
            if not resume_seen:
                resume_seen = receipt.commit_id == resume_after_commit_id
                return
            await queue.put(receipt)

        unsubscribe = self.client.subscribe_lane_commit_receipts(
            watcher=_watcher,
            branch_id=self.branch_id,
            projection_hash=self.projection_hash,
        )
        try:
            await _ensure_environment_sdk_notifications_started(self.client)
            while True:
                yield await queue.get()
        finally:
            closed = True
            unsubscribe()

    def _matches_lane(self, receipt: LaneCommitReceiptNotification) -> bool:
        if self.branch_id is None:
            return True
        return (
            receipt.branch_id == self.branch_id
            and (receipt.projection_hash or "").strip() == self.projection_hash
        )


async def _ensure_environment_sdk_notifications_started(
    client: EnvironmentCommitReceiptSdkClient,
) -> None:
    ensure_registered = getattr(client, "ensure_interface_session_registered", None)
    if not callable(ensure_registered):
        return
    result = ensure_registered()
    if inspect.isawaitable(result):
        await result


__all__ = [
    "EnvironmentCommitReceiptSdkClient",
    "EnvironmentCommitReceiptSource",
    "EnvironmentSdkCommitReceiptSource",
]
