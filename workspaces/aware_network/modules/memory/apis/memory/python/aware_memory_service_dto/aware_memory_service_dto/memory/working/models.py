from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class MemoryWorkingPin(BaseModel):
    """
    Canonical DTOs for actor-scoped working memory.
    Ownership:
    - Memory API owns these transport read models.
    - Memory ontology owns persisted MemoryWorking and MemoryWorkingItem truth.
    - Attention validates AttentionFocusTransition truth before Memory retains
    an attention pointer.
    - Identity owns actor membership and subscriptions.
    """

    # Attributes
    memory_working_id: UUID
    actor_id: UUID
    key: str = Field(default="default")
    content_chain_id: UUID | None = Field(default=None)
    item_count: int = Field(default=0)
    latest_item_id: UUID | None = Field(default=None)


class MemoryResolvedEventMeaningPin(BaseModel):
    # Attributes
    memory_working_event_meaning_id: UUID
    memory_working_event_frame_id: UUID
    memory_working_item_id: UUID
    event_id: UUID
    meaning_text: str
    provider_reference: str | None = Field(default=None)
    resolved_at: datetime | None = Field(default=None)
    resolver_status: str
    resolver_endpoint_ref: str
    resolver_discriminant: str
    resolver_program_impl_instruction_intent_id: UUID
    resolver_action_config_id: UUID
    resolver_api_capability_endpoint_id: UUID
    resolver_api_call_id: UUID
    resolver_api_call_key: UUID
    resolver_request_model_id: UUID
    resolver_api_call_outcome_id: UUID
    resolver_response_model_id: UUID
    resolver_response_class_config_id: UUID
    resolver_service_operation_id: UUID
    resolver_service_operation_config_id: UUID
    resolver_service_operation_commit_id: UUID
    resolver_service_operation_head_commit_id: UUID
    resolver_service_operation_branch_id: UUID
    resolver_service_operation_projection_hash: str
    resolver_api_call_outcome_commit_id: UUID
    resolver_api_call_outcome_head_commit_id: UUID
    resolver_api_call_outcome_branch_id: UUID
    resolver_api_call_outcome_projection_hash: str


class MemoryResolvedEventMeaningEvidence(BaseModel):
    # Attributes
    validation_status: str = Field(default="not_resolved")
    valid: bool = Field(default=False)
    usable: bool = Field(default=False)
    failure_reasons: list[str] = Field(default_factory=list)
    meaning: MemoryResolvedEventMeaningPin | None = Field(default=None)


class MemoryWorkingItemPin(BaseModel):
    # Attributes
    memory_working_item_id: UUID
    memory_working_id: UUID
    kind: str
    position: int = Field(default=0)
    created_at: datetime | None = Field(default=None)
    event_frame_id: UUID | None = Field(default=None)
    event_id: UUID | None = Field(default=None)
    event_config_id: UUID | None = Field(default=None)
    event_activation_id: UUID | None = Field(default=None)
    event_type: str | None = Field(default=None)
    event_source: str | None = Field(default=None)
    event_status: str | None = Field(default=None)
    commit_branch_id: UUID | None = Field(default=None)
    commit_projection_hash: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    action_intent_id: UUID | None = Field(default=None)
    intent_key: str | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_execution_id: UUID | None = Field(default=None)
    action_execution_key: str | None = Field(default=None)
    api_call_key: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_experience_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_event_id: UUID | None = Field(default=None)
    invocation_config_id: UUID | None = Field(default=None)
    endpoint_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    resolved_event_meaning: MemoryResolvedEventMeaningPin | None = Field(default=None)
    content_frame_id: UUID | None = Field(default=None)
    content_id: UUID | None = Field(default=None)
    tool_frame_id: UUID | None = Field(default=None)
    tool_call_id: UUID | None = Field(default=None)
    tool_response_id: UUID | None = Field(default=None)
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    attention_focus_transition_id: UUID | None = Field(default=None)
    rationale: str | None = Field(default=None)
    summary: str | None = Field(default=None)


class MemoryEventActionProvenanceEvidence(BaseModel):
    # Attributes
    validation_status: str = Field(default="not_validated")
    valid: bool = Field(default=False)
    usable: bool = Field(default=False)
    failure_reasons: list[str] = Field(default_factory=list)
    event_id: UUID | None = Field(default=None)
    event_config_id: UUID | None = Field(default=None)
    event_activation_id: UUID | None = Field(default=None)
    event_type: str | None = Field(default=None)
    event_source: str | None = Field(default=None)
    event_status: str | None = Field(default=None)
    commit_branch_id: UUID | None = Field(default=None)
    commit_projection_hash: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    object_instance_graph_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    actor_subscription_id: UUID | None = Field(default=None)
    action_intent_id: UUID | None = Field(default=None)
    intent_key: str | None = Field(default=None)
    action_config_id: UUID | None = Field(default=None)
    action_execution_id: UUID | None = Field(default=None)
    action_execution_key: str | None = Field(default=None)
    api_call_key: UUID | None = Field(default=None)
    action_binding_id: UUID | None = Field(default=None)
    action_experience_id: UUID | None = Field(default=None)
    environment_profile_id: UUID | None = Field(default=None)
    environment_event_id: UUID | None = Field(default=None)
    invocation_config_id: UUID | None = Field(default=None)
    endpoint_id: UUID | None = Field(default=None)


class MemoryWorkingItemEvidence(BaseModel):
    # Attributes
    item: MemoryWorkingItemPin
    validation_status: str = Field(default="not_validated")
    valid: bool = Field(default=False)
    usable: bool = Field(default=False)
    failure_reasons: list[str] = Field(default_factory=list)
    attention_validation: AttentionTransitionValidationEvidence | None = Field(default=None)
    event_action_provenance: MemoryEventActionProvenanceEvidence | None = Field(default=None)
    resolved_event_meaning: MemoryResolvedEventMeaningEvidence | None = Field(default=None)


class MemoryActorContextEvidence(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    parent_identity_session_id: UUID | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    identity_session_exists: bool = Field(default=False)
    identity_session_status: str | None = Field(default=None)
    actor_session_member_id: UUID | None = Field(default=None)
    actor_session_member_status: str | None = Field(default=None)
    actor_session_member_active: bool = Field(default=False)
    actor_sessions_considered: int = Field(default=0)
    validation_status: str = Field(default="not_validated")
    valid: bool = Field(default=False)
    usable: bool = Field(default=False)
    failure_reasons: list[str] = Field(default_factory=list)


class MemoryActorContextSnapshot(BaseModel):
    # Attributes
    actor_context: MemoryActorContextEvidence
    exists: bool = Field(default=False)
    memory_working: MemoryWorkingPin | None = Field(default=None)
    items: list[MemoryWorkingItemEvidence] = Field(default_factory=list)
    usable_item_count: int = Field(default=0)
    unresolved_item_count: int = Field(default=0)
    cursor: str | None = Field(default=None)
    digest: str | None = Field(default=None)
    sequence: int = Field(default=0)
    change_reason: str = Field(default="initial")
    observed_at: str | None = Field(default=None)


class MemoryActorContextEvent(BaseModel):
    # Attributes
    kind: str = Field(default="snapshot")
    snapshot: MemoryActorContextSnapshot


class MemoryActorContextFrameItem(BaseModel):
    # Attributes
    memory_working_item_id: UUID
    kind: str
    position: int = Field(default=0)
    text: str | None = Field(default=None)
    text_source: str | None = Field(default=None)
    meaning_status: str = Field(default="not_applicable")
    resolved_event_meaning_id: UUID | None = Field(default=None)
    source_kind: str | None = Field(default=None)
    source_id: UUID | None = Field(default=None)
    validation_status: str = Field(default="not_validated")
    usable: bool = Field(default=False)
    failure_reasons: list[str] = Field(default_factory=list)


class MemoryWorkingFact(BaseModel):
    """
    Post-persistence observation projected from committed Memory truth.
    This is not a Reactivity event or action request.
    """

    # Attributes
    kind: str
    actor_id: UUID
    memory_working_id: UUID
    memory_working_item_id: UUID
    event_id: UUID
    resolved_event_meaning_id: UUID | None = Field(default=None)
    source_actor_subscription_id: UUID | None = Field(default=None)
    memory_commit_id: UUID
    validation_status: str = Field(default="not_validated")
    usable: bool = Field(default=False)


class MemoryActorContextFrame(BaseModel):
    # Attributes
    actor_context: MemoryActorContextEvidence
    exists: bool = Field(default=False)
    memory_working: MemoryWorkingPin | None = Field(default=None)
    usable_items: list[MemoryActorContextFrameItem] = Field(default_factory=list)
    unresolved_items: list[MemoryActorContextFrameItem] = Field(default_factory=list)
    usable_item_count: int = Field(default=0)
    unresolved_item_count: int = Field(default=0)
    cursor: str | None = Field(default=None)
    digest: str | None = Field(default=None)
    sequence: int = Field(default=0)
    change_reason: str = Field(default="initial")
    observed_at: str | None = Field(default=None)


class MemoryActorContextFrameEvent(BaseModel):
    # Attributes
    kind: str = Field(default="frame")
    frame: MemoryActorContextFrame
    fact: MemoryWorkingFact | None = Field(default=None)


class AttentionTransitionValidationEvidence(BaseModel):
    # Attributes
    exists: bool = Field(default=False)
    valid: bool = Field(default=False)
    failure_reasons: list[str] = Field(default_factory=list)
    attention_focus_transition_id: UUID | None = Field(default=None)
    identity_session_id: UUID | None = Field(default=None)
    attention_session_id: UUID | None = Field(default=None)
    attention_session_section_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)


class MemoryWorkingCommitReceipt(BaseModel):
    # Attributes
    memory_working_id: UUID
    memory_working_item_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)
    status: str = Field(default="succeeded")
    info: str | None = Field(default=None)
