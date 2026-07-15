from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True, slots=True)
class HubCodePackageSelector:
    package_name: str
    language: str | None = None
    surface: str | None = None
    channel: str = "stable"
    version: str | None = None
    revision_id: str | None = None
    digest: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackageDescriptor:
    package_name: str
    language: str
    surface: str
    manifest_kind: str
    manifest_relative_path: str
    package_root: str
    sources_root: str | None = None
    fqn_prefix: str | None = None
    version: str | None = None
    revision_id: str | None = None
    digest: str | None = None
    artifact_media_type: str | None = None
    artifact_size_bytes: int | None = None
    download_handle: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HubCodePackageArtifactLock:
    artifact_url: str
    sha256: str
    size_bytes: int | None = None
    media_type: str | None = None
    archive_format: str | None = None
    revision_id: str | None = None
    published_at: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackageChannelHead:
    package_name: str
    revision_id: str
    language: str | None = None
    surface: str | None = None
    channel: str = "stable"
    updated_at: str | None = None
    publisher_execution_id: str | None = None
    idempotency_key: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HubCodePackageDiscoveryEntry:
    channel_head: HubCodePackageChannelHead
    descriptor: HubCodePackageDescriptor | None = None
    artifact_lock: HubCodePackageArtifactLock | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackageDiscoveryReceipt:
    entries: tuple[HubCodePackageDiscoveryEntry, ...]
    authority_source_url: str | None = None
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackageSearchReceipt:
    descriptors: tuple[HubCodePackageDescriptor, ...]
    authority_source_url: str | None = None
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackageDescribeReceipt:
    descriptor: HubCodePackageDescriptor
    authority_source_url: str | None = None
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackageResolveReceipt:
    selector: HubCodePackageSelector
    descriptor: HubCodePackageDescriptor
    artifact_lock: HubCodePackageArtifactLock
    authority_source_url: str | None = None
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackageDownloadReceipt:
    selector: HubCodePackageSelector
    artifact_lock: HubCodePackageArtifactLock
    authority_source_url: str | None = None
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackagePublishReceipt:
    selector: HubCodePackageSelector
    descriptor: HubCodePackageDescriptor
    artifact_lock: HubCodePackageArtifactLock
    authority_source_url: str | None = None
    accepted: bool = False
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubCodePackagePublicationEntry:
    descriptor: HubCodePackageDescriptor
    artifact_lock: HubCodePackageArtifactLock
    channel: str = "stable"
    updated_at: str | None = None


@dataclass(frozen=True, slots=True)
class HubArtifactProducerProvenance:
    producer_kind: str = "unknown"
    producer_key: str = "default"
    provenance_key: str | None = None
    producer_revision_id: str | None = None
    source_revision_id: str | None = None
    source_revision_kind: str | None = None
    materialization_ref: str | None = None
    build_ref: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HubArtifactPayloadLock:
    artifact_family: str
    artifact_key: str
    channel: str
    revision_id: str
    payload_url: str
    payload_sha256: str
    payload_size_bytes: int | None = None
    payload_media_type: str | None = None
    payload_contract: str | None = None
    authority_source_url: str | None = None
    selector_key: str | None = None
    target_ref: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HubArtifactPublishReceipt:
    artifact_lock: HubArtifactPayloadLock
    authority_source_url: str
    producer: HubArtifactProducerProvenance | None = None
    accepted: bool = False
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubArtifactResolveReceipt:
    artifact_lock: HubArtifactPayloadLock
    authority_source_url: str
    producer: HubArtifactProducerProvenance | None = None
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubArtifactJsonResolveReceipt:
    artifact_lock: HubArtifactPayloadLock
    payload: Mapping[str, object]
    authority_source_url: str
    producer: HubArtifactProducerProvenance | None = None
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubDeploymentArtifactProducerProvenance:
    producer_kind: str
    producer_revision_id: str | None = None
    source_revision_id: str | None = None
    source_revision_kind: str | None = None
    materialization_ref: str | None = None
    build_ref: str | None = None


@dataclass(frozen=True, slots=True)
class HubDeploymentArtifactLock:
    artifact_family: str
    artifact_key: str
    channel: str
    revision_id: str
    payload_url: str
    payload_sha256: str
    payload_contract_version: str = "aware.workspace_deployment.payload.v1"


@dataclass(frozen=True, slots=True)
class HubDeploymentArtifactTarget:
    selector_key: str
    target_ref: str
    node_package_name: str


@dataclass(frozen=True, slots=True)
class HubDeploymentArtifactResolveReceipt:
    artifact_lock: HubDeploymentArtifactLock
    target: HubDeploymentArtifactTarget
    producer: HubDeploymentArtifactProducerProvenance
    authority_source_url: str
    request_id: UUID | None = None
    info: str | None = None


@dataclass(frozen=True, slots=True)
class HubPublicMapEntry:
    artifact_family: str
    artifact_key: str
    channel: str = "stable"
    revision_id: str | None = None
    package_name: str | None = None
    language: str | None = None
    surface: str | None = None
    manifest_kind: str | None = None
    digest: str | None = None
    artifact_url: str | None = None
    artifact_sha256: str | None = None
    artifact_size_bytes: int | None = None
    media_type: str | None = None
    title: str | None = None
    summary: str | None = None
    experience_name: str | None = None
    fqn_prefix: str | None = None
    producer_kind: str | None = None
    producer_revision_id: str | None = None
    source_revision_id: str | None = None
    visibility: str = "public"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HubPublicMapDiscoveryReceipt:
    entries: tuple[HubPublicMapEntry, ...]
    authority_source_url: str | None = None
    request_id: UUID | None = None
    info: str | None = None


__all__ = [
    "HubArtifactPayloadLock",
    "HubArtifactJsonResolveReceipt",
    "HubArtifactProducerProvenance",
    "HubArtifactPublishReceipt",
    "HubArtifactResolveReceipt",
    "HubCodePackageArtifactLock",
    "HubCodePackageChannelHead",
    "HubCodePackageDescribeReceipt",
    "HubCodePackageDescriptor",
    "HubCodePackageDiscoveryEntry",
    "HubCodePackageDiscoveryReceipt",
    "HubCodePackageDownloadReceipt",
    "HubCodePackagePublishReceipt",
    "HubCodePackagePublicationEntry",
    "HubCodePackageResolveReceipt",
    "HubCodePackageSearchReceipt",
    "HubCodePackageSelector",
    "HubDeploymentArtifactLock",
    "HubDeploymentArtifactProducerProvenance",
    "HubDeploymentArtifactResolveReceipt",
    "HubDeploymentArtifactTarget",
    "HubPublicMapDiscoveryReceipt",
    "HubPublicMapEntry",
]
