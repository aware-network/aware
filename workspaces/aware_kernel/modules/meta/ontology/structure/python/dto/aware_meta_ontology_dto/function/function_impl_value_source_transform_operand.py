from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import BaseModel

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_impl_value_source import FunctionImplValueSource


class FunctionImplValueSourceTransformOperand(BaseModel):
    """
    Ordered operand slot for `FunctionImplValueSourceTransform`.
    Contract:
    - Operands are value sources, never raw expression JSON.
    - `position` is compiler-owned operand order for transform arity semantics.
    """

    # Relationships
    value_source: FunctionImplValueSource

    # Attributes
    position: int
