from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_intent_outcome_field_binding import (
    ProgramImplInstructionIntentOutcomeFieldBinding,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_program_impl_instruction_intent_outcome_field_binding_id,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_meta.runtime.handler_context import current_handler_session
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# --- AWARE: USER_IMPORTS END


async def build_via_program_impl_instruction_intent(
    program_impl_instruction_intent_id: UUID,
    source_program_impl_instruction_intent_id: UUID,
    source_response_attribute_config_id: UUID,
    target_request_attribute_config_id: UUID,
    required: bool = True,
    position: int | None = None,
) -> ProgramImplInstructionIntentOutcomeFieldBinding:
    """
    Create one deterministic prior-outcome field edge under its target intent.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction_intent
    if position is not None and position < 0:
        raise RuntimeError("Program continuation outcome binding requires position >= 0")
    session = current_handler_session()
    required_refs = (
        (
            ProgramImplInstructionIntent,
            program_impl_instruction_intent_id,
            "target intent",
        ),
        (
            ProgramImplInstructionIntent,
            source_program_impl_instruction_intent_id,
            "source intent",
        ),
        (AttributeConfig, source_response_attribute_config_id, "source attribute"),
        (
            AttributeConfig,
            target_request_attribute_config_id,
            "target request attribute",
        ),
    )
    for model, object_id, label in required_refs:
        if session.imap_get(model, object_id) is None:
            raise RuntimeError(f"Program continuation outcome binding requires {label}: {object_id}")

    binding_id = stable_program_impl_instruction_intent_outcome_field_binding_id(
        program_impl_instruction_intent_id=program_impl_instruction_intent_id,
        source_program_impl_instruction_intent_id=(source_program_impl_instruction_intent_id),
        source_response_attribute_config_id=source_response_attribute_config_id,
        target_request_attribute_config_id=target_request_attribute_config_id,
    )
    existing = session.imap_get(ProgramImplInstructionIntentOutcomeFieldBinding, binding_id)
    if existing is not None:
        if (
            existing.program_impl_instruction_intent_id != program_impl_instruction_intent_id
            or existing.source_program_impl_instruction_intent_id != source_program_impl_instruction_intent_id
            or existing.source_response_attribute_config_id != source_response_attribute_config_id
            or existing.target_request_attribute_config_id != target_request_attribute_config_id
            or existing.required != required
            or existing.position != position
        ):
            raise RuntimeError("Program continuation outcome binding payload mismatch: " + f"binding_id={binding_id}")
        return existing

    return ProgramImplInstructionIntentOutcomeFieldBinding(
        id=binding_id,
        program_impl_instruction_intent_id=program_impl_instruction_intent_id,
        source_program_impl_instruction_intent_id=(source_program_impl_instruction_intent_id),
        source_response_attribute_config_id=source_response_attribute_config_id,
        target_request_attribute_config_id=target_request_attribute_config_id,
        required=required,
        position=position,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction_intent
