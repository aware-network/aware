from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_view import ApiView
    from aware_service_ontology_orm_models.service.service_config_api import ServiceConfigApi


class ServiceOperationConfigApiView(ORMModel):
    # Relationships
    api_view: ApiView | None = Field(default=None, exclude=True)
    service_config_api: ServiceConfigApi | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.api_views")
    api_view_id: UUID = Field(description="Foreign key for ServiceOperationConfigApiView.api_view")
    service_config_api_id: UUID = Field(description="Foreign key for ServiceOperationConfigApiView.service_config_api")
