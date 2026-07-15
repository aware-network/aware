from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api import Api
    from aware_skill_ontology_dto.skill.skill_config_api_endpoint import SkillConfigApiEndpoint


class SkillConfigApi(BaseModel):
    # Relationships
    api: Api | None = Field(default=None)
    api_endpoints: list[SkillConfigApiEndpoint] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
