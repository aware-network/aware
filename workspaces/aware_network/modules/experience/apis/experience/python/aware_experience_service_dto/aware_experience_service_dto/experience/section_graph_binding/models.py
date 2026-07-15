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


class ExperienceSectionGraphBindingDescriptor(BaseModel):
    """
    Canonical DTOs for Experience-owned section-graph-binding catalog and state.
    Ownership:
    - Experience API owns the stable transport DTO boundary.
    - Experience ontology owns the underlying `section -> view -> graph identity` truth.
    - Attention remains the only lawful owner of committed focus truth.
    """

    # Attributes
    binding_key: str
    section_key: str
    projection_observable_id: UUID
    projection_experience_graph_identity_id: UUID
    object_projection_graph_identity_id: UUID
    view_ref: str
    graph_identity_ref: str


class ExperienceLayoutGraphBindingDescriptor(BaseModel):
    # Attributes
    binding_key: str
    projection_experience_layout_graph_binding_id: UUID
    projection_experience_id: UUID
    layout_config_id: UUID
    section_bindings: list[ExperienceSectionGraphBindingDescriptor] = Field(default_factory=list)


class ExperienceSectionFocusTarget(BaseModel):
    # Attributes
    kind: str = Field(
        default="constructor",
        description='Canonical token values:\n- "constructor": branchless focus over projection identity.\n- "materialized": focus has a committed ObjectInstanceGraphBranch.',
    )
    focus_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    object_projection_graph_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    target_type: str | None = Field(default=None)
    target_id: UUID | None = Field(default=None)
    description: str | None = Field(default=None)


class ExperienceViewInvocationActionDescriptor(BaseModel):
    # Attributes
    action_id: UUID = Field(description="Compatibility alias for `view_invocation_action_config_id`.")
    view_invocation_action_config_id: UUID
    experience_invocation_action_config_id: UUID
    api_view_capability_endpoint_id: UUID
    action_key: str
    target_kind: str
    endpoint_ref: str
    label: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)
    sdk_operation_api_view_capability_endpoint_id: UUID | None = Field(default=None)
    api_capability_endpoint_id: UUID | None = Field(default=None)
    sdk_operation_id: UUID | None = Field(default=None)


class ExperienceInvocationActionRolePolicy(BaseModel):
    # Attributes
    role_policy_id: UUID | None = Field(default=None)
    experience_invocation_action_config_id: UUID
    role_config_id: UUID
    role_config_name: str | None = Field(default=None)
    policy_key: str = Field(default="invoke")
    requirement_kind: str = Field(default="admitted_actor_role")
    description: str | None = Field(default=None)


class ExperienceInvocationActionRolePolicyResolution(BaseModel):
    # Attributes
    experience_name: str
    experience_invocation_action_config_id: UUID
    action_key: str | None = Field(default=None)
    allowed_policies: list[ExperienceInvocationActionRolePolicy] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceInvocationActionAdmissionPreflight(BaseModel):
    # Attributes
    accepted: bool = Field(default=False)
    status: str
    actor_id: UUID | None = Field(default=None)
    experience_invocation_action_config_id: UUID | None = Field(default=None)
    action_key: str | None = Field(default=None)
    matched_role_config_id: UUID | None = Field(default=None)
    matched_role_config_name: str | None = Field(default=None)
    matched_actor_role_id: UUID | None = Field(default=None)
    blockers: list[str] = Field(default_factory=list)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ExperienceViewInvocationActionReceipt(BaseModel):
    # Attributes
    projection_experience_view_instance_id: UUID
    view_invocation_action_config_id: UUID
    experience_invocation_action_config_id: UUID
    experience_invocation_action_id: UUID
    projection_experience_view_invocation_action_id: UUID
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    commit_id: UUID | None = Field(default=None)


class ExperienceViewInvocationActionApiDispatchReceipt(BaseModel):
    # Attributes
    endpoint_ref: str
    discriminant: str
    status: str = Field(default="succeeded")
    network_request_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    api_capability_endpoint_id: UUID | None = Field(default=None)
    call_key: UUID | None = Field(default=None)
    request_hash: str | None = Field(default=None)
    request_model_id: UUID | None = Field(default=None)
    api_call_outcome_id: UUID | None = Field(default=None)
    response_model_id: UUID | None = Field(default=None)
    service_operation_id: UUID | None = Field(default=None)
    service_operation_config_id: UUID | None = Field(default=None)
    service_operation_config_api_endpoint_id: UUID | None = Field(default=None)
    service_operation_commit_id: UUID | None = Field(default=None)
    service_operation_head_commit_id: UUID | None = Field(default=None)
    service_operation_event_ids: list[UUID] = Field(default_factory=list)
    service_operation_head_event_ids: list[UUID] = Field(default_factory=list)
    service_operation_branch_id: UUID | None = Field(default=None)
    service_operation_projection_hash: str | None = Field(default=None)
    api_call_outcome_commit_id: UUID | None = Field(default=None)
    api_call_outcome_head_commit_id: UUID | None = Field(default=None)
    api_call_outcome_event_ids: list[UUID] = Field(default_factory=list)
    api_call_outcome_head_event_ids: list[UUID] = Field(default_factory=list)
    api_call_outcome_branch_id: UUID | None = Field(default=None)
    api_call_outcome_projection_hash: str | None = Field(default=None)


class ExperienceSectionViewResolution(BaseModel):
    # Attributes
    projection_experience_id: UUID = Field(
        description="Experience-owned instance bridge:\nProjectionExperience + Attention Section + Observable -> ViewInstance."
    )
    section_id: UUID
    object_projection_graph_observable_id: UUID
    projection_experience_section_id: UUID
    projection_experience_section_view_id: UUID
    projection_experience_view_instance_id: UUID
    projection_experience_view_id: UUID
    section_graph_binding_id: UUID
    view_ref: str
    view_instance_key: str
    section_key: str | None = Field(default=None)
    status: str
    actions: list[ExperienceViewInvocationActionDescriptor] = Field(default_factory=list)


class ExperienceSectionGraphBindingState(BaseModel):
    # Attributes
    binding: ExperienceSectionGraphBindingDescriptor
    exists: bool = Field(default=False)
    is_active: bool = Field(default=False)
    focus_scope_id: UUID | None = Field(default=None)
    focus_id: UUID | None = Field(default=None)
    projection_observable_id: UUID | None = Field(default=None)
    projection_experience_graph_identity_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    focus_target: ExperienceSectionFocusTarget | None = Field(default=None)
    section_view: ExperienceSectionViewResolution | None = Field(default=None)


class ExperienceSectionGraphBindingStateSnapshot(BaseModel):
    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    states: list[ExperienceSectionGraphBindingState] = Field(default_factory=list)


class ExperienceSectionGraphBindingStateEvent(BaseModel):
    # Attributes
    kind: str = Field(default="snapshot")
    snapshot: ExperienceSectionGraphBindingStateSnapshot


class ExperienceLayoutGraphBindingState(BaseModel):
    # Attributes
    binding: ExperienceLayoutGraphBindingDescriptor
    exists: bool = Field(default=False)
    section_states: list[ExperienceSectionGraphBindingState] = Field(default_factory=list)


class ExperienceLayoutGraphBindingStateSnapshot(BaseModel):
    # Attributes
    experience_name: str
    catalog_revision: str | None = Field(default=None)
    states: list[ExperienceLayoutGraphBindingState] = Field(default_factory=list)
