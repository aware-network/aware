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

if TYPE_CHECKING:
    from aware_api_ontology.api.api import Api
    from aware_service_ontology.service.service_config_api_projection import ServiceConfigApiProjection


class ServiceConfigApi(ORMModel):
    # Relationships
    api: Api | None = Field(default=None, exclude=True)
    api_projections: list[ServiceConfigApiProjection] = Field(default_factory=list, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.apis")
    api_id: UUID = Field(description="Foreign key for ServiceConfigApi.api")

    async def create_projection(
        self, api_graph_projection_id: UUID, description: str | None = None
    ) -> ServiceConfigApiProjection:
        """Creates one config-level API projection bridge under this ServiceConfigApi."""

        payload = {"api_graph_projection_id": api_graph_projection_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_projection", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_service_ontology.service.service_config_api_projection import ServiceConfigApiProjection

        if isinstance(value, ServiceConfigApiProjection):
            return value
        return ServiceConfigApiProjection.validate_invocation_value(value)

    @classmethod
    async def build_via_service_config(
        cls, service_config_id: UUID, api_id: UUID, description: str | None = None
    ) -> ServiceConfigApi:
        """Create one config-level bridge between a ServiceConfig and one shared Api."""

        payload = {"service_config_id": service_config_id, "api_id": api_id, "description": description}
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceConfigApi):
            return value
        return ServiceConfigApi.validate_invocation_value(value)


class ServiceConfigApiCreateProjectionInput(BaseModel):
    api_graph_projection_id: UUID
    description: str | None = Field(default=None)


class ServiceConfigApiCreateProjectionOutput(BaseModel):
    value: ServiceConfigApiProjection


class ServiceConfigApiBuildViaServiceConfigInput(BaseModel):
    service_config_id: UUID = Field(description="Foreign key for ServiceConfig.apis")
    api_id: UUID
    description: str | None = Field(default=None)


class ServiceConfigApiBuildViaServiceConfigOutput(BaseModel):
    value: ServiceConfigApi


FUNCTIONS = {
    "ServiceConfigApi": {
        "create_projection": {
            "canonical": {
                "name": "create_projection",
                "description": "Creates one config-level API projection bridge under this ServiceConfigApi.",
                "is_constructor": False,
            },
            "input": ServiceConfigApiCreateProjectionInput,
            "output": ServiceConfigApiCreateProjectionOutput,
        },
        "build_via_service_config": {
            "canonical": {
                "name": "build_via_service_config",
                "description": "Create one config-level bridge between a ServiceConfig and one shared Api.",
                "is_constructor": True,
            },
            "input": ServiceConfigApiBuildViaServiceConfigInput,
            "output": ServiceConfigApiBuildViaServiceConfigOutput,
        },
    },
}

__all__ = [
    "ServiceConfigApi",
    "ServiceConfigApiCreateProjectionInput",
    "ServiceConfigApiCreateProjectionOutput",
    "ServiceConfigApiBuildViaServiceConfigInput",
    "ServiceConfigApiBuildViaServiceConfigOutput",
    "FUNCTIONS",
]
