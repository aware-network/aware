from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import inspect
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_meta_service.local_sdk import (
    dispatch_local_meta_lane_commit_receipt,
    get_local_meta_lane_commit_receipt_bus,
)
from aware_utils.logging import logger


LaneKey = tuple[UUID, str]
LaneCommitReceiptSubscriber = Callable[
    [LaneCommitReceiptNotification],
    Awaitable[None] | None,
]


class LaneCommitReceiptBus:
    """Node-local receipt fanout with Meta-service-facade bridging."""

    _instance: "_NodeLaneCommitReceiptBus | None" = None

    @classmethod
    def instance(cls) -> "_NodeLaneCommitReceiptBus":
        if cls._instance is None:
            cls._instance = _NodeLaneCommitReceiptBus()
        return cls._instance


class _NodeLaneCommitReceiptBus:
    def __init__(self) -> None:
        self._watchers_any: set[
            Callable[[LaneCommitReceiptNotification], Awaitable[None] | None]
        ] = set()
        self._watchers_by_lane: dict[
            LaneKey,
            set[Callable[[LaneCommitReceiptNotification], Awaitable[None] | None]],
        ] = {}
        self._suppressed_meta_keys: set[tuple[UUID, str, UUID]] = set()

    def subscribe_all(
        self,
        *,
        watcher: Callable[[LaneCommitReceiptNotification], Awaitable[None] | None],
    ) -> Callable[[], None]:
        self._watchers_any.add(watcher)

        def _meta_watcher(notification: object) -> Awaitable[None] | None:
            if self._meta_key_suppressed(notification):
                return None
            node_notification = _node_lane_commit_receipt_notification(notification)
            if node_notification is None:
                return None
            return watcher(node_notification)

        unsubscribe_meta = get_local_meta_lane_commit_receipt_bus().subscribe_all(
            watcher=_meta_watcher
        )

        def _unsubscribe() -> None:
            self._watchers_any.discard(watcher)
            unsubscribe_meta()

        return _unsubscribe

    def subscribe_lane(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        watcher: Callable[[LaneCommitReceiptNotification], Awaitable[None] | None],
    ) -> Callable[[], None]:
        projection_hash = (projection_hash or "").strip()
        if not projection_hash:
            raise ValueError("subscribe_lane requires projection_hash")

        key = (branch_id, projection_hash)
        watchers = self._watchers_by_lane.setdefault(key, set())
        watchers.add(watcher)

        def _meta_watcher(notification: object) -> Awaitable[None] | None:
            if self._meta_key_suppressed(notification):
                return None
            node_notification = _node_lane_commit_receipt_notification(notification)
            if node_notification is None:
                return None
            return watcher(node_notification)

        unsubscribe_meta = get_local_meta_lane_commit_receipt_bus().subscribe_lane(
            branch_id=branch_id,
            projection_hash=projection_hash,
            watcher=_meta_watcher,
        )

        def _unsubscribe() -> None:
            watchers.discard(watcher)
            if not watchers:
                self._watchers_by_lane.pop(key, None)
            unsubscribe_meta()

        return _unsubscribe

    def dispatch(self, notification: object) -> None:
        node_notification = _node_lane_commit_receipt_notification(notification)
        if node_notification is None:
            return

        meta_key = _lane_commit_receipt_meta_key(node_notification)
        if meta_key is not None:
            self._suppressed_meta_keys.add(meta_key)
        self._dispatch_local(node_notification)
        dispatch_local_meta_lane_commit_receipt(node_notification)
        if meta_key is not None:
            self._schedule_suppression_clear(meta_key)

    def _dispatch_local(self, notification: LaneCommitReceiptNotification) -> None:
        projection_hash = (notification.projection_hash or "").strip()
        if not projection_hash:
            return
        watchers = set(self._watchers_any)
        watchers.update(
            self._watchers_by_lane.get((notification.branch_id, projection_hash), set())
        )
        for watcher in watchers:
            try:
                result = watcher(notification)
            except Exception as exc:
                logger.warning("[node-lane-commit-receipt-bus] watcher failed: %s", exc)
                continue
            if not inspect.isawaitable(result):
                continue
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning(
                    "[node-lane-commit-receipt-bus] No running loop; skipping async dispatch"
                )
                continue
            loop.create_task(_await_watcher(result=result))

    def _meta_key_suppressed(self, notification: object) -> bool:
        meta_key = _lane_commit_receipt_meta_key(notification)
        return meta_key is not None and meta_key in self._suppressed_meta_keys

    def _schedule_suppression_clear(self, key: tuple[UUID, str, UUID]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self._suppressed_meta_keys.discard(key)
            return
        loop.call_later(0.1, self._suppressed_meta_keys.discard, key)


def _node_lane_commit_receipt_notification(
    notification: object,
) -> LaneCommitReceiptNotification | None:
    if isinstance(notification, LaneCommitReceiptNotification):
        return notification
    model_dump = getattr(notification, "model_dump", None)
    if callable(model_dump):
        return LaneCommitReceiptNotification.model_validate(
            model_dump(mode="python", exclude_none=True)
        )
    return None


async def _await_watcher(*, result: Awaitable[None]) -> None:
    try:
        await result
    except Exception as exc:
        logger.warning("[node-lane-commit-receipt-bus] watcher failed: %s", exc)


def _lane_commit_receipt_meta_key(
    notification: object,
) -> tuple[UUID, str, UUID] | None:
    projection_hash = (getattr(notification, "projection_hash", None) or "").strip()
    if not projection_hash:
        return None
    branch_id = getattr(notification, "branch_id", None)
    commit_id = getattr(notification, "commit_id", None)
    if not isinstance(branch_id, UUID) or not isinstance(commit_id, UUID):
        return None
    return (branch_id, projection_hash, commit_id)


__all__ = [
    "LaneKey",
    "LaneCommitReceiptSubscriber",
    "LaneCommitReceiptBus",
]
