from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology Dto
from aware_meta_ontology_dto.function.function_impl_instruction_enums import FunctionImplValueTransformKind

if TYPE_CHECKING:
    from aware_meta_ontology_dto.function.function_impl_value_source_transform_operand import (
        FunctionImplValueSourceTransformOperand,
    )
    from aware_meta_ontology_dto.primitive.primitive_config import PrimitiveConfig


class FunctionImplValueSourceTransform(BaseModel):
    """
    Deterministic pure transform payload for `FunctionImplValueSource`.
    Contract:
    - Parent `FunctionImplValueSource.kind` must be `transform`.
    - The transform is pure and deterministic over explicit operand value sources.
    - Transform evaluation is fail-closed on unsupported arity or operand types.
    """

    # Relationships
    output_primitive_config: PrimitiveConfig | None = Field(
        default=None, description="Optional primitive output declaration used by lowering/type checks."
    )
    operands: list[FunctionImplValueSourceTransformOperand] = Field(
        default_factory=list, description="Ordered operand sources local to the transform value-source tree."
    )

    # Attributes
    operation: FunctionImplValueTransformKind
