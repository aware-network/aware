from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_capability_endpoint import ApiCapabilityEndpoint


class SkillConfigApiEndpoint(BaseModel):
    # Relationships
    api_endpoint: ApiCapabilityEndpoint | None = Field(default=None)

    # Attributes
    capability_name: str
    description: str | None = Field(default=None)
    name: str
