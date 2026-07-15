from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_intent import ProgramImplInstructionIntent
from aware_experience_ontology.program.impl.program_impl_instruction_intent_activation_field_binding import (
    ProgramImplInstructionIntentActivationFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_outcome_field_binding import (
    ProgramImplInstructionIntentOutcomeFieldBinding,
)
from aware_experience_ontology.program.impl.program_impl_instruction_intent_receipt_field_binding import (
    ProgramImplInstructionIntentReceiptFieldBinding,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_program_impl_instruction_intent_id
from aware_reactivity.stable_ids import stable_event_config_action_config_id
from aware_reactivity_ontology.event.event_config_action_config import (
    EventConfigActionConfig,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_activation_field_binding(
    program_impl_instruction_intent: ProgramImplInstructionIntent,
    source_class_config_id: UUID,
    source_attribute_config_id: UUID,
    target_request_attribute_config_id: UUID,
    source_input_key: str,
    required: bool = True,
    position: int | None = None,
) -> ProgramImplInstructionIntentActivationFieldBinding:
    # --- AWARE: LOGIC START add_activation_field_binding
    intent_id = program_impl_instruction_intent.id
    if intent_id is None:
        raise RuntimeError("ProgramImplInstructionIntent.add_activation_field_binding requires id")
    created = await ProgramImplInstructionIntentActivationFieldBinding.build_via_program_impl_instruction_intent(
        program_impl_instruction_intent_id=intent_id,
        source_class_config_id=source_class_config_id,
        source_attribute_config_id=source_attribute_config_id,
        target_request_attribute_config_id=target_request_attribute_config_id,
        source_input_key=source_input_key,
        required=required,
        position=position,
    )
    for existing in program_impl_instruction_intent.activation_field_bindings:
        if existing.id == created.id:
            return existing
    program_impl_instruction_intent.activation_field_bindings.append(created)
    return created
    # --- AWARE: LOGIC END add_activation_field_binding


async def add_outcome_field_binding(
    program_impl_instruction_intent: ProgramImplInstructionIntent,
    source_program_impl_instruction_intent_id: UUID,
    source_response_attribute_config_id: UUID,
    target_request_attribute_config_id: UUID,
    required: bool = True,
    position: int | None = None,
) -> ProgramImplInstructionIntentOutcomeFieldBinding:
    # --- AWARE: LOGIC START add_outcome_field_binding
    intent_id = program_impl_instruction_intent.id
    if intent_id is None:
        raise RuntimeError("ProgramImplInstructionIntent.add_outcome_field_binding requires id")
    created = await ProgramImplInstructionIntentOutcomeFieldBinding.build_via_program_impl_instruction_intent(
        program_impl_instruction_intent_id=intent_id,
        source_program_impl_instruction_intent_id=(source_program_impl_instruction_intent_id),
        source_response_attribute_config_id=source_response_attribute_config_id,
        target_request_attribute_config_id=target_request_attribute_config_id,
        required=required,
        position=position,
    )
    for existing in program_impl_instruction_intent.outcome_field_bindings:
        if existing.id == created.id:
            return existing
    program_impl_instruction_intent.outcome_field_bindings.append(created)
    return created
    # --- AWARE: LOGIC END add_outcome_field_binding


async def add_receipt_field_binding(
    program_impl_instruction_intent: ProgramImplInstructionIntent,
    source_program_impl_instruction_intent_id: UUID,
    source_receipt_class_config_id: UUID,
    source_receipt_attribute_config_id: UUID,
    target_request_attribute_config_id: UUID,
    required: bool = True,
    position: int | None = None,
) -> ProgramImplInstructionIntentReceiptFieldBinding:
    # --- AWARE: LOGIC START add_receipt_field_binding
    intent_id = program_impl_instruction_intent.id
    if intent_id is None:
        raise RuntimeError("ProgramImplInstructionIntent.add_receipt_field_binding requires id")
    created = await ProgramImplInstructionIntentReceiptFieldBinding.build_via_program_impl_instruction_intent(
        program_impl_instruction_intent_id=intent_id,
        source_program_impl_instruction_intent_id=(source_program_impl_instruction_intent_id),
        source_receipt_class_config_id=source_receipt_class_config_id,
        source_receipt_attribute_config_id=source_receipt_attribute_config_id,
        target_request_attribute_config_id=target_request_attribute_config_id,
        required=required,
        position=position,
    )
    for existing in program_impl_instruction_intent.receipt_field_bindings:
        if existing.id == created.id:
            return existing
    program_impl_instruction_intent.receipt_field_bindings.append(created)
    return created
    # --- AWARE: LOGIC END add_receipt_field_binding


async def build_via_program_impl_instruction(
    program_impl_instruction_id: UUID, action_config_id: UUID, event_config_id: UUID
) -> ProgramImplInstructionIntent:
    """
    Create deterministic intent payload for one ProgramImplInstruction.

    Contract:
    - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
    """

    # --- AWARE: LOGIC START build_via_program_impl_instruction

    instruction_intent_id = stable_program_impl_instruction_intent_id(
        program_impl_instruction_id=program_impl_instruction_id,
    )
    session = current_handler_session()
    binding_id = stable_event_config_action_config_id(
        event_config_id=event_config_id,
        action_config_id=action_config_id,
    )
    if session.imap_get(EventConfigActionConfig, binding_id) is None:
        raise RuntimeError(
            "ProgramImpl.create_intent_instruction requires EventConfigActionConfig "
            + "binding to exist in current session: "
            + f"action_config_id={action_config_id} event_config_id={event_config_id}"
        )
    existing = session.imap_get(ProgramImplInstructionIntent, instruction_intent_id)
    if existing is not None:
        if existing.action_config_id != action_config_id or existing.event_config_id != event_config_id:
            raise RuntimeError(
                "ProgramImplInstructionIntent.build payload mismatch for existing "
                + "instruction intent: "
                + f"instruction_intent_id={instruction_intent_id}"
            )
        return existing

    return ProgramImplInstructionIntent(
        id=instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
    )
    # --- AWARE: LOGIC END build_via_program_impl_instruction
