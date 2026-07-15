from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.session_view_frame.models import ExperienceSessionViewFrame


class ExperienceViewStateProviderProvenance(BaseModel):
    """
    Canonical DTOs for Experience-owned view-state subscription snapshots.
    ApiView owns the readable lower view contract. Experience composes the
    mounted view and Attention context above that API contract. Provider services
    may own read-model execution, but they do not redefine the view contract or
    this subscription envelope.
    """

    # Attributes
    provider_kind: str
    provider_ref: str | None = Field(default=None)
    service_name: str | None = Field(default=None)
    api_view_ref: str | None = Field(default=None)
    api_view_id: UUID | None = Field(default=None)
    endpoint_ref: str | None = Field(default=None)
    discriminant: str | None = Field(default=None)
    service_operation_config_id: UUID | None = Field(default=None)
    service_operation_config_api_view_id: UUID | None = Field(default=None)
    api_capability_endpoint_id: UUID | None = Field(default=None)
    service_operation_branch_id: UUID | None = Field(default=None)
    service_operation_projection_hash: str | None = Field(default=None)
    api_call_outcome_branch_id: UUID | None = Field(default=None)
    api_call_outcome_projection_hash: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceViewStateSnapshot(BaseModel):
    # Attributes
    experience_name: str
    view_ref: str
    projection_view_key: str | None = Field(default=None)
    projection_experience_view_id: UUID | None = Field(default=None)
    projection_experience_view_instance_id: UUID | None = Field(default=None)
    session_view_frame: ExperienceSessionViewFrame | None = Field(default=None)
    session_view_frame_digest: str | None = Field(default=None)
    state_model_id: UUID | None = Field(default=None)
    state_model_ref: str | None = Field(default=None)
    provider: ExperienceViewStateProviderProvenance | None = Field(default=None)
    status: str = Field(default="unknown")
    state: JsonObject = Field(default_factory=JsonObject)
    cursor: str | None = Field(default=None)
    digest: str | None = Field(default=None)
    change_reason: str = Field(default="initial")
    sequence: int = Field(default=0)
    observed_at: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)
    error: str | None = Field(default=None)


class ExperienceViewStateEvent(BaseModel):
    # Attributes
    kind: str = Field(default="snapshot")
    snapshot: ExperienceViewStateSnapshot
