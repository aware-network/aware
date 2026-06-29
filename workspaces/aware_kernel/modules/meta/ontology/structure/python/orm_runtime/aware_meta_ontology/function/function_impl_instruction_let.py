from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject


class FunctionImplInstructionLet(ORMModel):
    """Function-local deterministic binding instruction payload."""

    # Attributes
    name: str
    value_expr: JsonObject

    # Foreign Keys
    function_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for FunctionImplInstruction.instruction_let"
    )

    @classmethod
    async def build_via_function_impl_instruction(
        cls, function_impl_instruction_id: UUID, name: str, value_expr: JsonObject
    ) -> FunctionImplInstructionLet:
        """
        Create deterministic `let` payload for one FunctionImplInstruction.

        Contract:
        - Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {"function_impl_instruction_id": function_impl_instruction_id, "name": name, "value_expr": value_expr}
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_function_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, FunctionImplInstructionLet):
            return value
        return FunctionImplInstructionLet.validate_invocation_value(value)


class FunctionImplInstructionLetBuildViaFunctionImplInstructionInput(BaseModel):
    function_impl_instruction_id: UUID = Field(description="Foreign key for FunctionImplInstruction.instruction_let")
    name: str
    value_expr: JsonObject


class FunctionImplInstructionLetBuildViaFunctionImplInstructionOutput(BaseModel):
    value: FunctionImplInstructionLet


FUNCTIONS = {
    "FunctionImplInstructionLet": {
        "build_via_function_impl_instruction": {
            "canonical": {
                "name": "build_via_function_impl_instruction",
                "description": "Create deterministic `let` payload for one FunctionImplInstruction.\n\nContract:\n- Parent context (`function_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": FunctionImplInstructionLetBuildViaFunctionImplInstructionInput,
            "output": FunctionImplInstructionLetBuildViaFunctionImplInstructionOutput,
        },
    },
}

__all__ = [
    "FunctionImplInstructionLet",
    "FunctionImplInstructionLetBuildViaFunctionImplInstructionInput",
    "FunctionImplInstructionLetBuildViaFunctionImplInstructionOutput",
    "FUNCTIONS",
]
