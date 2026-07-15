from __future__ import annotations

# Standard
from functools import lru_cache
from typing import (
    ClassVar,
    Literal,
    TYPE_CHECKING,
)
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.thread_layout_resolution.models import (
        ExperienceThreadLayoutIntentResolution,
    )


class ExperienceThreadLayoutResolutionServiceRequest(BaseModel):
    """
    Service DTOs for Experience semantic Thread-Layout intent resolution.
    This boundary returns config-level targets and evidence only. Runtime
    activation remains an Environment SDK/API responsibility.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_thread_layout_intent": "aware_experience_service_dto.experience.thread_layout_resolution.service_operation.ResolveExperienceThreadLayoutIntentRequest",
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
            return UnknownExperienceThreadLayoutResolutionServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceThreadLayoutResolutionServiceRequest(ExperienceThreadLayoutResolutionServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceThreadLayoutResolutionServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    resolution: ExperienceThreadLayoutIntentResolution | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_thread_layout_intent": "aware_experience_service_dto.experience.thread_layout_resolution.service_operation.ResolveExperienceThreadLayoutIntentResponse",
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
            return UnknownExperienceThreadLayoutResolutionServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceThreadLayoutResolutionServiceResponse(ExperienceThreadLayoutResolutionServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ResolveExperienceThreadLayoutIntentRequest(ExperienceThreadLayoutResolutionServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_experience_thread_layout_intent"] = "resolve_experience_thread_layout_intent"

    # Attributes
    intent_key: str
    experience_name: str | None = Field(default=None)
    profile_key: str | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    environment_handle: str | None = Field(default=None)
    environment_selector: str | None = Field(default=None)
    request_context: JsonObject = Field(default_factory=JsonObject)


class ResolveExperienceThreadLayoutIntentResponse(ExperienceThreadLayoutResolutionServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_experience_thread_layout_intent"] = "resolve_experience_thread_layout_intent"

    # Attributes
    resolution: ExperienceThreadLayoutIntentResolution
