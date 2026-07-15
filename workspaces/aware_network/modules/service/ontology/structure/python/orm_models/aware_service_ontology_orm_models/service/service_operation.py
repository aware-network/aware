from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Service Ontology Orm Models
from aware_service_ontology_orm_models.service.service_enums import ServiceOperationStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_api_ontology_orm_models.api.api_call import ApiCall
    from aware_service_ontology_orm_models.service.service_operation_config import ServiceOperationConfig
    from aware_service_ontology_orm_models.service.service_operation_config_api_endpoint import (
        ServiceOperationConfigApiEndpoint,
    )


class ServiceOperation(ORMModel):
    # Relationships
    api_call: ApiCall | None = Field(default=None, exclude=True)
    api_endpoint: ServiceOperationConfigApiEndpoint | None = Field(default=None, exclude=True)
    service_operation_config: ServiceOperationConfig | None = Field(default=None, exclude=True)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    operation_key: str
    result_info: str | None = Field(default=None)
    status: ServiceOperationStatus = Field(default=ServiceOperationStatus.queued)

    # Foreign Keys
    service_id: UUID = Field(description="Foreign key for Service.service_operations")
    api_call_id: UUID | None = Field(default=None, description="Foreign key for ServiceOperation.api_call")
    api_endpoint_id: UUID | None = Field(default=None, description="Foreign key for ServiceOperation.api_endpoint")
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperation.service_operation_config")
