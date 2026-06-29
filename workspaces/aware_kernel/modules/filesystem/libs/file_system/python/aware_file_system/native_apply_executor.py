from __future__ import annotations

import json
import os
import subprocess
import time
import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Mapping, Protocol, Sequence

from aware_file_system.native_apply import (
    NativeApplyUnavailable,
    WorkspaceApplyDelta,
    WorkspaceApplyReport,
    workspace_apply_delta_content_bytes,
    workspace_apply_report_from_mapping,
)


RUST_WORKSPACE_APPLY_BINARY_NAME = "aware-file-system-native-apply"
RUST_WORKSPACE_APPLY_SERVICE_BINARY_NAME = "aware-file-system-native-apply-service"
RUST_WORKSPACE_APPLY_LIBRARY_NAME = "aware_file_system_native"
RUST_WORKSPACE_APPLY_DEBUG_INVOCATION_KIND = "prepared_debug_cli_binary"
RUST_WORKSPACE_APPLY_RELEASE_INVOCATION_KIND = "prepared_release_cli_binary"
RUST_WORKSPACE_APPLY_PREPARED_INVOCATION_KIND = "provided_prepared_cli_binary"
RUST_WORKSPACE_APPLY_SERVICE_DEBUG_INVOCATION_KIND = "prepared_debug_service_binary"
RUST_WORKSPACE_APPLY_SERVICE_RELEASE_INVOCATION_KIND = "prepared_release_service_binary"
RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND = (
    "provided_prepared_service_binary"
)
RUST_WORKSPACE_APPLY_LIBRARY_DEBUG_INVOCATION_KIND = "prepared_debug_cdylib"
RUST_WORKSPACE_APPLY_LIBRARY_RELEASE_INVOCATION_KIND = "prepared_release_cdylib"
RUST_WORKSPACE_APPLY_LIBRARY_PREPARED_INVOCATION_KIND = "provided_prepared_cdylib"
RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND = "ctypes_in_process_cdylib_direct_stream_v1"
RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL = "length_prefixed_buffered_v1"
RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL = "chunked_stream_v1"
RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL = (
    "direct_chunked_stream_v1"
)
RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL = "full_apply_report_json_v1"
RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL = "compact_apply_report_v1"
RUST_WORKSPACE_APPLY_SERVICE_RESPONSE_SCHEMA = (
    "aware.file_system.workspace_apply_service_response.v1"
)
RUST_WORKSPACE_APPLY_SERVICE_TIMING_SCHEMA = (
    "aware.file_system.workspace_apply_service_timing.v1"
)
RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL = "timing_trailer_json_v1"
RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL = "buffered_binary_io_v1"
RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL = (
    "vectored_memoryview_v1"
)
DEFAULT_RUST_APPLY_BUILD_TIMEOUT_S = 240.0
DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES = 262_144

_COMPACT_APPLY_REPORT_FIELDS = (
    "backend_kind",
    "benchmark_version",
    "operation",
    "digest_backend_kind",
    "root_path",
    "applied_path_count",
    "bytes_written",
    "bytes_deleted",
    "digest_verified_count",
    "materialized_artifact_count",
    "stored_artifact_count",
)
_COMPACT_APPLY_CONTENT_ENGINE_FIELDS = (
    "engine_kind",
    "streaming_capable",
    "payload_count",
    "buffered_payload_count",
    "streamed_payload_count",
    "bytes_buffered",
    "bytes_streamed",
    "spooled_streamed_payload_count",
    "direct_streamed_payload_count",
    "bytes_spooled",
    "bytes_direct_streamed",
    "chunk_count",
    "max_chunk_bytes",
)
_COMPACT_APPLY_ENTRY_FIELDS = (
    "before_exists",
    "after_exists",
    "before_sha256",
    "after_sha256",
    "bytes_written",
    "bytes_deleted",
    "digest_verified",
)
_COMPACT_APPLY_PHASE_TIMING_FIELDS = (
    "unit",
    "root_canonicalize_ns",
    "apply_plan_ns",
    "apply_plan_delta_count",
    "apply_plan_unique_target_path_count",
    "apply_plan_parent_bucket_count",
    "apply_plan_max_parent_bucket_size_count",
    "apply_plan_bucket_count",
    "apply_plan_conflict_bucket_count",
    "apply_plan_parallel_safe_bucket_count",
    "apply_plan_parallel_safe_delta_count",
    "apply_plan_max_bucket_size_count",
    "apply_plan_repeated_target_path_count",
    "apply_plan_ancestor_conflict_count",
    "apply_scheduler_ns",
    "apply_scheduler_enabled_count",
    "apply_scheduler_skipped_count",
    "apply_scheduler_worker_count",
    "apply_scheduler_bucket_count",
    "apply_scheduler_delta_count",
    "apply_scheduler_parallel_bucket_count",
    "apply_scheduler_parallel_delta_count",
    "apply_scheduler_serial_conflict_bucket_count",
    "apply_scheduler_serial_conflict_delta_count",
    "apply_scheduler_worker_execution_count",
    "apply_scheduler_selector_ns",
    "apply_scheduler_requested_count",
    "apply_scheduler_selected_count",
    "apply_scheduler_sequential_fallback_count",
    "apply_scheduler_conflict_fallback_count",
    "apply_scheduler_worker_floor_fallback_count",
    "apply_scheduler_empty_batch_fallback_count",
    "path_validation_ns",
    "metadata_probe_ns",
    "root_safety_ns",
    "root_directory_check_ns",
    "existing_target_root_safety_ns",
    "after_write_root_safety_ns",
    "after_write_root_safety_gate_ns",
    "after_write_root_safety_skipped_count",
    "after_write_root_safety_executed_count",
    "target_leaf_safety_ns",
    "target_leaf_name_encode_ns",
    "target_leaf_open_ns",
    "target_leaf_open_count",
    "parent_descriptor_open_ns",
    "dirfd_cache_lookup_ns",
    "dirfd_chain_open_ns",
    "dirfd_mkdir_ns",
    "before_digest_ns",
    "before_digest_read_ns",
    "before_digest_hash_ns",
    "before_digest_hex_ns",
    "before_digest_bytes_read_count",
    "before_digest_bytes_hashed_count",
    "digest_normalization_ns",
    "parent_prepare_ns",
    "write_ns",
    "create_write_ns",
    "update_write_ns",
    "direct_stream_read_ns",
    "direct_stream_file_write_ns",
    "direct_stream_hash_ns",
    "direct_stream_chunk_read_count",
    "direct_stream_bytes_read_count",
    "direct_stream_buffer_reuse_count",
    "delete_ns",
    "after_digest_ns",
    "after_digest_hash_ns",
    "after_digest_hex_ns",
    "after_digest_bytes_hashed_count",
    "after_digest_precomputed_count",
    "after_digest_precomputed_bytes_hashed_count",
    "after_digest_precomputed_hash_ns",
    "after_digest_precomputed_hex_ns",
    "create_after_digest_ns",
    "update_after_digest_ns",
    "receipt_aggregation_ns",
    "total_profiled_apply_ns",
    "json_encode_ns",
)


class _CargoBuildRequestFactory(Protocol):
    def __call__(
        self,
        *,
        manifest_path: Path,
        bin_name: str,
        target_dir: Path | None,
        cargo_path: Path | None,
        cargo_home: Path | None,
        release: bool,
        timeout_s: float,
    ) -> object: ...


class _CargoDynamicLibraryBuildRequestFactory(Protocol):
    def __call__(
        self,
        *,
        manifest_path: Path,
        library_name: str,
        target_dir: Path | None,
        cargo_path: Path | None,
        cargo_home: Path | None,
        release: bool,
        timeout_s: float,
    ) -> object: ...


class _PreparedBinaryReceipt(Protocol):
    artifact_path: Path
    status: str

    def to_mapping(self) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class RustWorkspaceApplyExecutorConfig:
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    manifest_path: Path | None = None
    target_dir: Path | None = None
    prepared_binary_path: Path | None = None
    release: bool = False
    build_timeout_s: float = DEFAULT_RUST_APPLY_BUILD_TIMEOUT_S


@dataclass(frozen=True, slots=True)
class RustWorkspaceApplyExecutor:
    binary_path: Path
    invocation_kind: str
    manifest_path: Path
    target_dir: Path | None
    rust_build: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class RustWorkspaceApplyLibraryExecutorConfig:
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    manifest_path: Path | None = None
    target_dir: Path | None = None
    prepared_library_path: Path | None = None
    release: bool = False
    build_timeout_s: float = DEFAULT_RUST_APPLY_BUILD_TIMEOUT_S


@dataclass(frozen=True, slots=True)
class RustWorkspaceApplyLibraryExecutor:
    library_path: Path
    invocation_kind: str
    manifest_path: Path
    target_dir: Path | None
    rust_build: Mapping[str, Any] | None = None
    boundary_kind: str = RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND
    _library: RustWorkspaceApplyLibrary | None = None

    def apply(
        self,
        root: Path,
        deltas: Sequence[WorkspaceApplyDelta],
    ) -> WorkspaceApplyReport:
        library = self._library or RustWorkspaceApplyLibrary(self.library_path)
        return library.apply(root, deltas)


def prepare_rust_workspace_apply_executor(
    config: RustWorkspaceApplyExecutorConfig | None = None,
) -> RustWorkspaceApplyExecutor:
    return _prepare_rust_workspace_apply_binary(
        config=config,
        bin_name=RUST_WORKSPACE_APPLY_BINARY_NAME,
        debug_invocation_kind=RUST_WORKSPACE_APPLY_DEBUG_INVOCATION_KIND,
        release_invocation_kind=RUST_WORKSPACE_APPLY_RELEASE_INVOCATION_KIND,
        prepared_invocation_kind=RUST_WORKSPACE_APPLY_PREPARED_INVOCATION_KIND,
    )


def prepare_rust_workspace_apply_service_executor(
    config: RustWorkspaceApplyExecutorConfig | None = None,
) -> RustWorkspaceApplyExecutor:
    return _prepare_rust_workspace_apply_binary(
        config=config,
        bin_name=RUST_WORKSPACE_APPLY_SERVICE_BINARY_NAME,
        debug_invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_DEBUG_INVOCATION_KIND,
        release_invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_RELEASE_INVOCATION_KIND,
        prepared_invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND,
    )


def prepare_rust_workspace_apply_library_executor(
    config: RustWorkspaceApplyLibraryExecutorConfig | None = None,
) -> RustWorkspaceApplyLibraryExecutor:
    resolved = config or RustWorkspaceApplyLibraryExecutorConfig()
    manifest_path = (
        resolved.manifest_path.expanduser().resolve()
        if resolved.manifest_path is not None
        else default_rust_workspace_apply_manifest_path()
    )
    target_dir = (
        resolved.target_dir.expanduser().resolve()
        if resolved.target_dir is not None
        else None
    )

    if resolved.prepared_library_path is not None:
        library_path = resolved.prepared_library_path.expanduser().resolve()
        if not library_path.is_file():
            raise NativeApplyUnavailable(
                "Prepared Rust workspace apply library does not exist: "
                f"{library_path.as_posix()}"
            )
        return _load_workspace_apply_library_executor(
            library_path=library_path,
            invocation_kind=RUST_WORKSPACE_APPLY_LIBRARY_PREPARED_INVOCATION_KIND,
            manifest_path=manifest_path,
            target_dir=target_dir,
            rust_build=None,
        )

    cargo_api = _load_rust_tooling()
    try:
        request = cargo_api.dynamic_library_build_request(
            manifest_path=manifest_path,
            library_name=RUST_WORKSPACE_APPLY_LIBRARY_NAME,
            target_dir=target_dir,
            cargo_path=resolved.cargo_path,
            cargo_home=resolved.cargo_home,
            release=resolved.release,
            timeout_s=resolved.build_timeout_s,
        )
        receipt = cargo_api.prepare_dynamic_library(request)
    except cargo_api.unavailable_error as exc:
        raise NativeApplyUnavailable(str(exc)) from exc

    build_receipt = receipt.to_mapping()
    if receipt.status != "succeeded":
        result = _mapping_value(build_receipt, "result")
        output = ""
        if isinstance(result, Mapping):
            stderr = str(result.get("stderr") or "").strip()
            stdout = str(result.get("stdout") or "").strip()
            output = stderr or stdout
        raise NativeApplyUnavailable(
            "Rust workspace apply library preparation failed: "
            f"{output or receipt.status}"
        )

    library_path = receipt.artifact_path.expanduser().resolve()
    if not library_path.is_file():
        raise NativeApplyUnavailable(
            f"Rust workspace apply library was not built: {library_path.as_posix()}"
        )
    return _load_workspace_apply_library_executor(
        library_path=library_path,
        invocation_kind=(
            RUST_WORKSPACE_APPLY_LIBRARY_RELEASE_INVOCATION_KIND
            if resolved.release
            else RUST_WORKSPACE_APPLY_LIBRARY_DEBUG_INVOCATION_KIND
        ),
        manifest_path=manifest_path,
        target_dir=target_dir,
        rust_build=build_receipt,
    )


def _load_workspace_apply_library_executor(
    *,
    library_path: Path,
    invocation_kind: str,
    manifest_path: Path,
    target_dir: Path | None,
    rust_build: Mapping[str, Any] | None,
) -> RustWorkspaceApplyLibraryExecutor:
    library = RustWorkspaceApplyLibrary(library_path)
    return RustWorkspaceApplyLibraryExecutor(
        library_path=library.library_path,
        invocation_kind=invocation_kind,
        manifest_path=manifest_path,
        target_dir=target_dir,
        rust_build=rust_build,
        _library=library,
    )


def _prepare_rust_workspace_apply_binary(
    *,
    config: RustWorkspaceApplyExecutorConfig | None,
    bin_name: str,
    debug_invocation_kind: str,
    release_invocation_kind: str,
    prepared_invocation_kind: str,
) -> RustWorkspaceApplyExecutor:
    resolved = config or RustWorkspaceApplyExecutorConfig()
    manifest_path = (
        resolved.manifest_path.expanduser().resolve()
        if resolved.manifest_path is not None
        else default_rust_workspace_apply_manifest_path()
    )
    target_dir = (
        resolved.target_dir.expanduser().resolve()
        if resolved.target_dir is not None
        else None
    )

    if resolved.prepared_binary_path is not None:
        binary_path = resolved.prepared_binary_path.expanduser().resolve()
        if not binary_path.is_file():
            raise NativeApplyUnavailable(
                f"Prepared Rust workspace apply binary {bin_name!r} does not exist: "
                f"{binary_path.as_posix()}"
            )
        return RustWorkspaceApplyExecutor(
            binary_path=binary_path,
            invocation_kind=prepared_invocation_kind,
            manifest_path=manifest_path,
            target_dir=target_dir,
            rust_build=None,
        )

    cargo_api = _load_rust_tooling()
    try:
        request = cargo_api.build_request(
            manifest_path=manifest_path,
            bin_name=bin_name,
            target_dir=target_dir,
            cargo_path=resolved.cargo_path,
            cargo_home=resolved.cargo_home,
            release=resolved.release,
            timeout_s=resolved.build_timeout_s,
        )
        receipt = cargo_api.prepare_binary(request)
    except cargo_api.unavailable_error as exc:
        raise NativeApplyUnavailable(str(exc)) from exc

    build_receipt = receipt.to_mapping()
    if receipt.status != "succeeded":
        result = _mapping_value(build_receipt, "result")
        output = ""
        if isinstance(result, Mapping):
            stderr = str(result.get("stderr") or "").strip()
            stdout = str(result.get("stdout") or "").strip()
            output = stderr or stdout
        raise NativeApplyUnavailable(
            f"Rust workspace apply binary {bin_name!r} preparation failed: "
            f"{output or receipt.status}"
        )

    binary_path = receipt.artifact_path.expanduser().resolve()
    if not binary_path.is_file():
        raise NativeApplyUnavailable(
            f"Rust workspace apply binary was not built: {binary_path.as_posix()}"
        )
    return RustWorkspaceApplyExecutor(
        binary_path=binary_path,
        invocation_kind=(
            release_invocation_kind if resolved.release else debug_invocation_kind
        ),
        manifest_path=manifest_path,
        target_dir=target_dir,
        rust_build=build_receipt,
    )


def collect_prepared_rust_workspace_apply(
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    *,
    executor: RustWorkspaceApplyExecutor,
) -> WorkspaceApplyReport:
    command = [executor.binary_path.as_posix(), root.expanduser().resolve().as_posix()]
    for delta in deltas:
        content_arg = _workspace_apply_cli_content_arg(delta)
        command.extend(
            [
                delta.operation,
                delta.path,
                delta.expected_sha256 or "-",
                content_arg if content_arg is not None else "-",
            ]
        )

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise NativeApplyUnavailable(
            "Rust workspace apply command failed: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    try:
        raw_report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise NativeApplyUnavailable(
            "Rust workspace apply emitted invalid JSON"
        ) from exc
    if not isinstance(raw_report, Mapping):
        raise NativeApplyUnavailable(
            "Rust workspace apply report must be a JSON object"
        )
    return workspace_apply_report_from_mapping(raw_report)


class _NativeApplyDeltaV1(ctypes.Structure):
    _fields_ = (
        ("operation", ctypes.c_uint8),
        ("path_ptr", ctypes.c_void_p),
        ("path_len", ctypes.c_size_t),
        ("expected_sha256_ptr", ctypes.c_void_p),
        ("expected_sha256_len", ctypes.c_size_t),
        ("content_ptr", ctypes.c_void_p),
        ("content_len", ctypes.c_size_t),
        ("has_expected_sha256", ctypes.c_bool),
        ("has_content", ctypes.c_bool),
    )


class _NativeApplyOutputV1(ctypes.Structure):
    _fields_ = (("ptr", ctypes.c_void_p), ("len", ctypes.c_size_t))


_NATIVE_APPLY_OPERATION_CODES = {
    "create": 1,
    "update": 2,
    "delete": 3,
}


def _ffi_apply_deltas(
    deltas: Sequence[WorkspaceApplyDelta],
) -> tuple[ctypes.Array[_NativeApplyDeltaV1], tuple[object, ...]]:
    records: list[_NativeApplyDeltaV1] = []
    keepalive: list[object] = []
    for delta in deltas:
        operation = _NATIVE_APPLY_OPERATION_CODES.get(delta.operation)
        if operation is None:
            raise NativeApplyUnavailable(
                f"Rust workspace apply library operation is unsupported: {delta.operation}"
            )
        path_bytes = delta.path.encode("utf-8")
        path_pointer, path_keepalive = _ffi_bytes_pointer(path_bytes)
        keepalive.extend(path_keepalive)

        expected_pointer = ctypes.c_void_p()
        expected_len = 0
        has_expected = delta.expected_sha256 is not None
        if delta.expected_sha256 is not None:
            expected_bytes = delta.expected_sha256.encode("utf-8")
            expected_pointer, expected_keepalive = _ffi_bytes_pointer(expected_bytes)
            expected_len = len(expected_bytes)
            keepalive.extend(expected_keepalive)

        content_pointer = ctypes.c_void_p()
        content_len = 0
        content_bytes = workspace_apply_delta_content_bytes(delta)
        has_content = content_bytes is not None
        if content_bytes is not None:
            content_pointer, content_keepalive = _ffi_bytes_pointer(content_bytes)
            content_len = len(content_bytes)
            keepalive.extend(content_keepalive)

        records.append(
            _NativeApplyDeltaV1(
                operation=operation,
                path_ptr=path_pointer,
                path_len=len(path_bytes),
                expected_sha256_ptr=expected_pointer,
                expected_sha256_len=expected_len,
                content_ptr=content_pointer,
                content_len=content_len,
                has_expected_sha256=has_expected,
                has_content=has_content,
            )
        )
    array_type = _NativeApplyDeltaV1 * len(records)
    return array_type(*records), tuple(keepalive)


def _ffi_bytes_pointer(
    value: bytes | bytearray | memoryview,
) -> tuple[ctypes.c_void_p, tuple[object, ...]]:
    if len(value) == 0:
        return ctypes.c_void_p(), (value,)
    if isinstance(value, bytes):
        pointer = ctypes.c_char_p(value)
        return ctypes.cast(pointer, ctypes.c_void_p), (pointer, value)

    view = memoryview(value)
    if view.ndim != 1:
        raise ValueError("Rust workspace apply library buffers must be one-dimensional")
    if view.readonly or not view.c_contiguous:
        copied = view.tobytes()
        pointer = ctypes.c_char_p(copied)
        return ctypes.cast(pointer, ctypes.c_void_p), (pointer, copied)

    buffer_type = ctypes.c_ubyte * view.nbytes
    buffer = buffer_type.from_buffer(view)
    return ctypes.cast(buffer, ctypes.c_void_p), (buffer, view, value)


class RustWorkspaceApplyLibrary:
    def __init__(self, library_path: Path) -> None:
        resolved_path = library_path.expanduser().resolve()
        if not resolved_path.is_file():
            raise NativeApplyUnavailable(
                f"Rust workspace apply library does not exist: {resolved_path.as_posix()}"
            )
        self.library_path = resolved_path
        try:
            self._library = ctypes.CDLL(resolved_path.as_posix())
            self._apply = self._library.aware_file_system_workspace_apply_deltas_json_v1
            self._free = self._library.aware_file_system_workspace_apply_free_json_v1
        except OSError as exc:
            raise NativeApplyUnavailable(
                f"Rust workspace apply library failed to load: {exc}"
            ) from exc
        except AttributeError as exc:
            raise NativeApplyUnavailable(
                "Rust workspace apply library is missing required apply symbols"
            ) from exc

        self._apply.argtypes = (
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.POINTER(_NativeApplyDeltaV1),
            ctypes.c_size_t,
            ctypes.POINTER(_NativeApplyOutputV1),
        )
        self._apply.restype = ctypes.c_int
        self._free.argtypes = (ctypes.c_void_p, ctypes.c_size_t)
        self._free.restype = None

    def apply(
        self,
        root: Path,
        deltas: Sequence[WorkspaceApplyDelta],
    ) -> WorkspaceApplyReport:
        root_bytes = root.expanduser().resolve().as_posix().encode("utf-8")
        root_pointer, root_keepalive = _ffi_bytes_pointer(root_bytes)
        raw_deltas, keepalive = _ffi_apply_deltas(deltas)
        output = _NativeApplyOutputV1()
        status = self._apply(
            root_pointer,
            len(root_bytes),
            raw_deltas,
            len(raw_deltas),
            ctypes.byref(output),
        )
        _ = root_keepalive, keepalive
        try:
            response_bytes = (
                ctypes.string_at(output.ptr, output.len)
                if output.ptr and output.len
                else b""
            )
        finally:
            if output.ptr:
                self._free(output.ptr, output.len)

        try:
            raw_response = json.loads(response_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NativeApplyUnavailable(
                "Rust workspace apply library emitted invalid JSON"
            ) from exc
        if status != 0:
            message = ""
            if isinstance(raw_response, Mapping):
                message = str(raw_response.get("message") or "").strip()
            raise NativeApplyUnavailable(
                "Rust workspace apply library failed with status "
                f"{status}: {message or raw_response!r}"
            )
        if not isinstance(raw_response, Mapping):
            raise NativeApplyUnavailable(
                "Rust workspace apply library report must be a JSON object"
            )
        return workspace_apply_report_from_mapping(raw_response)


def collect_prepared_rust_workspace_apply_library(
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    *,
    executor: RustWorkspaceApplyLibraryExecutor,
) -> WorkspaceApplyReport:
    return executor.apply(root, deltas)


class RustWorkspaceApplyService:
    def __init__(self, executor: RustWorkspaceApplyExecutor) -> None:
        self.executor = executor
        self._process: subprocess.Popen[bytes] | None = None
        self.start_duration_s: float | None = None
        self.last_apply_client_timings_s: dict[str, float] | None = None
        self.last_apply_client_counters: dict[str, int] | None = None
        self.last_apply_client_protocol: str | None = None
        self.last_apply_client_response_protocol: str | None = None
        self.last_apply_client_request_handoff_protocol: str | None = None
        self.last_apply_server_timings_s: dict[str, float] | None = None
        self.last_apply_server_flags: dict[str, bool] | None = None
        self.last_apply_server_timing_protocol: str | None = None

    def __enter__(self) -> RustWorkspaceApplyService:
        return self.start()

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def start(self) -> RustWorkspaceApplyService:
        if self._process is not None and self._process.poll() is None:
            return self
        started = time.perf_counter()
        try:
            self._process = subprocess.Popen(
                [self.executor.binary_path.as_posix()],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            raise NativeApplyUnavailable(
                "Rust workspace apply service failed to start: " f"{exc}"
            ) from exc
        self.start_duration_s = time.perf_counter() - started
        return self

    def ping(self) -> dict[str, Any]:
        response = self._request("PING")
        _raise_service_error_response(response)
        if response.get("status") != "ok":
            raise NativeApplyUnavailable(
                f"Rust workspace apply service ping failed: {response!r}"
            )
        return response

    def apply(
        self,
        root: Path,
        deltas: Sequence[WorkspaceApplyDelta],
        *,
        stream_payloads: bool = False,
        direct_stream_payloads: bool = False,
        stream_chunk_bytes: int = DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES,
        compact_response: bool = False,
        server_timings: bool = False,
    ) -> WorkspaceApplyReport:
        if stream_payloads and direct_stream_payloads:
            raise ValueError(
                "Rust apply service can use either temp-spool streaming or "
                "direct streaming, not both."
            )
        if stream_payloads or direct_stream_payloads:
            _validate_stream_chunk_bytes(stream_chunk_bytes)
        payload_protocol = (
            RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
            if direct_stream_payloads
            else (
                RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
                if stream_payloads
                else RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
            )
        )
        base_command = (
            "APPLY_DIRECT_STREAM"
            if direct_stream_payloads
            else ("APPLY_STREAM" if stream_payloads else "APPLY")
        )
        command = f"{base_command}_COMPACT" if compact_response else base_command
        if server_timings:
            command = f"{command}_TIMED"
        response_protocol = (
            RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL
            if compact_response
            else RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
        )
        boundary_started = time.perf_counter()
        request_started = time.perf_counter()
        request_byte_count = 0
        request_content_byte_count = 0
        request_text_payload_count = 0
        request_binary_payload_count = 0
        request_buffered_payload_count = 0
        request_streamed_payload_count = 0
        request_spooled_streamed_payload_count = 0
        request_direct_streamed_payload_count = 0
        request_stream_chunk_count = 0
        request_max_chunk_bytes = 0
        request_root_resolve_s = 0.0
        request_control_write_s = 0.0
        request_delta_metadata_write_s = 0.0
        request_content_materialize_s = 0.0
        request_payload_write_s = 0.0
        request_flush_s = 0.0
        try:
            stream = self._stdin()
            request_writer = _ApplyServiceRequestWriter(
                stream,
                vectored=direct_stream_payloads,
            )
            root_resolve_started = time.perf_counter()
            root_path = root.expanduser().resolve().as_posix()
            request_root_resolve_s = time.perf_counter() - root_resolve_started
            control_write_started = time.perf_counter()
            request_byte_count += request_writer.write_protocol_line(command)
            request_byte_count += request_writer.write_required_protocol_string(
                root_path
            )
            request_byte_count += request_writer.write_protocol_line(str(len(deltas)))
            request_control_write_s = time.perf_counter() - control_write_started
            for delta in deltas:
                metadata_write_started = time.perf_counter()
                request_byte_count += request_writer.write_required_protocol_string(
                    delta.operation,
                )
                request_byte_count += request_writer.write_required_protocol_string(
                    delta.path
                )
                request_byte_count += request_writer.write_optional_protocol_string(
                    delta.expected_sha256,
                )
                request_delta_metadata_write_s += (
                    time.perf_counter() - metadata_write_started
                )
                content_materialize_started = time.perf_counter()
                content_bytes = workspace_apply_delta_content_bytes(delta)
                request_content_materialize_s += (
                    time.perf_counter() - content_materialize_started
                )
                if content_bytes is not None:
                    request_content_byte_count += len(content_bytes)
                    if delta.content_bytes is not None:
                        request_binary_payload_count += 1
                    else:
                        request_text_payload_count += 1
                    if stream_payloads:
                        request_streamed_payload_count += 1
                        request_spooled_streamed_payload_count += 1
                    elif direct_stream_payloads:
                        request_streamed_payload_count += 1
                        request_direct_streamed_payload_count += 1
                    else:
                        request_buffered_payload_count += 1
                payload_write_started = time.perf_counter()
                if stream_payloads or direct_stream_payloads:
                    (
                        payload_request_byte_count,
                        stream_chunk_count,
                        max_chunk_bytes,
                    ) = request_writer.write_optional_protocol_byte_chunks(
                        content_bytes,
                        stream_chunk_bytes=stream_chunk_bytes,
                    )
                    request_byte_count += payload_request_byte_count
                    request_stream_chunk_count += stream_chunk_count
                    request_max_chunk_bytes = max(
                        request_max_chunk_bytes,
                        max_chunk_bytes,
                    )
                else:
                    request_byte_count += request_writer.write_optional_protocol_bytes(
                        content_bytes,
                    )
                request_payload_write_s += time.perf_counter() - payload_write_started
            flush_started = time.perf_counter()
            request_writer.flush()
            request_flush_s = time.perf_counter() - flush_started
        except OSError as exc:
            raise NativeApplyUnavailable(
                "Rust workspace apply service request failed: " f"{exc}"
            ) from exc
        request_write_s = time.perf_counter() - request_started

        response_read_started = time.perf_counter()
        response_line = self._read_json_response_line()
        response_read_s = time.perf_counter() - response_read_started
        response_decode_started = time.perf_counter()
        response_json_decode_started = time.perf_counter()
        response = _decode_json_response(response_line)
        response_json_decode_s = time.perf_counter() - response_json_decode_started
        response_report_expand_started = time.perf_counter()
        response = _expand_apply_service_response(response, deltas=deltas)
        response_report_expand_s = time.perf_counter() - response_report_expand_started
        response_decode_s = time.perf_counter() - response_decode_started
        timing_trailer_read_s = 0.0
        timing_trailer_decode_s = 0.0
        server_timings_s: dict[str, float] | None = None
        server_flags: dict[str, bool] | None = None
        server_timing_protocol: str | None = None
        if server_timings:
            timing_trailer_read_started = time.perf_counter()
            timing_trailer_line = self._read_json_response_line()
            timing_trailer_read_s = time.perf_counter() - timing_trailer_read_started
            timing_trailer_decode_started = time.perf_counter()
            timing_trailer = _decode_apply_service_timing_trailer(timing_trailer_line)
            timing_trailer_decode_s = (
                time.perf_counter() - timing_trailer_decode_started
            )
            server_timings_s = _service_timing_seconds(timing_trailer)
            server_flags = _service_timing_flags(timing_trailer)
            server_timing_protocol = str(timing_trailer.get("protocol") or "")
        request_profiled_s = (
            request_root_resolve_s
            + request_control_write_s
            + request_delta_metadata_write_s
            + request_content_materialize_s
            + request_payload_write_s
            + request_flush_s
        )
        response_profiled_s = response_json_decode_s + response_report_expand_s
        self.last_apply_client_timings_s = {
            "request_write_s": request_write_s,
            "request_root_resolve_s": request_root_resolve_s,
            "request_control_write_s": request_control_write_s,
            "request_delta_metadata_write_s": request_delta_metadata_write_s,
            "request_content_materialize_s": request_content_materialize_s,
            "request_payload_write_s": request_payload_write_s,
            "request_flush_s": request_flush_s,
            "request_profiled_s": request_profiled_s,
            "request_unprofiled_s": max(0.0, request_write_s - request_profiled_s),
            "response_read_s": response_read_s,
            "response_decode_s": response_decode_s,
            "response_json_decode_s": response_json_decode_s,
            "response_report_expand_s": response_report_expand_s,
            "response_profiled_s": response_profiled_s,
            "response_unprofiled_s": max(0.0, response_decode_s - response_profiled_s),
            "timing_trailer_read_s": timing_trailer_read_s,
            "timing_trailer_decode_s": timing_trailer_decode_s,
            "total_client_boundary_s": time.perf_counter() - boundary_started,
        }
        self.last_apply_client_counters = {
            "request_byte_count": request_byte_count,
            "request_content_byte_count": request_content_byte_count,
            "request_protocol_byte_count": (
                request_byte_count - request_content_byte_count
            ),
            "request_payload_count": (
                request_buffered_payload_count + request_streamed_payload_count
            ),
            "request_buffered_payload_count": request_buffered_payload_count,
            "request_streamed_payload_count": request_streamed_payload_count,
            "request_spooled_streamed_payload_count": (
                request_spooled_streamed_payload_count
            ),
            "request_direct_streamed_payload_count": (
                request_direct_streamed_payload_count
            ),
            "request_text_payload_count": request_text_payload_count,
            "request_binary_payload_count": request_binary_payload_count,
            "request_stream_chunk_count": request_stream_chunk_count,
            "request_max_chunk_bytes": request_max_chunk_bytes,
            "request_write_call_count": request_writer.write_call_count,
            "request_writev_call_count": request_writer.writev_call_count,
            "request_buffered_write_call_count": (
                request_writer.buffered_write_call_count
            ),
            "request_vectored_payload_write_count": (
                request_writer.vectored_payload_write_count
            ),
            "request_vectored_payload_byte_count": (
                request_writer.vectored_payload_byte_count
            ),
            "request_vectored_write_fallback_count": (
                request_writer.vectored_write_fallback_count
            ),
            "response_byte_count": len(response_line),
            "compact_response": int(compact_response),
            "server_timings": int(server_timings),
        }
        self.last_apply_client_protocol = payload_protocol
        self.last_apply_client_response_protocol = response_protocol
        self.last_apply_client_request_handoff_protocol = (
            request_writer.handoff_protocol
        )
        self.last_apply_server_timings_s = server_timings_s
        self.last_apply_server_flags = server_flags
        self.last_apply_server_timing_protocol = server_timing_protocol
        _raise_service_error_response(response)
        if not isinstance(response, Mapping):
            raise NativeApplyUnavailable(
                "Rust workspace apply service report must be a JSON object"
            )
        return workspace_apply_report_from_mapping(response)

    def close(self) -> None:
        process = self._process
        if process is None:
            return
        try:
            if process.poll() is None:
                try:
                    response = self._request("EXIT")
                    _raise_service_error_response(response)
                except (NativeApplyUnavailable, OSError):
                    pass
                try:
                    process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5.0)
        finally:
            self._process = None

    def _request(self, command: str) -> dict[str, Any]:
        try:
            stream = self._stdin()
            _write_protocol_line(stream, command)
            stream.flush()
        except OSError as exc:
            raise NativeApplyUnavailable(
                "Rust workspace apply service request failed: " f"{exc}"
            ) from exc
        response = self._read_json_response()
        if not isinstance(response, dict):
            raise NativeApplyUnavailable(
                "Rust workspace apply service response must be a JSON object"
            )
        return response

    def _stdin(self) -> IO[bytes]:
        process = self._process
        if process is None or process.stdin is None:
            raise NativeApplyUnavailable("Rust workspace apply service is not started")
        if process.poll() is not None:
            raise NativeApplyUnavailable(
                "Rust workspace apply service exited before request"
            )
        return process.stdin

    def _read_json_response(self) -> Mapping[str, Any]:
        return _decode_json_response(self._read_json_response_line())

    def _read_json_response_line(self) -> bytes:
        process = self._process
        if process is None or process.stdout is None:
            raise NativeApplyUnavailable("Rust workspace apply service is not started")
        line = process.stdout.readline()
        if not line:
            stderr = ""
            if process.poll() is not None and process.stderr is not None:
                stderr = process.stderr.read().decode("utf-8", errors="replace").strip()
            detail = f": {stderr}" if stderr else ""
            raise NativeApplyUnavailable(
                "Rust workspace apply service closed without response" f"{detail}"
            )
        return line


def measure_rust_workspace_apply_persistent_boundary(
    *,
    executor: RustWorkspaceApplyExecutor,
    root: Path,
    iterations: int = 5,
) -> dict[str, Any]:
    if iterations < 1:
        raise ValueError(
            "Rust workspace apply persistent boundary iterations must be at least 1."
        )
    root_path = root.expanduser().resolve()
    root_path.mkdir(parents=True, exist_ok=True)

    samples: list[dict[str, Any]] = []
    service = RustWorkspaceApplyService(executor)
    with service:
        ping_started = time.perf_counter()
        ping_response = service.ping()
        ping_duration_s = time.perf_counter() - ping_started
        for iteration_index in range(iterations):
            deltas = (
                WorkspaceApplyDelta(
                    operation="delete",
                    path=f".aware-native-persistent-probe-{iteration_index}.tmp",
                ),
            )
            started = time.perf_counter()
            report = service.apply(root_path, deltas)
            duration_s = time.perf_counter() - started
            samples.append(
                {
                    "iteration_index": iteration_index,
                    "duration_s": duration_s,
                    "applied_path_count": report.applied_path_count,
                    "bytes_written": report.bytes_written,
                    "bytes_deleted": report.bytes_deleted,
                    "digest_verified_count": report.digest_verified_count,
                }
            )

    return {
        "probe_kind": "persistent_missing_file_delete",
        "boundary_kind": "persistent_process",
        "process_started_once": True,
        "invocation_kind": executor.invocation_kind,
        "binary_path": executor.binary_path.as_posix(),
        "sample_count": iterations,
        "service_start_duration_s": service.start_duration_s,
        "ping": {
            "duration_s": ping_duration_s,
            "response": ping_response,
        },
        "samples": samples,
        "summary": {"duration_s": _stats(samples, "duration_s")},
    }


def measure_rust_workspace_apply_startup(
    *,
    executor: RustWorkspaceApplyExecutor,
    root: Path,
    iterations: int = 5,
) -> dict[str, Any]:
    if iterations < 1:
        raise ValueError("Rust workspace apply startup iterations must be at least 1.")
    root_path = root.expanduser().resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    samples: list[dict[str, Any]] = []
    for iteration_index in range(iterations):
        command = [
            executor.binary_path.as_posix(),
            root_path.as_posix(),
            "delete",
            f".aware-native-startup-probe-{iteration_index}.tmp",
            "-",
            "-",
        ]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        duration_s = time.perf_counter() - started
        if completed.returncode != 0:
            raise NativeApplyUnavailable(
                "Rust workspace apply startup probe failed: "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )
        samples.append(
            {
                "iteration_index": iteration_index,
                "duration_s": duration_s,
            }
        )
    return {
        "probe_kind": "missing_file_delete",
        "invocation_kind": executor.invocation_kind,
        "binary_path": executor.binary_path.as_posix(),
        "sample_count": iterations,
        "samples": samples,
        "summary": {"duration_s": _stats(samples, "duration_s")},
    }


def default_rust_workspace_apply_manifest_path() -> Path:
    file_system_root = Path(__file__).resolve().parents[2]
    return file_system_root / "rust" / "aware_file_system_native" / "Cargo.toml"


@dataclass(frozen=True, slots=True)
class _RustToolingApi:
    build_request: _CargoBuildRequestFactory
    prepare_binary: Any
    dynamic_library_build_request: _CargoDynamicLibraryBuildRequestFactory
    prepare_dynamic_library: Any
    unavailable_error: type[Exception]


def _load_rust_tooling() -> _RustToolingApi:
    try:
        from aware_code.language.toolchain import CodeToolchainUnavailable
        from rust_tooling.cargo import (
            CargoBuildRequest,
            CargoDynamicLibraryBuildRequest,
            prepare_cargo_binary,
            prepare_cargo_dynamic_library,
        )
    except ModuleNotFoundError as exc:
        raise NativeApplyUnavailable(
            "rust-tooling is not installed; install aware-file-system[native] "
            "to use Rust native apply"
        ) from exc
    return _RustToolingApi(
        build_request=CargoBuildRequest,
        prepare_binary=prepare_cargo_binary,
        dynamic_library_build_request=CargoDynamicLibraryBuildRequest,
        prepare_dynamic_library=prepare_cargo_dynamic_library,
        unavailable_error=CodeToolchainUnavailable,
    )


def _mapping_value(mapping: Mapping[str, object], key: str) -> object:
    return mapping.get(key)


def _decode_json_response(line: bytes) -> Mapping[str, Any]:
    try:
        raw_response = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativeApplyUnavailable(
            "Rust workspace apply service emitted invalid JSON"
        ) from exc
    if not isinstance(raw_response, Mapping):
        raise NativeApplyUnavailable(
            "Rust workspace apply service response must be a JSON object"
        )
    return raw_response


def _decode_apply_service_response(
    line: bytes,
    *,
    deltas: Sequence[WorkspaceApplyDelta],
) -> Mapping[str, Any]:
    response = _decode_json_response(line)
    return _expand_apply_service_response(response, deltas=deltas)


def _expand_apply_service_response(
    response: Mapping[str, Any],
    *,
    deltas: Sequence[WorkspaceApplyDelta],
) -> Mapping[str, Any]:
    if response.get("f") == RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL:
        return _expand_compact_apply_service_response(response, deltas=deltas)
    return response


def _decode_apply_service_timing_trailer(line: bytes) -> Mapping[str, Any]:
    timing = _decode_json_response(line)
    if timing.get("schema") != RUST_WORKSPACE_APPLY_SERVICE_TIMING_SCHEMA:
        raise NativeApplyUnavailable(
            "Rust workspace apply service timing trailer schema mismatch"
        )
    if timing.get("protocol") != RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL:
        raise NativeApplyUnavailable(
            "Rust workspace apply service timing trailer protocol mismatch"
        )
    if timing.get("unit") != "nanoseconds":
        raise NativeApplyUnavailable(
            "Rust workspace apply service timing trailer unit mismatch"
        )
    return timing


def _service_timing_seconds(timing: Mapping[str, Any]) -> dict[str, float]:
    converted: dict[str, float] = {}
    for key, value in timing.items():
        if key == "unit" or not key.endswith("_ns"):
            continue
        if not isinstance(value, int | float):
            continue
        converted[f"{key.removesuffix('_ns')}_s"] = float(value) / 1_000_000_000.0
    return converted


def _service_timing_flags(timing: Mapping[str, Any]) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for key, value in timing.items():
        if isinstance(value, bool):
            flags[str(key)] = value
    return flags


def _expand_compact_apply_service_response(
    response: Mapping[str, Any],
    *,
    deltas: Sequence[WorkspaceApplyDelta],
) -> Mapping[str, Any]:
    if response.get("s") != RUST_WORKSPACE_APPLY_SERVICE_RESPONSE_SCHEMA:
        raise NativeApplyUnavailable(
            "Rust workspace apply service compact response schema mismatch"
        )
    raw_report = _required_list(
        response.get("r"),
        "Rust workspace apply service compact response missing report",
    )
    raw_content_engine = _required_list(
        response.get("c"),
        "Rust workspace apply service compact response missing content engine",
    )
    raw_entries = _required_list(
        response.get("e"),
        "Rust workspace apply service compact response missing entries",
    )
    raw_phase_timings = _required_list(
        response.get("p"),
        "Rust workspace apply service compact response missing phase timings",
    )
    expanded_report = _zip_compact_fields(
        fields=_COMPACT_APPLY_REPORT_FIELDS,
        values=raw_report,
        label="report",
    )
    expanded_report["content_engine"] = _zip_compact_fields(
        fields=_COMPACT_APPLY_CONTENT_ENGINE_FIELDS,
        values=raw_content_engine,
        label="content_engine",
    )
    if len(raw_entries) != len(deltas):
        raise NativeApplyUnavailable(
            "Rust workspace apply service compact entry count mismatch: "
            f"expected {len(deltas)}, got {len(raw_entries)}"
        )
    expanded_report["entries"] = [
        _expand_compact_entry(
            raw_entry=_required_list(entry, "compact entry must be a list"),
            delta=delta,
        )
        for entry, delta in zip(raw_entries, deltas, strict=True)
    ]
    expanded_report["phase_timings"] = _zip_compact_fields(
        fields=_COMPACT_APPLY_PHASE_TIMING_FIELDS,
        values=raw_phase_timings,
        label="phase_timings",
    )
    expanded_report["service_response_schema"] = response.get("s")
    expanded_report["service_response_format"] = response.get("f")
    return expanded_report


def _expand_compact_entry(
    *,
    raw_entry: Sequence[object],
    delta: WorkspaceApplyDelta,
) -> dict[str, object]:
    entry = _zip_compact_fields(
        fields=_COMPACT_APPLY_ENTRY_FIELDS,
        values=raw_entry,
        label="entry",
    )
    expected_sha256 = _normalize_expected_sha256_for_response(delta.expected_sha256)
    after_sha256 = entry["after_sha256"]
    if (
        after_sha256 is None
        and expected_sha256 is not None
        and delta.operation in {"create", "update"}
        and bool(entry["digest_verified"])
    ):
        after_sha256 = expected_sha256
    return {
        "path": _normalize_response_path(delta.path),
        "operation": delta.operation,
        "before_exists": entry["before_exists"],
        "after_exists": entry["after_exists"],
        "before_sha256": entry["before_sha256"],
        "after_sha256": after_sha256,
        "expected_sha256": expected_sha256,
        "bytes_written": entry["bytes_written"],
        "bytes_deleted": entry["bytes_deleted"],
        "digest_verified": entry["digest_verified"],
    }


def _normalize_expected_sha256_for_response(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if not text or text == "-":
        return None
    if text.startswith("sha256:"):
        text = text.split(":", 1)[1]
    return text


def _normalize_response_path(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def _required_list(value: object, message: str) -> list[object]:
    if not isinstance(value, list):
        raise NativeApplyUnavailable(message)
    return value


def _zip_compact_fields(
    *,
    fields: Sequence[str],
    values: Sequence[object],
    label: str,
) -> dict[str, object]:
    if len(values) != len(fields):
        raise NativeApplyUnavailable(
            "Rust workspace apply service compact "
            f"{label} field count mismatch: expected {len(fields)}, got {len(values)}"
        )
    return dict(zip(fields, values, strict=True))


def _encode_protocol_line(text: str) -> bytes:
    return text.encode("utf-8") + b"\n"


def _encode_required_protocol_string(value: str) -> bytes:
    data = value.encode("utf-8")
    return _encode_protocol_line(str(len(data))) + data


class _ApplyServiceRequestWriter:
    def __init__(self, stream: IO[bytes], *, vectored: bool) -> None:
        self._stream = stream
        self._fd = _stream_fileno(stream) if vectored else None
        self.handoff_protocol = (
            RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
            if self._fd is not None
            else RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
        )
        self.write_call_count = 0
        self.writev_call_count = 0
        self.buffered_write_call_count = 0
        self.vectored_payload_write_count = 0
        self.vectored_payload_byte_count = 0
        self.vectored_write_fallback_count = 0

    def write_protocol_line(self, text: str) -> int:
        data = _encode_protocol_line(text)
        return self._write(data)

    def write_required_protocol_string(self, value: str) -> int:
        data = value.encode("utf-8")
        header = _encode_protocol_line(str(len(data)))
        return self._writev((header, data))

    def write_optional_protocol_string(self, value: str | None) -> int:
        if value is None:
            return self.write_protocol_line("-1")
        return self.write_required_protocol_string(value)

    def write_optional_protocol_bytes(self, value: bytes | None) -> int:
        if value is None:
            return self.write_protocol_line("-1")
        header = _encode_protocol_line(str(len(value)))
        return self._writev((header, value))

    def write_optional_protocol_byte_chunks(
        self,
        value: bytes | None,
        *,
        stream_chunk_bytes: int,
    ) -> tuple[int, int, int]:
        if value is None:
            return self.write_protocol_line("-1"), 0, 0
        _validate_stream_chunk_bytes(stream_chunk_bytes)
        request_byte_count = self.write_protocol_line(str(len(value)))
        chunk_count = (
            (len(value) + stream_chunk_bytes - 1) // stream_chunk_bytes if value else 0
        )
        request_byte_count += self.write_protocol_line(str(chunk_count))
        max_chunk_bytes = 0
        view = memoryview(value)
        for offset in range(0, len(value), stream_chunk_bytes):
            chunk = view[offset : offset + stream_chunk_bytes]
            header = _encode_protocol_line(str(len(chunk)))
            request_byte_count += self._writev((header, chunk), payload=True)
            max_chunk_bytes = max(max_chunk_bytes, len(chunk))
        return request_byte_count, chunk_count, max_chunk_bytes

    def flush(self) -> None:
        self._stream.flush()

    def _write(self, data: bytes) -> int:
        if self._fd is None:
            self._stream.write(data)
            self.buffered_write_call_count += 1
        else:
            _write_all(self._fd, data)
            self.write_call_count += 1
        return len(data)

    def _writev(
        self,
        parts: Sequence[bytes | memoryview],
        *,
        payload: bool = False,
    ) -> int:
        if self._fd is None:
            for part in parts:
                self._stream.write(part)
                self.buffered_write_call_count += 1
            byte_count = sum(len(part) for part in parts)
            return byte_count
        try:
            byte_count, call_count = _writev_all(self._fd, parts)
        except (AttributeError, NotImplementedError):
            self.vectored_write_fallback_count += 1
            byte_count = 0
            call_count = 0
            for part in parts:
                byte_count += _write_all(self._fd, part)
                call_count += 1
        self.writev_call_count += call_count
        if payload:
            self.vectored_payload_write_count += 1
            # Payload calls are exactly [header, chunk].
            self.vectored_payload_byte_count += len(parts[-1])
        return byte_count


def _stream_fileno(stream: IO[bytes]) -> int | None:
    if not hasattr(os, "writev"):
        return None
    try:
        return stream.fileno()
    except (AttributeError, OSError):
        return None


def _write_all(fd: int, data: bytes | memoryview) -> int:
    view = memoryview(data)
    total_written = 0
    while total_written < len(view):
        written = os.write(fd, view[total_written:])
        if written <= 0:
            raise OSError("Rust apply service request pipe wrote zero bytes")
        total_written += written
    return total_written


def _writev_all(
    fd: int,
    parts: Sequence[bytes | memoryview],
) -> tuple[int, int]:
    views = [memoryview(part) for part in parts if len(part) > 0]
    total_byte_count = sum(len(view) for view in views)
    total_written = 0
    call_count = 0
    while views:
        written = os.writev(fd, views)
        if written <= 0:
            raise OSError("Rust apply service request pipe wrote zero bytes")
        call_count += 1
        total_written += written
        remaining = written
        while views and remaining >= len(views[0]):
            remaining -= len(views[0])
            views.pop(0)
        if views and remaining:
            views[0] = views[0][remaining:]
    return total_byte_count, call_count


def _write_protocol_line(stream: IO[bytes], text: str) -> int:
    data = _encode_protocol_line(text)
    stream.write(data)
    return len(data)


def _write_required_protocol_string(stream: IO[bytes], value: str) -> int:
    data = _encode_required_protocol_string(value)
    stream.write(data)
    return len(data)


def _write_optional_protocol_string(stream: IO[bytes], value: str | None) -> int:
    if value is None:
        return _write_protocol_line(stream, "-1")
    return _write_required_protocol_string(stream, value)


def _write_optional_protocol_bytes(stream: IO[bytes], value: bytes | None) -> int:
    if value is None:
        return _write_protocol_line(stream, "-1")
    data = _encode_protocol_line(str(len(value))) + value
    stream.write(data)
    return len(data)


def _write_optional_protocol_byte_chunks(
    stream: IO[bytes],
    value: bytes | None,
    *,
    stream_chunk_bytes: int,
) -> tuple[int, int, int]:
    if value is None:
        return _write_protocol_line(stream, "-1"), 0, 0
    _validate_stream_chunk_bytes(stream_chunk_bytes)
    request_byte_count = _write_protocol_line(stream, str(len(value)))
    chunk_count = (
        (len(value) + stream_chunk_bytes - 1) // stream_chunk_bytes if value else 0
    )
    request_byte_count += _write_protocol_line(stream, str(chunk_count))
    max_chunk_bytes = 0
    view = memoryview(value)
    for offset in range(0, len(value), stream_chunk_bytes):
        chunk = view[offset : offset + stream_chunk_bytes]
        request_byte_count += _write_protocol_line(stream, str(len(chunk)))
        stream.write(chunk)
        request_byte_count += len(chunk)
        max_chunk_bytes = max(max_chunk_bytes, len(chunk))
    return request_byte_count, chunk_count, max_chunk_bytes


def _validate_stream_chunk_bytes(stream_chunk_bytes: int) -> None:
    if stream_chunk_bytes < 1:
        raise ValueError("Rust apply stream_chunk_bytes must be at least 1.")


def _workspace_apply_cli_content_arg(delta: WorkspaceApplyDelta) -> str | None:
    if delta.content_bytes is None:
        return delta.content_text
    if delta.content_text is not None:
        raise NativeApplyUnavailable(
            "Rust workspace apply CLI delta must provide either content_text or "
            "content_bytes, not both"
        )
    try:
        content = delta.content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise NativeApplyUnavailable(
            "Rust workspace apply CLI only accepts UTF-8 content arguments; "
            "use RustWorkspaceApplyService for binary payloads"
        ) from exc
    if "\x00" in content:
        raise NativeApplyUnavailable(
            "Rust workspace apply CLI cannot carry NUL bytes; use "
            "RustWorkspaceApplyService for binary payloads"
        )
    return content


def _raise_service_error_response(response: Mapping[str, Any]) -> None:
    if response.get("status") == "error":
        raise NativeApplyUnavailable(
            "Rust workspace apply service failed: "
            f"{str(response.get('message') or '').strip()}"
        )


def _stats(samples: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = sorted(
        float(sample[key])
        for sample in samples
        if isinstance(sample.get(key), int | float)
    )
    if not values:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "p95": None,
            "max": None,
        }
    return {
        "count": len(values),
        "min": values[0],
        "median": _median(values),
        "p95": _percentile_nearest_rank(values, 0.95),
        "max": values[-1],
    }


def _median(values: Sequence[float]) -> float:
    midpoint = len(values) // 2
    if len(values) % 2 == 1:
        return values[midpoint]
    return (values[midpoint - 1] + values[midpoint]) / 2


def _percentile_nearest_rank(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    rank = max(1, int(len(values) * percentile + 0.999999))
    return values[min(rank, len(values)) - 1]
