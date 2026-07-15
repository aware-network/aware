from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

from aware_meta.receipts._lane_receipt_bus import LaneKey, LaneReceiptBus
from aware_meta.receipts.notifications import LaneActionExecutionReceiptNotification

LaneActionExecutionKey: TypeAlias = LaneKey
LaneActionExecutionReceiptSubscriber: TypeAlias = Callable[
    [LaneActionExecutionReceiptNotification],
    Awaitable[None] | None,
]


class LaneActionExecutionReceiptBus(
    LaneReceiptBus[LaneActionExecutionReceiptNotification]
):
    """In-process dispatch for canonical lane action execution receipts."""

    _log_label = "action-execution-receipt-bus"
    _notification_type = LaneActionExecutionReceiptNotification


__all__ = [
    "LaneActionExecutionKey",
    "LaneActionExecutionReceiptSubscriber",
    "LaneActionExecutionReceiptBus",
]
