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
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_api_ontology.api.api_view import ApiView
    from aware_service_ontology.service.service_config_api import ServiceConfigApi


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

    @classmethod
    async def build_via_service_operation_config(
        cls,
        service_operation_config_id: UUID,
        service_config_api_id: UUID,
        api_view_id: UUID,
        description: str | None = None,
    ) -> ServiceOperationConfigApiView:
        """
        Creates one ServiceOperationConfig-owned fulfillment binding for an API view.

        Contract:
        - Parent ServiceOperationConfig scope is propagated by constructor lowering.
        - `api_view` is the API-owned readable state contract this Service operation fulfills.
        - The owning ServiceOperationConfig is the fulfillment provider; no nested view-provider rail
        exists.
        """

        payload = {
            "service_operation_config_id": service_operation_config_id,
            "service_config_api_id": service_config_api_id,
            "api_view_id": api_view_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_service_operation_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceOperationConfigApiView):
            return value
        return ServiceOperationConfigApiView.validate_invocation_value(value)


class ServiceOperationConfigApiViewBuildViaServiceOperationConfigInput(BaseModel):
    service_operation_config_id: UUID = Field(description="Foreign key for ServiceOperationConfig.api_views")
    service_config_api_id: UUID
    api_view_id: UUID
    description: str | None = Field(default=None)


class ServiceOperationConfigApiViewBuildViaServiceOperationConfigOutput(BaseModel):
    value: ServiceOperationConfigApiView


FUNCTIONS = {
    "ServiceOperationConfigApiView": {
        "build_via_service_operation_config": {
            "canonical": {
                "name": "build_via_service_operation_config",
                "description": "Creates one ServiceOperationConfig-owned fulfillment binding for an API view.\n\nContract:\n- Parent ServiceOperationConfig scope is propagated by constructor lowering.\n- `api_view` is the API-owned readable state contract this Service operation fulfills.\n- The owning ServiceOperationConfig is the fulfillment provider; no nested view-provider rail exists.",
                "is_constructor": True,
            },
            "input": ServiceOperationConfigApiViewBuildViaServiceOperationConfigInput,
            "output": ServiceOperationConfigApiViewBuildViaServiceOperationConfigOutput,
        },
    },
}

__all__ = [
    "ServiceOperationConfigApiView",
    "ServiceOperationConfigApiViewBuildViaServiceOperationConfigInput",
    "ServiceOperationConfigApiViewBuildViaServiceOperationConfigOutput",
    "FUNCTIONS",
]
