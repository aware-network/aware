from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_impl_instruction_enums import (
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.function.function_impl_instruction_require_operand import (
        FunctionImplInstructionRequireOperand,
    )


class FunctionImplInstructionRequire(ORMModel):
    """
    Deterministic guard payload for function execution rail.
    Notes:
    - Grammar lowering for `require` is staged after this ontology contract.
    - Runtime must remain fail-closed until lowering/execution support is complete.
    """

    # Relationships
    operands: list[FunctionImplInstructionRequireOperand] = Field(default_factory=list)

    # Attributes
    kind: FunctionImplRequireKind
    compare_operator: FunctionImplRequireCompareOperator | None = Field(default=None)
    expected_count: int | None = Field(default=None)
    message: str | None = Field(default=None)

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_require"
    )
