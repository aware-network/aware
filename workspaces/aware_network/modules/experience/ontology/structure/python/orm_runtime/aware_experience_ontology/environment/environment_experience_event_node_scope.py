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
    from aware_experience_ontology.projection.projection_experience_node_identity import (
        ProjectionExperienceNodeIdentity,
    )
    from aware_meta_ontology.graph.instance.object_instance_graph_branch import ObjectInstanceGraphBranch
    from aware_reactivity_ontology.event.event_config_condition_config import EventConfigConditionConfig
    from aware_reactivity_ontology.event.event_config_condition_config_scope import EventConfigConditionConfigScope


class EnvironmentExperienceEventNodeScope(ORMModel):
    # Relationships
    event_config_condition_config: EventConfigConditionConfig | None = Field(default=None, exclude=True)
    projection_experience_node_identity: ProjectionExperienceNodeIdentity | None = Field(default=None, exclude=True)
    object_instance_graph_branch: ObjectInstanceGraphBranch | None = Field(default=None, exclude=True)
    event_config_condition_config_scope: EventConfigConditionConfigScope | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.node_scopes")
    event_config_condition_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceEventNodeScope.event_config_condition_config"
    )
    projection_experience_node_identity_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceEventNodeScope.projection_experience_node_identity"
    )
    object_instance_graph_branch_id: UUID | None = Field(
        default=None, description="Foreign key for EnvironmentExperienceEventNodeScope.object_instance_graph_branch"
    )
    event_config_condition_config_scope_id: UUID | None = Field(
        default=None,
        description="Foreign key for EnvironmentExperienceEventNodeScope.event_config_condition_config_scope",
    )

    @classmethod
    async def build_via_environment_experience_event(
        cls,
        environment_experience_event_id: UUID,
        event_config_condition_config_id: UUID,
        projection_experience_node_identity_id: UUID,
        object_instance_graph_branch_id: UUID | None = None,
        event_config_condition_config_scope_id: UUID | None = None,
    ) -> EnvironmentExperienceEventNodeScope:
        """
        Create one environment-scoped event trigger node binding.

        Contract:
        - Identity is derived from
          `(environment_experience_event_id, event_config_condition_config_id,
          projection_experience_node_identity_id)`.
        - This row says which declared graph-binding node may trigger the event.
        - Lowering must resolve the node identity through
          ProjectionExperienceNodeClassIdentity and create/use a Reactivity
          EventConfigConditionConfigScope whose ClassInstanceIdentity belongs to
          the same ProjectionExperienceOIGI lane.
        - Action request target mapping remains under ActionExperienceInvocation
          request fields; this object owns trigger scope only.
        """

        payload = {
            "environment_experience_event_id": environment_experience_event_id,
            "event_config_condition_config_id": event_config_condition_config_id,
            "projection_experience_node_identity_id": projection_experience_node_identity_id,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "event_config_condition_config_scope_id": event_config_condition_config_scope_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_event", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceEventNodeScope):
            return value
        return EnvironmentExperienceEventNodeScope.validate_invocation_value(value)


class EnvironmentExperienceEventNodeScopeBuildViaEnvironmentExperienceEventInput(BaseModel):
    environment_experience_event_id: UUID = Field(description="Foreign key for EnvironmentExperienceEvent.node_scopes")
    event_config_condition_config_id: UUID
    projection_experience_node_identity_id: UUID
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    event_config_condition_config_scope_id: UUID | None = Field(default=None)


class EnvironmentExperienceEventNodeScopeBuildViaEnvironmentExperienceEventOutput(BaseModel):
    value: EnvironmentExperienceEventNodeScope


FUNCTIONS = {
    "EnvironmentExperienceEventNodeScope": {
        "build_via_environment_experience_event": {
            "canonical": {
                "name": "build_via_environment_experience_event",
                "description": "Create one environment-scoped event trigger node binding.\n\nContract:\n- Identity is derived from\n  `(environment_experience_event_id, event_config_condition_config_id,\n  projection_experience_node_identity_id)`.\n- This row says which declared graph-binding node may trigger the event.\n- Lowering must resolve the node identity through\n  ProjectionExperienceNodeClassIdentity and create/use a Reactivity\n  EventConfigConditionConfigScope whose ClassInstanceIdentity belongs to\n  the same ProjectionExperienceOIGI lane.\n- Action request target mapping remains under ActionExperienceInvocation\n  request fields; this object owns trigger scope only.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceEventNodeScopeBuildViaEnvironmentExperienceEventInput,
            "output": EnvironmentExperienceEventNodeScopeBuildViaEnvironmentExperienceEventOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceEventNodeScope",
    "EnvironmentExperienceEventNodeScopeBuildViaEnvironmentExperienceEventInput",
    "EnvironmentExperienceEventNodeScopeBuildViaEnvironmentExperienceEventOutput",
    "FUNCTIONS",
]
