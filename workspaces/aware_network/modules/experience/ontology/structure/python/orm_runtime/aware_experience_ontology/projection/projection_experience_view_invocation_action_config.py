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
    from aware_api_ontology.api.api_view_capability_endpoint import ApiViewCapabilityEndpoint
    from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction
    from aware_experience_ontology.invocation.experience_invocation_action_config import (
        ExperienceInvocationActionConfig,
    )
    from aware_sdk_ontology.sdk.sdk_operation_api_view_capability_endpoint import SdkOperationApiViewCapabilityEndpoint


class ProjectionExperienceViewInvocationActionConfig(ORMModel):
    """
    View-owned binding to one generic Experience invocation action config.
    Contract:
    - Panes render and dispatch these actions by `action_key`; they do not own
    the SDK/API capability target.
    - API-owned `ApiViewCapabilityEndpoint` is mandatory view-action truth.
    - SDK-owned `SdkOperationApiViewCapabilityEndpoint` is optional client-facing
    operation truth for the same API view capability endpoint.
    - Generic executable target relationships live on `ExperienceInvocationActionConfig`.
    - Reactivity actions remain separate under `ActionConfig` / `ActionExperience`.
    """

    # Relationships
    api_view_capability_endpoint: ApiViewCapabilityEndpoint | None = Field(default=None)
    sdk_operation_api_view_capability_endpoint: SdkOperationApiViewCapabilityEndpoint | None = Field(default=None)
    experience_invocation_action_config: ExperienceInvocationActionConfig | None = Field(default=None)

    # Attributes
    action_key: str
    label: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)

    # Foreign Keys
    projection_experience_view_id: UUID = Field(
        description="Foreign key for ProjectionExperienceView.invocation_action_configs"
    )
    api_view_capability_endpoint_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInvocationActionConfig.api_view_capability_endpoint"
    )
    sdk_operation_api_view_capability_endpoint_id: UUID | None = Field(
        default=None,
        description="Foreign key for ProjectionExperienceViewInvocationActionConfig.sdk_operation_api_view_capability_endpoint",
    )
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ProjectionExperienceViewInvocationActionConfig.experience_invocation_action_config"
    )

    async def record_invocation(
        self,
        invocation_key: UUID,
        actor_id: UUID | None = None,
        api_call_id: UUID | None = None,
        sdk_operation_call_id: UUID | None = None,
        request_ref: str | None = None,
        receipt_ref: str | None = None,
        status: str = "pending",
    ) -> ExperienceInvocationAction:
        """
        Record one actual invocation handled through this view action config.

        Contract:
        - `ExperienceInvocationAction` is the single standalone invocation
          receipt for one crossing.
        - `ExperienceInvocationActionConfig` remains target metadata only.
        - Concrete view provenance attaches through
          `ProjectionExperienceViewInvocationAction`.
        - This view config does not own receipt identity.
        """

        payload = {
            "invocation_key": invocation_key,
            "actor_id": actor_id,
            "api_call_id": api_call_id,
            "sdk_operation_call_id": sdk_operation_call_id,
            "request_ref": request_ref,
            "receipt_ref": receipt_ref,
            "status": status,
        }
        result = await invoke_instance(orm_model=self, function_name="record_invocation", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.experience_invocation_action import ExperienceInvocationAction

        if isinstance(value, ExperienceInvocationAction):
            return value
        return ExperienceInvocationAction.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience_view(
        cls,
        projection_experience_view_id: UUID,
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
        Bind one API-owned view action under a ProjectionExperienceView.

        Contract:
        - Parent `ProjectionExperienceView` scope is propagated by constructor lowering.
        - Identity is scoped by parent `ProjectionExperienceView` and
          `ApiViewCapabilityEndpoint`.
        - `experience_invocation_action_config` holds executable API endpoint XOR
          SDK operation target metadata.
        - `sdk_operation_api_view_capability_endpoint` may wrap the API view action
          with an SDK operation but must resolve to the same API view capability
          endpoint.
        - `action_key` is copied from API-owned view action truth for panes.
        """

        payload = {
            "projection_experience_view_id": projection_experience_view_id,
            "api_view_capability_endpoint_id": api_view_capability_endpoint_id,
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "action_key": action_key,
            "sdk_operation_api_view_capability_endpoint_id": sdk_operation_api_view_capability_endpoint_id,
            "label": label,
            "receipt_policy": receipt_policy,
            "confirmation_policy": confirmation_policy,
            "optimistic_policy": optimistic_policy,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience_view", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProjectionExperienceViewInvocationActionConfig):
            return value
        return ProjectionExperienceViewInvocationActionConfig.validate_invocation_value(value)


class ProjectionExperienceViewInvocationActionConfigRecordInvocationInput(BaseModel):
    invocation_key: UUID
    actor_id: UUID | None = Field(default=None)
    api_call_id: UUID | None = Field(default=None)
    sdk_operation_call_id: UUID | None = Field(default=None)
    request_ref: str | None = Field(default=None)
    receipt_ref: str | None = Field(default=None)
    status: str = Field(default="pending")


class ProjectionExperienceViewInvocationActionConfigRecordInvocationOutput(BaseModel):
    value: ExperienceInvocationAction


class ProjectionExperienceViewInvocationActionConfigBuildViaProjectionExperienceViewInput(BaseModel):
    projection_experience_view_id: UUID = Field(
        description="Foreign key for ProjectionExperienceView.invocation_action_configs"
    )
    api_view_capability_endpoint_id: UUID
    experience_invocation_action_config_id: UUID
    action_key: str
    sdk_operation_api_view_capability_endpoint_id: UUID | None = Field(default=None)
    label: str | None = Field(default=None)
    receipt_policy: str | None = Field(default=None)
    confirmation_policy: str | None = Field(default=None)
    optimistic_policy: str | None = Field(default=None)


class ProjectionExperienceViewInvocationActionConfigBuildViaProjectionExperienceViewOutput(BaseModel):
    value: ProjectionExperienceViewInvocationActionConfig


FUNCTIONS = {
    "ProjectionExperienceViewInvocationActionConfig": {
        "record_invocation": {
            "canonical": {
                "name": "record_invocation",
                "description": "Record one actual invocation handled through this view action config.\n\nContract:\n- `ExperienceInvocationAction` is the single standalone invocation\n  receipt for one crossing.\n- `ExperienceInvocationActionConfig` remains target metadata only.\n- Concrete view provenance attaches through\n  `ProjectionExperienceViewInvocationAction`.\n- This view config does not own receipt identity.",
                "is_constructor": False,
            },
            "input": ProjectionExperienceViewInvocationActionConfigRecordInvocationInput,
            "output": ProjectionExperienceViewInvocationActionConfigRecordInvocationOutput,
        },
        "build_via_projection_experience_view": {
            "canonical": {
                "name": "build_via_projection_experience_view",
                "description": "Bind one API-owned view action under a ProjectionExperienceView.\n\nContract:\n- Parent `ProjectionExperienceView` scope is propagated by constructor lowering.\n- Identity is scoped by parent `ProjectionExperienceView` and\n  `ApiViewCapabilityEndpoint`.\n- `experience_invocation_action_config` holds executable API endpoint XOR\n  SDK operation target metadata.\n- `sdk_operation_api_view_capability_endpoint` may wrap the API view action\n  with an SDK operation but must resolve to the same API view capability\n  endpoint.\n- `action_key` is copied from API-owned view action truth for panes.",
                "is_constructor": True,
            },
            "input": ProjectionExperienceViewInvocationActionConfigBuildViaProjectionExperienceViewInput,
            "output": ProjectionExperienceViewInvocationActionConfigBuildViaProjectionExperienceViewOutput,
        },
    },
}

__all__ = [
    "ProjectionExperienceViewInvocationActionConfig",
    "ProjectionExperienceViewInvocationActionConfigRecordInvocationInput",
    "ProjectionExperienceViewInvocationActionConfigRecordInvocationOutput",
    "ProjectionExperienceViewInvocationActionConfigBuildViaProjectionExperienceViewInput",
    "ProjectionExperienceViewInvocationActionConfigBuildViaProjectionExperienceViewOutput",
    "FUNCTIONS",
]
