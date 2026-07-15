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

    @classmethod
    async def create_via_function_impl_instruction_require(
        cls, function_impl_instruction_require_id: UUID, position: int, value_source_id: UUID
    ) -> FunctionImplInstructionRequireOperand:
        """Create deterministic operand binding under one `require` payload."""

        payload = {
            "function_impl_instruction_require_id": function_impl_instruction_require_id,
            "position": position,
            "value_source_id": value_source_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_function_impl_instruction_require", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionRequireOperand):
            return value
        return FunctionImplInstructionRequireOperand.validate_invocation_value(value)


class FunctionImplInstructionRequireOperandCreateViaFunctionImplInstructionRequireInput(BaseModel):
    function_impl_instruction_require_id: UUID = Field(
        description="Foreign key for FunctionImplInstructionRequire.operands"
    )
    position: int
    value_source_id: UUID


class FunctionImplInstructionRequireOperandCreateViaFunctionImplInstructionRequireOutput(BaseModel):
    value: FunctionImplInstructionRequireOperand


FUNCTIONS = {
    "FunctionImplInstructionRequireOperand": {
        "create_via_function_impl_instruction_require": {
            "canonical": {
                "name": "create_via_function_impl_instruction_require",
                "description": "Create deterministic operand binding under one `require` payload.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionRequireOperandCreateViaFunctionImplInstructionRequireInput,
            "output": FunctionImplInstructionRequireOperandCreateViaFunctionImplInstructionRequireOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionRequireOperand",
    "FunctionImplInstructionRequireOperandCreateViaFunctionImplInstructionRequireInput",
    "FunctionImplInstructionRequireOperandCreateViaFunctionImplInstructionRequireOutput",
    "FUNCTIONS",
]
