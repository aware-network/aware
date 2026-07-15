from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Meta Ontology Orm Models
from aware_meta_ontology_orm_models.function.function_impl_instruction_enums import FunctionImplValueTransformKind

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.function.function_impl_value_source_transform_operand import (
        FunctionImplValueSourceTransformOperand,
    )
    from aware_meta_ontology_orm_models.primitive.primitive_config import PrimitiveConfig


class FunctionImplValueSourceTransform(ORMModel):
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

    # Foreign Keys
    function_impl_value_source_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSource.source_transform"
    )
    output_primitive_config_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplValueSourceTransform.output_primitive_config"
    )
