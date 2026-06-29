from __future__ import annotations

# Standard
from enum import Enum
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject


class FileSystemEntryKind(Enum):
    """
    FileSystem API DTOs for local observation, delta exchange, and apply receipts.
    Contract:
    - These DTOs are transport payloads, not filesystem ontology/state entities.
    - FileSystem owns path safety, stable relative paths, metadata, hashes, and
    backend execution receipts.
    - Workspace, Issue, and other consumers own semantic meaning above these
    paths. FileSystem must not infer package/source ownership.
    - Python may route the protocol while Rust or another native backend performs
    hot filesystem work behind this contract.
    """

    file = "file"
    directory = "directory"
    symlink = "symlink"
    other = "other"
    missing = "missing"


class FileSystemDeltaOperation(Enum):
    create = "create"
    update = "update"
    delete = "delete"


class FileSystemFilterProfile(Enum):
    canonical_source = "canonical_source"
    all_user_source = "all_user_source"
    artifact_output = "artifact_output"
    no_filter = "no_filter"


class FileSystemDigestAlgorithm(Enum):
    sha256 = "sha256"


class FileSystemBackendKind(Enum):
    python = "python"
    rust = "rust"
    service = "service"
    unknown = "unknown"


class FileSystemPathSafetyMode(Enum):
    root_relative = "root_relative"
    no_follow_verified = "no_follow_verified"
    unsupported = "unsupported"


class FileSystemRootRef(BaseModel):
    # Attributes
    root_path: str
    root_id: str | None = Field(default=None)
    workspace_id: UUID | None = Field(default=None)
    workspace_revision_id: UUID | None = Field(default=None)
    checkout_id: str | None = Field(default=None)
    display_name: str | None = Field(default=None)


class FileSystemRelativePath(BaseModel):
    # Attributes
    relative_path: str


class FileSystemContentDigest(BaseModel):
    # Attributes
    algorithm: FileSystemDigestAlgorithm = Field(default=FileSystemDigestAlgorithm.sha256)
    hex: str
    byte_length: int | None = Field(default=None)


class FileSystemEntryMetadata(BaseModel):
    # Attributes
    kind: FileSystemEntryKind
    size_bytes: int | None = Field(default=None)
    modified_time_ns: int | None = Field(default=None)
    mode: str | None = Field(default=None)
    executable: bool = Field(default=False)
    symlink_target: str | None = Field(default=None)


class FileSystemEntrySnapshot(BaseModel):
    # Attributes
    path: FileSystemRelativePath
    metadata: FileSystemEntryMetadata
    digest: FileSystemContentDigest | None = Field(default=None)


class FileSystemScanStats(BaseModel):
    # Attributes
    scanned_entry_count: int = Field(default=0)
    file_count: int = Field(default=0)
    directory_count: int = Field(default=0)
    symlink_count: int = Field(default=0)
    content_read_count: int = Field(default=0)
    cache_hit_count: int = Field(default=0)
    cache_miss_count: int = Field(default=0)
    changed_directory_count: int = Field(default=0)
    duration_s: float | None = Field(default=None)


class FileSystemBackendReceipt(BaseModel):
    # Attributes
    backend_kind: FileSystemBackendKind = Field(default=FileSystemBackendKind.unknown)
    backend_name: str | None = Field(default=None)
    backend_version: str | None = Field(default=None)
    implementation_language: str | None = Field(default=None)
    native_accelerated: bool = Field(default=False)
    platform: str | None = Field(default=None)
    receipt_path: str | None = Field(default=None)
    timings: JsonObject = Field(default_factory=JsonObject)
    metadata: JsonObject = Field(default_factory=JsonObject)


class FileSystemSnapshot(BaseModel):
    # Attributes
    root: FileSystemRootRef
    filter_profile: FileSystemFilterProfile = Field(default=FileSystemFilterProfile.canonical_source)
    entries: list[FileSystemEntrySnapshot] = Field(default_factory=list)
    stats: FileSystemScanStats | None = Field(default=None)
    backend_receipt: FileSystemBackendReceipt | None = Field(default=None)


class FileSystemDeltaEntry(BaseModel):
    # Attributes
    operation: FileSystemDeltaOperation
    path: FileSystemRelativePath
    before_metadata: FileSystemEntryMetadata | None = Field(default=None)
    after_metadata: FileSystemEntryMetadata | None = Field(default=None)
    before_digest: FileSystemContentDigest | None = Field(default=None)
    after_digest: FileSystemContentDigest | None = Field(default=None)
    content_text: str | None = Field(default=None)
    content_ref: str | None = Field(default=None)


class FileSystemDeltaTotals(BaseModel):
    # Attributes
    create_count: int = Field(default=0)
    update_count: int = Field(default=0)
    delete_count: int = Field(default=0)
    byte_count: int = Field(default=0)
    digest_count: int = Field(default=0)


class FileSystemDeltaSet(BaseModel):
    # Attributes
    root: FileSystemRootRef
    base_revision_id: str | None = Field(default=None)
    target_revision_id: str | None = Field(default=None)
    filter_profile: FileSystemFilterProfile = Field(default=FileSystemFilterProfile.canonical_source)
    entries: list[FileSystemDeltaEntry] = Field(default_factory=list)
    totals: FileSystemDeltaTotals | None = Field(default=None)
    backend_receipt: FileSystemBackendReceipt | None = Field(default=None)


class FileSystemArtifactReceipt(BaseModel):
    # Attributes
    artifact_ref: str
    relative_path: FileSystemRelativePath | None = Field(default=None)
    digest: FileSystemContentDigest | None = Field(default=None)
    media_type: str | None = Field(default=None)
    byte_length: int | None = Field(default=None)
    stored: bool = Field(default=False)


class FileSystemApplyPolicy(BaseModel):
    # Attributes
    verify_digests: bool = Field(default=True)
    reject_path_escape: bool = Field(default=True)
    allow_delete_missing: bool = Field(default=True)
    store_artifacts: bool = Field(default=False)
    path_safety_mode: FileSystemPathSafetyMode = Field(default=FileSystemPathSafetyMode.root_relative)


class FileSystemApplyReceipt(BaseModel):
    # Attributes
    root: FileSystemRootRef
    success: bool = Field(default=True)
    error: str | None = Field(default=None)
    created_count: int = Field(default=0)
    updated_count: int = Field(default=0)
    deleted_count: int = Field(default=0)
    bytes_written: int = Field(default=0)
    bytes_deleted: int = Field(default=0)
    digest_verified_count: int = Field(default=0)
    artifact_receipts: list[FileSystemArtifactReceipt] = Field(default_factory=list)
    backend_receipt: FileSystemBackendReceipt | None = Field(default=None)


class FileSystemBackendCapability(BaseModel):
    # Attributes
    backend_kind: FileSystemBackendKind = Field(default=FileSystemBackendKind.unknown)
    backend_name: str
    implementation_language: str | None = Field(default=None)
    native_accelerated: bool = Field(default=False)
    supports_snapshot: bool = Field(default=False)
    supports_delta_collect: bool = Field(default=False)
    supports_delta_apply: bool = Field(default=False)
    supports_digest_verification: bool = Field(default=False)
    supports_artifact_storage: bool = Field(default=False)
    path_safety_mode: FileSystemPathSafetyMode = Field(default=FileSystemPathSafetyMode.unsupported)


class FileSystemBackendCapabilities(BaseModel):
    # Attributes
    capabilities: list[FileSystemBackendCapability] = Field(default_factory=list)
    selected_backend: FileSystemBackendCapability | None = Field(default=None)
