from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction


class ServiceOperationConfigApiEndpointFunction(ORMModel):
    # Relationships
    api_capability_endpoint_function: ApiCapabilityEndpointFunction | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_operation_config_api_endpoint_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpoint.endpoint_functions"
    )
    api_capability_endpoint_function_id: UUID = Field(
        description="Foreign key for ServiceOperationConfigApiEndpointFunction.api_capability_endpoint_function"
    )
