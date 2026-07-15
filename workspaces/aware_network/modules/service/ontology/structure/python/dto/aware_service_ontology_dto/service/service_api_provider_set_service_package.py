from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_service_ontology_dto.service.service_package import ServicePackage


class ServiceApiProviderSetServicePackage(BaseModel):
    # Relationships
    service_package: ServicePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    membership_key: str | None = Field(default=None)
