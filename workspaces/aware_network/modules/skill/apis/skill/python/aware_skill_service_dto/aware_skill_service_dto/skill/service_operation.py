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


class SkillServiceRequest(BaseModel):
    """
    Skill service operation DTOs (transport-only).
    Contract:
    - Exposes Skill invocation through the canonical API-Service boundary.
    - Carries clean committed SkillPackage and ApiPackage refs only.
    - Keeps actor-provided step payloads at the API-call boundary; Skill owns routing receipts.
    Note:
    - These DTOs are not SSOT execution state.
    - Canonical truth remains SkillConfig, SkillRun, SkillRunStep, ApiCall, and committed package refs.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "invoke": "aware_skill_service_dto.skill.service_operation.SkillInvokeRequest",
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
            return UnknownSkillServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownSkillServiceRequest(SkillServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class SkillServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "invoke": "aware_skill_service_dto.skill.service_operation.SkillInvokeResponse",
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
            return UnknownSkillServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownSkillServiceResponse(SkillServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class SkillPackageRef(BaseModel):
    # Attributes
    family_key: str = Field(default="skill")
    package_kind: str = Field(default="skill")
    package_name: str
    semantic_package_id: UUID | None = Field(default=None)
    semantic_object_instance_graph_commit_id: UUID
    semantic_branch_id: UUID | None = Field(default=None)
    semantic_root_kind: str | None = Field(default=None)
    semantic_root_id: UUID | None = Field(default=None)
    semantic_root_object_instance_graph_commit_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)


class SkillApiPackageRef(BaseModel):
    # Attributes
    family_key: str = Field(default="api")
    package_kind: str = Field(default="api")
    package_name: str
    semantic_package_id: UUID | None = Field(default=None)
    semantic_object_instance_graph_commit_id: UUID
    semantic_branch_id: UUID | None = Field(default=None)
    semantic_projection_name: str | None = Field(default=None)
    semantic_root_kind: str | None = Field(default=None)
    semantic_root_id: UUID | None = Field(default=None)
    source_code_package_id: UUID | None = Field(default=None)


class SkillStepApiCallInput(BaseModel):
    # Attributes
    skill_config_step_id: UUID
    request_payload: JsonObject = Field(default_factory=JsonObject)
    call_key: UUID | None = Field(default=None)
    description: str | None = Field(default=None)


class SkillInvokeRequest(SkillServiceRequest):
    # Discriminator Tag
    operation: Literal["invoke"] = "invoke"

    # Attributes
    skill_package: SkillPackageRef
    api_packages: list[SkillApiPackageRef] = Field(default_factory=list)
    skill_config_id: UUID
    run_key: str
    step_inputs: list[SkillStepApiCallInput] = Field(default_factory=list)
    run_status: str = Field(default="succeeded")
    step_status: str = Field(default="succeeded")
    description: str | None = Field(default=None)
    commit: bool = Field(default=True)
    publish: bool = Field(default=False)


class SkillApiCallReceipt(BaseModel):
    # Attributes
    skill_config_step_id: UUID
    api_call_id: UUID
    api_capability_endpoint_id: UUID
    call_key: UUID
    request_hash: str
    request_model_id: UUID
    request_class_config_id: UUID
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    head_commit_id: UUID


class SkillRunStepReceipt(BaseModel):
    # Attributes
    skill_config_step_id: UUID
    skill_run_step_id: UUID
    api_call: SkillApiCallReceipt
    status: str


class SkillInvokeResult(BaseModel):
    # Attributes
    skill_config_id: UUID
    skill_run_id: UUID
    run_key: str
    status: str
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    head_commit_id: UUID
    steps: list[SkillRunStepReceipt] = Field(default_factory=list)


class SkillInvokeResponse(SkillServiceResponse):
    # Discriminator Tag
    operation: Literal["invoke"] = "invoke"

    # Attributes
    result: SkillInvokeResult | None = Field(default=None)
