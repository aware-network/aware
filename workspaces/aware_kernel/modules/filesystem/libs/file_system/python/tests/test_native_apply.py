from __future__ import annotations

import hashlib
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
    WorkspaceApplyEntry,
    WorkspaceApplyParityError,
    WorkspaceApplyReport,
    assert_workspace_apply_parity,
    collect_python_workspace_apply,
    collect_rust_workspace_apply,
    workspace_apply_report_from_mapping,
)


def test_rust_workspace_apply_matches_python_apply(tmp_path: Path) -> None:
    python_root = tmp_path / "python-workspace"
    rust_root = tmp_path / "rust-workspace"
    _write_apply_fixture(python_root)
    shutil.copytree(python_root, rust_root)
    client_content = "def generated_home_client():\n    return 'ready'\n"
    existing_content = "new\n"
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
        WorkspaceApplyDelta(
            operation="delete",
            path="stale.txt",
        ),
    )

    python_report = collect_python_workspace_apply(python_root, deltas)
    try:
        rust_report = collect_rust_workspace_apply(
            rust_root,
            deltas,
            target_dir=tmp_path / "cargo-target",
        )
    except NativeApplyUnavailable as exc:
        pytest.skip(str(exc))

    assert_workspace_apply_parity(
        python_report=python_report,
        rust_report=rust_report,
    )
    assert rust_report.applied_path_count == 3
    assert rust_report.digest_verified_count == 1
    assert rust_report.stored_artifact_count == 0
    assert (rust_root / "generated/home-api/src/client.py").read_text(
        encoding="utf-8"
    ) == client_content
    assert (rust_root / "generated/existing.py").read_text(
        encoding="utf-8"
    ) == existing_content
    assert not (rust_root / "stale.txt").exists()


def test_workspace_apply_parity_reports_entry_mismatch() -> None:
    python_report = WorkspaceApplyReport(
        backend_kind="python",
        benchmark_version="aware.file_system.workspace_fs_benchmark.v1",
        operation="workspace_apply_deltas",
        root_path="/tmp/python",
        entries=(
            WorkspaceApplyEntry(
                path="generated/client.py",
                operation="update",
                before_exists=False,
                after_exists=True,
                before_sha256=None,
                after_sha256="a" * 64,
                expected_sha256=None,
                bytes_written=3,
                bytes_deleted=0,
                digest_verified=False,
            ),
        ),
        applied_path_count=1,
        bytes_written=3,
        bytes_deleted=0,
        digest_verified_count=0,
        materialized_artifact_count=0,
        stored_artifact_count=0,
    )
    rust_report = WorkspaceApplyReport(
        backend_kind="rust",
        benchmark_version="aware.file_system.workspace_fs_benchmark.v1",
        operation="workspace_apply_deltas",
        root_path="/tmp/rust",
        entries=(
            WorkspaceApplyEntry(
                path="generated/client.py",
                operation="update",
                before_exists=False,
                after_exists=True,
                before_sha256=None,
                after_sha256="b" * 64,
                expected_sha256=None,
                bytes_written=3,
                bytes_deleted=0,
                digest_verified=False,
            ),
        ),
        applied_path_count=1,
        bytes_written=3,
        bytes_deleted=0,
        digest_verified_count=0,
        materialized_artifact_count=0,
        stored_artifact_count=0,
    )

    with pytest.raises(WorkspaceApplyParityError, match="entry mismatch"):
        assert_workspace_apply_parity(
            python_report=python_report,
            rust_report=rust_report,
        )


def test_python_workspace_apply_rejects_parent_traversal(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    with pytest.raises(ValueError, match="within root"):
        collect_python_workspace_apply(
            root,
            (
                WorkspaceApplyDelta(
                    operation="update",
                    path="../outside.txt",
                    content_text="escape\n",
                ),
            ),
        )


def test_python_workspace_apply_writes_binary_payload(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    content = b"\x00aware-binary\n\xff"
    digest = hashlib.sha256(content).hexdigest()

    report = collect_python_workspace_apply(
        root,
        (
            WorkspaceApplyDelta(
                operation="create",
                path="generated/blob.bin",
                content_bytes=content,
                expected_sha256=f"sha256:{digest}",
            ),
        ),
    )

    assert report.bytes_written == len(content)
    assert report.digest_verified_count == 1
    assert report.entries[0].after_sha256 == digest
    assert (root / "generated/blob.bin").read_bytes() == content


def test_workspace_apply_report_preserves_content_engine_receipt() -> None:
    report = workspace_apply_report_from_mapping(
        {
            "backend_kind": "rust",
            "benchmark_version": "aware.file_system.workspace_fs_benchmark.v1",
            "operation": "workspace_apply_deltas",
            "root_path": "/tmp/workspace",
            "applied_path_count": 1,
            "bytes_written": 5,
            "bytes_deleted": 0,
            "digest_verified_count": 1,
            "materialized_artifact_count": 0,
            "stored_artifact_count": 0,
            "digest_backend_kind": "libcrypto_evp",
            "content_engine": {
                "engine_kind": "rust_apply_content_engine_v0",
                "streaming_capable": True,
                "payload_count": 1,
                "buffered_payload_count": 1,
                "streamed_payload_count": 0,
                "bytes_buffered": 5,
                "bytes_streamed": 0,
                "chunk_count": 1,
                "max_chunk_bytes": 5,
            },
            "entries": [
                {
                    "path": "generated/client.py",
                    "operation": "update",
                    "before_exists": False,
                    "after_exists": True,
                    "before_sha256": None,
                    "after_sha256": "a" * 64,
                    "expected_sha256": "a" * 64,
                    "bytes_written": 5,
                    "bytes_deleted": 0,
                    "digest_verified": True,
                }
            ],
        }
    )

    assert report.content_engine is not None
    assert report.content_engine["engine_kind"] == "rust_apply_content_engine_v0"
    assert report.content_engine["streaming_capable"] is True
    assert report.content_engine["bytes_buffered"] == 5
    assert report.content_engine["streamed_payload_count"] == 0
    assert report.digest_backend_kind == "libcrypto_evp"


def _write_apply_fixture(root: Path) -> None:
    _write(root / "aware.workspace.toml", "[workspace]\n")
    _write(root / "stale.txt", "stale")
    _write(root / "generated/existing.py", "old\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
