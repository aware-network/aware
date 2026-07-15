from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject


class FunctionImplInstructionLet(ORMModel):
    """Function-local deterministic binding instruction payload."""

    # Attributes
    name: str
    value_expr: JsonObject

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_let"
    )
