from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import inspect
from typing import ClassVar
from uuid import UUID

from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_environment_sdk import EnvironmentSdkCommitReceiptSource
from aware_utils.logging import logger


LaneKey = tuple[UUID, str]


class _ServiceHostEnvironmentLaneCommitReceiptBus:
    _instance: ClassVar["_ServiceHostEnvironmentLaneCommitReceiptBus | None"] = None

    def __init__(self) -> None:
        self._watchers_any: set[
            Callable[[LaneCommitReceiptNotification], Awaitable[None] | None]
        ] = set()
        self._watchers_by_lane: dict[
            LaneKey,
            set[Callable[[LaneCommitReceiptNotification], Awaitable[None] | None]],
        ] = {}

    @classmethod
    def instance(cls) -> "_ServiceHostEnvironmentLaneCommitReceiptBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe_all(
        self,
        *,
        watcher: Callable[
            [LaneCommitReceiptNotification],
            Awaitable[None] | None,
        ],
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
        watcher: Callable[
            [LaneCommitReceiptNotification],
            Awaitable[None] | None,
        ],
    ) -> Callable[[], None]:
        projection_hash = (projection_hash or "").strip()
        if not projection_hash:
            raise ValueError("subscribe_lane requires projection_hash")
        key = (branch_id, projection_hash)
        watchers = self._watchers_by_lane.setdefault(key, set())
        watchers.add(watcher)

        def _unsubscribe() -> None:
            watchers.discard(watcher)
            if not watchers:
                self._watchers_by_lane.pop(key, None)

        return _unsubscribe

    def dispatch(self, receipt: LaneCommitReceiptNotification) -> None:
        projection_hash = (receipt.projection_hash or "").strip()
        if not projection_hash:
            return
        watchers = set(self._watchers_any)
        watchers.update(
            self._watchers_by_lane.get((receipt.branch_id, projection_hash), set())
        )
        for watcher in watchers:
            try:
                result = watcher(receipt)
            except Exception as exc:
                logger.warning("[service-host-receipt-bus] watcher failed: %s", exc)
                continue
            if not inspect.isawaitable(result):
                continue
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning(
                    "[service-host-receipt-bus] No running loop; skipping async dispatch"
                )
                continue
            loop.create_task(_await_watcher(result=result))


async def _await_watcher(*, result: Awaitable[None]) -> None:
    try:
        await result
    except Exception as exc:
        logger.warning("[service-host-receipt-bus] watcher failed: %s", exc)


class ServiceHostEnvironmentCommitReceiptClient:
    """Service-local Environment receipt fanout backed by the ServiceHost bus."""

    async def ensure_interface_session_registered(self) -> None:
        return None

    def subscribe_lane_commit_receipts(
        self,
        *,
        watcher: Callable[
            [LaneCommitReceiptNotification],
            Awaitable[None] | None,
        ],
        branch_id: UUID | None = None,
        projection_hash: str | None = None,
    ) -> Callable[[], None]:
        if (branch_id is None) != (projection_hash is None):
            raise ValueError(
                "ServiceHost lane receipt subscription requires both branch_id "
                "and projection_hash, or neither."
            )
        if branch_id is None:
            return _ServiceHostEnvironmentLaneCommitReceiptBus.instance().subscribe_all(
                watcher=watcher
            )
        return _ServiceHostEnvironmentLaneCommitReceiptBus.instance().subscribe_lane(
            branch_id=branch_id,
            projection_hash=(projection_hash or "").strip(),
            watcher=watcher,
        )


def dispatch_service_host_lane_commit_receipt(
    receipt: LaneCommitReceiptNotification,
) -> None:
    _ServiceHostEnvironmentLaneCommitReceiptBus.instance().dispatch(receipt)


def build_service_host_environment_commit_receipt_source() -> (
    EnvironmentSdkCommitReceiptSource
):
    return EnvironmentSdkCommitReceiptSource(
        client=ServiceHostEnvironmentCommitReceiptClient(),
    )


__all__ = [
    "ServiceHostEnvironmentCommitReceiptClient",
    "build_service_host_environment_commit_receipt_source",
    "dispatch_service_host_lane_commit_receipt",
]
