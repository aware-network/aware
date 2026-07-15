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
    from aware_environment_ontology.environment.environment_profile import EnvironmentProfile
    from aware_experience_ontology.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )


class EnvironmentExperienceProfile(ORMModel):
    """
    Applied Experience profile over one concrete Environment EnvironmentProfile.
    Purpose:
    - Bridge reusable Experience profile config to an applied EnvironmentProfile.
    - Keep reusable actor/projection/event/process/thread policy on
    EnvironmentExperienceProfileConfig.
    - Provide the applied profile id that later Environment/Experience sessions
    and mounts can target.
    Contract:
    - This object references applied Environment EnvironmentProfile and
    reusable EnvironmentExperienceProfileConfig truth.
    - It does not own reusable Experience policy.
    - Session/mount ownership is intentionally added in the next rail after this
    config/applied split is proven end to end.
    """

    # Relationships
    profile_config: EnvironmentExperienceProfileConfig | None = Field(default=None)
    environment_profile: EnvironmentProfile | None = Field(default=None)

    # Attributes
    title: str | None = Field(default=None)
    status: str = Field(default="active")
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.profiles")
    profile_config_id: UUID = Field(description="Foreign key for EnvironmentExperienceProfile.profile_config")
    environment_profile_id: UUID = Field(description="Foreign key for EnvironmentExperienceProfile.environment_profile")

    @classmethod
    async def build_via_environment_experience(
        cls,
        environment_experience_id: UUID,
        profile_config_id: UUID,
        environment_profile_id: UUID,
        status: str = "active",
        title: str | None = None,
        description: str | None = None,
        metadata_json: JsonObject | None = {},
    ) -> EnvironmentExperienceProfile:
        """
        Construct one applied EnvironmentExperienceProfile under EnvironmentExperience.

        Contract:
        - Identity is derived from parent EnvironmentExperience path plus
          `(profile_config_id, environment_profile_id)`.
        - `profile_config_id` owns reusable Experience policy.
        - `environment_profile_id` owns concrete Environment session topology.
        """

        payload = {
            "environment_experience_id": environment_experience_id,
            "profile_config_id": profile_config_id,
            "environment_profile_id": environment_profile_id,
            "status": status,
            "title": title,
            "description": description,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceProfile):
            return value
        return EnvironmentExperienceProfile.validate_invocation_value(value)


class EnvironmentExperienceProfileBuildViaEnvironmentExperienceInput(BaseModel):
    environment_experience_id: UUID = Field(description="Foreign key for EnvironmentExperience.profiles")
    profile_config_id: UUID
    environment_profile_id: UUID
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class EnvironmentExperienceProfileBuildViaEnvironmentExperienceOutput(BaseModel):
    value: EnvironmentExperienceProfile


FUNCTIONS = {
    "EnvironmentExperienceProfile": {
        "build_via_environment_experience": {
            "canonical": {
                "name": "build_via_environment_experience",
                "description": "Construct one applied EnvironmentExperienceProfile under EnvironmentExperience.\n\nContract:\n- Identity is derived from parent EnvironmentExperience path plus\n  `(profile_config_id, environment_profile_id)`.\n- `profile_config_id` owns reusable Experience policy.\n- `environment_profile_id` owns concrete Environment session topology.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceProfileBuildViaEnvironmentExperienceInput,
            "output": EnvironmentExperienceProfileBuildViaEnvironmentExperienceOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceProfile",
    "EnvironmentExperienceProfileBuildViaEnvironmentExperienceInput",
    "EnvironmentExperienceProfileBuildViaEnvironmentExperienceOutput",
    "FUNCTIONS",
]
