from __future__ import annotations

# Standard
from datetime import datetime
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


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

    @classmethod
    async def build_via_memory_working_event_frame(
        cls,
        memory_working_event_frame_id: UUID,
        resolver_api_call_outcome_id: UUID,
        meaning_text: str,
        resolver_status: str,
        resolver_endpoint_ref: str,
        resolver_discriminant: str,
        resolver_program_impl_instruction_intent_id: UUID,
        resolver_action_config_id: UUID,
        resolver_api_capability_endpoint_id: UUID,
        resolver_api_call_id: UUID,
        resolver_api_call_key: UUID,
        resolver_request_model_id: UUID,
        resolver_response_model_id: UUID,
        resolver_response_class_config_id: UUID,
        resolver_service_operation_id: UUID,
        resolver_service_operation_config_id: UUID,
        resolver_service_operation_commit_id: UUID,
        resolver_service_operation_head_commit_id: UUID,
        resolver_service_operation_branch_id: UUID,
        resolver_service_operation_projection_hash: str,
        resolver_api_call_outcome_commit_id: UUID,
        resolver_api_call_outcome_head_commit_id: UUID,
        resolver_api_call_outcome_branch_id: UUID,
        resolver_api_call_outcome_projection_hash: str,
        provider_reference: str | None = None,
        resolved_at: datetime | None = None,
    ) -> MemoryWorkingEventMeaning:
        """Build one normalized provider result with terminal resolver evidence."""

        payload = {
            "memory_working_event_frame_id": memory_working_event_frame_id,
            "resolver_api_call_outcome_id": resolver_api_call_outcome_id,
            "meaning_text": meaning_text,
            "resolver_status": resolver_status,
            "resolver_endpoint_ref": resolver_endpoint_ref,
            "resolver_discriminant": resolver_discriminant,
            "resolver_program_impl_instruction_intent_id": resolver_program_impl_instruction_intent_id,
            "resolver_action_config_id": resolver_action_config_id,
            "resolver_api_capability_endpoint_id": resolver_api_capability_endpoint_id,
            "resolver_api_call_id": resolver_api_call_id,
            "resolver_api_call_key": resolver_api_call_key,
            "resolver_request_model_id": resolver_request_model_id,
            "resolver_response_model_id": resolver_response_model_id,
            "resolver_response_class_config_id": resolver_response_class_config_id,
            "resolver_service_operation_id": resolver_service_operation_id,
            "resolver_service_operation_config_id": resolver_service_operation_config_id,
            "resolver_service_operation_commit_id": resolver_service_operation_commit_id,
            "resolver_service_operation_head_commit_id": resolver_service_operation_head_commit_id,
            "resolver_service_operation_branch_id": resolver_service_operation_branch_id,
            "resolver_service_operation_projection_hash": resolver_service_operation_projection_hash,
            "resolver_api_call_outcome_commit_id": resolver_api_call_outcome_commit_id,
            "resolver_api_call_outcome_head_commit_id": resolver_api_call_outcome_head_commit_id,
            "resolver_api_call_outcome_branch_id": resolver_api_call_outcome_branch_id,
            "resolver_api_call_outcome_projection_hash": resolver_api_call_outcome_projection_hash,
            "provider_reference": provider_reference,
            "resolved_at": resolved_at,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_memory_working_event_frame", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryWorkingEventMeaning):
            return value
        return MemoryWorkingEventMeaning.validate_invocation_value(value)


class MemoryWorkingEventMeaningBuildViaMemoryWorkingEventFrameInput(BaseModel):
    memory_working_event_frame_id: UUID = Field(description="Foreign key for MemoryWorkingEventFrame.resolved_meaning")
    resolver_api_call_outcome_id: UUID
    meaning_text: str
    resolver_status: str
    resolver_endpoint_ref: str
    resolver_discriminant: str
    resolver_program_impl_instruction_intent_id: UUID
    resolver_action_config_id: UUID
    resolver_api_capability_endpoint_id: UUID
    resolver_api_call_id: UUID
    resolver_api_call_key: UUID
    resolver_request_model_id: UUID
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
    provider_reference: str | None = Field(default=None)
    resolved_at: datetime | None = Field(default=None)


class MemoryWorkingEventMeaningBuildViaMemoryWorkingEventFrameOutput(BaseModel):
    value: MemoryWorkingEventMeaning


FUNCTIONS = {
    "MemoryWorkingEventMeaning": {
        "build_via_memory_working_event_frame": {
            "canonical": {
                "name": "build_via_memory_working_event_frame",
                "description": "Build one normalized provider result with terminal resolver evidence.",
                "is_constructor": True,
            },
            "input": MemoryWorkingEventMeaningBuildViaMemoryWorkingEventFrameInput,
            "output": MemoryWorkingEventMeaningBuildViaMemoryWorkingEventFrameOutput,
        },
    },
}

__all__ = [
    "MemoryWorkingEventMeaning",
    "MemoryWorkingEventMeaningBuildViaMemoryWorkingEventFrameInput",
    "MemoryWorkingEventMeaningBuildViaMemoryWorkingEventFrameOutput",
    "FUNCTIONS",
]
