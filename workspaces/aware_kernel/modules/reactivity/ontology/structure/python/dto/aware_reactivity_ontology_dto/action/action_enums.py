from __future__ import annotations

# Standard
from enum import Enum


class ActionStatus(Enum):
    executing = "executing"
    handled_failure = "handled_failure"
    handled_success = "handled_success"
    requested = "requested"
    skipped = "skipped"


class ActionIntentStatus(Enum):
    requested = "requested"
    skipped = "skipped"
    superseded = "superseded"


class ActionExecutionStatus(Enum):
    accepted = "accepted"
    canceled = "canceled"
    created = "created"
    failed = "failed"
    rejected = "rejected"
    running = "running"
    succeeded = "succeeded"
    timed_out = "timed_out"


class ActionFeedbackStage(Enum):
    dispatch = "dispatch"
    execute = "execute"
    terminal = "terminal"


class ActionFeedbackStatus(Enum):
    accepted = "accepted"
    failed = "failed"
    rejected = "rejected"
    requested = "requested"
    responded = "responded"
    running = "running"
    skipped = "skipped"
    succeeded = "succeeded"
