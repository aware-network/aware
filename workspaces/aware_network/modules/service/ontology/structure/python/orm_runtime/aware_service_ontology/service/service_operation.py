from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Service Ontology
from aware_service_ontology.service.service_enums import ServiceOperationStatus

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_api_ontology.api.api_call import ApiCall
    from aware_service_ontology.service.service_operation_config import ServiceOperationConfig
    from aware_service_ontology.service.service_operation_config_api_endpoint import ServiceOperationConfigApiEndpoint


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

    async def set_status(self, status: ServiceOperationStatus, result_info: str | None = None) -> ServiceOperation:
        """Updates execution status for this ServiceOperation."""

        payload = {"status": status, "result_info": result_info}
        result = await invoke_instance(orm_model=self, function_name="set_status", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceOperation):
            return value
        return ServiceOperation.validate_invocation_value(value)

    @classmethod
    async def build_via_service(
        cls,
        service_id: UUID,
        service_operation_config_id: UUID,
        operation_key: str,
        api_call_id: UUID | None = None,
        api_endpoint_id: UUID | None = None,
        status: ServiceOperationStatus = ServiceOperationStatus.queued,
        result_info: str | None = None,
        execution_context: JsonObject | None = None,
    ) -> ServiceOperation:
        """Creates one canonical service execution receipt under a concrete Service."""

        payload = {
            "service_id": service_id,
            "service_operation_config_id": service_operation_config_id,
            "operation_key": operation_key,
            "api_call_id": api_call_id,
            "api_endpoint_id": api_endpoint_id,
            "status": status,
            "result_info": result_info,
            "execution_context": execution_context,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceOperation):
            return value
        return ServiceOperation.validate_invocation_value(value)


class ServiceOperationSetStatusInput(BaseModel):
    status: ServiceOperationStatus
    result_info: str | None = Field(default=None)


class ServiceOperationSetStatusOutput(BaseModel):
    value: ServiceOperation


class ServiceOperationBuildViaServiceInput(BaseModel):
    service_id: UUID = Field(description="Foreign key for Service.service_operations")
    service_operation_config_id: UUID
    operation_key: str
    api_call_id: UUID | None = Field(default=None)
    api_endpoint_id: UUID | None = Field(default=None)
    status: ServiceOperationStatus = Field(default=ServiceOperationStatus.queued)
    result_info: str | None = Field(default=None)
    execution_context: JsonObject | None = Field(default=None)


class ServiceOperationBuildViaServiceOutput(BaseModel):
    value: ServiceOperation


FUNCTIONS = {
    "ServiceOperation": {
        "set_status": {
            "canonical": {
                "name": "set_status",
                "description": "Updates execution status for this ServiceOperation.",
                "is_constructor": False,
            },
            "input": ServiceOperationSetStatusInput,
            "output": ServiceOperationSetStatusOutput,
        },
        "build_via_service": {
            "canonical": {
                "name": "build_via_service",
                "description": "Creates one canonical service execution receipt under a concrete Service.",
                "is_constructor": True,
            },
            "input": ServiceOperationBuildViaServiceInput,
            "output": ServiceOperationBuildViaServiceOutput,
        },
    },
}

__all__ = [
    "ServiceOperation",
    "ServiceOperationSetStatusInput",
    "ServiceOperationSetStatusOutput",
    "ServiceOperationBuildViaServiceInput",
    "ServiceOperationBuildViaServiceOutput",
    "FUNCTIONS",
]
