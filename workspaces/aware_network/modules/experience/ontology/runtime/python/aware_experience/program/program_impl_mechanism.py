from __future__ import annotations

# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.program.impl.program_impl import ProgramImpl
from aware_experience_ontology.program.impl.program_impl_instruction import (
    ProgramImplInstruction,
)


def require_program_impl_id(program_impl: ProgramImpl, *, fn_name: str) -> UUID:
    program_impl_id = program_impl.id
    if program_impl_id is None:
        raise RuntimeError(f"ProgramImpl.{fn_name} requires id")
    return program_impl_id


def attach_created_instruction(
    *,
    program_impl: ProgramImpl,
    created_instruction: ProgramImplInstruction,
    fn_name: str,
) -> ProgramImplInstruction:
    program_impl_id = require_program_impl_id(program_impl, fn_name=fn_name)
    if created_instruction.program_impl_id != program_impl_id:
        raise RuntimeError(
            f"ProgramImpl.{fn_name} instruction/program mismatch: "
            f"instruction_id={created_instruction.id} program_impl_id={program_impl_id}"
        )

    for existing in program_impl.instructions:
        if existing.id == created_instruction.id:
            return existing
    program_impl.instructions.append(created_instruction)
    return created_instruction
