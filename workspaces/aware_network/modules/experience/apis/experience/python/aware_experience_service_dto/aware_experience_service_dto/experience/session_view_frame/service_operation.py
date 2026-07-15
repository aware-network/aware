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

# Environment Service Dto
from aware_environment_service_dto.environment.environment import (
    EnvironmentActorAdmissionReceipt,
    EnvironmentSessionJoinReceipt,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.actor_admission.models import ExperienceActorConfigAdmissionReceipt
    from aware_experience_service_dto.experience.session_context.models import (
        ExperienceSessionAttentionResolutionRequest,
    )
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffActorContext
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffScope
    from aware_experience_service_dto.experience.session_view_frame.models import ExperienceSessionViewFrame


class ExperienceSessionViewFrameServiceRequest(BaseModel):
    """
    Request/response DTOs for Experience session view-frame resolution.
    The operation returns a consumer read model by first resolving Experience
    session context, which resolves Attention through Environment service API
    truth. It does not persist a frame or inspect Attention internals directly.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_session_view_frame": "aware_experience_service_dto.experience.session_view_frame.service_operation.ResolveExperienceSessionViewFrameRequest",
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
            return UnknownExperienceSessionViewFrameServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionViewFrameServiceRequest(ExperienceSessionViewFrameServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceSessionViewFrameServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    frame: ExperienceSessionViewFrame | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_session_view_frame": "aware_experience_service_dto.experience.session_view_frame.service_operation.ResolveExperienceSessionViewFrameResponse",
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
            return UnknownExperienceSessionViewFrameServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionViewFrameServiceResponse(ExperienceSessionViewFrameServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ResolveExperienceSessionViewFrameRequest(ExperienceSessionViewFrameServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_experience_session_view_frame"] = "resolve_experience_session_view_frame"

    # Attributes
    session_scope: ExperienceSessionHandoffScope
    actor_context: ExperienceSessionHandoffActorContext | None = Field(default=None)
    environment_admission: EnvironmentActorAdmissionReceipt | None = Field(default=None)
    environment_session_join: EnvironmentSessionJoinReceipt | None = Field(default=None)
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = Field(default=None)
    experience_identity_session_config_id: UUID | None = Field(default=None)
    environment_attention: ExperienceSessionAttentionResolutionRequest | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class ResolveExperienceSessionViewFrameResponse(ExperienceSessionViewFrameServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_experience_session_view_frame"] = "resolve_experience_session_view_frame"

    # Attributes
    frame: ExperienceSessionViewFrame
