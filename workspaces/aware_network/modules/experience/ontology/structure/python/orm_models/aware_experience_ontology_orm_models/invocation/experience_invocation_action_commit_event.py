from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_reactivity_ontology_orm_models.event.event import Event


class ExperienceInvocationActionCommitEvent(ORMModel):
    """Event provenance emitted from an Experience invocation action commit."""

    # Relationships
    event: Event | None = Field(default=None)

    # Attributes
    event_role: str = Field(default="emitted")
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_invocation_action_commit_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionCommit.events"
    )
    event_id: UUID = Field(description="Foreign key for ExperienceInvocationActionCommitEvent.event")
