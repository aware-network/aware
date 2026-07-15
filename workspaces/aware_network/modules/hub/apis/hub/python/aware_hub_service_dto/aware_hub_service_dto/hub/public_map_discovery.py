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


class PublicMapDiscoveryRequest(BaseModel):
    """
    Hub public map discovery DTOs.
    Contract:
    - Hub owns public package/revision map discovery before identity admission.
    - Entries describe distribution/readiness truth only; they do not activate
    runtime, resolve Experience semantics, price access, or mutate Interface.
    - Initial service implementation may lower existing CodePackage authority
    entries into this shape while later Hub producers publish richer artifact
    families such as experience-package, workspace-revision, and kernel-revision.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "discover_public_map": "aware_hub_service_dto.hub.public_map_discovery.DiscoverPublicMapRequest",
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
            return UnknownPublicMapDiscoveryRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownPublicMapDiscoveryRequest(PublicMapDiscoveryRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class PublicMapDiscoveryResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "discover_public_map": "aware_hub_service_dto.hub.public_map_discovery.DiscoverPublicMapResponse",
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
            return UnknownPublicMapDiscoveryResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownPublicMapDiscoveryResponse(PublicMapDiscoveryResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class HubPublicMapEntry(BaseModel):
    # Attributes
    artifact_family: str
    artifact_key: str
    channel: str = Field(default="stable")
    revision_id: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    language: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    digest: str | None = Field(default=None)
    artifact_url: str | None = Field(default=None)
    artifact_sha256: str | None = Field(default=None)
    artifact_size_bytes: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    title: str | None = Field(default=None)
    summary: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    producer_kind: str | None = Field(default=None)
    producer_revision_id: str | None = Field(default=None)
    source_revision_id: str | None = Field(default=None)
    visibility: str = Field(default="public")
    metadata: JsonObject = Field(default_factory=JsonObject)


class DiscoverPublicMapRequest(PublicMapDiscoveryRequest):
    # Discriminator Tag
    operation: Literal["discover_public_map"] = "discover_public_map"

    # Attributes
    query: str | None = Field(default=None)
    artifact_family: str | None = Field(default=None)
    artifact_key: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    experience_name: str | None = Field(default=None)
    channel: str | None = Field(default=None)
    authority_base_url: str | None = Field(default=None)
    index_url: str | None = Field(default=None)
    limit: int = Field(default=50)


class DiscoverPublicMapResponse(PublicMapDiscoveryResponse):
    # Discriminator Tag
    operation: Literal["discover_public_map"] = "discover_public_map"

    # Attributes
    authority_source_url: str | None = Field(default=None)
    entries: list[HubPublicMapEntry] = Field(default_factory=list)
