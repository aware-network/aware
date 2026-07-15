from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_experience_ontology_dto.program.impl.program_impl_instruction_intent import ProgramImplInstructionIntent
    from aware_reactivity_ontology_dto.action.action_config import ActionConfig
    from aware_reactivity_ontology_dto.event.event_config import EventConfig


class ProgramTurnInstructionAction(BaseModel):
    """
    Canonical per-turn program intent receipt.
    Contract:
    - Anchors one `ProgramImplInstructionIntent` execution under one
    `ProgramTurnInstruction`.
    - Stores program provenance for the actor-free Reactivity `ActionIntent`.
    - Does not dispatch, fulfill, or mutate action lifecycle state.
    """

    # Relationships
    program_impl_instruction_intent: ProgramImplInstructionIntent | None = Field(default=None)
    action_config: ActionConfig | None = Field(default=None)
    event_config: EventConfig | None = Field(default=None)

    # Attributes
    action_intent_id: UUID
    intent_key: str
