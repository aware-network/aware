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
    from aware_service_ontology_orm_models.service.service_config_api import ServiceConfigApi
    from aware_service_ontology_orm_models.service.service_operation_config_api_endpoint_function import (
        ServiceOperationConfigApiEndpointFunction,
    )


class ServiceOperationConfigApiEndpoint(ORMModel):
    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None, exclude=True)
    endpoint_functions: list[ServiceOperationConfigApiEndpointFunction] = Field(default_factory=list, exclude=True)
    service_config_api: ServiceConfigApi | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.api_endpoints")
    api_capability_endpoint_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpoint.api_capability_endpoint"
    )
    service_config_api_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpoint.service_config_api"
    )
