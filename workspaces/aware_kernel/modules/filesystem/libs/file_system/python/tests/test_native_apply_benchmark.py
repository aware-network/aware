from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.native_apply import NativeApplyUnavailable  # noqa: E402
from aware_file_system.native_apply_benchmark import (  # noqa: E402
    NATIVE_APPLY_BENCHMARK_VERSION,
    NativeApplyBenchmarkConfig,
    run_native_apply_benchmark,
    validate_native_apply_benchmark_receipt,
)
from aware_file_system.native_apply_executor import (  # noqa: E402
    RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND,
    RUST_WORKSPACE_APPLY_LIBRARY_DEBUG_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL,
)
from aware_file_system.scripts import benchmark_native_apply  # noqa: E402


def test_native_apply_benchmark_emits_python_vs_rust_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_FILE_SYSTEM_NATIVE_APPLY_PARALLEL_WORKERS", raising=False)
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=2,
                payload_bytes=96,
                iterations=2,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert receipt["receipt_schema"] == NATIVE_APPLY_BENCHMARK_VERSION
    assert receipt["mode"] == "synthetic_apply_fixture"
    assert receipt["iteration_count"] == 2
    assert receipt["fixture"]["fixture_profile"] == "balanced"
    assert receipt["fixture"]["create_file_count"] == 2
    assert receipt["fixture"]["update_file_count"] == 2
    assert receipt["fixture"]["delete_file_count"] == 2
    assert receipt["fixture"]["expected_applied_path_count"] == 6
    assert receipt["fixture"]["expected_digest_verified_count"] == 4
    assert receipt["fixture"]["expected_stored_artifact_count"] == 0
    assert receipt["python_backend"]["backend_kind"] == "python"
    assert receipt["rust_backend"]["backend_kind"] == "rust"
    assert receipt["rust_backend"]["invocation_kind"] == "prepared_debug_cli_binary"
    assert receipt["rust_build"]["status"] == "succeeded"
    assert receipt["rust_build"]["artifact_exists"] is True
    assert receipt["parity"]["passed"] is True
    assert receipt["parity"]["mismatches"] == []

    python_samples = receipt["python_backend"]["samples"]
    rust_samples = receipt["rust_backend"]["samples"]
    assert [sample["iteration_index"] for sample in python_samples] == [0, 1]
    assert [sample["iteration_index"] for sample in rust_samples] == [0, 1]
    for python_sample, rust_sample in zip(python_samples, rust_samples, strict=True):
        assert python_sample["applied_path_count"] == rust_sample["applied_path_count"]
        assert python_sample["bytes_written"] == rust_sample["bytes_written"]
        assert python_sample["bytes_deleted"] == rust_sample["bytes_deleted"]
        assert (
            python_sample["digest_verified_count"]
            == rust_sample["digest_verified_count"]
        )
        assert python_sample["operations_per_second"] >= 0
        assert rust_sample["operations_per_second"] >= 0
        assert rust_sample["duration_s"] >= 0
        assert rust_sample["digest_backend_kind"] in {
            "rustcrypto_sha2_asm_optimized",
            "rustcrypto_sha2_software",
            "libcrypto_evp",
        }
        assert python_sample["phase_timings_s"] is None
        rust_phase_timings = rust_sample["phase_timings_s"]
        assert rust_phase_timings is not None
        assert rust_phase_timings["metadata_probe_s"] >= 0
        assert rust_phase_timings["before_digest_read_s"] >= 0
        assert rust_phase_timings["before_digest_hash_s"] >= 0
        assert rust_phase_timings["before_digest_hex_s"] >= 0
        assert rust_phase_timings["after_digest_hash_s"] >= 0
        assert rust_phase_timings["after_digest_hex_s"] >= 0
        assert rust_phase_timings["write_s"] >= 0
        assert rust_phase_timings["create_write_s"] >= 0
        assert rust_phase_timings["update_write_s"] >= 0
        assert rust_phase_timings["target_leaf_safety_s"] >= 0
        assert rust_phase_timings["parent_descriptor_open_s"] >= 0
        assert rust_phase_timings["dirfd_cache_lookup_s"] >= 0
        assert rust_phase_timings["dirfd_chain_open_s"] >= 0
        assert rust_phase_timings["dirfd_mkdir_s"] >= 0
        assert rust_phase_timings["after_write_root_safety_s"] >= 0
        assert rust_phase_timings["after_write_root_safety_gate_s"] >= 0
        assert rust_phase_timings["apply_plan_s"] >= 0
        assert rust_phase_timings["apply_scheduler_s"] >= 0
        assert rust_phase_timings["apply_scheduler_selector_s"] >= 0
        assert rust_phase_timings["total_profiled_apply_s"] >= 0
        assert rust_phase_timings["json_encode_s"] >= 0
        rust_phase_counters = rust_sample["phase_counters"]
        assert rust_phase_counters is not None
        assert (
            rust_phase_counters["apply_plan_delta_count"]
            == rust_sample["applied_path_count"]
        )
        assert (
            rust_phase_counters["apply_plan_unique_target_path_count"]
            == rust_sample["applied_path_count"]
        )
        assert rust_phase_counters["apply_plan_parent_bucket_count"] >= 1
        assert rust_phase_counters["apply_plan_max_parent_bucket_size_count"] >= 1
        assert (
            rust_phase_counters["apply_plan_bucket_count"]
            == rust_sample["applied_path_count"]
        )
        assert rust_phase_counters["apply_plan_conflict_bucket_count"] == 0
        assert (
            rust_phase_counters["apply_plan_parallel_safe_bucket_count"]
            == rust_sample["applied_path_count"]
        )
        assert (
            rust_phase_counters["apply_plan_parallel_safe_delta_count"]
            == rust_sample["applied_path_count"]
        )
        assert rust_phase_counters["apply_plan_max_bucket_size_count"] == 1
        assert rust_phase_counters["apply_plan_repeated_target_path_count"] == 0
        assert rust_phase_counters["apply_plan_ancestor_conflict_count"] == 0
        assert rust_phase_counters["apply_scheduler_enabled_count"] == 0
        assert rust_phase_counters["apply_scheduler_skipped_count"] == 1
        assert rust_phase_counters["apply_scheduler_worker_count"] == 0
        assert rust_phase_counters["apply_scheduler_bucket_count"] == 0
        assert rust_phase_counters["apply_scheduler_delta_count"] == 0
        assert rust_phase_counters["apply_scheduler_parallel_bucket_count"] == 0
        assert rust_phase_counters["apply_scheduler_parallel_delta_count"] == 0
        assert rust_phase_counters["apply_scheduler_serial_conflict_bucket_count"] == 0
        assert rust_phase_counters["apply_scheduler_serial_conflict_delta_count"] == 0
        assert rust_phase_counters["apply_scheduler_worker_execution_count"] == 0
        assert rust_phase_counters["apply_scheduler_requested_count"] == 0
        assert rust_phase_counters["apply_scheduler_selected_count"] == 0
        assert rust_phase_counters["apply_scheduler_sequential_fallback_count"] == 0
        assert rust_phase_counters["apply_scheduler_conflict_fallback_count"] == 0
        assert rust_phase_counters["apply_scheduler_worker_floor_fallback_count"] == 0
        assert rust_phase_counters["apply_scheduler_empty_batch_fallback_count"] == 0
        assert rust_phase_counters["before_digest_bytes_read_count"] >= 0
        assert rust_phase_counters["before_digest_bytes_hashed_count"] >= 0
        assert rust_phase_counters["after_digest_bytes_hashed_count"] >= 0
        assert rust_phase_counters["after_digest_precomputed_count"] == 0
        assert rust_phase_counters["after_digest_precomputed_bytes_hashed_count"] == 0
        rust_content_engine = rust_sample["content_engine"]
        assert rust_content_engine is not None
        assert rust_content_engine["engine_kind"] == "rust_apply_content_engine_v0"
        assert rust_content_engine["streaming_capable"] is True
        assert rust_content_engine["payload_count"] == 4
        assert rust_content_engine["buffered_payload_count"] == 4
        assert rust_content_engine["streamed_payload_count"] == 0
        assert rust_content_engine["bytes_buffered"] == rust_sample["bytes_written"]
        assert rust_content_engine["bytes_streamed"] == 0
        assert rust_content_engine["chunk_count"] == 4
        assert rust_content_engine["max_chunk_bytes"] > 0
        if sys.platform != "win32":
            assert rust_phase_counters["after_write_root_safety_skipped_count"] == 4
            assert rust_phase_counters["after_write_root_safety_executed_count"] == 0
        else:
            assert rust_phase_counters["after_write_root_safety_skipped_count"] == 0
            assert rust_phase_counters["after_write_root_safety_executed_count"] == 4

    rust_summary = receipt["rust_backend"]["summary"]
    assert rust_summary["phase_timings_s.metadata_probe_s"]["count"] == 2
    assert rust_summary["phase_timings_s.before_digest_read_s"]["count"] == 2
    assert rust_summary["phase_timings_s.before_digest_hash_s"]["count"] == 2
    assert rust_summary["phase_timings_s.after_digest_hash_s"]["count"] == 2
    assert rust_summary["phase_timings_s.create_write_s"]["count"] == 2
    assert rust_summary["phase_timings_s.update_write_s"]["count"] == 2
    assert rust_summary["phase_timings_s.target_leaf_safety_s"]["count"] == 2
    assert rust_summary["phase_timings_s.parent_descriptor_open_s"]["count"] == 2
    assert rust_summary["phase_timings_s.dirfd_cache_lookup_s"]["count"] == 2
    assert rust_summary["phase_timings_s.dirfd_chain_open_s"]["count"] == 2
    assert rust_summary["phase_timings_s.dirfd_mkdir_s"]["count"] == 2
    assert rust_summary["phase_timings_s.after_write_root_safety_gate_s"]["count"] == 2
    assert rust_summary["phase_timings_s.apply_plan_s"]["count"] == 2
    assert rust_summary["phase_timings_s.apply_scheduler_s"]["count"] == 2
    assert rust_summary["phase_timings_s.apply_scheduler_selector_s"]["count"] == 2
    assert (
        rust_summary["phase_counters.after_write_root_safety_skipped_count"]["count"]
        == 2
    )
    assert (
        rust_summary["phase_counters.after_write_root_safety_executed_count"]["count"]
        == 2
    )
    assert rust_summary["phase_counters.before_digest_bytes_read_count"]["count"] == 2
    assert rust_summary["phase_counters.after_digest_bytes_hashed_count"]["count"] == 2
    assert rust_summary["phase_counters.after_digest_precomputed_count"]["count"] == 2
    assert rust_summary["phase_counters.apply_plan_delta_count"]["count"] == 2
    assert rust_summary["phase_counters.apply_plan_bucket_count"]["count"] == 2
    assert (
        rust_summary["phase_counters.apply_plan_parallel_safe_delta_count"]["count"]
        == 2
    )
    assert rust_summary["phase_counters.apply_plan_max_bucket_size_count"]["count"] == 2
    assert rust_summary["phase_counters.apply_scheduler_skipped_count"]["count"] == 2
    assert rust_summary["phase_counters.apply_scheduler_enabled_count"]["count"] == 2
    assert rust_summary["phase_counters.apply_scheduler_requested_count"]["count"] == 2
    assert rust_summary["phase_counters.apply_scheduler_selected_count"]["count"] == 2
    assert (
        rust_summary["phase_counters.apply_scheduler_sequential_fallback_count"][
            "count"
        ]
        == 2
    )
    assert (
        rust_summary["phase_counters.apply_scheduler_conflict_fallback_count"]["count"]
        == 2
    )
    assert (
        rust_summary["phase_counters.apply_scheduler_worker_floor_fallback_count"][
            "count"
        ]
        == 2
    )
    assert (
        rust_summary["phase_counters.apply_scheduler_empty_batch_fallback_count"][
            "count"
        ]
        == 2
    )
    assert (
        rust_summary["phase_counters.apply_scheduler_worker_execution_count"]["count"]
        == 2
    )
    assert rust_summary["content_engine.payload_count"]["count"] == 2
    assert rust_summary["content_engine.buffered_payload_count"]["count"] == 2
    assert rust_summary["content_engine.bytes_buffered"]["count"] == 2
    assert rust_summary["content_engine.chunk_count"]["count"] == 2
    assert rust_summary["phase_timings_s.total_profiled_apply_s"]["count"] == 2

    validated = validate_native_apply_benchmark_receipt(receipt)
    assert validated.parity.passed is True


def test_native_apply_benchmark_can_enable_parallel_scheduler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWARE_FILE_SYSTEM_NATIVE_APPLY_PARALLEL_WORKERS", "2")
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=2,
                payload_bytes=96,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    rust_sample = receipt["rust_backend"]["samples"][0]
    rust_phase_timings = rust_sample["phase_timings_s"]
    assert rust_phase_timings is not None
    assert rust_phase_timings["apply_scheduler_s"] > 0
    assert rust_phase_timings["apply_scheduler_selector_s"] > 0
    rust_phase_counters = rust_sample["phase_counters"]
    assert rust_phase_counters is not None
    assert rust_phase_counters["apply_scheduler_requested_count"] == 1
    assert rust_phase_counters["apply_scheduler_selected_count"] == 1
    assert rust_phase_counters["apply_scheduler_sequential_fallback_count"] == 0
    assert rust_phase_counters["apply_scheduler_conflict_fallback_count"] == 0
    assert rust_phase_counters["apply_scheduler_worker_floor_fallback_count"] == 0
    assert rust_phase_counters["apply_scheduler_empty_batch_fallback_count"] == 0
    assert rust_phase_counters["apply_scheduler_enabled_count"] == 1
    assert rust_phase_counters["apply_scheduler_skipped_count"] == 0
    assert rust_phase_counters["apply_scheduler_worker_count"] == 2
    assert (
        rust_phase_counters["apply_scheduler_parallel_delta_count"]
        == rust_sample["applied_path_count"]
    )
    assert rust_phase_counters["apply_scheduler_serial_conflict_delta_count"] == 0
    assert rust_phase_counters["apply_scheduler_worker_execution_count"] == 2
    assert receipt["parity"]["passed"] is True


def test_native_apply_benchmark_supports_scale_fixture_counts(
    tmp_path: Path,
) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                fixture_profile="delete_heavy_cleanup",
                files_per_operation=1,
                create_file_count=2,
                update_file_count=1,
                delete_file_count=4,
                payload_bytes=80,
                verify_digests=False,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert receipt["fixture"]["fixture_profile"] == "delete_heavy_cleanup"
    assert receipt["fixture"]["create_file_count"] == 2
    assert receipt["fixture"]["update_file_count"] == 1
    assert receipt["fixture"]["delete_file_count"] == 4
    assert receipt["fixture"]["digest_verification_enabled"] is False
    assert receipt["fixture"]["expected_applied_path_count"] == 7
    assert receipt["fixture"]["expected_digest_verified_count"] == 0

    python_sample = receipt["python_backend"]["samples"][0]
    rust_sample = receipt["rust_backend"]["samples"][0]
    assert python_sample["applied_path_count"] == 7
    assert rust_sample["applied_path_count"] == 7
    assert python_sample["digest_verified_count"] == 0
    assert rust_sample["digest_verified_count"] == 0
    assert python_sample["bytes_written_per_second"] >= 0
    assert rust_sample["bytes_written_per_second"] >= 0

    validated = validate_native_apply_benchmark_receipt(receipt)
    assert validated.fixture["expected_applied_path_count"] == 7


def test_native_apply_benchmark_can_time_persistent_service_backend(
    tmp_path: Path,
) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=80,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                rust_service_backend=True,
                rust_service_streaming_payload=True,
                rust_service_stream_chunk_bytes=16,
                payload_content_kind="bytes",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert receipt["rust_service_backend"]["backend_kind"] == "rust"
    assert (
        receipt["rust_service_backend"]["invocation_kind"]
        == "prepared_debug_service_binary"
    )
    assert receipt["rust_service_build"]["status"] == "succeeded"
    assert receipt["rust_service_execution"]["process_started_once"] is True
    assert receipt["rust_service_execution"]["ping"]["response"]["status"] == "ok"
    assert (
        receipt["rust_service_payload_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
    )
    assert (
        receipt["rust_service_response_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
    )
    assert (
        receipt["rust_service_request_handoff_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert receipt["parity"]["passed"] is True
    assert receipt["fixture"]["payload_content_kind"] == "bytes"

    python_sample = receipt["python_backend"]["samples"][0]
    service_sample = receipt["rust_service_backend"]["samples"][0]
    assert (
        service_sample["service_payload_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
    )
    assert (
        service_sample["service_response_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
    )
    assert (
        service_sample["service_request_handoff_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert service_sample["applied_path_count"] == python_sample["applied_path_count"]
    assert service_sample["bytes_written"] == python_sample["bytes_written"]
    assert service_sample["bytes_deleted"] == python_sample["bytes_deleted"]
    assert (
        service_sample["digest_verified_count"]
        == python_sample["digest_verified_count"]
    )
    assert service_sample["operations_per_second"] >= 0
    service_phase_timings = service_sample["phase_timings_s"]
    assert service_phase_timings is not None
    assert service_phase_timings["metadata_probe_s"] >= 0
    assert service_phase_timings["before_digest_hash_s"] >= 0
    assert service_phase_timings["after_digest_hash_s"] >= 0
    assert service_phase_timings["create_write_s"] >= 0
    assert service_phase_timings["update_write_s"] >= 0
    assert service_phase_timings["target_leaf_safety_s"] >= 0
    assert service_phase_timings["parent_descriptor_open_s"] >= 0
    assert service_phase_timings["dirfd_cache_lookup_s"] >= 0
    assert service_phase_timings["dirfd_chain_open_s"] >= 0
    assert service_phase_timings["dirfd_mkdir_s"] >= 0
    assert service_phase_timings["after_write_root_safety_s"] >= 0
    assert service_phase_timings["after_write_root_safety_gate_s"] >= 0
    assert service_phase_timings["json_encode_s"] >= 0
    service_phase_counters = service_sample["phase_counters"]
    assert service_phase_counters is not None
    assert service_phase_counters["before_digest_bytes_read_count"] >= 0
    assert service_phase_counters["after_digest_bytes_hashed_count"] >= 0
    assert service_phase_counters["after_digest_precomputed_count"] == 2
    assert service_phase_counters["after_digest_precomputed_bytes_hashed_count"] == (
        service_sample["bytes_written"]
    )
    service_content_engine = service_sample["content_engine"]
    assert service_content_engine is not None
    assert service_content_engine["engine_kind"] == "rust_apply_content_engine_v0"
    assert service_content_engine["streaming_capable"] is True
    assert service_content_engine["payload_count"] == 2
    assert service_content_engine["buffered_payload_count"] == 0
    assert service_content_engine["streamed_payload_count"] == 2
    assert service_content_engine["bytes_buffered"] == 0
    assert service_content_engine["bytes_streamed"] == service_sample["bytes_written"]
    assert service_content_engine["spooled_streamed_payload_count"] == 2
    assert service_content_engine["direct_streamed_payload_count"] == 0
    assert service_content_engine["bytes_spooled"] == service_sample["bytes_written"]
    assert service_content_engine["bytes_direct_streamed"] == 0
    assert service_content_engine["chunk_count"] > 2
    assert 0 < service_content_engine["max_chunk_bytes"] <= 16
    service_client_timings = service_sample["service_client_timings_s"]
    assert service_client_timings is not None
    assert service_client_timings["request_write_s"] >= 0
    assert service_client_timings["request_delta_metadata_write_s"] >= 0
    assert service_client_timings["request_content_materialize_s"] >= 0
    assert service_client_timings["request_payload_write_s"] >= 0
    assert service_client_timings["request_flush_s"] >= 0
    assert service_client_timings["response_read_s"] >= 0
    assert service_client_timings["response_decode_s"] >= 0
    assert service_client_timings["response_json_decode_s"] >= 0
    assert service_client_timings["response_report_expand_s"] >= 0
    assert service_client_timings["total_client_boundary_s"] >= 0
    service_client_counters = service_sample["service_client_counters"]
    assert service_client_counters is not None
    assert service_client_counters["request_byte_count"] > 0
    assert (
        service_client_counters["request_content_byte_count"]
        == service_sample["bytes_written"]
    )
    assert service_client_counters["request_protocol_byte_count"] > 0
    assert service_client_counters["request_payload_count"] == 2
    assert service_client_counters["request_buffered_payload_count"] == 0
    assert service_client_counters["request_streamed_payload_count"] == 2
    assert service_client_counters["request_spooled_streamed_payload_count"] == 2
    assert service_client_counters["request_direct_streamed_payload_count"] == 0
    assert service_client_counters["request_text_payload_count"] == 0
    assert service_client_counters["request_binary_payload_count"] == 2
    assert service_client_counters["request_stream_chunk_count"] == (
        service_content_engine["chunk_count"]
    )
    assert 0 < service_client_counters["request_max_chunk_bytes"] <= 16
    assert service_client_counters["request_write_call_count"] == 0
    assert service_client_counters["request_writev_call_count"] == 0
    assert service_client_counters["request_buffered_write_call_count"] > 0
    assert service_client_counters["request_vectored_payload_write_count"] == 0
    assert service_client_counters["request_vectored_payload_byte_count"] == 0
    assert service_client_counters["response_byte_count"] > 0
    if sys.platform != "win32":
        assert service_phase_counters["after_write_root_safety_skipped_count"] == 2
        assert service_phase_counters["after_write_root_safety_executed_count"] == 0
    else:
        assert service_phase_counters["after_write_root_safety_skipped_count"] == 0
        assert service_phase_counters["after_write_root_safety_executed_count"] == 2
    assert (
        receipt["rust_service_backend"]["summary"][
            "phase_timings_s.total_profiled_apply_s"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_timings_s.request_write_s"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_timings_s.request_payload_write_s"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_timings_s.response_report_expand_s"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_counters.request_byte_count"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_counters.request_content_byte_count"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_counters.request_streamed_payload_count"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_counters.request_stream_chunk_count"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_counters.request_buffered_write_call_count"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"]["content_engine.bytes_streamed"][
            "count"
        ]
        == 1
    )

    validated = validate_native_apply_benchmark_receipt(receipt)
    assert validated.rust_service_backend is not None


def test_native_apply_benchmark_can_time_direct_streaming_service_backend(
    tmp_path: Path,
) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=96,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                rust_service_backend=True,
                rust_service_direct_streaming_payload=True,
                rust_service_stream_chunk_bytes=16,
                payload_content_kind="bytes",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert (
        receipt["rust_service_payload_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
    )
    assert (
        receipt["rust_service_response_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
    )
    expected_handoff_protocol = (
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
        if hasattr(os, "writev")
        else RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert receipt["rust_service_request_handoff_protocol"] == expected_handoff_protocol
    assert receipt["parity"]["passed"] is True
    service_sample = receipt["rust_service_backend"]["samples"][0]
    assert (
        service_sample["service_payload_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
    )
    assert (
        service_sample["service_response_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
    )
    assert (
        service_sample["service_request_handoff_protocol"] == expected_handoff_protocol
    )
    service_content_engine = service_sample["content_engine"]
    assert service_content_engine is not None
    assert service_content_engine["payload_count"] == 2
    assert service_content_engine["buffered_payload_count"] == 0
    assert service_content_engine["streamed_payload_count"] == 2
    assert service_content_engine["spooled_streamed_payload_count"] == 0
    assert service_content_engine["direct_streamed_payload_count"] == 2
    assert service_content_engine["bytes_buffered"] == 0
    assert service_content_engine["bytes_spooled"] == 0
    assert service_content_engine["bytes_streamed"] == service_sample["bytes_written"]
    assert service_content_engine["bytes_direct_streamed"] == (
        service_sample["bytes_written"]
    )
    service_client_counters = service_sample["service_client_counters"]
    assert service_client_counters is not None
    assert service_client_counters["request_buffered_payload_count"] == 0
    assert service_client_counters["request_streamed_payload_count"] == 2
    assert service_client_counters["request_spooled_streamed_payload_count"] == 0
    assert service_client_counters["request_direct_streamed_payload_count"] == 2
    if expected_handoff_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
    ):
        assert service_client_counters["request_write_call_count"] > 0
        assert service_client_counters["request_writev_call_count"] > 0
        assert service_client_counters["request_buffered_write_call_count"] == 0
        assert service_client_counters["request_vectored_payload_write_count"] == (
            service_client_counters["request_stream_chunk_count"]
        )
        assert service_client_counters["request_vectored_payload_byte_count"] == (
            service_sample["bytes_written"]
        )
        assert service_client_counters["request_vectored_write_fallback_count"] == 0
    else:
        assert service_client_counters["request_write_call_count"] == 0
        assert service_client_counters["request_writev_call_count"] == 0
        assert service_client_counters["request_buffered_write_call_count"] > 0
    service_phase_timings = service_sample["phase_timings_s"]
    assert service_phase_timings is not None
    assert service_phase_timings["direct_stream_read_s"] >= 0
    assert service_phase_timings["direct_stream_file_write_s"] >= 0
    assert service_phase_timings["direct_stream_hash_s"] >= 0
    service_phase_counters = service_sample["phase_counters"]
    assert service_phase_counters is not None
    assert service_phase_counters["direct_stream_chunk_read_count"] == (
        service_content_engine["chunk_count"]
    )
    assert service_phase_counters["direct_stream_bytes_read_count"] == (
        service_sample["bytes_written"]
    )
    assert service_phase_counters["direct_stream_buffer_reuse_count"] == (
        service_content_engine["chunk_count"]
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "phase_timings_s.direct_stream_read_s"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "phase_timings_s.direct_stream_file_write_s"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "phase_counters.direct_stream_buffer_reuse_count"
        ]["count"]
        == 1
    )
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_counters.request_writev_call_count"
        ]["count"]
        == 1
    )


def test_native_apply_benchmark_can_time_rust_library_backend(
    tmp_path: Path,
) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=96,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                rust_library_backend=True,
                payload_content_kind="bytes",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert receipt["rust_library_backend"]["backend_kind"] == "rust"
    assert (
        receipt["rust_library_backend"]["invocation_kind"]
        == RUST_WORKSPACE_APPLY_LIBRARY_DEBUG_INVOCATION_KIND
    )
    assert receipt["rust_library_build"]["status"] == "succeeded"
    assert receipt["rust_library_execution"]["boundary_kind"] == (
        RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND
    )
    assert receipt["rust_library_execution"]["library_path"]
    assert receipt["parity"]["passed"] is True
    assert receipt["fixture"]["payload_content_kind"] == "bytes"

    python_sample = receipt["python_backend"]["samples"][0]
    library_sample = receipt["rust_library_backend"]["samples"][0]
    assert library_sample["library_boundary_kind"] == (
        RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND
    )
    assert library_sample["applied_path_count"] == python_sample["applied_path_count"]
    assert library_sample["bytes_written"] == python_sample["bytes_written"]
    assert library_sample["bytes_deleted"] == python_sample["bytes_deleted"]
    assert (
        library_sample["digest_verified_count"]
        == python_sample["digest_verified_count"]
    )
    assert library_sample["operations_per_second"] >= 0
    library_content_engine = library_sample["content_engine"]
    assert library_content_engine is not None
    assert library_content_engine["payload_count"] == 2
    assert library_content_engine["buffered_payload_count"] == 0
    assert library_content_engine["streamed_payload_count"] == 2
    assert library_content_engine["spooled_streamed_payload_count"] == 0
    assert library_content_engine["direct_streamed_payload_count"] == 2
    assert library_content_engine["bytes_buffered"] == 0
    assert library_content_engine["bytes_streamed"] == library_sample["bytes_written"]
    assert library_content_engine["bytes_spooled"] == 0
    assert (
        library_content_engine["bytes_direct_streamed"]
        == library_sample["bytes_written"]
    )
    library_phase_counters = library_sample["phase_counters"]
    assert library_phase_counters is not None
    assert library_phase_counters["after_digest_precomputed_count"] == 2
    assert (
        library_phase_counters["after_digest_precomputed_bytes_hashed_count"]
        == library_sample["bytes_written"]
    )
    assert library_phase_counters["direct_stream_chunk_read_count"] == 2
    assert (
        library_phase_counters["direct_stream_bytes_read_count"]
        == library_sample["bytes_written"]
    )
    assert receipt["rust_library_backend"]["summary"]["duration_s"]["count"] == 1
    assert (
        receipt["rust_library_backend"]["summary"][
            "content_engine.direct_streamed_payload_count"
        ]["count"]
        == 1
    )


def test_native_apply_benchmark_can_time_compact_response_service_backend(
    tmp_path: Path,
) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=96,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                rust_service_backend=True,
                rust_service_direct_streaming_payload=True,
                rust_service_stream_chunk_bytes=16,
                rust_service_compact_response=True,
                payload_content_kind="bytes",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert (
        receipt["rust_service_response_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL
    )
    assert receipt["parity"]["passed"] is True
    service_sample = receipt["rust_service_backend"]["samples"][0]
    assert service_sample["service_response_protocol"] == (
        RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL
    )
    assert service_sample["service_request_handoff_protocol"] in {
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL,
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL,
    }
    assert service_sample["service_client_counters"]["compact_response"] == 1
    assert service_sample["service_client_counters"]["response_byte_count"] > 0
    assert (
        receipt["rust_service_backend"]["summary"][
            "service_client_counters.compact_response"
        ]["count"]
        == 1
    )


def test_native_apply_benchmark_can_time_server_side_service_boundary(
    tmp_path: Path,
) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=96,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                rust_service_backend=True,
                rust_service_direct_streaming_payload=True,
                rust_service_stream_chunk_bytes=16,
                rust_service_compact_response=True,
                rust_service_server_timings=True,
                payload_content_kind="bytes",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert (
        receipt["rust_service_timing_protocol"]
        == RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL
    )
    service_sample = receipt["rust_service_backend"]["samples"][0]
    assert service_sample["service_server_timings_s"]["apply_s"] >= 0.0
    assert service_sample["service_server_timings_s"]["response_write_s"] >= 0.0
    assert (
        service_sample["service_server_flags"]["direct_stream_fused_request_apply"]
        is True
    )
    assert (
        receipt["rust_service_backend"]["summary"]["service_server_timings_s.apply_s"][
            "count"
        ]
        == 1
    )


def test_native_apply_benchmark_writes_receipt_file(tmp_path: Path) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=64,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                write_receipt=True,
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    receipt_path = Path(receipt["receipt_path"])
    assert receipt_path.parent == (
        tmp_path / "fixture" / ".aware" / "reports" / "file_system" / "performance"
    )
    assert receipt_path.is_file()
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == receipt


def test_native_apply_benchmark_cli_maps_scale_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured_configs: list[NativeApplyBenchmarkConfig] = []

    def fake_run(config: NativeApplyBenchmarkConfig) -> dict[str, object]:
        captured_configs.append(config)
        return {"ok": True}

    monkeypatch.setattr(benchmark_native_apply, "run_native_apply_benchmark", fake_run)

    exit_code = benchmark_native_apply.main(
        [
            "--fixture-root",
            (tmp_path / "fixture").as_posix(),
            "--target-dir",
            (tmp_path / "target").as_posix(),
            "--cargo-home",
            (tmp_path / "cargo-home").as_posix(),
            "--prepared-binary-path",
            (tmp_path / "native-apply").as_posix(),
            "--prepared-service-binary-path",
            (tmp_path / "native-apply-service").as_posix(),
            "--prepared-library-path",
            (tmp_path / "libaware-file-system-native.so").as_posix(),
            "--fixture-profile",
            "delete_heavy_cleanup",
            "--create-file-count",
            "2",
            "--update-file-count",
            "1",
            "--delete-file-count",
            "4",
            "--payload-bytes",
            "96",
            "--payload-content-kind",
            "bytes",
            "--iterations",
            "7",
            "--no-digest-verification",
            "--release",
            "--build-timeout-s",
            "12.5",
            "--rust-library-backend",
            "--rust-service-backend",
            "--rust-service-direct-streaming-payload",
            "--rust-service-stream-chunk-bytes",
            "2048",
            "--rust-service-compact-response",
            "--rust-service-server-timings",
            "--compact",
        ]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True}
    config = captured_configs[0]
    assert config.fixture_profile == "delete_heavy_cleanup"
    assert config.create_file_count == 2
    assert config.update_file_count == 1
    assert config.delete_file_count == 4
    assert config.payload_bytes == 96
    assert config.payload_content_kind == "bytes"
    assert config.iterations == 7
    assert config.verify_digests is False
    assert config.release is True
    assert config.build_timeout_s == 12.5
    assert config.cargo_home == tmp_path / "cargo-home"
    assert config.prepared_binary_path == tmp_path / "native-apply"
    assert config.prepared_service_binary_path == tmp_path / "native-apply-service"
    assert config.prepared_library_path == (tmp_path / "libaware-file-system-native.so")
    assert config.rust_library_backend is True
    assert config.rust_service_backend is True
    assert config.rust_service_streaming_payload is False
    assert config.rust_service_direct_streaming_payload is True
    assert config.rust_service_stream_chunk_bytes == 2048
    assert config.rust_service_compact_response is True
    assert config.rust_service_server_timings is True


def test_native_apply_benchmark_rejects_non_empty_fixture_root(
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir()
    (fixture_root / "existing.txt").write_text("do not overwrite\n", encoding="utf-8")

    with pytest.raises(ValueError, match="fixture root must be empty"):
        run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=64,
                iterations=1,
                fixture_root=fixture_root,
                target_dir=tmp_path / "cargo-target",
            )
        )


def test_native_apply_benchmark_rejects_compact_response_without_service(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="compact response requires"):
        run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=64,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                rust_service_compact_response=True,
            )
        )


def test_native_apply_benchmark_rejects_server_timings_without_service(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="server timings requires"):
        run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=64,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
                rust_service_server_timings=True,
            )
        )


def test_native_apply_benchmark_validation_requires_passing_parity(
    tmp_path: Path,
) -> None:
    try:
        receipt = run_native_apply_benchmark(
            NativeApplyBenchmarkConfig(
                files_per_operation=1,
                payload_bytes=64,
                iterations=1,
                fixture_root=tmp_path / "fixture",
                target_dir=tmp_path / "cargo-target",
            )
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    receipt["parity"]["passed"] = False
    receipt["parity"]["mismatches"] = ["forced mismatch"]

    with pytest.raises(ValueError, match="passing parity"):
        validate_native_apply_benchmark_receipt(receipt)
