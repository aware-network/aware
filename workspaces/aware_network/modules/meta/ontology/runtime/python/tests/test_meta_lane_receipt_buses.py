from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Protocol, cast
from uuid import UUID, uuid4

import pytest
from aware_meta.receipts.notifications import (
    LaneActionExecutionReceiptNotification,
    LaneActionFeedbackReceiptNotification,
    LaneActionTerminalReceiptNotification,
    LaneCommitReceiptNotification,
    LaneEventReceiptNotification,
    LaneTurnStreamReceiptNotification,
)
from aware_meta.receipts import (
    LaneActionExecutionReceiptBus,
    LaneActionFeedbackReceiptBus,
    LaneActionTerminalReceiptBus,
    LaneCommitReceiptBus,
    LaneEventReceiptBus,
    LaneTurnStreamReceiptBus,
)


def _branch_id() -> UUID:
    return uuid4()


def _projection_hash() -> str:
    return "f" * 64


def _commit_receipt() -> LaneCommitReceiptNotification:
    return LaneCommitReceiptNotification(
        branch_id=_branch_id(),
        projection_hash=_projection_hash(),
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )


def _event_receipt() -> LaneEventReceiptNotification:
    return LaneEventReceiptNotification(
        branch_id=_branch_id(),
        projection_hash=_projection_hash(),
        event_id=uuid4(),
        event_type="reactivity.action.requested",
        source="actor_subscription",
        created_at_unix_ms=1,
        commit_id=uuid4(),
    )


def _action_execution_receipt() -> LaneActionExecutionReceiptNotification:
    return LaneActionExecutionReceiptNotification(
        branch_id=_branch_id(),
        projection_hash=_projection_hash(),
        action_execution_id=uuid4(),
        event_id=uuid4(),
        event_type="reactivity.action.requested",
        source="actor_subscription",
        created_at_unix_ms=1,
        commit_id=uuid4(),
    )


def _action_feedback_receipt() -> LaneActionFeedbackReceiptNotification:
    return LaneActionFeedbackReceiptNotification(
        branch_id=_branch_id(),
        projection_hash=_projection_hash(),
        action_execution_id=uuid4(),
        event_id=uuid4(),
        sequence=0,
        created_at_unix_ms=1,
        stage="execute",
        status="running",
    )


def _action_terminal_receipt() -> LaneActionTerminalReceiptNotification:
    return LaneActionTerminalReceiptNotification(
        branch_id=_branch_id(),
        projection_hash=_projection_hash(),
        action_execution_id=uuid4(),
        event_id=uuid4(),
        terminal_status="succeeded",
        handled=True,
        created_at_unix_ms=1,
    )


def _turn_stream_receipt() -> LaneTurnStreamReceiptNotification:
    return LaneTurnStreamReceiptNotification(
        branch_id=_branch_id(),
        projection_hash=_projection_hash(),
        service="inference",
        inference_request_id=uuid4(),
        created_at_unix_ms=1,
        stream_kind="content_delta",
    )


class _ReceiptBus(Protocol):
    def subscribe_all(self, *, watcher: object) -> Callable[[], None]: ...

    def dispatch(self, notification: object) -> None: ...


_ReceiptCase = tuple[str, Callable[[], object], Callable[[], object]]


_CASES: tuple[_ReceiptCase, ...] = (
    ("commit", LaneCommitReceiptBus, _commit_receipt),
    ("event", LaneEventReceiptBus, _event_receipt),
    ("action_execution", LaneActionExecutionReceiptBus, _action_execution_receipt),
    ("action_feedback", LaneActionFeedbackReceiptBus, _action_feedback_receipt),
    ("action_terminal", LaneActionTerminalReceiptBus, _action_terminal_receipt),
    ("turn_stream", LaneTurnStreamReceiptBus, _turn_stream_receipt),
)


def test_meta_lane_receipt_buses_are_meta_owned() -> None:
    assert LaneCommitReceiptBus.__module__ == (
        "aware_meta.receipts.lane_commit_receipt_bus"
    )
    assert LaneEventReceiptBus.__module__ == (
        "aware_meta.receipts.lane_event_receipt_bus"
    )
    assert LaneActionExecutionReceiptBus.__module__ == (
        "aware_meta.receipts.lane_action_execution_receipt_bus"
    )


@pytest.mark.parametrize(
    ("_label", "bus_factory", "receipt_factory"),
    _CASES,
    ids=[case[0] for case in _CASES],
)
def test_meta_lane_receipt_buses_dispatch_sync_watchers_without_event_loop(
    _label: str,
    bus_factory: Callable[[], object],
    receipt_factory: Callable[[], object],
) -> None:
    bus = cast(_ReceiptBus, bus_factory())
    received: list[object] = []

    def _watcher(notification: object) -> None:
        received.append(notification)

    bus.subscribe_all(watcher=_watcher)
    receipt = receipt_factory()
    bus.dispatch(receipt)

    assert received == [receipt]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("_label", "bus_factory", "receipt_factory"),
    _CASES,
    ids=[case[0] for case in _CASES],
)
async def test_meta_lane_receipt_buses_dispatch_async_watchers_with_event_loop(
    _label: str,
    bus_factory: Callable[[], object],
    receipt_factory: Callable[[], object],
) -> None:
    bus = cast(_ReceiptBus, bus_factory())
    done = asyncio.Event()

    async def _watcher(_notification: object) -> None:
        done.set()

    bus.subscribe_all(watcher=_watcher)
    bus.dispatch(receipt_factory())
    await asyncio.wait_for(done.wait(), timeout=0.2)
