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
    from aware_api_ontology.api.api_graph_projection import ApiGraphProjection


class ServiceConfigApiProjection(ORMModel):
    # Relationships
    api_graph_projection: ApiGraphProjection | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    service_config_api_id: UUID = Field(description="Foreign key for ServiceConfigApi.api_projections")
    api_graph_projection_id: UUID = Field(description="Foreign key for ServiceConfigApiProjection.api_graph_projection")

    @classmethod
    async def build_via_service_config_api(
        cls, service_config_api_id: UUID, api_graph_projection_id: UUID, description: str | None = None
    ) -> ServiceConfigApiProjection:
        """Create one config-level bridge from a ServiceConfigApi to one API-owned graph projection."""

        payload = {
            "service_config_api_id": service_config_api_id,
            "api_graph_projection_id": api_graph_projection_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_service_config_api", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ServiceConfigApiProjection):
            return value
        return ServiceConfigApiProjection.validate_invocation_value(value)


class ServiceConfigApiProjectionBuildViaServiceConfigApiInput(BaseModel):
    service_config_api_id: UUID = Field(description="Foreign key for ServiceConfigApi.api_projections")
    api_graph_projection_id: UUID
    description: str | None = Field(default=None)


class ServiceConfigApiProjectionBuildViaServiceConfigApiOutput(BaseModel):
    value: ServiceConfigApiProjection


FUNCTIONS = {
    "ServiceConfigApiProjection": {
        "build_via_service_config_api": {
            "canonical": {
                "name": "build_via_service_config_api",
                "description": "Create one config-level bridge from a ServiceConfigApi to one API-owned graph projection.",
                "is_constructor": True,
            },
            "input": ServiceConfigApiProjectionBuildViaServiceConfigApiInput,
            "output": ServiceConfigApiProjectionBuildViaServiceConfigApiOutput,
        },
    },
}

__all__ = [
    "ServiceConfigApiProjection",
    "ServiceConfigApiProjectionBuildViaServiceConfigApiInput",
    "ServiceConfigApiProjectionBuildViaServiceConfigApiOutput",
    "FUNCTIONS",
]
