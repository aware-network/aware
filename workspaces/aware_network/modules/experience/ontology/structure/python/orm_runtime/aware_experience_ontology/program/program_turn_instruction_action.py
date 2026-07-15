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
    from aware_experience_ontology.program.impl.program_impl_instruction_intent import ProgramImplInstructionIntent
    from aware_reactivity_ontology.action.action_config import ActionConfig
    from aware_reactivity_ontology.event.event_config import EventConfig


class ProgramTurnInstructionAction(ORMModel):
    """
    Canonical per-turn program intent receipt.
    Contract:
    - Anchors one `ProgramImplInstructionIntent` execution under one
    `ProgramTurnInstruction`.
    - Stores program provenance for the actor-free Reactivity `ActionIntent`.
    - Does not dispatch, fulfill, or mutate action lifecycle state.
    """

    # Relationships
    program_impl_instruction_intent: ProgramImplInstructionIntent | None = Field(default=None, exclude=True)
    action_config: ActionConfig | None = Field(default=None, exclude=True)
    event_config: EventConfig | None = Field(default=None, exclude=True)

    # Attributes
    action_intent_id: UUID
    intent_key: str

    # Foreign Keys
    program_turn_instruction_id: UUID | None = Field(
        default=None, description="Foreign key for ProgramTurnInstruction.action_receipt"
    )
    program_impl_instruction_intent_id: UUID = Field(
        description="Foreign key for ProgramTurnInstructionAction.program_impl_instruction_intent"
    )
    action_config_id: UUID = Field(description="Foreign key for ProgramTurnInstructionAction.action_config")
    event_config_id: UUID = Field(description="Foreign key for ProgramTurnInstructionAction.event_config")

    @classmethod
    async def build_via_program_turn_instruction(
        cls,
        program_turn_instruction_id: UUID,
        program_impl_instruction_intent_id: UUID,
        action_config_id: UUID,
        event_config_id: UUID,
        action_intent_id: UUID,
        intent_key: str,
    ) -> ProgramTurnInstructionAction:
        """
        Create deterministic ProgramTurnInstructionAction under one instruction.

        Contract:
        - Parent context (`program_turn_instruction_id`) is injected by
          parent-edge lowering.
        - `intent_key` is the same opaque key supplied to Reactivity
          `ActionIntent.create`.
        """

        payload = {
            "program_turn_instruction_id": program_turn_instruction_id,
            "program_impl_instruction_intent_id": program_impl_instruction_intent_id,
            "action_config_id": action_config_id,
            "event_config_id": event_config_id,
            "action_intent_id": action_intent_id,
            "intent_key": intent_key,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_turn_instruction", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramTurnInstructionAction):
            return value
        return ProgramTurnInstructionAction.validate_invocation_value(value)


class ProgramTurnInstructionActionBuildViaProgramTurnInstructionInput(BaseModel):
    program_turn_instruction_id: UUID = Field(description="Foreign key for ProgramTurnInstruction.action_receipt")
    program_impl_instruction_intent_id: UUID
    action_config_id: UUID
    event_config_id: UUID
    action_intent_id: UUID
    intent_key: str


class ProgramTurnInstructionActionBuildViaProgramTurnInstructionOutput(BaseModel):
    value: ProgramTurnInstructionAction


FUNCTIONS = {
    "ProgramTurnInstructionAction": {
        "build_via_program_turn_instruction": {
            "canonical": {
                "name": "build_via_program_turn_instruction",
                "description": "Create deterministic ProgramTurnInstructionAction under one instruction.\n\nContract:\n- Parent context (`program_turn_instruction_id`) is injected by\n  parent-edge lowering.\n- `intent_key` is the same opaque key supplied to Reactivity\n  `ActionIntent.create`.",
                "is_constructor": True,
            },
            "input": ProgramTurnInstructionActionBuildViaProgramTurnInstructionInput,
            "output": ProgramTurnInstructionActionBuildViaProgramTurnInstructionOutput,
        },
    },
}

__all__ = [
    "ProgramTurnInstructionAction",
    "ProgramTurnInstructionActionBuildViaProgramTurnInstructionInput",
    "ProgramTurnInstructionActionBuildViaProgramTurnInstructionOutput",
    "FUNCTIONS",
]
