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
    from aware_identity_ontology.role.role_config import RoleConfig


class RoleConfigInvocationActionConfig(ORMModel):
    """
    Experience action-entrypoint policy for admitted Identity roles.
    Contract:
    - Experience owns this policy because public consumers invoke Experience
    action configs, not ontology functions directly.
    - Identity owns `RoleConfig` and concrete `ActorRole` materialization.
    - Service/Ontology mutation policy remains the lower graph mutation gate.
    """

    # Relationships
    role_config: RoleConfig | None = Field(default=None)

    # Attributes
    policy_key: str = Field(default="invoke")
    requirement_kind: str = Field(default="admitted_actor_role")
    description: str | None = Field(default=None)

    # Foreign Keys
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionConfig.role_policies"
    )
    role_config_id: UUID = Field(description="Foreign key for RoleConfigInvocationActionConfig.role_config")

    @classmethod
    async def build_via_experience_invocation_action_config(
        cls,
        experience_invocation_action_config_id: UUID,
        role_config_id: UUID,
        policy_key: str = "invoke",
        requirement_kind: str = "admitted_actor_role",
        description: str | None = None,
    ) -> RoleConfigInvocationActionConfig:
        """Bind one RoleConfig to the parent ExperienceInvocationActionConfig."""

        payload = {
            "experience_invocation_action_config_id": experience_invocation_action_config_id,
            "role_config_id": role_config_id,
            "policy_key": policy_key,
            "requirement_kind": requirement_kind,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_experience_invocation_action_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, RoleConfigInvocationActionConfig):
            return value
        return RoleConfigInvocationActionConfig.validate_invocation_value(value)


class RoleConfigInvocationActionConfigBuildViaExperienceInvocationActionConfigInput(BaseModel):
    experience_invocation_action_config_id: UUID = Field(
        description="Foreign key for ExperienceInvocationActionConfig.role_policies"
    )
    role_config_id: UUID
    policy_key: str = Field(default="invoke")
    requirement_kind: str = Field(default="admitted_actor_role")
    description: str | None = Field(default=None)


class RoleConfigInvocationActionConfigBuildViaExperienceInvocationActionConfigOutput(BaseModel):
    value: RoleConfigInvocationActionConfig


FUNCTIONS = {
    "RoleConfigInvocationActionConfig": {
        "build_via_experience_invocation_action_config": {
            "canonical": {
                "name": "build_via_experience_invocation_action_config",
                "description": "Bind one RoleConfig to the parent ExperienceInvocationActionConfig.",
                "is_constructor": True,
            },
            "input": RoleConfigInvocationActionConfigBuildViaExperienceInvocationActionConfigInput,
            "output": RoleConfigInvocationActionConfigBuildViaExperienceInvocationActionConfigOutput,
        },
    },
}

__all__ = [
    "RoleConfigInvocationActionConfig",
    "RoleConfigInvocationActionConfigBuildViaExperienceInvocationActionConfigInput",
    "RoleConfigInvocationActionConfigBuildViaExperienceInvocationActionConfigOutput",
    "FUNCTIONS",
]
