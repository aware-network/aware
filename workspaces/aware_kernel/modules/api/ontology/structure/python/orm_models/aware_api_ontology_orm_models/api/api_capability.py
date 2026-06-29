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


class ApiCapability(ORMModel):
    # Relationships
    api_capability_endpoints: list[ApiCapabilityEndpoint] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_id: UUID = Field(description="Foreign key for Api.api_capabilities")
