"""Default bridge adapters (passthrough delta + in-memory evidence)."""

from __future__ import annotations

from typing import Any

from aware_workspace_operator.bridge.interfaces import (
    EvidencePort,
    WorkspaceDeltaPort,
)
from aware_workspace_operator.bridge.models import BridgeEvidenceEvent


class PassthroughWorkspaceDeltaAdapter(WorkspaceDeltaPort):
    """Default delta adapter: return the payload unchanged."""

    async def normalize_code_package_delta(
        self, *, code_package_delta: dict[str, Any]
    ) -> dict[str, Any]:
        return dict(code_package_delta)


class InMemoryEvidenceAdapter(EvidencePort):
    """In-memory append-only evidence sink for tests/orchestration."""

    def __init__(self) -> None:
        self._events: list[BridgeEvidenceEvent] = []

    @property
    def events(self) -> tuple[BridgeEvidenceEvent, ...]:
        return tuple(self._events)

    async def record(self, *, event: BridgeEvidenceEvent) -> None:
        self._events.append(event)


__all__ = [
    "InMemoryEvidenceAdapter",
    "PassthroughWorkspaceDeltaAdapter",
]
