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
from aware_api_ontology.api.api_capability_endpoint_stream_enums import (
    ApiCapabilityEndpointStreamEventKind,
    ApiCapabilityEndpointStreamMode,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

if TYPE_CHECKING:
    from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
        ApiCapabilityEndpointStreamEventConfig,
    )


class ApiCapabilityEndpointStreamConfig(ORMModel):
    """Optional stream contract beneath one request contract."""

    # Relationships
    api_capability_endpoint_stream_event_configs: list[ApiCapabilityEndpointStreamEventConfig] = Field(
        default_factory=list, exclude=True
    )

    # Attributes
    stream_mode: ApiCapabilityEndpointStreamMode
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_request_config_id: UUID | None = Field(
        default=None, description="Foreign key for ApiCapabilityEndpointRequestConfig.stream_config"
    )

    async def create_event_config(
        self, kind: ApiCapabilityEndpointStreamEventKind, class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpointStreamEventConfig:
        """Create one typed stream event contract beneath this stream config."""

        payload = {"kind": kind, "class_config_id": class_config_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_event_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability_endpoint_stream_event_config import (
            ApiCapabilityEndpointStreamEventConfig,
        )

        if isinstance(value, ApiCapabilityEndpointStreamEventConfig):
            return value
        return ApiCapabilityEndpointStreamEventConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_api_capability_endpoint_request_config(
        cls,
        api_capability_endpoint_request_config_id: UUID,
        stream_mode: ApiCapabilityEndpointStreamMode,
        description: str | None = None,
    ) -> ApiCapabilityEndpointStreamConfig:
        """Create one endpoint stream contract beneath ApiCapabilityEndpointRequestConfig."""

        payload = {
            "api_capability_endpoint_request_config_id": api_capability_endpoint_request_config_id,
            "stream_mode": stream_mode,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_api_capability_endpoint_request_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCapabilityEndpointStreamConfig):
            return value
        return ApiCapabilityEndpointStreamConfig.validate_invocation_value(value)


class ApiCapabilityEndpointStreamConfigCreateEventConfigInput(BaseModel):
    kind: ApiCapabilityEndpointStreamEventKind
    class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointStreamConfigCreateEventConfigOutput(BaseModel):
    value: ApiCapabilityEndpointStreamEventConfig


class ApiCapabilityEndpointStreamConfigBuildViaApiCapabilityEndpointRequestConfigInput(BaseModel):
    api_capability_endpoint_request_config_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpointRequestConfig.stream_config"
    )
    stream_mode: ApiCapabilityEndpointStreamMode
    description: str | None = Field(default=None)


class ApiCapabilityEndpointStreamConfigBuildViaApiCapabilityEndpointRequestConfigOutput(BaseModel):
    value: ApiCapabilityEndpointStreamConfig


FUNCTIONS = {
    "ApiCapabilityEndpointStreamConfig": {
        "create_event_config": {
            "canonical": {
                "name": "create_event_config",
                "description": "Create one typed stream event contract beneath this stream config.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointStreamConfigCreateEventConfigInput,
            "output": ApiCapabilityEndpointStreamConfigCreateEventConfigOutput,
        },
        "build_via_api_capability_endpoint_request_config": {
            "canonical": {
                "name": "build_via_api_capability_endpoint_request_config",
                "description": "Create one endpoint stream contract beneath ApiCapabilityEndpointRequestConfig.",
                "is_constructor": True,
            },
            "input": ApiCapabilityEndpointStreamConfigBuildViaApiCapabilityEndpointRequestConfigInput,
            "output": ApiCapabilityEndpointStreamConfigBuildViaApiCapabilityEndpointRequestConfigOutput,
        },
    },
}

__all__ = [
    "ApiCapabilityEndpointStreamConfig",
    "ApiCapabilityEndpointStreamConfigCreateEventConfigInput",
    "ApiCapabilityEndpointStreamConfigCreateEventConfigOutput",
    "ApiCapabilityEndpointStreamConfigBuildViaApiCapabilityEndpointRequestConfigInput",
    "ApiCapabilityEndpointStreamConfigBuildViaApiCapabilityEndpointRequestConfigOutput",
    "FUNCTIONS",
]
