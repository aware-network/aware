from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class SessionConfigEnsureRequest(BaseModel):
    """
    Public DTOs for Identity-owned shared sessions.
    Contract:
    - Identity owns generic SessionConfig, Session, SessionMember, and
    SessionMemberActorRole truth.
    - Providers attach domain sessions/capabilities through provider-neutral
    SessionProvider contracts.
    - DTOs expose session participation and provider attachments without
    importing Environment, Experience, Conversation, Workflow, Workspace, or
    Attention domains.
    """

    # Attributes
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionConfigSummary(BaseModel):
    # Attributes
    session_config_id: UUID
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class SessionConfigEnsureReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    session_config: SessionConfigSummary
    info: str | None = Field(default=None)


class SessionConfigActorConfigBindRequest(BaseModel):
    # Attributes
    session_config_id: UUID
    actor_config_id: UUID
    status: str = Field(default="active")
    purpose: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionConfigActorConfigSummary(BaseModel):
    # Attributes
    session_config_actor_config_id: UUID
    session_config_id: UUID
    actor_config_id: UUID
    status: str = Field(default="active")
    purpose: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class SessionConfigActorConfigBindReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    binding: SessionConfigActorConfigSummary
    info: str | None = Field(default=None)


class SessionProviderRegisterRequest(BaseModel):
    # Attributes
    provider_key: str
    provider_kind: str = Field(default="provider")
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    contract_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionProviderSummary(BaseModel):
    # Attributes
    session_provider_id: UUID
    provider_key: str
    provider_kind: str = Field(default="provider")
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    contract_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class SessionProviderRegisterReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    provider: SessionProviderSummary
    info: str | None = Field(default=None)


class SessionProviderConfigBindRequest(BaseModel):
    # Attributes
    session_provider_id: UUID
    config_key: str
    session_config_id: UUID
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    provider_contract_ref: str | None = Field(default=None)
    selection_policy: str = Field(default="contract_required")
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionProviderSessionConfigSummary(BaseModel):
    # Attributes
    session_provider_session_config_id: UUID
    session_provider_id: UUID
    config_key: str
    session_config_id: UUID
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    provider_contract_ref: str | None = Field(default=None)
    selection_policy: str = Field(default="contract_required")
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class SessionProviderConfigBindReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    binding: SessionProviderSessionConfigSummary
    info: str | None = Field(default=None)


class SessionStartRequest(BaseModel):
    # Attributes
    session_config_id: UUID
    key: str
    parent_session_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    created_by_actor_id: UUID | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionSummary(BaseModel):
    # Attributes
    session_id: UUID
    session_config_id: UUID
    parent_session_id: UUID | None = Field(default=None)
    key: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    purpose: str | None = Field(default=None)
    status: str = Field(default="active")
    created_by_actor_id: UUID | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_ref: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    provider_sessions: list[SessionProviderSessionSummary] = Field(default_factory=list)
    member_count: int = Field(default=0)


class SessionStartReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    session: SessionSummary
    info: str | None = Field(default=None)


class SessionDescribeRequest(BaseModel):
    # Attributes
    session_id: UUID
    request_id: UUID | None = Field(default=None)


class SessionDescribeResult(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    session: SessionSummary | None = Field(default=None)
    info: str | None = Field(default=None)


class SessionJoinRequest(BaseModel):
    # Attributes
    session_id: UUID
    actor_id: UUID
    session_actor_config_id: UUID
    status: str = Field(default="active")
    joined_at_unix_ms: int | None = Field(default=None)
    left_at_unix_ms: int | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionMemberSummary(BaseModel):
    # Attributes
    session_member_id: UUID
    session_id: UUID
    actor_id: UUID
    session_actor_config_id: UUID
    status: str = Field(default="active")
    joined_at_unix_ms: int | None = Field(default=None)
    left_at_unix_ms: int | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    actor_roles: list[SessionMemberActorRoleSummary] = Field(default_factory=list)


class SessionJoinReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    member: SessionMemberSummary
    info: str | None = Field(default=None)


class SessionMemberActorRoleRecordRequest(BaseModel):
    # Attributes
    session_id: UUID
    session_member_id: UUID
    actor_role_id: UUID
    source_kind: str = Field(default="identity_session")
    status: str = Field(default="active")
    evidence_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionMemberActorRoleSummary(BaseModel):
    # Attributes
    session_member_actor_role_id: UUID
    session_member_id: UUID
    actor_role_id: UUID
    source_kind: str = Field(default="identity_session")
    status: str = Field(default="active")
    evidence_json: JsonObject = Field(default_factory=JsonObject)


class SessionMemberActorRoleRecordReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_role: SessionMemberActorRoleSummary
    info: str | None = Field(default=None)


class SessionProviderSessionAttachRequest(BaseModel):
    # Attributes
    session_id: UUID
    provider_session_config_id: UUID
    provider_session_key: str
    provider_session_ref: str | None = Field(default=None)
    provider_object_instance_graph_identity_id: UUID | None = Field(default=None)
    provider_class_instance_identity_id: UUID | None = Field(default=None)
    provider_object_instance_graph_branch_id: UUID | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    request_id: UUID | None = Field(default=None)


class SessionProviderSessionSummary(BaseModel):
    # Attributes
    session_provider_session_id: UUID
    session_id: UUID
    provider_session_config_id: UUID
    provider_session_key: str
    provider_session_ref: str | None = Field(default=None)
    provider_object_instance_graph_identity_id: UUID | None = Field(default=None)
    provider_class_instance_identity_id: UUID | None = Field(default=None)
    provider_object_instance_graph_branch_id: UUID | None = Field(default=None)
    status: str = Field(default="active")
    metadata_json: JsonObject = Field(default_factory=JsonObject)


class SessionProviderSessionAttachReceipt(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    provider_session: SessionProviderSessionSummary
    info: str | None = Field(default=None)


class ActorSessionsListRequest(BaseModel):
    # Attributes
    actor_id: UUID
    parent_session_id: UUID | None = Field(default=None)
    status: str | None = Field(default=None)
    include_inactive: bool = Field(default=False)
    request_id: UUID | None = Field(default=None)


class ActorSessionsListResult(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID
    sessions: list[SessionSummary] = Field(default_factory=list)
    info: str | None = Field(default=None)


class ChildSessionsListRequest(BaseModel):
    # Attributes
    parent_session_id: UUID
    session_config_id: UUID | None = Field(default=None)
    status: str | None = Field(default=None)
    include_inactive: bool = Field(default=False)
    request_id: UUID | None = Field(default=None)


class ChildSessionsListResult(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    parent_session_id: UUID
    sessions: list[SessionSummary] = Field(default_factory=list)
    info: str | None = Field(default=None)


class SessionMembersListRequest(BaseModel):
    # Attributes
    session_id: UUID
    status: str | None = Field(default=None)
    include_inactive: bool = Field(default=False)
    request_id: UUID | None = Field(default=None)


class SessionMembersListResult(BaseModel):
    # Attributes
    request_id: UUID | None = Field(default=None)
    session_id: UUID
    members: list[SessionMemberSummary] = Field(default_factory=list)
    info: str | None = Field(default=None)
