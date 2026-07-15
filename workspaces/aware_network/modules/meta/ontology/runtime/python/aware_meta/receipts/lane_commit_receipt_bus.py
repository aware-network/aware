from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

from aware_meta.receipts._lane_receipt_bus import LaneKey, LaneReceiptBus
from aware_meta.receipts.notifications import LaneCommitReceiptNotification

LaneCommitReceiptSubscriber: TypeAlias = Callable[
    [LaneCommitReceiptNotification],
    Awaitable[None] | None,
]


class LaneCommitReceiptBus(LaneReceiptBus[LaneCommitReceiptNotification]):
    """In-process dispatch for canonical lane commit receipts."""

    _log_label = "receipt-bus"
    _notification_type = LaneCommitReceiptNotification


__all__ = [
    "LaneKey",
    "LaneCommitReceiptSubscriber",
    "LaneCommitReceiptBus",
]
