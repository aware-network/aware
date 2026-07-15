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
    from aware_service_ontology_dto.service.service_config_api import ServiceConfigApi
    from aware_service_ontology_dto.service.service_operation_config_api_endpoint_function import (
        ServiceOperationConfigApiEndpointFunction,
    )


class ServiceOperationConfigApiEndpoint(BaseModel):
    # Relationships
    api_capability_endpoint: ApiCapabilityEndpoint | None = Field(default=None)
    endpoint_functions: list[ServiceOperationConfigApiEndpointFunction] = Field(default_factory=list)
    service_config_api: ServiceConfigApi | None = Field(default=None)

    # Attributes
    description: str | None = Field(default=None)
