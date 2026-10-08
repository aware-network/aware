from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.native_apply_benchmark import (  # noqa: E402
    NativeApplyBenchmarkConfig,
)
from aware_file_system.native_apply_executor import (  # noqa: E402
    DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES,
    RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND,
    RUST_WORKSPACE_APPLY_LIBRARY_RELEASE_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_RELEASE_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_RELEASE_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL,
    RustWorkspaceApplyExecutor,
    RustWorkspaceApplyLibraryExecutor,
)
from aware_file_system.scripts import profile_native_apply  # noqa: E402
from aware_file_system.scripts.profile_native_apply import (  # noqa: E402
    NATIVE_APPLY_PROFILE_MATRIX_VERSION,
    NativeApplyProfileMatrixConfig,
    default_profile_cases,
    run_native_apply_profile_matrix,
)


def test_default_profile_cases_are_stable() -> None:
    assert [case.name for case in default_profile_cases()] == [
        "many_small_files",
        "delete_heavy_cleanup",
        "large_payloads",
        "many_small_files_no_digest",
    ]


def test_profile_matrix_writes_summary_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_configs: list[NativeApplyBenchmarkConfig] = []
    fake_executor = RustWorkspaceApplyExecutor(
        binary_path=tmp_path / "native-apply",
        invocation_kind=RUST_WORKSPACE_APPLY_RELEASE_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        rust_build={"status": "succeeded"},
    )
    fake_service_executor = RustWorkspaceApplyExecutor(
        binary_path=tmp_path / "native-apply-service",
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_RELEASE_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        rust_build={"status": "succeeded"},
    )
    fake_library_executor = RustWorkspaceApplyLibraryExecutor(
        library_path=tmp_path / "libaware_file_system_native.so",
        invocation_kind=RUST_WORKSPACE_APPLY_LIBRARY_RELEASE_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        rust_build={"status": "succeeded"},
    )

    def fake_run(config: NativeApplyBenchmarkConfig) -> dict[str, Any]:
        captured_configs.append(config)
        return _fake_benchmark_receipt(
            config=config,
            python_median_s=0.004,
            rust_median_s=0.002,
        )

    monkeypatch.setattr(
        profile_native_apply,
        "prepare_rust_workspace_apply_executor",
        lambda *_args, **_kwargs: fake_executor,
    )
    monkeypatch.setattr(
        profile_native_apply,
        "measure_rust_workspace_apply_startup",
        lambda **_kwargs: _fake_startup_probe(),
    )
    monkeypatch.setattr(
        profile_native_apply,
        "prepare_rust_workspace_apply_service_executor",
        lambda *_args, **_kwargs: fake_service_executor,
    )
    monkeypatch.setattr(
        profile_native_apply,
        "prepare_rust_workspace_apply_library_executor",
        lambda *_args, **_kwargs: fake_library_executor,
    )
    monkeypatch.setattr(
        profile_native_apply,
        "measure_rust_workspace_apply_persistent_boundary",
        lambda **_kwargs: _fake_persistent_boundary_probe(
            sample_count=_kwargs["iterations"],
        ),
    )
    monkeypatch.setattr(profile_native_apply, "run_native_apply_benchmark", fake_run)

    receipt = run_native_apply_profile_matrix(
        NativeApplyProfileMatrixConfig(
            fixture_root=tmp_path / "matrix",
            target_dir=tmp_path / "target",
            iterations=3,
            release=True,
            persistent_boundary_probe=True,
            persistent_boundary_iterations=6,
            rust_library_backend=True,
            rust_service_backend=True,
            payload_content_kind="bytes",
            case_names=("many_small_files", "large_payloads"),
            write_receipt=True,
        )
    )

    assert receipt["receipt_schema"] == NATIVE_APPLY_PROFILE_MATRIX_VERSION
    assert receipt["case_count"] == 2
    assert receipt["release"] is True
    assert Path(receipt["receipt_path"]).is_file()
    assert json.loads(Path(receipt["receipt_path"]).read_text()) == receipt

    assert [config.fixture_profile for config in captured_configs] == [
        "many_small_files",
        "large_payloads",
    ]
    assert captured_configs[0].iterations == 3
    assert captured_configs[0].release is True
    assert captured_configs[0].prepared_binary_path == tmp_path / "native-apply"
    assert captured_configs[0].prepared_library_path == (
        tmp_path / "libaware_file_system_native.so"
    )
    assert captured_configs[0].prepared_service_binary_path == (
        tmp_path / "native-apply-service"
    )
    assert captured_configs[0].rust_library_backend is True
    assert captured_configs[0].rust_service_backend is True
    assert captured_configs[0].rust_service_streaming_payload is False
    assert captured_configs[0].rust_service_direct_streaming_payload is False
    assert captured_configs[0].rust_service_stream_chunk_bytes == (
        DEFAULT_RUST_APPLY_STREAM_CHUNK_BYTES
    )
    assert captured_configs[0].payload_content_kind == "bytes"
    assert captured_configs[0].receipt_dir == (
        tmp_path
        / "matrix"
        / ".aware"
        / "reports"
        / "file_system"
        / "performance"
        / "cases"
        / "many_small_files"
    )

    first_case = receipt["cases"][0]
    assert (
        receipt["analysis"]["slowest_rust_service_case"]["case_name"]
        == "many_small_files"
    )
    assert receipt["analysis"]["first_optimization_target"]["case_name"] == (
        "many_small_files"
    )
    assert receipt["root_execution"]["prepared_once"] is True
    assert (
        receipt["root_execution"]["binary_path"]
        == (tmp_path / "native-apply").as_posix()
    )
    assert receipt["root_execution"]["startup_probe"]["sample_count"] == 2
    assert receipt["root_execution"]["rust_library_backend_enabled"] is True
    assert (
        receipt["root_execution"]["library_path"]
        == (tmp_path / "libaware_file_system_native.so").as_posix()
    )
    assert receipt["root_execution"]["library_boundary_kind"] == (
        RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND
    )
    assert receipt["root_execution"]["rust_service_backend_enabled"] is True
    assert (
        receipt["root_execution"]["service_binary_path"]
        == (tmp_path / "native-apply-service").as_posix()
    )
    assert (
        receipt["root_execution"]["persistent_boundary_probe"]["boundary_kind"]
        == "persistent_process"
    )
    assert receipt["root_execution"]["persistent_boundary_probe"]["sample_count"] == 6
    assert first_case["case_name"] == "many_small_files"
    assert (
        first_case["rust_invocation_kind"]
        == RUST_WORKSPACE_APPLY_RELEASE_INVOCATION_KIND
    )
    assert (
        first_case["benchmark_rust_invocation_kind"] == "provided_prepared_cli_binary"
    )
    assert (
        first_case["benchmark_rust_library_invocation_kind"]
        == "provided_prepared_cdylib"
    )
    assert first_case["rust_library_boundary_kind"] == (
        RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND
    )
    assert first_case["rust_library_to_python_duration_ratio"] == 0.375
    assert first_case["rust_library_to_rust_cli_duration_ratio"] == 0.75
    assert first_case["rust_service_to_rust_library_duration_ratio"] == pytest.approx(
        2 / 3
    )
    assert (
        first_case["benchmark_rust_service_invocation_kind"]
        == "provided_prepared_service_binary"
    )
    assert first_case["rust_to_python_duration_ratio"] == 0.5
    assert first_case["rust_service_to_python_duration_ratio"] == 0.25
    assert first_case["rust_service_to_rust_cli_duration_ratio"] == 0.5
    assert first_case["rust_service_phase_medians_s"]["target_leaf_safety_s"] == 0.0015
    assert first_case["rust_service_phase_medians_s"]["target_leaf_open_s"] == 0.0012
    assert (
        first_case["rust_service_phase_counters"][
            "after_write_root_safety_skipped_count"
        ]
        == 4
    )
    assert first_case["rust_service_phase_counters"]["target_leaf_open_count"] == 2
    assert first_case["rust_service_client_medians_s"]["request_write_s"] == 0.0004
    assert (
        first_case["rust_service_client_medians_s"]["request_payload_write_s"]
        == 0.00022
    )
    assert (
        first_case["rust_service_client_medians_s"]["response_report_expand_s"]
        == 0.00005
    )
    assert first_case["rust_service_client_counters"]["request_byte_count"] == 4096
    assert first_case["rust_service_content_engine"]["bytes_buffered"] == 8192
    assert first_case["rust_service_payload_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
    )
    assert first_case["rust_service_request_handoff_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert first_case["dominant_rust_service_phase"] == {
        "phase_name": "target_leaf_safety_s",
        "median_s": 0.0015,
    }
    assert receipt["analysis"]["dominant_rust_service_phases"][0] == {
        "case_name": "many_small_files",
        "phase_name": "target_leaf_safety_s",
        "median_s": 0.0015,
    }
    hotspot_analysis = receipt["analysis"]["rust_apply_hotspots"]
    assert hotspot_analysis["case_count"] == 2
    assert hotspot_analysis["highest_target_leaf_open_share_case"] == {
        "case_name": "many_small_files",
        "metric": "target_leaf_open_share_of_service_duration",
        "value": pytest.approx(0.0012 / 0.001),
    }
    assert hotspot_analysis["cases"][0]["target_leaf_open_average_s"] == pytest.approx(
        0.0012 / 2
    )
    boundary_profile = receipt["analysis"]["request_boundary_profile"]
    assert boundary_profile["case_count"] == 2
    assert boundary_profile["cases"][0]["request_handoff_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert boundary_profile["cases"][0][
        "request_payload_write_share_of_service_duration"
    ] == pytest.approx(0.00022 / 0.001)
    assert boundary_profile["cases"][0]["request_buffered_write_call_count"] == 6
    assert boundary_profile["cases"][0]["request_writev_call_count"] == 0
    assert boundary_profile["cases"][0][
        "response_report_expand_share_of_service_duration"
    ] == pytest.approx(0.00005 / 0.001)
    assert (
        boundary_profile["highest_request_payload_write_share_case"]["case_name"]
        == "many_small_files"
    )
    assert first_case["parity_passed"] is True
    assert first_case["fixture"]["operation_count"] == 288
    assert first_case["fixture"]["payload_content_kind"] == "bytes"


def test_profile_matrix_compares_service_payload_protocols(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_configs: list[NativeApplyBenchmarkConfig] = []
    fake_executor = RustWorkspaceApplyExecutor(
        binary_path=tmp_path / "native-apply",
        invocation_kind=RUST_WORKSPACE_APPLY_RELEASE_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        rust_build={"status": "succeeded"},
    )
    fake_service_executor = RustWorkspaceApplyExecutor(
        binary_path=tmp_path / "native-apply-service",
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_RELEASE_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        rust_build={"status": "succeeded"},
    )

    def fake_run(config: NativeApplyBenchmarkConfig) -> dict[str, Any]:
        captured_configs.append(config)
        return _fake_benchmark_receipt(
            config=config,
            python_median_s=0.004,
            rust_median_s=0.002,
        )

    monkeypatch.setattr(
        profile_native_apply,
        "prepare_rust_workspace_apply_executor",
        lambda *_args, **_kwargs: fake_executor,
    )
    monkeypatch.setattr(
        profile_native_apply,
        "prepare_rust_workspace_apply_service_executor",
        lambda *_args, **_kwargs: fake_service_executor,
    )
    monkeypatch.setattr(
        profile_native_apply,
        "measure_rust_workspace_apply_startup",
        lambda **_kwargs: _fake_startup_probe(),
    )
    monkeypatch.setattr(profile_native_apply, "run_native_apply_benchmark", fake_run)

    receipt = run_native_apply_profile_matrix(
        NativeApplyProfileMatrixConfig(
            fixture_root=tmp_path / "matrix",
            target_dir=tmp_path / "target",
            iterations=1,
            release=True,
            compare_service_payload_protocols=True,
            rust_service_stream_chunk_bytes=512,
            rust_service_server_timings=True,
            payload_content_kind="bytes",
            case_names=("many_small_files",),
            write_receipt=True,
        )
    )

    assert len(captured_configs) == 3
    assert captured_configs[0].rust_service_backend is True
    assert captured_configs[0].rust_service_streaming_payload is False
    assert captured_configs[0].rust_service_direct_streaming_payload is False
    assert captured_configs[1].rust_service_backend is True
    assert captured_configs[1].rust_service_streaming_payload is True
    assert captured_configs[1].rust_service_direct_streaming_payload is False
    assert captured_configs[1].rust_service_stream_chunk_bytes == 512
    assert captured_configs[2].rust_service_backend is True
    assert captured_configs[2].rust_service_streaming_payload is False
    assert captured_configs[2].rust_service_direct_streaming_payload is True
    assert captured_configs[2].rust_service_stream_chunk_bytes == 512
    assert captured_configs[0].fixture_root is not None
    assert captured_configs[1].fixture_root is not None
    assert captured_configs[2].fixture_root is not None
    assert captured_configs[0].fixture_root.name == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
    )
    assert captured_configs[1].fixture_root.name == (
        RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
    )
    assert captured_configs[2].fixture_root.name == (
        RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
    )

    assert receipt["service_payload_protocol_comparison_enabled"] is True
    assert receipt["service_stream_chunk_bytes"] == 512
    assert receipt["root_execution"]["rust_service_backend_enabled"] is True
    comparison = receipt["service_payload_protocol_comparisons"][0]
    assert comparison["case_name"] == "many_small_files"
    assert comparison["buffered"]["rust_service_payload_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
    )
    assert comparison["streaming"]["rust_service_payload_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
    )
    assert comparison["direct_streaming"]["rust_service_payload_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
    )
    assert comparison["comparison"]["buffered_request_handoff_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert comparison["comparison"]["streaming_request_handoff_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert comparison["comparison"]["direct_streaming_request_handoff_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
    )
    assert (
        comparison["comparison"]["streaming_to_buffered_rust_service_duration_ratio"]
        == 1.5
    )
    assert (
        comparison["comparison"][
            "direct_streaming_to_buffered_rust_service_duration_ratio"
        ]
        == 1.1
    )
    assert comparison["comparison"][
        "direct_streaming_to_temp_spool_streaming_duration_ratio"
    ] == pytest.approx(1.1 / 1.5)
    assert comparison["comparison"]["streaming_content_engine"]["bytes_buffered"] == 0
    assert (
        comparison["comparison"]["direct_streaming_content_engine"][
            "direct_streamed_payload_count"
        ]
        == 2
    )
    protocol_analysis = receipt["analysis"]["service_payload_protocol_comparison"]
    assert protocol_analysis["case_count"] == 1
    assert protocol_analysis["streaming_zero_engine_buffered_bytes"] is True
    assert protocol_analysis["direct_streaming_zero_engine_buffered_bytes"] is True
    assert protocol_analysis["direct_streaming_uses_direct_engine_path"] is True
    assert (
        protocol_analysis["worst_streaming_to_buffered_ratio_case"]["case_name"]
        == "many_small_files"
    )
    assert (
        protocol_analysis["worst_direct_streaming_to_buffered_ratio_case"]["case_name"]
        == "many_small_files"
    )


def test_profile_matrix_compares_direct_stream_chunk_sizes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_configs: list[NativeApplyBenchmarkConfig] = []
    fake_executor = RustWorkspaceApplyExecutor(
        binary_path=tmp_path / "native-apply",
        invocation_kind=RUST_WORKSPACE_APPLY_RELEASE_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        rust_build={"status": "succeeded"},
    )
    fake_service_executor = RustWorkspaceApplyExecutor(
        binary_path=tmp_path / "native-apply-service",
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_RELEASE_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
        rust_build={"status": "succeeded"},
    )

    def fake_run(config: NativeApplyBenchmarkConfig) -> dict[str, Any]:
        captured_configs.append(config)
        return _fake_benchmark_receipt(
            config=config,
            python_median_s=0.004,
            rust_median_s=0.002,
        )

    monkeypatch.setattr(
        profile_native_apply,
        "prepare_rust_workspace_apply_executor",
        lambda *_args, **_kwargs: fake_executor,
    )
    monkeypatch.setattr(
        profile_native_apply,
        "prepare_rust_workspace_apply_service_executor",
        lambda *_args, **_kwargs: fake_service_executor,
    )
    monkeypatch.setattr(
        profile_native_apply,
        "measure_rust_workspace_apply_startup",
        lambda **_kwargs: _fake_startup_probe(),
    )
    monkeypatch.setattr(profile_native_apply, "run_native_apply_benchmark", fake_run)

    receipt = run_native_apply_profile_matrix(
        NativeApplyProfileMatrixConfig(
            fixture_root=tmp_path / "matrix",
            target_dir=tmp_path / "target",
            iterations=1,
            release=True,
            compare_direct_stream_chunk_sizes=True,
            direct_stream_chunk_size_bytes=(4096, 65536),
            rust_service_stream_chunk_bytes=512,
            rust_service_server_timings=True,
            payload_content_kind="bytes",
            case_names=("large_payloads",),
            write_receipt=True,
        )
    )

    assert len(captured_configs) == 4
    assert captured_configs[0].rust_service_backend is True
    assert captured_configs[0].rust_service_streaming_payload is False
    assert captured_configs[0].rust_service_direct_streaming_payload is False
    assert captured_configs[1].rust_service_streaming_payload is True
    assert captured_configs[1].rust_service_stream_chunk_bytes == 512
    assert captured_configs[2].rust_service_direct_streaming_payload is True
    assert captured_configs[2].rust_service_stream_chunk_bytes == 4096
    assert captured_configs[3].rust_service_direct_streaming_payload is True
    assert captured_configs[3].rust_service_stream_chunk_bytes == 65536

    assert receipt["direct_stream_chunk_size_comparison_enabled"] is True
    assert receipt["service_response_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
    )
    assert receipt["service_timing_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL
    )
    assert receipt["direct_stream_chunk_size_bytes"] == [4096, 65536]
    assert receipt["cases"][0]["direct_stream_chunk_bytes"] == 65536
    comparison = receipt["direct_stream_chunk_size_comparisons"][0]
    assert comparison["case_name"] == "large_payloads"
    assert comparison["buffered"]["rust_service_payload_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
    )
    assert comparison["temp_spool_streaming"]["rust_service_payload_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
    )
    assert comparison["temp_spool_streaming"]["stream_chunk_bytes"] == 512
    assert [
        direct["direct_stream_chunk_bytes"]
        for direct in comparison["direct_streaming_by_chunk_size"]
    ] == [4096, 65536]
    assert (
        comparison["comparison"]["best_direct_streaming_chunk_result"]["chunk_bytes"]
        == 65536
    )
    best_direct_detail = next(
        result
        for result in comparison["comparison"]["direct_chunk_results"]
        if result["chunk_bytes"] == 65536
    )
    assert best_direct_detail["direct_stream_read_median_s"] == pytest.approx(0.00011)
    assert best_direct_detail["direct_stream_file_write_median_s"] == pytest.approx(
        0.00021
    )
    assert best_direct_detail["direct_stream_hash_median_s"] == pytest.approx(0.00009)
    assert best_direct_detail["target_leaf_open_median_s"] == pytest.approx(0.0012)
    assert best_direct_detail["target_leaf_open_count"] == 2
    assert best_direct_detail["target_leaf_open_average_s"] == pytest.approx(0.0012 / 2)
    assert best_direct_detail[
        "target_leaf_open_share_of_service_duration"
    ] == pytest.approx(0.0012 / 0.0009)
    assert best_direct_detail["direct_stream_hash_bytes_per_second"] == pytest.approx(
        8192 / 0.00009
    )
    assert best_direct_detail[
        "direct_stream_hash_share_of_write_phase"
    ] == pytest.approx(0.00009 / 0.0008)
    assert best_direct_detail[
        "direct_stream_hash_share_of_service_duration"
    ] == pytest.approx(0.00009 / 0.0009)
    assert best_direct_detail["direct_stream_non_hash_write_median_s"] == pytest.approx(
        0.0008 - 0.00009
    )
    assert best_direct_detail["response_byte_count"] == 2048
    assert best_direct_detail["response_bytes_per_applied_path"] == pytest.approx(
        2048 / 36
    )
    assert best_direct_detail["response_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
    )
    assert best_direct_detail["request_handoff_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
    )
    assert best_direct_detail["digest_backend_kind"] == "rustcrypto_sha2_asm_optimized"
    assert best_direct_detail["timing_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL
    )
    assert best_direct_detail["server_apply_median_s"] == pytest.approx(0.0007)
    assert best_direct_detail["server_response_encode_median_s"] == pytest.approx(
        0.00003
    )
    assert best_direct_detail["server_response_write_median_s"] == pytest.approx(
        0.00004
    )
    assert best_direct_detail[
        "server_apply_share_of_service_duration"
    ] == pytest.approx(0.0007 / 0.0009)
    assert best_direct_detail["client_wait_minus_server_total_s"] == pytest.approx(
        0.0002 - 0.0008
    )
    assert best_direct_detail["request_payload_write_median_s"] == pytest.approx(
        0.00022
    )
    assert best_direct_detail[
        "request_payload_write_share_of_service_duration"
    ] == pytest.approx(0.00022 / 0.0009)
    assert best_direct_detail["response_report_expand_median_s"] == pytest.approx(
        0.00005
    )
    assert best_direct_detail[
        "response_report_expand_share_of_service_duration"
    ] == pytest.approx(0.00005 / 0.0009)
    assert comparison["comparison"]["best_direct_streaming_chunk_result"][
        "value"
    ] == pytest.approx(0.0009)
    assert (
        comparison["comparison"]["worst_direct_streaming_to_buffered_ratio_result"][
            "chunk_bytes"
        ]
        == 4096
    )
    chunk_analysis = receipt["analysis"]["direct_stream_chunk_size_comparison"]
    assert chunk_analysis["case_count"] == 1
    assert chunk_analysis["sample_count"] == 2
    assert chunk_analysis["recommended_direct_stream_chunk_bytes"] == 65536
    assert chunk_analysis["direct_streaming_zero_engine_buffered_bytes"] is True
    assert chunk_analysis["direct_streaming_zero_spooled_bytes"] is True
    hash_analysis = chunk_analysis["direct_stream_hash_throughput"]
    assert hash_analysis["sample_count"] == 2
    assert hash_analysis["digest_backend_kinds"] == ["rustcrypto_sha2_asm_optimized"]
    assert hash_analysis["request_handoff_protocols"] == [
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
    ]
    assert hash_analysis[
        "average_direct_stream_hash_bytes_per_second"
    ] == pytest.approx(8192 / 0.00009)
    assert hash_analysis[
        "average_server_apply_share_of_service_duration"
    ] == pytest.approx(((0.0007 / 0.0014) + (0.0007 / 0.0009)) / 2)
    assert hash_analysis[
        "average_server_response_write_share_of_service_duration"
    ] == pytest.approx(((0.00004 / 0.0014) + (0.00004 / 0.0009)) / 2)
    assert hash_analysis[
        "maximum_direct_stream_hash_share_of_write_phase"
    ] == pytest.approx(0.00009 / 0.0008)
    assert (
        hash_analysis["slowest_direct_stream_hash_throughput_result"]["chunk_bytes"]
        == 4096
    )
    assert hash_analysis["average_response_byte_count"] == 2048
    assert hash_analysis["average_response_bytes_per_applied_path"] == pytest.approx(
        2048 / 36
    )
    assert hash_analysis[
        "average_request_payload_write_share_of_service_duration"
    ] == pytest.approx(((0.00022 / 0.0014) + (0.00022 / 0.0009)) / 2)
    assert hash_analysis[
        "average_response_report_expand_share_of_service_duration"
    ] == pytest.approx(((0.00005 / 0.0014) + (0.00005 / 0.0009)) / 2)
    assert (
        hash_analysis["highest_request_payload_write_share_result"]["chunk_bytes"]
        == 65536
    )


def test_profile_matrix_cli_maps_arguments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured_configs: list[NativeApplyProfileMatrixConfig] = []

    def fake_run(config: NativeApplyProfileMatrixConfig) -> dict[str, object]:
        captured_configs.append(config)
        return {"ok": True}

    monkeypatch.setattr(
        profile_native_apply,
        "run_native_apply_profile_matrix",
        fake_run,
    )

    exit_code = profile_native_apply.main(
        [
            "--fixture-root",
            (tmp_path / "fixture").as_posix(),
            "--target-dir",
            (tmp_path / "target").as_posix(),
            "--cargo-path",
            (tmp_path / "cargo").as_posix(),
            "--cargo-home",
            (tmp_path / "cargo-home").as_posix(),
            "--manifest-path",
            (tmp_path / "Cargo.toml").as_posix(),
            "--prepared-binary-path",
            (tmp_path / "native-apply").as_posix(),
            "--prepared-service-binary-path",
            (tmp_path / "native-apply-service").as_posix(),
            "--prepared-library-path",
            (tmp_path / "libaware_file_system_native.so").as_posix(),
            "--case",
            "many_small_files",
            "--case",
            "large_payloads",
            "--iterations",
            "7",
            "--payload-content-kind",
            "bytes",
            "--release",
            "--build-timeout-s",
            "12.5",
            "--startup-iterations",
            "4",
            "--persistent-boundary-probe",
            "--persistent-boundary-iterations",
            "6",
            "--rust-library-backend",
            "--rust-service-backend",
            "--rust-service-direct-streaming-payload",
            "--rust-service-stream-chunk-bytes",
            "512",
            "--rust-service-compact-response",
            "--rust-service-server-timings",
            "--compare-service-payload-protocols",
            "--compare-direct-stream-chunk-sizes",
            "--direct-stream-chunk-bytes",
            "4096",
            "--direct-stream-chunk-bytes",
            "65536",
            "--write-receipt",
            "--receipt-dir",
            (tmp_path / "receipts").as_posix(),
            "--compact",
        ]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True}
    config = captured_configs[0]
    assert config.fixture_root == tmp_path / "fixture"
    assert config.target_dir == tmp_path / "target"
    assert config.cargo_path == tmp_path / "cargo"
    assert config.cargo_home == tmp_path / "cargo-home"
    assert config.manifest_path == tmp_path / "Cargo.toml"
    assert config.prepared_binary_path == tmp_path / "native-apply"
    assert config.prepared_service_binary_path == tmp_path / "native-apply-service"
    assert config.prepared_library_path == (tmp_path / "libaware_file_system_native.so")
    assert config.case_names == ("many_small_files", "large_payloads")
    assert config.iterations == 7
    assert config.payload_content_kind == "bytes"
    assert config.release is True
    assert config.build_timeout_s == 12.5
    assert config.startup_iterations == 4
    assert config.persistent_boundary_probe is True
    assert config.persistent_boundary_iterations == 6
    assert config.rust_library_backend is True
    assert config.rust_service_backend is True
    assert config.rust_service_streaming_payload is False
    assert config.rust_service_direct_streaming_payload is True
    assert config.rust_service_stream_chunk_bytes == 512
    assert config.rust_service_compact_response is True
    assert config.rust_service_server_timings is True
    assert config.compare_service_payload_protocols is True
    assert config.compare_direct_stream_chunk_sizes is True
    assert config.direct_stream_chunk_size_bytes == (4096, 65536)
    assert config.write_receipt is True
    assert config.receipt_dir == tmp_path / "receipts"


def test_profile_matrix_rejects_unknown_case(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown native apply profile case"):
        run_native_apply_profile_matrix(
            NativeApplyProfileMatrixConfig(
                fixture_root=tmp_path / "matrix",
                case_names=("unknown",),
            )
        )


def _fake_benchmark_receipt(
    *,
    config: NativeApplyBenchmarkConfig,
    python_median_s: float,
    rust_median_s: float,
) -> dict[str, Any]:
    service_median_s = rust_median_s / 2
    if config.rust_service_streaming_payload:
        service_median_s = rust_median_s * 0.75
    if config.rust_service_direct_streaming_payload:
        direct_factor_by_chunk = {
            4096: 0.70,
            65536: 0.45,
        }
        service_median_s = rust_median_s * direct_factor_by_chunk.get(
            config.rust_service_stream_chunk_bytes,
            0.55,
        )
    receipt: dict[str, Any] = {
        "receipt_path": (
            config.receipt_dir / "case-receipt.json"
            if config.receipt_dir is not None
            else None
        ),
        "python_backend": {
            "summary": _summary(
                duration_s=python_median_s,
                operations_per_second=1000.0,
                bytes_written_per_second=2000.0,
            )
        },
        "rust_backend": {
            "invocation_kind": "provided_prepared_cli_binary",
            "samples": [
                {
                    "digest_backend_kind": "rustcrypto_sha2_asm_optimized",
                }
            ],
            "summary": _summary(
                duration_s=rust_median_s,
                operations_per_second=2000.0,
                bytes_written_per_second=3000.0,
            ),
        },
        "parity": {"passed": True},
    }
    if config.rust_service_backend:
        request_handoff_protocol = (
            RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
            if config.rust_service_direct_streaming_payload
            else RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
        )
        receipt["rust_service_backend"] = {
            "invocation_kind": "provided_prepared_service_binary",
            "samples": [
                {
                    "digest_backend_kind": "rustcrypto_sha2_asm_optimized",
                    "service_request_handoff_protocol": request_handoff_protocol,
                }
            ],
            "summary": _summary(
                duration_s=service_median_s,
                operations_per_second=3000.0,
                bytes_written_per_second=4000.0,
                streaming=(
                    config.rust_service_streaming_payload
                    or config.rust_service_direct_streaming_payload
                ),
                direct_streaming=config.rust_service_direct_streaming_payload,
                stream_chunk_bytes=config.rust_service_stream_chunk_bytes,
            ),
        }
        receipt["rust_service_payload_protocol"] = (
            RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
            if config.rust_service_direct_streaming_payload
            else (
                RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
                if config.rust_service_streaming_payload
                else RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
            )
        )
        receipt["rust_service_response_protocol"] = (
            RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL
            if config.rust_service_compact_response
            else RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
        )
        receipt["rust_service_request_handoff_protocol"] = request_handoff_protocol
        receipt["rust_service_timing_protocol"] = (
            RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL
            if config.rust_service_server_timings
            else None
        )
    if config.rust_library_backend:
        receipt["rust_library_backend"] = {
            "invocation_kind": "provided_prepared_cdylib",
            "samples": [
                {
                    "digest_backend_kind": "rustcrypto_sha2_asm_optimized",
                    "library_boundary_kind": RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND,
                }
            ],
            "summary": _summary(
                duration_s=rust_median_s * 0.75,
                operations_per_second=2500.0,
                bytes_written_per_second=3500.0,
                streaming=True,
                direct_streaming=True,
            ),
        }
        receipt["rust_library_execution"] = {
            "boundary_kind": RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND,
        }
    return receipt


def _fake_startup_probe() -> dict[str, object]:
    return {
        "probe_kind": "missing_file_delete",
        "sample_count": 2,
        "summary": {"duration_s": _stats(0.001)},
    }


def _fake_persistent_boundary_probe(*, sample_count: int) -> dict[str, object]:
    return {
        "probe_kind": "persistent_missing_file_delete",
        "boundary_kind": "persistent_process",
        "process_started_once": True,
        "sample_count": sample_count,
        "summary": {"duration_s": _stats(0.0002)},
    }


def _summary(
    *,
    duration_s: float,
    operations_per_second: float,
    bytes_written_per_second: float,
    streaming: bool = False,
    direct_streaming: bool = False,
    stream_chunk_bytes: int = 512,
) -> dict[str, dict[str, float | int]]:
    buffered_payload_count = 0 if streaming else 2
    streamed_payload_count = 2 if streaming else 0
    spooled_streamed_payload_count = (
        streamed_payload_count if streaming and not direct_streaming else 0
    )
    direct_streamed_payload_count = streamed_payload_count if direct_streaming else 0
    bytes_buffered = 0 if streaming else 8192
    bytes_streamed = 8192 if streaming else 0
    bytes_spooled = bytes_streamed if streaming and not direct_streaming else 0
    bytes_direct_streamed = bytes_streamed if direct_streaming else 0
    request_buffered_payload_count = 0 if streaming else 2
    request_streamed_payload_count = 2 if streaming else 0
    request_spooled_streamed_payload_count = (
        request_streamed_payload_count if streaming and not direct_streaming else 0
    )
    request_direct_streamed_payload_count = (
        request_streamed_payload_count if direct_streaming else 0
    )
    request_stream_chunk_count = max(1, 8192 // stream_chunk_bytes) if streaming else 0
    request_write_call_count = 4 if direct_streaming else 0
    request_writev_call_count = 6 if direct_streaming else 0
    request_buffered_write_call_count = 0 if direct_streaming else 6
    request_vectored_payload_write_count = (
        request_stream_chunk_count if direct_streaming else 0
    )
    request_vectored_payload_byte_count = 8192 if direct_streaming else 0
    direct_stream_read_s = 0.00011 if direct_streaming else 0.0
    direct_stream_file_write_s = 0.00021 if direct_streaming else 0.0
    direct_stream_hash_s = 0.00009 if direct_streaming else 0.0
    direct_stream_bytes_read_count = bytes_direct_streamed if direct_streaming else 0
    direct_stream_buffer_reuse_count = (
        request_stream_chunk_count if direct_streaming else 0
    )
    target_leaf_open_s = 0.0012
    target_leaf_name_encode_s = 0.0001
    return {
        "duration_s": _stats(duration_s),
        "operations_per_second": _stats(operations_per_second),
        "bytes_written_per_second": _stats(bytes_written_per_second),
        "phase_counters.after_write_root_safety_skipped_count": _stats(4),
        "phase_counters.after_write_root_safety_executed_count": _stats(0),
        "phase_counters.direct_stream_chunk_read_count": _stats(
            request_stream_chunk_count if direct_streaming else 0
        ),
        "phase_counters.direct_stream_bytes_read_count": _stats(
            direct_stream_bytes_read_count
        ),
        "phase_counters.direct_stream_buffer_reuse_count": _stats(
            direct_stream_buffer_reuse_count
        ),
        "phase_counters.target_leaf_open_count": _stats(2),
        "phase_timings_s.before_digest_s": _stats(0.001),
        "phase_timings_s.direct_stream_read_s": _stats(direct_stream_read_s),
        "phase_timings_s.direct_stream_file_write_s": _stats(
            direct_stream_file_write_s
        ),
        "phase_timings_s.direct_stream_hash_s": _stats(direct_stream_hash_s),
        "phase_timings_s.target_leaf_name_encode_s": _stats(target_leaf_name_encode_s),
        "phase_timings_s.target_leaf_open_s": _stats(target_leaf_open_s),
        "phase_timings_s.target_leaf_safety_s": _stats(0.0015),
        "phase_timings_s.total_profiled_apply_s": _stats(0.003),
        "phase_timings_s.write_s": _stats(0.0008),
        "content_engine.payload_count": _stats(2),
        "content_engine.buffered_payload_count": _stats(buffered_payload_count),
        "content_engine.streamed_payload_count": _stats(streamed_payload_count),
        "content_engine.spooled_streamed_payload_count": _stats(
            spooled_streamed_payload_count
        ),
        "content_engine.direct_streamed_payload_count": _stats(
            direct_streamed_payload_count
        ),
        "content_engine.bytes_buffered": _stats(bytes_buffered),
        "content_engine.bytes_streamed": _stats(bytes_streamed),
        "content_engine.bytes_spooled": _stats(bytes_spooled),
        "content_engine.bytes_direct_streamed": _stats(bytes_direct_streamed),
        "content_engine.chunk_count": _stats(
            request_stream_chunk_count if streaming else 2
        ),
        "content_engine.max_chunk_bytes": _stats(
            stream_chunk_bytes if streaming else 4096
        ),
        "service_client_timings_s.request_write_s": _stats(0.0004),
        "service_client_timings_s.request_root_resolve_s": _stats(0.00001),
        "service_client_timings_s.request_control_write_s": _stats(0.00002),
        "service_client_timings_s.request_delta_metadata_write_s": _stats(0.00006),
        "service_client_timings_s.request_content_materialize_s": _stats(0.00003),
        "service_client_timings_s.request_payload_write_s": _stats(0.00022),
        "service_client_timings_s.request_flush_s": _stats(0.00004),
        "service_client_timings_s.request_profiled_s": _stats(0.00038),
        "service_client_timings_s.request_unprofiled_s": _stats(0.00002),
        "service_client_timings_s.response_read_s": _stats(0.0002),
        "service_client_timings_s.response_decode_s": _stats(0.0001),
        "service_client_timings_s.response_json_decode_s": _stats(0.00004),
        "service_client_timings_s.response_report_expand_s": _stats(0.00005),
        "service_client_timings_s.response_profiled_s": _stats(0.00009),
        "service_client_timings_s.response_unprofiled_s": _stats(0.00001),
        "service_client_timings_s.total_client_boundary_s": _stats(0.00075),
        "service_server_timings_s.request_read_s": _stats(
            0.00005 if not direct_streaming else 0.0
        ),
        "service_server_timings_s.apply_s": _stats(0.0007),
        "service_server_timings_s.response_encode_s": _stats(0.00003),
        "service_server_timings_s.response_write_s": _stats(0.00004),
        "service_server_timings_s.total_service_s": _stats(0.0008),
        "service_client_counters.request_byte_count": _stats(4096),
        "service_client_counters.request_payload_count": _stats(2),
        "service_client_counters.request_buffered_payload_count": _stats(
            request_buffered_payload_count
        ),
        "service_client_counters.request_streamed_payload_count": _stats(
            request_streamed_payload_count
        ),
        "service_client_counters.request_spooled_streamed_payload_count": _stats(
            request_spooled_streamed_payload_count
        ),
        "service_client_counters.request_direct_streamed_payload_count": _stats(
            request_direct_streamed_payload_count
        ),
        "service_client_counters.request_stream_chunk_count": _stats(
            request_stream_chunk_count
        ),
        "service_client_counters.request_write_call_count": _stats(
            request_write_call_count
        ),
        "service_client_counters.request_writev_call_count": _stats(
            request_writev_call_count
        ),
        "service_client_counters.request_buffered_write_call_count": _stats(
            request_buffered_write_call_count
        ),
        "service_client_counters.request_vectored_payload_write_count": _stats(
            request_vectored_payload_write_count
        ),
        "service_client_counters.request_vectored_payload_byte_count": _stats(
            request_vectored_payload_byte_count
        ),
        "service_client_counters.request_vectored_write_fallback_count": _stats(0),
        "service_client_counters.response_byte_count": _stats(2048),
    }


def _stats(value: float) -> dict[str, float | int]:
    return {
        "count": 1,
        "min": value,
        "median": value,
        "p95": value,
        "max": value,
    }
