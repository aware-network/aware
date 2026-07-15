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
    from aware_service_ontology_orm_models.service.service_config_api_projection import ServiceConfigApiProjection


class ServiceConfigApi(ORMModel):
    # Relationships
    api: Api | None = Field(default=None, exclude=True)
    api_projections: list[ServiceConfigApiProjection] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.apis")
    api_id: UUID = Field(description="Foreign key for ServiceConfigApi.api")
