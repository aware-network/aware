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
    from aware_experience_ontology.action.action_experience import ActionExperience


class EnvironmentExperienceEventAction(ORMModel):
    # Relationships
    action_experience: ActionExperience | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.actions")
    action_experience_id: UUID = Field(description="Foreign key for EnvironmentExperienceEventAction.action_experience")

    @classmethod
    async def build_via_environment_experience_event(
        cls, environment_experience_event_id: UUID, action_experience_id: UUID
    ) -> EnvironmentExperienceEventAction:
        """
        Create a deterministic EnvironmentExperienceEventAction association edge.

        Notes:
        - Identity is derived from `(environment_experience_event_id, action_experience_id)`.
        """

        payload = {
            "environment_experience_event_id": environment_experience_event_id,
            "action_experience_id": action_experience_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_event", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceEventAction):
            return value
        return EnvironmentExperienceEventAction.validate_invocation_value(value)


class EnvironmentExperienceEventActionBuildViaEnvironmentExperienceEventInput(BaseModel):
    environment_experience_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.actions")
    action_experience_id: UUID


class EnvironmentExperienceEventActionBuildViaEnvironmentExperienceEventOutput(BaseModel):
    value: EnvironmentExperienceEventAction


FUNCTIONS = {
    "EnvironmentExperienceEventAction": {
        "build_via_environment_experience_event": {
            "canonical": {
                "name": "build_via_environment_experience_event",
                "description": "Create a deterministic EnvironmentExperienceEventAction association edge.\n\nNotes:\n- Identity is derived from `(environment_experience_event_id, action_experience_id)`.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceEventActionBuildViaEnvironmentExperienceEventInput,
            "output": EnvironmentExperienceEventActionBuildViaEnvironmentExperienceEventOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceEventAction",
    "EnvironmentExperienceEventActionBuildViaEnvironmentExperienceEventInput",
    "EnvironmentExperienceEventActionBuildViaEnvironmentExperienceEventOutput",
    "FUNCTIONS",
]
