from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
import inspect
from typing import Awaitable, Callable, Protocol, cast
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)

DEFAULT_ENVIRONMENT_REACTIVITY_SUBSCRIBER_ID = "aware_reactivity.environment_fanout"


class EnvironmentCommitReceiptSource(Protocol):
    """Environment API/SDK fanout source for lane commit receipts."""

    def stream_commit_receipts(
        self,
        *,
        subscriber_id: str,
        resume_after_commit_id: UUID | None = None,
    ) -> AsyncIterator[LaneCommitReceiptNotification]: ...


class EnvironmentCommitReceiptSdkClient(Protocol):
    """Network SDK client that receives Environment lane receipt notifications."""

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
    """Adapts the Environment SDK callback fanout into Reactivity's source port."""

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


class ReactivityEnvironmentReceiptAuthority(Protocol):
    async def process_environment_commit_receipt(
        self,
        receipt: LaneCommitReceiptNotification,
    ) -> tuple[ActorReactivityBridgeEvent, ...]: ...


@dataclass(frozen=True, slots=True)
class ReactivityEnvironmentCommitOutcome:
    commit_id: UUID
    status: str
    semantic_events: tuple[ActorReactivityBridgeEvent, ...] = ()
    reason: str | None = None


@dataclass(slots=True)
class ReactivityEnvironmentCommitSubscriber:
    """Consumes Environment-owned commit fanout and resolves Reactivity policies."""

    source: EnvironmentCommitReceiptSource
    authority: ReactivityEnvironmentReceiptAuthority
    subscriber_id: str = DEFAULT_ENVIRONMENT_REACTIVITY_SUBSCRIBER_ID

    async def run(
        self,
        *,
        resume_after_commit_id: UUID | None = None,
        max_receipts: int | None = None,
    ) -> tuple[ReactivityEnvironmentCommitOutcome, ...]:
        outcomes: list[ReactivityEnvironmentCommitOutcome] = []
        receipt_stream = self.source.stream_commit_receipts(
            subscriber_id=self.subscriber_id,
            resume_after_commit_id=resume_after_commit_id,
        )
        try:
            async for receipt in receipt_stream:
                events = await self.authority.process_environment_commit_receipt(
                    receipt
                )
                outcomes.append(
                    ReactivityEnvironmentCommitOutcome(
                        commit_id=receipt.commit_id,
                        status="resolved" if events else "no_match",
                        semantic_events=events,
                        reason=None if events else "no_registered_policy_match",
                    )
                )
                if max_receipts is not None and len(outcomes) >= max_receipts:
                    break
        finally:
            aclose = cast(
                Callable[[], Awaitable[None]] | None,
                getattr(receipt_stream, "aclose", None),
            )
            if aclose is not None:
                await aclose()
        return tuple(outcomes)


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
    "DEFAULT_ENVIRONMENT_REACTIVITY_SUBSCRIBER_ID",
    "EnvironmentCommitReceiptSource",
    "EnvironmentCommitReceiptSdkClient",
    "EnvironmentSdkCommitReceiptSource",
    "ReactivityEnvironmentCommitOutcome",
    "ReactivityEnvironmentCommitSubscriber",
    "ReactivityEnvironmentReceiptAuthority",
]
