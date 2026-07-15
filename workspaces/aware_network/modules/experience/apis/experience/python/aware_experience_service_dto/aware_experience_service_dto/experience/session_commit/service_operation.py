from __future__ import annotations

# Standard
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
)

# Types
from aware_types import JsonObject


class ExperienceSessionOperationRequest(BaseModel):
    """
    Commit-producing Experience session command DTOs.
    Session authority and profile participation are separate projection roots.
    These transport contracts deliberately carry no global profile, lens, or
    ProjectionExperience activation semantics.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "start_experience_session": "aware_experience_service_dto.experience.session_commit.service_operation.StartExperienceSessionRequest",
        "describe_experience_session": "aware_experience_service_dto.experience.session_commit.service_operation.DescribeExperienceSessionRequest",
        "mount_experience_session_profile": "aware_experience_service_dto.experience.session_commit.service_operation.MountExperienceSessionProfileRequest",
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
            return UnknownExperienceSessionOperationRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionOperationRequest(ExperienceSessionOperationRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceSessionOperationResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    domain_commit_id: UUID | None = Field(default=None)
    object_instance_graph_commit_id: UUID | None = Field(default=None)
    graph_hash_post: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "start_experience_session": "aware_experience_service_dto.experience.session_commit.service_operation.StartExperienceSessionResponse",
        "describe_experience_session": "aware_experience_service_dto.experience.session_commit.service_operation.DescribeExperienceSessionResponse",
        "mount_experience_session_profile": "aware_experience_service_dto.experience.session_commit.service_operation.MountExperienceSessionProfileResponse",
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
            return UnknownExperienceSessionOperationResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceSessionOperationResponse(ExperienceSessionOperationResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class StartExperienceSessionRequest(ExperienceSessionOperationRequest):
    # Discriminator Tag
    operation: Literal["start_experience_session"] = "start_experience_session"

    # Attributes
    environment_experience_id: UUID
    environment_id: UUID
    identity_session_id: UUID
    environment_session_id: UUID
    state: str = Field(default="active")


class StartExperienceSessionResponse(ExperienceSessionOperationResponse):
    # Discriminator Tag
    operation: Literal["start_experience_session"] = "start_experience_session"

    # Attributes
    experience_session_id: UUID
    environment_experience_id: UUID
    environment_id: UUID
    identity_session_id: UUID
    environment_session_id: UUID
    state: str


class DescribeExperienceSessionRequest(ExperienceSessionOperationRequest):
    # Discriminator Tag
    operation: Literal["describe_experience_session"] = "describe_experience_session"

    # Attributes
    experience_session_id: UUID


class ExperienceSessionView(BaseModel):
    # Attributes
    experience_session_id: UUID
    environment_experience_id: UUID
    identity_session_id: UUID
    environment_session_id: UUID
    state: str
    domain_commit_id: UUID


class DescribeExperienceSessionResponse(ExperienceSessionOperationResponse):
    # Discriminator Tag
    operation: Literal["describe_experience_session"] = "describe_experience_session"

    # Attributes
    status: str
    session: ExperienceSessionView | None = Field(default=None)


class MountExperienceSessionProfileRequest(ExperienceSessionOperationRequest):
    # Discriminator Tag
    operation: Literal["mount_experience_session_profile"] = "mount_experience_session_profile"

    # Attributes
    experience_session_id: UUID
    profile_id: UUID
    status: str = Field(default="active")
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)


class MountExperienceSessionProfileResponse(ExperienceSessionOperationResponse):
    # Discriminator Tag
    operation: Literal["mount_experience_session_profile"] = "mount_experience_session_profile"

    # Attributes
    experience_session_profile_id: UUID
    experience_session_id: UUID
    profile_id: UUID
    status: str
    metadata_json: JsonObject | None = Field(default_factory=JsonObject)
