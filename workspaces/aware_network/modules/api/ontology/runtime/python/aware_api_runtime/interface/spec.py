from __future__ import annotations

from pydantic import BaseModel, Field


class ApiInterfaceStreamEventSpec(BaseModel):
    kind: str
    class_ref: str
    source_path: str
    description: str | None = None


class ApiInterfaceStreamSpec(BaseModel):
    stream_mode: str
    source_path: str
    events: list[ApiInterfaceStreamEventSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInterfaceResponseSpec(BaseModel):
    class_ref: str
    source_path: str
    description: str | None = None


class ApiInterfaceRequestSpec(BaseModel):
    class_ref: str
    source_path: str
    description: str | None = None


class ApiInterfaceEndpointSpec(BaseModel):
    name: str
    source_path: str
    discriminant: str
    request: ApiInterfaceRequestSpec
    response: ApiInterfaceResponseSpec | None = None
    stream: ApiInterfaceStreamSpec | None = None
    description: str | None = None


class ApiInterfaceCapabilitySpec(BaseModel):
    name: str
    source_path: str
    endpoints: list[ApiInterfaceEndpointSpec] = Field(default_factory=list)
    description: str | None = None


class ApiInterfaceApiSpec(BaseModel):
    name: str
    source_path: str
    capabilities: list[ApiInterfaceCapabilitySpec] = Field(default_factory=list)


class ApiInterfaceSpec(BaseModel):
    schema_version: int
    package_name: str
    fqn_prefix: str
    apis: list[ApiInterfaceApiSpec] = Field(default_factory=list)


__all__ = [
    "ApiInterfaceApiSpec",
    "ApiInterfaceCapabilitySpec",
    "ApiInterfaceEndpointSpec",
    "ApiInterfaceRequestSpec",
    "ApiInterfaceResponseSpec",
    "ApiInterfaceSpec",
    "ApiInterfaceStreamEventSpec",
    "ApiInterfaceStreamSpec",
]
