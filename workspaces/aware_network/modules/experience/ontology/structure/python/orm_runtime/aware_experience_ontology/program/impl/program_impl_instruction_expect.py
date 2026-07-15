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
    from aware_reactivity_ontology.event.event_config import EventConfig


class ProgramImplInstructionExpect(ORMModel):
    """
    Program expectation contract step.
    Contract:
    - Declares expected EventConfig vocabulary.
    - Program does not emit events; runtime owns Event truth.
    """

    # Relationships
    event_config: EventConfig | None = Field(default=None, exclude=True)

    # Attributes
    required: bool = Field(default=True)

    # Foreign Keys
    program_impl_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramImplInstruction.instruction_expect"
    )
    event_config_id: UUID = Field(description="Foreign key for ProgramImplInstructionExpect.event_config")

    @classmethod
    async def build_via_program_impl_instruction(
        cls, program_impl_instruction_id: UUID, event_config_id: UUID, required: bool = True
    ) -> ProgramImplInstructionExpect:
        """
        Create deterministic expect payload for one ProgramImplInstruction.

        Contract:
        - Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.
        """

        payload = {
            "program_impl_instruction_id": program_impl_instruction_id,
            "event_config_id": event_config_id,
            "required": required,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_impl_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramImplInstructionExpect):
            return value
        return ProgramImplInstructionExpect.validate_invocation_value(value)


class ProgramImplInstructionExpectBuildViaProgramImplInstructionInput(BaseModel):
    program_impl_instruction_id: UUID = Field(description="Foreign key for ProgramImplInstruction.instruction_expect")
    event_config_id: UUID
    required: bool = Field(default=True)


class ProgramImplInstructionExpectBuildViaProgramImplInstructionOutput(BaseModel):
    value: ProgramImplInstructionExpect


FUNCTIONS = {
    "ProgramImplInstructionExpect": {
        "build_via_program_impl_instruction": {
            "canonical": {
                "name": "build_via_program_impl_instruction",
                "description": "Create deterministic expect payload for one ProgramImplInstruction.\n\nContract:\n- Parent context (`program_impl_instruction_id`) is injected by parent-edge lowering.",
                "is_constructor": True,
            },
            "input": ProgramImplInstructionExpectBuildViaProgramImplInstructionInput,
            "output": ProgramImplInstructionExpectBuildViaProgramImplInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramImplInstructionExpect",
    "ProgramImplInstructionExpectBuildViaProgramImplInstructionInput",
    "ProgramImplInstructionExpectBuildViaProgramImplInstructionOutput",
    "FUNCTIONS",
]
