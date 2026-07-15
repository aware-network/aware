from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class ProgramImplInstructionLet(ORMModel):
    """
    Program local binding step.
    Contract:
    - Deterministic/pure computation only.
    - No runtime effects.
    """

    # Attributes
    name: str
    value_expr: JsonObject

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_let"
    )
