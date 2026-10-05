from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contracts import GoalIntent
from .host import CancellationToken, HostResult
from .observation import GoalObservation, GoalObservationQuery
from .persistence import GoalOperationalRecord, ReplayResult
from .reconciliation import GoalReconciliationIntent


@runtime_checkable
class GoalOperationalAuthority(Protocol):
    """Provider-neutral operational surface required by Goal consumers."""

    def read(self, authority_ref: str) -> GoalOperationalRecord | None: ...

    def replay(
        self,
        authority_ref: str,
        *,
        epoch: str,
        after_cursor: int,
    ) -> ReplayResult | None: ...

    def observe(
        self,
        authority_ref: str,
        query: GoalObservationQuery,
    ) -> GoalObservation | None: ...

    def submit(
        self,
        authority_ref: str,
        intent: GoalIntent,
        *,
        cancellation: CancellationToken | None = None,
    ) -> HostResult: ...

    def reconcile(
        self,
        authority_ref: str,
        intent: GoalReconciliationIntent,
        *,
        cancellation: CancellationToken | None = None,
    ) -> HostResult: ...
