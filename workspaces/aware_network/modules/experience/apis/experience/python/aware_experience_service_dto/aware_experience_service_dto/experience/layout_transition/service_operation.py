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

if TYPE_CHECKING:
    from aware_experience_service_dto.experience.layout_transition.models import ExperienceInterfaceWindowLayoutTarget
    from aware_experience_service_dto.experience.layout_transition.models import ExperienceLayoutActorRoleGate
    from aware_experience_service_dto.experience.layout_transition.models import ExperienceLayoutTransitionReceipt


class ExperienceLayoutTransitionServiceRequest(BaseModel):
    """
    Canonical request/response DTOs for Experience-mediated layout transitions.
    Product services request layout intent here. Experience resolves target semantics,
    activates Attention section/focus/observable state, and Interface applies protected
    window mutation through its own API/SDK boundary.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "request_experience_layout_transition": "aware_experience_service_dto.experience.layout_transition.service_operation.RequestExperienceLayoutTransitionRequest",
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
            return UnknownExperienceLayoutTransitionServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceLayoutTransitionServiceRequest(ExperienceLayoutTransitionServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceLayoutTransitionServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    receipt: ExperienceLayoutTransitionReceipt | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "request_experience_layout_transition": "aware_experience_service_dto.experience.layout_transition.service_operation.RequestExperienceLayoutTransitionResponse",
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
            return UnknownExperienceLayoutTransitionServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceLayoutTransitionServiceResponse(ExperienceLayoutTransitionServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class RequestExperienceLayoutTransitionRequest(ExperienceLayoutTransitionServiceRequest):
    # Discriminator Tag
    operation: Literal["request_experience_layout_transition"] = "request_experience_layout_transition"

    # Attributes
    namespace: str
    actor_id: UUID
    identity_id: UUID | None = Field(default=None)
    experience_name: str = Field(default="aware_control_identity")
    intent_key: str = Field(default="identity.admission")
    target: ExperienceInterfaceWindowLayoutTarget | None = Field(default=None)
    role_gate: ExperienceLayoutActorRoleGate
    reason: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)


class RequestExperienceLayoutTransitionResponse(ExperienceLayoutTransitionServiceResponse):
    # Discriminator Tag
    operation: Literal["request_experience_layout_transition"] = "request_experience_layout_transition"

    # Attributes
    receipt: ExperienceLayoutTransitionReceipt
