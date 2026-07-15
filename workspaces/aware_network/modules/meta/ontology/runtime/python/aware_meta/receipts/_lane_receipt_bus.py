from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import inspect
from typing import Any, ClassVar, Generic, Self, TypeAlias, TypeVar, cast
from uuid import UUID

from aware_utils.logging import logger

LaneKey: TypeAlias = tuple[UUID, str]
TNotification = TypeVar("TNotification")


class LaneReceiptBus(Generic[TNotification]):
    """In-process dispatch for canonical lane receipts."""

    _instance: ClassVar[Any] = None
    _log_label: ClassVar[str] = "receipt-bus"
    _notification_type: ClassVar[type[Any]]

    def __init__(self) -> None:
        self._watchers_any: set[
            Callable[[TNotification], Awaitable[None] | None]
        ] = set()
        self._watchers_by_lane: dict[
            LaneKey,
            set[Callable[[TNotification], Awaitable[None] | None]],
        ] = {}

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cast(Self, cls._instance)

    def subscribe_all(
        self,
        *,
        watcher: Callable[[TNotification], Awaitable[None] | None],
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
        watcher: Callable[[TNotification], Awaitable[None] | None],
    ) -> Callable[[], None]:
        projection_hash = (projection_hash or "").strip()
        if not projection_hash:
            raise ValueError("subscribe_lane requires projection_hash")

        key: LaneKey = (branch_id, projection_hash)
        watchers = self._watchers_by_lane.setdefault(key, set())
        watchers.add(watcher)

        def _unsubscribe() -> None:
            watchers.discard(watcher)
            if not watchers:
                self._watchers_by_lane.pop(key, None)

        return _unsubscribe

    def dispatch(self, notification: object) -> None:
        if not isinstance(notification, self._notification_type):
            return

        typed_notification = cast(TNotification, notification)
        raw_projection_hash = getattr(notification, "projection_hash", None)
        projection_hash = (
            str(raw_projection_hash).strip()
            if raw_projection_hash is not None
            else ""
        )
        branch_id = getattr(notification, "branch_id", None)
        if branch_id is None or not projection_hash:
            return

        key: LaneKey = (branch_id, projection_hash)
        watchers = set(self._watchers_any)
        watchers.update(self._watchers_by_lane.get(key, set()))
        if not watchers:
            return

        for watcher in watchers:
            try:
                result = watcher(typed_notification)
            except Exception as exc:
                logger.warning("[%s] watcher failed: %s", self._log_label, exc)
                continue
            if not inspect.isawaitable(result):
                continue
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning(
                    "[%s] No running loop; skipping async dispatch",
                    self._log_label,
                )
                continue
            loop.create_task(self._await_watcher(result=result))

    async def _await_watcher(self, *, result: Awaitable[None]) -> None:
        try:
            await result
        except Exception as exc:
            logger.warning("[%s] watcher failed: %s", self._log_label, exc)


__all__ = [
    "LaneKey",
    "LaneReceiptBus",
]
