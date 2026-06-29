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

# File System Service Dto
from aware_file_system_service_dto.file_system.types import (
    FileSystemBackendKind,
    FileSystemFilterProfile,
)

if TYPE_CHECKING:
    from aware_file_system_service_dto.file_system.types import FileSystemApplyPolicy
    from aware_file_system_service_dto.file_system.types import FileSystemApplyReceipt
    from aware_file_system_service_dto.file_system.types import FileSystemBackendCapabilities
    from aware_file_system_service_dto.file_system.types import FileSystemBackendReceipt
    from aware_file_system_service_dto.file_system.types import FileSystemDeltaSet
    from aware_file_system_service_dto.file_system.types import FileSystemRelativePath
    from aware_file_system_service_dto.file_system.types import FileSystemRootRef
    from aware_file_system_service_dto.file_system.types import FileSystemSnapshot


class FileSystemServiceRequest(BaseModel):
    """
    FileSystem service operation DTOs (transport-only).
    These operation payloads define the future API boundary. They do not imply
    a service implementation exists yet.
    """

    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "scan_snapshot": "aware_file_system_service_dto.file_system.service_operation.ScanFileSystemSnapshotRequest",
        "collect_delta": "aware_file_system_service_dto.file_system.service_operation.CollectFileSystemDeltaRequest",
        "apply_delta": "aware_file_system_service_dto.file_system.service_operation.ApplyFileSystemDeltaRequest",
        "verify_root": "aware_file_system_service_dto.file_system.service_operation.VerifyFileSystemRootRequest",
        "backend_capabilities": "aware_file_system_service_dto.file_system.service_operation.ResolveFileSystemBackendCapabilitiesRequest",
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
            return UnknownFileSystemServiceRequest.model_validate(v)
        return cls.model_validate(v)


class UnknownFileSystemServiceRequest(FileSystemServiceRequest):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class FileSystemServiceResponse(BaseModel):
    # Discriminator Key
    operation: str

    # Attributes
    request_id: UUID | None = Field(default=None)
    success: bool = Field(default=True)
    info: str | None = Field(default=None)
    error: str | None = Field(default=None)
    backend_receipt: FileSystemBackendReceipt | None = Field(default=None)

    _DISCRIMINATOR_KEY: ClassVar[str] = "operation"
    _TAG_TO_TYPE: ClassVar[dict[str, str]] = {
        "scan_snapshot": "aware_file_system_service_dto.file_system.service_operation.ScanFileSystemSnapshotResponse",
        "collect_delta": "aware_file_system_service_dto.file_system.service_operation.CollectFileSystemDeltaResponse",
        "apply_delta": "aware_file_system_service_dto.file_system.service_operation.ApplyFileSystemDeltaResponse",
        "verify_root": "aware_file_system_service_dto.file_system.service_operation.VerifyFileSystemRootResponse",
        "backend_capabilities": "aware_file_system_service_dto.file_system.service_operation.ResolveFileSystemBackendCapabilitiesResponse",
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
            return UnknownFileSystemServiceResponse.model_validate(v)
        return cls.model_validate(v)


class UnknownFileSystemServiceResponse(FileSystemServiceResponse):
    """Forward-compatible fallback when `operation` is not a known discriminator tag."""

    model_config = {"extra": "allow"}


class ScanFileSystemSnapshotRequest(FileSystemServiceRequest):
    # Discriminator Tag
    operation: Literal["scan_snapshot"] = "scan_snapshot"

    # Attributes
    root: FileSystemRootRef
    filter_profile: FileSystemFilterProfile = Field(default=FileSystemFilterProfile.canonical_source)
    include_paths: list[str] = Field(default_factory=list)
    exclude_paths: list[str] = Field(default_factory=list)
    include_hashes: bool = Field(default=False)
    force_refresh: bool = Field(default=False)
    backend_kind: FileSystemBackendKind = Field(default=FileSystemBackendKind.unknown)


class ScanFileSystemSnapshotResponse(FileSystemServiceResponse):
    # Discriminator Tag
    operation: Literal["scan_snapshot"] = "scan_snapshot"

    # Attributes
    snapshot: FileSystemSnapshot | None = Field(default=None)


class CollectFileSystemDeltaRequest(FileSystemServiceRequest):
    # Discriminator Tag
    operation: Literal["collect_delta"] = "collect_delta"

    # Attributes
    root: FileSystemRootRef
    base_snapshot: FileSystemSnapshot | None = Field(default=None)
    changed_paths: list[FileSystemRelativePath] = Field(default_factory=list)
    filter_profile: FileSystemFilterProfile = Field(default=FileSystemFilterProfile.canonical_source)
    include_content: bool = Field(default=False)
    include_hashes: bool = Field(default=True)
    backend_kind: FileSystemBackendKind = Field(default=FileSystemBackendKind.unknown)


class CollectFileSystemDeltaResponse(FileSystemServiceResponse):
    # Discriminator Tag
    operation: Literal["collect_delta"] = "collect_delta"

    # Attributes
    delta_set: FileSystemDeltaSet | None = Field(default=None)


class ApplyFileSystemDeltaRequest(FileSystemServiceRequest):
    # Discriminator Tag
    operation: Literal["apply_delta"] = "apply_delta"

    # Attributes
    root: FileSystemRootRef
    delta_set: FileSystemDeltaSet
    policy: FileSystemApplyPolicy | None = Field(default=None)
    dry_run: bool = Field(default=False)
    backend_kind: FileSystemBackendKind = Field(default=FileSystemBackendKind.unknown)


class ApplyFileSystemDeltaResponse(FileSystemServiceResponse):
    # Discriminator Tag
    operation: Literal["apply_delta"] = "apply_delta"

    # Attributes
    receipt: FileSystemApplyReceipt | None = Field(default=None)


class VerifyFileSystemRootRequest(FileSystemServiceRequest):
    # Discriminator Tag
    operation: Literal["verify_root"] = "verify_root"

    # Attributes
    root: FileSystemRootRef
    relative_paths: list[FileSystemRelativePath] = Field(default_factory=list)
    reject_path_escape: bool = Field(default=True)


class VerifyFileSystemRootResponse(FileSystemServiceResponse):
    # Discriminator Tag
    operation: Literal["verify_root"] = "verify_root"

    # Attributes
    root_ok: bool = Field(default=False)
    rejected_paths: list[FileSystemRelativePath] = Field(default_factory=list)


class ResolveFileSystemBackendCapabilitiesRequest(FileSystemServiceRequest):
    # Discriminator Tag
    operation: Literal["backend_capabilities"] = "backend_capabilities"

    # Attributes
    requested_backend_kind: FileSystemBackendKind = Field(default=FileSystemBackendKind.unknown)
    require_native: bool = Field(default=False)


class ResolveFileSystemBackendCapabilitiesResponse(FileSystemServiceResponse):
    # Discriminator Tag
    operation: Literal["backend_capabilities"] = "backend_capabilities"

    # Attributes
    capabilities: FileSystemBackendCapabilities | None = Field(default=None)
