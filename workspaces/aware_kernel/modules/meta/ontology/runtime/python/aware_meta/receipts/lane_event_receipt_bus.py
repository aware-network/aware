from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

from aware_meta.receipts._lane_receipt_bus import LaneKey, LaneReceiptBus
from aware_meta.receipts.notifications import LaneEventReceiptNotification

LaneEventKey: TypeAlias = LaneKey
LaneEventReceiptSubscriber: TypeAlias = Callable[
    [LaneEventReceiptNotification],
    Awaitable[None] | None,
]


class LaneEventReceiptBus(LaneReceiptBus[LaneEventReceiptNotification]):
    """In-process dispatch for canonical lane event receipts."""

    _log_label = "event-receipt-bus"
    _notification_type = LaneEventReceiptNotification


__all__ = [
    "LaneEventKey",
    "LaneEventReceiptSubscriber",
    "LaneEventReceiptBus",
]
