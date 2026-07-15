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
from aware_api_ontology.api.api_capability_endpoint_stream_enums import ApiCapabilityEndpointStreamEventKind

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig


class ApiCapabilityEndpointStreamEventConfig(ORMModel):
    """Typed event contract beneath one endpoint stream contract."""

    # Relationships
    class_config: ClassConfig | None = Field(default=None, exclude=True)

    # Attributes
    kind: ApiCapabilityEndpointStreamEventKind
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_endpoint_stream_config_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpointStreamConfig.api_capability_endpoint_stream_event_configs"
    )
    class_config_id: UUID = Field(description="Foreign key for ApiCapabilityEndpointStreamEventConfig.class_config")

    @classmethod
    async def create_via_api_capability_endpoint_stream_config(
        cls,
        api_capability_endpoint_stream_config_id: UUID,
        kind: ApiCapabilityEndpointStreamEventKind,
        class_config_id: UUID,
        description: str | None = None,
    ) -> ApiCapabilityEndpointStreamEventConfig:
        """Create one typed stream event contract beneath ApiCapabilityEndpointStreamConfig."""

        payload = {
            "api_capability_endpoint_stream_config_id": api_capability_endpoint_stream_config_id,
            "kind": kind,
            "class_config_id": class_config_id,
            "description": description,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_api_capability_endpoint_stream_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCapabilityEndpointStreamEventConfig):
            return value
        return ApiCapabilityEndpointStreamEventConfig.validate_invocation_value(value)


class ApiCapabilityEndpointStreamEventConfigCreateViaApiCapabilityEndpointStreamConfigInput(BaseModel):
    api_capability_endpoint_stream_config_id: UUID = Field(
        description="Foreign key for ApiCapabilityEndpointStreamConfig.api_capability_endpoint_stream_event_configs"
    )
    kind: ApiCapabilityEndpointStreamEventKind
    class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointStreamEventConfigCreateViaApiCapabilityEndpointStreamConfigOutput(BaseModel):
    value: ApiCapabilityEndpointStreamEventConfig


FUNCTIONS = {
    "ApiCapabilityEndpointStreamEventConfig": {
        "create_via_api_capability_endpoint_stream_config": {
            "canonical": {
                "name": "create_via_api_capability_endpoint_stream_config",
                "description": "Create one typed stream event contract beneath ApiCapabilityEndpointStreamConfig.",
                "is_constructor": True,
            },
            "input": ApiCapabilityEndpointStreamEventConfigCreateViaApiCapabilityEndpointStreamConfigInput,
            "output": ApiCapabilityEndpointStreamEventConfigCreateViaApiCapabilityEndpointStreamConfigOutput,
        },
    },
}

__all__ = [
    "ApiCapabilityEndpointStreamEventConfig",
    "ApiCapabilityEndpointStreamEventConfigCreateViaApiCapabilityEndpointStreamConfigInput",
    "ApiCapabilityEndpointStreamEventConfigCreateViaApiCapabilityEndpointStreamConfigOutput",
    "FUNCTIONS",
]
