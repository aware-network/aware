from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import platform
from time import perf_counter
from typing import Any, cast

from aware_file_system.config import (
    CanonicalSourceFilterConfig,
    Config,
    FileSystemConfig,
    FilterConfig,
)
from aware_file_system.index.file_metadata_cached import FileMetadataCached
from aware_file_system.index.file_system_index import FileSystemIndex
from aware_file_system.native_apply import (
    NativeApplyUnavailable,
    WorkspaceApplyDelta,
    collect_python_workspace_apply,
)
from aware_file_system.native_backend import (
    WORKSPACE_APPLY_DELTAS_OPERATION,
    WORKSPACE_SNAPSHOT_OPERATION,
    active_backend_capabilities,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaRequest,
    ApplyFileSystemDeltaResponse,
    CollectFileSystemDeltaRequest,
    CollectFileSystemDeltaResponse,
    ResolveFileSystemBackendCapabilitiesRequest,
    ResolveFileSystemBackendCapabilitiesResponse,
    ScanFileSystemSnapshotRequest,
    ScanFileSystemSnapshotResponse,
    VerifyFileSystemRootRequest,
    VerifyFileSystemRootResponse,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemApplyPolicy,
    FileSystemApplyReceipt,
    FileSystemBackendCapabilities,
    FileSystemBackendCapability,
    FileSystemBackendKind,
    FileSystemBackendReceipt,
    FileSystemContentDigest,
    FileSystemDeltaEntry,
    FileSystemDeltaOperation,
    FileSystemDeltaSet,
    FileSystemDeltaTotals,
    FileSystemDigestAlgorithm,
    FileSystemEntryKind,
    FileSystemEntryMetadata,
    FileSystemEntrySnapshot,
    FileSystemFilterProfile,
    FileSystemPathSafetyMode,
    FileSystemRelativePath,
    FileSystemRootRef,
    FileSystemScanStats,
    FileSystemSnapshot,
)

RUST_SERVICE_APPLY_STREAM_CHUNK_BYTES = 65_536


@dataclass(frozen=True, slots=True)
class DirectFileSystemRuntimeApiSession:
    api_client: "DirectFileSystemRuntimeApiClient"

    def warm_rust_apply_backend(self) -> dict[str, Any]:
        return self.api_client.warm_rust_apply_backend()

    def close(self) -> dict[str, Any]:
        return self.api_client.close()

    def __enter__(self) -> "DirectFileSystemRuntimeApiSession":
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


class DirectFileSystemRuntimeApiClient:
    """Generated-API-compatible FileSystem client backed by local runtime code."""

    def __init__(self, *, support: "_FileSystemRuntimeSupport | None" = None) -> None:
        self._support = support or _FileSystemRuntimeSupport()
        self._filesystem = _DirectFileSystemNamespaceClient(support=self._support)

    @property
    def filesystem(self) -> "_DirectFileSystemNamespaceClient":
        return self._filesystem

    def warm_rust_apply_backend(self) -> dict[str, Any]:
        return self._support.warm_rust_apply_service()

    def close(self) -> dict[str, Any]:
        return self._support.close()


class _DirectFileSystemNamespaceClient:
    def __init__(self, *, support: "_FileSystemRuntimeSupport") -> None:
        self.backend = _DirectFileSystemBackendClient(support=support)
        self.delta = _DirectFileSystemDeltaClient(support=support)
        self.root = _DirectFileSystemRootClient(support=support)
        self.snapshot = _DirectFileSystemSnapshotClient(support=support)


class _DirectFileSystemBackendClient:
    def __init__(self, *, support: "_FileSystemRuntimeSupport") -> None:
        self._support = support

    async def capabilities(
        self,
        request: ResolveFileSystemBackendCapabilitiesRequest,
    ) -> ResolveFileSystemBackendCapabilitiesResponse:
        success, error, capabilities = self._support.capabilities(
            requested_backend_kind=request.requested_backend_kind,
            require_native=request.require_native,
        )
        return ResolveFileSystemBackendCapabilitiesResponse(
            request_id=request.request_id,
            success=success,
            error=error,
            capabilities=capabilities,
            backend_receipt=self._support.backend_receipt(
                operation=request.operation,
                metadata={
                    "requested_backend_kind": request.requested_backend_kind.value,
                    "require_native": request.require_native,
                },
            ),
        )


class _DirectFileSystemRootClient:
    def __init__(self, *, support: "_FileSystemRuntimeSupport") -> None:
        self._support = support

    async def verify(
        self,
        request: VerifyFileSystemRootRequest,
    ) -> VerifyFileSystemRootResponse:
        try:
            root_path = _resolve_existing_root(request.root)
            rejected = []
            for item in request.relative_paths:
                try:
                    _resolve_relative_file_path(root_path=root_path, path=item)
                except ValueError:
                    rejected.append(item)
            root_ok = not rejected
            return VerifyFileSystemRootResponse(
                request_id=request.request_id,
                success=root_ok or not request.reject_path_escape,
                error=(
                    None
                    if root_ok or not request.reject_path_escape
                    else "path_escape_rejected"
                ),
                root_ok=root_ok,
                rejected_paths=rejected,
                backend_receipt=self._support.backend_receipt(
                    operation=request.operation,
                    metadata={"checked_path_count": len(request.relative_paths)},
                ),
            )
        except Exception as exc:
            return VerifyFileSystemRootResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                root_ok=False,
                rejected_paths=list(request.relative_paths),
                backend_receipt=self._support.backend_receipt(
                    operation=request.operation,
                    metadata={"error": str(exc)},
                ),
            )


class _DirectFileSystemSnapshotClient:
    def __init__(self, *, support: "_FileSystemRuntimeSupport") -> None:
        self._support = support

    async def scan(
        self,
        request: ScanFileSystemSnapshotRequest,
    ) -> ScanFileSystemSnapshotResponse:
        try:
            scan = _scan_root_snapshot(
                root=request.root,
                filter_profile=request.filter_profile,
                include_paths=tuple(request.include_paths),
                exclude_paths=tuple(request.exclude_paths),
                include_hashes=request.include_hashes,
                force_refresh=request.force_refresh,
                support=self._support,
            )
            return ScanFileSystemSnapshotResponse(
                request_id=request.request_id,
                success=True,
                snapshot=scan.snapshot,
                backend_receipt=scan.snapshot.backend_receipt,
            )
        except Exception as exc:
            receipt = self._support.backend_receipt(
                operation=request.operation,
                metadata={"error": str(exc)},
            )
            return ScanFileSystemSnapshotResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                snapshot=None,
                backend_receipt=receipt,
            )


class _DirectFileSystemDeltaClient:
    def __init__(self, *, support: "_FileSystemRuntimeSupport") -> None:
        self._support = support

    async def collect(
        self,
        request: CollectFileSystemDeltaRequest,
    ) -> CollectFileSystemDeltaResponse:
        try:
            scan = _scan_root_snapshot(
                root=request.root,
                filter_profile=request.filter_profile,
                include_paths=tuple(
                    item.relative_path for item in request.changed_paths
                ),
                exclude_paths=(),
                include_hashes=request.include_hashes,
                force_refresh=True,
                support=self._support,
            )
            delta_set = _collect_delta_set(
                request=request,
                current_snapshot=scan.snapshot,
            )
            return CollectFileSystemDeltaResponse(
                request_id=request.request_id,
                success=True,
                delta_set=delta_set,
                backend_receipt=delta_set.backend_receipt,
            )
        except Exception as exc:
            receipt = self._support.backend_receipt(
                operation=request.operation,
                metadata={"error": str(exc)},
            )
            return CollectFileSystemDeltaResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                delta_set=None,
                backend_receipt=receipt,
            )

    async def apply(
        self,
        request: ApplyFileSystemDeltaRequest,
    ) -> ApplyFileSystemDeltaResponse:
        policy = request.policy or FileSystemApplyPolicy()
        try:
            root_path = _resolve_existing_root(request.root)
            backend_kind = _effective_apply_backend_kind(request.backend_kind)
            if request.dry_run:
                receipt = _dry_run_apply_delta_set(
                    root_path=root_path,
                    root=request.root,
                    delta_set=request.delta_set,
                    policy=policy,
                    support=self._support,
                )
            elif backend_kind is FileSystemBackendKind.rust:
                receipt = _apply_delta_set_rust(
                    root_path=root_path,
                    root=request.root,
                    delta_set=request.delta_set,
                    policy=policy,
                    support=self._support,
                )
            else:
                receipt = _apply_delta_set_python(
                    root_path=root_path,
                    root=request.root,
                    delta_set=request.delta_set,
                    policy=policy,
                    support=self._support,
                    requested_backend_kind=request.backend_kind,
                )
            return ApplyFileSystemDeltaResponse(
                request_id=request.request_id,
                success=receipt.success,
                error=receipt.error,
                receipt=receipt,
                backend_receipt=receipt.backend_receipt,
            )
        except Exception as exc:
            requested_backend_kind = request.backend_kind
            backend_kind = _effective_apply_backend_kind(requested_backend_kind)
            backend_receipt = self._support.backend_receipt(
                backend_kind=backend_kind,
                operation=request.operation,
                metadata={
                    "error": str(exc),
                    "requested_backend_kind": requested_backend_kind.value,
                },
            )
            receipt = FileSystemApplyReceipt(
                root=request.root,
                success=False,
                error=str(exc),
                backend_receipt=backend_receipt,
            )
            return ApplyFileSystemDeltaResponse(
                request_id=request.request_id,
                success=False,
                error=str(exc),
                receipt=receipt,
                backend_receipt=backend_receipt,
            )


@dataclass(frozen=True, slots=True)
class _SnapshotScan:
    snapshot: FileSystemSnapshot
    scan_result: object
    duration_s: float
    content_read_count: int


class _FileSystemRuntimeSupport:
    def __init__(self) -> None:
        self._rust_apply_service: object | None = None

    def rust_apply_service(self) -> object:
        service = self._rust_apply_service
        if service is not None:
            service.start()
            return service
        from aware_file_system.native_apply_executor import (
            RustWorkspaceApplyExecutorConfig,
            RustWorkspaceApplyService,
            prepare_rust_workspace_apply_service_executor,
        )

        executor = prepare_rust_workspace_apply_service_executor(
            RustWorkspaceApplyExecutorConfig(release=True)
        )
        service = RustWorkspaceApplyService(executor)
        service.start()
        self._rust_apply_service = service
        return service

    def warm_rust_apply_service(self) -> dict[str, Any]:
        cached_before = self._rust_apply_service is not None
        started = perf_counter()
        service = self.rust_apply_service()
        warm_duration_s = perf_counter() - started
        ping_started = perf_counter()
        ping_response = service.ping()
        ping_duration_s = perf_counter() - ping_started
        return {
            "backend_kind": FileSystemBackendKind.rust.value,
            "cached_before": cached_before,
            "cached_after": True,
            "warm_duration_s": warm_duration_s,
            "process_start_duration_s": service.start_duration_s,
            "ping_duration_s": ping_duration_s,
            "ping_response": ping_response,
            "service_invocation_kind": service.executor.invocation_kind,
            "service_binary_path": service.executor.binary_path.as_posix(),
        }

    def close(self) -> dict[str, Any]:
        service = self._rust_apply_service
        self._rust_apply_service = None
        if service is not None:
            service.close()
        return {
            "rust_apply_service_cached_before": service is not None,
            "rust_apply_service_closed": service is not None,
        }

    def backend_receipt(
        self,
        *,
        backend_kind: FileSystemBackendKind = FileSystemBackendKind.python,
        backend_name: str | None = None,
        implementation_language: str | None = None,
        native_accelerated: bool = False,
        operation: str | None = None,
        duration_s: float | None = None,
        metadata: dict[str, object] | None = None,
    ) -> FileSystemBackendReceipt:
        timings: dict[str, object] = {}
        if duration_s is not None:
            timings["duration_s"] = duration_s
        receipt_metadata = dict(metadata or {})
        if operation is not None:
            receipt_metadata["operation"] = operation
        return FileSystemBackendReceipt(
            backend_kind=backend_kind,
            backend_name=backend_name or "aware-file-system",
            implementation_language=implementation_language or "python",
            native_accelerated=native_accelerated,
            platform=platform.platform(),
            timings=timings,
            metadata=receipt_metadata,
        )

    def capabilities(
        self,
        *,
        requested_backend_kind: FileSystemBackendKind,
        require_native: bool,
    ) -> tuple[bool, str | None, FileSystemBackendCapabilities]:
        native = active_backend_capabilities(prefer_native=True)
        python_capability = FileSystemBackendCapability(
            backend_kind=FileSystemBackendKind.python,
            backend_name="aware-file-system-python",
            implementation_language="python",
            native_accelerated=False,
            supports_snapshot=True,
            supports_delta_collect=True,
            supports_delta_apply=True,
            supports_digest_verification=True,
            supports_artifact_storage=False,
            path_safety_mode=FileSystemPathSafetyMode.root_relative,
        )
        capabilities = [python_capability]
        rust_capability: FileSystemBackendCapability | None = None
        if native.native_available:
            supported = set(native.supported_operations)
            rust_capability = FileSystemBackendCapability(
                backend_kind=FileSystemBackendKind.rust,
                backend_name="aware-file-system-rust",
                implementation_language="rust",
                native_accelerated=True,
                supports_snapshot=WORKSPACE_SNAPSHOT_OPERATION in supported,
                supports_delta_collect=False,
                supports_delta_apply=WORKSPACE_APPLY_DELTAS_OPERATION in supported,
                supports_digest_verification=True,
                supports_artifact_storage=False,
                path_safety_mode=FileSystemPathSafetyMode.root_relative,
            )
            capabilities.append(rust_capability)

        selected = python_capability
        if requested_backend_kind is FileSystemBackendKind.rust:
            if rust_capability is None:
                return (
                    False,
                    native.reason or "Rust FileSystem backend is not available.",
                    FileSystemBackendCapabilities(
                        capabilities=capabilities,
                        selected_backend=None,
                    ),
                )
            selected = rust_capability

        if require_native and rust_capability is None:
            return (
                False,
                native.reason or "Native FileSystem backend is required but unavailable.",
                FileSystemBackendCapabilities(
                    capabilities=capabilities,
                    selected_backend=None,
                ),
            )
        return (
            True,
            None,
            FileSystemBackendCapabilities(
                capabilities=capabilities,
                selected_backend=selected,
            ),
        )


def build_direct_file_system_runtime_api_client() -> DirectFileSystemRuntimeApiClient:
    return DirectFileSystemRuntimeApiClient()


def build_direct_file_system_runtime_api_session() -> DirectFileSystemRuntimeApiSession:
    return DirectFileSystemRuntimeApiSession(
        api_client=DirectFileSystemRuntimeApiClient(),
    )


def _scan_root_snapshot(
    *,
    root: FileSystemRootRef,
    filter_profile: FileSystemFilterProfile,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
    include_hashes: bool,
    force_refresh: bool,
    support: _FileSystemRuntimeSupport,
) -> _SnapshotScan:
    root_path = _resolve_existing_root(root)
    index = FileSystemIndex(
        Config(
            file_system=FileSystemConfig(
                root_path=root_path.as_posix(),
                generate_tree=False,
                export_json=False,
            ),
            filter=_filter_config_for_profile(filter_profile),
        )
    )
    started = perf_counter()
    scan_result, current_files = index.scan_relative_metadata(
        force_refresh=force_refresh
    )
    duration_s = perf_counter() - started

    entries: list[FileSystemEntrySnapshot] = []
    content_read_count = 0
    for relative_path in sorted(current_files):
        normalized = _normalize_relative_text(relative_path)
        if not _path_selected(
            normalized,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
        ):
            continue
        metadata = current_files[relative_path]
        digest: FileSystemContentDigest | None = None
        if include_hashes:
            digest = _digest_for_metadata(root_path=root_path, metadata=metadata)
            content_read_count += 1
        entries.append(
            FileSystemEntrySnapshot(
                path=FileSystemRelativePath(relative_path=normalized),
                metadata=_entry_metadata(
                    root_path=root_path,
                    relative_path=normalized,
                    metadata=metadata,
                ),
                digest=digest,
            )
        )

    cache_stats = index.scanner.get_cache_stats()
    directory_cache = cast(dict[str, Any], cache_stats.get("directory_cache", {}))
    cache_miss_count = max(
        int(getattr(scan_result, "total_changes", 0)),
        content_read_count,
    )
    cache_hit_count = max(
        0,
        int(getattr(scan_result, "files_processed", 0)) - cache_miss_count,
    )
    stats = FileSystemScanStats(
        scanned_entry_count=len(entries),
        file_count=len(entries),
        directory_count=int(directory_cache.get("total_directories") or 0),
        symlink_count=0,
        content_read_count=content_read_count,
        cache_hit_count=cache_hit_count,
        cache_miss_count=cache_miss_count,
        changed_directory_count=int(directory_cache.get("changed_directories") or 0),
        duration_s=duration_s,
    )
    backend_receipt = support.backend_receipt(
        operation="scan_snapshot",
        duration_s=duration_s,
        metadata={
            "filter_profile": filter_profile.value,
            "force_refresh": force_refresh,
            "include_hashes": include_hashes,
            "include_path_count": len(include_paths),
            "scanned_entry_count": len(entries),
            "content_read_count": content_read_count,
        },
    )
    snapshot = FileSystemSnapshot(
        root=root,
        filter_profile=filter_profile,
        entries=entries,
        stats=stats,
        backend_receipt=backend_receipt,
    )
    return _SnapshotScan(
        snapshot=snapshot,
        scan_result=scan_result,
        duration_s=duration_s,
        content_read_count=content_read_count,
    )


def _collect_delta_set(
    *,
    request: CollectFileSystemDeltaRequest,
    current_snapshot: FileSystemSnapshot,
) -> FileSystemDeltaSet:
    base_entries = {
        _normalize_relative_text(entry.path.relative_path): entry
        for entry in (request.base_snapshot.entries if request.base_snapshot else [])
    }
    current_entries = {
        _normalize_relative_text(entry.path.relative_path): entry
        for entry in current_snapshot.entries
    }
    selected_paths = set(base_entries) | set(current_entries)
    if request.changed_paths:
        changed = {
            _normalize_relative_text(item.relative_path)
            for item in request.changed_paths
        }
        selected_paths = selected_paths & changed

    root_path = _resolve_existing_root(request.root)
    entries: list[FileSystemDeltaEntry] = []
    for relative_path in sorted(selected_paths):
        before = base_entries.get(relative_path)
        after = current_entries.get(relative_path)
        if before is None and after is not None:
            entries.append(
                _delta_entry(
                    operation=FileSystemDeltaOperation.create,
                    path=relative_path,
                    before=None,
                    after=after,
                    include_content=request.include_content,
                    root_path=root_path,
                )
            )
        elif before is not None and after is None:
            entries.append(
                _delta_entry(
                    operation=FileSystemDeltaOperation.delete,
                    path=relative_path,
                    before=before,
                    after=None,
                    include_content=False,
                    root_path=root_path,
                )
            )
        elif (
            before is not None
            and after is not None
            and _snapshot_entry_changed(before, after)
        ):
            entries.append(
                _delta_entry(
                    operation=FileSystemDeltaOperation.update,
                    path=relative_path,
                    before=before,
                    after=after,
                    include_content=request.include_content,
                    root_path=root_path,
                )
            )

    totals = FileSystemDeltaTotals(
        create_count=sum(
            1 for entry in entries if entry.operation is FileSystemDeltaOperation.create
        ),
        update_count=sum(
            1 for entry in entries if entry.operation is FileSystemDeltaOperation.update
        ),
        delete_count=sum(
            1 for entry in entries if entry.operation is FileSystemDeltaOperation.delete
        ),
        byte_count=sum(
            int(
                (
                    entry.after_metadata.size_bytes
                    if entry.after_metadata is not None
                    else entry.before_metadata.size_bytes
                    if entry.before_metadata is not None
                    else 0
                )
                or 0
            )
            for entry in entries
        ),
        digest_count=sum(
            1
            for entry in entries
            if entry.after_digest is not None or entry.before_digest is not None
        ),
    )
    return FileSystemDeltaSet(
        root=request.root,
        base_revision_id=(
            request.base_snapshot.root.root_id
            if request.base_snapshot is not None
            else None
        ),
        filter_profile=request.filter_profile,
        entries=entries,
        totals=totals,
        backend_receipt=current_snapshot.backend_receipt,
    )


def _delta_entry(
    *,
    operation: FileSystemDeltaOperation,
    path: str,
    before: FileSystemEntrySnapshot | None,
    after: FileSystemEntrySnapshot | None,
    include_content: bool,
    root_path: Path,
) -> FileSystemDeltaEntry:
    content_text = None
    if (
        include_content
        and after is not None
        and operation is not FileSystemDeltaOperation.delete
    ):
        target = _resolve_relative_file_path(root_path=root_path, path=after.path)
        content_text = target.read_text(encoding="utf-8")
    return FileSystemDeltaEntry(
        operation=operation,
        path=FileSystemRelativePath(relative_path=path),
        before_metadata=before.metadata if before is not None else None,
        after_metadata=after.metadata if after is not None else None,
        before_digest=before.digest if before is not None else None,
        after_digest=after.digest if after is not None else None,
        content_text=content_text,
    )


def _apply_delta_set_python(
    *,
    root_path: Path,
    root: FileSystemRootRef,
    delta_set: FileSystemDeltaSet,
    policy: FileSystemApplyPolicy,
    support: _FileSystemRuntimeSupport,
    requested_backend_kind: FileSystemBackendKind,
) -> FileSystemApplyReceipt:
    _validate_apply_policy(policy)
    started = perf_counter()
    workspace_deltas = tuple(
        _workspace_apply_delta(root_path=root_path, entry=entry, policy=policy)
        for entry in delta_set.entries
    )
    report = collect_python_workspace_apply(root_path, workspace_deltas)
    duration_s = perf_counter() - started
    return FileSystemApplyReceipt(
        root=root,
        success=True,
        created_count=sum(1 for entry in report.entries if entry.operation == "create"),
        updated_count=sum(1 for entry in report.entries if entry.operation == "update"),
        deleted_count=sum(1 for entry in report.entries if entry.operation == "delete"),
        bytes_written=report.bytes_written,
        bytes_deleted=report.bytes_deleted,
        digest_verified_count=report.digest_verified_count,
        artifact_receipts=[],
        backend_receipt=support.backend_receipt(
            backend_kind=FileSystemBackendKind.python,
            operation="apply_delta",
            duration_s=duration_s,
            metadata={
                "dry_run": False,
                "requested_backend_kind": requested_backend_kind.value,
                "applied_path_count": report.applied_path_count,
                "stored_artifact_count": report.stored_artifact_count,
            },
        ),
    )


def _apply_delta_set_rust(
    *,
    root_path: Path,
    root: FileSystemRootRef,
    delta_set: FileSystemDeltaSet,
    policy: FileSystemApplyPolicy,
    support: _FileSystemRuntimeSupport,
) -> FileSystemApplyReceipt:
    _validate_apply_policy(policy)
    started = perf_counter()
    workspace_deltas = tuple(
        _workspace_apply_delta(root_path=root_path, entry=entry, policy=policy)
        for entry in delta_set.entries
    )
    try:
        rust_service = support.rust_apply_service()
        report = rust_service.apply(
            root_path,
            workspace_deltas,
            direct_stream_payloads=True,
            stream_chunk_bytes=RUST_SERVICE_APPLY_STREAM_CHUNK_BYTES,
            compact_response=True,
            server_timings=True,
        )
    except NativeApplyUnavailable:
        raise
    duration_s = perf_counter() - started
    content_engine = (
        dict(report.content_engine) if report.content_engine is not None else None
    )
    metadata = {
        "dry_run": False,
        "requested_backend_kind": FileSystemBackendKind.rust.value,
        "applied_path_count": report.applied_path_count,
        "stored_artifact_count": report.stored_artifact_count,
        "digest_backend_kind": report.digest_backend_kind,
        "service_payload_protocol": rust_service.last_apply_client_protocol,
        "service_response_protocol": rust_service.last_apply_client_response_protocol,
        "service_timing_protocol": rust_service.last_apply_server_timing_protocol,
        "service_stream_chunk_bytes": RUST_SERVICE_APPLY_STREAM_CHUNK_BYTES,
        "service_content_engine": content_engine,
        "service_client_timings_s": rust_service.last_apply_client_timings_s,
        "service_client_counters": rust_service.last_apply_client_counters,
        "service_server_timings_s": rust_service.last_apply_server_timings_s,
        "service_server_flags": rust_service.last_apply_server_flags,
        "service_invocation_kind": rust_service.executor.invocation_kind,
        "service_binary_path": rust_service.executor.binary_path.as_posix(),
    }
    return FileSystemApplyReceipt(
        root=root,
        success=True,
        created_count=sum(1 for entry in report.entries if entry.operation == "create"),
        updated_count=sum(1 for entry in report.entries if entry.operation == "update"),
        deleted_count=sum(1 for entry in report.entries if entry.operation == "delete"),
        bytes_written=report.bytes_written,
        bytes_deleted=report.bytes_deleted,
        digest_verified_count=report.digest_verified_count,
        artifact_receipts=[],
        backend_receipt=support.backend_receipt(
            backend_kind=FileSystemBackendKind.rust,
            backend_name="aware-file-system-rust",
            implementation_language="rust",
            native_accelerated=True,
            operation="apply_delta",
            duration_s=duration_s,
            metadata=metadata,
        ),
    )


def _dry_run_apply_delta_set(
    *,
    root_path: Path,
    root: FileSystemRootRef,
    delta_set: FileSystemDeltaSet,
    policy: FileSystemApplyPolicy,
    support: _FileSystemRuntimeSupport,
) -> FileSystemApplyReceipt:
    _validate_apply_policy(policy)
    started = perf_counter()
    created_count = 0
    updated_count = 0
    deleted_count = 0
    bytes_written = 0
    bytes_deleted = 0
    digest_verified_count = 0
    for entry in delta_set.entries:
        target = _resolve_relative_file_path(root_path=root_path, path=entry.path)
        operation = _operation_value(entry.operation)
        if operation in {"create", "update"}:
            if operation == "create":
                created_count += 1
            else:
                updated_count += 1
            content_bytes = _entry_content_bytes(entry)
            bytes_written += len(content_bytes)
            if policy.verify_digests and entry.after_digest is not None:
                _verify_content_digest(content_bytes, entry.after_digest)
                digest_verified_count += 1
        elif operation == "delete":
            deleted_count += 1
            if target.exists():
                if not target.is_file():
                    raise ValueError(
                        "FileSystem dry-run delete target is not a file: "
                        f"{entry.path.relative_path}"
                    )
                bytes_deleted += target.stat().st_size
            elif not policy.allow_delete_missing:
                raise ValueError(
                    "FileSystem dry-run delete target is missing: "
                    f"{entry.path.relative_path}"
                )
        else:
            raise ValueError(f"Unsupported FileSystem delta operation: {operation}")

    duration_s = perf_counter() - started
    return FileSystemApplyReceipt(
        root=root,
        success=True,
        created_count=created_count,
        updated_count=updated_count,
        deleted_count=deleted_count,
        bytes_written=bytes_written,
        bytes_deleted=bytes_deleted,
        digest_verified_count=digest_verified_count,
        artifact_receipts=[],
        backend_receipt=support.backend_receipt(
            operation="apply_delta",
            duration_s=duration_s,
            metadata={"dry_run": True},
        ),
    )


def _workspace_apply_delta(
    *,
    root_path: Path,
    entry: FileSystemDeltaEntry,
    policy: FileSystemApplyPolicy,
) -> WorkspaceApplyDelta:
    target = _resolve_relative_file_path(root_path=root_path, path=entry.path)
    operation = _operation_value(entry.operation)
    if operation == "delete":
        if not target.exists() and not policy.allow_delete_missing:
            raise ValueError(
                f"FileSystem delete target is missing: {entry.path.relative_path}"
            )
        return WorkspaceApplyDelta(operation="delete", path=entry.path.relative_path)
    if operation not in {"create", "update"}:
        raise ValueError(f"Unsupported FileSystem delta operation: {operation}")
    content_bytes = _entry_content_bytes(entry)
    expected_sha256 = (
        entry.after_digest.hex
        if policy.verify_digests and entry.after_digest is not None
        else None
    )
    return WorkspaceApplyDelta(
        operation=operation,
        path=entry.path.relative_path,
        content_bytes=content_bytes,
        expected_sha256=expected_sha256,
    )


def _entry_content_bytes(entry: FileSystemDeltaEntry) -> bytes:
    if entry.content_ref is not None:
        raise ValueError("FileSystem SDK direct runtime does not resolve content_ref.")
    if entry.content_text is None:
        raise ValueError(
            f"FileSystem apply requires content_text for {entry.operation.value}: "
            f"{entry.path.relative_path}"
        )
    return entry.content_text.encode("utf-8")


def _verify_content_digest(
    content: bytes,
    digest: FileSystemContentDigest,
) -> None:
    if digest.algorithm is not FileSystemDigestAlgorithm.sha256:
        raise ValueError(
            f"Unsupported FileSystem digest algorithm: {digest.algorithm.value}"
        )
    actual = sha256(content).hexdigest()
    if actual != digest.hex:
        raise ValueError(
            f"FileSystem digest mismatch: expected {digest.hex}, got {actual}"
        )


def _validate_apply_policy(policy: FileSystemApplyPolicy) -> None:
    if not policy.reject_path_escape:
        raise ValueError("FileSystem SDK direct runtime requires reject_path_escape=true.")
    if policy.store_artifacts:
        raise ValueError("FileSystem SDK direct runtime does not store artifacts yet.")
    if policy.path_safety_mode is FileSystemPathSafetyMode.unsupported:
        raise ValueError("FileSystem apply path safety mode is unsupported.")


def _effective_apply_backend_kind(
    requested: FileSystemBackendKind,
) -> FileSystemBackendKind:
    if requested is FileSystemBackendKind.rust:
        return FileSystemBackendKind.rust
    return FileSystemBackendKind.python


def _entry_metadata(
    *,
    root_path: Path,
    relative_path: str,
    metadata: FileMetadataCached,
) -> FileSystemEntryMetadata:
    target = root_path / relative_path
    stat = target.lstat()
    mode = oct(stat.st_mode & 0o777)
    return FileSystemEntryMetadata(
        kind=FileSystemEntryKind.file,
        size_bytes=metadata.size,
        modified_time_ns=metadata.mtime_ns,
        mode=mode,
        executable=bool(stat.st_mode & 0o111),
        symlink_target=target.readlink().as_posix() if target.is_symlink() else None,
    )


def _digest_for_metadata(
    *,
    root_path: Path,
    metadata: FileMetadataCached,
) -> FileSystemContentDigest:
    target = _resolve_relative_file_path(
        root_path=root_path,
        path=FileSystemRelativePath(relative_path=metadata.path),
    )
    return FileSystemContentDigest(
        algorithm=FileSystemDigestAlgorithm.sha256,
        hex=metadata.compute_hash_if_needed(target.as_posix()),
        byte_length=metadata.size,
    )


def _snapshot_entry_changed(
    before: FileSystemEntrySnapshot,
    after: FileSystemEntrySnapshot,
) -> bool:
    if before.digest is not None and after.digest is not None:
        return before.digest.hex != after.digest.hex
    return before.metadata.model_dump(mode="json") != after.metadata.model_dump(
        mode="json"
    )


def _resolve_existing_root(root: FileSystemRootRef) -> Path:
    root_path = Path(root.root_path).expanduser().resolve()
    if not root_path.is_dir():
        raise ValueError(f"FileSystem root is not a directory: {root.root_path}")
    return root_path


def _resolve_relative_file_path(
    *,
    root_path: Path,
    path: FileSystemRelativePath,
) -> Path:
    normalized = _normalize_relative_text(path.relative_path)
    target = (root_path / normalized).resolve()
    try:
        target.relative_to(root_path)
    except ValueError as exc:
        raise ValueError(
            f"FileSystem relative path escapes root: {path.relative_path}"
        ) from exc
    return target


def _normalize_relative_text(value: str) -> str:
    raw = str(value or "").replace("\\", "/")
    candidate = Path(raw)
    if not raw.strip() or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"FileSystem path must stay root-relative: {value!r}")
    normalized = candidate.as_posix().strip("/")
    if not normalized or normalized == ".":
        raise ValueError("FileSystem relative path must target an entry.")
    return normalized


def _path_selected(
    relative_path: str,
    *,
    include_paths: tuple[str, ...],
    exclude_paths: tuple[str, ...],
) -> bool:
    include_tokens = tuple(_normalize_selector_path(path) for path in include_paths)
    exclude_tokens = tuple(_normalize_selector_path(path) for path in exclude_paths)
    if include_tokens and not any(
        _path_matches_selector(relative_path, token) for token in include_tokens
    ):
        return False
    return not any(
        _path_matches_selector(relative_path, token) for token in exclude_tokens
    )


def _normalize_selector_path(value: str) -> str:
    return str(value or "").replace("\\", "/").strip("/")


def _path_matches_selector(relative_path: str, selector: str) -> bool:
    if not selector:
        return False
    return relative_path == selector or relative_path.startswith(f"{selector}/")


def _filter_config_for_profile(profile: FileSystemFilterProfile) -> FilterConfig:
    if profile is FileSystemFilterProfile.no_filter:
        return FilterConfig(
            use_gitignore=False,
            regex=[],
            ignored_dirs=[],
            inherit_ignore_defaults=False,
        )
    if profile is FileSystemFilterProfile.all_user_source:
        return FilterConfig(use_gitignore=True)
    return CanonicalSourceFilterConfig()


def _operation_value(operation: FileSystemDeltaOperation | str) -> str:
    if isinstance(operation, FileSystemDeltaOperation):
        return operation.value
    return str(operation)


__all__ = [
    "DirectFileSystemRuntimeApiClient",
    "DirectFileSystemRuntimeApiSession",
    "build_direct_file_system_runtime_api_client",
    "build_direct_file_system_runtime_api_session",
]
