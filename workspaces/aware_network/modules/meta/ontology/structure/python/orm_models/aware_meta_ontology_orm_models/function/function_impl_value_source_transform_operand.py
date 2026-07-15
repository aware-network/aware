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


class FunctionImplValueSourceTransformOperand(ORMModel):
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

    # Foreign Keys
    function_impl_value_source_transform_id: UUID = Field(
        description="Foreign key for FunctionImplValueSourceTransform.operands"
    )
    value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceTransformOperand.value_source"
    )
