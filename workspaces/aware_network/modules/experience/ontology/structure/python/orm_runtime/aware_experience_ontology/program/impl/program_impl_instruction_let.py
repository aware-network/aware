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


class ProgramImplInstructionLet(ORMModel):
    """
    Program local binding step.
    Contract:
    - Deterministic/pure computation only.
    - No runtime effects.
    """

    # Attributes
    name: str
    value_expr: JsonObject

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_let"
    )

    @classmethod
    async def build_via_program_impl_instruction(
        cls, program_impl_instruction_id: UUID, name: str, value_expr: JsonObject
    ) -> ProgramImplInstructionLet:
        """
        Create deterministic let payload for one ProgramImplInstruction.

        Contract:
        - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {"program_impl_instruction_id": program_impl_instruction_id, "name": name, "value_expr": value_expr}
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionLet):
            return value
        return ProgramImplInstructionLet.validate_invocation_value(value)


class ProgramImplInstructionLetBuildViaProgramImplInstructionInput(BaseModel):
    program_impl_instruction_id: UUID = Field(description="Foreign key for ProgramImplInstruction.instruction_let")
    name: str
    value_expr: JsonObject


class ProgramImplInstructionLetBuildViaProgramImplInstructionOutput(BaseModel):
    value: ProgramImplInstructionLet


FUNCTIONS = {
    "ProgramImplInstructionLet": {
        "build_via_program_impl_instruction": {
            "canonical": {
                "name": "build_via_program_impl_instruction",
                "description": "Create deterministic let payload for one ProgramImplInstruction.\n\nContract:\n- Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionLetBuildViaProgramImplInstructionInput,
            "output": ProgramImplInstructionLetBuildViaProgramImplInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionLet",
    "ProgramImplInstructionLetBuildViaProgramImplInstructionInput",
    "ProgramImplInstructionLetBuildViaProgramImplInstructionOutput",
    "FUNCTIONS",
]
