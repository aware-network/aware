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
    from aware_experience_ontology.program.program_config_port import ProgramConfigPort


class ProgramImplInstructionBind(ORMModel):
    """
    Program branch+view context selection step.
    Contract:
    - `program_config_port` selects branch connectivity contract.
    - `view_key` selects representation contract.
    - No stable-id resolution occurs in config; runtime resolves at turn execution.
    """

    # Relationships
    program_config_port: ProgramConfigPort | None = Field(default=None, exclude=True)

    # Attributes
    is_active: bool = Field(default=True)
    view_key: str

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_bind"
    )
    program_config_port_id: UUID = Field(description="Foreign key for ProgramImplInstructionBind.program_config_port")

    @classmethod
    async def build_via_program_impl_instruction(
        cls, program_impl_instruction_id: UUID, program_config_port_id: UUID, view_key: str, is_active: bool = True
    ) -> ProgramImplInstructionBind:
        """
        Create deterministic bind payload for one ProgramImplInstruction.

        Contract:
        - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "program_impl_instruction_id": program_impl_instruction_id,
            "program_config_port_id": program_config_port_id,
            "view_key": view_key,
            "is_active": is_active,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionBind):
            return value
        return ProgramImplInstructionBind.validate_invocation_value(value)


class ProgramImplInstructionBindBuildViaProgramImplInstructionInput(BaseModel):
    program_impl_instruction_id: UUID = Field(description="Foreign key for ProgramImplInstruction.instruction_bind")
    program_config_port_id: UUID
    view_key: str
    is_active: bool = Field(default=True)


class ProgramImplInstructionBindBuildViaProgramImplInstructionOutput(BaseModel):
    value: ProgramImplInstructionBind


FUNCTIONS = {
    "ProgramImplInstructionBind": {
        "build_via_program_impl_instruction": {
            "canonical": {
                "name": "build_via_program_impl_instruction",
                "description": "Create deterministic bind payload for one ProgramImplInstruction.\n\nContract:\n- Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionBindBuildViaProgramImplInstructionInput,
            "output": ProgramImplInstructionBindBuildViaProgramImplInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionBind",
    "ProgramImplInstructionBindBuildViaProgramImplInstructionInput",
    "ProgramImplInstructionBindBuildViaProgramImplInstructionOutput",
    "FUNCTIONS",
]
