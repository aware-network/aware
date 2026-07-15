from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from aware_service_runtime.temporal_mutation_error_codes import (
    TemporalMutationServiceErrorCode,
)


@dataclass(frozen=True, slots=True)
class TemporalMutationAdmissionRequest:
    operation: str
    actor_id: UUID | None
    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    branch_id: UUID | None
    projection_hash: str | None
    session_id: UUID | None = None
    base_commit_id: UUID | None = None
    revision: int | None = None
    expected_revision: int | None = None
    from_revision: int | None = None
    function_id: UUID | None = None
    object_id: UUID | None = None
    commit_message: str | None = None
    session_revision: int | None = None
    session_base_commit_id: UUID | None = None
    session_writer_actor_id: UUID | None = None
    writer_lease_expires_at: datetime | None = None
    subscriber_count: int | None = None


@dataclass(frozen=True, slots=True)
class TemporalMutationAdmissionDecision:
    allowed: bool
    reason: str | None = None
    error_code: str = TemporalMutationServiceErrorCode.admission_denied.value
    context: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def allow(cls, *, context: Mapping[str, object] | None = None):
        return cls(allowed=True, context=context or {})

    @classmethod
    def deny(
        cls,
        reason: str,
        *,
        error_code: str = TemporalMutationServiceErrorCode.admission_denied.value,
        context: Mapping[str, object] | None = None,
    ):
        return cls(
            allowed=False,
            reason=reason,
            error_code=error_code,
            context=context or {},
        )


class TemporalMutationAdmissionPolicy(Protocol):
    async def authorize(
        self, request: TemporalMutationAdmissionRequest
    ) -> TemporalMutationAdmissionDecision: ...


class DenyAllTemporalMutationAdmissionPolicy:
    async def authorize(
        self, request: TemporalMutationAdmissionRequest
    ) -> TemporalMutationAdmissionDecision:
        return TemporalMutationAdmissionDecision.deny(
            "Temporal mutation admission policy is not configured.",
            context={"operation": request.operation},
        )


class AllowAllTemporalMutationAdmissionPolicy:
    async def authorize(
        self, request: TemporalMutationAdmissionRequest
    ) -> TemporalMutationAdmissionDecision:
        _ = request
        return TemporalMutationAdmissionDecision.allow()


__all__ = [
    "AllowAllTemporalMutationAdmissionPolicy",
    "DenyAllTemporalMutationAdmissionPolicy",
    "TemporalMutationAdmissionDecision",
    "TemporalMutationAdmissionPolicy",
    "TemporalMutationAdmissionRequest",
]
