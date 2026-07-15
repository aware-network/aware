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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_identity_ontology.actor.actor_config import ActorConfig


class EnvironmentProfileActorConfig(ORMModel):
    """
    EnvironmentProfileConfig actor eligibility policy.
    Contract:
    - Environment owns admission eligibility for shared OS entrance.
    - Identity owns ActorConfig, RoleConfig, Role, ActorRole, and concrete
    role assignment truth.
    - This edge never embeds actors and never grants access by itself.
    - Environment service admission resolves ActorConfig -> RoleConfig[] and
    delegates concrete role assignment to Identity.
    """

    # Relationships
    actor_config: ActorConfig | None = Field(default=None)

    # Attributes
    access_scope: str = Field(default="profile")
    description: str | None = Field(default=None)
    metadata_json: JsonObject = Field(default_factory=JsonObject)
    policy_key: str = Field(default="admit")
    requirement_kind: str = Field(default="environment_actor_config")
    status: str = Field(default="active")

    # Foreign Keys
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.actor_configs")
    actor_config_id: UUID = Field(description="Foreign key for EnvironmentProfileActorConfig.actor_config")

    @classmethod
    async def create_via_environment_profile_config(
        cls,
        environment_profile_config_id: UUID,
        actor_config_id: UUID,
        policy_key: str = "admit",
        requirement_kind: str = "environment_actor_config",
        access_scope: str = "profile",
        status: str = "active",
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentProfileActorConfig:
        """
        Create one EnvironmentProfileConfig ActorConfig eligibility edge.

        Contract:
        - Stable identity is `(environment_profile_config_id, actor_config_id, policy_key)`.
        - The edge is policy eligibility only; concrete admission is Identity-owned.
        - `access_scope` is explicit so v0 profile admission does not imply hidden
          ProcessConfig or ThreadConfig rights.
        """

        payload = {
            "environment_profile_config_id": environment_profile_config_id,
            "actor_config_id": actor_config_id,
            "policy_key": policy_key,
            "requirement_kind": requirement_kind,
            "access_scope": access_scope,
            "status": status,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_environment_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentProfileActorConfig):
            return value
        return EnvironmentProfileActorConfig.validate_invocation_value(value)


class EnvironmentProfileActorConfigCreateViaEnvironmentProfileConfigInput(BaseModel):
    environment_profile_config_id: UUID = Field(description="Foreign key for EnvironmentProfileConfig.actor_configs")
    actor_config_id: UUID
    policy_key: str = Field(default="admit")
    requirement_kind: str = Field(default="environment_actor_config")
    access_scope: str = Field(default="profile")
    status: str = Field(default="active")
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentProfileActorConfigCreateViaEnvironmentProfileConfigOutput(BaseModel):
    value: EnvironmentProfileActorConfig


FUNCTIONS = {
    "EnvironmentProfileActorConfig": {
        "create_via_environment_profile_config": {
            "canonical": {
                "name": "create_via_environment_profile_config",
                "description": "Create one EnvironmentProfileConfig ActorConfig eligibility edge.\n\nContract:\n- Stable identity is `(environment_profile_config_id, actor_config_id, policy_key)`.\n- The edge is policy eligibility only; concrete admission is Identity-owned.\n- `access_scope` is explicit so v0 profile admission does not imply hidden\n  ProcessConfig or ThreadConfig rights.",
                "is_constructor": True,
            },
            "input": EnvironmentProfileActorConfigCreateViaEnvironmentProfileConfigInput,
            "output": EnvironmentProfileActorConfigCreateViaEnvironmentProfileConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentProfileActorConfig",
    "EnvironmentProfileActorConfigCreateViaEnvironmentProfileConfigInput",
    "EnvironmentProfileActorConfigCreateViaEnvironmentProfileConfigOutput",
    "FUNCTIONS",
]
