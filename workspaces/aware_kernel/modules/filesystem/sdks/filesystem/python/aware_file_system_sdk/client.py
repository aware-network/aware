from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaResponse,
)
from aware_file_system_service_dto.file_system.service_operation import (
    CollectFileSystemDeltaRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    CollectFileSystemDeltaResponse,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemApplyPolicy,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemBackendKind,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaSet,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemFilterProfile,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemRelativePath,
)
from aware_file_system_service_dto.file_system.types import FileSystemRootRef
from aware_file_system_service_dto.file_system.service_operation import (
    ScanFileSystemSnapshotRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ScanFileSystemSnapshotResponse,
)
from aware_file_system_service_dto.file_system.service_operation import (
    VerifyFileSystemRootRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    VerifyFileSystemRootResponse,
)


class FileSystemSdkError(RuntimeError):
    pass


class FileSystemDeltaCapabilityClient(Protocol):
    async def apply(
        self,
        request: ApplyFileSystemDeltaRequest,
    ) -> ApplyFileSystemDeltaResponse: ...

    async def collect(
        self,
        request: CollectFileSystemDeltaRequest,
    ) -> CollectFileSystemDeltaResponse: ...


class FileSystemRootCapabilityClient(Protocol):
    async def verify(
        self,
        request: VerifyFileSystemRootRequest,
    ) -> VerifyFileSystemRootResponse: ...


class FileSystemSnapshotCapabilityClient(Protocol):
    async def scan(
        self,
        request: ScanFileSystemSnapshotRequest,
    ) -> ScanFileSystemSnapshotResponse: ...


class FileSystemApiNamespaceClient(Protocol):
    @property
    def delta(self) -> FileSystemDeltaCapabilityClient: ...

    @property
    def root(self) -> FileSystemRootCapabilityClient: ...

    @property
    def snapshot(self) -> FileSystemSnapshotCapabilityClient: ...


class FileSystemGeneratedApiClient(Protocol):
    @property
    def filesystem(self) -> FileSystemApiNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class AwareFileSystemSdk:
    api_client: FileSystemGeneratedApiClient
    backend_kind: FileSystemBackendKind = FileSystemBackendKind.service

    async def verify_root(
        self,
        *,
        root_path: str | Path,
        relative_paths: Sequence[str] = (),
        reject_path_escape: bool = True,
        display_name: str = "filesystem-sdk",
    ) -> VerifyFileSystemRootResponse:
        root_ref = build_root_ref(root_path=root_path, display_name=display_name)
        response = await self.api_client.filesystem.root.verify(
            VerifyFileSystemRootRequest(
                root=root_ref,
                relative_paths=[
                    FileSystemRelativePath(relative_path=normalize_relative_path(path))
                    for path in relative_paths
                ],
                reject_path_escape=reject_path_escape,
            )
        )
        if not response.success or not response.root_ok:
            raise FileSystemSdkError(
                response.error or "FileSystem root verification failed."
            )
        return response

    async def scan(
        self,
        *,
        root_path: str | Path,
        include_paths: Sequence[str] = (),
        exclude_paths: Sequence[str] = (),
        include_hashes: bool = False,
        force_refresh: bool = False,
        filter_profile: FileSystemFilterProfile = FileSystemFilterProfile.canonical_source,
        display_name: str = "filesystem-sdk-scan",
    ) -> ScanFileSystemSnapshotResponse:
        root_ref = build_root_ref(root_path=root_path, display_name=display_name)
        response = await self.api_client.filesystem.snapshot.scan(
            ScanFileSystemSnapshotRequest(
                root=root_ref,
                filter_profile=filter_profile,
                include_paths=[normalize_relative_path(path) for path in include_paths],
                exclude_paths=[normalize_relative_path(path) for path in exclude_paths],
                include_hashes=include_hashes,
                force_refresh=force_refresh,
            )
        )
        if not response.success:
            raise FileSystemSdkError(response.error or "FileSystem snapshot scan failed.")
        return response

    async def collect_delta(
        self,
        request: CollectFileSystemDeltaRequest,
    ) -> CollectFileSystemDeltaResponse:
        response = await self.api_client.filesystem.delta.collect(request)
        if not response.success:
            raise FileSystemSdkError(response.error or "FileSystem delta collect failed.")
        return response

    async def apply_delta_set(
        self,
        *,
        root_path: str | Path,
        delta_set: FileSystemDeltaSet,
        policy: FileSystemApplyPolicy | None = None,
        dry_run: bool = False,
        backend_kind: FileSystemBackendKind | None = None,
        display_name: str = "filesystem-sdk-delta-apply",
    ) -> ApplyFileSystemDeltaResponse:
        root_ref = build_root_ref(root_path=root_path, display_name=display_name)
        response = await self.api_client.filesystem.delta.apply(
            ApplyFileSystemDeltaRequest(
                root=root_ref,
                delta_set=delta_set.model_copy(update={"root": root_ref}),
                policy=policy or default_apply_policy(),
                dry_run=dry_run,
                backend_kind=backend_kind or self.backend_kind,
            )
        )
        receipt = response.receipt
        if not response.success or receipt is None or not receipt.success:
            error = response.error
            if receipt is not None and receipt.error:
                error = receipt.error
            message = (
                f"FileSystem delta apply failed: "
                f"{error or 'missing apply receipt'}"
            )
            raise FileSystemSdkError(message)
        return response


def build_file_system_sdk(
    *,
    api_client: FileSystemGeneratedApiClient,
    backend_kind: FileSystemBackendKind = FileSystemBackendKind.service,
) -> AwareFileSystemSdk:
    return AwareFileSystemSdk(api_client=api_client, backend_kind=backend_kind)


def build_root_ref(*, root_path: str | Path, display_name: str) -> FileSystemRootRef:
    root = Path(root_path).expanduser().resolve()
    return FileSystemRootRef(root_path=root.as_posix(), display_name=display_name)


def default_apply_policy() -> FileSystemApplyPolicy:
    return FileSystemApplyPolicy(
        verify_digests=True,
        reject_path_escape=True,
        allow_delete_missing=True,
        store_artifacts=False,
    )


def normalize_relative_path(value: str) -> str:
    raw = value.strip()
    if Path(raw).is_absolute():
        raise FileSystemSdkError("FileSystem SDK path must be root-relative.")
    parts: list[str] = []
    for part in Path(raw).as_posix().strip("/").split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            raise FileSystemSdkError(
                "FileSystem SDK path escapes the filesystem root."
            )
        parts.append(part)
    return "/".join(parts) if parts else "."


__all__ = [
    "AwareFileSystemSdk",
    "FileSystemApiNamespaceClient",
    "FileSystemDeltaCapabilityClient",
    "FileSystemGeneratedApiClient",
    "FileSystemRootCapabilityClient",
    "FileSystemSdkError",
    "FileSystemSnapshotCapabilityClient",
    "build_file_system_sdk",
    "build_root_ref",
    "default_apply_policy",
    "normalize_relative_path",
]
