from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api import Api
    from aware_skill_ontology_orm_models.skill.skill_config_api_endpoint import SkillConfigApiEndpoint


class SkillConfigApi(ORMModel):
    # Relationships
    api: Api | None = Field(default=None)
    api_endpoints: list[SkillConfigApiEndpoint] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    skill_config_id: UUID = Field(description="Foreign key for SkillConfig.apis")
    api_id: UUID = Field(description="Foreign key for SkillConfigApi.api")
