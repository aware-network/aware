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
    from aware_experience_ontology.projection.projection_experience import ProjectionExperience


class EnvironmentExperienceProjection(ORMModel):
    # Relationships
    projection_experience: ProjectionExperience | None = Field(default=None, exclude=True)

    # Foreign Keys
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.experiences"
    )
    projection_experience_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProjection.projection_experience"
    )

    @classmethod
    async def build_via_environment_experience_profile_config(
        cls, environment_experience_profile_config_id: UUID, projection_experience_id: UUID
    ) -> EnvironmentExperienceProjection:
        """
        Create a deterministic EnvironmentExperienceProjection association edge.

        Notes:
        - Identity is derived from `(environment_experience_profile_config_id, projection_experience_id)`.
        """

        payload = {
            "environment_experience_profile_config_id": environment_experience_profile_config_id,
            "projection_experience_id": projection_experience_id,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_environment_experience_profile_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, EnvironmentExperienceProjection):
            return value
        return EnvironmentExperienceProjection.validate_invocation_value(value)


class EnvironmentExperienceProjectionBuildViaEnvironmentExperienceProfileConfigInput(BaseModel):
    environment_experience_profile_config_id: UUID = Field(
        description="Foreign key for EnvironmentExperienceProfileConfig.experiences"
    )
    projection_experience_id: UUID


class EnvironmentExperienceProjectionBuildViaEnvironmentExperienceProfileConfigOutput(BaseModel):
    value: EnvironmentExperienceProjection


FUNCTIONS = {
    "EnvironmentExperienceProjection": {
        "build_via_environment_experience_profile_config": {
            "canonical": {
                "name": "build_via_environment_experience_profile_config",
                "description": "Create a deterministic EnvironmentExperienceProjection association edge.\n\nNotes:\n- Identity is derived from `(environment_experience_profile_config_id, projection_experience_id)`.",
                "is_constructor": True,
            },
            "input": EnvironmentExperienceProjectionBuildViaEnvironmentExperienceProfileConfigInput,
            "output": EnvironmentExperienceProjectionBuildViaEnvironmentExperienceProfileConfigOutput,
        },
    },
}

__all__ = [
    "EnvironmentExperienceProjection",
    "EnvironmentExperienceProjectionBuildViaEnvironmentExperienceProfileConfigInput",
    "EnvironmentExperienceProjectionBuildViaEnvironmentExperienceProfileConfigOutput",
    "FUNCTIONS",
]
