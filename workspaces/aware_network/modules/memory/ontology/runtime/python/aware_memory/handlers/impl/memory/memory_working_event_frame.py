from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Memory Ontology
from aware_memory_ontology.memory.memory_working_event_frame import MemoryWorkingEventFrame
from aware_memory_ontology.memory.memory_working_event_meaning import MemoryWorkingEventMeaning

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_memory_ontology.stable_ids import stable_memory_working_event_frame_id

# --- AWARE: USER_IMPORTS END


async def record_resolved_meaning(
    memory_working_event_frame: MemoryWorkingEventFrame,
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
    """
    Persist exactly one resolved meaning under this remembered event.
    """

    # --- AWARE: LOGIC START record_resolved_meaning
    existing = memory_working_event_frame.resolved_meaning
    expected = {
        "resolver_api_call_outcome_id": resolver_api_call_outcome_id,
        "meaning_text": meaning_text.strip(),
        "resolver_status": resolver_status.strip().lower(),
        "resolver_endpoint_ref": resolver_endpoint_ref.strip(),
        "resolver_discriminant": resolver_discriminant.strip(),
        "resolver_program_impl_instruction_intent_id": (resolver_program_impl_instruction_intent_id),
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
        "resolver_service_operation_head_commit_id": (resolver_service_operation_head_commit_id),
        "resolver_service_operation_branch_id": resolver_service_operation_branch_id,
        "resolver_service_operation_projection_hash": (resolver_service_operation_projection_hash.strip()),
        "resolver_api_call_outcome_commit_id": resolver_api_call_outcome_commit_id,
        "resolver_api_call_outcome_head_commit_id": (resolver_api_call_outcome_head_commit_id),
        "resolver_api_call_outcome_branch_id": resolver_api_call_outcome_branch_id,
        "resolver_api_call_outcome_projection_hash": (resolver_api_call_outcome_projection_hash.strip()),
        "provider_reference": (provider_reference.strip() if provider_reference else None),
    }
    if existing is not None:
        mismatched = [
            field_name
            for field_name, expected_value in expected.items()
            if getattr(existing, field_name) != expected_value
        ]
        if resolved_at is not None and existing.resolved_at != resolved_at:
            mismatched.append("resolved_at")
        if mismatched:
            raise ValueError(
                "Memory event frame already has a different resolved meaning: " + ", ".join(sorted(set(mismatched)))
            )
        return existing

    created = await MemoryWorkingEventMeaning.build_via_memory_working_event_frame(
        memory_working_event_frame_id=memory_working_event_frame.id,
        resolver_api_call_outcome_id=resolver_api_call_outcome_id,
        meaning_text=meaning_text,
        resolver_status=resolver_status,
        resolver_endpoint_ref=resolver_endpoint_ref,
        resolver_discriminant=resolver_discriminant,
        resolver_program_impl_instruction_intent_id=(resolver_program_impl_instruction_intent_id),
        resolver_action_config_id=resolver_action_config_id,
        resolver_api_capability_endpoint_id=resolver_api_capability_endpoint_id,
        resolver_api_call_id=resolver_api_call_id,
        resolver_api_call_key=resolver_api_call_key,
        resolver_request_model_id=resolver_request_model_id,
        resolver_response_model_id=resolver_response_model_id,
        resolver_response_class_config_id=resolver_response_class_config_id,
        resolver_service_operation_id=resolver_service_operation_id,
        resolver_service_operation_config_id=resolver_service_operation_config_id,
        resolver_service_operation_commit_id=resolver_service_operation_commit_id,
        resolver_service_operation_head_commit_id=(resolver_service_operation_head_commit_id),
        resolver_service_operation_branch_id=resolver_service_operation_branch_id,
        resolver_service_operation_projection_hash=(resolver_service_operation_projection_hash),
        resolver_api_call_outcome_commit_id=resolver_api_call_outcome_commit_id,
        resolver_api_call_outcome_head_commit_id=(resolver_api_call_outcome_head_commit_id),
        resolver_api_call_outcome_branch_id=resolver_api_call_outcome_branch_id,
        resolver_api_call_outcome_projection_hash=(resolver_api_call_outcome_projection_hash),
        provider_reference=provider_reference,
        resolved_at=resolved_at,
    )
    memory_working_event_frame.resolved_meaning = created
    return created
    # --- AWARE: LOGIC END record_resolved_meaning


async def build_via_memory_working_item(
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

    # --- AWARE: LOGIC START build_via_memory_working_item
    return MemoryWorkingEventFrame(
        id=stable_memory_working_event_frame_id(
            memory_working_item_id=memory_working_item_id,
            event_id=event_id,
        ),
        event_id=event_id,
    )
    # --- AWARE: LOGIC END build_via_memory_working_item
