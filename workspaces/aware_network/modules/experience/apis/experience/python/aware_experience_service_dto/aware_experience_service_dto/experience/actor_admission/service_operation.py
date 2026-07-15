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
    from aware_experience_service_dto.experience.actor_admission.models import ExperienceActorConfigAdmissionReceipt


class ExperienceActorConfigAdmissionServiceRequest(BaseModel):
    """
    Service DTOs for Experience ActorConfig admission.
    The operation admits one actor under an Experience-owned ActorConfig and
    delegates concrete role materialization to Identity.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "admit_experience_actor_config": "aware_experience_service_dto.experience.actor_admission.service_operation.AdmitExperienceActorConfigRequest",
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
            return UnknownExperienceActorConfigAdmissionServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceActorConfigAdmissionServiceRequest(ExperienceActorConfigAdmissionServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceActorConfigAdmissionServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    accepted: bool = Field(default=False)
    status: str
    error: str | None = Field(default=None)
    receipt: ExperienceActorConfigAdmissionReceipt | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "admit_experience_actor_config": "aware_experience_service_dto.experience.actor_admission.service_operation.AdmitExperienceActorConfigResponse",
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
            return UnknownExperienceActorConfigAdmissionServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceActorConfigAdmissionServiceResponse(ExperienceActorConfigAdmissionServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class AdmitExperienceActorConfigRequest(ExperienceActorConfigAdmissionServiceRequest):
    # Discriminator Tag
    operation: Literal["admit_experience_actor_config"] = "admit_experience_actor_config"

    # Attributes
    experience_name: str
    actor_id: UUID
    actor_config_id: UUID
    class_instance_identity_id: UUID
    object_instance_graph_branch_key: str = Field(default="all")
    object_instance_graph_branch_id: UUID | None = Field(default=None)
    requested_role_config_ids: list[UUID] = Field(default_factory=list)
    requested_role_config_names: list[str] = Field(default_factory=list)
    reason: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)


class AdmitExperienceActorConfigResponse(ExperienceActorConfigAdmissionServiceResponse):
    # Discriminator Tag
    operation: Literal["admit_experience_actor_config"] = "admit_experience_actor_config"

    # Attributes
    receipt: ExperienceActorConfigAdmissionReceipt
