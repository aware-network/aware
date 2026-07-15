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
    from aware_identity_ontology.actor.actor_config import ActorConfig


class EnvironmentExperienceActorConfig(ORMModel):
    # Relationships
    actor_config: ActorConfig | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.actors"
    )
    actor_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceActorConfig.actor_config")

    @classmethod
    async def build_via_environment_experience_profile_config(
        cls, environment_experience_profile_config_id: UUID, actor_config_id: UUID
    ) -> EnvironmentExperienceActorConfig:
        """Create a deterministic EnvironmentExperienceActorConfig association edge."""

        payload = {
            "environment_experience_profile_config_id": environment_experience_profile_config_id,
            "actor_config_id": actor_config_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceActorConfig):
            return value
        return EnvironmentExperienceActorConfig.validate_invocation_value(value)


class EnvironmentExperienceActorConfigBuildViaEnvironmentExperienceProfileConfigInput(BaseModel):
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.actors"
    )
    actor_config_id: UUID


class EnvironmentExperienceActorConfigBuildViaEnvironmentExperienceProfileConfigOutput(BaseModel):
    value: EnvironmentExperienceActorConfig


FUNCTIONS = {
    "EnvironmentExperienceActorConfig": {
        "build_via_environment_experience_profile_config": {
            "canonical": {
                "name": "build_via_environment_experience_profile_config",
                "description": "Create a deterministic EnvironmentExperienceActorConfig association edge.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceActorConfigBuildViaEnvironmentExperienceProfileConfigInput,
            "output": EnvironmentExperienceActorConfigBuildViaEnvironmentExperienceProfileConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceActorConfig",
    "EnvironmentExperienceActorConfigBuildViaEnvironmentExperienceProfileConfigInput",
    "EnvironmentExperienceActorConfigBuildViaEnvironmentExperienceProfileConfigOutput",
    "FUNCTIONS",
]
