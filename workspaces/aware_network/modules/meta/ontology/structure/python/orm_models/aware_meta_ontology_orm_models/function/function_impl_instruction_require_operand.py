from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstructionRequireOperand(ORMModel):
    """
    Deterministic operand slot for `FunctionImplInstructionRequire`.
    Contract:
    - Operands are explicit typed sources (`FunctionImplValueSource`), never raw expressions.
    - `position` is compiler-owned operand order for kind-specific arity semantics.
    """

    # Relationships
    value_source: FunctionImplValueSource

    # Attributes
    position: int

    # Foreign Keys
    function_impl_instruction_require_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionRequire.operands"
    )
    value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstructionRequireOperand.value_source"
    )
