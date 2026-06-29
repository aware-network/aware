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
    from aware_meta_ontology.class_.class_config import ClassConfig


class ApiCapabilityEndpointResponseConfig(ORMModel):
    """Optional terminal response contract beneath one request contract."""

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_request_config_id: UUID | None = Field(
        default=None, description="Foreign key for ApiCapabilityEndpointRequestConfig.response_config"
    )
    class_config_id: UUID = Field(description="Foreign key for ApiCapabilityEndpointResponseConfig.class_config")

    @classmethod
    async def build_via_api_capability_endpoint_request_config(
        cls, api_capability_endpoint_request_config_id: UUID, class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpointResponseConfig:
        """Create one endpoint response contract beneath ApiCapabilityEndpointRequestConfig."""

        payload = {
            "api_capability_endpoint_request_config_id": api_capability_endpoint_request_config_id,
            "class_config_id": class_config_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_api_capability_endpoint_request_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCapabilityEndpointResponseConfig):
            return value
        return ApiCapabilityEndpointResponseConfig.validate_invocation_value(value)


class ApiCapabilityEndpointResponseConfigBuildViaApiCapabilityEndpointRequestConfigInput(BaseModel):
    api_capability_endpoint_request_config_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpointRequestConfig.response_config"
    )
    class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointResponseConfigBuildViaApiCapabilityEndpointRequestConfigOutput(BaseModel):
    value: ApiCapabilityEndpointResponseConfig


FUNCTIONS = {
    "ApiCapabilityEndpointResponseConfig": {
        "build_via_api_capability_endpoint_request_config": {
            "canonical": {
                "name": "build_via_api_capability_endpoint_request_config",
                "description": "Create one endpoint response contract beneath ApiCapabilityEndpointRequestConfig.",
                "is_constructor": True,
            },
            "input": ApiCapabilityEndpointResponseConfigBuildViaApiCapabilityEndpointRequestConfigInput,
            "output": ApiCapabilityEndpointResponseConfigBuildViaApiCapabilityEndpointRequestConfigOutput,
        },
    },
}

__all__ = [
    "ApiCapabilityEndpointResponseConfig",
    "ApiCapabilityEndpointResponseConfigBuildViaApiCapabilityEndpointRequestConfigInput",
    "ApiCapabilityEndpointResponseConfigBuildViaApiCapabilityEndpointRequestConfigOutput",
    "FUNCTIONS",
]
