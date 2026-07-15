from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Awaitable, Callable, ClassVar
from uuid import UUID

from aware_utils.logging import logger

FanoutPullHintLaneKey = tuple[UUID, str]


@dataclass(frozen=True, slots=True)
class FanoutPullHintNotification:
    source_node_id: UUID | None
    branch_id: UUID | None
    projection_hash: str
    commit_id: UUID | None


FanoutPullHintSubscriber = Callable[
    [FanoutPullHintNotification],
    Awaitable[None] | None,
]


class FanoutPullHintBus:
    """Node-local dispatch for peer fanout pull hints.

    Intent:
    - Remote `fanout_notify_pull` notifications stay transport-only.
    - Internal consumers can observe that a peer advertised a newer lane head.
    - This bus MUST NOT be treated as equivalent to a local lane-head receipt.

    Contract:
    - Dispatch is best-effort and must never break the router.
    - Subscriptions are keyed by the canonical lane key: (branch_id, projection_hash).
    """

    _instance: ClassVar["FanoutPullHintBus | None"] = None

    def __init__(self) -> None:
        self._watchers_any: set[FanoutPullHintSubscriber] = set()
        self._watchers_by_lane: dict[
            FanoutPullHintLaneKey,
            set[FanoutPullHintSubscriber],
        ] = {}

    @classmethod
    def instance(cls) -> "FanoutPullHintBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe_all(
        self,
        *,
        watcher: FanoutPullHintSubscriber,
    ) -> Callable[[], None]:
        self._watchers_any.add(watcher)

        def _unsubscribe() -> None:
            self._watchers_any.discard(watcher)

        return _unsubscribe

    def subscribe_lane(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        watcher: FanoutPullHintSubscriber,
    ) -> Callable[[], None]:
        projection_hash = (projection_hash or "").strip()
        if not projection_hash:
            raise ValueError("subscribe_lane requires projection_hash")

        key: FanoutPullHintLaneKey = (branch_id, projection_hash)
        watchers = self._watchers_by_lane.setdefault(key, set())
        watchers.add(watcher)

        def _unsubscribe() -> None:
            watchers.discard(watcher)
            if not watchers:
                self._watchers_by_lane.pop(key, None)

        return _unsubscribe

    def dispatch(self, notification: object) -> None:
        if not isinstance(notification, FanoutPullHintNotification):
            return

        projection_hash = (notification.projection_hash or "").strip()
        if notification.branch_id is None or not projection_hash:
            return

        key: FanoutPullHintLaneKey = (notification.branch_id, projection_hash)
        watchers = set(self._watchers_any)
        watchers.update(self._watchers_by_lane.get(key, set()))
        if not watchers:
            return

        for watcher in watchers:
            try:
                result = watcher(notification)
            except Exception as exc:
                logger.warning("[fanout-hint-bus] watcher failed: %s", exc)
                continue
            if not inspect.isawaitable(result):
                continue
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning(
                    "[fanout-hint-bus] No running loop; skipping async hint dispatch"
                )
                continue
            loop.create_task(self._await_watcher(result=result))

    @staticmethod
    async def _await_watcher(*, result: Awaitable[None]) -> None:
        try:
            await result
        except Exception as exc:
            logger.warning("[fanout-hint-bus] watcher failed: %s", exc)
