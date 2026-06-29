from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aware_file_system.benchmark_receipt_contract import (
    WORKSPACE_FS_BENCHMARK_VERSION,
)
from aware_file_system.native_apply import (
    WorkspaceApplyDelta,
    WorkspaceApplyReport,
    assert_workspace_apply_parity,
    collect_python_workspace_apply,
)
from aware_file_system.native_apply_executor import (
    DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES,
    RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_DEBUG_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
    RustWorkspaceApplyService,
    RustWorkspaceApplyExecutor,
    RustWorkspaceApplyExecutorConfig,
    RustWorkspaceApplyLibraryExecutor,
    RustWorkspaceApplyLibraryExecutorConfig,
    collect_prepared_rust_workspace_apply,
    collect_prepared_rust_workspace_apply_library,
    prepare_rust_workspace_apply_executor,
    prepare_rust_workspace_apply_library_executor,
    prepare_rust_workspace_apply_service_executor,
)


NATIVE_APPLY_BENCHMARK_VERSION = "aware.file_system.native_apply_benchmark.v1"
SYNTHETIC_APPLY_FIXTURE_MODE = "synthetic_apply_fixture"
RUST_INVOCATION_KIND = RUST_WORKSPACE_APPLY_DEBUG_INVOCATION_KIND
BALANCED_APPLY_FIXTURE_PROFILE = "balanced"
CUSTOM_APPLY_FIXTURE_PROFILE = "custom"
ApplyPayloadContentKind = Literal["text", "bytes"]


@dataclass(frozen=True, slots=True)
class NativeApplyBenchmarkConfig:
    files_per_operation: int = 16
    payload_bytes: int = 1024
    iterations: int = 3
    fixture_profile: str = BALANCED_APPLY_FIXTURE_PROFILE
    create_file_count: int | None = None
    update_file_count: int | None = None
    delete_file_count: int | None = None
    verify_digests: bool = True
    payload_content_kind: ApplyPayloadContentKind = "text"
    fixture_root: Path | None = None
    target_dir: Path | None = None
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    manifest_path: Path | None = None
    prepared_binary_path: Path | None = None
    prepared_service_binary_path: Path | None = None
    prepared_library_path: Path | None = None
    rust_library_backend: bool = False
    rust_service_backend: bool = False
    rust_service_streaming_payload: bool = False
    rust_service_direct_streaming_payload: bool = False
    rust_service_stream_chunk_bytes: int = DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES
    rust_service_compact_response: bool = False
    rust_service_server_timings: bool = False
    release: bool = False
    build_timeout_s: float = 240.0
    write_receipt: bool = False
    receipt_dir: Path | None = None


class ApplyBenchmarkStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0)
    min: float | None
    median: float | None
    p95: float | None
    max: float | None


class ApplyBenchmarkSample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iteration_index: int = Field(ge=0)
    duration_s: float = Field(ge=0)
    applied_path_count: int = Field(ge=0)
    bytes_written: int = Field(ge=0)
    bytes_deleted: int = Field(ge=0)
    digest_verified_count: int = Field(ge=0)
    stored_artifact_count: int = Field(ge=0)
    operations_per_second: float | None = Field(default=None, ge=0)
    bytes_written_per_second: float | None = Field(default=None, ge=0)
    phase_timings_s: dict[str, float] | None = None
    phase_counters: dict[str, int] | None = None
    content_engine: dict[str, Any] | None = None
    service_payload_protocol: str | None = None
    service_response_protocol: str | None = None
    service_request_handoff_protocol: str | None = None
    service_client_timings_s: dict[str, float] | None = None
    service_client_counters: dict[str, int] | None = None
    service_server_timings_s: dict[str, float] | None = None
    service_server_flags: dict[str, bool] | None = None
    library_boundary_kind: str | None = None
    digest_backend_kind: str | None = None


@dataclass(frozen=True, slots=True)
class NativeApplyFixtureShape:
    fixture_profile: str
    create_file_count: int
    update_file_count: int
    delete_file_count: int
    payload_bytes: int
    verify_digests: bool
    payload_content_kind: ApplyPayloadContentKind

    @property
    def expected_applied_path_count(self) -> int:
        return self.create_file_count + self.update_file_count + self.delete_file_count

    @property
    def expected_digest_verified_count(self) -> int:
        if not self.verify_digests:
            return 0
        return self.create_file_count + self.update_file_count


class ApplyBenchmarkBackendRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend_kind: Literal["python", "rust"]
    invocation_kind: str
    samples: list[ApplyBenchmarkSample]
    summary: dict[str, ApplyBenchmarkStats]


class ApplyBenchmarkParity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    sample_count: int = Field(ge=0)
    checked_fields: list[str]
    mismatches: list[str]


class NativeApplyBenchmarkReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_schema: Literal["aware.file_system.native_apply_benchmark.v1"]
    benchmark_version: Literal["aware.file_system.workspace_fs_benchmark.v1"]
    mode: Literal["synthetic_apply_fixture"]
    iteration_count: int = Field(ge=1)
    fixture_root: str = Field(min_length=1)
    target_dir: str = Field(min_length=1)
    fixture: dict[str, Any]
    python_backend: ApplyBenchmarkBackendRun
    rust_backend: ApplyBenchmarkBackendRun
    rust_library_backend: ApplyBenchmarkBackendRun | None = None
    rust_service_backend: ApplyBenchmarkBackendRun | None = None
    rust_build: dict[str, Any] | None = None
    rust_library_build: dict[str, Any] | None = None
    rust_library_execution: dict[str, Any] | None = None
    rust_service_build: dict[str, Any] | None = None
    rust_service_execution: dict[str, Any] | None = None
    rust_service_payload_protocol: str | None = None
    rust_service_response_protocol: str | None = None
    rust_service_request_handoff_protocol: str | None = None
    rust_service_timing_protocol: str | None = None
    parity: ApplyBenchmarkParity
    recommendation: dict[str, Any]
    receipt_path: str | None = None

    @model_validator(mode="after")
    def _validate_receipt_shape(self) -> NativeApplyBenchmarkReceipt:
        required_fixture_keys = {
            "files_per_operation",
            "payload_bytes",
            "expected_applied_path_count",
            "expected_stored_artifact_count",
        }
        missing = required_fixture_keys.difference(self.fixture)
        if missing:
            raise ValueError(
                "native apply fixture missing keys: " + ", ".join(sorted(missing))
            )
        for backend in (
            self.python_backend,
            self.rust_backend,
            self.rust_library_backend,
            self.rust_service_backend,
        ):
            if backend is None:
                continue
            if len(backend.samples) != self.iteration_count:
                raise ValueError(
                    f"{backend.backend_kind} sample count must equal iteration_count"
                )
            indexes = [sample.iteration_index for sample in backend.samples]
            if indexes != list(range(self.iteration_count)):
                raise ValueError(
                    f"{backend.backend_kind} samples must use contiguous indexes"
                )
            for key in ("duration_s",):
                stats = backend.summary.get(key)
                if stats is None or stats.count != self.iteration_count:
                    raise ValueError(
                        f"{backend.backend_kind} summary.{key} count mismatch"
                    )
        if self.parity.sample_count != self.iteration_count:
            raise ValueError("parity sample_count must equal iteration_count")
        if not self.parity.passed or self.parity.mismatches:
            raise ValueError("native apply benchmark requires passing parity")
        return self


def run_native_apply_benchmark(
    config: NativeApplyBenchmarkConfig | None = None,
) -> dict[str, Any]:
    resolved = config or NativeApplyBenchmarkConfig()
    _validate_config(resolved)
    if resolved.fixture_root is None:
        raise ValueError("Native apply benchmark requires an explicit fixture_root.")
    fixture_root = resolved.fixture_root.expanduser().resolve()
    _ensure_empty_or_missing(fixture_root)
    fixture_root.mkdir(parents=True, exist_ok=True)
    target_dir = (
        resolved.target_dir.expanduser().resolve()
        if resolved.target_dir is not None
        else fixture_root / ".cargo-target"
    )
    fixture_shape = _fixture_shape(resolved)
    rust_executor = prepare_rust_workspace_apply_executor(
        RustWorkspaceApplyExecutorConfig(
            cargo_path=resolved.cargo_path,
            cargo_home=resolved.cargo_home,
            manifest_path=resolved.manifest_path,
            target_dir=target_dir,
            prepared_binary_path=resolved.prepared_binary_path,
            release=resolved.release,
            build_timeout_s=resolved.build_timeout_s,
        )
    )
    service_executor = None
    library_executor = None
    rust_library_execution = None
    if resolved.rust_library_backend:
        library_executor = prepare_rust_workspace_apply_library_executor(
            RustWorkspaceApplyLibraryExecutorConfig(
                cargo_path=resolved.cargo_path,
                cargo_home=resolved.cargo_home,
                manifest_path=resolved.manifest_path,
                target_dir=target_dir,
                prepared_library_path=resolved.prepared_library_path,
                release=resolved.release,
                build_timeout_s=resolved.build_timeout_s,
            )
        )
        rust_library_execution = {
            "boundary_kind": library_executor.boundary_kind,
            "library_path": library_executor.library_path.as_posix(),
            "invocation_kind": library_executor.invocation_kind,
        }
    rust_service = None
    rust_service_execution = None
    if resolved.rust_service_backend:
        service_executor = prepare_rust_workspace_apply_service_executor(
            RustWorkspaceApplyExecutorConfig(
                cargo_path=resolved.cargo_path,
                cargo_home=resolved.cargo_home,
                manifest_path=resolved.manifest_path,
                target_dir=target_dir,
                prepared_binary_path=resolved.prepared_service_binary_path,
                release=resolved.release,
                build_timeout_s=resolved.build_timeout_s,
            )
        )
        rust_service = RustWorkspaceApplyService(service_executor).start()
        ping_started = time.perf_counter()
        ping_response = rust_service.ping()
        rust_service_execution = {
            "boundary_kind": "persistent_process",
            "process_started_once": True,
            "service_start_duration_s": rust_service.start_duration_s,
            "ping": {
                "duration_s": time.perf_counter() - ping_started,
                "response": ping_response,
            },
        }

    python_samples: list[dict[str, Any]] = []
    rust_samples: list[dict[str, Any]] = []
    rust_library_samples: list[dict[str, Any]] = []
    rust_service_samples: list[dict[str, Any]] = []
    mismatches: list[str] = []
    fixture = _fixture_metadata(config=resolved, shape=fixture_shape)
    try:
        for iteration_index in range(resolved.iterations):
            iteration_root = fixture_root / f"iteration_{iteration_index}"
            base_root = iteration_root / "base"
            python_root = iteration_root / "python"
            rust_root = iteration_root / "rust"
            rust_library_root = iteration_root / "rust_library"
            rust_service_root = iteration_root / "rust_service"
            deltas = _write_apply_fixture(
                root=base_root,
                shape=fixture_shape,
                iteration_index=iteration_index,
            )
            shutil.copytree(base_root, python_root)
            shutil.copytree(base_root, rust_root)
            if library_executor is not None:
                shutil.copytree(base_root, rust_library_root)
            if rust_service is not None:
                shutil.copytree(base_root, rust_service_root)

            python_report, python_duration = _measure_python_apply(
                root=python_root,
                deltas=deltas,
            )
            rust_report, rust_duration = _measure_rust_apply(
                root=rust_root,
                deltas=deltas,
                executor=rust_executor,
            )
            try:
                assert_workspace_apply_parity(
                    python_report=python_report,
                    rust_report=rust_report,
                )
            except AssertionError as exc:
                mismatches.append(f"rust cli iteration {iteration_index}: {exc}")

            python_samples.append(
                _sample_from_report(iteration_index, python_report, python_duration)
            )
            rust_samples.append(
                _sample_from_report(iteration_index, rust_report, rust_duration)
            )

            if library_executor is not None:
                library_report, library_duration = _measure_rust_library_apply(
                    root=rust_library_root,
                    deltas=deltas,
                    executor=library_executor,
                )
                try:
                    assert_workspace_apply_parity(
                        python_report=python_report,
                        rust_report=library_report,
                    )
                except AssertionError as exc:
                    mismatches.append(
                        f"rust library iteration {iteration_index}: {exc}"
                    )
                rust_library_samples.append(
                    _sample_from_report(
                        iteration_index,
                        library_report,
                        library_duration,
                        library_boundary_kind=library_executor.boundary_kind,
                    )
                )

            if rust_service is not None:
                (
                    service_report,
                    service_duration,
                    service_client_timings_s,
                    service_client_counters,
                    service_server_timings_s,
                    service_server_flags,
                    service_payload_protocol,
                    service_response_protocol,
                    service_request_handoff_protocol,
                ) = _measure_rust_service_apply(
                    root=rust_service_root,
                    deltas=deltas,
                    service=rust_service,
                    stream_payloads=resolved.rust_service_streaming_payload,
                    direct_stream_payloads=(
                        resolved.rust_service_direct_streaming_payload
                    ),
                    stream_chunk_bytes=resolved.rust_service_stream_chunk_bytes,
                    compact_response=resolved.rust_service_compact_response,
                    server_timings=resolved.rust_service_server_timings,
                )
                try:
                    assert_workspace_apply_parity(
                        python_report=python_report,
                        rust_report=service_report,
                    )
                except AssertionError as exc:
                    mismatches.append(
                        f"rust service iteration {iteration_index}: {exc}"
                    )
                rust_service_samples.append(
                    _sample_from_report(
                        iteration_index,
                        service_report,
                        service_duration,
                        service_client_timings_s=service_client_timings_s,
                        service_client_counters=service_client_counters,
                        service_server_timings_s=service_server_timings_s,
                        service_server_flags=service_server_flags,
                        service_payload_protocol=service_payload_protocol,
                        service_response_protocol=service_response_protocol,
                        service_request_handoff_protocol=(
                            service_request_handoff_protocol
                        ),
                    )
                )
    finally:
        if rust_service is not None:
            rust_service.close()

    receipt = {
        "receipt_schema": NATIVE_APPLY_BENCHMARK_VERSION,
        "benchmark_version": WORKSPACE_FS_BENCHMARK_VERSION,
        "mode": SYNTHETIC_APPLY_FIXTURE_MODE,
        "iteration_count": resolved.iterations,
        "fixture_root": fixture_root.as_posix(),
        "target_dir": target_dir.as_posix(),
        "fixture": fixture,
        "python_backend": {
            "backend_kind": "python",
            "invocation_kind": "in_process_python",
            "samples": python_samples,
            "summary": _backend_summary(python_samples),
        },
        "rust_backend": {
            "backend_kind": "rust",
            "invocation_kind": rust_executor.invocation_kind,
            "samples": rust_samples,
            "summary": _backend_summary(rust_samples),
        },
        "rust_build": rust_executor.rust_build,
        "rust_library_backend": (
            {
                "backend_kind": "rust",
                "invocation_kind": library_executor.invocation_kind,
                "samples": rust_library_samples,
                "summary": _backend_summary(rust_library_samples),
            }
            if library_executor is not None
            else None
        ),
        "rust_library_build": (
            library_executor.rust_build if library_executor is not None else None
        ),
        "rust_library_execution": rust_library_execution,
        "rust_service_backend": (
            {
                "backend_kind": "rust",
                "invocation_kind": service_executor.invocation_kind,
                "samples": rust_service_samples,
                "summary": _backend_summary(rust_service_samples),
            }
            if service_executor is not None
            else None
        ),
        "rust_service_build": (
            service_executor.rust_build if service_executor is not None else None
        ),
        "rust_service_execution": rust_service_execution,
        "rust_service_payload_protocol": (
            (
                RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
                if resolved.rust_service_direct_streaming_payload
                else (
                    RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
                    if resolved.rust_service_streaming_payload
                    else RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
                )
            )
            if service_executor is not None
            else None
        ),
        "rust_service_response_protocol": (
            (
                RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL
                if resolved.rust_service_compact_response
                else RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
            )
            if service_executor is not None
            else None
        ),
        "rust_service_request_handoff_protocol": (
            _first_sample_string(
                rust_service_samples,
                "service_request_handoff_protocol",
            )
            if service_executor is not None
            else None
        ),
        "rust_service_timing_protocol": (
            RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL
            if service_executor is not None and resolved.rust_service_server_timings
            else None
        ),
        "parity": {
            "passed": not mismatches,
            "sample_count": resolved.iterations,
            "checked_fields": [
                "entries",
                "bytes_written",
                "bytes_deleted",
                "digest_verified_count",
                "stored_artifact_count",
            ],
            "mismatches": mismatches,
        },
        "recommendation": {
            "rust_must_preserve": [
                "workspace-relative path safety",
                "create/update/delete apply semantics",
                "before/after SHA-256 receipt equality",
                "digest verification failures before routing changes",
            ],
            "rust_should_improve": [
                "batched materialized-output write duration",
                "digest verification throughput",
                "delete-heavy materialized cleanup duration",
                "persistent-service backend duration before native-library work",
                "streamed service payload duration and bounded client buffering",
                "compact service response receipts for many-small direct deltas",
                "server-side service timing split before binary/native-library routing",
                "native-library request-boundary receipts before default routing",
            ],
        },
    }
    validated = validate_native_apply_benchmark_receipt(receipt).model_dump(mode="json")
    return _maybe_write_receipt(receipt=validated, config=resolved, root=fixture_root)


def validate_native_apply_benchmark_receipt(
    receipt: Mapping[str, Any],
) -> NativeApplyBenchmarkReceipt:
    return NativeApplyBenchmarkReceipt.model_validate(dict(receipt))


def _measure_python_apply(
    *,
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
) -> tuple[WorkspaceApplyReport, float]:
    started = time.perf_counter()
    report = collect_python_workspace_apply(root, deltas)
    return report, time.perf_counter() - started


def _measure_rust_apply(
    *,
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    executor: RustWorkspaceApplyExecutor,
) -> tuple[WorkspaceApplyReport, float]:
    started = time.perf_counter()
    report = collect_prepared_rust_workspace_apply(root, deltas, executor=executor)
    duration = time.perf_counter() - started
    return report, duration


def _measure_rust_library_apply(
    *,
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    executor: RustWorkspaceApplyLibraryExecutor,
) -> tuple[WorkspaceApplyReport, float]:
    started = time.perf_counter()
    report = collect_prepared_rust_workspace_apply_library(
        root,
        deltas,
        executor=executor,
    )
    duration = time.perf_counter() - started
    return report, duration


def _measure_rust_service_apply(
    *,
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    service: RustWorkspaceApplyService,
    stream_payloads: bool,
    direct_stream_payloads: bool,
    stream_chunk_bytes: int,
    compact_response: bool,
    server_timings: bool,
) -> tuple[
    WorkspaceApplyReport,
    float,
    dict[str, float] | None,
    dict[str, int] | None,
    dict[str, float] | None,
    dict[str, bool] | None,
    str | None,
    str | None,
    str | None,
]:
    started = time.perf_counter()
    report = service.apply(
        root,
        deltas,
        stream_payloads=stream_payloads,
        direct_stream_payloads=direct_stream_payloads,
        stream_chunk_bytes=stream_chunk_bytes,
        compact_response=compact_response,
        server_timings=server_timings,
    )
    duration = time.perf_counter() - started
    return (
        report,
        duration,
        service.last_apply_client_timings_s,
        service.last_apply_client_counters,
        service.last_apply_server_timings_s,
        service.last_apply_server_flags,
        service.last_apply_client_protocol,
        service.last_apply_client_response_protocol,
        service.last_apply_client_request_handoff_protocol,
    )


def _write_apply_fixture(
    *,
    root: Path,
    shape: NativeApplyFixtureShape,
    iteration_index: int,
) -> tuple[WorkspaceApplyDelta, ...]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "aware.workspace.toml").write_text(
        '[workspace]\nname = "native-apply-benchmark"\n',
        encoding="utf-8",
    )
    deltas: list[WorkspaceApplyDelta] = []
    for index in range(shape.create_file_count):
        create_text = _payload(
            seed=f"create-{iteration_index}-{index}",
            payload_bytes=shape.payload_bytes,
        )
        create_bytes = create_text.encode("utf-8")
        deltas.append(
            WorkspaceApplyDelta(
                operation="create",
                path=f"generated/new/item_{index}.py",
                content_text=(
                    create_text if shape.payload_content_kind == "text" else None
                ),
                content_bytes=(
                    create_bytes if shape.payload_content_kind == "bytes" else None
                ),
                expected_sha256=_expected_digest(
                    content=create_bytes,
                    verify_digests=shape.verify_digests,
                ),
            )
        )

    for index in range(shape.update_file_count):
        update_path = root / "generated" / "existing" / f"item_{index}.py"
        update_path.parent.mkdir(parents=True, exist_ok=True)
        update_path.write_text(
            _payload(
                seed=f"old-{iteration_index}-{index}",
                payload_bytes=shape.payload_bytes,
            ),
            encoding="utf-8",
        )
        update_text = _payload(
            seed=f"update-{iteration_index}-{index}",
            payload_bytes=shape.payload_bytes,
        )
        update_bytes = update_text.encode("utf-8")
        deltas.append(
            WorkspaceApplyDelta(
                operation="update",
                path=f"generated/existing/item_{index}.py",
                content_text=(
                    update_text if shape.payload_content_kind == "text" else None
                ),
                content_bytes=(
                    update_bytes if shape.payload_content_kind == "bytes" else None
                ),
                expected_sha256=_expected_digest(
                    content=update_bytes,
                    verify_digests=shape.verify_digests,
                ),
            )
        )

    for index in range(shape.delete_file_count):
        delete_path = root / "generated" / "delete" / f"item_{index}.txt"
        delete_path.parent.mkdir(parents=True, exist_ok=True)
        delete_path.write_text(
            _payload(
                seed=f"delete-{iteration_index}-{index}",
                payload_bytes=shape.payload_bytes,
            ),
            encoding="utf-8",
        )
        deltas.append(
            WorkspaceApplyDelta(
                operation="delete",
                path=f"generated/delete/item_{index}.txt",
            )
        )
    return tuple(deltas)


def _fixture_metadata(
    *,
    config: NativeApplyBenchmarkConfig,
    shape: NativeApplyFixtureShape,
) -> dict[str, Any]:
    return {
        "fixture_profile": shape.fixture_profile,
        "files_per_operation": config.files_per_operation,
        "payload_bytes": shape.payload_bytes,
        "payload_content_kind": shape.payload_content_kind,
        "create_file_count": shape.create_file_count,
        "update_file_count": shape.update_file_count,
        "delete_file_count": shape.delete_file_count,
        "digest_verification_enabled": shape.verify_digests,
        "expected_applied_path_count": shape.expected_applied_path_count,
        "expected_digest_verified_count": shape.expected_digest_verified_count,
        "expected_written_file_count": (
            shape.create_file_count + shape.update_file_count
        ),
        "expected_deleted_file_count": shape.delete_file_count,
        "expected_stored_artifact_count": 0,
    }


def _sample_from_report(
    iteration_index: int,
    report: WorkspaceApplyReport,
    duration_s: float,
    *,
    service_client_timings_s: Mapping[str, float] | None = None,
    service_client_counters: Mapping[str, int] | None = None,
    service_server_timings_s: Mapping[str, float] | None = None,
    service_server_flags: Mapping[str, bool] | None = None,
    service_payload_protocol: str | None = None,
    service_response_protocol: str | None = None,
    service_request_handoff_protocol: str | None = None,
    library_boundary_kind: str | None = None,
) -> dict[str, Any]:
    sample: dict[str, Any] = {
        "iteration_index": iteration_index,
        "duration_s": duration_s,
        "applied_path_count": report.applied_path_count,
        "bytes_written": report.bytes_written,
        "bytes_deleted": report.bytes_deleted,
        "digest_verified_count": report.digest_verified_count,
        "stored_artifact_count": report.stored_artifact_count,
        "operations_per_second": _rate(report.applied_path_count, duration_s),
        "bytes_written_per_second": _rate(report.bytes_written, duration_s),
    }
    if report.digest_backend_kind:
        sample["digest_backend_kind"] = report.digest_backend_kind
    phase_timings_s = _phase_timings_seconds(report.phase_timings)
    if phase_timings_s:
        sample["phase_timings_s"] = phase_timings_s
    phase_counters = _phase_counters(report.phase_timings)
    if phase_counters:
        sample["phase_counters"] = phase_counters
    if report.content_engine:
        sample["content_engine"] = dict(report.content_engine)
    if service_payload_protocol:
        sample["service_payload_protocol"] = service_payload_protocol
    if service_response_protocol:
        sample["service_response_protocol"] = service_response_protocol
    if service_request_handoff_protocol:
        sample["service_request_handoff_protocol"] = service_request_handoff_protocol
    if library_boundary_kind:
        sample["library_boundary_kind"] = library_boundary_kind
    if service_client_timings_s:
        sample["service_client_timings_s"] = dict(service_client_timings_s)
    if service_client_counters:
        sample["service_client_counters"] = dict(service_client_counters)
    if service_server_timings_s:
        sample["service_server_timings_s"] = dict(service_server_timings_s)
    if service_server_flags:
        sample["service_server_flags"] = dict(service_server_flags)
    return sample


def _backend_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "duration_s": _stats(samples, "duration_s"),
        "operations_per_second": _stats(samples, "operations_per_second"),
        "bytes_written_per_second": _stats(samples, "bytes_written_per_second"),
    }
    for phase_name in _phase_timing_names(samples):
        phase_samples = [
            {"value": phase_timings[phase_name]}
            for sample in samples
            if isinstance((phase_timings := sample.get("phase_timings_s")), Mapping)
            and isinstance(phase_timings.get(phase_name), int | float)
        ]
        summary[f"phase_timings_s.{phase_name}"] = _stats(phase_samples, "value")
    for counter_name in _phase_counter_names(samples):
        counter_samples = [
            {"value": phase_counters[counter_name]}
            for sample in samples
            if isinstance((phase_counters := sample.get("phase_counters")), Mapping)
            and isinstance(phase_counters.get(counter_name), int | float)
        ]
        summary[f"phase_counters.{counter_name}"] = _stats(counter_samples, "value")
    for counter_name in _content_engine_counter_names(samples):
        counter_samples = [
            {"value": content_engine[counter_name]}
            for sample in samples
            if isinstance((content_engine := sample.get("content_engine")), Mapping)
            and _is_numeric_stat_value(content_engine.get(counter_name))
        ]
        summary[f"content_engine.{counter_name}"] = _stats(counter_samples, "value")
    for timing_name in _service_client_timing_names(samples):
        timing_samples = [
            {"value": service_timings[timing_name]}
            for sample in samples
            if isinstance(
                (service_timings := sample.get("service_client_timings_s")),
                Mapping,
            )
            and isinstance(service_timings.get(timing_name), int | float)
        ]
        summary[f"service_client_timings_s.{timing_name}"] = _stats(
            timing_samples,
            "value",
        )
    for counter_name in _service_client_counter_names(samples):
        counter_samples = [
            {"value": service_counters[counter_name]}
            for sample in samples
            if isinstance(
                (service_counters := sample.get("service_client_counters")),
                Mapping,
            )
            and isinstance(service_counters.get(counter_name), int | float)
        ]
        summary[f"service_client_counters.{counter_name}"] = _stats(
            counter_samples,
            "value",
        )
    for timing_name in _service_server_timing_names(samples):
        timing_samples = [
            {"value": service_timings[timing_name]}
            for sample in samples
            if isinstance(
                (service_timings := sample.get("service_server_timings_s")),
                Mapping,
            )
            and isinstance(service_timings.get(timing_name), int | float)
        ]
        summary[f"service_server_timings_s.{timing_name}"] = _stats(
            timing_samples,
            "value",
        )
    return summary


def _first_sample_string(
    samples: Sequence[Mapping[str, Any]],
    key: str,
) -> str | None:
    for sample in samples:
        value = sample.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _phase_timings_seconds(
    phase_timings: Mapping[str, Any] | None,
) -> dict[str, float]:
    if not phase_timings:
        return {}
    converted: dict[str, float] = {}
    for key, value in phase_timings.items():
        if key == "unit" or not key.endswith("_ns"):
            continue
        if not isinstance(value, int | float):
            continue
        converted[key.removesuffix("_ns") + "_s"] = float(value) / 1_000_000_000.0
    return converted


def _phase_counters(phase_timings: Mapping[str, Any] | None) -> dict[str, int]:
    if not phase_timings:
        return {}
    counters: dict[str, int] = {}
    for key, value in phase_timings.items():
        if not key.endswith("_count") or not isinstance(value, int | float):
            continue
        counters[key] = int(value)
    return counters


def _phase_timing_names(samples: list[dict[str, Any]]) -> tuple[str, ...]:
    names: set[str] = set()
    for sample in samples:
        phase_timings = sample.get("phase_timings_s")
        if isinstance(phase_timings, Mapping):
            names.update(
                key
                for key, value in phase_timings.items()
                if isinstance(value, int | float)
            )
    return tuple(sorted(names))


def _phase_counter_names(samples: list[dict[str, Any]]) -> tuple[str, ...]:
    names: set[str] = set()
    for sample in samples:
        phase_counters = sample.get("phase_counters")
        if isinstance(phase_counters, Mapping):
            names.update(
                key
                for key, value in phase_counters.items()
                if isinstance(value, int | float)
            )
    return tuple(sorted(names))


def _service_client_timing_names(samples: list[dict[str, Any]]) -> tuple[str, ...]:
    names: set[str] = set()
    for sample in samples:
        service_timings = sample.get("service_client_timings_s")
        if isinstance(service_timings, Mapping):
            names.update(
                key
                for key, value in service_timings.items()
                if isinstance(value, int | float)
            )
    return tuple(sorted(names))


def _content_engine_counter_names(samples: list[dict[str, Any]]) -> tuple[str, ...]:
    names: set[str] = set()
    for sample in samples:
        content_engine = sample.get("content_engine")
        if isinstance(content_engine, Mapping):
            names.update(
                key
                for key, value in content_engine.items()
                if _is_numeric_stat_value(value)
            )
    return tuple(sorted(names))


def _service_client_counter_names(samples: list[dict[str, Any]]) -> tuple[str, ...]:
    names: set[str] = set()
    for sample in samples:
        service_counters = sample.get("service_client_counters")
        if isinstance(service_counters, Mapping):
            names.update(
                key
                for key, value in service_counters.items()
                if isinstance(value, int | float)
            )
    return tuple(sorted(names))


def _service_server_timing_names(samples: list[dict[str, Any]]) -> tuple[str, ...]:
    names: set[str] = set()
    for sample in samples:
        service_timings = sample.get("service_server_timings_s")
        if isinstance(service_timings, Mapping):
            names.update(
                key
                for key, value in service_timings.items()
                if isinstance(value, int | float)
            )
    return tuple(sorted(names))


def _is_numeric_stat_value(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


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
        "median": float(median(values)),
        "p95": _percentile_nearest_rank(values, 0.95),
        "max": values[-1],
    }


def _rate(value: int, duration_s: float) -> float:
    if duration_s <= 0:
        return 0.0
    return float(value) / duration_s


def _percentile_nearest_rank(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    rank = max(1, int(len(values) * percentile + 0.999999))
    return values[min(rank, len(values)) - 1]


def _payload(*, seed: str, payload_bytes: int) -> str:
    base = f"# generated {seed}\nVALUE = {seed!r}\n"
    encoded_len = len(base.encode("utf-8"))
    if encoded_len >= payload_bytes:
        return base
    padding = "x" * max(payload_bytes - encoded_len, 0)
    return base + "# " + padding + "\n"


def _sha256_bytes(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest()


def _expected_digest(*, content: bytes, verify_digests: bool) -> str | None:
    if not verify_digests:
        return None
    return "sha256:" + _sha256_bytes(content)


def _fixture_shape(config: NativeApplyBenchmarkConfig) -> NativeApplyFixtureShape:
    default_count = config.files_per_operation
    return NativeApplyFixtureShape(
        fixture_profile=config.fixture_profile.strip() or CUSTOM_APPLY_FIXTURE_PROFILE,
        create_file_count=_resolved_operation_count(
            config.create_file_count,
            default_count=default_count,
            name="create_file_count",
        ),
        update_file_count=_resolved_operation_count(
            config.update_file_count,
            default_count=default_count,
            name="update_file_count",
        ),
        delete_file_count=_resolved_operation_count(
            config.delete_file_count,
            default_count=default_count,
            name="delete_file_count",
        ),
        payload_bytes=config.payload_bytes,
        verify_digests=config.verify_digests,
        payload_content_kind=config.payload_content_kind,
    )


def _resolved_operation_count(
    value: int | None,
    *,
    default_count: int,
    name: str,
) -> int:
    count = default_count if value is None else value
    if count < 0:
        raise ValueError(f"Native apply benchmark {name} must be non-negative.")
    return count


def _validate_config(config: NativeApplyBenchmarkConfig) -> None:
    if config.iterations < 1:
        raise ValueError("Native apply benchmark iterations must be at least 1.")
    if config.files_per_operation < 1:
        raise ValueError(
            "Native apply benchmark files_per_operation must be at least 1."
        )
    if config.payload_bytes < 1:
        raise ValueError("Native apply benchmark payload_bytes must be at least 1.")
    if (
        config.rust_service_streaming_payload
        and config.rust_service_direct_streaming_payload
    ):
        raise ValueError(
            "Native apply benchmark can use either temp-spool streaming or direct "
            "streaming, not both."
        )
    if config.payload_content_kind not in {"text", "bytes"}:
        raise ValueError(
            "Native apply benchmark payload_content_kind must be text or bytes."
        )
    streaming_enabled = (
        config.rust_service_streaming_payload
        or config.rust_service_direct_streaming_payload
    )
    if streaming_enabled and not config.rust_service_backend:
        raise ValueError(
            "Native apply benchmark streaming payload requires rust_service_backend."
        )
    if config.rust_service_compact_response and not config.rust_service_backend:
        raise ValueError(
            "Native apply benchmark compact response requires rust_service_backend."
        )
    if config.rust_service_server_timings and not config.rust_service_backend:
        raise ValueError(
            "Native apply benchmark server timings requires rust_service_backend."
        )
    if streaming_enabled and config.rust_service_stream_chunk_bytes < 1:
        raise ValueError(
            "Native apply benchmark rust_service_stream_chunk_bytes must be at least 1."
        )
    shape = _fixture_shape(config)
    if shape.expected_applied_path_count < 1:
        raise ValueError("Native apply benchmark requires at least one operation.")


def _ensure_empty_or_missing(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise ValueError(
            "Native apply benchmark fixture root must be empty: " f"{path}"
        )


def _maybe_write_receipt(
    *,
    receipt: dict[str, Any],
    config: NativeApplyBenchmarkConfig,
    root: Path,
) -> dict[str, Any]:
    if not config.write_receipt:
        return receipt
    receipt_dir = (
        config.receipt_dir.expanduser().resolve()
        if config.receipt_dir is not None
        else root / ".aware" / "reports" / "file_system" / "performance"
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{NATIVE_APPLY_BENCHMARK_VERSION}.{timestamp}.json"
    receipt_path = receipt_dir / filename
    receipt_with_path = {**receipt, "receipt_path": receipt_path.as_posix()}
    validate_native_apply_benchmark_receipt(receipt_with_path)
    receipt_path.write_text(
        json.dumps(receipt_with_path, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_with_path
