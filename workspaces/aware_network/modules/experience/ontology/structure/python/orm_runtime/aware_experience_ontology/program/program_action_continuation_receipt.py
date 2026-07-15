from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)


class ProgramActionContinuationReceipt(BaseModel):
    """
    Typed terminal receipt source for one Program action continuation.
    Contract:
    - Provider response fields remain owned by the provider response ClassConfig.
    - This schema owns only Program selection and terminal API/commit evidence.
    - Continuation bindings select fields relationally by AttributeConfig id.
    - This is a composition schema, not a scheduler or persisted execution plan.
    """

    # Attributes
    status: str
    endpoint_ref: str
    discriminant: str
    source_program_impl_instruction_intent_id: UUID
    source_action_config_id: UUID
    api_capability_endpoint_id: UUID
    api_call_id: UUID
    api_call_key: UUID
    request_model_id: UUID
    api_call_outcome_id: UUID
    response_model_id: UUID | None = Field(default=None)
    response_class_config_id: UUID | None = Field(default=None)
    service_operation_id: UUID | None = Field(default=None)
    service_operation_config_id: UUID | None = Field(default=None)
    service_operation_commit_id: UUID | None = Field(default=None)
    service_operation_head_commit_id: UUID | None = Field(default=None)
    service_operation_branch_id: UUID | None = Field(default=None)
    service_operation_projection_hash: str | None = Field(default=None)
    api_call_outcome_commit_id: UUID | None = Field(default=None)
    api_call_outcome_head_commit_id: UUID | None = Field(default=None)
    api_call_outcome_branch_id: UUID | None = Field(default=None)
    api_call_outcome_projection_hash: str | None = Field(default=None)
