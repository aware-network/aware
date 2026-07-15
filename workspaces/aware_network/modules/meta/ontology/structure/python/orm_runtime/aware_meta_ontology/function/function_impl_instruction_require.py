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
from aware_meta_ontology.function.function_impl_instruction_enums import (
    FunctionImplRequireCompareOperator,
    FunctionImplRequireKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_meta_ontology.function.function_impl_instruction_require_operand import (
        FunctionImplInstructionRequireOperand,
    )


class FunctionImplInstructionRequire(ORMModel):
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

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_require"
    )

    async def add_operand(self, position: int, value_source_id: UUID) -> FunctionImplInstructionRequireOperand:
        """Attach one deterministic operand source under this `require` payload."""

        payload = {"position": position, "value_source_id": value_source_id}
        result = await invoke_instance(orm_model=self, function_name="add_operand", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_meta_ontology.function.function_impl_instruction_require_operand import (
            FunctionImplInstructionRequireOperand,
        )

        if isinstance(value, FunctionImplInstructionRequireOperand):
            return value
        return FunctionImplInstructionRequireOperand.validate_invocation_value(value)

    @classmethod
    async def build_via_function_impl_instruction(
        cls,
        function_impl_instruction_id: UUID,
        kind: FunctionImplRequireKind,
        compare_operator: FunctionImplRequireCompareOperator | None = None,
        expected_count: int | None = None,
        message: str | None = None,
    ) -> FunctionImplInstructionRequire:
        """
        Create deterministic `require` payload for one FunctionImplInstruction.

        Contract:
        - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "function_impl_instruction_id": function_impl_instruction_id,
            "kind": kind,
            "compare_operator": compare_operator,
            "expected_count": expected_count,
            "message": message,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionRequire):
            return value
        return FunctionImplInstructionRequire.validate_invocation_value(value)


class FunctionImplInstructionRequireAddOperandInput(BaseModel):
    position: int
    value_source_id: UUID


class FunctionImplInstructionRequireAddOperandOutput(BaseModel):
    value: FunctionImplInstructionRequireOperand


class FunctionImplInstructionRequireBuildViaFunctionImplInstructionInput(BaseModel):
    function_impl_instruction_id: UUID = Field(
        description="Foreign key for FunctionImplInstruction.instruction_require"
    )
    kind: FunctionImplRequireKind
    compare_operator: FunctionImplRequireCompareOperator | None = Field(default=None)
    expected_count: int | None = Field(default=None)
    message: str | None = Field(default=None)


class FunctionImplInstructionRequireBuildViaFunctionImplInstructionOutput(BaseModel):
    value: FunctionImplInstructionRequire


FUNCTIONS = {
    "FunctionImplInstructionRequire": {
        "add_operand": {
            "canonical": {
                "name": "add_operand",
                "description": "Attach one deterministic operand source under this `require` payload.",
                "is_constructor": False,
            },
            "input": FunctionImplInstructionRequireAddOperandInput,
            "output": FunctionImplInstructionRequireAddOperandOutput,
        },
        "build_via_function_impl_instruction": {
            "canonical": {
                "name": "build_via_function_impl_instruction",
                "description": "Create deterministic `require` payload for one FunctionImplInstruction.\n\nContract:\n- Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionRequireBuildViaFunctionImplInstructionInput,
            "output": FunctionImplInstructionRequireBuildViaFunctionImplInstructionOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionRequire",
    "FunctionImplInstructionRequireAddOperandInput",
    "FunctionImplInstructionRequireAddOperandOutput",
    "FunctionImplInstructionRequireBuildViaFunctionImplInstructionInput",
    "FunctionImplInstructionRequireBuildViaFunctionImplInstructionOutput",
    "FUNCTIONS",
]
