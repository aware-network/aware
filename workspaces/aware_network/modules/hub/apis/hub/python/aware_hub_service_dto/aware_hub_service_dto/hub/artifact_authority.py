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


class HubArtifactAuthorityRequest(BaseModel):
    """
    Hub-owned generic artifact authority DTOs.
    Contract:
    - Hub owns artifact family/key/channel/revision authority.
    - Producers may provide payload bytes, payload JSON, a staged payload URL, or
    a pre-published payload lock.
    - Producer provenance remains descriptive; Hub artifact revisions own the
    immutable payload lock and channel head.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "publish_hub_artifact": "aware_hub_service_dto.hub.artifact_authority.PublishHubArtifactRequest",
        "resolve_hub_artifact": "aware_hub_service_dto.hub.artifact_authority.ResolveHubArtifactRequest",
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
            return UnknownHubArtifactAuthorityRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownHubArtifactAuthorityRequest(HubArtifactAuthorityRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class HubArtifactAuthorityResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "publish_hub_artifact": "aware_hub_service_dto.hub.artifact_authority.PublishHubArtifactResponse",
        "resolve_hub_artifact": "aware_hub_service_dto.hub.artifact_authority.ResolveHubArtifactResponse",
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
            return UnknownHubArtifactAuthorityResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownHubArtifactAuthorityResponse(HubArtifactAuthorityResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class HubArtifactProducerProvenance(BaseModel):
    # Attributes
    producer_kind: str = Field(default="unknown")
    producer_key: str = Field(default="default")
    provenance_key: str | None = Field(default=None)
    producer_revision_id: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    source_revision_kind: str | None = Field(default=None)
    materialization_ref: str | None = Field(default=None)
    build_ref: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubArtifactPayloadLock(BaseModel):
    # Attributes
    artifact_family: str
    artifact_key: str
    channel: str = Field(default="stable")
    revision_id: str
    payload_url: str
    payload_sha256: str
    payload_size_bytes: int | None = Field(default=None)
    payload_media_type: str | None = Field(default=None)
    payload_contract: str | None = Field(default=None)
    authority_source_url: str | None = Field(default=None)
    selector_key: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class PublishHubArtifactRequest(HubArtifactAuthorityRequest):
    # Discriminator Tag
    operation: Literal["publish_hub_artifact"] = "publish_hub_artifact"

    # Attributes
    artifact_family: str
    artifact_key: str
    revision_id: str
    channel: str = Field(default="stable")
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)
    payload_url: str | None = Field(default=None)
    payload_sha256: str | None = Field(default=None)
    payload_size_bytes: int | None = Field(default=None)
    payload_media_type: str | None = Field(default=None)
    payload_contract: str | None = Field(default=None)
    payload_json: JsonObject | None = Field(default=None)
    payload_bytes_base64: str | None = Field(default=None)
    payload_source_url: str | None = Field(default=None)
    selector_key: str | None = Field(default=None)
    target_ref: str | None = Field(default=None)
    producer: HubArtifactProducerProvenance | None = Field(default=None)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    published_at_utc: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class PublishHubArtifactResponse(HubArtifactAuthorityResponse):
    # Discriminator Tag
    operation: Literal["publish_hub_artifact"] = "publish_hub_artifact"

    # Attributes
    accepted: bool = Field(default=False)
    authority_source_url: str
    artifact_lock: HubArtifactPayloadLock
    producer: HubArtifactProducerProvenance | None = Field(default=None)


class ResolveHubArtifactRequest(HubArtifactAuthorityRequest):
    # Discriminator Tag
    operation: Literal["resolve_hub_artifact"] = "resolve_hub_artifact"

    # Attributes
    artifact_family: str
    artifact_key: str
    channel: str = Field(default="stable")
    revision_id: str | None = Field(default=None)
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)


class ResolveHubArtifactResponse(HubArtifactAuthorityResponse):
    # Discriminator Tag
    operation: Literal["resolve_hub_artifact"] = "resolve_hub_artifact"

    # Attributes
    authority_source_url: str
    artifact_lock: HubArtifactPayloadLock
    producer: HubArtifactProducerProvenance | None = Field(default=None)
