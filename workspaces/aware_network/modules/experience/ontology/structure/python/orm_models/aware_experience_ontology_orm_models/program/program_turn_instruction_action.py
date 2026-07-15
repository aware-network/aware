from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_experience_ontology_orm_models.program.impl.program_impl_instruction_intent import (
        ProgramImplInstructionIntent,
    )
    from aware_reactivity_ontology_orm_models.action.action_config import ActionConfig
    from aware_reactivity_ontology_orm_models.event.event_config import EventConfig


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
