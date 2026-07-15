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
    from aware_reactivity_ontology.event.event import Event


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

    @classmethod
    async def build_via_experience_invocation_action_commit(
        cls,
        experience_invocation_action_commit_id: UUID,
        event_id: UUID,
        event_role: str = "emitted",
        description: str | None = None,
    ) -> ExperienceInvocationActionCommitEvent:
        """
        Link one Reactivity event to one invocation-action commit edge.

        Contract:
        - Parent `ExperienceInvocationActionCommit` scope is propagated by
          constructor lowering.
        - The event remains Reactivity-owned runtime evidence.
        """

        payload = {
            "experience_invocation_action_commit_id": experience_invocation_action_commit_id,
            "event_id": event_id,
            "event_role": event_role,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_experience_invocation_action_commit", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceInvocationActionCommitEvent):
            return value
        return ExperienceInvocationActionCommitEvent.validate_invocation_value(value)


class ExperienceInvocationActionCommitEventBuildViaExperienceInvocationActionCommitInput(BaseModel):
    experience_invocation_action_commit_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionCommit.events"
    )
    event_id: UUID
    event_role: str = Field(default="emitted")
    description: str | None = Field(default=None)


class ExperienceInvocationActionCommitEventBuildViaExperienceInvocationActionCommitOutput(BaseModel):
    value: ExperienceInvocationActionCommitEvent


FUNCTIONS = {
    "ExperienceInvocationActionCommitEvent": {
        "build_via_experience_invocation_action_commit": {
            "canonical": {
                "name": "build_via_experience_invocation_action_commit",
                "description": "Link one Reactivity event to one invocation-action commit edge.\n\nContract:\n- Parent `ExperienceInvocationActionCommit` scope is propagated by\n  constructor lowering.\n- The event remains Reactivity-owned runtime evidence.",
                "is_constructor": True,
            },
            "input": ExperienceInvocationActionCommitEventBuildViaExperienceInvocationActionCommitInput,
            "output": ExperienceInvocationActionCommitEventBuildViaExperienceInvocationActionCommitOutput,
        },
    },
}

__all__ = [
    "ExperienceInvocationActionCommitEvent",
    "ExperienceInvocationActionCommitEventBuildViaExperienceInvocationActionCommitInput",
    "ExperienceInvocationActionCommitEventBuildViaExperienceInvocationActionCommitOutput",
    "FUNCTIONS",
]
