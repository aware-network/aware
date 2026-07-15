from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.event.event_config import EventConfig


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
