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
    from aware_experience_ontology.program.program_config_input_config import ProgramConfigInputConfig


class ProgramImplInstructionInput(ORMModel):
    """Program input as instruction"""

    # Relationships
    program_config_input_config: ProgramConfigInputConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_input"
    )
    program_config_input_config_id: UUID = Field(
        description="Foreign key for ProgramImplInstructionInput.program_config_input_config"
    )

    @classmethod
    async def build_via_program_impl_instruction(
        cls, program_impl_instruction_id: UUID, program_config_input_config_id: UUID
    ) -> ProgramImplInstructionInput:
        """Create a deterministic ProgramImplInstructionInput."""

        payload = {
            "program_impl_instruction_id": program_impl_instruction_id,
            "program_config_input_config_id": program_config_input_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionInput):
            return value
        return ProgramImplInstructionInput.validate_invocation_value(value)


class ProgramImplInstructionInputBuildViaProgramImplInstructionInput(BaseModel):
    program_impl_instruction_id: UUID = Field(description="Foreign key for ProgramImplInstruction.instruction_input")
    program_config_input_config_id: UUID


class ProgramImplInstructionInputBuildViaProgramImplInstructionOutput(BaseModel):
    value: ProgramImplInstructionInput


FUNCTIONS = {
    "ProgramImplInstructionInput": {
        "build_via_program_impl_instruction": {
            "canonical": {
                "name": "build_via_program_impl_instruction",
                "description": "Create a deterministic ProgramImplInstructionInput.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionInputBuildViaProgramImplInstructionInput,
            "output": ProgramImplInstructionInputBuildViaProgramImplInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionInput",
    "ProgramImplInstructionInputBuildViaProgramImplInstructionInput",
    "ProgramImplInstructionInputBuildViaProgramImplInstructionOutput",
    "FUNCTIONS",
]
