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
    from aware_api_ontology.api.api_call import ApiCall
    from aware_api_ontology.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction
    from aware_api_ontology.api.api_capability_endpoint_request_config import ApiCapabilityEndpointRequestConfig
    from aware_api_ontology.api.api_capability_endpoint_response_config import ApiCapabilityEndpointResponseConfig
    from aware_api_ontology.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig


class ApiCapabilityEndpoint(ORMModel):
    """
    Public API caller hit surface.
    Caller-facing truth:
    - the caller hits one endpoint
    - the caller provides payload through this endpoint's request contract DTO `ClassConfig`
    - stage-one `ApiCall` anchors here, not on endpoint-function fulfillment
    This object is ingress contract truth, not graph-call fulfillment truth.
    Endpoint identity stays on the public port rail (`api_capability_id + name`).
    The required request contract is created beneath that one endpoint rail during
    endpoint construction; it is not a second public authoring step.
    """

    # Relationships
    api_calls: list[ApiCall] = Field(default_factory=list, exclude=True)
    request_config: ApiCapabilityEndpointRequestConfig | None = Field(default=None, exclude=True)
    api_capability_endpoint_functions: list[ApiCapabilityEndpointFunction] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    description: str | None = Field(default=None)

    # Foreign Keys
    api_capability_id: UUID = Field(description="Foreign key for ApiCapability.api_capability_endpoints")

    async def create_call(self, call_key: UUID, description: str | None = None) -> ApiCall:
        """Create one stage-one API call receipt anchored on this endpoint."""

        payload = {"call_key": call_key, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_call", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_call import ApiCall

        if isinstance(value, ApiCall):
            return value
        return ApiCall.validate_invocation_value(value)

    async def create_function(
        self, name: str, api_graph_capability_function_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpointFunction:
        """Create one named endpoint-owned callable binding to one graph-scoped capability function."""

        payload = {
            "name": name,
            "api_graph_capability_function_id": api_graph_capability_function_id,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="create_function", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability_endpoint_function import ApiCapabilityEndpointFunction

        if isinstance(value, ApiCapabilityEndpointFunction):
            return value
        return ApiCapabilityEndpointFunction.validate_invocation_value(value)

    async def ensure_request_config(
        self, request_class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpointRequestConfig:
        """
        Ensure the required request contract beneath this endpoint.

        Contract:
        - Endpoint creation must materialize this rail already.
        - This function exists so the endpoint -> request_config relationship remains
          an explicit containment propagation rail in canonical `.aware`.
        """

        payload = {"request_class_config_id": request_class_config_id, "description": description}
        result = await invoke_instance(orm_model=self, function_name="ensure_request_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability_endpoint_request_config import ApiCapabilityEndpointRequestConfig

        if isinstance(value, ApiCapabilityEndpointRequestConfig):
            return value
        return ApiCapabilityEndpointRequestConfig.validate_invocation_value(value)

    async def create_response_config(
        self, class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpointResponseConfig:
        """Create one optional response contract beneath this endpoint's request contract."""

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
        """Create one optional stream contract beneath this endpoint's request contract."""

        payload = {"stream_mode": stream_mode, "description": description}
        result = await invoke_instance(orm_model=self, function_name="create_stream_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_api_ontology.api.api_capability_endpoint_stream_config import ApiCapabilityEndpointStreamConfig

        if isinstance(value, ApiCapabilityEndpointStreamConfig):
            return value
        return ApiCapabilityEndpointStreamConfig.validate_invocation_value(value)

    @classmethod
    async def create_via_api_capability(
        cls, api_capability_id: UUID, name: str, request_class_config_id: UUID, description: str | None = None
    ) -> ApiCapabilityEndpoint:
        """
        Create one deterministic external/public endpoint rail under ApiCapability
        and materialize its required request contract in the same constructor path.
        """

        payload = {
            "api_capability_id": api_capability_id,
            "name": name,
            "request_class_config_id": request_class_config_id,
            "description": description,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_api_capability", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ApiCapabilityEndpoint):
            return value
        return ApiCapabilityEndpoint.validate_invocation_value(value)


class ApiCapabilityEndpointCreateCallInput(BaseModel):
    call_key: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointCreateCallOutput(BaseModel):
    value: ApiCall


class ApiCapabilityEndpointCreateFunctionInput(BaseModel):
    name: str
    api_graph_capability_function_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointCreateFunctionOutput(BaseModel):
    value: ApiCapabilityEndpointFunction


class ApiCapabilityEndpointEnsureRequestConfigInput(BaseModel):
    request_class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointEnsureRequestConfigOutput(BaseModel):
    value: ApiCapabilityEndpointRequestConfig


class ApiCapabilityEndpointCreateResponseConfigInput(BaseModel):
    class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointCreateResponseConfigOutput(BaseModel):
    value: ApiCapabilityEndpointResponseConfig


class ApiCapabilityEndpointCreateStreamConfigInput(BaseModel):
    stream_mode: ApiCapabilityEndpointStreamMode
    description: str | None = Field(default=None)


class ApiCapabilityEndpointCreateStreamConfigOutput(BaseModel):
    value: ApiCapabilityEndpointStreamConfig


class ApiCapabilityEndpointCreateViaApiCapabilityInput(BaseModel):
    api_capability_id: UUID = Field(description="Foreign key for ApiCapability.api_capability_endpoints")
    name: str
    request_class_config_id: UUID
    description: str | None = Field(default=None)


class ApiCapabilityEndpointCreateViaApiCapabilityOutput(BaseModel):
    value: ApiCapabilityEndpoint


FUNCTIONS = {
    "ApiCapabilityEndpoint": {
        "create_call": {
            "canonical": {
                "name": "create_call",
                "description": "Create one stage-one API call receipt anchored on this endpoint.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointCreateCallInput,
            "output": ApiCapabilityEndpointCreateCallOutput,
        },
        "create_function": {
            "canonical": {
                "name": "create_function",
                "description": "Create one named endpoint-owned callable binding to one graph-scoped capability function.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointCreateFunctionInput,
            "output": ApiCapabilityEndpointCreateFunctionOutput,
        },
        "ensure_request_config": {
            "canonical": {
                "name": "ensure_request_config",
                "description": "Ensure the required request contract beneath this endpoint.\n\nContract:\n- Endpoint creation must materialize this rail already.\n- This function exists so the endpoint -> request_config relationship remains\n  an explicit containment propagation rail in canonical `.aware`.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointEnsureRequestConfigInput,
            "output": ApiCapabilityEndpointEnsureRequestConfigOutput,
        },
        "create_response_config": {
            "canonical": {
                "name": "create_response_config",
                "description": "Create one optional response contract beneath this endpoint's request contract.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointCreateResponseConfigInput,
            "output": ApiCapabilityEndpointCreateResponseConfigOutput,
        },
        "create_stream_config": {
            "canonical": {
                "name": "create_stream_config",
                "description": "Create one optional stream contract beneath this endpoint's request contract.",
                "is_constructor": False,
            },
            "input": ApiCapabilityEndpointCreateStreamConfigInput,
            "output": ApiCapabilityEndpointCreateStreamConfigOutput,
        },
        "create_via_api_capability": {
            "canonical": {
                "name": "create_via_api_capability",
                "description": "Create one deterministic external/public endpoint rail under ApiCapability\nand materialize its required request contract in the same constructor path.",
                "is_constructor": True,
            },
            "input": ApiCapabilityEndpointCreateViaApiCapabilityInput,
            "output": ApiCapabilityEndpointCreateViaApiCapabilityOutput,
        },
    },
}

__all__ = [
    "ApiCapabilityEndpoint",
    "ApiCapabilityEndpointCreateCallInput",
    "ApiCapabilityEndpointCreateCallOutput",
    "ApiCapabilityEndpointCreateFunctionInput",
    "ApiCapabilityEndpointCreateFunctionOutput",
    "ApiCapabilityEndpointEnsureRequestConfigInput",
    "ApiCapabilityEndpointEnsureRequestConfigOutput",
    "ApiCapabilityEndpointCreateResponseConfigInput",
    "ApiCapabilityEndpointCreateResponseConfigOutput",
    "ApiCapabilityEndpointCreateStreamConfigInput",
    "ApiCapabilityEndpointCreateStreamConfigOutput",
    "ApiCapabilityEndpointCreateViaApiCapabilityInput",
    "ApiCapabilityEndpointCreateViaApiCapabilityOutput",
    "FUNCTIONS",
]
