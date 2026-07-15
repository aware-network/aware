from __future__ import annotations

# Standard
from enum import Enum


class SubscriptionActivationStatus(Enum):
    ready = "ready"
    blocked_by_route = "blocked_by_route"
    done = "done"
    skipped = "skipped"


class SubscriptionAddressingPolicy(Enum):
    any = "any"
    routed_only = "routed_only"
    unrouted_only = "unrouted_only"


class SubscriptionFilterMode(Enum):
    all_instances = "all_instances"
    owned_instances = "owned_instances"
    role_instances = "role_instances"
    specific_instances = "specific_instances"
    tagged_instances = "tagged_instances"


class SubscriptionStatus(Enum):
    active = "active"
    disabled = "disabled"
    expired = "expired"
    paused = "paused"
