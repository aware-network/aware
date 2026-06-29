from __future__ import annotations

# Standard
from enum import Enum


class ActionIntentStatus(Enum):
    """Canonical action intent status tokens."""

    requested = "requested"
    skipped = "skipped"
    superseded = "superseded"


class ActionExecutionStatus(Enum):
    """Canonical action execution status tokens."""

    accepted = "accepted"
    canceled = "canceled"
    created = "created"
    failed = "failed"
    rejected = "rejected"
    running = "running"
    succeeded = "succeeded"
    timed_out = "timed_out"


class ActionFeedbackStage(Enum):
    """
    Canonical lifecycle stage emitted by reactivity action feedback.
    Notes:
    - v0 emitters currently produce `dispatch` and `execute`.
    - `terminal` aligns feedback with the ontology-backed lifecycle rail.
    - `stream` and `finalize` remain compatibility tokens while callers migrate.
    """

    dispatch = "dispatch"
    execute = "execute"
    terminal = "terminal"
    stream = "stream"
    finalize = "finalize"


class ActionFeedbackStatus(Enum):
    """Canonical progressive execution feedback status tokens."""

    accepted = "accepted"
    failed = "failed"
    rejected = "rejected"
    requested = "requested"
    running = "running"
    responded = "responded"
    skipped = "skipped"
    succeeded = "succeeded"


class ActionTerminalStatus(Enum):
    """Canonical action execution terminal status tokens."""

    succeeded = "succeeded"
    skipped = "skipped"
    failed = "failed"
    timed_out = "timed_out"
    canceled = "canceled"
