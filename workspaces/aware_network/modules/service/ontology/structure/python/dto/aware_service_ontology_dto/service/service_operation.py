from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Service Ontology Dto
from aware_service_ontology_dto.service.service_enums import ServiceOperationStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_api_ontology_dto.api.api_call import ApiCall
    from aware_service_ontology_dto.service.service_operation_config import ServiceOperationConfig
    from aware_service_ontology_dto.service.service_operation_config_api_endpoint import (
        ServiceOperationConfigApiEndpoint,
    )


class ServiceOperation(BaseModel):
    # Relationships
    api_call: ApiCall | None = Field(default=None)
    api_endpoint: ServiceOperationConfigApiEndpoint | None = Field(default=None)
    service_operation_config: ServiceOperationConfig | None = Field(default=None)

    # Attributes
    execution_context: JsonObject = Field(default_factory=JsonObject)
    operation_key: str
    result_info: str | None = Field(default=None)
    status: ServiceOperationStatus = Field(default=ServiceOperationStatus.queued)
