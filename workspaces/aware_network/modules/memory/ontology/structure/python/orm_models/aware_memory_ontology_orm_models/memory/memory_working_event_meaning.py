from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class MemoryWorkingEventMeaning(ORMModel):
    """
    Provider-neutral resolved meaning for one remembered event.
    Contract:
    - Memory owns persistence and this normalized envelope.
    - The domain provider owns interpretation and returns only normalized text
    plus an optional opaque provider reference.
    - Resolver action/API/commit provenance comes from Experience terminal
    continuation truth, never from provider-echoed fields.
    - V0 accepts exactly one resolved meaning under one event frame.
    """

    # Attributes
    meaning_text: str
    provider_reference: str | None = Field(default=None)
    resolved_at: datetime
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

    # Foreign Keys
    memory_working_event_frame_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingEventFrame.resolved_meaning"
    )
