from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
    from aware_experience_ontology.invocation.role_config_invocation_action_config import (
        RoleConfigInvocationActionConfig,
    )
    from aware_sdk_ontology.sdk.sdk_operation import SdkOperation


class ExperienceInvocationActionConfig(ORMModel):
    """
    Experience-owned reusable invocation action configuration.
    Contract:
    - This is the canonical executable target configuration for an invocation
    action.
    - Projection views, sensors, actuators, and future surfaces consume this
    config instead of duplicating executable API/SDK target fields.
    - View-action identity lives on `ProjectionExperienceViewInvocationActionConfig`
    through API-owned `ApiViewCapabilityEndpoint` and optional SDK-owned
    `SdkOperationApiViewCapabilityEndpoint`; it does not live here.
    - Actual invocation receipts are children of the surface config that
    handled the action, for example `ProjectionExperienceViewInvocationActionConfig`.
    """

    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)
    sdk_operation: SdkOperation | None = Field(default=None)
    role_policies: list[RoleConfigInvocationActionConfig] = Field(default_factory=list)

    # Attributes
    target_kind: ExperienceInvocationActionTargetKind

    # Foreign Keys
    projection_experience_id: UUID = Field(description="Foreign key for ProjectionExperience.invocation_action_configs")
    api_capability_endpoint_id: UUID | None = Field(
        default=None, description="Foreign key for ExperienceInvocationActionConfig.api_capability_endpoint"
    )
    sdk_operation_id: UUID | None = Field(
        default=None, description="Foreign key for ExperienceInvocationActionConfig.sdk_operation"
    )

    async def allow_role_config(
        self,
        role_config_id: UUID,
        policy_key: str = "invoke",
        requirement_kind: str = "admitted_actor_role",
        description: str | None = None,
    ) -> RoleConfigInvocationActionConfig:
        """
        Authorize one Identity RoleConfig to invoke this Experience action config.

        Contract:
        - Experience owns the action-entrypoint policy.
        - Identity owns the concrete RoleConfig and ActorRole truth.
        - Dispatch preflight must prove admitted actor-role evidence against this edge.
        """

        payload = {
            "role_config_id": role_config_id,
            "policy_key": policy_key,
            "requirement_kind": requirement_kind,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="allow_role_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.invocation.role_config_invocation_action_config import (
            RoleConfigInvocationActionConfig,
        )

        if isinstance(value, RoleConfigInvocationActionConfig):
            return value
        return RoleConfigInvocationActionConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_projection_experience(
        cls,
        projection_experience_id: UUID,
        target_kind: ExperienceInvocationActionTargetKind,
        api_capability_endpoint_id: UUID | None = None,
        sdk_operation_id: UUID | None = None,
    ) -> ExperienceInvocationActionConfig:
        """
        Create one deterministic invocation action config under a ProjectionExperience.

        Contract:
        - Parent `ProjectionExperience` scope is propagated by constructor lowering.
        - `target_kind` discriminates the executable target family.
        - `api` targets must set only `api_capability_endpoint`.
        - `sdk` targets must set only `sdk_operation`.
        - String target refs and renderer action keys are intentionally absent;
          surface wrappers own those higher-level bindings.
        """

        payload = {
            "projection_experience_id": projection_experience_id,
            "target_kind": target_kind,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "sdk_operation_id": sdk_operation_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_projection_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceInvocationActionConfig):
            return value
        return ExperienceInvocationActionConfig.validate_invocation_value(value)


class ExperienceInvocationActionConfigAllowRoleConfigInput(BaseModel):
    role_config_id: UUID
    policy_key: str = Field(default="invoke")
    requirement_kind: str = Field(default="admitted_actor_role")
    description: str | None = Field(default=None)


class ExperienceInvocationActionConfigAllowRoleConfigOutput(BaseModel):
    value: RoleConfigInvocationActionConfig


class ExperienceInvocationActionConfigBuildViaProjectionExperienceInput(BaseModel):
    projection_experience_id: UUID = Field(description="Foreign key for ProjectionExperience.invocation_action_configs")
    target_kind: ExperienceInvocationActionTargetKind
    api_capability_endpoint_id: UUID | None = Field(default=None)
    sdk_operation_id: UUID | None = Field(default=None)


class ExperienceInvocationActionConfigBuildViaProjectionExperienceOutput(BaseModel):
    value: ExperienceInvocationActionConfig


FUNCTIONS = {
    "ExperienceInvocationActionConfig": {
        "allow_role_config": {
            "canonical": {
                "name": "allow_role_config",
                "description": "Authorize one Identity RoleConfig to invoke this Experience action config.\n\nContract:\n- Experience owns the action-entrypoint policy.\n- Identity owns the concrete RoleConfig and ActorRole truth.\n- Dispatch preflight must prove admitted actor-role evidence against this edge.",
                "is_constructor": False,
            },
            "input": ExperienceInvocationActionConfigAllowRoleConfigInput,
            "output": ExperienceInvocationActionConfigAllowRoleConfigOutput,
        },
        "build_via_projection_experience": {
            "canonical": {
                "name": "build_via_projection_experience",
                "description": "Create one deterministic invocation action config under a ProjectionExperience.\n\nContract:\n- Parent `ProjectionExperience` scope is propagated by constructor lowering.\n- `target_kind` discriminates the executable target family.\n- `api` targets must set only `api_capability_endpoint`.\n- `sdk` targets must set only `sdk_operation`.\n- String target refs and renderer action keys are intentionally absent;\n  surface wrappers own those higher-level bindings.",
                "is_constructor": True,
            },
            "input": ExperienceInvocationActionConfigBuildViaProjectionExperienceInput,
            "output": ExperienceInvocationActionConfigBuildViaProjectionExperienceOutput,
        },
    },
}

__all__ = [
    "ExperienceInvocationActionConfig",
    "ExperienceInvocationActionConfigAllowRoleConfigInput",
    "ExperienceInvocationActionConfigAllowRoleConfigOutput",
    "ExperienceInvocationActionConfigBuildViaProjectionExperienceInput",
    "ExperienceInvocationActionConfigBuildViaProjectionExperienceOutput",
    "FUNCTIONS",
]
