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
    from aware_experience_ontology.program.impl.program_impl_instruction_invoke_attribute_config import (
        ProgramImplInstructionInvokeAttributeConfig,
    )


class ProgramTurnInstructionInvokeAttributeConfig(ORMModel):
    """
    Canonical invoke-argument execution receipt under one ProgramTurnInstructionInvoke.
    Contract:
    - Captures one executed invoke argument contract row.
    - Enables replay parity checks for invoke argument coverage.
    """

    # Relationships
    program_impl_instruction_invoke_attribute_config: ProgramImplInstructionInvokeAttributeConfig | None = Field(
        default=None, exclude=True
    )

    # Foreign Keys
    program_turn_instruction_invoke_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionInvoke.attribute_config_receipts"
    )
    program_impl_instruction_invoke_attribute_config_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionInvokeAttributeConfig.program_impl_instruction_invoke_attribute_config"
    )

    @classmethod
    async def build_via_program_turn_instruction_invoke(
        cls, program_turn_instruction_invoke_id: UUID, program_impl_instruction_invoke_attribute_config_id: UUID
    ) -> ProgramTurnInstructionInvokeAttributeConfig:
        """Create deterministic ProgramTurnInstructionInvokeAttributeConfig under ProgramTurnInstructionInvoke."""

        payload = {
            "program_turn_instruction_invoke_id": program_turn_instruction_invoke_id,
            "program_impl_instruction_invoke_attribute_config_id": program_impl_instruction_invoke_attribute_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_turn_instruction_invoke", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurnInstructionInvokeAttributeConfig):
            return value
        return ProgramTurnInstructionInvokeAttributeConfig.validate_invocation_value(value)


class ProgramTurnInstructionInvokeAttributeConfigBuildViaProgramTurnInstructionInvokeInput(BaseModel):
    program_turn_instruction_invoke_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionInvoke.attribute_config_receipts"
    )
    program_impl_instruction_invoke_attribute_config_id: UUID


class ProgramTurnInstructionInvokeAttributeConfigBuildViaProgramTurnInstructionInvokeOutput(BaseModel):
    value: ProgramTurnInstructionInvokeAttributeConfig


FUNCTIONS = {
    "ProgramTurnInstructionInvokeAttributeConfig": {
        "build_via_program_turn_instruction_invoke": {
            "canonical": {
                "name": "build_via_program_turn_instruction_invoke",
                "description": "Create deterministic ProgramTurnInstructionInvokeAttributeConfig under ProgramTurnInstructionInvoke.",
                "is_constructor": True,
            },
            "input": ProgramTurnInstructionInvokeAttributeConfigBuildViaProgramTurnInstructionInvokeInput,
            "output": ProgramTurnInstructionInvokeAttributeConfigBuildViaProgramTurnInstructionInvokeOutput,
        },
    },
}

__all__ = [
    "ProgramTurnInstructionInvokeAttributeConfig",
    "ProgramTurnInstructionInvokeAttributeConfigBuildViaProgramTurnInstructionInvokeInput",
    "ProgramTurnInstructionInvokeAttributeConfigBuildViaProgramTurnInstructionInvokeOutput",
    "FUNCTIONS",
]
