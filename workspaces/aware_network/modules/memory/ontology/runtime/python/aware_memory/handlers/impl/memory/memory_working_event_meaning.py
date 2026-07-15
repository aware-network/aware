from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from datetime import datetime
from uuid import UUID

# Memory Ontology
from aware_memory_ontology.memory.memory_working_event_meaning import MemoryWorkingEventMeaning

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from datetime import timezone

from aware_memory_ontology.stable_ids import stable_memory_working_event_meaning_id

# --- AWARE: USER_IMPORTS END


async def build_via_memory_working_event_frame(
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
    """
    Build one normalized provider result with terminal resolver evidence.
    """

    # --- AWARE: LOGIC START build_via_memory_working_event_frame
    meaning_text_norm = meaning_text.strip()
    if not meaning_text_norm:
        raise ValueError("Memory resolved event meaning requires non-empty meaning_text")
    if resolver_status.strip().lower() != "succeeded":
        raise ValueError("Memory resolved event meaning requires resolver_status='succeeded'")

    required_text = {
        "resolver_endpoint_ref": resolver_endpoint_ref,
        "resolver_discriminant": resolver_discriminant,
        "resolver_service_operation_projection_hash": (resolver_service_operation_projection_hash),
        "resolver_api_call_outcome_projection_hash": (resolver_api_call_outcome_projection_hash),
    }
    normalized_text: dict[str, str] = {}
    for field_name, field_value in required_text.items():
        value = field_value.strip()
        if not value:
            raise ValueError(f"Memory resolved event meaning requires non-empty {field_name}")
        normalized_text[field_name] = value

    return MemoryWorkingEventMeaning(
        id=stable_memory_working_event_meaning_id(
            memory_working_event_frame_id=memory_working_event_frame_id,
            resolver_api_call_outcome_id=resolver_api_call_outcome_id,
        ),
        memory_working_event_frame_id=memory_working_event_frame_id,
        meaning_text=meaning_text_norm,
        provider_reference=(provider_reference.strip() if provider_reference else None),
        resolved_at=resolved_at or datetime.now(timezone.utc),
        resolver_status="succeeded",
        resolver_endpoint_ref=normalized_text["resolver_endpoint_ref"],
        resolver_discriminant=normalized_text["resolver_discriminant"],
        resolver_program_impl_instruction_intent_id=(resolver_program_impl_instruction_intent_id),
        resolver_action_config_id=resolver_action_config_id,
        resolver_api_capability_endpoint_id=resolver_api_capability_endpoint_id,
        resolver_api_call_id=resolver_api_call_id,
        resolver_api_call_key=resolver_api_call_key,
        resolver_request_model_id=resolver_request_model_id,
        resolver_api_call_outcome_id=resolver_api_call_outcome_id,
        resolver_response_model_id=resolver_response_model_id,
        resolver_response_class_config_id=resolver_response_class_config_id,
        resolver_service_operation_id=resolver_service_operation_id,
        resolver_service_operation_config_id=resolver_service_operation_config_id,
        resolver_service_operation_commit_id=resolver_service_operation_commit_id,
        resolver_service_operation_head_commit_id=(resolver_service_operation_head_commit_id),
        resolver_service_operation_branch_id=resolver_service_operation_branch_id,
        resolver_service_operation_projection_hash=normalized_text["resolver_service_operation_projection_hash"],
        resolver_api_call_outcome_commit_id=resolver_api_call_outcome_commit_id,
        resolver_api_call_outcome_head_commit_id=(resolver_api_call_outcome_head_commit_id),
        resolver_api_call_outcome_branch_id=resolver_api_call_outcome_branch_id,
        resolver_api_call_outcome_projection_hash=normalized_text["resolver_api_call_outcome_projection_hash"],
    )
    # --- AWARE: LOGIC END build_via_memory_working_event_frame
