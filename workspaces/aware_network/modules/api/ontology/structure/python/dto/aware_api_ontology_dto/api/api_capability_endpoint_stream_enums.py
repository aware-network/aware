from __future__ import annotations

# Standard
from enum import Enum


class ApiCapabilityEndpointStreamMode(Enum):
    server = "server"
    client = "client"
    bidirectional = "bidirectional"


class ApiCapabilityEndpointStreamEventKind(Enum):
    snapshot = "snapshot"
    delta = "delta"
    notice = "notice"
    complete = "complete"
    error = "error"
