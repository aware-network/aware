from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.program_turn_instruction_action import ProgramTurnInstructionAction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction_intent import (
    ProgramImplInstructionIntent,
)
from aware_experience_ontology.stable_ids import (
    stable_program_turn_instruction_action_id,
)

# Reactivity Ontology
from aware_reactivity_ontology.action.action_config import ActionConfig
from aware_reactivity_ontology.event.event_config import EventConfig

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_program_turn_instruction(
    program_turn_instruction_id: UUID,
    program_impl_instruction_intent_id: UUID,
    action_config_id: UUID,
    event_config_id: UUID,
    action_intent_id: UUID,
    intent_key: str,
) -> ProgramTurnInstructionAction:
    """
    Create deterministic ProgramTurnInstructionAction under one instruction.

    Contract:
    - Parent context (`program_turn_instruction_id`) is injected by
      parent-edge lowering.
    - `intent_key` is the same opaque key supplied to Reactivity
      `ActionIntent.create`.
    """

    # --- AWARE: LOGIC START build_via_program_turn_instruction
    normalized_intent_key = str(intent_key or "").strip()
    if not normalized_intent_key:
        raise RuntimeError("ProgramTurnInstructionAction.build requires non-empty intent_key")

    action_receipt_id = stable_program_turn_instruction_action_id(
        program_turn_instruction_id=program_turn_instruction_id,
        program_impl_instruction_intent_id=program_impl_instruction_intent_id,
        action_config_id=action_config_id,
        event_config_id=event_config_id,
        intent_key=normalized_intent_key,
    )

    session = current_handler_session()
    intent_instruction = session.imap_get(ProgramImplInstructionIntent, program_impl_instruction_intent_id)
    if intent_instruction is None:
        raise RuntimeError(
            "ProgramTurnInstructionAction.build requires ProgramImplInstructionIntent in session: "
            + f"{program_impl_instruction_intent_id}"
        )

    if intent_instruction.action_config_id != action_config_id:
        raise RuntimeError(
            "ProgramTurnInstructionAction.build action_config mismatch for intent instruction: "
            + f"instruction_action_config_id={intent_instruction.action_config_id} "
            + f"action_config_id={action_config_id}"
        )
    if intent_instruction.event_config_id != event_config_id:
        raise RuntimeError(
            "ProgramTurnInstructionAction.build event_config mismatch for intent instruction: "
            + f"instruction_event_config_id={intent_instruction.event_config_id} "
            + f"event_config_id={event_config_id}"
        )

    action_config = session.imap_get(ActionConfig, action_config_id)
    event_config = session.imap_get(EventConfig, event_config_id)

    existing = session.imap_get(ProgramTurnInstructionAction, action_receipt_id)
    if existing is not None:
        if (
            existing.program_turn_instruction_id != program_turn_instruction_id
            or existing.program_impl_instruction_intent_id != program_impl_instruction_intent_id
            or existing.action_config_id != action_config_id
            or existing.event_config_id != event_config_id
            or existing.action_intent_id != action_intent_id
            or existing.intent_key != normalized_intent_key
        ):
            raise RuntimeError(
                "ProgramTurnInstructionAction.build payload mismatch for existing receipt: "
                f"program_turn_instruction_action_id={action_receipt_id}"
            )
        if existing.program_impl_instruction_intent is None:
            existing.program_impl_instruction_intent = intent_instruction
        if existing.action_config is None and action_config is not None:
            existing.action_config = action_config
        if existing.event_config is None and event_config is not None:
            existing.event_config = event_config
        return existing

    return ProgramTurnInstructionAction(
        id=action_receipt_id,
        program_turn_instruction_id=program_turn_instruction_id,
        program_impl_instruction_intent_id=program_impl_instruction_intent_id,
        program_impl_instruction_intent=intent_instruction,
        action_config_id=action_config_id,
        action_config=action_config,
        event_config_id=event_config_id,
        event_config=event_config,
        action_intent_id=action_intent_id,
        intent_key=normalized_intent_key,
    )
    # --- AWARE: LOGIC END build_via_program_turn_instruction
