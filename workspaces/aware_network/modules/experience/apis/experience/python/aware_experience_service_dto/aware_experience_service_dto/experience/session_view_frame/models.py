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
    from aware_experience_service_dto.experience.session_context.models import ExperienceSessionContextReceipt
    from aware_experience_service_dto.experience.session_handoff.models import (
        ExperienceSessionHandoffActorAdmissionReceipt,
    )
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffScope
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionIdentityEvidence


class ExperienceSessionViewFrameLens(BaseModel):
    """
    Experience session view-frame DTOs over Environment session Attention.
    Ownership:
    - Experience owns actor-specific session/lens interpretation.
    - Environment owns EnvironmentSession/NavigationContext/SessionThread to
    AttentionSession resolution.
    - Attention owns AttentionSession/AttentionFocusTransition truth.
    - This DTO is a consumer read model, not persisted ontology and not a
    duplicate Attention frame.
    """

    # Attributes
    status: str = Field(default="pending")
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    section_key: str | None = Field(default=None)
    window_key: str | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    layout_config_section_config_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionViewFrame(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    session_scope: ExperienceSessionHandoffScope
    actor_admission: ExperienceSessionHandoffActorAdmissionReceipt | None = Field(default=None)
    identity_evidence: ExperienceSessionIdentityEvidence | None = Field(default=None)
    environment_attention_resolution: EnvironmentSessionAttentionResolution | None = Field(default=None)
    context_receipt: ExperienceSessionContextReceipt | None = Field(default=None)
    lens: ExperienceSessionViewFrameLens | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_session_id: UUID | None = Field(default=None)
    environment_navigation_context_id: UUID | None = Field(default=None)
    environment_session_thread_id: UUID | None = Field(default=None)
    environment_session_attention_session_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    thread_layout_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    active_attention_focus_transition_id: UUID | None = Field(default=None)
    transition_count: int = Field(default=0)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)
