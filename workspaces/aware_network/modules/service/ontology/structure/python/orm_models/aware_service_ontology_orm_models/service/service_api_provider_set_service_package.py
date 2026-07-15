from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_service_ontology_orm_models.service.service_package import ServicePackage


class ServiceApiProviderSetServicePackage(ORMModel):
    # Relationships
    service_package: ServicePackage | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
    membership_key: str | None = Field(default=None)

    # Foreign Keys
    service_api_provider_set_id: UUID = Field(description="Foreign key for ServiceApiProviderSet.service_packages")
    service_package_id: UUID = Field(description="Foreign key for ServiceApiProviderSetServicePackage.service_package")
