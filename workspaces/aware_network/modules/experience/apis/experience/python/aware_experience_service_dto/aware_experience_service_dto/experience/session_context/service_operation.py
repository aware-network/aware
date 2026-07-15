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
    from aware_experience_service_dto.experience.session_context.models import ExperienceSessionContextReceipt
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffActorContext
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffScope


class ExperienceSessionContextServiceRequest(BaseModel):
    """
    Request/response DTOs for Experience session context resolution.
    The operation validates the Experience session actor handoff context, then
    resolves the shared Environment/Attention target through Environment service
    API truth. It returns a read receipt for consumers such as Interface.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_session_context": "aware_experience_service_dto.experience.session_context.service_operation.ResolveExperienceSessionContextRequest",
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
            return UnknownExperienceSessionContextServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionContextServiceRequest(ExperienceSessionContextServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceSessionContextServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    receipt: ExperienceSessionContextReceipt | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_session_context": "aware_experience_service_dto.experience.session_context.service_operation.ResolveExperienceSessionContextResponse",
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
            return UnknownExperienceSessionContextServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionContextServiceResponse(ExperienceSessionContextServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ResolveExperienceSessionContextRequest(ExperienceSessionContextServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_experience_session_context"] = "resolve_experience_session_context"

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


class ResolveExperienceSessionContextResponse(ExperienceSessionContextServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_experience_session_context"] = "resolve_experience_session_context"

    # Attributes
    receipt: ExperienceSessionContextReceipt
