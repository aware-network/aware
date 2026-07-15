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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_experience_ontology.program.program_turn_instruction import ProgramTurnInstruction
    from aware_experience_ontology.turn.turn import Turn


class ProgramTurn(ORMModel):
    # Relationships
    turn: Turn | None = Field(default=None, exclude=True)
    instructions: list[ProgramTurnInstruction] = Field(default_factory=list, exclude=True)

    # Attributes
    order: int

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.turns")
    turn_id: UUID = Field(description="Foreign key for ProgramTurn.turn")

    async def create_instruction(self, program_instruction_id: UUID, sequence: int) -> ProgramTurnInstruction:
        """
        Create one instruction execution receipt under this ProgramTurn.

        Contract:
        - Mutates only ProgramTurn membership (`instructions`).
        - Instruction linkage is typed via `aware_experience.program.impl.ProgramImplInstruction`.
        """

        payload = {"program_instruction_id": program_instruction_id, "sequence": sequence}
        result = await invoke_instance(orm_model=self, function_name="create_instruction", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_turn_instruction import ProgramTurnInstruction

        if isinstance(value, ProgramTurnInstruction):
            return value
        return ProgramTurnInstruction.validate_invocation_value(value)

    @classmethod
    async def build_via_program(cls, program_id: UUID, turn_id: UUID, order: int = 0) -> ProgramTurn:
        """Create a deterministic ProgramTurn."""

        payload = {"program_id": program_id, "turn_id": turn_id, "order": order}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurn):
            return value
        return ProgramTurn.validate_invocation_value(value)


class ProgramTurnCreateInstructionInput(BaseModel):
    program_instruction_id: UUID
    sequence: int


class ProgramTurnCreateInstructionOutput(BaseModel):
    value: ProgramTurnInstruction


class ProgramTurnBuildViaProgramInput(BaseModel):
    program_id: UUID = Field(description="Foreign key for Program.turns")
    turn_id: UUID
    order: int = Field(default=0)


class ProgramTurnBuildViaProgramOutput(BaseModel):
    value: ProgramTurn


FUNCTIONS = {
    "ProgramTurn": {
        "create_instruction": {
            "canonical": {
                "name": "create_instruction",
                "description": "Create one instruction execution receipt under this ProgramTurn.\n\nContract:\n- Mutates only ProgramTurn membership (`instructions`).\n- Instruction linkage is typed via `aware_experience.program.impl.ProgramImplInstruction`.",
                "is_constructor": False,
            },
            "input": ProgramTurnCreateInstructionInput,
            "output": ProgramTurnCreateInstructionOutput,
        },
        "build_via_program": {
            "canonical": {
                "name": "build_via_program",
                "description": "Create a deterministic ProgramTurn.",
                "is_constructor": True,
            },
            "input": ProgramTurnBuildViaProgramInput,
            "output": ProgramTurnBuildViaProgramOutput,
        },
    },
}

__all__ = [
    "ProgramTurn",
    "ProgramTurnCreateInstructionInput",
    "ProgramTurnCreateInstructionOutput",
    "ProgramTurnBuildViaProgramInput",
    "ProgramTurnBuildViaProgramOutput",
    "FUNCTIONS",
]
