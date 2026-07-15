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
    from aware_experience_ontology.invocation.experience_invocation_action_commit_event import (
        ExperienceInvocationActionCommitEvent,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import ObjectInstanceGraphCommit


class ExperienceInvocationActionCommit(ORMModel):
    """
    Commit provenance for one Experience invocation action.
    Contract:
    - `ExperienceInvocationAction` owns the causal relationship.
    - `ObjectInstanceGraphCommit` remains Meta-owned commit truth.
    - Events emitted from the commit are linked through
    `ExperienceInvocationActionCommitEvent`.
    """

    # Relationships
    object_instance_graph_commit: ObjectInstanceGraphCommit | None = Field(default=None)
    events: list[ExperienceInvocationActionCommitEvent] = Field(default_factory=list)

    # Attributes
    commit_role: str = Field(default="mutation")
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_invocation_action_id: UUID = Field(description="Foreign key for ExperienceInvocationAction.commits")
    object_instance_graph_commit_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionCommit.object_instance_graph_commit"
    )

    async def add_event(
        self, event_id: UUID, event_role: str = "emitted", description: str | None = None
    ) -> ExperienceInvocationActionCommitEvent:
        """
        Link one Reactivity event to this invocation action commit.

        Contract:
        - Reactivity owns `Event`.
        - This edge closes the Experience provenance loop: action -> commit -> event.
        """

        payload = {"event_id": event_id, "event_role": event_role, "description": description}
        result = await invoke_instance(orm_model=self, function_name="add_event", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.experience_invocation_action_commit_event import (
            ExperienceInvocationActionCommitEvent,
        )

        if isinstance(value, ExperienceInvocationActionCommitEvent):
            return value
        return ExperienceInvocationActionCommitEvent.validate_invocation_value(value)

    @classmethod
    async def build_via_experience_invocation_action(
        cls,
        experience_invocation_action_id: UUID,
        object_instance_graph_commit_id: UUID,
        commit_role: str = "mutation",
        description: str | None = None,
    ) -> ExperienceInvocationActionCommit:
        """
        Link one Meta-owned graph commit to this invocation action.

        Contract:
        - Parent `ExperienceInvocationAction` scope is propagated by constructor lowering.
        - `commit_role` names whether the commit was produced, consumed, or
          otherwise observed by this action.
        """

        payload = {
            "experience_invocation_action_id": experience_invocation_action_id,
            "object_instance_graph_commit_id": object_instance_graph_commit_id,
            "commit_role": commit_role,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_experience_invocation_action", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceInvocationActionCommit):
            return value
        return ExperienceInvocationActionCommit.validate_invocation_value(value)


class ExperienceInvocationActionCommitAddEventInput(BaseModel):
    event_id: UUID
    event_role: str = Field(default="emitted")
    description: str | None = Field(default=None)


class ExperienceInvocationActionCommitAddEventOutput(BaseModel):
    value: ExperienceInvocationActionCommitEvent


class ExperienceInvocationActionCommitBuildViaExperienceInvocationActionInput(BaseModel):
    experience_invocation_action_id: UUID = Field(description="Foreign key for ExperienceInvocationAction.commits")
    object_instance_graph_commit_id: UUID
    commit_role: str = Field(default="mutation")
    description: str | None = Field(default=None)


class ExperienceInvocationActionCommitBuildViaExperienceInvocationActionOutput(BaseModel):
    value: ExperienceInvocationActionCommit


FUNCTIONS = {
    "ExperienceInvocationActionCommit": {
        "add_event": {
            "canonical": {
                "name": "add_event",
                "description": "Link one Reactivity event to this invocation action commit.\n\nContract:\n- Reactivity owns `Event`.\n- This edge closes the Experience provenance loop: action -> commit -> event.",
                "is_constructor": False,
            },
            "input": ExperienceInvocationActionCommitAddEventInput,
            "output": ExperienceInvocationActionCommitAddEventOutput,
        },
        "build_via_experience_invocation_action": {
            "canonical": {
                "name": "build_via_experience_invocation_action",
                "description": "Link one Meta-owned graph commit to this invocation action.\n\nContract:\n- Parent `ExperienceInvocationAction` scope is propagated by constructor lowering.\n- `commit_role` names whether the commit was produced, consumed, or\n  otherwise observed by this action.",
                "is_constructor": True,
            },
            "input": ExperienceInvocationActionCommitBuildViaExperienceInvocationActionInput,
            "output": ExperienceInvocationActionCommitBuildViaExperienceInvocationActionOutput,
        },
    },
}

__all__ = [
    "ExperienceInvocationActionCommit",
    "ExperienceInvocationActionCommitAddEventInput",
    "ExperienceInvocationActionCommitAddEventOutput",
    "ExperienceInvocationActionCommitBuildViaExperienceInvocationActionInput",
    "ExperienceInvocationActionCommitBuildViaExperienceInvocationActionOutput",
    "FUNCTIONS",
]
