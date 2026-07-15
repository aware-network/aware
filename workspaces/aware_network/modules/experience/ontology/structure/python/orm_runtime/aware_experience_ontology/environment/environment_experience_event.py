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
    from aware_experience_ontology.environment.environment_experience_event_action import (
        EnvironmentExperienceEventAction,
    )
    from aware_experience_ontology.environment.environment_experience_event_node_scope import (
        EnvironmentExperienceEventNodeScope,
    )
    from aware_reactivity_ontology.event.event_config import EventConfig


class EnvironmentExperienceEvent(ORMModel):
    # Relationships
    event_config: EventConfig | None = Field(default=None, exclude=True)
    actions: list[EnvironmentExperienceEventAction] = Field(default_factory=list, exclude=True)
    node_scopes: list[EnvironmentExperienceEventNodeScope] = Field(
        default_factory=list,
        exclude=True,
        description="Declared trigger-node scopes for this environment event.\nContract:\n- Trigger scope is separate from action request target composition.\n- Each row binds one EventConfigConditionConfig to one\nProjectionExperienceNodeIdentity declared by this profile's graph\nbinding.\n- Lowering resolves the node identity through\nProjectionExperienceNodeClassIdentity into a Reactivity\nEventConfigConditionConfigScope carrying Meta ClassInstanceIdentity.",
    )

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.events"
    )
    event_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.event_config")

    async def add_action_experience(self, action_experience_id: UUID) -> EnvironmentExperienceEventAction:
        """Attach one environment-scoped action dispatch mapping to this event."""

        payload = {"action_experience_id": action_experience_id}
        result = await invoke_instance(orm_model=self, function_name="add_action_experience", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_event_action import (
            EnvironmentExperienceEventAction,
        )

        if isinstance(value, EnvironmentExperienceEventAction):
            return value
        return EnvironmentExperienceEventAction.validate_invocation_value(value)

    async def add_node_scope(
        self,
        event_config_condition_config_id: UUID,
        projection_experience_node_identity_id: UUID,
        object_instance_graph_branch_id: UUID | None = None,
        event_config_condition_config_scope_id: UUID | None = None,
    ) -> EnvironmentExperienceEventNodeScope:
        """
        Attach one declared trigger-node scope to this event binding.

        Contract:
        - The node identity must belong to this environment profile's own
          projection experience binding.
        - This is authoring/lowering policy only; Reactivity receives only the
          lowered Meta scope.
        """

        payload = {
            "event_config_condition_config_id": event_config_condition_config_id,
            "projection_experience_node_identity_id": projection_experience_node_identity_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "event_config_condition_config_scope_id": event_config_condition_config_scope_id,
        }
        result = await invoke_instance(orm_model=self, function_name="add_node_scope", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.environment.environment_experience_event_node_scope import (
            EnvironmentExperienceEventNodeScope,
        )

        if isinstance(value, EnvironmentExperienceEventNodeScope):
            return value
        return EnvironmentExperienceEventNodeScope.validate_invocation_value(value)

    @classmethod
    async def build_via_environment_experience_profile_config(
        cls, environment_experience_profile_config_id: UUID, event_config_id: UUID
    ) -> EnvironmentExperienceEvent:
        """
        Construct the canonical EnvironmentExperienceEvent for an environment territory.

        Notes:
        - Identity is derived from `(environment_experience_profile_config_id, event_config_id)`.
        - Constructor does not mutate EnvironmentExperienceProfileConfig directly.
        """

        payload = {
            "environment_experience_profile_config_id": environment_experience_profile_config_id,
            "event_config_id": event_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceEvent):
            return value
        return EnvironmentExperienceEvent.validate_invocation_value(value)


class EnvironmentExperienceEventAddActionExperienceInput(BaseModel):
    action_experience_id: UUID


class EnvironmentExperienceEventAddActionExperienceOutput(BaseModel):
    value: EnvironmentExperienceEventAction


class EnvironmentExperienceEventAddNodeScopeInput(BaseModel):
    event_config_condition_config_id: UUID
    projection_experience_node_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    event_config_condition_config_scope_id: UUID | None = Field(default=None)


class EnvironmentExperienceEventAddNodeScopeOutput(BaseModel):
    value: EnvironmentExperienceEventNodeScope


class EnvironmentExperienceEventBuildViaEnvironmentExperienceProfileConfigInput(BaseModel):
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.events"
    )
    event_config_id: UUID


class EnvironmentExperienceEventBuildViaEnvironmentExperienceProfileConfigOutput(BaseModel):
    value: EnvironmentExperienceEvent


FUNCTIONS = {
    "EnvironmentExperienceEvent": {
        "add_action_experience": {
            "canonical": {
                "name": "add_action_experience",
                "description": "Attach one environment-scoped action dispatch mapping to this event.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceEventAddActionExperienceInput,
            "output": EnvironmentExperienceEventAddActionExperienceOutput,
        },
        "add_node_scope": {
            "canonical": {
                "name": "add_node_scope",
                "description": "Attach one declared trigger-node scope to this event binding.\n\nContract:\n- The node identity must belong to this environment profile's own\n  projection experience binding.\n- This is authoring/lowering policy only; Reactivity receives only the\n  lowered Meta scope.",
                "is_constructor": False,
            },
            "input": EnvironmentExperienceEventAddNodeScopeInput,
            "output": EnvironmentExperienceEventAddNodeScopeOutput,
        },
        "build_via_environment_experience_profile_config": {
            "canonical": {
                "name": "build_via_environment_experience_profile_config",
                "description": "Construct the canonical EnvironmentExperienceEvent for an environment territory.\n\nNotes:\n- Identity is derived from `(environment_experience_profile_config_id, event_config_id)`.\n- Constructor does not mutate EnvironmentExperienceProfileConfig directly.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceEventBuildViaEnvironmentExperienceProfileConfigInput,
            "output": EnvironmentExperienceEventBuildViaEnvironmentExperienceProfileConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceEvent",
    "EnvironmentExperienceEventAddActionExperienceInput",
    "EnvironmentExperienceEventAddActionExperienceOutput",
    "EnvironmentExperienceEventAddNodeScopeInput",
    "EnvironmentExperienceEventAddNodeScopeOutput",
    "EnvironmentExperienceEventBuildViaEnvironmentExperienceProfileConfigInput",
    "EnvironmentExperienceEventBuildViaEnvironmentExperienceProfileConfigOutput",
    "FUNCTIONS",
]
