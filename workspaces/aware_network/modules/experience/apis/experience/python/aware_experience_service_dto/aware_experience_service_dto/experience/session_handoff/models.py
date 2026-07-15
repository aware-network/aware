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
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)

# Identity Service Dto
from aware_identity_service_dto.session.session import (
    SessionMemberActorRoleSummary,
    SessionMemberSummary,
    SessionSummary,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.actor_admission.models import ExperienceActorConfigAdmissionReceipt


class ExperienceSessionHandoffScope(BaseModel):
    """
    Canonical DTOs for consumer-to-Experience session handoff.
    Ownership:
    - Interface supplies caller and runtime focus evidence.
    - Experience owns session actor admission and session feature execution.
    - The handoff does not make Interface own the Experience session lifecycle.
    """

    # Attributes
    namespace: str | None = Field(default=None)
    experience_name: str
    profile_key: str | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_session_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    workspace_session_id: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    window_key: str | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    layout_config_id: UUID | None = Field(default=None)
    section_key: str | None = Field(default=None)
    layout_config_section_config_id: UUID | None = Field(default=None)
    layout_section_id: UUID | None = Field(default=None)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    section_graph_binding_key: str | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    topology_seed_key: str | None = Field(default=None)
    source_kind: str = Field(default="interface_runtime_focus")
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionHandoffActorContext(BaseModel):
    # Attributes
    status: str = Field(default="ready")
    kind: str | None = Field(default=None)
    source: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    identity_id: UUID | None = Field(default=None)
    execution_id: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    provider_session_id: str | None = Field(default=None)
    agent_process_thread_id: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionHandoffFeatureSpec(BaseModel):
    # Attributes
    feature_key: str
    reason: str | None = Field(default=None)
    lease_key: str | None = Field(default=None)
    config: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionIdentityEvidence(BaseModel):
    # Attributes
    parent_environment_identity_session: SessionSummary | None = Field(default=None)
    experience_identity_session: SessionSummary | None = Field(default=None)
    experience_identity_member: SessionMemberSummary | None = Field(default=None)
    experience_identity_actor_roles: list[SessionMemberActorRoleSummary] = Field(default_factory=list)
    environment_session_join: EnvironmentSessionJoinReceipt | None = Field(default=None)
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionHandoffActorAdmissionReceipt(BaseModel):
    # Attributes
    status: str
    admitted: bool = Field(default=False)
    reason: str | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    actor_kind: str | None = Field(default=None)
    identity_id: UUID | None = Field(default=None)
    execution_id: str | None = Field(default=None)
    provider_key: str | None = Field(default=None)
    provider_session_id: str | None = Field(default=None)
    agent_process_thread_id: str | None = Field(default=None)
    environment_admission: EnvironmentActorAdmissionReceipt | None = Field(default=None)
    environment_session_join: EnvironmentSessionJoinReceipt | None = Field(default=None)
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = Field(default=None)
    identity_evidence: ExperienceSessionIdentityEvidence | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    next_suggested_action: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionHandoffFeatureLeaseReceipt(BaseModel):
    # Attributes
    lease_key: str
    feature_key: str
    desired_state: str
    worker_status: str
    revision: int
    info: str | None = Field(default=None)
    last_error: str | None = Field(default=None)
    health_payload: JsonObject | None = Field(default=None)


class ExperienceSessionHandoffReceipt(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    admitted: bool = Field(default=False)
    feature_enabled: bool = Field(default=False)
    session_scope: ExperienceSessionHandoffScope
    actor_admission: ExperienceSessionHandoffActorAdmissionReceipt | None = Field(default=None)
    identity_evidence: ExperienceSessionIdentityEvidence | None = Field(default=None)
    feature_lease: ExperienceSessionHandoffFeatureLeaseReceipt | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    error: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceSessionHandoffStatusReceipt(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    session_scope: ExperienceSessionHandoffScope
    actor_admission: ExperienceSessionHandoffActorAdmissionReceipt | None = Field(default=None)
    identity_evidence: ExperienceSessionIdentityEvidence | None = Field(default=None)
    feature_lease: ExperienceSessionHandoffFeatureLeaseReceipt | None = Field(default=None)
    feature_leases: list[ExperienceSessionHandoffFeatureLeaseReceipt] = Field(default_factory=list)
    feature_lease_count: int = Field(default=0)
    error: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)
