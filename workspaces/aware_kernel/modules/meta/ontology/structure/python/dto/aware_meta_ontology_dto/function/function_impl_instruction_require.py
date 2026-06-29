from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_instruction_enums import (
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
)

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_impl_instruction_require_operand import (
        FunctionImplInstructionRequireOperand,
    )


class FunctionImplInstructionRequire(BaseModel):
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
