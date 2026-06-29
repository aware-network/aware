from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeAlias

from aware_meta.receipts._lane_receipt_bus import LaneKey, LaneReceiptBus
from aware_meta.receipts.notifications import LaneActionFeedbackReceiptNotification

LaneActionFeedbackKey: TypeAlias = LaneKey
LaneActionFeedbackReceiptSubscriber: TypeAlias = Callable[
    [LaneActionFeedbackReceiptNotification],
    Awaitable[None] | None,
]


class LaneActionFeedbackReceiptBus(
    LaneReceiptBus[LaneActionFeedbackReceiptNotification]
):
    """In-process dispatch for canonical lane action feedback receipts."""

    _log_label = "action-feedback-receipt-bus"
    _notification_type = LaneActionFeedbackReceiptNotification


__all__ = [
    "LaneActionFeedbackKey",
    "LaneActionFeedbackReceiptSubscriber",
    "LaneActionFeedbackReceiptBus",
]
