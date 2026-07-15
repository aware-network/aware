from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import BaseModel

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplInstructionRequireOperand(BaseModel):
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
