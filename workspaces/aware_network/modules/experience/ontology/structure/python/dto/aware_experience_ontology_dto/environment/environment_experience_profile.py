from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_profile import EnvironmentProfile
    from aware_experience_ontology_dto.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )


class EnvironmentExperienceProfile(BaseModel):
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
