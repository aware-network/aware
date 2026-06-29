from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Api Ontology
from aware_api_ontology.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamMode

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_api_ontology.api.api_capability_endpoint_response_config import ApiCapabilityEndpointResponseConfig
    from aware_api_ontology.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig
    from aware_meta_ontology.class_.class_config import ClassConfig


class ApiCapabilityEndpointRequestConfig(ORMModel):
    """
    Required request contract under one endpoint.
    Caller-facing contract truth:
    - owns the endpoint request DTO `ClassConfig`
    - may own one terminal response contract
    - may own one stream contract
    """

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)
    response_config: ApiCapabilityEndpointResponseConfig | None = Field(default=None, exclude=True)
    stream_config: ApiCapabilityEndpointStreamConfig | None = Field(default=None, exclude=True)

    # Attributes
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_id: UUID = Field(description="Foreign key for ApiCapabilityEndpoint.request_config")
    class_config_id: UUID = Field(description="Foreign key for ApiCapabilityEndpointRequestConfig.class_config")

    async def create_response_config(
        self, class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpointResponseConfig:
        """Create one optional terminal response contract beneath this request contract."""

        payload = {"class_config_id": class_config_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_response_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability_endpoint_response_config import ApiCapabilityEndpointResponseConfig

        if isinstance(value, ApiCapabilityEndpointResponseConfig):
            return value
        return ApiCapabilityEndpointResponseConfig.validate_invocation_value(value)

    async def create_stream_config(
        self, stream_mode: ApiCapabilityEndpointStreamMode, description: str | None = None
    ) -> ApiCapabilityEndpointStreamConfig:
        """Create one optional stream contract beneath this request contract."""

        payload = {"stream_mode": stream_mode, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_stream_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig

        if isinstance(value, ApiCapabilityEndpointStreamConfig):
            return value
        return ApiCapabilityEndpointStreamConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_api_capability_endpoint(
        cls, api_capability_endpoint_id: UUID, class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpointRequestConfig:
        """Create one endpoint request contract beneath ApiCapabilityEndpoint."""

        payload = {
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "class_config_id": class_config_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_api_capability_endpoint", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCapabilityEndpointRequestConfig):
            return value
        return ApiCapabilityEndpointRequestConfig.validate_invocation_value(value)


class ApiCapabilityEndpointRequestConfigCreateResponseConfigInput(BaseModel):
    class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointRequestConfigCreateResponseConfigOutput(BaseModel):
    value: ApiCapabilityEndpointResponseConfig


class ApiCapabilityEndpointRequestConfigCreateStreamConfigInput(BaseModel):
    stream_mode: ApiCapabilityEndpointStreamMode
    description: str | None = Field(default=None)


class ApiCapabilityEndpointRequestConfigCreateStreamConfigOutput(BaseModel):
    value: ApiCapabilityEndpointStreamConfig


class ApiCapabilityEndpointRequestConfigBuildViaApiCapabilityEndpointInput(BaseModel):
    api_capability_endpoint_id: UUID = Field(description="Foreign key for ApiCapabilityEndpoint.request_config")
    class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointRequestConfigBuildViaApiCapabilityEndpointOutput(BaseModel):
    value: ApiCapabilityEndpointRequestConfig


FUNCTIONS = {
    "ApiCapabilityEndpointRequestConfig": {
        "create_response_config": {
            "canonical": {
                "name": "create_response_config",
                "description": "Create one optional terminal response contract beneath this request contract.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointRequestConfigCreateResponseConfigInput,
            "output": ApiCapabilityEndpointRequestConfigCreateResponseConfigOutput,
        },
        "create_stream_config": {
            "canonical": {
                "name": "create_stream_config",
                "description": "Create one optional stream contract beneath this request contract.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointRequestConfigCreateStreamConfigInput,
            "output": ApiCapabilityEndpointRequestConfigCreateStreamConfigOutput,
        },
        "build_via_api_capability_endpoint": {
            "canonical": {
                "name": "build_via_api_capability_endpoint",
                "description": "Create one endpoint request contract beneath ApiCapabilityEndpoint.",
                "is_constructor": True,
            },
            "input": ApiCapabilityEndpointRequestConfigBuildViaApiCapabilityEndpointInput,
            "output": ApiCapabilityEndpointRequestConfigBuildViaApiCapabilityEndpointOutput,
        },
    },
}

__all__ = [
    "ApiCapabilityEndpointRequestConfig",
    "ApiCapabilityEndpointRequestConfigCreateResponseConfigInput",
    "ApiCapabilityEndpointRequestConfigCreateResponseConfigOutput",
    "ApiCapabilityEndpointRequestConfigCreateStreamConfigInput",
    "ApiCapabilityEndpointRequestConfigCreateStreamConfigOutput",
    "ApiCapabilityEndpointRequestConfigBuildViaApiCapabilityEndpointInput",
    "ApiCapabilityEndpointRequestConfigBuildViaApiCapabilityEndpointOutput",
    "FUNCTIONS",
]
