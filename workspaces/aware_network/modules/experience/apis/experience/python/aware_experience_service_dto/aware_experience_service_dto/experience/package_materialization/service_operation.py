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
    from aware_experience_service_dto.experience.package_materialization.models import (
        ExperiencePackageProjectionOwnershipCatalog,
    )


class ExperiencePackageProjectionOwnershipServiceRequest(BaseModel):
    """
    Service DTOs for Experience package projection ownership operations.
    These operations are the public facade for package-level Experience projection
    ownership and materialization evidence. ServiceHost, Node, Interface, and
    Agent consumers should call this API/SDK surface instead of importing
    Experience runtime materialization internals.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    actor_id: UUID | None = Field(default=None)
    workspace_root: str | None = Field(default=None)
    experience_toml_path: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    request_context: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_package_projection_ownership": "aware_experience_service_dto.experience.package_materialization.service_operation.ResolveExperiencePackageProjectionOwnershipRequest",
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
            return UnknownExperiencePackageProjectionOwnershipServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownExperiencePackageProjectionOwnershipServiceRequest(ExperiencePackageProjectionOwnershipServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ExperiencePackageProjectionOwnershipServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    status: str
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    catalog: ExperiencePackageProjectionOwnershipCatalog | None = Field(default=None)
    evidence: JsonObject = Field(default_factory=JsonObject)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_experience_package_projection_ownership": "aware_experience_service_dto.experience.package_materialization.service_operation.ResolveExperiencePackageProjectionOwnershipResponse",
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
            return UnknownExperiencePackageProjectionOwnershipServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownExperiencePackageProjectionOwnershipServiceResponse(ExperiencePackageProjectionOwnershipServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ResolveExperiencePackageProjectionOwnershipRequest(ExperiencePackageProjectionOwnershipServiceRequest):
    # Discriminator Tag
    operation: Literal["resolve_experience_package_projection_ownership"] = (
        "resolve_experience_package_projection_ownership"
    )

    # Attributes
    validate_only: bool = Field(default=True)


class ResolveExperiencePackageProjectionOwnershipResponse(ExperiencePackageProjectionOwnershipServiceResponse):
    # Discriminator Tag
    operation: Literal["resolve_experience_package_projection_ownership"] = (
        "resolve_experience_package_projection_ownership"
    )

    # Attributes
    catalog: ExperiencePackageProjectionOwnershipCatalog
