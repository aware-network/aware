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


class DeploymentArtifactAuthorityRequest(BaseModel):
    """
    Hub-owned deployment artifact authority DTOs.
    Contract:
    - Hub owns the public deployment authority request/response model.
    - Producers such as Workspace map their revision truth into generic
    producer provenance.
    - Hub resolves deployment artifact payload locks; it does not resolve
    WorkspaceRevision semantics.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_deployment_artifact": "aware_hub_service_dto.hub.deployment_artifact_authority.ResolveDeploymentArtifactRequest",
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
            return UnknownDeploymentArtifactAuthorityRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownDeploymentArtifactAuthorityRequest(DeploymentArtifactAuthorityRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class DeploymentArtifactAuthorityResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "resolve_deployment_artifact": "aware_hub_service_dto.hub.deployment_artifact_authority.ResolveDeploymentArtifactResponse",
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
            return UnknownDeploymentArtifactAuthorityResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownDeploymentArtifactAuthorityResponse(DeploymentArtifactAuthorityResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class DeploymentArtifactProducerProvenance(BaseModel):
    # Attributes
    producer_kind: str
    producer_revision_id: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    source_revision_kind: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    build_ref: str | None = Field(default=None)


class DeploymentArtifactLock(BaseModel):
    # Attributes
    artifact_family: str = Field(default="workspace-deployment")
    artifact_key: str
    channel: str = Field(default="stable")
    revision_id: str
    payload_url: str
    payload_sha256: str
    payload_contract_version: str = Field(default="aware.workspace_deployment.payload.v1")


class DeploymentArtifactTarget(BaseModel):
    # Attributes
    selector_key: str
    target_ref: str
    node_package_name: str


class ResolveDeploymentArtifactRequest(DeploymentArtifactAuthorityRequest):
    # Discriminator Tag
    operation: Literal["resolve_deployment_artifact"] = "resolve_deployment_artifact"

    # Attributes
    artifact_family: str = Field(default="workspace-deployment")
    artifact_key: str | None = Field(default=None)
    channel: str = Field(default="stable")
    revision_id: str | None = Field(default=None)
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)


class ResolveDeploymentArtifactResponse(DeploymentArtifactAuthorityResponse):
    # Discriminator Tag
    operation: Literal["resolve_deployment_artifact"] = "resolve_deployment_artifact"

    # Attributes
    authority_source_url: str
    artifact_family: str
    artifact_key: str
    channel: str
    revision_id: str
    payload_url: str
    payload_sha256: str
    selector_key: str
    target_ref: str
    producer: DeploymentArtifactProducerProvenance
    node_package_name: str
    artifact_lock: DeploymentArtifactLock
    target: DeploymentArtifactTarget
