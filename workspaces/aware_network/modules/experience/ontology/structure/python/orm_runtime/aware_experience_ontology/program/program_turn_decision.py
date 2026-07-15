from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.program_enums import (
    ProgramTurnDecisionReason,
    ProgramTurnTransition,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor


class ProgramTurnInstructionDecision(ORMModel):
    """
    Canonical per-instruction checkpoint decision receipt.
    Contract:
    - Captures runtime transition semantics as commit-backed facts.
    - Linked through `ProgramTurnInstruction` membership.
    """

    # Attributes
    transition: ProgramTurnTransition
    reason: ProgramTurnDecisionReason
    step_index: int
    total_steps: int
    invokes_in_turn: int = Field(default=0)
    elapsed_ms_in_turn: int = Field(default=0)
    awaiting_external_signal: bool = Field(default=False)
    instruction_failed: bool = Field(default=False)

    # Foreign Keys
    program_turn_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.decisions")

    @classmethod
    async def build_via_program_turn_instruction(
        cls,
        program_turn_instruction_id: UUID,
        transition: ProgramTurnTransition,
        reason: ProgramTurnDecisionReason,
        step_index: int,
        total_steps: int,
        invokes_in_turn: int = 0,
        elapsed_ms_in_turn: int = 0,
        awaiting_external_signal: bool = False,
        instruction_failed: bool = False,
    ) -> ProgramTurnInstructionDecision:
        """
        Construct a deterministic ProgramTurnInstructionDecision.

        Contract:
        - Constructor is idempotent for repeated calls with the same payload under one
        ProgramTurnInstruction.
        """

        payload = {
            "program_turn_instruction_id": program_turn_instruction_id,
            "transition": transition,
            "reason": reason,
            "step_index": step_index,
            "total_steps": total_steps,
            "invokes_in_turn": invokes_in_turn,
            "elapsed_ms_in_turn": elapsed_ms_in_turn,
            "awaiting_external_signal": awaiting_external_signal,
            "instruction_failed": instruction_failed,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_turn_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurnInstructionDecision):
            return value
        return ProgramTurnInstructionDecision.validate_invocation_value(value)


class ProgramTurnInstructionDecisionBuildViaProgramTurnInstructionInput(BaseModel):
    program_turn_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.decisions")
    transition: ProgramTurnTransition
    reason: ProgramTurnDecisionReason
    step_index: int
    total_steps: int
    invokes_in_turn: int = Field(default=0)
    elapsed_ms_in_turn: int = Field(default=0)
    awaiting_external_signal: bool = Field(default=False)
    instruction_failed: bool = Field(default=False)


class ProgramTurnInstructionDecisionBuildViaProgramTurnInstructionOutput(BaseModel):
    value: ProgramTurnInstructionDecision


FUNCTIONS = {
    "ProgramTurnInstructionDecision": {
        "build_via_program_turn_instruction": {
            "canonical": {
                "name": "build_via_program_turn_instruction",
                "description": "Construct a deterministic ProgramTurnInstructionDecision.\n\nContract:\n- Constructor is idempotent for repeated calls with the same payload under one ProgramTurnInstruction.",
                "is_constructor": True,
            },
            "input": ProgramTurnInstructionDecisionBuildViaProgramTurnInstructionInput,
            "output": ProgramTurnInstructionDecisionBuildViaProgramTurnInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramTurnInstructionDecision",
    "ProgramTurnInstructionDecisionBuildViaProgramTurnInstructionInput",
    "ProgramTurnInstructionDecisionBuildViaProgramTurnInstructionOutput",
    "FUNCTIONS",
]
