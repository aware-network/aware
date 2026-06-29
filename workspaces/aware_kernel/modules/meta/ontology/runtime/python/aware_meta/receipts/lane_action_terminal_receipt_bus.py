from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

from aware_meta.receipts._lane_receipt_bus import LaneKey, LaneReceiptBus
from aware_meta.receipts.notifications import LaneActionTerminalReceiptNotification

LaneActionTerminalKey: TypeAlias = LaneKey
LaneActionTerminalReceiptSubscriber: TypeAlias = Callable[
    [LaneActionTerminalReceiptNotification],
    Awaitable[None] | None,
]


class LaneActionTerminalReceiptBus(
    LaneReceiptBus[LaneActionTerminalReceiptNotification]
):
    """In-process dispatch for canonical lane action terminal receipts."""

    _log_label = "action-terminal-receipt-bus"
    _notification_type = LaneActionTerminalReceiptNotification


__all__ = [
    "LaneActionTerminalKey",
    "LaneActionTerminalReceiptSubscriber",
    "LaneActionTerminalReceiptBus",
]
