from __future__ import annotations

# Standard
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
)

# Third-party
from pydantic import (
    BaseModel,
    Field,
    SerializeAsAny,
    field_validator,
)

# Environment Service Dto
from aware_environment_service_dto.environment.environment import (
    EnvironmentOperationRequest,
    EnvironmentOperationResponse,
)


class EnvironmentServiceOperation(BaseModel):
    """
    Environment service operation base (DTO-only).
    SSOT: `environment-service-dto` generated from `apis/environment/dto`.
    This is the Environment plugin rail payload root. Service-specific variants
    (Inference now; LSP/Terminal later) should `augment` this type.
    NOTE:
    This is defined in its own module to avoid import cycles between the
    environment DTO module and service-specific DTO modules.
    """

    # Discriminator Key
    service: str

    # Attributes
    operation: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "service"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {}

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
            return UnknownEnvironmentServiceOperation.model_validate(v)
        return cls.model_validate(v)


class UnknownEnvironmentServiceOperation(EnvironmentServiceOperation):
    """Forward-compatible fallback when `service` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class EnvironmentServiceOperationRequest(EnvironmentOperationRequest):
    # Discriminator Tag
    operation: Literal["service_operation"] = "service_operation"

    # Attributes
    service_operation: SerializeAsAny[EnvironmentServiceOperation]

    @field_validator("service_operation", mode="before")
    @classmethod
    def _parse_service_operation(cls, v):
        if v is None:
            return None
        return EnvironmentServiceOperation.parse(v)


class EnvironmentServiceOperationResponse(EnvironmentOperationResponse):
    # Discriminator Tag
    operation: Literal["service_operation"] = "service_operation"

    # Attributes
    service_operation: SerializeAsAny[EnvironmentServiceOperation]

    @field_validator("service_operation", mode="before")
    @classmethod
    def _parse_service_operation(cls, v):
        if v is None:
            return None
        return EnvironmentServiceOperation.parse(v)
