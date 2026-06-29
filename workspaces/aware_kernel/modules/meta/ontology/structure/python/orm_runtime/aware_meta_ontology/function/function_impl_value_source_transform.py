from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Meta Ontology
from aware_meta_ontology.function.function_impl_instruction_enums import FunctionImplValueTransformKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_impl_value_source_transform_operand import (
        FunctionImplValueSourceTransformOperand,
    )
    from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig


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

    async def add_operand(self, position: int, value_source_id: UUID) -> FunctionImplValueSourceTransformOperand:
        """Add one deterministic transform operand source."""

        payload = {"position": position, "value_source_id": value_source_id}
        result = await invoke_instance(orm_model=self, function_name="add_operand", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_value_source_transform_operand import (
            FunctionImplValueSourceTransformOperand,
        )

        if isinstance(value, FunctionImplValueSourceTransformOperand):
            return value
        return FunctionImplValueSourceTransformOperand.validate_invocation_value(value)

    @classmethod
    async def build_via_function_impl_value_source(
        cls,
        function_impl_value_source_id: UUID,
        operation: FunctionImplValueTransformKind,
        output_primitive_config_id: UUID | None = None,
    ) -> FunctionImplValueSourceTransform:
        """
        Create deterministic transform payload under one FunctionImplValueSource.

        Contract:
        - Parent context (`function_impl_value_source_id`) is injected by parent-edge lowering.
        - Identity is parent-scoped and unique for the owning value source.
        """

        payload = {
            "function_impl_value_source_id": function_impl_value_source_id,
            "operation": operation,
            "output_primitive_config_id": output_primitive_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_value_source", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplValueSourceTransform):
            return value
        return FunctionImplValueSourceTransform.validate_invocation_value(value)


class FunctionImplValueSourceTransformAddOperandInput(BaseModel):
    position: int
    value_source_id: UUID


class FunctionImplValueSourceTransformAddOperandOutput(BaseModel):
    value: FunctionImplValueSourceTransformOperand


class FunctionImplValueSourceTransformBuildViaFunctionImplValueSourceInput(BaseModel):
    function_impl_value_source_id: UUID = Field(description="Foreign key for FunctionImplValueSource.source_transform")
    operation: FunctionImplValueTransformKind
    output_primitive_config_id: UUID | None = Field(default=None)


class FunctionImplValueSourceTransformBuildViaFunctionImplValueSourceOutput(BaseModel):
    value: FunctionImplValueSourceTransform


FUNCTIONS = {
    "FunctionImplValueSourceTransform": {
        "add_operand": {
            "canonical": {
                "name": "add_operand",
                "description": "Add one deterministic transform operand source.",
                "is_constructor": False,
            },
            "input": FunctionImplValueSourceTransformAddOperandInput,
            "output": FunctionImplValueSourceTransformAddOperandOutput,
        },
        "build_via_function_impl_value_source": {
            "canonical": {
                "name": "build_via_function_impl_value_source",
                "description": "Create deterministic transform payload under one FunctionImplValueSource.\n\nContract:\n- Parent context (`function_impl_value_source_id`) is injected by parent-edge lowering.\n- Identity is parent-scoped and unique for the owning value source.",
                "is_constructor": True,
            },
            "input": FunctionImplValueSourceTransformBuildViaFunctionImplValueSourceInput,
            "output": FunctionImplValueSourceTransformBuildViaFunctionImplValueSourceOutput,
        },
    },
}

__all__ = [
    "FunctionImplValueSourceTransform",
    "FunctionImplValueSourceTransformAddOperandInput",
    "FunctionImplValueSourceTransformAddOperandOutput",
    "FunctionImplValueSourceTransformBuildViaFunctionImplValueSourceInput",
    "FunctionImplValueSourceTransformBuildViaFunctionImplValueSourceOutput",
    "FUNCTIONS",
]
