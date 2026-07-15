from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_service_ontology_dto.service.service_api_provider_set_service_package import (
        ServiceApiProviderSetServicePackage,
    )


class ServiceApiProviderSet(BaseModel):
    # Relationships
    service_packages: list[ServiceApiProviderSetServicePackage] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    key: str
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)
