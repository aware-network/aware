from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint import ApiCapabilityEndpoint


class SkillConfigApiEndpoint(ORMModel):
    # Relationships
    api_endpoint: ApiCapabilityEndpoint | None = Field(default=None)

    # Attributes
    capability_name: str
    description: str | None = Field(default=None)
    name: str

    # Foreign Keys
    skill_config_api_id: UUID = Field(description="Foreign key for SkillConfigApi.api_endpoints")
    api_endpoint_id: UUID = Field(description="Foreign key for SkillConfigApiEndpoint.api_endpoint")
