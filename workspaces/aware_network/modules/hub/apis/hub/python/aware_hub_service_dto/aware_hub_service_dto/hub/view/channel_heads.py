from __future__ import annotations

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class HubPublicDiscoveryDescriptorV1(BaseModel):
    """
    View-state contract for public Hub package channel-head discovery.
    Public API view key: hub.channel_heads
    """

    # Attributes
    package_name: str | None = Field(default=None)
    language: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    manifest_kind: str | None = Field(default=None)
    version: str | None = Field(default=None)
    revision_id: str | None = Field(default=None)
    digest: str | None = Field(default=None)
    package_root: str | None = Field(default=None)
    sources_root: str | None = Field(default=None)
    fqn_prefix: str | None = Field(default=None)
    manifest_relative_path: str | None = Field(default=None)
    artifact_media_type: str | None = Field(default=None)
    artifact_size_bytes: int | None = Field(default=None)
    download_handle: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)


class HubPublicDiscoveryArtifactLockV1(BaseModel):
    # Attributes
    artifact_url: str | None = Field(default=None)
    sha256: str | None = Field(default=None)
    size_bytes: int | None = Field(default=None)
    media_type: str | None = Field(default=None)
    archive_format: str | None = Field(default=None)
    revision_id: str | None = Field(default=None)
    published_at: str | None = Field(default=None)


class HubPublicDiscoveryEntryV1(BaseModel):
    # Attributes
    package_name: str | None = Field(default=None)
    language: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    channel: str = Field(default="stable")
    revision_id: str | None = Field(default=None)
    updated_at: str | None = Field(default=None)
    publisher_execution_id: str | None = Field(default=None)
    idempotency_key: str | None = Field(default=None)
    metadata: JsonObject = Field(default_factory=JsonObject)
    descriptor: HubPublicDiscoveryDescriptorV1 | None = Field(default=None)
    artifact_lock: HubPublicDiscoveryArtifactLockV1 | None = Field(default=None)
    refs: JsonObject = Field(default_factory=JsonObject)


class HubPublicDiscoveryViewStateV1(BaseModel):
    # Attributes
    status: str = Field(default="waiting")
    authority_source_url: str | None = Field(default=None)
    query: str | None = Field(default=None)
    package_name: str | None = Field(default=None)
    language: str | None = Field(default=None)
    surface: str | None = Field(default=None)
    channel: str | None = Field(default=None)
    limit: int = Field(default=50)
    entries: list[HubPublicDiscoveryEntryV1] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    empty_message: str = Field(default="No public Hub packages published yet")
    error: str | None = Field(default=None)
    provenance: JsonObject = Field(default_factory=JsonObject)
