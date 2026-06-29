from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from aware_file_system.native_apply_benchmark import (
    ApplyPayloadContentKind,
    NativeApplyBenchmarkConfig,
    run_native_apply_benchmark,
)
from aware_file_system.native_apply_executor import (
    DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES,
    RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
    RustWorkspaceApplyExecutor,
    RustWorkspaceApplyExecutorConfig,
    RustWorkspaceApplyLibraryExecutor,
    RustWorkspaceApplyLibraryExecutorConfig,
    measure_rust_workspace_apply_persistent_boundary,
    measure_rust_workspace_apply_startup,
    prepare_rust_workspace_apply_executor,
    prepare_rust_workspace_apply_library_executor,
    prepare_rust_workspace_apply_service_executor,
)


NATIVE_APPLY_PROFILE_MATRIX_VERSION = "aware.file_system.native_apply_profile_matrix.v1"
DEFAULT_DIRECT_STREAM_CHUNK_SWEEP_BYTES = (
    4 * 1024,
    16 * 1024,
    64 * 1024,
    256 * 1024,
    1024 * 1024,
)


@dataclass(frozen=True, slots=True)
class NativeApplyProfileCase:
    name: str
    create_file_count: int
    update_file_count: int
    delete_file_count: int
    payload_bytes: int
    verify_digests: bool = True

    @property
    def operation_count(self) -> int:
        return self.create_file_count + self.update_file_count + self.delete_file_count


@dataclass(frozen=True, slots=True)
class NativeApplyProfileMatrixConfig:
    fixture_root: Path
    target_dir: Path | None = None
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    manifest_path: Path | None = None
    prepared_binary_path: Path | None = None
    prepared_service_binary_path: Path | None = None
    prepared_library_path: Path | None = None
    iterations: int = 5
    release: bool = False
    build_timeout_s: float = 240.0
    startup_iterations: int = 5
    persistent_boundary_probe: bool = False
    persistent_boundary_iterations: int = 5
    rust_library_backend: bool = False
    rust_service_backend: bool = False
    rust_service_streaming_payload: bool = False
    rust_service_direct_streaming_payload: bool = False
    rust_service_stream_chunk_bytes: int = DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES
    rust_service_compact_response: bool = False
    rust_service_server_timings: bool = False
    compare_service_payload_protocols: bool = False
    compare_direct_stream_chunk_sizes: bool = False
    direct_stream_chunk_size_bytes: tuple[int, ...] = ()
    payload_content_kind: ApplyPayloadContentKind = "text"
    case_names: tuple[str, ...] = ()
    write_receipt: bool = False
    receipt_dir: Path | None = None


def default_profile_cases() -> tuple[NativeApplyProfileCase, ...]:
    return (
        NativeApplyProfileCase(
            name="many_small_files",
            create_file_count=128,
            update_file_count=128,
            delete_file_count=32,
            payload_bytes=128,
            verify_digests=True,
        ),
        NativeApplyProfileCase(
            name="delete_heavy_cleanup",
            create_file_count=32,
            update_file_count=32,
            delete_file_count=256,
            payload_bytes=256,
            verify_digests=True,
        ),
        NativeApplyProfileCase(
            name="large_payloads",
            create_file_count=16,
            update_file_count=16,
            delete_file_count=4,
            payload_bytes=32 * 1024,
            verify_digests=True,
        ),
        NativeApplyProfileCase(
            name="many_small_files_no_digest",
            create_file_count=128,
            update_file_count=128,
            delete_file_count=32,
            payload_bytes=128,
            verify_digests=False,
        ),
    )


def run_native_apply_profile_matrix(
    config: NativeApplyProfileMatrixConfig,
) -> dict[str, Any]:
    _validate_config(config)
    fixture_root = config.fixture_root.expanduser().resolve()
    _ensure_empty_or_missing(fixture_root)
    fixture_root.mkdir(parents=True, exist_ok=True)
    target_dir = (
        config.target_dir.expanduser().resolve()
        if config.target_dir is not None
        else fixture_root / ".cargo-target"
    )
    cases = _selected_cases(config.case_names)
    root_executor = prepare_rust_workspace_apply_executor(
        RustWorkspaceApplyExecutorConfig(
            cargo_path=config.cargo_path,
            cargo_home=config.cargo_home,
            manifest_path=config.manifest_path,
            target_dir=target_dir,
            prepared_binary_path=config.prepared_binary_path,
            release=config.release,
            build_timeout_s=config.build_timeout_s,
        )
    )
    library_executor = None
    if config.rust_library_backend:
        library_executor = prepare_rust_workspace_apply_library_executor(
            RustWorkspaceApplyLibraryExecutorConfig(
                cargo_path=config.cargo_path,
                cargo_home=config.cargo_home,
                manifest_path=config.manifest_path,
                target_dir=target_dir,
                prepared_library_path=config.prepared_library_path,
                release=config.release,
                build_timeout_s=config.build_timeout_s,
            )
        )
    startup_probe = measure_rust_workspace_apply_startup(
        executor=root_executor,
        root=fixture_root / "startup_probe",
        iterations=config.startup_iterations,
    )
    persistent_boundary_probe = None
    service_executor = None
    service_backend_required = (
        config.persistent_boundary_probe
        or config.rust_service_backend
        or config.compare_service_payload_protocols
        or config.compare_direct_stream_chunk_sizes
    )
    if service_backend_required:
        service_executor = prepare_rust_workspace_apply_service_executor(
            RustWorkspaceApplyExecutorConfig(
                cargo_path=config.cargo_path,
                cargo_home=config.cargo_home,
                manifest_path=config.manifest_path,
                target_dir=target_dir,
                prepared_binary_path=config.prepared_service_binary_path,
                release=config.release,
                build_timeout_s=config.build_timeout_s,
            )
        )
    if config.persistent_boundary_probe:
        if service_executor is None:
            raise RuntimeError("persistent boundary probe requires a service executor")
        persistent_boundary_probe = measure_rust_workspace_apply_persistent_boundary(
            executor=service_executor,
            root=fixture_root / "persistent_boundary_probe",
            iterations=config.persistent_boundary_iterations,
        )

    case_summaries: list[dict[str, Any]] = []
    service_payload_protocol_comparisons: list[dict[str, Any]] = []
    direct_stream_chunk_size_comparisons: list[dict[str, Any]] = []
    for case in cases:
        if config.compare_direct_stream_chunk_sizes:
            if service_executor is None:
                raise RuntimeError(
                    "direct stream chunk-size comparison requires service executor"
                )
            comparison = _run_direct_stream_chunk_size_comparison(
                case=case,
                config=config,
                fixture_root=fixture_root,
                target_dir=target_dir,
                root_executor=root_executor,
                library_executor=library_executor,
                service_executor=service_executor,
            )
            direct_stream_chunk_size_comparisons.append(comparison)
            case_summaries.append(comparison["best_direct_streaming"])
            continue

        if config.compare_service_payload_protocols:
            if service_executor is None:
                raise RuntimeError(
                    "service payload comparison requires service executor"
                )
            comparison = _run_service_payload_protocol_comparison(
                case=case,
                config=config,
                fixture_root=fixture_root,
                target_dir=target_dir,
                root_executor=root_executor,
                library_executor=library_executor,
                service_executor=service_executor,
            )
            service_payload_protocol_comparisons.append(comparison)
            case_summaries.append(comparison["direct_streaming"])
            continue

        receipt = _run_case_benchmark(
            case=case,
            config=config,
            fixture_root=fixture_root / "cases" / case.name,
            target_dir=target_dir,
            root_executor=root_executor,
            library_executor=library_executor,
            service_executor=service_executor,
            rust_service_backend=config.rust_service_backend,
            rust_service_streaming_payload=config.rust_service_streaming_payload,
            rust_service_direct_streaming_payload=(
                config.rust_service_direct_streaming_payload
            ),
            receipt_dir=(
                _case_receipt_dir(fixture_root=fixture_root, case=case)
                if config.write_receipt
                else None
            ),
        )
        case_summaries.append(
            _case_summary(
                case=case,
                payload_content_kind=config.payload_content_kind,
                receipt=receipt,
                root_executor=root_executor,
            )
        )

    matrix_receipt = {
        "receipt_schema": NATIVE_APPLY_PROFILE_MATRIX_VERSION,
        "mode": "native_apply_profile_matrix",
        "fixture_root": fixture_root.as_posix(),
        "target_dir": target_dir.as_posix(),
        "iteration_count": config.iterations,
        "release": config.release,
        "service_payload_protocol_comparison_enabled": (
            config.compare_service_payload_protocols
        ),
        "direct_stream_chunk_size_comparison_enabled": (
            config.compare_direct_stream_chunk_sizes
        ),
        "service_stream_chunk_bytes": config.rust_service_stream_chunk_bytes,
        "service_response_protocol": (
            RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL
            if config.rust_service_compact_response
            else RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
        ),
        "service_timing_protocol": (
            RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL
            if config.rust_service_server_timings
            else None
        ),
        "direct_stream_chunk_size_bytes": list(_direct_stream_chunk_sizes(config)),
        "root_execution": {
            "prepared_once": True,
            "binary_path": root_executor.binary_path.as_posix(),
            "invocation_kind": root_executor.invocation_kind,
            "rust_build": root_executor.rust_build,
            "startup_probe": startup_probe,
            "rust_library_backend_enabled": config.rust_library_backend,
            "library_path": (
                library_executor.library_path.as_posix()
                if library_executor is not None
                else None
            ),
            "library_invocation_kind": (
                library_executor.invocation_kind
                if library_executor is not None
                else None
            ),
            "library_boundary_kind": (
                library_executor.boundary_kind if library_executor is not None else None
            ),
            "rust_library_build": (
                library_executor.rust_build if library_executor is not None else None
            ),
            "rust_service_backend_enabled": (
                config.rust_service_backend
                or config.compare_service_payload_protocols
                or config.compare_direct_stream_chunk_sizes
            ),
            "service_binary_path": (
                service_executor.binary_path.as_posix()
                if service_executor is not None
                else None
            ),
            "service_invocation_kind": (
                service_executor.invocation_kind
                if service_executor is not None
                else None
            ),
            "rust_service_build": (
                service_executor.rust_build if service_executor is not None else None
            ),
            "persistent_boundary_probe": persistent_boundary_probe,
        },
        "case_count": len(case_summaries),
        "cases": case_summaries,
        "service_payload_protocol_comparisons": (service_payload_protocol_comparisons),
        "direct_stream_chunk_size_comparisons": (direct_stream_chunk_size_comparisons),
        "analysis": _matrix_analysis(
            case_summaries,
            service_payload_protocol_comparisons,
            direct_stream_chunk_size_comparisons,
        ),
        "next_pass": {
            "root_installation": [
                "avoid per-call binary preparation",
                "prefer release prepared binary for profiling receipts",
                "measure process startup overhead separately from apply work",
            ],
            "rust_algorithms": [
                "batch file writes",
                "parallel or streaming SHA-256",
                "delete-heavy cleanup traversal",
                "native library or persistent service boundary",
            ],
        },
    }
    return _maybe_write_profile_receipt(
        receipt=matrix_receipt,
        config=config,
        fixture_root=fixture_root,
    )


def _matrix_analysis(
    case_summaries: Sequence[Mapping[str, Any]],
    service_payload_protocol_comparisons: Sequence[Mapping[str, Any]] = (),
    direct_stream_chunk_size_comparisons: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    slowest_service_case = _case_with_max(
        case_summaries,
        "rust_service_median_s",
    )
    worst_service_to_python_case = _case_with_max(
        case_summaries,
        "rust_service_to_python_duration_ratio",
    )
    worst_service_to_cli_case = _case_with_max(
        case_summaries,
        "rust_service_to_rust_cli_duration_ratio",
    )
    digest_delta = _many_small_digest_delta(case_summaries)
    apply_hotspots = _rust_apply_hotspot_analysis(case_summaries)
    request_boundary_profile = _request_boundary_profile_analysis(case_summaries)
    return {
        "slowest_rust_service_case": slowest_service_case,
        "worst_rust_service_to_python_ratio_case": worst_service_to_python_case,
        "worst_rust_service_to_rust_cli_ratio_case": worst_service_to_cli_case,
        "dominant_rust_service_phases": _dominant_service_phases(case_summaries),
        "many_small_digest_delta": digest_delta,
        "rust_apply_hotspots": apply_hotspots,
        "request_boundary_profile": request_boundary_profile,
        "service_payload_protocol_comparison": (
            _service_payload_protocol_matrix_analysis(
                service_payload_protocol_comparisons
            )
        ),
        "direct_stream_chunk_size_comparison": (
            _direct_stream_chunk_size_matrix_analysis(
                direct_stream_chunk_size_comparisons
            )
        ),
        "first_optimization_target": _first_optimization_target(
            slowest_service_case,
            digest_delta,
        ),
    }


def _run_case_benchmark(
    *,
    case: NativeApplyProfileCase,
    config: NativeApplyProfileMatrixConfig,
    fixture_root: Path,
    target_dir: Path,
    root_executor: RustWorkspaceApplyExecutor,
    library_executor: RustWorkspaceApplyLibraryExecutor | None,
    service_executor: RustWorkspaceApplyExecutor | None,
    rust_service_backend: bool,
    rust_service_streaming_payload: bool,
    rust_service_direct_streaming_payload: bool,
    rust_service_stream_chunk_bytes: int | None = None,
    receipt_dir: Path | None = None,
) -> dict[str, Any]:
    stream_chunk_bytes = (
        rust_service_stream_chunk_bytes
        if rust_service_stream_chunk_bytes is not None
        else config.rust_service_stream_chunk_bytes
    )
    return run_native_apply_benchmark(
        NativeApplyBenchmarkConfig(
            files_per_operation=1,
            payload_bytes=case.payload_bytes,
            iterations=config.iterations,
            fixture_profile=case.name,
            create_file_count=case.create_file_count,
            update_file_count=case.update_file_count,
            delete_file_count=case.delete_file_count,
            verify_digests=case.verify_digests,
            payload_content_kind=config.payload_content_kind,
            fixture_root=fixture_root,
            target_dir=target_dir,
            prepared_binary_path=root_executor.binary_path,
            prepared_library_path=(
                library_executor.library_path
                if library_executor is not None
                else config.prepared_library_path
            ),
            prepared_service_binary_path=(
                service_executor.binary_path
                if service_executor is not None
                else config.prepared_service_binary_path
            ),
            rust_library_backend=library_executor is not None,
            rust_service_backend=rust_service_backend,
            rust_service_streaming_payload=rust_service_streaming_payload,
            rust_service_direct_streaming_payload=(
                rust_service_direct_streaming_payload
            ),
            rust_service_stream_chunk_bytes=stream_chunk_bytes,
            rust_service_compact_response=config.rust_service_compact_response,
            rust_service_server_timings=config.rust_service_server_timings,
            manifest_path=config.manifest_path,
            release=config.release,
            write_receipt=config.write_receipt,
            receipt_dir=receipt_dir,
        )
    )


def _run_service_payload_protocol_comparison(
    *,
    case: NativeApplyProfileCase,
    config: NativeApplyProfileMatrixConfig,
    fixture_root: Path,
    target_dir: Path,
    root_executor: RustWorkspaceApplyExecutor,
    library_executor: RustWorkspaceApplyLibraryExecutor | None,
    service_executor: RustWorkspaceApplyExecutor,
) -> dict[str, Any]:
    buffered_receipt = _run_case_benchmark(
        case=case,
        config=config,
        fixture_root=fixture_root
        / "cases"
        / case.name
        / RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL,
        target_dir=target_dir,
        root_executor=root_executor,
        library_executor=library_executor,
        service_executor=service_executor,
        rust_service_backend=True,
        rust_service_streaming_payload=False,
        rust_service_direct_streaming_payload=False,
        receipt_dir=(
            _case_receipt_dir(
                fixture_root=fixture_root,
                case=case,
                protocol_label=RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL,
            )
            if config.write_receipt
            else None
        ),
    )
    streaming_receipt = _run_case_benchmark(
        case=case,
        config=config,
        fixture_root=fixture_root
        / "cases"
        / case.name
        / RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL,
        target_dir=target_dir,
        root_executor=root_executor,
        library_executor=library_executor,
        service_executor=service_executor,
        rust_service_backend=True,
        rust_service_streaming_payload=True,
        rust_service_direct_streaming_payload=False,
        receipt_dir=(
            _case_receipt_dir(
                fixture_root=fixture_root,
                case=case,
                protocol_label=RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL,
            )
            if config.write_receipt
            else None
        ),
    )
    direct_streaming_receipt = _run_case_benchmark(
        case=case,
        config=config,
        fixture_root=fixture_root
        / "cases"
        / case.name
        / RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
        target_dir=target_dir,
        root_executor=root_executor,
        library_executor=library_executor,
        service_executor=service_executor,
        rust_service_backend=True,
        rust_service_streaming_payload=False,
        rust_service_direct_streaming_payload=True,
        receipt_dir=(
            _case_receipt_dir(
                fixture_root=fixture_root,
                case=case,
                protocol_label=(
                    RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
                ),
            )
            if config.write_receipt
            else None
        ),
    )
    buffered = _case_summary(
        case=case,
        payload_content_kind=config.payload_content_kind,
        receipt=buffered_receipt,
        root_executor=root_executor,
    )
    streaming = _case_summary(
        case=case,
        payload_content_kind=config.payload_content_kind,
        receipt=streaming_receipt,
        root_executor=root_executor,
    )
    direct_streaming = _case_summary(
        case=case,
        payload_content_kind=config.payload_content_kind,
        receipt=direct_streaming_receipt,
        root_executor=root_executor,
    )
    comparison = _service_payload_protocol_case_comparison(
        case_name=case.name,
        buffered=buffered,
        streaming=streaming,
        direct_streaming=direct_streaming,
    )
    return {
        "case_name": case.name,
        "fixture": direct_streaming["fixture"],
        "buffered": buffered,
        "streaming": streaming,
        "direct_streaming": direct_streaming,
        "comparison": comparison,
    }


def _run_direct_stream_chunk_size_comparison(
    *,
    case: NativeApplyProfileCase,
    config: NativeApplyProfileMatrixConfig,
    fixture_root: Path,
    target_dir: Path,
    root_executor: RustWorkspaceApplyExecutor,
    library_executor: RustWorkspaceApplyLibraryExecutor | None,
    service_executor: RustWorkspaceApplyExecutor,
) -> dict[str, Any]:
    buffered_receipt = _run_case_benchmark(
        case=case,
        config=config,
        fixture_root=fixture_root
        / "cases"
        / case.name
        / "direct_stream_chunk_size_sweep"
        / RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL,
        target_dir=target_dir,
        root_executor=root_executor,
        library_executor=library_executor,
        service_executor=service_executor,
        rust_service_backend=True,
        rust_service_streaming_payload=False,
        rust_service_direct_streaming_payload=False,
        receipt_dir=(
            _case_receipt_dir(
                fixture_root=fixture_root,
                case=case,
                protocol_label=(
                    "direct_stream_chunk_size_sweep"
                    f"/{RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL}"
                ),
            )
            if config.write_receipt
            else None
        ),
    )
    temp_spool_receipt = _run_case_benchmark(
        case=case,
        config=config,
        fixture_root=fixture_root
        / "cases"
        / case.name
        / "direct_stream_chunk_size_sweep"
        / RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
        / f"chunk_{config.rust_service_stream_chunk_bytes}",
        target_dir=target_dir,
        root_executor=root_executor,
        library_executor=library_executor,
        service_executor=service_executor,
        rust_service_backend=True,
        rust_service_streaming_payload=True,
        rust_service_direct_streaming_payload=False,
        receipt_dir=(
            _case_receipt_dir(
                fixture_root=fixture_root,
                case=case,
                protocol_label=(
                    "direct_stream_chunk_size_sweep/"
                    f"{RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL}/"
                    f"chunk_{config.rust_service_stream_chunk_bytes}"
                ),
            )
            if config.write_receipt
            else None
        ),
    )
    buffered = _case_summary(
        case=case,
        payload_content_kind=config.payload_content_kind,
        receipt=buffered_receipt,
        root_executor=root_executor,
    )
    temp_spool = _case_summary(
        case=case,
        payload_content_kind=config.payload_content_kind,
        receipt=temp_spool_receipt,
        root_executor=root_executor,
    )
    temp_spool["stream_chunk_bytes"] = config.rust_service_stream_chunk_bytes

    direct_summaries: list[dict[str, Any]] = []
    for chunk_bytes in _direct_stream_chunk_sizes(config):
        direct_receipt = _run_case_benchmark(
            case=case,
            config=config,
            fixture_root=fixture_root
            / "cases"
            / case.name
            / "direct_stream_chunk_size_sweep"
            / RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
            / f"chunk_{chunk_bytes}",
            target_dir=target_dir,
            root_executor=root_executor,
            library_executor=library_executor,
            service_executor=service_executor,
            rust_service_backend=True,
            rust_service_streaming_payload=False,
            rust_service_direct_streaming_payload=True,
            rust_service_stream_chunk_bytes=chunk_bytes,
            receipt_dir=(
                _case_receipt_dir(
                    fixture_root=fixture_root,
                    case=case,
                    protocol_label=(
                        "direct_stream_chunk_size_sweep/"
                        f"{RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL}/"
                        f"chunk_{chunk_bytes}"
                    ),
                )
                if config.write_receipt
                else None
            ),
        )
        direct = _case_summary(
            case=case,
            payload_content_kind=config.payload_content_kind,
            receipt=direct_receipt,
            root_executor=root_executor,
        )
        direct["direct_stream_chunk_bytes"] = chunk_bytes
        direct_summaries.append(direct)

    comparison = _direct_stream_chunk_size_case_comparison(
        case_name=case.name,
        buffered=buffered,
        temp_spool=temp_spool,
        direct_summaries=direct_summaries,
    )
    best_direct = _direct_summary_for_chunk(
        direct_summaries,
        _mapping_value(
            comparison.get("best_direct_streaming_chunk_result"), "chunk_bytes"
        ),
    )
    return {
        "case_name": case.name,
        "fixture": (best_direct or direct_summaries[0])["fixture"],
        "buffered": buffered,
        "temp_spool_streaming": temp_spool,
        "direct_streaming_by_chunk_size": direct_summaries,
        "best_direct_streaming": best_direct or direct_summaries[0],
        "comparison": comparison,
    }


def _case_with_max(
    case_summaries: Sequence[Mapping[str, Any]],
    metric: str,
) -> dict[str, Any] | None:
    selected: Mapping[str, Any] | None = None
    selected_value: float | None = None
    for case in case_summaries:
        value = _float_value(case.get(metric))
        if value is None:
            continue
        if selected_value is None or value > selected_value:
            selected = case
            selected_value = value
    if selected is None or selected_value is None:
        return None
    return {
        "case_name": _optional_string(selected.get("case_name")),
        "metric": metric,
        "value": selected_value,
        "rust_algorithm_hint": _rust_algorithm_hint(
            _optional_string(selected.get("case_name"))
        ),
    }


def _many_small_digest_delta(
    case_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    by_name = {
        str(case.get("case_name")): case
        for case in case_summaries
        if case.get("case_name") is not None
    }
    with_digest = _float_value(
        by_name.get("many_small_files", {}).get("rust_service_median_s")
    )
    without_digest = _float_value(
        by_name.get("many_small_files_no_digest", {}).get("rust_service_median_s")
    )
    if with_digest is None or without_digest is None:
        return None
    return {
        "case_name": "many_small_files",
        "with_digest_rust_service_median_s": with_digest,
        "without_digest_rust_service_median_s": without_digest,
        "digest_cost_s": with_digest - without_digest,
        "with_to_without_digest_ratio": _ratio(with_digest, without_digest),
    }


def _rust_apply_hotspot_analysis(
    case_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    cases = [
        hotspot
        for case in case_summaries
        if (hotspot := _rust_apply_case_hotspot(case)) is not None
    ]
    highest_leaf_open_share = _hotspot_case_with_max(
        cases,
        "target_leaf_open_share_of_service_duration",
    )
    highest_direct_read_share = _hotspot_case_with_max(
        cases,
        "direct_stream_read_share_of_service_duration",
    )
    highest_file_write_share = _hotspot_case_with_max(
        cases,
        "direct_stream_file_write_share_of_service_duration",
    )
    highest_hash_write_share = _hotspot_case_with_max(
        cases,
        "direct_stream_hash_share_of_write_phase",
    )
    return {
        "case_count": len(cases),
        "cases": cases,
        "highest_target_leaf_open_share_case": highest_leaf_open_share,
        "highest_direct_stream_read_share_case": highest_direct_read_share,
        "highest_direct_stream_file_write_share_case": highest_file_write_share,
        "highest_direct_stream_hash_share_of_write_phase_case": (
            highest_hash_write_share
        ),
        "recommendation": _rust_apply_hotspot_recommendation(
            highest_leaf_open_share=highest_leaf_open_share,
            highest_direct_read_share=highest_direct_read_share,
            highest_file_write_share=highest_file_write_share,
            highest_hash_write_share=highest_hash_write_share,
        ),
    }


def _rust_apply_case_hotspot(case: Mapping[str, Any]) -> dict[str, Any] | None:
    phase_medians = _mapping_or_empty(case.get("rust_service_phase_medians_s"))
    phase_counters = _mapping_or_empty(case.get("rust_service_phase_counters"))
    content_engine = _mapping_or_empty(case.get("rust_service_content_engine"))
    service_median_s = _float_value(case.get("rust_service_median_s"))
    if service_median_s is None:
        return None

    target_leaf_safety_s = _float_value(
        _mapping_value(phase_medians, "target_leaf_safety_s")
    )
    target_leaf_name_encode_s = _float_value(
        _mapping_value(phase_medians, "target_leaf_name_encode_s")
    )
    target_leaf_open_s = _float_value(
        _mapping_value(phase_medians, "target_leaf_open_s")
    )
    target_leaf_open_count = _float_value(
        _mapping_value(phase_counters, "target_leaf_open_count")
    )
    write_s = _float_value(_mapping_value(phase_medians, "write_s"))
    direct_stream_read_s = _float_value(
        _mapping_value(phase_medians, "direct_stream_read_s")
    )
    direct_stream_file_write_s = _float_value(
        _mapping_value(phase_medians, "direct_stream_file_write_s")
    )
    direct_stream_hash_s = _float_value(
        _mapping_value(phase_medians, "direct_stream_hash_s")
    )
    bytes_direct_streamed = _float_value(
        _mapping_value(content_engine, "bytes_direct_streamed")
    )
    return {
        "case_name": _optional_string(case.get("case_name")),
        "rust_service_median_s": service_median_s,
        "target_leaf_safety_median_s": target_leaf_safety_s,
        "target_leaf_name_encode_median_s": target_leaf_name_encode_s,
        "target_leaf_open_median_s": target_leaf_open_s,
        "target_leaf_open_count": target_leaf_open_count,
        "target_leaf_open_average_s": _ratio(
            target_leaf_open_s,
            target_leaf_open_count,
        ),
        "target_leaf_open_share_of_leaf_safety": _ratio(
            target_leaf_open_s,
            target_leaf_safety_s,
        ),
        "target_leaf_name_encode_share_of_leaf_safety": _ratio(
            target_leaf_name_encode_s,
            target_leaf_safety_s,
        ),
        "target_leaf_safety_share_of_service_duration": _ratio(
            target_leaf_safety_s,
            service_median_s,
        ),
        "target_leaf_open_share_of_service_duration": _ratio(
            target_leaf_open_s,
            service_median_s,
        ),
        "write_phase_median_s": write_s,
        "direct_stream_read_median_s": direct_stream_read_s,
        "direct_stream_read_share_of_service_duration": _ratio(
            direct_stream_read_s,
            service_median_s,
        ),
        "direct_stream_file_write_median_s": direct_stream_file_write_s,
        "direct_stream_file_write_share_of_service_duration": _ratio(
            direct_stream_file_write_s,
            service_median_s,
        ),
        "direct_stream_hash_median_s": direct_stream_hash_s,
        "direct_stream_hash_share_of_write_phase": _ratio(
            direct_stream_hash_s,
            write_s,
        ),
        "direct_stream_hash_share_of_service_duration": _ratio(
            direct_stream_hash_s,
            service_median_s,
        ),
        "direct_stream_hash_bytes_per_second": _bytes_per_second(
            bytes_direct_streamed,
            direct_stream_hash_s,
        ),
    }


def _hotspot_case_with_max(
    hotspots: Sequence[Mapping[str, Any]],
    metric: str,
) -> dict[str, Any] | None:
    selected: Mapping[str, Any] | None = None
    selected_value: float | None = None
    for hotspot in hotspots:
        value = _float_value(hotspot.get(metric))
        if value is None:
            continue
        if selected_value is None or value > selected_value:
            selected = hotspot
            selected_value = value
    if selected is None or selected_value is None:
        return None
    return {
        "case_name": _optional_string(selected.get("case_name")),
        "metric": metric,
        "value": selected_value,
    }


def _rust_apply_hotspot_recommendation(
    *,
    highest_leaf_open_share: Mapping[str, Any] | None,
    highest_direct_read_share: Mapping[str, Any] | None,
    highest_file_write_share: Mapping[str, Any] | None,
    highest_hash_write_share: Mapping[str, Any] | None,
) -> str:
    leaf_share = _float_value(
        highest_leaf_open_share.get("value")
        if isinstance(highest_leaf_open_share, Mapping)
        else None
    )
    read_share = _float_value(
        highest_direct_read_share.get("value")
        if isinstance(highest_direct_read_share, Mapping)
        else None
    )
    file_write_share = _float_value(
        highest_file_write_share.get("value")
        if isinstance(highest_file_write_share, Mapping)
        else None
    )
    hash_write_share = _float_value(
        highest_hash_write_share.get("value")
        if isinstance(highest_hash_write_share, Mapping)
        else None
    )
    if leaf_share is not None and leaf_share >= 0.25:
        return (
            "target leaf open/openat is a first-class many-small hotspot; keep "
            "O_NOFOLLOW safety and evaluate batching or native library request "
            "routing before changing semantics"
        )
    if read_share is not None and read_share >= 0.25:
        return (
            "direct-stream request ingestion is a first-class boundary hotspot; "
            "optimize chunk framing and native/zero-copy boundary before tuning "
            "file writes"
        )
    if hash_write_share is not None and hash_write_share >= 0.50:
        return (
            "SHA verification dominates direct write time; target digest "
            "throughput while preserving expected digest validation"
        )
    if file_write_share is not None and file_write_share >= 0.25:
        return (
            "direct file writes are a visible service-duration share; evaluate "
            "larger chunks and platform-specific write strategy next"
        )
    return (
        "no single Rust apply subphase dominates the current matrix; collect "
        "larger release receipts before replacing the service boundary"
    )


def _first_optimization_target(
    slowest_service_case: Mapping[str, Any] | None,
    digest_delta: Mapping[str, Any] | None,
) -> dict[str, Any]:
    case_name = _optional_string(
        slowest_service_case.get("case_name") if slowest_service_case else None
    )
    reason = "highest rust_service_median_s in the profile matrix"
    if digest_delta is not None:
        ratio = _float_value(digest_delta.get("with_to_without_digest_ratio"))
        if ratio is not None and ratio >= 1.5:
            return {
                "case_name": "many_small_files",
                "focus": "digest verification overhead",
                "reason": (
                    "many-small digest-enabled service median is at least 1.5x "
                    "the no-digest service median"
                ),
            }
    return {
        "case_name": case_name,
        "focus": _rust_algorithm_hint(case_name),
        "reason": reason,
    }


def _rust_algorithm_hint(case_name: str | None) -> str:
    if case_name == "large_payloads":
        return "streaming write and SHA-256 throughput"
    if case_name == "delete_heavy_cleanup":
        return "delete-heavy cleanup and file metadata handling"
    if case_name == "many_small_files_no_digest":
        return "small-file write/delete overhead without digest cost"
    if case_name == "many_small_files":
        return "small-file write/delete plus digest verification overhead"
    return "receipt-backed Rust apply hot path"


def _case_summary(
    *,
    case: NativeApplyProfileCase,
    payload_content_kind: str,
    receipt: Mapping[str, Any],
    root_executor: RustWorkspaceApplyExecutor,
) -> dict[str, Any]:
    python_backend = _mapping_value(receipt, "python_backend")
    rust_backend = _mapping_value(receipt, "rust_backend")
    rust_library_backend = _mapping_value(receipt, "rust_library_backend")
    rust_service_backend = _mapping_value(receipt, "rust_service_backend")
    python_summary = _mapping_value(python_backend, "summary")
    rust_summary = _mapping_value(rust_backend, "summary")
    rust_library_summary = _mapping_value(rust_library_backend, "summary")
    rust_service_summary = _mapping_value(rust_service_backend, "summary")
    python_median_s = _summary_median(python_summary, "duration_s")
    rust_median_s = _summary_median(rust_summary, "duration_s")
    rust_library_median_s = _summary_median(rust_library_summary, "duration_s")
    rust_service_median_s = _summary_median(rust_service_summary, "duration_s")
    return {
        "case_name": case.name,
        "fixture": {
            "create_file_count": case.create_file_count,
            "update_file_count": case.update_file_count,
            "delete_file_count": case.delete_file_count,
            "payload_bytes": case.payload_bytes,
            "payload_content_kind": payload_content_kind,
            "verify_digests": case.verify_digests,
            "operation_count": case.operation_count,
        },
        "applied_path_count": case.operation_count,
        "benchmark_receipt_path": _optional_string(receipt.get("receipt_path")),
        "rust_invocation_kind": root_executor.invocation_kind,
        "benchmark_rust_invocation_kind": _optional_string(
            _mapping_value(rust_backend, "invocation_kind")
        ),
        "benchmark_rust_library_invocation_kind": _optional_string(
            _mapping_value(rust_library_backend, "invocation_kind")
        ),
        "rust_library_boundary_kind": (
            _optional_string(
                _mapping_value(receipt.get("rust_library_execution"), "boundary_kind")
            )
            or _backend_library_boundary_kind(rust_library_backend)
        ),
        "benchmark_rust_service_invocation_kind": _optional_string(
            _mapping_value(rust_service_backend, "invocation_kind")
        ),
        "rust_service_payload_protocol": _optional_string(
            receipt.get("rust_service_payload_protocol")
        ),
        "rust_service_response_protocol": _optional_string(
            receipt.get("rust_service_response_protocol")
        ),
        "rust_service_request_handoff_protocol": (
            _optional_string(receipt.get("rust_service_request_handoff_protocol"))
            or _backend_request_handoff_protocol(rust_service_backend)
        ),
        "rust_digest_backend_kind": _backend_digest_kind(rust_backend),
        "rust_library_digest_backend_kind": _backend_digest_kind(rust_library_backend),
        "rust_service_digest_backend_kind": _backend_digest_kind(rust_service_backend),
        "rust_service_timing_protocol": _optional_string(
            receipt.get("rust_service_timing_protocol")
        ),
        "python_median_s": python_median_s,
        "rust_median_s": rust_median_s,
        "rust_library_median_s": rust_library_median_s,
        "rust_service_median_s": rust_service_median_s,
        "rust_to_python_duration_ratio": _ratio(rust_median_s, python_median_s),
        "rust_library_to_python_duration_ratio": _ratio(
            rust_library_median_s,
            python_median_s,
        ),
        "rust_library_to_rust_cli_duration_ratio": _ratio(
            rust_library_median_s,
            rust_median_s,
        ),
        "rust_service_to_rust_library_duration_ratio": _ratio(
            rust_service_median_s,
            rust_library_median_s,
        ),
        "rust_service_to_python_duration_ratio": _ratio(
            rust_service_median_s,
            python_median_s,
        ),
        "rust_service_to_rust_cli_duration_ratio": _ratio(
            rust_service_median_s,
            rust_median_s,
        ),
        "python_operations_per_second_median": _summary_median(
            python_summary,
            "operations_per_second",
        ),
        "rust_operations_per_second_median": _summary_median(
            rust_summary,
            "operations_per_second",
        ),
        "rust_library_operations_per_second_median": _summary_median(
            rust_library_summary,
            "operations_per_second",
        ),
        "rust_service_operations_per_second_median": _summary_median(
            rust_service_summary,
            "operations_per_second",
        ),
        "python_bytes_written_per_second_median": _summary_median(
            python_summary,
            "bytes_written_per_second",
        ),
        "rust_bytes_written_per_second_median": _summary_median(
            rust_summary,
            "bytes_written_per_second",
        ),
        "rust_library_bytes_written_per_second_median": _summary_median(
            rust_library_summary,
            "bytes_written_per_second",
        ),
        "rust_service_bytes_written_per_second_median": _summary_median(
            rust_service_summary,
            "bytes_written_per_second",
        ),
        "rust_phase_medians_s": _phase_medians(rust_summary),
        "rust_library_phase_medians_s": _phase_medians(rust_library_summary),
        "rust_service_phase_medians_s": _phase_medians(rust_service_summary),
        "rust_service_phase_counters": _phase_counters(rust_service_summary),
        "rust_service_content_engine": _content_engine_counters(
            rust_service_summary,
        ),
        "rust_service_client_medians_s": _service_client_medians(
            rust_service_summary,
        ),
        "rust_service_client_counters": _service_client_counters(
            rust_service_summary,
        ),
        "rust_service_server_medians_s": _service_server_medians(
            rust_service_summary,
        ),
        "dominant_rust_service_phase": _dominant_phase(
            _phase_medians(rust_service_summary),
        ),
        "parity_passed": bool(
            _mapping_value(_mapping_value(receipt, "parity"), "passed")
        ),
    }


def _backend_digest_kind(backend: object) -> str | None:
    if not isinstance(backend, Mapping):
        return None
    mapping = backend
    samples = _list_value(mapping.get("samples"))
    for sample in samples:
        if isinstance(sample, Mapping):
            value = _optional_string(sample.get("digest_backend_kind"))
            if value:
                return value
    return None


def _backend_request_handoff_protocol(backend: object) -> str | None:
    if not isinstance(backend, Mapping):
        return None
    samples = _list_value(backend.get("samples"))
    for sample in samples:
        if isinstance(sample, Mapping):
            value = _optional_string(sample.get("service_request_handoff_protocol"))
            if value:
                return value
    return None


def _backend_library_boundary_kind(backend: object) -> str | None:
    if not isinstance(backend, Mapping):
        return None
    samples = _list_value(backend.get("samples"))
    for sample in samples:
        if isinstance(sample, Mapping):
            value = _optional_string(sample.get("library_boundary_kind"))
            if value:
                return value
    return None


def _service_payload_protocol_case_comparison(
    *,
    case_name: str,
    buffered: Mapping[str, Any],
    streaming: Mapping[str, Any],
    direct_streaming: Mapping[str, Any],
) -> dict[str, Any]:
    buffered_service_median_s = _float_value(buffered.get("rust_service_median_s"))
    streaming_service_median_s = _float_value(streaming.get("rust_service_median_s"))
    direct_service_median_s = _float_value(
        direct_streaming.get("rust_service_median_s")
    )
    buffered_request_write_s = _float_value(
        _mapping_value(buffered.get("rust_service_client_medians_s"), "request_write_s")
    )
    streaming_request_write_s = _float_value(
        _mapping_value(
            streaming.get("rust_service_client_medians_s"), "request_write_s"
        )
    )
    direct_request_write_s = _float_value(
        _mapping_value(
            direct_streaming.get("rust_service_client_medians_s"),
            "request_write_s",
        )
    )
    return {
        "case_name": case_name,
        "buffered_protocol": buffered.get("rust_service_payload_protocol"),
        "streaming_protocol": streaming.get("rust_service_payload_protocol"),
        "direct_streaming_protocol": direct_streaming.get(
            "rust_service_payload_protocol"
        ),
        "buffered_request_handoff_protocol": buffered.get(
            "rust_service_request_handoff_protocol"
        ),
        "streaming_request_handoff_protocol": streaming.get(
            "rust_service_request_handoff_protocol"
        ),
        "direct_streaming_request_handoff_protocol": direct_streaming.get(
            "rust_service_request_handoff_protocol"
        ),
        "buffered_rust_service_median_s": buffered_service_median_s,
        "streaming_rust_service_median_s": streaming_service_median_s,
        "direct_streaming_rust_service_median_s": direct_service_median_s,
        "streaming_to_buffered_rust_service_duration_ratio": _ratio(
            streaming_service_median_s,
            buffered_service_median_s,
        ),
        "direct_streaming_to_buffered_rust_service_duration_ratio": _ratio(
            direct_service_median_s,
            buffered_service_median_s,
        ),
        "direct_streaming_to_temp_spool_streaming_duration_ratio": _ratio(
            direct_service_median_s,
            streaming_service_median_s,
        ),
        "streaming_minus_buffered_rust_service_duration_s": _delta(
            streaming_service_median_s,
            buffered_service_median_s,
        ),
        "direct_streaming_minus_buffered_rust_service_duration_s": _delta(
            direct_service_median_s,
            buffered_service_median_s,
        ),
        "direct_streaming_minus_temp_spool_streaming_duration_s": _delta(
            direct_service_median_s,
            streaming_service_median_s,
        ),
        "buffered_request_write_median_s": buffered_request_write_s,
        "streaming_request_write_median_s": streaming_request_write_s,
        "direct_streaming_request_write_median_s": direct_request_write_s,
        "streaming_minus_buffered_request_write_s": _delta(
            streaming_request_write_s,
            buffered_request_write_s,
        ),
        "direct_streaming_minus_buffered_request_write_s": _delta(
            direct_request_write_s,
            buffered_request_write_s,
        ),
        "direct_streaming_minus_temp_spool_streaming_request_write_s": _delta(
            direct_request_write_s,
            streaming_request_write_s,
        ),
        "buffered_content_engine": buffered.get("rust_service_content_engine"),
        "streaming_content_engine": streaming.get("rust_service_content_engine"),
        "direct_streaming_content_engine": direct_streaming.get(
            "rust_service_content_engine"
        ),
        "buffered_client_counters": buffered.get("rust_service_client_counters"),
        "streaming_client_counters": streaming.get("rust_service_client_counters"),
        "direct_streaming_client_counters": direct_streaming.get(
            "rust_service_client_counters"
        ),
        "recommendation": _service_payload_protocol_case_recommendation(
            case_name=case_name,
            streaming_to_buffered_ratio=_ratio(
                streaming_service_median_s,
                buffered_service_median_s,
            ),
            direct_to_buffered_ratio=_ratio(
                direct_service_median_s,
                buffered_service_median_s,
            ),
            direct_to_temp_spool_ratio=_ratio(
                direct_service_median_s,
                streaming_service_median_s,
            ),
        ),
    }


def _service_payload_protocol_case_recommendation(
    *,
    case_name: str,
    streaming_to_buffered_ratio: float | None,
    direct_to_buffered_ratio: float | None,
    direct_to_temp_spool_ratio: float | None,
) -> str:
    if direct_to_buffered_ratio is not None and direct_to_temp_spool_ratio is not None:
        if direct_to_buffered_ratio <= 1.05:
            return (
                "direct streaming is timing-competitive with buffered payloads "
                f"for {case_name}; promote it as the next bounded-memory backend "
                "candidate and validate multi-writer orchestration"
            )
        if direct_to_temp_spool_ratio <= 0.85:
            return (
                "direct streaming materially improves temp-spool streaming but "
                "is still slower than buffered payloads; keep buffered default "
                "while continuing direct-stream optimization"
            )
    if streaming_to_buffered_ratio is None:
        return "insufficient service protocol timing evidence"
    if streaming_to_buffered_ratio <= 1.05:
        return (
            "streaming service payload is timing-competitive; keep temp-spool "
            "streaming as a candidate while scaling multi-writer orchestration"
        )
    if streaming_to_buffered_ratio <= 1.25:
        return (
            "streaming reduces Rust engine buffering but adds measurable "
            f"{case_name} overhead; keep buffered default and gather larger samples"
        )
    return (
        "streaming reduces Rust engine buffering but the temp-spool protocol is "
        "too expensive for this case; consider native-library or direct writer "
        "streaming before making streaming canonical"
    )


def _service_payload_protocol_matrix_analysis(
    comparisons: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    if not comparisons:
        return None
    case_comparisons = [
        comparison["comparison"]
        for comparison in comparisons
        if isinstance(comparison.get("comparison"), Mapping)
    ]
    worst = _comparison_with_max(
        case_comparisons,
        "streaming_to_buffered_rust_service_duration_ratio",
    )
    best = _comparison_with_min(
        case_comparisons,
        "streaming_to_buffered_rust_service_duration_ratio",
    )
    worst_direct = _comparison_with_max(
        case_comparisons,
        "direct_streaming_to_buffered_rust_service_duration_ratio",
    )
    best_direct = _comparison_with_min(
        case_comparisons,
        "direct_streaming_to_buffered_rust_service_duration_ratio",
    )
    best_direct_to_temp_spool = _comparison_with_min(
        case_comparisons,
        "direct_streaming_to_temp_spool_streaming_duration_ratio",
    )
    streaming_zero_buffered = all(
        _float_value(
            _mapping_value(
                comparison.get("streaming_content_engine"),
                "bytes_buffered",
            )
        )
        == 0
        for comparison in case_comparisons
    )
    direct_zero_buffered = all(
        _float_value(
            _mapping_value(
                comparison.get("direct_streaming_content_engine"),
                "bytes_buffered",
            )
        )
        == 0
        for comparison in case_comparisons
    )
    direct_all_direct = all(
        (
            _float_value(
                _mapping_value(
                    comparison.get("direct_streaming_content_engine"),
                    "direct_streamed_payload_count",
                )
            )
            or 0
        )
        > 0
        for comparison in case_comparisons
    )
    worst_ratio = _float_value(
        worst.get("value") if isinstance(worst, Mapping) else None
    )
    worst_direct_ratio = _float_value(
        worst_direct.get("value") if isinstance(worst_direct, Mapping) else None
    )
    return {
        "case_count": len(case_comparisons),
        "worst_streaming_to_buffered_ratio_case": worst,
        "best_streaming_to_buffered_ratio_case": best,
        "worst_direct_streaming_to_buffered_ratio_case": worst_direct,
        "best_direct_streaming_to_buffered_ratio_case": best_direct,
        "best_direct_streaming_to_temp_spool_ratio_case": best_direct_to_temp_spool,
        "streaming_zero_engine_buffered_bytes": streaming_zero_buffered,
        "direct_streaming_zero_engine_buffered_bytes": direct_zero_buffered,
        "direct_streaming_uses_direct_engine_path": direct_all_direct,
        "architecture_recommendation": _service_payload_architecture_recommendation(
            worst_ratio=worst_ratio,
            worst_direct_ratio=worst_direct_ratio,
            streaming_zero_buffered=streaming_zero_buffered,
            direct_zero_buffered=direct_zero_buffered,
        ),
    }


def _service_payload_architecture_recommendation(
    *,
    worst_ratio: float | None,
    worst_direct_ratio: float | None,
    streaming_zero_buffered: bool,
    direct_zero_buffered: bool,
) -> str:
    if worst_direct_ratio is not None and direct_zero_buffered:
        if worst_direct_ratio <= 1.05:
            return (
                "direct streaming preserves bounded Rust engine buffering and is "
                "timing-competitive with buffered service payloads; make direct "
                "streaming the candidate canonical streaming boundary"
            )
        if worst_direct_ratio <= 1.25:
            return (
                "direct streaming preserves bounded Rust engine buffering with "
                "moderate overhead; keep buffered default and optimize direct "
                "streaming before multi-writer orchestration"
            )
    if worst_ratio is None:
        return "collect service protocol comparison receipts before architecture change"
    if worst_ratio <= 1.05 and streaming_zero_buffered:
        return (
            "keep chunked temp-spool streaming as the service candidate; next "
            "work should focus on conflict orchestration and larger receipt samples"
        )
    if worst_ratio <= 1.25:
        return (
            "keep buffered service payloads as the default and retain chunked "
            "streaming as an evidence path; defer native-library/direct streaming "
            "until larger payload receipts or multi-writer constraints require it"
        )
    return (
        "temp-spool streaming removes Rust engine buffering but has too much "
        "service overhead; evaluate native-library or direct-to-target streaming "
        "before promoting streaming to the canonical backend path"
    )


def _direct_stream_chunk_size_case_comparison(
    *,
    case_name: str,
    buffered: Mapping[str, Any],
    temp_spool: Mapping[str, Any],
    direct_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    buffered_service_median_s = _float_value(buffered.get("rust_service_median_s"))
    temp_spool_service_median_s = _float_value(temp_spool.get("rust_service_median_s"))
    chunk_results = [
        _direct_stream_chunk_result(
            case_name=case_name,
            direct=direct,
            buffered_service_median_s=buffered_service_median_s,
            temp_spool_service_median_s=temp_spool_service_median_s,
        )
        for direct in direct_summaries
    ]
    best = _direct_chunk_result_with_selected(
        chunk_results,
        "direct_rust_service_median_s",
        select_max=False,
    )
    worst_buffered_ratio = _direct_chunk_result_with_selected(
        chunk_results,
        "direct_to_buffered_rust_service_duration_ratio",
        select_max=True,
    )
    best_buffered_ratio = _direct_chunk_result_with_selected(
        chunk_results,
        "direct_to_buffered_rust_service_duration_ratio",
        select_max=False,
    )
    best_temp_spool_ratio = _direct_chunk_result_with_selected(
        chunk_results,
        "direct_to_temp_spool_streaming_duration_ratio",
        select_max=False,
    )
    return {
        "case_name": case_name,
        "buffered_protocol": buffered.get("rust_service_payload_protocol"),
        "temp_spool_protocol": temp_spool.get("rust_service_payload_protocol"),
        "direct_streaming_protocol": (
            RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
        ),
        "buffered_request_handoff_protocol": buffered.get(
            "rust_service_request_handoff_protocol"
        ),
        "temp_spool_request_handoff_protocol": temp_spool.get(
            "rust_service_request_handoff_protocol"
        ),
        "buffered_rust_service_median_s": buffered_service_median_s,
        "temp_spool_rust_service_median_s": temp_spool_service_median_s,
        "temp_spool_chunk_bytes": temp_spool.get("stream_chunk_bytes"),
        "direct_chunk_results": chunk_results,
        "best_direct_streaming_chunk_result": best,
        "best_direct_streaming_to_buffered_ratio_result": best_buffered_ratio,
        "worst_direct_streaming_to_buffered_ratio_result": worst_buffered_ratio,
        "best_direct_streaming_to_temp_spool_ratio_result": best_temp_spool_ratio,
        "recommendation": _direct_stream_chunk_size_case_recommendation(best),
    }


def _direct_stream_chunk_result(
    *,
    case_name: str,
    direct: Mapping[str, Any],
    buffered_service_median_s: float | None,
    temp_spool_service_median_s: float | None,
) -> dict[str, Any]:
    direct_service_median_s = _float_value(direct.get("rust_service_median_s"))
    chunk_bytes = _int_value(direct.get("direct_stream_chunk_bytes"))
    client_medians = _mapping_or_empty(direct.get("rust_service_client_medians_s"))
    server_medians = _mapping_or_empty(direct.get("rust_service_server_medians_s"))
    phase_medians = _mapping_or_empty(direct.get("rust_service_phase_medians_s"))
    content_engine = _mapping_or_empty(direct.get("rust_service_content_engine"))
    client_counters = _mapping_or_empty(direct.get("rust_service_client_counters"))
    write_phase_median_s = _float_value(_mapping_value(phase_medians, "write_s"))
    direct_stream_read_median_s = _float_value(
        _mapping_value(phase_medians, "direct_stream_read_s")
    )
    direct_stream_file_write_median_s = _float_value(
        _mapping_value(phase_medians, "direct_stream_file_write_s")
    )
    direct_stream_hash_median_s = _float_value(
        _mapping_value(phase_medians, "direct_stream_hash_s")
    )
    target_leaf_safety_median_s = _float_value(
        _mapping_value(phase_medians, "target_leaf_safety_s")
    )
    target_leaf_name_encode_median_s = _float_value(
        _mapping_value(phase_medians, "target_leaf_name_encode_s")
    )
    target_leaf_open_median_s = _float_value(
        _mapping_value(phase_medians, "target_leaf_open_s")
    )
    target_leaf_open_count = _float_value(
        _mapping_value(
            _mapping_or_empty(direct.get("rust_service_phase_counters")),
            "target_leaf_open_count",
        )
    )
    request_write_median_s = _float_value(
        _mapping_value(client_medians, "request_write_s")
    )
    request_delta_metadata_write_median_s = _float_value(
        _mapping_value(client_medians, "request_delta_metadata_write_s")
    )
    request_content_materialize_median_s = _float_value(
        _mapping_value(client_medians, "request_content_materialize_s")
    )
    request_payload_write_median_s = _float_value(
        _mapping_value(client_medians, "request_payload_write_s")
    )
    request_flush_median_s = _float_value(
        _mapping_value(client_medians, "request_flush_s")
    )
    request_profiled_median_s = _float_value(
        _mapping_value(client_medians, "request_profiled_s")
    )
    request_unprofiled_median_s = _float_value(
        _mapping_value(client_medians, "request_unprofiled_s")
    )
    response_read_median_s = _float_value(
        _mapping_value(client_medians, "response_read_s")
    )
    response_decode_median_s = _float_value(
        _mapping_value(client_medians, "response_decode_s")
    )
    response_json_decode_median_s = _float_value(
        _mapping_value(client_medians, "response_json_decode_s")
    )
    response_report_expand_median_s = _float_value(
        _mapping_value(client_medians, "response_report_expand_s")
    )
    response_profiled_median_s = _float_value(
        _mapping_value(client_medians, "response_profiled_s")
    )
    response_unprofiled_median_s = _float_value(
        _mapping_value(client_medians, "response_unprofiled_s")
    )
    response_byte_count = _float_value(
        _mapping_value(client_counters, "response_byte_count")
    )
    server_apply_median_s = _float_value(_mapping_value(server_medians, "apply_s"))
    server_response_encode_median_s = _float_value(
        _mapping_value(server_medians, "response_encode_s")
    )
    server_response_write_median_s = _float_value(
        _mapping_value(server_medians, "response_write_s")
    )
    server_total_median_s = _float_value(
        _mapping_value(server_medians, "total_service_s")
    )
    bytes_direct_streamed = _float_value(
        _mapping_value(content_engine, "bytes_direct_streamed")
    )
    return {
        "case_name": case_name,
        "chunk_bytes": chunk_bytes,
        "request_handoff_protocol": _optional_string(
            direct.get("rust_service_request_handoff_protocol")
        ),
        "direct_rust_service_median_s": direct_service_median_s,
        "direct_to_buffered_rust_service_duration_ratio": _ratio(
            direct_service_median_s,
            buffered_service_median_s,
        ),
        "direct_to_temp_spool_streaming_duration_ratio": _ratio(
            direct_service_median_s,
            temp_spool_service_median_s,
        ),
        "request_write_median_s": request_write_median_s,
        "request_write_share_of_service_duration": _ratio(
            request_write_median_s,
            direct_service_median_s,
        ),
        "request_delta_metadata_write_median_s": (
            request_delta_metadata_write_median_s
        ),
        "request_delta_metadata_write_share_of_service_duration": _ratio(
            request_delta_metadata_write_median_s,
            direct_service_median_s,
        ),
        "request_content_materialize_median_s": (request_content_materialize_median_s),
        "request_content_materialize_share_of_service_duration": _ratio(
            request_content_materialize_median_s,
            direct_service_median_s,
        ),
        "request_payload_write_median_s": request_payload_write_median_s,
        "request_payload_write_share_of_service_duration": _ratio(
            request_payload_write_median_s,
            direct_service_median_s,
        ),
        "request_flush_median_s": request_flush_median_s,
        "request_flush_share_of_service_duration": _ratio(
            request_flush_median_s,
            direct_service_median_s,
        ),
        "request_profiled_median_s": request_profiled_median_s,
        "request_unprofiled_median_s": request_unprofiled_median_s,
        "response_read_median_s": response_read_median_s,
        "response_read_share_of_service_duration": _ratio(
            response_read_median_s,
            direct_service_median_s,
        ),
        "response_decode_median_s": response_decode_median_s,
        "response_decode_share_of_service_duration": _ratio(
            response_decode_median_s,
            direct_service_median_s,
        ),
        "response_json_decode_median_s": response_json_decode_median_s,
        "response_json_decode_share_of_service_duration": _ratio(
            response_json_decode_median_s,
            direct_service_median_s,
        ),
        "response_report_expand_median_s": response_report_expand_median_s,
        "response_report_expand_share_of_service_duration": _ratio(
            response_report_expand_median_s,
            direct_service_median_s,
        ),
        "response_profiled_median_s": response_profiled_median_s,
        "response_unprofiled_median_s": response_unprofiled_median_s,
        "response_byte_count": response_byte_count,
        "response_bytes_per_applied_path": _ratio(
            response_byte_count,
            _float_value(direct.get("applied_path_count")),
        ),
        "response_protocol": _optional_string(
            direct.get("rust_service_response_protocol")
        ),
        "digest_backend_kind": _optional_string(
            direct.get("rust_service_digest_backend_kind")
            or direct.get("rust_digest_backend_kind")
        ),
        "timing_protocol": _optional_string(direct.get("rust_service_timing_protocol")),
        "total_client_boundary_median_s": _float_value(
            _mapping_value(client_medians, "total_client_boundary_s")
        ),
        "server_timings_median_s": server_medians,
        "server_apply_median_s": server_apply_median_s,
        "server_apply_share_of_service_duration": _ratio(
            server_apply_median_s,
            direct_service_median_s,
        ),
        "server_response_encode_median_s": server_response_encode_median_s,
        "server_response_encode_share_of_service_duration": _ratio(
            server_response_encode_median_s,
            direct_service_median_s,
        ),
        "server_response_write_median_s": server_response_write_median_s,
        "server_response_write_share_of_service_duration": _ratio(
            server_response_write_median_s,
            direct_service_median_s,
        ),
        "server_total_median_s": server_total_median_s,
        "client_wait_minus_server_total_s": _delta(
            response_read_median_s,
            server_total_median_s,
        ),
        "write_phase_median_s": write_phase_median_s,
        "target_leaf_safety_median_s": target_leaf_safety_median_s,
        "target_leaf_name_encode_median_s": target_leaf_name_encode_median_s,
        "target_leaf_open_median_s": target_leaf_open_median_s,
        "target_leaf_open_count": target_leaf_open_count,
        "target_leaf_open_average_s": _ratio(
            target_leaf_open_median_s,
            target_leaf_open_count,
        ),
        "target_leaf_open_share_of_leaf_safety": _ratio(
            target_leaf_open_median_s,
            target_leaf_safety_median_s,
        ),
        "target_leaf_open_share_of_service_duration": _ratio(
            target_leaf_open_median_s,
            direct_service_median_s,
        ),
        "direct_stream_read_median_s": direct_stream_read_median_s,
        "direct_stream_read_share_of_service_duration": _ratio(
            direct_stream_read_median_s,
            direct_service_median_s,
        ),
        "direct_stream_file_write_median_s": direct_stream_file_write_median_s,
        "direct_stream_file_write_share_of_service_duration": _ratio(
            direct_stream_file_write_median_s,
            direct_service_median_s,
        ),
        "direct_stream_hash_median_s": direct_stream_hash_median_s,
        "direct_stream_hash_bytes_per_second": _bytes_per_second(
            bytes_direct_streamed,
            direct_stream_hash_median_s,
        ),
        "direct_stream_hash_share_of_write_phase": _ratio(
            direct_stream_hash_median_s,
            write_phase_median_s,
        ),
        "direct_stream_hash_share_of_service_duration": _ratio(
            direct_stream_hash_median_s,
            direct_service_median_s,
        ),
        "direct_stream_non_hash_write_median_s": _delta(
            write_phase_median_s,
            direct_stream_hash_median_s,
        ),
        "content_engine": content_engine,
        "client_counters": client_counters,
        "direct_streamed_payload_count": _float_value(
            _mapping_value(content_engine, "direct_streamed_payload_count")
        ),
        "bytes_buffered": _float_value(
            _mapping_value(content_engine, "bytes_buffered")
        ),
        "bytes_spooled": _float_value(_mapping_value(content_engine, "bytes_spooled")),
        "bytes_direct_streamed": bytes_direct_streamed,
        "chunk_count": _float_value(_mapping_value(content_engine, "chunk_count")),
        "max_chunk_bytes": _float_value(
            _mapping_value(content_engine, "max_chunk_bytes")
        ),
        "request_stream_chunk_count": _float_value(
            _mapping_value(client_counters, "request_stream_chunk_count")
        ),
        "request_max_chunk_bytes": _float_value(
            _mapping_value(client_counters, "request_max_chunk_bytes")
        ),
        "parity_passed": bool(direct.get("parity_passed")),
    }


def _direct_stream_chunk_size_case_recommendation(
    best_result: Mapping[str, Any] | None,
) -> str:
    if not isinstance(best_result, Mapping):
        return "insufficient direct streaming chunk-size evidence"
    chunk_bytes = _int_value(best_result.get("chunk_bytes"))
    buffered_ratio = _float_value(
        best_result.get("direct_to_buffered_rust_service_duration_ratio")
    )
    temp_ratio = _float_value(
        best_result.get("direct_to_temp_spool_streaming_duration_ratio")
    )
    if buffered_ratio is not None and buffered_ratio <= 1.05:
        return (
            f"use {chunk_bytes} byte chunks as the direct streaming candidate for "
            "this case; it is timing-competitive with buffered payloads"
        )
    if temp_ratio is not None and temp_ratio <= 0.90:
        return (
            f"use {chunk_bytes} byte chunks for direct-stream optimization; it "
            "beats temp-spool streaming but buffered remains the default"
        )
    return (
        f"{chunk_bytes} byte chunks are the best measured direct-stream option, "
        "but buffered should remain the default"
    )


def _direct_stream_chunk_size_matrix_analysis(
    comparisons: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    if not comparisons:
        return None
    case_comparisons = [
        comparison["comparison"]
        for comparison in comparisons
        if isinstance(comparison.get("comparison"), Mapping)
    ]
    results = [
        result
        for comparison in case_comparisons
        for result in _list_value(comparison.get("direct_chunk_results"))
        if isinstance(result, Mapping)
    ]
    best = _direct_chunk_result_with_selected(
        results,
        "direct_rust_service_median_s",
        select_max=False,
    )
    worst_buffered_ratio = _direct_chunk_result_with_selected(
        results,
        "direct_to_buffered_rust_service_duration_ratio",
        select_max=True,
    )
    best_temp_spool_ratio = _direct_chunk_result_with_selected(
        results,
        "direct_to_temp_spool_streaming_duration_ratio",
        select_max=False,
    )
    rollup = _direct_chunk_size_rollup(results)
    recommended = _recommended_direct_chunk_size(rollup)
    hash_throughput = _direct_stream_hash_throughput_analysis(results)
    return {
        "case_count": len(case_comparisons),
        "sample_count": len(results),
        "chunk_size_rollup": rollup,
        "direct_stream_hash_throughput": hash_throughput,
        "recommended_direct_stream_chunk_bytes": (
            recommended.get("chunk_bytes") if recommended else None
        ),
        "recommended_direct_stream_chunk_result": recommended,
        "best_direct_streaming_chunk_result": best,
        "worst_direct_streaming_to_buffered_ratio_result": worst_buffered_ratio,
        "best_direct_streaming_to_temp_spool_ratio_result": best_temp_spool_ratio,
        "direct_streaming_zero_engine_buffered_bytes": all(
            (_float_value(result.get("bytes_buffered")) == 0) for result in results
        ),
        "direct_streaming_zero_spooled_bytes": all(
            (_float_value(result.get("bytes_spooled")) == 0) for result in results
        ),
        "recommendation": _direct_stream_chunk_size_matrix_recommendation(
            recommended,
            hash_throughput,
        ),
    }


def _direct_chunk_result_with_selected(
    results: Sequence[Mapping[str, Any]],
    metric: str,
    *,
    select_max: bool,
) -> dict[str, Any] | None:
    selected: Mapping[str, Any] | None = None
    selected_value: float | None = None
    for result in results:
        value = _float_value(result.get(metric))
        if value is None:
            continue
        if selected_value is None:
            selected = result
            selected_value = value
            continue
        if (select_max and value > selected_value) or (
            not select_max and value < selected_value
        ):
            selected = result
            selected_value = value
    if selected is None or selected_value is None:
        return None
    return {
        "case_name": _optional_string(selected.get("case_name")),
        "chunk_bytes": _int_value(selected.get("chunk_bytes")),
        "metric": metric,
        "value": selected_value,
    }


def _direct_chunk_size_rollup(
    results: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[int, list[Mapping[str, Any]]] = {}
    for result in results:
        chunk_bytes = _int_value(result.get("chunk_bytes"))
        if chunk_bytes is None:
            continue
        grouped.setdefault(chunk_bytes, []).append(result)
    rollups: list[dict[str, Any]] = []
    for chunk_bytes, chunk_results in sorted(grouped.items()):
        service_medians = [
            value
            for result in chunk_results
            if (value := _float_value(result.get("direct_rust_service_median_s")))
            is not None
        ]
        buffered_ratios = [
            value
            for result in chunk_results
            if (
                value := _float_value(
                    result.get("direct_to_buffered_rust_service_duration_ratio")
                )
            )
            is not None
        ]
        temp_spool_ratios = [
            value
            for result in chunk_results
            if (
                value := _float_value(
                    result.get("direct_to_temp_spool_streaming_duration_ratio")
                )
            )
            is not None
        ]
        rollups.append(
            {
                "chunk_bytes": chunk_bytes,
                "case_count": len(chunk_results),
                "average_direct_rust_service_median_s": _average(service_medians),
                "average_direct_to_buffered_ratio": _average(buffered_ratios),
                "worst_direct_to_buffered_ratio": (
                    max(buffered_ratios) if buffered_ratios else None
                ),
                "average_direct_to_temp_spool_ratio": _average(temp_spool_ratios),
                "worst_direct_to_temp_spool_ratio": (
                    max(temp_spool_ratios) if temp_spool_ratios else None
                ),
            }
        )
    return rollups


def _direct_stream_hash_throughput_analysis(
    results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    hash_bytes_per_second = [
        value
        for result in results
        if (value := _float_value(result.get("direct_stream_hash_bytes_per_second")))
        is not None
    ]
    hash_shares = [
        value
        for result in results
        if (
            value := _float_value(result.get("direct_stream_hash_share_of_write_phase"))
        )
        is not None
    ]
    service_hash_shares = [
        value
        for result in results
        if (
            value := _float_value(
                result.get("direct_stream_hash_share_of_service_duration")
            )
        )
        is not None
    ]
    request_write_shares = [
        value
        for result in results
        if (
            value := _float_value(result.get("request_write_share_of_service_duration"))
        )
        is not None
    ]
    request_payload_write_shares = [
        value
        for result in results
        if (
            value := _float_value(
                result.get("request_payload_write_share_of_service_duration")
            )
        )
        is not None
    ]
    request_content_materialize_shares = [
        value
        for result in results
        if (
            value := _float_value(
                result.get("request_content_materialize_share_of_service_duration")
            )
        )
        is not None
    ]
    response_read_shares = [
        value
        for result in results
        if (
            value := _float_value(result.get("response_read_share_of_service_duration"))
        )
        is not None
    ]
    response_report_expand_shares = [
        value
        for result in results
        if (
            value := _float_value(
                result.get("response_report_expand_share_of_service_duration")
            )
        )
        is not None
    ]
    response_byte_counts = [
        value
        for result in results
        if (value := _float_value(result.get("response_byte_count"))) is not None
    ]
    response_bytes_per_path = [
        value
        for result in results
        if (value := _float_value(result.get("response_bytes_per_applied_path")))
        is not None
    ]
    server_apply_shares = [
        value
        for result in results
        if (value := _float_value(result.get("server_apply_share_of_service_duration")))
        is not None
    ]
    server_response_encode_shares = [
        value
        for result in results
        if (
            value := _float_value(
                result.get("server_response_encode_share_of_service_duration")
            )
        )
        is not None
    ]
    server_response_write_shares = [
        value
        for result in results
        if (
            value := _float_value(
                result.get("server_response_write_share_of_service_duration")
            )
        )
        is not None
    ]
    client_wait_minus_server_total = [
        value
        for result in results
        if (value := _float_value(result.get("client_wait_minus_server_total_s")))
        is not None
    ]
    digest_backend_kinds = sorted(
        {
            value
            for result in results
            if (value := _optional_string(result.get("digest_backend_kind")))
            is not None
        }
    )
    request_handoff_protocols = sorted(
        {
            value
            for result in results
            if (value := _optional_string(result.get("request_handoff_protocol")))
            is not None
        }
    )
    slowest_hash = _direct_chunk_result_with_selected(
        results,
        "direct_stream_hash_bytes_per_second",
        select_max=False,
    )
    highest_hash_share = _direct_chunk_result_with_selected(
        results,
        "direct_stream_hash_share_of_write_phase",
        select_max=True,
    )
    highest_response_share = _direct_chunk_result_with_selected(
        results,
        "response_read_share_of_service_duration",
        select_max=True,
    )
    highest_payload_write_share = _direct_chunk_result_with_selected(
        results,
        "request_payload_write_share_of_service_duration",
        select_max=True,
    )
    highest_response_expand_share = _direct_chunk_result_with_selected(
        results,
        "response_report_expand_share_of_service_duration",
        select_max=True,
    )
    return {
        "sample_count": len(results),
        "digest_backend_kinds": digest_backend_kinds,
        "request_handoff_protocols": request_handoff_protocols,
        "average_direct_stream_hash_bytes_per_second": _average(hash_bytes_per_second),
        "minimum_direct_stream_hash_bytes_per_second": (
            min(hash_bytes_per_second) if hash_bytes_per_second else None
        ),
        "average_direct_stream_hash_share_of_write_phase": _average(hash_shares),
        "maximum_direct_stream_hash_share_of_write_phase": (
            max(hash_shares) if hash_shares else None
        ),
        "average_direct_stream_hash_share_of_service_duration": _average(
            service_hash_shares
        ),
        "maximum_direct_stream_hash_share_of_service_duration": (
            max(service_hash_shares) if service_hash_shares else None
        ),
        "average_request_write_share_of_service_duration": _average(
            request_write_shares
        ),
        "average_request_payload_write_share_of_service_duration": _average(
            request_payload_write_shares
        ),
        "average_request_content_materialize_share_of_service_duration": _average(
            request_content_materialize_shares
        ),
        "average_response_read_share_of_service_duration": _average(
            response_read_shares
        ),
        "average_response_report_expand_share_of_service_duration": _average(
            response_report_expand_shares
        ),
        "average_response_byte_count": _average(response_byte_counts),
        "minimum_response_byte_count": (
            min(response_byte_counts) if response_byte_counts else None
        ),
        "maximum_response_byte_count": (
            max(response_byte_counts) if response_byte_counts else None
        ),
        "average_response_bytes_per_applied_path": _average(response_bytes_per_path),
        "average_server_apply_share_of_service_duration": _average(server_apply_shares),
        "average_server_response_encode_share_of_service_duration": _average(
            server_response_encode_shares
        ),
        "average_server_response_write_share_of_service_duration": _average(
            server_response_write_shares
        ),
        "average_client_wait_minus_server_total_s": _average(
            client_wait_minus_server_total
        ),
        "slowest_direct_stream_hash_throughput_result": slowest_hash,
        "highest_hash_share_result": highest_hash_share,
        "highest_response_read_share_result": highest_response_share,
        "highest_request_payload_write_share_result": highest_payload_write_share,
        "highest_response_report_expand_share_result": highest_response_expand_share,
    }


def _request_boundary_profile_analysis(
    case_summaries: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    cases = [
        profile
        for case in case_summaries
        if (profile := _request_boundary_case_profile(case)) is not None
    ]
    highest_client_boundary_share = _hotspot_case_with_max(
        cases,
        "total_client_boundary_share_of_service_duration",
    )
    highest_payload_write_share = _hotspot_case_with_max(
        cases,
        "request_payload_write_share_of_service_duration",
    )
    highest_content_materialize_share = _hotspot_case_with_max(
        cases,
        "request_content_materialize_share_of_service_duration",
    )
    highest_response_expand_share = _hotspot_case_with_max(
        cases,
        "response_report_expand_share_of_service_duration",
    )
    return {
        "case_count": len(cases),
        "cases": cases,
        "highest_total_client_boundary_share_case": highest_client_boundary_share,
        "highest_request_payload_write_share_case": highest_payload_write_share,
        "highest_request_content_materialize_share_case": (
            highest_content_materialize_share
        ),
        "highest_response_report_expand_share_case": highest_response_expand_share,
        "recommendation": _request_boundary_profile_recommendation(
            highest_client_boundary_share=highest_client_boundary_share,
            highest_payload_write_share=highest_payload_write_share,
            highest_content_materialize_share=highest_content_materialize_share,
            highest_response_expand_share=highest_response_expand_share,
        ),
    }


def _request_boundary_case_profile(
    case: Mapping[str, Any],
) -> dict[str, Any] | None:
    client_medians = _mapping_or_empty(case.get("rust_service_client_medians_s"))
    client_counters = _mapping_or_empty(case.get("rust_service_client_counters"))
    service_median_s = _float_value(case.get("rust_service_median_s"))
    if service_median_s is None or not client_medians:
        return None

    request_write_s = _float_value(_mapping_value(client_medians, "request_write_s"))
    request_root_resolve_s = _float_value(
        _mapping_value(client_medians, "request_root_resolve_s")
    )
    request_control_write_s = _float_value(
        _mapping_value(client_medians, "request_control_write_s")
    )
    request_delta_metadata_write_s = _float_value(
        _mapping_value(client_medians, "request_delta_metadata_write_s")
    )
    request_content_materialize_s = _float_value(
        _mapping_value(client_medians, "request_content_materialize_s")
    )
    request_payload_write_s = _float_value(
        _mapping_value(client_medians, "request_payload_write_s")
    )
    request_flush_s = _float_value(_mapping_value(client_medians, "request_flush_s"))
    request_profiled_s = _float_value(
        _mapping_value(client_medians, "request_profiled_s")
    )
    request_unprofiled_s = _float_value(
        _mapping_value(client_medians, "request_unprofiled_s")
    )
    response_read_s = _float_value(_mapping_value(client_medians, "response_read_s"))
    response_decode_s = _float_value(
        _mapping_value(client_medians, "response_decode_s")
    )
    response_json_decode_s = _float_value(
        _mapping_value(client_medians, "response_json_decode_s")
    )
    response_report_expand_s = _float_value(
        _mapping_value(client_medians, "response_report_expand_s")
    )
    response_profiled_s = _float_value(
        _mapping_value(client_medians, "response_profiled_s")
    )
    response_unprofiled_s = _float_value(
        _mapping_value(client_medians, "response_unprofiled_s")
    )
    total_client_boundary_s = _float_value(
        _mapping_value(client_medians, "total_client_boundary_s")
    )
    return {
        "case_name": _optional_string(case.get("case_name")),
        "request_handoff_protocol": _optional_string(
            case.get("rust_service_request_handoff_protocol")
        ),
        "rust_service_median_s": service_median_s,
        "total_client_boundary_median_s": total_client_boundary_s,
        "total_client_boundary_share_of_service_duration": _ratio(
            total_client_boundary_s,
            service_median_s,
        ),
        "request_write_median_s": request_write_s,
        "request_write_share_of_service_duration": _ratio(
            request_write_s,
            service_median_s,
        ),
        "request_root_resolve_median_s": request_root_resolve_s,
        "request_root_resolve_share_of_service_duration": _ratio(
            request_root_resolve_s,
            service_median_s,
        ),
        "request_control_write_median_s": request_control_write_s,
        "request_control_write_share_of_service_duration": _ratio(
            request_control_write_s,
            service_median_s,
        ),
        "request_delta_metadata_write_median_s": request_delta_metadata_write_s,
        "request_delta_metadata_write_share_of_service_duration": _ratio(
            request_delta_metadata_write_s,
            service_median_s,
        ),
        "request_content_materialize_median_s": request_content_materialize_s,
        "request_content_materialize_share_of_service_duration": _ratio(
            request_content_materialize_s,
            service_median_s,
        ),
        "request_payload_write_median_s": request_payload_write_s,
        "request_payload_write_share_of_service_duration": _ratio(
            request_payload_write_s,
            service_median_s,
        ),
        "request_flush_median_s": request_flush_s,
        "request_flush_share_of_service_duration": _ratio(
            request_flush_s,
            service_median_s,
        ),
        "request_profiled_median_s": request_profiled_s,
        "request_unprofiled_median_s": request_unprofiled_s,
        "response_read_median_s": response_read_s,
        "response_read_share_of_service_duration": _ratio(
            response_read_s,
            service_median_s,
        ),
        "response_decode_median_s": response_decode_s,
        "response_decode_share_of_service_duration": _ratio(
            response_decode_s,
            service_median_s,
        ),
        "response_json_decode_median_s": response_json_decode_s,
        "response_json_decode_share_of_service_duration": _ratio(
            response_json_decode_s,
            service_median_s,
        ),
        "response_report_expand_median_s": response_report_expand_s,
        "response_report_expand_share_of_service_duration": _ratio(
            response_report_expand_s,
            service_median_s,
        ),
        "response_profiled_median_s": response_profiled_s,
        "response_unprofiled_median_s": response_unprofiled_s,
        "request_byte_count": _float_value(
            _mapping_value(client_counters, "request_byte_count")
        ),
        "request_content_byte_count": _float_value(
            _mapping_value(client_counters, "request_content_byte_count")
        ),
        "request_protocol_byte_count": _float_value(
            _mapping_value(client_counters, "request_protocol_byte_count")
        ),
        "request_write_call_count": _float_value(
            _mapping_value(client_counters, "request_write_call_count")
        ),
        "request_writev_call_count": _float_value(
            _mapping_value(client_counters, "request_writev_call_count")
        ),
        "request_buffered_write_call_count": _float_value(
            _mapping_value(client_counters, "request_buffered_write_call_count")
        ),
        "request_vectored_payload_write_count": _float_value(
            _mapping_value(client_counters, "request_vectored_payload_write_count")
        ),
        "request_vectored_payload_byte_count": _float_value(
            _mapping_value(client_counters, "request_vectored_payload_byte_count")
        ),
        "request_vectored_write_fallback_count": _float_value(
            _mapping_value(client_counters, "request_vectored_write_fallback_count")
        ),
        "response_byte_count": _float_value(
            _mapping_value(client_counters, "response_byte_count")
        ),
    }


def _request_boundary_profile_recommendation(
    *,
    highest_client_boundary_share: Mapping[str, Any] | None,
    highest_payload_write_share: Mapping[str, Any] | None,
    highest_content_materialize_share: Mapping[str, Any] | None,
    highest_response_expand_share: Mapping[str, Any] | None,
) -> str:
    client_share = _float_value(
        highest_client_boundary_share.get("value")
        if isinstance(highest_client_boundary_share, Mapping)
        else None
    )
    payload_share = _float_value(
        highest_payload_write_share.get("value")
        if isinstance(highest_payload_write_share, Mapping)
        else None
    )
    materialize_share = _float_value(
        highest_content_materialize_share.get("value")
        if isinstance(highest_content_materialize_share, Mapping)
        else None
    )
    expand_share = _float_value(
        highest_response_expand_share.get("value")
        if isinstance(highest_response_expand_share, Mapping)
        else None
    )
    if client_share is not None and client_share >= 0.35:
        if payload_share is not None and payload_share >= 0.15:
            return (
                "Python-to-Rust request payload writes are a visible service "
                "duration share; evaluate native/zero-copy request handoff "
                "before changing Rust apply semantics"
            )
        if materialize_share is not None and materialize_share >= 0.15:
            return (
                "Python request content materialization is a visible boundary "
                "cost; avoid duplicate byte conversion before native-library work"
            )
        if expand_share is not None and expand_share >= 0.10:
            return (
                "response expansion is measurable; keep compact receipts and "
                "evaluate lower-allocation response mapping"
            )
    return (
        "request-boundary split is available; optimize Rust apply hotspots only "
        "after release receipts show client boundary is not dominant"
    )


def _recommended_direct_chunk_size(
    rollups: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    selected: Mapping[str, Any] | None = None
    selected_worst_ratio: float | None = None
    selected_average_ratio: float | None = None
    for rollup in rollups:
        worst_ratio = _float_value(rollup.get("worst_direct_to_buffered_ratio"))
        average_ratio = _float_value(rollup.get("average_direct_to_buffered_ratio"))
        if worst_ratio is None:
            continue
        if selected is None:
            selected = rollup
            selected_worst_ratio = worst_ratio
            selected_average_ratio = average_ratio
            continue
        if worst_ratio < (selected_worst_ratio or float("inf")):
            selected = rollup
            selected_worst_ratio = worst_ratio
            selected_average_ratio = average_ratio
            continue
        if (
            worst_ratio == selected_worst_ratio
            and average_ratio is not None
            and (
                selected_average_ratio is None or average_ratio < selected_average_ratio
            )
        ):
            selected = rollup
            selected_average_ratio = average_ratio
    return dict(selected) if selected is not None else None


def _direct_stream_chunk_size_matrix_recommendation(
    recommended: Mapping[str, Any] | None,
    hash_throughput: Mapping[str, Any] | None = None,
) -> str:
    if not isinstance(recommended, Mapping):
        return "collect direct streaming chunk-size receipts before changing defaults"
    chunk_bytes = _int_value(recommended.get("chunk_bytes"))
    worst_ratio = _float_value(recommended.get("worst_direct_to_buffered_ratio"))
    max_hash_share = _float_value(
        _mapping_value(
            hash_throughput, "maximum_direct_stream_hash_share_of_write_phase"
        )
    )
    if max_hash_share is not None and max_hash_share >= 0.70:
        return (
            f"use {chunk_bytes} byte chunks and target SHA throughput next; "
            f"direct-stream hashing accounts for up to {max_hash_share:.1%} "
            "of the direct write phase"
        )
    if worst_ratio is not None and worst_ratio <= 1.05:
        return (
            f"use {chunk_bytes} byte chunks as the direct streaming candidate; "
            "the worst selected-case buffered ratio is within 5%"
        )
    return (
        f"use {chunk_bytes} byte chunks for the next direct-streaming optimization "
        "receipt, but keep buffered service payloads as the default"
    )


def _comparison_with_max(
    comparisons: Sequence[Mapping[str, Any]],
    metric: str,
) -> dict[str, Any] | None:
    return _comparison_with_selected(comparisons, metric, select_max=True)


def _comparison_with_min(
    comparisons: Sequence[Mapping[str, Any]],
    metric: str,
) -> dict[str, Any] | None:
    return _comparison_with_selected(comparisons, metric, select_max=False)


def _comparison_with_selected(
    comparisons: Sequence[Mapping[str, Any]],
    metric: str,
    *,
    select_max: bool,
) -> dict[str, Any] | None:
    selected: Mapping[str, Any] | None = None
    selected_value: float | None = None
    for comparison in comparisons:
        value = _float_value(comparison.get(metric))
        if value is None:
            continue
        if selected_value is None:
            selected = comparison
            selected_value = value
            continue
        if (select_max and value > selected_value) or (
            not select_max and value < selected_value
        ):
            selected = comparison
            selected_value = value
    if selected is None or selected_value is None:
        return None
    return {
        "case_name": _optional_string(selected.get("case_name")),
        "metric": metric,
        "value": selected_value,
        "recommendation": _optional_string(selected.get("recommendation")),
    }


def _dominant_service_phases(
    case_summaries: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    phases: list[dict[str, Any]] = []
    for case in case_summaries:
        dominant = _mapping_value(case, "dominant_rust_service_phase")
        if not isinstance(dominant, Mapping):
            continue
        phases.append(
            {
                "case_name": _optional_string(case.get("case_name")),
                "phase_name": _optional_string(dominant.get("phase_name")),
                "median_s": _float_value(dominant.get("median_s")),
            }
        )
    return phases


def _phase_medians(summary: object) -> dict[str, float]:
    if not isinstance(summary, Mapping):
        return {}
    medians: dict[str, float] = {}
    for key in summary:
        if not str(key).startswith("phase_timings_s."):
            continue
        phase_name = str(key).removeprefix("phase_timings_s.")
        median_s = _summary_median(summary, str(key))
        if median_s is not None:
            medians[phase_name] = median_s
    return medians


def _phase_counters(summary: object) -> dict[str, float]:
    if not isinstance(summary, Mapping):
        return {}
    counters: dict[str, float] = {}
    for key in summary:
        if not str(key).startswith("phase_counters."):
            continue
        counter_name = str(key).removeprefix("phase_counters.")
        median_value = _summary_median(summary, str(key))
        if median_value is not None:
            counters[counter_name] = median_value
    return counters


def _content_engine_counters(summary: object) -> dict[str, float]:
    if not isinstance(summary, Mapping):
        return {}
    counters: dict[str, float] = {}
    for key in summary:
        if not str(key).startswith("content_engine."):
            continue
        counter_name = str(key).removeprefix("content_engine.")
        median_value = _summary_median(summary, str(key))
        if median_value is not None:
            counters[counter_name] = median_value
    return counters


def _service_client_medians(summary: object) -> dict[str, float]:
    if not isinstance(summary, Mapping):
        return {}
    medians: dict[str, float] = {}
    for key in summary:
        if not str(key).startswith("service_client_timings_s."):
            continue
        timing_name = str(key).removeprefix("service_client_timings_s.")
        median_s = _summary_median(summary, str(key))
        if median_s is not None:
            medians[timing_name] = median_s
    return medians


def _service_client_counters(summary: object) -> dict[str, float]:
    if not isinstance(summary, Mapping):
        return {}
    counters: dict[str, float] = {}
    for key in summary:
        if not str(key).startswith("service_client_counters."):
            continue
        counter_name = str(key).removeprefix("service_client_counters.")
        median_value = _summary_median(summary, str(key))
        if median_value is not None:
            counters[counter_name] = median_value
    return counters


def _service_server_medians(summary: object) -> dict[str, float]:
    if not isinstance(summary, Mapping):
        return {}
    medians: dict[str, float] = {}
    for key in summary:
        if not str(key).startswith("service_server_timings_s."):
            continue
        timing_name = str(key).removeprefix("service_server_timings_s.")
        median_s = _summary_median(summary, str(key))
        if median_s is not None:
            medians[timing_name] = median_s
    return medians


def _dominant_phase(phase_medians_s: Mapping[str, float]) -> dict[str, Any] | None:
    selected_name: str | None = None
    selected_value: float | None = None
    for phase_name, median_s in phase_medians_s.items():
        if phase_name in {
            "json_encode_s",
            "total_profiled_apply_s",
            "root_safety_s",
        }:
            continue
        if selected_value is None or median_s > selected_value:
            selected_name = phase_name
            selected_value = median_s
    if selected_name is None or selected_value is None:
        return None
    return {
        "phase_name": selected_name,
        "median_s": selected_value,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a stable Python-vs-Rust native apply profile matrix.",
    )
    parser.add_argument("--fixture-root", required=True)
    parser.add_argument("--target-dir", default=None)
    parser.add_argument("--cargo-path", default=None)
    parser.add_argument("--cargo-home", default=None)
    parser.add_argument("--manifest-path", default=None)
    parser.add_argument("--prepared-binary-path", default=None)
    parser.add_argument("--prepared-service-binary-path", default=None)
    parser.add_argument("--prepared-library-path", default=None)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument(
        "--payload-content-kind",
        choices=("text", "bytes"),
        default="text",
    )
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--build-timeout-s", type=float, default=240.0)
    parser.add_argument("--startup-iterations", type=int, default=5)
    parser.add_argument("--persistent-boundary-probe", action="store_true")
    parser.add_argument("--persistent-boundary-iterations", type=int, default=5)
    parser.add_argument("--rust-library-backend", action="store_true")
    parser.add_argument("--rust-service-backend", action="store_true")
    parser.add_argument("--rust-service-streaming-payload", action="store_true")
    parser.add_argument("--rust-service-direct-streaming-payload", action="store_true")
    parser.add_argument("--rust-service-stream-chunk-bytes", type=int, default=262_144)
    parser.add_argument("--rust-service-compact-response", action="store_true")
    parser.add_argument("--rust-service-server-timings", action="store_true")
    parser.add_argument("--compare-service-payload-protocols", action="store_true")
    parser.add_argument("--compare-direct-stream-chunk-sizes", action="store_true")
    parser.add_argument(
        "--direct-stream-chunk-bytes",
        action="append",
        type=int,
        default=[],
    )
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--receipt-dir", default=None)
    parser.add_argument("--compact", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    receipt = run_native_apply_profile_matrix(
        NativeApplyProfileMatrixConfig(
            fixture_root=Path(args.fixture_root),
            target_dir=Path(args.target_dir) if args.target_dir else None,
            cargo_path=Path(args.cargo_path) if args.cargo_path else None,
            cargo_home=Path(args.cargo_home) if args.cargo_home else None,
            manifest_path=Path(args.manifest_path) if args.manifest_path else None,
            prepared_binary_path=(
                Path(args.prepared_binary_path) if args.prepared_binary_path else None
            ),
            prepared_service_binary_path=(
                Path(args.prepared_service_binary_path)
                if args.prepared_service_binary_path
                else None
            ),
            prepared_library_path=(
                Path(args.prepared_library_path) if args.prepared_library_path else None
            ),
            iterations=args.iterations,
            payload_content_kind=args.payload_content_kind,
            release=args.release,
            build_timeout_s=args.build_timeout_s,
            startup_iterations=args.startup_iterations,
            persistent_boundary_probe=args.persistent_boundary_probe,
            persistent_boundary_iterations=args.persistent_boundary_iterations,
            rust_library_backend=args.rust_library_backend,
            rust_service_backend=args.rust_service_backend,
            rust_service_streaming_payload=args.rust_service_streaming_payload,
            rust_service_direct_streaming_payload=(
                args.rust_service_direct_streaming_payload
            ),
            rust_service_stream_chunk_bytes=args.rust_service_stream_chunk_bytes,
            rust_service_compact_response=args.rust_service_compact_response,
            rust_service_server_timings=args.rust_service_server_timings,
            compare_service_payload_protocols=args.compare_service_payload_protocols,
            compare_direct_stream_chunk_sizes=args.compare_direct_stream_chunk_sizes,
            direct_stream_chunk_size_bytes=tuple(args.direct_stream_chunk_bytes),
            case_names=tuple(args.case),
            write_receipt=args.write_receipt,
            receipt_dir=Path(args.receipt_dir) if args.receipt_dir else None,
        )
    )
    indent = None if args.compact else 2
    print(json.dumps(receipt, indent=indent, sort_keys=True))
    return 0


def _selected_cases(case_names: Sequence[str]) -> tuple[NativeApplyProfileCase, ...]:
    cases_by_name = {case.name: case for case in default_profile_cases()}
    if not case_names:
        return tuple(cases_by_name.values())
    selected: list[NativeApplyProfileCase] = []
    for name in case_names:
        if name not in cases_by_name:
            available = ", ".join(sorted(cases_by_name))
            raise ValueError(f"Unknown native apply profile case {name!r}: {available}")
        selected.append(cases_by_name[name])
    return tuple(selected)


def _case_receipt_dir(
    *,
    fixture_root: Path,
    case: NativeApplyProfileCase,
    protocol_label: str | None = None,
) -> Path:
    path = (
        fixture_root
        / ".aware"
        / "reports"
        / "file_system"
        / "performance"
        / "cases"
        / case.name
    )
    if protocol_label is not None:
        path = path / protocol_label
    return path


def _maybe_write_profile_receipt(
    *,
    receipt: dict[str, Any],
    config: NativeApplyProfileMatrixConfig,
    fixture_root: Path,
) -> dict[str, Any]:
    if not config.write_receipt:
        return receipt
    receipt_dir = (
        config.receipt_dir.expanduser().resolve()
        if config.receipt_dir is not None
        else fixture_root / ".aware" / "reports" / "file_system" / "performance"
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = (
        receipt_dir / f"{NATIVE_APPLY_PROFILE_MATRIX_VERSION}.{timestamp}.json"
    )
    receipt_with_path = {**receipt, "receipt_path": receipt_path.as_posix()}
    receipt_path.write_text(
        json.dumps(receipt_with_path, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_with_path


def _direct_stream_chunk_sizes(
    config: NativeApplyProfileMatrixConfig,
) -> tuple[int, ...]:
    raw_sizes = (
        config.direct_stream_chunk_size_bytes
        if config.direct_stream_chunk_size_bytes
        else DEFAULT_DIRECT_STREAM_CHUNK_SWEEP_BYTES
    )
    deduped: list[int] = []
    for chunk_bytes in raw_sizes:
        if chunk_bytes not in deduped:
            deduped.append(chunk_bytes)
    return tuple(deduped)


def _direct_summary_for_chunk(
    summaries: Sequence[Mapping[str, Any]],
    chunk_bytes: object,
) -> dict[str, Any] | None:
    selected_chunk_bytes = _int_value(chunk_bytes)
    if selected_chunk_bytes is None:
        return None
    for summary in summaries:
        if _int_value(summary.get("direct_stream_chunk_bytes")) == selected_chunk_bytes:
            return dict(summary)
    return None


def _summary_median(summary: object, key: str) -> float | None:
    stats = _mapping_value(summary, key)
    value = _mapping_value(stats, "median")
    if isinstance(value, int | float):
        return float(value)
    return None


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _bytes_per_second(
    byte_count: float | None, duration_s: float | None
) -> float | None:
    if byte_count is None or duration_s is None or duration_s <= 0:
        return None
    return byte_count / duration_s


def _delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return value - baseline


def _float_value(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _list_value(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _average(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _mapping_value(value: object, key: str) -> object:
    if not isinstance(value, Mapping):
        return None
    return value.get(key)


def _mapping_or_empty(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _validate_config(config: NativeApplyProfileMatrixConfig) -> None:
    if config.iterations < 1:
        raise ValueError("Native apply profile matrix iterations must be at least 1.")
    if config.startup_iterations < 1:
        raise ValueError(
            "Native apply profile matrix startup_iterations must be at least 1."
        )
    if config.persistent_boundary_iterations < 1:
        raise ValueError(
            "Native apply profile matrix persistent_boundary_iterations must be "
            "at least 1."
        )
    if config.payload_content_kind not in {"text", "bytes"}:
        raise ValueError(
            "Native apply profile matrix payload_content_kind must be text or bytes."
        )
    if config.rust_service_stream_chunk_bytes < 1:
        raise ValueError(
            "Native apply profile matrix rust_service_stream_chunk_bytes must be "
            "at least 1."
        )
    for chunk_bytes in _direct_stream_chunk_sizes(config):
        if chunk_bytes < 1:
            raise ValueError(
                "Native apply profile matrix direct_stream_chunk_size_bytes must "
                "all be at least 1."
            )
    if (
        config.compare_service_payload_protocols
        and config.compare_direct_stream_chunk_sizes
    ):
        raise ValueError(
            "Native apply profile matrix can compare service payload protocols "
            "or direct stream chunk sizes, not both in one run."
        )
    if (
        config.rust_service_streaming_payload
        and config.rust_service_direct_streaming_payload
    ):
        raise ValueError(
            "Native apply profile matrix can use either temp-spool streaming or "
            "direct streaming, not both."
        )
    streaming_enabled = (
        config.rust_service_streaming_payload
        or config.rust_service_direct_streaming_payload
    )
    service_comparison_enabled = (
        config.compare_service_payload_protocols
        or config.compare_direct_stream_chunk_sizes
    )
    if streaming_enabled and not config.rust_service_backend:
        raise ValueError(
            "Native apply profile matrix streaming payload requires "
            "rust_service_backend."
        )
    if config.rust_service_compact_response and not config.rust_service_backend:
        raise ValueError(
            "Native apply profile matrix compact response requires "
            "rust_service_backend."
        )
    if (
        config.rust_service_server_timings
        and not config.rust_service_backend
        and not service_comparison_enabled
    ):
        raise ValueError(
            "Native apply profile matrix server timings requires "
            "rust_service_backend."
        )
    if (
        config.direct_stream_chunk_size_bytes
        and not config.compare_direct_stream_chunk_sizes
    ):
        raise ValueError(
            "Native apply profile matrix direct stream chunk sizes require "
            "chunk-size comparison."
        )
    if service_comparison_enabled and config.rust_service_direct_streaming_payload:
        raise ValueError(
            "Native apply profile matrix direct streaming payload should not be "
            "set when a service comparison mode controls the protocol."
        )
    _selected_cases(config.case_names)


def _ensure_empty_or_missing(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise ValueError(
            "Native apply profile matrix fixture root must be empty: " f"{path}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
