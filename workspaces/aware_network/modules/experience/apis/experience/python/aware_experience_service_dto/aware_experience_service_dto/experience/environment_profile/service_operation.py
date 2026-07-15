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
    from aware_experience_service_dto.experience.environment_profile.models import (
        ExperienceEnvironmentProfileProgramApplyReceipt,
    )
    from aware_experience_service_dto.experience.environment_profile.models import (
        ExperienceEnvironmentProfileRuntimeMountReceipt,
    )
    from aware_experience_service_dto.experience.environment_profile.models import ExperienceEnvironmentProfileSpec
    from aware_experience_service_dto.experience.environment_profile.models import (
        ExperienceEnvironmentProfileTopologySeedSpec,
    )


class ExperienceEnvironmentProfileServiceRequest(BaseModel):
    """
    Service DTOs for Experience-owned EnvironmentExperience profile operations.
    These operations are the target facade for Environment compatibility
    proxies. Environment callers should not import Experience runtime
    materialization internals directly.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    environment_id: UUID
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    request_context: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "upsert_experience_environment_profile": "aware_experience_service_dto.experience.environment_profile.service_operation.UpsertExperienceEnvironmentProfileRequest",
        "provision_experience_environment_profile": "aware_experience_service_dto.experience.environment_profile.service_operation.ProvisionExperienceEnvironmentProfileRequest",
        "apply_experience_environment_profile_programs": "aware_experience_service_dto.experience.environment_profile.service_operation.ApplyExperienceEnvironmentProfileProgramsRequest",
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
            return UnknownExperienceEnvironmentProfileServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceEnvironmentProfileServiceRequest(ExperienceEnvironmentProfileServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperienceEnvironmentProfileServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    status: str
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    environment_id: UUID | None = Field(default=None)
    process_id: UUID | None = Field(default=None)
    thread_id: UUID | None = Field(default=None)
    branch_id: UUID | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    environment_experience_profile_id: UUID | None = Field(default=None)
    profile_key: str | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "upsert_experience_environment_profile": "aware_experience_service_dto.experience.environment_profile.service_operation.UpsertExperienceEnvironmentProfileResponse",
        "provision_experience_environment_profile": "aware_experience_service_dto.experience.environment_profile.service_operation.ProvisionExperienceEnvironmentProfileResponse",
        "apply_experience_environment_profile_programs": "aware_experience_service_dto.experience.environment_profile.service_operation.ApplyExperienceEnvironmentProfileProgramsResponse",
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
            return UnknownExperienceEnvironmentProfileServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperienceEnvironmentProfileServiceResponse(ExperienceEnvironmentProfileServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class UpsertExperienceEnvironmentProfileRequest(ExperienceEnvironmentProfileServiceRequest):
    # Discriminator Tag
    operation: Literal["upsert_experience_environment_profile"] = "upsert_experience_environment_profile"

    # Attributes
    profile: ExperienceEnvironmentProfileSpec = Field(
        description="Declarative profile to resolve and commit into Experience-owned profile truth."
    )
    topology_seeds: list[ExperienceEnvironmentProfileTopologySeedSpec] = Field(
        default_factory=list, description="Named runtime topology seeds to bind beside the reusable profile config."
    )
    validate_only: bool = Field(default=False, description="Validate and plan without committing runtime state.")


class UpsertExperienceEnvironmentProfileResponse(ExperienceEnvironmentProfileServiceResponse):
    # Discriminator Tag
    operation: Literal["upsert_experience_environment_profile"] = "upsert_experience_environment_profile"

    # Attributes
    process_config_ids: list[UUID] = Field(default_factory=list)
    thread_config_ids: list[UUID] = Field(default_factory=list)
    thread_projection_association_ids: list[UUID] = Field(default_factory=list)
    thread_layout_config_ids: list[UUID] = Field(default_factory=list)
    topology_seed_ids: list[UUID] = Field(default_factory=list)
    topology_process_seed_ids: list[UUID] = Field(default_factory=list)
    topology_thread_seed_ids: list[UUID] = Field(default_factory=list)
    topology_thread_layout_seed_ids: list[UUID] = Field(default_factory=list)


class ProvisionExperienceEnvironmentProfileRequest(ExperienceEnvironmentProfileServiceRequest):
    # Discriminator Tag
    operation: Literal["provision_experience_environment_profile"] = "provision_experience_environment_profile"

    # Attributes
    environment_experience_profile_id: UUID | None = Field(
        default=None,
        description="Optional explicit profile override. When omitted, Experience resolves from active environment profile truth.",
    )
    profile_key: str | None = Field(
        default=None, description="Optional profile key selector for Experience-owned profile resolution."
    )
    topology_seed_key: str = Field(
        description="Named topology seed to lower into runtime Process/Thread/ThreadLayout territory."
    )
    validate_only: bool = Field(default=False, description="Validate and plan without committing runtime state.")


class ProvisionExperienceEnvironmentProfileResponse(ExperienceEnvironmentProfileServiceResponse):
    # Discriminator Tag
    operation: Literal["provision_experience_environment_profile"] = "provision_experience_environment_profile"

    # Attributes
    runtime_mounts: list[ExperienceEnvironmentProfileRuntimeMountReceipt] = Field(default_factory=list)
    process_ids: list[UUID] = Field(default_factory=list)
    thread_ids: list[UUID] = Field(default_factory=list)
    thread_layout_ids: list[UUID] = Field(default_factory=list)


class ApplyExperienceEnvironmentProfileProgramsRequest(ExperienceEnvironmentProfileServiceRequest):
    # Discriminator Tag
    operation: Literal["apply_experience_environment_profile_programs"] = (
        "apply_experience_environment_profile_programs"
    )

    # Attributes
    environment_experience_profile_id: UUID | None = Field(
        default=None,
        description="Experience-owned Program/Turn run boundary.\nContract:\n- Environment contributes topology ids (`environment_id`, `thread_id`) only.\n- Experience owns Program, ProgramTurn, Turn, and ThreadProgram run truth.\n- The service must not route this through legacy RuntimeHarness/libs/runtime rails.",
    )
    profile_key: str | None = Field(default=None)
    phase: str = Field(default="bootstrap")
    target_actor_id: UUID | None = Field(default=None)
    validate_only: bool = Field(default=False)


class ApplyExperienceEnvironmentProfileProgramsResponse(ExperienceEnvironmentProfileServiceResponse):
    # Discriminator Tag
    operation: Literal["apply_experience_environment_profile_programs"] = (
        "apply_experience_environment_profile_programs"
    )

    # Attributes
    phase: str = Field(
        default="bootstrap", description="Execution phase resolved by the Experience-owned Program run boundary."
    )
    target_actor_id: UUID | None = Field(default=None)
    receipts: list[ExperienceEnvironmentProfileProgramApplyReceipt] = Field(
        default_factory=list, description="Receipts describe Experience-owned Program/Turn run effects."
    )
