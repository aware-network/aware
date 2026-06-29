from __future__ import annotations

# Standard
from enum import Enum
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
    SerializeAsAny,
    field_validator,
    model_validator,
)

# Types
from aware_types import (
    JsonObject,
    JsonValue,
)


class ApiRequestStatus(Enum):
    """
    Canonical API ingress DTOs (transport-layer, graph/ORM agnostic).
    SSOT: `api-service-dto` generated from this API-owned `.aware` contract.
    `aware_comms` may re-export these DTOs for transport/client import
    stability, but schema ownership remains under `modules/api/apis/api/dto`.
    """

    succeeded = "succeeded"
    failed = "failed"
    pending = "pending"


class ApiStreamLifecycle(Enum):
    auto_close = "auto_close"
    started = "started"
    closed = "closed"


class ApiOperationContext(BaseModel):
    # Attributes
    actor_id: UUID | None = Field(default=None)


class ApiOperation(BaseModel):
    # Attributes
    request: SerializeAsAny[ApiOperationRequest] | None = Field(default=None)
    response: SerializeAsAny[ApiOperationResponse] | None = Field(default=None)

    @field_validator("request", mode="before")
    @classmethod
    def _parse_request(cls, v):
        if v is None:
            return None
        return ApiOperationRequest.parse(v)

    @field_validator("response", mode="before")
    @classmethod
    def _parse_response(cls, v):
        if v is None:
            return None
        return ApiOperationResponse.parse(v)

    @model_validator(mode="after")
    def _validate_oneof_0(self):
        if (
            sum(
                v is not None
                for v in (
                    self.request,
                    self.response,
                )
            )
            != 1
        ):
            raise ValueError("Exactly one of request, response must be set")
        return self


class ApiOperationRequest(ApiOperationContext):
    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "invoke_api_endpoint": "aware_api_service_dto.comms.models.api.InvokeApiEndpointRequest",
        "stream_api_endpoint": "aware_api_service_dto.comms.models.api.StreamApiEndpointRequest",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownApiOperationRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownApiOperationRequest(ApiOperationRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ApiOperationResponse(ApiOperationContext):
    # Discriminator Key
    operation: str

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "invoke_api_endpoint": "aware_api_service_dto.comms.models.api.InvokeApiEndpointResponse",
    }

    @staticmethod
    @lru_cache(maxsize=None)
    def _resolve_fqn(fqn: str):
        from importlib import import_module

        module_name, class_name = fqn.rsplit(".", 1)
        return getattr(import_module(module_name), class_name)

    @classmethod
    def parse(cls, v, *, strict: bool = False):
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            tag = v.get(cls._DISCRIMINATOR_KEY)
            fqn = cls._TAG_TO_TYPE.get(tag)
            if fqn:
                model_cls = cls._resolve_fqn(fqn)
                return model_cls.model_validate(v)
            if strict:
                raise ValueError(f"Unknown {cls.__name__} tag: {tag!r}")
            return UnknownApiOperationResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownApiOperationResponse(ApiOperationResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ApiInvocationSurfaceContext(BaseModel):
    # Attributes
    pane_ref: str | None = Field(default=None)
    window_key: str | None = Field(default=None)
    layout_key: str | None = Field(default=None)
    section_key: str | None = Field(default=None)
    pane_kind: str | None = Field(default=None)
    state_source_kind: str | None = Field(default=None)
    pane_config_id: UUID | None = Field(default=None)
    pane_package_id: UUID | None = Field(default=None)
    pane_package_name: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    projection_experience_view_id: UUID | None = Field(default=None)
    state_model_id: UUID | None = Field(default=None)
    state_provider_ref: str | None = Field(default=None)
    state_provider_kind: str | None = Field(default=None)


class ApiInvocationExperienceContext(BaseModel):
    # Attributes
    experience_name: str | None = Field(default=None)
    experience_ref: str | None = Field(default=None)
    projection_experience_id: UUID | None = Field(default=None)
    projection_experience_view_id: UUID | None = Field(default=None)
    experience_revision: str | None = Field(default=None)


class ApiInvocationAttentionScope(BaseModel):
    # Attributes
    layout_section_id: UUID | None = Field(default=None)
    section_focus_scope_id: UUID | None = Field(default=None)
    focus_scope_id: UUID | None = Field(default=None)
    observable_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    state_projection_hash: str | None = Field(default=None)


class ApiInvocationContext(BaseModel):
    # Attributes
    surface: ApiInvocationSurfaceContext | None = Field(default=None)
    experience: ApiInvocationExperienceContext | None = Field(default=None)
    attention: ApiInvocationAttentionScope | None = Field(default=None)


class InvokeApiEndpointRequest(ApiOperationRequest):
    # Discriminator Tag
    operation: Literal["invoke_api_endpoint"] = "invoke_api_endpoint"

    # Attributes
    endpoint_ref: str
    discriminant: str
    request_payload: JsonObject
    invocation_context: ApiInvocationContext | None = Field(default=None)


class StreamApiEndpointRequest(ApiOperationRequest):
    # Discriminator Tag
    operation: Literal["stream_api_endpoint"] = "stream_api_endpoint"

    # Attributes
    endpoint_ref: str
    discriminant: str
    request_payload: JsonObject
    invocation_context: ApiInvocationContext | None = Field(default=None)


class InvokeApiEndpointResponse(ApiOperationResponse):
    # Discriminator Tag
    operation: Literal["invoke_api_endpoint"] = "invoke_api_endpoint"

    # Attributes
    status: ApiRequestStatus
    error: str | None = Field(default=None)
    response_payload: JsonValue | None = Field(default=None)
    stream_lifecycle: ApiStreamLifecycle = Field(default=ApiStreamLifecycle.auto_close)
