from __future__ import annotations

# Standard
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_memory_ontology.memory.memory_working_event_meaning import MemoryWorkingEventMeaning
    from aware_reactivity_ontology.event.event import Event


class MemoryWorkingEventFrame(ORMModel):
    """
    Event payload for a MemoryWorkingItem.
    Contract:
    - Must be linked to a `MemoryWorkingItem` whose `kind=event`.
    - Event provenance is canonical reactivity evidence.
    """

    # Relationships
    event: Event | None = Field(default=None, exclude=True)
    resolved_meaning: MemoryWorkingEventMeaning | None = Field(default=None, exclude=True)

    # Attributes
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

    # Foreign Keys
    memory_working_item_id: UUID | None = Field(
        default=None, description="Foreign key for MemoryWorkingItem.event_frame"
    )
    event_id: UUID = Field(description="Foreign key for MemoryWorkingEventFrame.event")

    async def record_resolved_meaning(
        self,
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
        """Persist exactly one resolved meaning under this remembered event."""

        payload = {
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
        result = await invoke_instance(orm_model=self, function_name="record_resolved_meaning", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_memory_ontology.memory.memory_working_event_meaning import MemoryWorkingEventMeaning

        if isinstance(value, MemoryWorkingEventMeaning):
            return value
        return MemoryWorkingEventMeaning.validate_invocation_value(value)

    @classmethod
    async def build_via_memory_working_item(
        cls,
        memory_working_item_id: UUID,
        event_id: UUID,
        event_config_id: UUID | None = None,
        event_activation_id: UUID | None = None,
        event_type: str | None = None,
        event_source: str | None = None,
        event_status: str | None = None,
        commit_branch_id: UUID | None = None,
        commit_projection_hash: str | None = None,
        commit_id: UUID | None = None,
        object_instance_graph_id: UUID | None = None,
        object_instance_graph_commit_id: UUID | None = None,
        action_intent_id: UUID | None = None,
        intent_key: str | None = None,
        action_config_id: UUID | None = None,
        action_execution_id: UUID | None = None,
        action_execution_key: str | None = None,
        api_call_key: UUID | None = None,
        action_binding_id: UUID | None = None,
        action_experience_id: UUID | None = None,
        environment_profile_id: UUID | None = None,
        environment_event_id: UUID | None = None,
        invocation_config_id: UUID | None = None,
        endpoint_id: UUID | None = None,
        actor_subscription_id: UUID | None = None,
    ) -> MemoryWorkingEventFrame:
        """
        Builds deterministic event frame payload for a memory item.

        Event provenance may be supplied by the Experience action-dispatch
        request composer. Memory stores it with the event frame so later
        context reads can distinguish action-dispatch-backed event memory from
        direct/unverified event writes.
        """

        payload = {
            "memory_working_item_id": memory_working_item_id,
            "event_id": event_id,
            "event_config_id": event_config_id,
            "event_activation_id": event_activation_id,
            "event_type": event_type,
            "event_source": event_source,
            "event_status": event_status,
            "commit_branch_id": commit_branch_id,
            "commit_projection_hash": commit_projection_hash,
            "commit_id": commit_id,
            "object_instance_graph_id": object_instance_graph_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "action_intent_id": action_intent_id,
            "intent_key": intent_key,
            "action_config_id": action_config_id,
            "action_execution_id": action_execution_id,
            "action_execution_key": action_execution_key,
            "api_call_key": api_call_key,
            "action_binding_id": action_binding_id,
            "action_experience_id": action_experience_id,
            "environment_profile_id": environment_profile_id,
            "environment_event_id": environment_event_id,
            "invocation_config_id": invocation_config_id,
            "endpoint_id": endpoint_id,
            "actor_subscription_id": actor_subscription_id,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_memory_working_item", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, MemoryWorkingEventFrame):
            return value
        return MemoryWorkingEventFrame.validate_invocation_value(value)


class MemoryWorkingEventFrameRecordResolvedMeaningInput(BaseModel):
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


class MemoryWorkingEventFrameRecordResolvedMeaningOutput(BaseModel):
    value: MemoryWorkingEventMeaning


class MemoryWorkingEventFrameBuildViaMemoryWorkingItemInput(BaseModel):
    memory_working_item_id: UUID = Field(description="Foreign key for MemoryWorkingItem.event_frame")
    event_id: UUID
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


class MemoryWorkingEventFrameBuildViaMemoryWorkingItemOutput(BaseModel):
    value: MemoryWorkingEventFrame


FUNCTIONS = {
    "MemoryWorkingEventFrame": {
        "record_resolved_meaning": {
            "canonical": {
                "name": "record_resolved_meaning",
                "description": "Persist exactly one resolved meaning under this remembered event.",
                "is_constructor": False,
            },
            "input": MemoryWorkingEventFrameRecordResolvedMeaningInput,
            "output": MemoryWorkingEventFrameRecordResolvedMeaningOutput,
        },
        "build_via_memory_working_item": {
            "canonical": {
                "name": "build_via_memory_working_item",
                "description": "Builds deterministic event frame payload for a memory item.\n\nEvent provenance may be supplied by the Experience action-dispatch\nrequest composer. Memory stores it with the event frame so later\ncontext reads can distinguish action-dispatch-backed event memory from\ndirect/unverified event writes.",
                "is_constructor": True,
            },
            "input": MemoryWorkingEventFrameBuildViaMemoryWorkingItemInput,
            "output": MemoryWorkingEventFrameBuildViaMemoryWorkingItemOutput,
        },
    },
}

__all__ = [
    "MemoryWorkingEventFrame",
    "MemoryWorkingEventFrameRecordResolvedMeaningInput",
    "MemoryWorkingEventFrameRecordResolvedMeaningOutput",
    "MemoryWorkingEventFrameBuildViaMemoryWorkingItemInput",
    "MemoryWorkingEventFrameBuildViaMemoryWorkingItemOutput",
    "FUNCTIONS",
]
