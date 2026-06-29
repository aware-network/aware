from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

from aware_meta.receipts._lane_receipt_bus import LaneKey, LaneReceiptBus
from aware_meta.receipts.notifications import LaneTurnStreamReceiptNotification

LaneTurnStreamKey: TypeAlias = LaneKey
LaneTurnStreamReceiptSubscriber: TypeAlias = Callable[
    [LaneTurnStreamReceiptNotification],
    Awaitable[None] | None,
]


class LaneTurnStreamReceiptBus(LaneReceiptBus[LaneTurnStreamReceiptNotification]):
    """In-process dispatch for canonical lane turn stream receipts."""

    _log_label = "turn-stream-receipt-bus"
    _notification_type = LaneTurnStreamReceiptNotification


__all__ = [
    "LaneTurnStreamKey",
    "LaneTurnStreamReceiptSubscriber",
    "LaneTurnStreamReceiptBus",
]
