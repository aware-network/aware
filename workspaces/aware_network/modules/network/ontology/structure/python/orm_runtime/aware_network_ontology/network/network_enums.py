from __future__ import annotations

# Standard
from enum import Enum


class NetworkAppType(Enum):
    """
    Network protocol enums.
    These live in the ontology (SSOT) because they are referenced by network
    domain models and must be available when composing the runtime OCG without
    any DTO/API packages.
    """

    environment = "environment"
    interface = "interface"
    network_node = "network_node"


class NetworkEnvironmentRole(Enum):
    owner = "owner"
    replica = "replica"


class NetworkFanoutMode(Enum):
    notify_pull = "notify_pull"


class NetworkNodeStatus(Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    syncing = "syncing"


class NetworkOperationMessageType(Enum):
    request = "request"
    response = "response"
    stream = "stream"
    notification = "notification"


class NetworkOperationType(Enum):
    api = "api"
    environment = "environment"
    environment_config = "environment_config"
    service = "service"
    network_node = "network_node"


class NetworkRequestStatus(Enum):
    accepted = "accepted"
    pending = "pending"
    rejected = "rejected"
    succeeded = "succeeded"
    failed = "failed"
