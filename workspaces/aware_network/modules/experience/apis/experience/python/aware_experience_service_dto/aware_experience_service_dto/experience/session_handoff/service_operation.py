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
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffActorContext
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffFeatureSpec
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffReceipt
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffScope
    from aware_experience_service_dto.experience.session_handoff.models import ExperienceSessionHandoffStatusReceipt


class ExperienceSessionHandoffServiceRequest(BaseModel):
    """
    Request/response DTOs for the Experience session handoff service boundary.
    The handoff admits the caller actor into an Experience session and ensures
    one requested Experience-owned session feature. Consumers provide evidence;
    Experience owns the resulting admission and feature lease semantics.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "ensure_experience_session_handoff": "aware_experience_service_dto.experience.session_handoff.service_operation.EnsureExperienceSessionHandoffRequest",
        "get_experience_session_handoff_status": "aware_experience_service_dto.experience.session_handoff.service_operation.GetExperienceSessionHandoffStatusRequest",
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
            return UnknownExperienceSessionHandoffServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionHandoffServiceRequest(ExperienceSessionHandoffServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceSessionHandoffServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    receipt: ExperienceSessionHandoffReceipt | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "ensure_experience_session_handoff": "aware_experience_service_dto.experience.session_handoff.service_operation.EnsureExperienceSessionHandoffResponse",
        "get_experience_session_handoff_status": "aware_experience_service_dto.experience.session_handoff.service_operation.GetExperienceSessionHandoffStatusResponse",
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
            return UnknownExperienceSessionHandoffServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionHandoffServiceResponse(ExperienceSessionHandoffServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class EnsureExperienceSessionHandoffRequest(ExperienceSessionHandoffServiceRequest):
    # Discriminator Tag
    operation: Literal["ensure_experience_session_handoff"] = "ensure_experience_session_handoff"

    # Attributes
    session_scope: ExperienceSessionHandoffScope
    actor_context: ExperienceSessionHandoffActorContext | None = Field(default=None)
    environment_admission: EnvironmentActorAdmissionReceipt | None = Field(
        default=None,
        description="Environment actor admission evidence produced by Environment SDK/service.\nContract:\n- Required for runtime Experience session admission.\n- Must match session actor/environment scope.\n- Experience never admits a runtime actor from actor context alone.\n- Admission is not navigation: it carries no process/thread/branch/projection scope.",
    )
    environment_session_join: EnvironmentSessionJoinReceipt | None = Field(
        default=None,
        description="Environment session join evidence produced by Environment SDK/service.\nContract:\n- Required before Experience starts a child Identity Session.\n- Must carry EnvironmentSession Identity evidence.\n- Must match actor/environment scope and the Environment admission.",
    )
    experience_actor_admission: ExperienceActorConfigAdmissionReceipt | None = Field(
        default=None,
        description="Experience-specific ActorConfig admission evidence.\nContract:\n- Required before Experience records child-session actor-role evidence.\n- Environment membership is parent context, not Experience authorization.",
    )
    experience_identity_session_config_id: UUID | None = Field(
        default=None,
        description="Identity SessionConfig used for the child Experience Identity Session.\nContract:\n- Explicit caller/service-resolved input; no key-based inference.\n- Parent is the EnvironmentSession Identity Session from\n`environment_session_join.identity_evidence.identity_session`.",
    )
    feature: ExperienceSessionHandoffFeatureSpec
    idempotency_key: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class EnsureExperienceSessionHandoffResponse(ExperienceSessionHandoffServiceResponse):
    # Discriminator Tag
    operation: Literal["ensure_experience_session_handoff"] = "ensure_experience_session_handoff"

    # Attributes
    receipt: ExperienceSessionHandoffReceipt


class GetExperienceSessionHandoffStatusRequest(ExperienceSessionHandoffServiceRequest):
    # Discriminator Tag
    operation: Literal["get_experience_session_handoff_status"] = "get_experience_session_handoff_status"

    # Attributes
    session_scope: ExperienceSessionHandoffScope
    feature_key: str | None = Field(default=None)
    lease_key: str | None = Field(default=None)
    include_health: bool = Field(default=True)
    evidence: JsonObject = Field(default_factory=JsonObject)


class GetExperienceSessionHandoffStatusResponse(ExperienceSessionHandoffServiceResponse):
    # Discriminator Tag
    operation: Literal["get_experience_session_handoff_status"] = "get_experience_session_handoff_status"

    # Attributes
    receipt: ExperienceSessionHandoffStatusReceipt
