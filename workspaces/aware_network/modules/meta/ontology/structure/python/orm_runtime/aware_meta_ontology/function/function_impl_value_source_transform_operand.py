from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_impl_value_source import FunctionImplValueSource


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

    @classmethod
    async def build_via_function_impl_value_source_transform(
        cls, function_impl_value_source_transform_id: UUID, position: int, value_source_id: UUID
    ) -> FunctionImplValueSourceTransformOperand:
        """Create deterministic operand binding under one transform payload."""

        payload = {
            "function_impl_value_source_transform_id": function_impl_value_source_transform_id,
            "position": position,
            "value_source_id": value_source_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_value_source_transform", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplValueSourceTransformOperand):
            return value
        return FunctionImplValueSourceTransformOperand.validate_invocation_value(value)


class FunctionImplValueSourceTransformOperandBuildViaFunctionImplValueSourceTransformInput(BaseModel):
    function_impl_value_source_transform_id: UUID = Field(
        description="Foreign key for FunctionImplValueSourceTransform.operands"
    )
    position: int
    value_source_id: UUID


class FunctionImplValueSourceTransformOperandBuildViaFunctionImplValueSourceTransformOutput(BaseModel):
    value: FunctionImplValueSourceTransformOperand


FUNCTIONS = {
    "FunctionImplValueSourceTransformOperand": {
        "build_via_function_impl_value_source_transform": {
            "canonical": {
                "name": "build_via_function_impl_value_source_transform",
                "description": "Create deterministic operand binding under one transform payload.",
                "is_constructor": True,
            },
            "input": FunctionImplValueSourceTransformOperandBuildViaFunctionImplValueSourceTransformInput,
            "output": FunctionImplValueSourceTransformOperandBuildViaFunctionImplValueSourceTransformOutput,
        },
    },
}

__all__ = [
    "FunctionImplValueSourceTransformOperand",
    "FunctionImplValueSourceTransformOperandBuildViaFunctionImplValueSourceTransformInput",
    "FunctionImplValueSourceTransformOperandBuildViaFunctionImplValueSourceTransformOutput",
    "FUNCTIONS",
]
