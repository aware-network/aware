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
    from aware_experience_service_dto.experience.session_view_frame.service_operation import (
        ResolveExperienceSessionViewFrameRequest,
    )
    from aware_experience_service_dto.experience.view_state.models import ExperienceViewStateSnapshot


class ExperienceViewStateServiceRequest(BaseModel):
    """
    Canonical request/response DTOs for Experience view-state subscriptions.
    These DTOs describe an Experience-owned subscription facade. Service-owned
    provider endpoints remain typed fulfillment rails behind this facade.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "watch_experience_view_state": "aware_experience_service_dto.experience.view_state.service_operation.WatchExperienceViewStateRequest",
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
            return UnknownExperienceViewStateServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceViewStateServiceRequest(ExperienceViewStateServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceViewStateServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    snapshot: ExperienceViewStateSnapshot | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "watch_experience_view_state": "aware_experience_service_dto.experience.view_state.service_operation.WatchExperienceViewStateResponse",
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
            return UnknownExperienceViewStateServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceViewStateServiceResponse(ExperienceViewStateServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class WatchExperienceViewStateRequest(ExperienceViewStateServiceRequest):
    # Discriminator Tag
    operation: Literal["watch_experience_view_state"] = "watch_experience_view_state"

    # Attributes
    experience_name: str
    session_view_frame_request: ResolveExperienceSessionViewFrameRequest
    projection_experience_view_instance_id: UUID | None = Field(default=None)
    provider_context: JsonObject = Field(default_factory=JsonObject)
    known_cursor: str | None = Field(default=None)
    known_digest: str | None = Field(default=None)
    poll_interval_ms: int = Field(default=1000)


class WatchExperienceViewStateResponse(ExperienceViewStateServiceResponse):
    # Discriminator Tag
    operation: Literal["watch_experience_view_state"] = "watch_experience_view_state"

    # Attributes
    experience_name: str
    snapshot: ExperienceViewStateSnapshot
    changed: bool = Field(default=True)
