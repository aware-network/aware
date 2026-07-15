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
    from aware_experience_ontology.environment.environment_experience_profile import EnvironmentExperienceProfile


class ExperienceSessionProfile(ORMModel):
    """
    Session-local mount of one applied Experience profile.
    Contract:
    - EnvironmentExperienceProfile remains reusable applied profile truth.
    - This row records participation/provenance within one ExperienceSession.
    - It carries no global active-profile or active-projection semantics.
    """

    # Relationships
    profile: EnvironmentExperienceProfile | None = Field(default=None)

    # Attributes
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)

    # Foreign Keys
    experience_session_id: UUID = Field(description="Foreign key for ExperienceSession.profiles")
    profile_id: UUID = Field(description="Foreign key for ExperienceSessionProfile.profile")

    @classmethod
    async def build_via_experience_session(
        cls,
        experience_session_id: UUID,
        profile_id: UUID,
        status: str = "active",
        metadata_json: JsonObject | None = {},
    ) -> ExperienceSessionProfile:
        """
        Mount one applied Experience profile under ExperienceSession.

        Stable identity is ExperienceSession plus applied profile.
        """

        payload = {
            "experience_session_id": experience_session_id,
            "profile_id": profile_id,
            "status": status,
            "metadata_json": metadata_json,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_experience_session", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ExperienceSessionProfile):
            return value
        return ExperienceSessionProfile.validate_invocation_value(value)


class ExperienceSessionProfileBuildViaExperienceSessionInput(BaseModel):
    experience_session_id: UUID = Field(description="Foreign key for ExperienceSession.profiles")
    profile_id: UUID
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class ExperienceSessionProfileBuildViaExperienceSessionOutput(BaseModel):
    value: ExperienceSessionProfile


FUNCTIONS = {
    "ExperienceSessionProfile": {
        "build_via_experience_session": {
            "canonical": {
                "name": "build_via_experience_session",
                "description": "Mount one applied Experience profile under ExperienceSession.\n\nStable identity is ExperienceSession plus applied profile.",
                "is_constructor": True,
            },
            "input": ExperienceSessionProfileBuildViaExperienceSessionInput,
            "output": ExperienceSessionProfileBuildViaExperienceSessionOutput,
        },
    },
}

__all__ = [
    "ExperienceSessionProfile",
    "ExperienceSessionProfileBuildViaExperienceSessionInput",
    "ExperienceSessionProfileBuildViaExperienceSessionOutput",
    "FUNCTIONS",
]
