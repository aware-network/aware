from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Environment Service Dto
from aware_environment_service_dto.environment.environment import EnvironmentSessionAttentionResolution

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.session_handoff.models import (
        ExperienceSessionHandoffActorAdmissionReceipt,
    )
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffScope
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionIdentityEvidence


class ExperienceSessionAttentionResolutionRequest(BaseModel):
    """
    Experience session context DTOs over Environment session Attention resolution.
    Ownership:
    - Experience owns actor-specific session/lens admission context.
    - Environment owns EnvironmentSession/NavigationContext/SessionThread to
    AttentionSession resolution.
    - Attention owns AttentionSession/AttentionFocusTransition truth.
    - This DTO is a read receipt, not a persisted Experience frame.
    """

    # Attributes
    environment_navigation_context_id: UUID | None = Field(default=None)
    environment_session_thread_id: UUID | None = Field(default=None)
    environment_session_attention_session_id: UUID | None = Field(default=None)
    expected_attention_session_id: UUID | None = Field(default=None)
    attention_focus_transition_id: UUID | None = Field(default=None)
    expected_attention_session_section_id: UUID | None = Field(default=None)
    expected_focus_scope_id: UUID | None = Field(default=None)
    expected_object_instance_graph_commit_id: UUID | None = Field(default=None)
    expected_projection_hash: str | None = Field(default=None)
    include_attention_session: bool = Field(default=True)
    include_transition_list: bool = Field(default=False)
    transition_limit: int | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionLensContext(BaseModel):
    # Attributes
    status: str = Field(default="pending")
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionContextReceipt(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    session_scope: ExperienceSessionHandoffScope
    actor_admission: ExperienceSessionHandoffActorAdmissionReceipt | None = Field(default=None)
    identity_evidence: ExperienceSessionIdentityEvidence | None = Field(default=None)
    environment_attention_resolution: EnvironmentSessionAttentionResolution | None = Field(default=None)
    lens: ExperienceSessionLensContext | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)
