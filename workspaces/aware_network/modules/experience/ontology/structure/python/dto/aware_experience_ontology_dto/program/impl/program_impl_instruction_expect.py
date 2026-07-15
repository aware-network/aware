from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.event.event_config import EventConfig


class ProgramImplInstructionExpect(BaseModel):
    """
    Program expectation contract step.
    Contract:
    - Declares expected EventConfig vocabulary.
    - Program does not emit events; runtime owns Event truth.
    """

    # Relationships
    event_config: EventConfig | None = Field(default=None)

    # Attributes
    required: bool = Field(default=True)
