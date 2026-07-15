from __future__ import annotations

# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
)
from aware_experience_ontology.program.impl.program_impl_instruction_enums import (
    ProgramImplInstructionType,
)

# Stable ids
from aware_experience.stable_ids import stable_program_impl_instruction_id

from aware_meta.runtime.handler_context import (
    current_handler_session,
)


def ensure_bound(instance: object) -> object:
    if getattr(instance, "bound_session", None) is None:
        session = current_handler_session()
        instance.bind_to_session(session)
    return instance


def bind_instruction_payload(
    *,
    instruction: ProgramImplInstruction,
    slot_name: str,
    created_payload: object,
) -> object:
    created_payload_id = getattr(created_payload, "id", None)
    if created_payload_id is None:
        raise RuntimeError(f"ProgramImplInstruction.{slot_name} requires a payload with a deterministic id")

    current_payload = getattr(instruction, slot_name)
    if current_payload is not None:
        current_payload_id = getattr(current_payload, "id", None)
        if current_payload_id != created_payload_id:
            raise RuntimeError(
                "ProgramImplInstruction payload mismatch for existing slot: "
                f"slot={slot_name} existing_id={current_payload_id} requested_id={created_payload_id}"
            )
        return current_payload

    for other_slot in (
        "instruction_input",
        "instruction_let",
        "instruction_bind",
        "instruction_invoke",
        "instruction_expect",
        "instruction_intent",
    ):
        if other_slot == slot_name:
            continue
        if getattr(instruction, other_slot) is not None:
            raise RuntimeError(
                "ProgramImplInstruction payload polymorphism violation: "
                f"slot={slot_name} conflicts_with={other_slot} on instruction_id={instruction.id}"
            )

    setattr(instruction, slot_name, created_payload)
    return created_payload


def ensure_instruction(
    *,
    program_impl_id: UUID,
    sequence: int,
    instruction_type: ProgramImplInstructionType,
) -> ProgramImplInstruction:
    instruction_id = stable_program_impl_instruction_id(
        program_impl_id=program_impl_id,
        sequence=sequence,
    )
    session = current_handler_session()
    existing = session.imap_get(ProgramImplInstruction, instruction_id)
    if existing is not None:
        if (
            existing.program_impl_id != program_impl_id
            or existing.sequence != sequence
            or existing.type != instruction_type
        ):
            raise RuntimeError(
                "ProgramImplInstruction.build_via_program_impl payload mismatch for existing instruction: "
                f"instruction_id={instruction_id}"
            )
        return existing

    created = ProgramImplInstruction(
        id=instruction_id,
        program_impl_id=program_impl_id,
        type=instruction_type,
        sequence=sequence,
    )
    ensure_bound(created)
    return created


async def create_typed_instruction(
    *,
    program_impl_id: UUID,
    sequence: int,
    instruction_type: ProgramImplInstructionType,
    slot_name: str,
    payload_builder,
) -> ProgramImplInstruction:
    instruction = ensure_instruction(
        program_impl_id=program_impl_id,
        sequence=sequence,
        instruction_type=instruction_type,
    )
    instruction_id = instruction.id
    if instruction_id is None:
        raise RuntimeError("ProgramImplInstruction typed constructor requires id")

    created_payload = await payload_builder(instruction_id)
    ensure_bound(created_payload)
    bind_instruction_payload(
        instruction=instruction,
        slot_name=slot_name,
        created_payload=created_payload,
    )
    return instruction
