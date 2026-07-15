from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_service_ontology_orm_models.service.service_api_provider_set_service_package import (
        ServiceApiProviderSetServicePackage,
    )


class ServiceApiProviderSet(ORMModel):
    # Relationships
    service_packages: list[ServiceApiProviderSetServicePackage] = Field(default_factory=list)

    # Attributes
    description: str | None = Field(default=None)
    key: str
    title: str | None = Field(default=None)
    version_number: int = Field(default=1)
