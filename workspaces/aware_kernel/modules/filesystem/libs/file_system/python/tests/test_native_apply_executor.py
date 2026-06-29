from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.native_apply import (  # noqa: E402
    NativeApplyUnavailable,
    WorkspaceApplyDelta,
    assert_workspace_apply_parity,
    collect_python_workspace_apply,
)
from aware_file_system.native_apply_executor import (  # noqa: E402
    RUST_WORKSPACE_APPLY_DEBUG_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND,
    RUST_WORKSPACE_APPLY_LIBRARY_DEBUG_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_PREPARED_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_DEBUG_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND,
    RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL,
    RustWorkspaceApplyService,
    RustWorkspaceApplyExecutor,
    RustWorkspaceApplyExecutorConfig,
    RustWorkspaceApplyLibraryExecutorConfig,
    collect_prepared_rust_workspace_apply,
    collect_prepared_rust_workspace_apply_library,
    measure_rust_workspace_apply_persistent_boundary,
    measure_rust_workspace_apply_startup,
    prepare_rust_workspace_apply_executor,
    prepare_rust_workspace_apply_library_executor,
    prepare_rust_workspace_apply_service_executor,
)


def test_prepare_rust_workspace_apply_executor_accepts_existing_binary(
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "aware-file-system-native-apply"
    binary_path.write_text("#!/usr/bin/env sh\n", encoding="utf-8")

    executor = prepare_rust_workspace_apply_executor(
        RustWorkspaceApplyExecutorConfig(prepared_binary_path=binary_path)
    )

    assert executor.binary_path == binary_path.resolve()
    assert executor.invocation_kind == RUST_WORKSPACE_APPLY_PREPARED_INVOCATION_KIND
    assert executor.rust_build is None


def test_prepare_rust_workspace_apply_executor_rejects_missing_binary(
    tmp_path: Path,
) -> None:
    with pytest.raises(NativeApplyUnavailable, match="does not exist"):
        prepare_rust_workspace_apply_executor(
            RustWorkspaceApplyExecutorConfig(
                prepared_binary_path=tmp_path / "missing-native-apply"
            )
        )


def test_prepare_rust_workspace_apply_library_executor_rejects_missing_library(
    tmp_path: Path,
) -> None:
    with pytest.raises(NativeApplyUnavailable, match="does not exist"):
        prepare_rust_workspace_apply_library_executor(
            RustWorkspaceApplyLibraryExecutorConfig(
                prepared_library_path=tmp_path / "missing-native-apply-library.so"
            )
        )


def test_measure_rust_workspace_apply_startup_uses_prepared_binary(
    tmp_path: Path,
) -> None:
    binary_path = tmp_path / "fake-native-apply"
    report = json.dumps(
        {
            "backend_kind": "rust",
            "benchmark_version": "aware.file_system.workspace_fs_benchmark.v1",
            "operation": "workspace_apply_deltas",
            "root_path": "/tmp",
            "entries": [],
            "applied_path_count": 0,
            "bytes_written": 0,
            "bytes_deleted": 0,
            "digest_verified_count": 0,
            "materialized_artifact_count": 0,
            "stored_artifact_count": 0,
        }
    )
    binary_path.write_text(
        f"#!/usr/bin/env sh\nprintf '%s\\n' '{report}'\n",
        encoding="utf-8",
    )
    binary_path.chmod(0o755)
    executor = RustWorkspaceApplyExecutor(
        binary_path=binary_path,
        invocation_kind=RUST_WORKSPACE_APPLY_PREPARED_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
    )

    receipt = measure_rust_workspace_apply_startup(
        executor=executor,
        root=tmp_path / "startup-root",
        iterations=2,
    )

    assert receipt["probe_kind"] == "missing_file_delete"
    assert receipt["invocation_kind"] == RUST_WORKSPACE_APPLY_PREPARED_INVOCATION_KIND
    assert receipt["sample_count"] == 2
    assert receipt["summary"]["duration_s"]["count"] == 2


def test_rust_workspace_apply_service_uses_length_prefixed_protocol(
    tmp_path: Path,
) -> None:
    service_binary = _write_fake_apply_service(tmp_path)
    executor = RustWorkspaceApplyExecutor(
        binary_path=service_binary,
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
    )
    content = "hello\nfrom persistent service\n"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()

    with RustWorkspaceApplyService(executor) as service:
        assert service.ping()["operation"] == "ping"
        report = service.apply(
            tmp_path,
            (
                WorkspaceApplyDelta(
                    operation="create",
                    path="generated/service.txt",
                    content_text=content,
                    expected_sha256=f"sha256:{digest}",
                ),
            ),
        )

    assert report.backend_kind == "rust"
    assert report.applied_path_count == 1
    assert report.bytes_written == len(content.encode("utf-8"))
    assert report.digest_verified_count == 1
    assert report.entries[0].path == "generated/service.txt"
    assert service.last_apply_client_timings_s is not None
    assert service.last_apply_client_timings_s["request_write_s"] >= 0
    assert service.last_apply_client_timings_s["request_root_resolve_s"] >= 0
    assert service.last_apply_client_timings_s["request_control_write_s"] >= 0
    assert service.last_apply_client_timings_s["request_delta_metadata_write_s"] >= 0
    assert service.last_apply_client_timings_s["request_content_materialize_s"] >= 0
    assert service.last_apply_client_timings_s["request_payload_write_s"] >= 0
    assert service.last_apply_client_timings_s["request_flush_s"] >= 0
    assert service.last_apply_client_timings_s["request_profiled_s"] >= 0
    assert service.last_apply_client_timings_s["request_unprofiled_s"] >= 0
    assert service.last_apply_client_timings_s["response_read_s"] >= 0
    assert service.last_apply_client_timings_s["response_decode_s"] >= 0
    assert service.last_apply_client_timings_s["response_json_decode_s"] >= 0
    assert service.last_apply_client_timings_s["response_report_expand_s"] >= 0
    assert service.last_apply_client_timings_s["response_profiled_s"] >= 0
    assert service.last_apply_client_timings_s["response_unprofiled_s"] >= 0
    assert service.last_apply_client_timings_s["total_client_boundary_s"] >= 0
    assert service.last_apply_client_counters is not None
    assert service.last_apply_client_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_PAYLOAD_PROTOCOL
    )
    assert service.last_apply_client_response_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_FULL_RESPONSE_PROTOCOL
    )
    assert service.last_apply_client_request_handoff_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert service.last_apply_client_counters["request_byte_count"] > 0
    assert service.last_apply_client_counters["request_content_byte_count"] == len(
        content.encode("utf-8")
    )
    assert service.last_apply_client_counters["request_protocol_byte_count"] > 0
    assert service.last_apply_client_counters["request_payload_count"] == 1
    assert service.last_apply_client_counters["request_buffered_payload_count"] == 1
    assert service.last_apply_client_counters["request_streamed_payload_count"] == 0
    assert service.last_apply_client_counters["request_text_payload_count"] == 1
    assert service.last_apply_client_counters["request_binary_payload_count"] == 0
    assert service.last_apply_client_counters["request_stream_chunk_count"] == 0
    assert service.last_apply_client_counters["request_max_chunk_bytes"] == 0
    assert service.last_apply_client_counters["request_write_call_count"] == 0
    assert service.last_apply_client_counters["request_writev_call_count"] == 0
    assert service.last_apply_client_counters["request_buffered_write_call_count"] > 0
    assert (
        service.last_apply_client_counters["request_vectored_payload_write_count"] == 0
    )
    assert (
        service.last_apply_client_counters["request_vectored_payload_byte_count"] == 0
    )
    assert service.last_apply_client_counters["response_byte_count"] > 0
    assert service.last_apply_client_counters["compact_response"] == 0


def test_rust_workspace_apply_service_can_stream_chunked_payloads(
    tmp_path: Path,
) -> None:
    service_binary = _write_fake_apply_service(tmp_path)
    executor = RustWorkspaceApplyExecutor(
        binary_path=service_binary,
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
    )
    content = b"chunked payload through fake service"
    digest = hashlib.sha256(content).hexdigest()

    with RustWorkspaceApplyService(executor) as service:
        report = service.apply(
            tmp_path,
            (
                WorkspaceApplyDelta(
                    operation="create",
                    path="generated/service.bin",
                    content_bytes=content,
                    expected_sha256=f"sha256:{digest}",
                ),
            ),
            stream_payloads=True,
            stream_chunk_bytes=7,
        )

    assert report.backend_kind == "rust"
    assert report.applied_path_count == 1
    assert report.bytes_written == len(content)
    assert report.digest_verified_count == 1
    assert report.content_engine is not None
    assert report.content_engine["payload_count"] == 1
    assert report.content_engine["buffered_payload_count"] == 0
    assert report.content_engine["streamed_payload_count"] == 1
    assert report.content_engine["bytes_buffered"] == 0
    assert report.content_engine["bytes_streamed"] == len(content)
    expected_chunk_count = (len(content) + 6) // 7
    assert report.content_engine["chunk_count"] == expected_chunk_count
    assert report.content_engine["max_chunk_bytes"] == 7
    assert service.last_apply_client_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_STREAMING_PAYLOAD_PROTOCOL
    )
    assert service.last_apply_client_request_handoff_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert service.last_apply_client_counters is not None
    assert service.last_apply_client_counters["request_content_byte_count"] == len(
        content
    )
    assert service.last_apply_client_counters["request_payload_count"] == 1
    assert service.last_apply_client_counters["request_buffered_payload_count"] == 0
    assert service.last_apply_client_counters["request_streamed_payload_count"] == 1
    assert service.last_apply_client_counters["request_binary_payload_count"] == 1
    assert service.last_apply_client_counters["request_text_payload_count"] == 0
    assert (
        service.last_apply_client_counters["request_stream_chunk_count"]
        == expected_chunk_count
    )
    assert service.last_apply_client_counters["request_max_chunk_bytes"] == 7
    assert service.last_apply_client_counters["request_write_call_count"] == 0
    assert service.last_apply_client_counters["request_writev_call_count"] == 0
    assert service.last_apply_client_counters["request_buffered_write_call_count"] > 0
    assert (
        service.last_apply_client_counters["request_vectored_payload_write_count"] == 0
    )


def test_rust_workspace_apply_service_can_direct_stream_chunked_payloads(
    tmp_path: Path,
) -> None:
    service_binary = _write_fake_apply_service(tmp_path)
    executor = RustWorkspaceApplyExecutor(
        binary_path=service_binary,
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
    )
    content = b"direct chunked payload through fake service"
    digest = hashlib.sha256(content).hexdigest()

    with RustWorkspaceApplyService(executor) as service:
        report = service.apply(
            tmp_path,
            (
                WorkspaceApplyDelta(
                    operation="create",
                    path="generated/direct-service.bin",
                    content_bytes=content,
                    expected_sha256=f"sha256:{digest}",
                ),
            ),
            direct_stream_payloads=True,
            stream_chunk_bytes=9,
        )

    assert report.backend_kind == "rust"
    assert report.applied_path_count == 1
    assert report.bytes_written == len(content)
    assert report.digest_verified_count == 1
    assert report.content_engine is not None
    assert report.content_engine["payload_count"] == 1
    assert report.content_engine["buffered_payload_count"] == 0
    assert report.content_engine["streamed_payload_count"] == 1
    assert report.content_engine["bytes_buffered"] == 0
    assert report.content_engine["bytes_streamed"] == len(content)
    assert report.content_engine["direct_streamed_payload_count"] == 1
    assert report.content_engine["spooled_streamed_payload_count"] == 0
    assert report.content_engine["bytes_direct_streamed"] == len(content)
    assert report.content_engine["bytes_spooled"] == 0
    expected_chunk_count = (len(content) + 8) // 9
    assert report.content_engine["chunk_count"] == expected_chunk_count
    assert report.content_engine["max_chunk_bytes"] == 9
    assert service.last_apply_client_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
    )
    expected_handoff_protocol = (
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
        if hasattr(os, "writev")
        else RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL
    )
    assert service.last_apply_client_request_handoff_protocol == (
        expected_handoff_protocol
    )
    assert service.last_apply_client_counters is not None
    assert service.last_apply_client_counters["request_content_byte_count"] == len(
        content
    )
    assert service.last_apply_client_counters["request_payload_count"] == 1
    assert service.last_apply_client_counters["request_buffered_payload_count"] == 0
    assert service.last_apply_client_counters["request_streamed_payload_count"] == 1
    assert (
        service.last_apply_client_counters["request_spooled_streamed_payload_count"]
        == 0
    )
    assert (
        service.last_apply_client_counters["request_direct_streamed_payload_count"] == 1
    )
    assert service.last_apply_client_counters["request_binary_payload_count"] == 1
    assert (
        service.last_apply_client_counters["request_stream_chunk_count"]
        == expected_chunk_count
    )
    assert service.last_apply_client_counters["request_max_chunk_bytes"] == 9
    if expected_handoff_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL
    ):
        assert service.last_apply_client_counters["request_write_call_count"] > 0
        assert service.last_apply_client_counters["request_writev_call_count"] > 0
        assert (
            service.last_apply_client_counters["request_buffered_write_call_count"] == 0
        )
        assert (
            service.last_apply_client_counters["request_vectored_payload_write_count"]
            == expected_chunk_count
        )
        assert service.last_apply_client_counters[
            "request_vectored_payload_byte_count"
        ] == len(content)
        assert (
            service.last_apply_client_counters["request_vectored_write_fallback_count"]
            == 0
        )
    else:
        assert service.last_apply_client_counters["request_write_call_count"] == 0
        assert service.last_apply_client_counters["request_writev_call_count"] == 0
        assert (
            service.last_apply_client_counters["request_buffered_write_call_count"] > 0
        )


def test_rust_workspace_apply_service_expands_compact_response(
    tmp_path: Path,
) -> None:
    service_binary = _write_fake_apply_service(tmp_path)
    executor = RustWorkspaceApplyExecutor(
        binary_path=service_binary,
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
    )
    content = b"compact direct chunked payload through fake service"
    digest = hashlib.sha256(content).hexdigest()

    with RustWorkspaceApplyService(executor) as service:
        report = service.apply(
            tmp_path,
            (
                WorkspaceApplyDelta(
                    operation="create",
                    path="generated/compact-direct-service.bin",
                    content_bytes=content,
                    expected_sha256=f"sha256:{digest}",
                ),
            ),
            direct_stream_payloads=True,
            stream_chunk_bytes=11,
            compact_response=True,
            server_timings=True,
        )

    assert report.backend_kind == "rust"
    assert report.applied_path_count == 1
    assert report.bytes_written == len(content)
    assert report.digest_verified_count == 1
    assert report.entries[0].path == "generated/compact-direct-service.bin"
    assert report.entries[0].after_sha256 == digest
    assert report.content_engine is not None
    assert report.content_engine["direct_streamed_payload_count"] == 1
    assert report.phase_timings is not None
    assert report.phase_timings["unit"] == "nanoseconds"
    assert report.phase_timings["target_leaf_open_count"] == 0
    assert report.phase_timings["target_leaf_open_ns"] == 0
    assert service.last_apply_client_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
    )
    assert service.last_apply_client_response_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL
    )
    assert service.last_apply_client_request_handoff_protocol in {
        RUST_WORKSPACE_APPLY_SERVICE_BUFFERED_REQUEST_HANDOFF_PROTOCOL,
        RUST_WORKSPACE_APPLY_SERVICE_VECTORED_REQUEST_HANDOFF_PROTOCOL,
    }
    assert service.last_apply_client_counters is not None
    assert service.last_apply_client_counters["compact_response"] == 1
    assert service.last_apply_client_counters["server_timings"] == 1
    assert service.last_apply_client_counters["response_byte_count"] > 0
    assert service.last_apply_server_timing_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL
    )
    assert service.last_apply_server_timings_s is not None
    assert service.last_apply_server_timings_s["apply_s"] >= 0.0
    assert service.last_apply_server_timings_s["response_write_s"] >= 0.0
    assert service.last_apply_server_flags == {
        "direct_stream_fused_request_apply": True
    }


def test_measure_rust_workspace_apply_persistent_boundary_uses_one_service_process(
    tmp_path: Path,
) -> None:
    service_binary = _write_fake_apply_service(tmp_path)
    executor = RustWorkspaceApplyExecutor(
        binary_path=service_binary,
        invocation_kind=RUST_WORKSPACE_APPLY_SERVICE_PREPARED_INVOCATION_KIND,
        manifest_path=tmp_path / "Cargo.toml",
        target_dir=tmp_path / "target",
    )

    receipt = measure_rust_workspace_apply_persistent_boundary(
        executor=executor,
        root=tmp_path / "persistent-root",
        iterations=3,
    )

    assert receipt["probe_kind"] == "persistent_missing_file_delete"
    assert receipt["boundary_kind"] == "persistent_process"
    assert receipt["process_started_once"] is True
    assert receipt["sample_count"] == 3
    assert receipt["ping"]["response"]["operation"] == "ping"
    assert receipt["summary"]["duration_s"]["count"] == 3


def test_prepared_rust_workspace_apply_matches_python_apply(tmp_path: Path) -> None:
    python_root = tmp_path / "python-workspace"
    rust_root = tmp_path / "rust-workspace"
    _write_apply_fixture(python_root)
    shutil.copytree(python_root, rust_root)
    client_content = "def generated_home_client():\n    return 'prepared'\n"
    existing_content = "prepared update\n"
    digest = hashlib.sha256(client_content.encode("utf-8")).hexdigest()
    deltas = (
        WorkspaceApplyDelta(
            operation="create",
            path="generated/home-api/src/client.py",
            content_text=client_content,
            expected_sha256=f"sha256:{digest}",
        ),
        WorkspaceApplyDelta(
            operation="update",
            path="generated/existing.py",
            content_text=existing_content,
        ),
        WorkspaceApplyDelta(operation="delete", path="stale.txt"),
    )

    python_report = collect_python_workspace_apply(python_root, deltas)
    try:
        executor = prepare_rust_workspace_apply_executor(
            RustWorkspaceApplyExecutorConfig(target_dir=tmp_path / "cargo-target")
        )
        rust_report = collect_prepared_rust_workspace_apply(
            rust_root,
            deltas,
            executor=executor,
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert executor.invocation_kind == RUST_WORKSPACE_APPLY_DEBUG_INVOCATION_KIND
    assert executor.rust_build is not None
    assert executor.rust_build["status"] == "succeeded"
    assert_workspace_apply_parity(
        python_report=python_report,
        rust_report=rust_report,
    )
    assert rust_report.phase_timings is not None
    assert rust_report.phase_timings["after_digest_precomputed_count"] == 0
    assert rust_report.phase_timings["after_digest_precomputed_bytes_hashed_count"] == 0


def test_prepared_rust_workspace_apply_service_matches_python_apply(
    tmp_path: Path,
) -> None:
    python_root = tmp_path / "python-workspace"
    rust_root = tmp_path / "rust-workspace"
    _write_apply_fixture(python_root)
    shutil.copytree(python_root, rust_root)
    client_content = "def generated_home_client():\n    return 'service'\n"
    existing_content = "service update\n"
    digest = hashlib.sha256(client_content.encode("utf-8")).hexdigest()
    deltas = (
        WorkspaceApplyDelta(
            operation="create",
            path="generated/home-api/src/client.py",
            content_text=client_content,
            expected_sha256=f"sha256:{digest}",
        ),
        WorkspaceApplyDelta(
            operation="update",
            path="generated/existing.py",
            content_text=existing_content,
        ),
        WorkspaceApplyDelta(operation="delete", path="stale.txt"),
    )

    python_report = collect_python_workspace_apply(python_root, deltas)
    try:
        executor = prepare_rust_workspace_apply_service_executor(
            RustWorkspaceApplyExecutorConfig(target_dir=tmp_path / "cargo-target")
        )
        with RustWorkspaceApplyService(executor) as service:
            rust_report = service.apply(
                rust_root,
                deltas,
                direct_stream_payloads=True,
                stream_chunk_bytes=4,
            )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert (
        executor.invocation_kind == RUST_WORKSPACE_APPLY_SERVICE_DEBUG_INVOCATION_KIND
    )
    assert executor.rust_build is not None
    assert executor.rust_build["status"] == "succeeded"
    assert_workspace_apply_parity(
        python_report=python_report,
        rust_report=rust_report,
    )
    assert rust_report.phase_timings is not None
    assert rust_report.phase_timings["after_digest_precomputed_count"] == 2
    assert (
        rust_report.phase_timings["after_digest_precomputed_bytes_hashed_count"]
        == rust_report.bytes_written
    )


def test_prepared_rust_workspace_apply_service_matches_python_binary_apply(
    tmp_path: Path,
) -> None:
    python_root = tmp_path / "python-workspace"
    rust_root = tmp_path / "rust-workspace"
    _write_apply_fixture(python_root)
    shutil.copytree(python_root, rust_root)
    binary_content = b"\x00\xffaware-binary-payload\n\x10\x80"
    digest = hashlib.sha256(binary_content).hexdigest()
    deltas = (
        WorkspaceApplyDelta(
            operation="create",
            path="generated/binary/blob.bin",
            content_bytes=binary_content,
            expected_sha256=f"sha256:{digest}",
        ),
    )

    python_report = collect_python_workspace_apply(python_root, deltas)
    try:
        executor = prepare_rust_workspace_apply_service_executor(
            RustWorkspaceApplyExecutorConfig(target_dir=tmp_path / "cargo-target")
        )
        with RustWorkspaceApplyService(executor) as service:
            rust_report = service.apply(
                rust_root,
                deltas,
                direct_stream_payloads=True,
                stream_chunk_bytes=4,
            )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert_workspace_apply_parity(
        python_report=python_report,
        rust_report=rust_report,
    )
    assert (rust_root / "generated/binary/blob.bin").read_bytes() == binary_content
    assert rust_report.phase_timings is not None
    assert rust_report.phase_timings["after_digest_precomputed_count"] == 1
    assert rust_report.phase_timings[
        "after_digest_precomputed_bytes_hashed_count"
    ] == len(binary_content)
    assert rust_report.content_engine is not None
    assert rust_report.content_engine["payload_count"] == 1
    assert rust_report.content_engine["buffered_payload_count"] == 0
    assert rust_report.content_engine["streamed_payload_count"] == 1
    assert rust_report.content_engine["bytes_buffered"] == 0
    assert rust_report.content_engine["bytes_streamed"] == len(binary_content)
    assert rust_report.content_engine["direct_streamed_payload_count"] == 1
    assert rust_report.content_engine["spooled_streamed_payload_count"] == 0
    assert rust_report.content_engine["bytes_direct_streamed"] == len(binary_content)
    assert rust_report.content_engine["bytes_spooled"] == 0
    assert rust_report.content_engine["chunk_count"] == (len(binary_content) + 3) // 4
    assert rust_report.content_engine["max_chunk_bytes"] == 4
    assert service.last_apply_client_protocol == (
        RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL
    )
    assert service.last_apply_client_counters is not None
    assert service.last_apply_client_counters["request_content_byte_count"] == len(
        binary_content
    )
    assert service.last_apply_client_counters["request_payload_count"] == 1
    assert service.last_apply_client_counters["request_buffered_payload_count"] == 0
    assert service.last_apply_client_counters["request_streamed_payload_count"] == 1
    assert (
        service.last_apply_client_counters["request_spooled_streamed_payload_count"]
        == 0
    )
    assert (
        service.last_apply_client_counters["request_direct_streamed_payload_count"] == 1
    )
    assert service.last_apply_client_counters["request_binary_payload_count"] == 1
    assert service.last_apply_client_counters["request_text_payload_count"] == 0
    assert (
        service.last_apply_client_counters["request_stream_chunk_count"]
        == (len(binary_content) + 3) // 4
    )
    assert service.last_apply_client_counters["request_max_chunk_bytes"] == 4


def test_prepared_rust_workspace_apply_library_matches_python_binary_apply(
    tmp_path: Path,
) -> None:
    python_root = tmp_path / "python-workspace"
    rust_root = tmp_path / "rust-workspace"
    _write_apply_fixture(python_root)
    shutil.copytree(python_root, rust_root)
    binary_content = b"\x00\xffaware-library-payload\n\x10\x80"
    digest = hashlib.sha256(binary_content).hexdigest()
    deltas = (
        WorkspaceApplyDelta(
            operation="create",
            path="generated/library/blob.bin",
            content_bytes=binary_content,
            expected_sha256=f"sha256:{digest}",
        ),
        WorkspaceApplyDelta(operation="delete", path="stale.txt"),
    )

    python_report = collect_python_workspace_apply(python_root, deltas)
    try:
        executor = prepare_rust_workspace_apply_library_executor(
            RustWorkspaceApplyLibraryExecutorConfig(
                target_dir=tmp_path / "cargo-target"
            )
        )
        rust_report = collect_prepared_rust_workspace_apply_library(
            rust_root,
            deltas,
            executor=executor,
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert (
        executor.invocation_kind == RUST_WORKSPACE_APPLY_LIBRARY_DEBUG_INVOCATION_KIND
    )
    assert executor.boundary_kind == RUST_WORKSPACE_APPLY_LIBRARY_BOUNDARY_KIND
    assert executor.rust_build is not None
    assert executor.rust_build["status"] == "succeeded"
    assert executor.library_path.is_file()
    assert_workspace_apply_parity(
        python_report=python_report,
        rust_report=rust_report,
    )
    assert (rust_root / "generated/library/blob.bin").read_bytes() == binary_content
    assert rust_report.content_engine is not None
    assert rust_report.content_engine["payload_count"] == 1
    assert rust_report.content_engine["buffered_payload_count"] == 0
    assert rust_report.content_engine["streamed_payload_count"] == 1
    assert rust_report.content_engine["spooled_streamed_payload_count"] == 0
    assert rust_report.content_engine["direct_streamed_payload_count"] == 1
    assert rust_report.content_engine["bytes_buffered"] == 0
    assert rust_report.content_engine["bytes_streamed"] == len(binary_content)
    assert rust_report.content_engine["bytes_spooled"] == 0
    assert rust_report.content_engine["bytes_direct_streamed"] == len(binary_content)
    assert rust_report.phase_timings is not None
    assert rust_report.phase_timings["after_digest_precomputed_count"] == 1
    assert rust_report.phase_timings[
        "after_digest_precomputed_bytes_hashed_count"
    ] == len(binary_content)
    assert rust_report.phase_timings["direct_stream_chunk_read_count"] == 1
    assert rust_report.phase_timings["direct_stream_bytes_read_count"] == len(
        binary_content
    )


def _write_apply_fixture(root: Path) -> None:
    _write(root / "aware.workspace.toml", "[workspace]\n")
    _write(root / "stale.txt", "stale")
    _write(root / "generated/existing.py", "old\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_fake_apply_service(tmp_path: Path) -> Path:
    service_path = tmp_path / "fake-native-apply-service"
    service_path.write_text(
        """#!/usr/bin/env python3
import hashlib
import json
import sys

stdin = sys.stdin.buffer

def read_line():
    line = stdin.readline()
    if not line:
        return None
    return line.rstrip(b"\\r\\n").decode("utf-8")

def read_string():
    size = int(read_line())
    if size < 0:
        return None
    return stdin.read(size).decode("utf-8")

def read_bytes():
    size = int(read_line())
    if size < 0:
        return None
    return stdin.read(size)

def read_streamed_bytes():
    size = int(read_line())
    if size < 0:
        return None, 0, 0
    chunk_count = int(read_line())
    chunks = []
    max_chunk_bytes = 0
    for _ in range(chunk_count):
        chunk_size = int(read_line())
        chunk = stdin.read(chunk_size)
        chunks.append(chunk)
        max_chunk_bytes = max(max_chunk_bytes, len(chunk))
    content = b"".join(chunks)
    if len(content) != size:
        raise RuntimeError("streamed byte count mismatch")
    return content, chunk_count, max_chunk_bytes

def digest(value):
    if value is None:
        return None
    return hashlib.sha256(value).hexdigest()

def compact_report(report):
    return {
        "s": "aware.file_system.workspace_apply_service_response.v1",
        "f": "compact_apply_report_v1",
        "r": [
            report["backend_kind"],
            report["benchmark_version"],
            report["operation"],
            "sha2_asm_optimized",
            report["root_path"],
            report["applied_path_count"],
            report["bytes_written"],
            report["bytes_deleted"],
            report["digest_verified_count"],
            report["materialized_artifact_count"],
            report["stored_artifact_count"],
        ],
        "c": [
            report["content_engine"]["engine_kind"],
            report["content_engine"]["streaming_capable"],
            report["content_engine"]["payload_count"],
            report["content_engine"]["buffered_payload_count"],
            report["content_engine"]["streamed_payload_count"],
            report["content_engine"]["bytes_buffered"],
            report["content_engine"]["bytes_streamed"],
            report["content_engine"]["spooled_streamed_payload_count"],
            report["content_engine"]["direct_streamed_payload_count"],
            report["content_engine"]["bytes_spooled"],
            report["content_engine"]["bytes_direct_streamed"],
            report["content_engine"]["chunk_count"],
            report["content_engine"]["max_chunk_bytes"],
        ],
        "e": [
            [
                entry["before_exists"],
                entry["after_exists"],
                entry["before_sha256"],
                None
                if entry["after_sha256"] == entry["expected_sha256"]
                else entry["after_sha256"],
                entry["bytes_written"],
                entry["bytes_deleted"],
                entry["digest_verified"],
            ]
            for entry in report["entries"]
        ],
        "p": ["nanoseconds"] + [0] * 79,
    }

while True:
    command = read_line()
    if command is None:
        break
    if command == "PING":
        print(json.dumps({"status": "ok", "operation": "ping"}), flush=True)
        continue
    if command == "EXIT":
        print(json.dumps({"status": "ok", "operation": "exit"}), flush=True)
        break
    timed_response = command.endswith("_TIMED")
    command = command.removesuffix("_TIMED")
    compact_response = command.endswith("_COMPACT")
    base_command = command.removesuffix("_COMPACT")
    if base_command not in {"APPLY", "APPLY_STREAM", "APPLY_DIRECT_STREAM"}:
        print(json.dumps({"status": "error", "message": command}), flush=True)
        continue
    streaming = base_command in {"APPLY_STREAM", "APPLY_DIRECT_STREAM"}
    direct_streaming = base_command == "APPLY_DIRECT_STREAM"
    root = read_string()
    count = int(read_line())
    entries = []
    bytes_written = 0
    digest_verified_count = 0
    payload_count = 0
    buffered_payload_count = 0
    streamed_payload_count = 0
    spooled_streamed_payload_count = 0
    direct_streamed_payload_count = 0
    bytes_buffered = 0
    bytes_streamed = 0
    bytes_spooled = 0
    bytes_direct_streamed = 0
    total_chunk_count = 0
    total_max_chunk_bytes = 0
    for _ in range(count):
        operation = read_string()
        path = read_string()
        expected = read_string()
        if streaming:
            content, chunk_count, max_chunk_bytes = read_streamed_bytes()
        else:
            content = read_bytes()
            chunk_count = 1 if content else 0
            max_chunk_bytes = len(content) if content else 0
        normalized_expected = None
        if expected:
            normalized_expected = expected.removeprefix("sha256:")
        after_sha = digest(content) if operation in {"create", "update"} else None
        written = len(content) if content is not None else 0
        bytes_written += written
        if content is not None:
            payload_count += 1
            total_chunk_count += chunk_count
            total_max_chunk_bytes = max(total_max_chunk_bytes, max_chunk_bytes)
            if streaming:
                streamed_payload_count += 1
                bytes_streamed += written
                if direct_streaming:
                    direct_streamed_payload_count += 1
                    bytes_direct_streamed += written
                else:
                    spooled_streamed_payload_count += 1
                    bytes_spooled += written
            else:
                buffered_payload_count += 1
                bytes_buffered += written
        digest_verified = normalized_expected is not None
        digest_verified_count += 1 if digest_verified else 0
        entries.append(
            {
                "path": path,
                "operation": operation,
                "before_exists": False,
                "after_exists": operation != "delete",
                "before_sha256": None,
                "after_sha256": after_sha,
                "expected_sha256": normalized_expected,
                "bytes_written": written,
                "bytes_deleted": 0,
                "digest_verified": digest_verified,
            }
        )
    report = {
        "backend_kind": "rust",
        "benchmark_version": "aware.file_system.workspace_fs_benchmark.v1",
        "operation": "workspace_apply_deltas",
        "root_path": root,
        "entries": entries,
        "applied_path_count": len(entries),
        "bytes_written": bytes_written,
        "bytes_deleted": 0,
        "digest_verified_count": digest_verified_count,
        "materialized_artifact_count": 0,
        "stored_artifact_count": 0,
        "content_engine": {
            "engine_kind": "rust_apply_content_engine_v0",
            "streaming_capable": True,
            "payload_count": payload_count,
            "buffered_payload_count": buffered_payload_count,
            "streamed_payload_count": streamed_payload_count,
            "bytes_buffered": bytes_buffered,
            "bytes_streamed": bytes_streamed,
            "spooled_streamed_payload_count": spooled_streamed_payload_count,
            "direct_streamed_payload_count": direct_streamed_payload_count,
            "bytes_spooled": bytes_spooled,
            "bytes_direct_streamed": bytes_direct_streamed,
            "chunk_count": total_chunk_count,
            "max_chunk_bytes": total_max_chunk_bytes,
        },
    }
    print(json.dumps(compact_report(report) if compact_response else report), flush=True)
    if timed_response:
        print(json.dumps({
            "schema": "aware.file_system.workspace_apply_service_timing.v1",
            "protocol": "timing_trailer_json_v1",
            "unit": "nanoseconds",
            "request_read_ns": 0,
            "apply_ns": 1000,
            "response_encode_ns": 2000,
            "response_write_ns": 3000,
            "total_service_ns": 6000,
            "direct_stream_fused_request_apply": direct_streaming,
        }), flush=True)
""",
        encoding="utf-8",
    )
    service_path.chmod(0o755)
    return service_path
