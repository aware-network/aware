from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Experience Ontology Orm Models
from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_enums import ProgramImplInstructionType

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_bind import (
        ProgramImplInstructionBind,
    )
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_expect import (
        ProgramImplInstructionExpect,
    )
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_input import (
        ProgramImplInstructionInput,
    )
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_intent import (
        ProgramImplInstructionIntent,
    )
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_invoke import (
        ProgramImplInstructionInvoke,
    )
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_let import ProgramImplInstructionLet


class ProgramImplInstruction(ORMModel):
    """Polymorphic instruction for program impl construction."""

    # Relationships
    instruction_input: ProgramImplInstructionInput | None = Field(default=None)
    instruction_let: ProgramImplInstructionLet | None = Field(default=None)
    instruction_bind: ProgramImplInstructionBind | None = Field(default=None)
    instruction_invoke: ProgramImplInstructionInvoke | None = Field(default=None)
    instruction_expect: ProgramImplInstructionExpect | None = Field(default=None)
    instruction_intent: ProgramImplInstructionIntent | None = Field(default=None)

    # Attributes
    type: ProgramImplInstructionType
    sequence: int

    # Foreign Keys
    program_impl_id: UUID = Field(description="Foreign key for ProgramImpl.instructions")
