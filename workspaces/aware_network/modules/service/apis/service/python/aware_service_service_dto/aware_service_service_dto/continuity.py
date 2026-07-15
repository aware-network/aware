from __future__ import annotations

# Standard
from datetime import datetime
from enum import Enum
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ServiceContinuityStatus(Enum):
    """
    Provider-neutral continuity observation shared by service participants.
    This DTO is the common provenance and lifecycle envelope only. Participant
    APIs own their domain continuity state and pair it with this observation in
    their own typed response. Recovery decisions must not depend on an opaque
    JSON payload in this contract.
    """

    unknown = "unknown"
    ready = "ready"
    degraded = "degraded"
    blocked = "blocked"
    unavailable = "unavailable"


class ServiceContinuityFreshness(Enum):
    unknown = "unknown"
    live = "live"
    cached = "cached"
    stale = "stale"


class ServiceContinuityBlocker(BaseModel):
    # Attributes
    code: str
    message: str
    source_ref: str | None = Field(default=None)
    retryable: bool = Field(default=False)
    retry_after: datetime | None = Field(default=None)


class ServiceContinuityNextAction(BaseModel):
    # Attributes
    action_key: str
    title: str
    description: str | None = Field(default=None)
    capability_ref: str | None = Field(default=None)
    endpoint_ref: str | None = Field(default=None)
    requires_live_authority: bool = Field(default=True)


class ServiceContinuityObservation(BaseModel):
    # Attributes
    observation_id: UUID
    schema_version: str = Field(default="service.continuity.observation.v1")
    participant_ref: str
    service_package_ref: str
    continuity_contract_ref: str
    status: ServiceContinuityStatus = Field(default=ServiceContinuityStatus.unknown)
    freshness: ServiceContinuityFreshness = Field(default=ServiceContinuityFreshness.unknown)
    observed_at: datetime
    valid_until: datetime | None = Field(default=None)
    source_revision_ref: str | None = Field(default=None)
    authority_id: str | None = Field(default=None)
    authority_generation_id: str | None = Field(default=None)
    observation_receipt_ref: str | None = Field(default=None)
    blockers: list[ServiceContinuityBlocker] = Field(default_factory=list)
    next_actions: list[ServiceContinuityNextAction] = Field(default_factory=list)
