from __future__ import annotations

# Standard
from enum import Enum


class EventDeliveryMode(Enum):
    batched = "batched"
    immediate = "immediate"
    queued = "queued"
    scheduled = "scheduled"


class EventPriority(Enum):
    critical = "critical"
    deferred = "deferred"
    high = "high"
    low = "low"
    normal = "normal"


class EventScheduleStatus(Enum):
    active = "active"
    inactive = "inactive"


class EventStatus(Enum):
    handled_failure = "handled_failure"
    handled_success = "handled_success"
    handling = "handling"
    ignored = "ignored"
    raised = "raised"


class EventType(Enum):
    condition = "condition"
    manual = "manual"
    scheduled = "scheduled"
    system = "system"
    webhook = "webhook"
