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
    from aware_api_ontology.api.api_view import ApiView
    from aware_experience_ontology.projection.projection_experience_view_instance import (
        ProjectionExperienceViewInstance,
    )
    from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
        ProjectionExperienceViewInvocationActionConfig,
    )
    from aware_experience_ontology.projection.projection_experience_view_state_provider import (
        ProjectionExperienceViewStateProvider,
    )


class ProjectionExperienceView(ORMModel):
    # Relationships
    api_view: ApiView | None = Field(
        default=None, description="API-owned lower view-state contract this Experience view exposes."
    )
    invocation_action_configs: list[ProjectionExperienceViewInvocationActionConfig] = Field(
        default_factory=list, description="Experience-owned invocation actions that panes may render and dispatch."
    )
    view_instances: list[ProjectionExperienceViewInstance] = Field(
        default_factory=list, description="Concrete rendered/view-state instances of this view."
    )
    state_providers: list[ProjectionExperienceViewStateProvider] = Field(
        default_factory=list,
        exclude=True,
        description="Canonical provider binding that turns host-owned materialized state into this view state.",
    )

    # Attributes
    name: str

    # Foreign Keys
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_views"
    )
    api_view_id: UUID = Field(description="Foreign key for ProjectionExperienceView.api_view")

    async def set_state_provider(
        self, provider_ref: str, provider_kind: str = "runtime_callable", purity: str = "pure_read"
    ) -> ProjectionExperienceViewStateProvider:
        """
        Bind the pure read provider for this exact ProjectionExperienceView.

        Contract:
        - The view remains the semantic selector and owns provider selection.
        - The provider must only read host-owned materialized state and produce the declared state model.
        - Runtime callables and SDK functions are adapter implementations, not semantic authority.
        """

        payload = {"provider_ref": provider_ref, "provider_kind": provider_kind, "purity": purity}
        result = await invoke_instance(orm_model=self, function_name="set_state_provider", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_view_state_provider import (
            ProjectionExperienceViewStateProvider,
        )

        if isinstance(value, ProjectionExperienceViewStateProvider):
            return value
        return ProjectionExperienceViewStateProvider.validate_invocation_value(value)

    async def add_invocation_action(
        self,
        api_view_capability_endpoint_id: UUID,
        experience_invocation_action_config_id: UUID,
        action_key: str,
        sdk_operation_api_view_capability_endpoint_id: UUID | None = None,
        label: str | None = None,
        receipt_policy: str | None = None,
        confirmation_policy: str | None = None,
        optimistic_policy: str | None = None,
    ) -> ProjectionExperienceViewInvocationActionConfig:
        """
        Bind one Experience-owned invocation action to this view.

        Contract:
        - `api_view_capability_endpoint` is the API-owned view action truth.
        - `sdk_operation_api_view_capability_endpoint`, when present, wraps the
          same API view action with an SDK operation.
        - `experience_invocation_action_config` carries executable API endpoint XOR
          SDK operation target metadata.
        - `action_key` is copied from API-owned view action truth for panes.
        - This is not a Reactivity `ActionConfig`; it is a user/client invocation capability.
        """

        payload = {
            "api_view_capability_endpoint_id": api_view_capability_endpoint_id,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "action_key": action_key,
            "sdk_operation_api_view_capability_endpoint_id": sdk_operation_api_view_capability_endpoint_id,
            "label": label,
            "receipt_policy": receipt_policy,
            "confirmation_policy": confirmation_policy,
            "optimistic_policy": optimistic_policy,
        }
        result = await invoke_instance(orm_model=self, function_name="add_invocation_action", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
            ProjectionExperienceViewInvocationActionConfig,
        )

        if isinstance(value, ProjectionExperienceViewInvocationActionConfig):
            return value
        return ProjectionExperienceViewInvocationActionConfig.validate_invocation_value(value)

    async def bind_invocation_action_config(
        self,
        api_view_capability_endpoint_id: UUID,
        experience_invocation_action_config_id: UUID,
        action_key: str,
        sdk_operation_api_view_capability_endpoint_id: UUID | None = None,
        label: str | None = None,
        receipt_policy: str | None = None,
        confirmation_policy: str | None = None,
        optimistic_policy: str | None = None,
    ) -> ProjectionExperienceViewInvocationActionConfig:
        """
        Bind one generic Experience invocation target config to an API-owned
        view action exposed by this view.

        Contract:
        - `api_view_capability_endpoint` is mandatory view-action truth.
        - Target execution metadata stays on `ExperienceInvocationActionConfig`.
        - Optional SDK operation view binding wraps the same API view action.
        """

        payload = {
            "api_view_capability_endpoint_id": api_view_capability_endpoint_id,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "action_key": action_key,
            "sdk_operation_api_view_capability_endpoint_id": sdk_operation_api_view_capability_endpoint_id,
            "label": label,
            "receipt_policy": receipt_policy,
            "confirmation_policy": confirmation_policy,
            "optimistic_policy": optimistic_policy,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_invocation_action_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_view_invocation_action_config import (
            ProjectionExperienceViewInvocationActionConfig,
        )

        if isinstance(value, ProjectionExperienceViewInvocationActionConfig):
            return value
        return ProjectionExperienceViewInvocationActionConfig.validate_invocation_value(value)

    async def create_instance(
        self,
        section_graph_binding_id: UUID,
        view_instance_key: str,
        object_instance_graph_branch_id: UUID | None = None,
        state_commit_id: UUID | None = None,
        status: str = "active",
    ) -> ProjectionExperienceViewInstance:
        """
        Create one concrete rendered instance of this Experience view.

        Contract:
        - `ProjectionExperienceView` is reusable view configuration.
        - `ProjectionExperienceViewInstance` is the concrete view fulfillment for
          one section-graph binding, optionally backed by one materialized branch.
        - Attention FocusScope remains transitional selector state and is not view identity.
        - Action provenance must attach to this instance, not only to the view config.
        """

        payload = {
            "section_graph_binding_id": section_graph_binding_id,
            "view_instance_key": view_instance_key,
            "object_instance_graph_branch_id": object_instance_graph_branch_id,
            "state_commit_id": state_commit_id,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="create_instance", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.projection.projection_experience_view_instance import (
            ProjectionExperienceViewInstance,
        )

        if isinstance(value, ProjectionExperienceViewInstance):
            return value
        return ProjectionExperienceViewInstance.validate_invocation_value(value)

    @classmethod
    async def create_via_projection_experience(
        cls, projection_experience_id: UUID, api_view_id: UUID, name: str
    ) -> ProjectionExperienceView:
        """
        Construct a deterministic ProjectionExperienceView under a ProjectionExperience.

        Contract:
        - `ProjectionExperienceView.id` is deterministic for `(projection_experience_id, name)`.
        - Constructor converges the API-view binding for repeated calls with the same Experience mount key.
        - `api_view` is the canonical lower API-owned readable view-state contract.
        - Observable and state-model metadata are derived from `api_view`; Experience
          does not duplicate lower view contract truth.
        """

        payload = {"projection_experience_id": projection_experience_id, "api_view_id": api_view_id, "name": name}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceView):
            return value
        return ProjectionExperienceView.validate_invocation_value(value)


class ProjectionExperienceViewSetStateProviderInput(BaseModel):
    provider_ref: str
    provider_kind: str = Field(default="runtime_callable")
    purity: str = Field(default="pure_read")


class ProjectionExperienceViewSetStateProviderOutput(BaseModel):
    value: ProjectionExperienceViewStateProvider


class ProjectionExperienceViewAddInvocationActionInput(BaseModel):
    api_view_capability_endpoint_id: UUID
    experience_invocation_action_config_id: UUID
    action_key: str
    sdk_operation_api_view_capability_endpoint_id: UUID | None = Field(default=None)
    label: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)


class ProjectionExperienceViewAddInvocationActionOutput(BaseModel):
    value: ProjectionExperienceViewInvocationActionConfig


class ProjectionExperienceViewBindInvocationActionConfigInput(BaseModel):
    api_view_capability_endpoint_id: UUID
    experience_invocation_action_config_id: UUID
    action_key: str
    sdk_operation_api_view_capability_endpoint_id: UUID | None = Field(default=None)
    label: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)


class ProjectionExperienceViewBindInvocationActionConfigOutput(BaseModel):
    value: ProjectionExperienceViewInvocationActionConfig


class ProjectionExperienceViewCreateInstanceInput(BaseModel):
    section_graph_binding_id: UUID
    view_instance_key: str
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    state_commit_id: UUID | None = Field(default=None)
    status: str = Field(default="active")


class ProjectionExperienceViewCreateInstanceOutput(BaseModel):
    value: ProjectionExperienceViewInstance


class ProjectionExperienceViewCreateViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(
        description="Foreign key for ProjectionExperience.projection_experience_views"
    )
    api_view_id: UUID
    name: str


class ProjectionExperienceViewCreateViaProjectionExperienceOutput(BaseModel):
    value: ProjectionExperienceView


FUNCTIONS = {
    "ProjectionExperienceView": {
        "set_state_provider": {
            "canonical": {
                "name": "set_state_provider",
                "description": "Bind the pure read provider for this exact ProjectionExperienceView.\n\nContract:\n- The view remains the semantic selector and owns provider selection.\n- The provider must only read host-owned materialized state and produce the declared state model.\n- Runtime callables and SDK functions are adapter implementations, not semantic authority.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceViewSetStateProviderInput,
            "output": ProjectionExperienceViewSetStateProviderOutput,
        },
        "add_invocation_action": {
            "canonical": {
                "name": "add_invocation_action",
                "description": "Bind one Experience-owned invocation action to this view.\n\nContract:\n- `api_view_capability_endpoint` is the API-owned view action truth.\n- `sdk_operation_api_view_capability_endpoint`, when present, wraps the\n  same API view action with an SDK operation.\n- `experience_invocation_action_config` carries executable API endpoint XOR\n  SDK operation target metadata.\n- `action_key` is copied from API-owned view action truth for panes.\n- This is not a Reactivity `ActionConfig`; it is a user/client invocation capability.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceViewAddInvocationActionInput,
            "output": ProjectionExperienceViewAddInvocationActionOutput,
        },
        "bind_invocation_action_config": {
            "canonical": {
                "name": "bind_invocation_action_config",
                "description": "Bind one generic Experience invocation target config to an API-owned\nview action exposed by this view.\n\nContract:\n- `api_view_capability_endpoint` is mandatory view-action truth.\n- Target execution metadata stays on `ExperienceInvocationActionConfig`.\n- Optional SDK operation view binding wraps the same API view action.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceViewBindInvocationActionConfigInput,
            "output": ProjectionExperienceViewBindInvocationActionConfigOutput,
        },
        "create_instance": {
            "canonical": {
                "name": "create_instance",
                "description": "Create one concrete rendered instance of this Experience view.\n\nContract:\n- `ProjectionExperienceView` is reusable view configuration.\n- `ProjectionExperienceViewInstance` is the concrete view fulfillment for\n  one section-graph binding, optionally backed by one materialized branch.\n- Attention FocusScope remains transitional selector state and is not view identity.\n- Action provenance must attach to this instance, not only to the view config.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceViewCreateInstanceInput,
            "output": ProjectionExperienceViewCreateInstanceOutput,
        },
        "create_via_projection_experience": {
            "canonical": {
                "name": "create_via_projection_experience",
                "description": "Construct a deterministic ProjectionExperienceView under a ProjectionExperience.\n\nContract:\n- `ProjectionExperienceView.id` is deterministic for `(projection_experience_id, name)`.\n- Constructor converges the API-view binding for repeated calls with the same Experience mount key.\n- `api_view` is the canonical lower API-owned readable view-state contract.\n- Observable and state-model metadata are derived from `api_view`; Experience\n  does not duplicate lower view contract truth.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceViewCreateViaProjectionExperienceInput,
            "output": ProjectionExperienceViewCreateViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceView",
    "ProjectionExperienceViewSetStateProviderInput",
    "ProjectionExperienceViewSetStateProviderOutput",
    "ProjectionExperienceViewAddInvocationActionInput",
    "ProjectionExperienceViewAddInvocationActionOutput",
    "ProjectionExperienceViewBindInvocationActionConfigInput",
    "ProjectionExperienceViewBindInvocationActionConfigOutput",
    "ProjectionExperienceViewCreateInstanceInput",
    "ProjectionExperienceViewCreateInstanceOutput",
    "ProjectionExperienceViewCreateViaProjectionExperienceInput",
    "ProjectionExperienceViewCreateViaProjectionExperienceOutput",
    "FUNCTIONS",
]
