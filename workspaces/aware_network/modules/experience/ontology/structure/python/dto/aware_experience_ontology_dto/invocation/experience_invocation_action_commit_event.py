from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_reactivity_ontology_dto.event.event import Event


class ExperienceInvocationActionCommitEvent(BaseModel):
    """Event provenance emitted from an Experience invocation action commit."""

    # Relationships
    event: Event | None = Field(default=None)

    # Attributes
    event_role: str = Field(default="emitted")
    description: str | None = Field(default=None)
