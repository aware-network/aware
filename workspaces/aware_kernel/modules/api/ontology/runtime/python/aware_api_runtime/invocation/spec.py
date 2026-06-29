from __future__ import annotations

from pydantic import BaseModel, Field


class ApiInvocationFulfillmentBindingSpec(BaseModel):
    name: str
    graph_target: str
    graph_capability_function_name: str
    source_path: str


class ApiInvocationStreamEventSpec(BaseModel):
    kind: str
    class_ref: str
    python_model_ref: str | None = None
    source_path: str
    description: str | None = None


class ApiInvocationStreamSpec(BaseModel):
    stream_mode: str
    source_path: str
    events: list[ApiInvocationStreamEventSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInvocationResponseSpec(BaseModel):
    class_ref: str
    python_model_ref: str | None = None
    source_path: str
    description: str | None = None


class ApiInvocationRequestSpec(BaseModel):
    class_ref: str
    python_model_ref: str | None = None
    source_path: str
    description: str | None = None


class ApiInvocationEndpointSpec(BaseModel):
    name: str
    source_path: str
    endpoint_ref: str
    discriminant: str
    invocation_kind: str
    client_backend: str
    client_operation: str
    addressing_strategy: str
    request: ApiInvocationRequestSpec
    response: ApiInvocationResponseSpec | None = None
    stream: ApiInvocationStreamSpec | None = None
    fulfillment_bindings: list[ApiInvocationFulfillmentBindingSpec] = Field(default_factory=list)
    adapter_callable_ref: str | None = None
    description: str | None = None


class ApiInvocationCapabilitySpec(BaseModel):
    name: str
    source_path: str
    endpoints: list[ApiInvocationEndpointSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInvocationApiSpec(BaseModel):
    name: str
    source_path: str
    capabilities: list[ApiInvocationCapabilitySpec] = Field(default_factory=list)


class ApiInvocationManifest(BaseModel):
    schema_version: int
    package_name: str
    fqn_prefix: str
    apis: list[ApiInvocationApiSpec] = Field(default_factory=list)


__all__ = [
    "ApiInvocationApiSpec",
    "ApiInvocationCapabilitySpec",
    "ApiInvocationEndpointSpec",
    "ApiInvocationFulfillmentBindingSpec",
    "ApiInvocationManifest",
    "ApiInvocationRequestSpec",
    "ApiInvocationResponseSpec",
    "ApiInvocationStreamEventSpec",
    "ApiInvocationStreamSpec",
]
