from __future__ import annotations

import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.native_hash import (  # noqa: E402
    NativeHashUnavailable,
    WorkspaceHashEntry,
    WorkspaceHashParityError,
    WorkspaceHashReport,
    assert_workspace_hash_parity,
    collect_python_workspace_hashes,
    collect_rust_workspace_hashes,
)


def test_rust_workspace_hashes_match_python_hashlib(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    _write(root / "demo" / "root.aware", "abc")
    _write(root / "z-last.txt", "last\n")
    _write(root / "empty.txt", "")
    requested_paths = (
        "z-last.txt",
        "demo/root.aware",
        "demo/root.aware",
        "empty.txt",
    )

    python_report = collect_python_workspace_hashes(root, requested_paths)
    try:
        rust_report = collect_rust_workspace_hashes(
            root,
            requested_paths,
            target_dir=tmp_path / "cargo-target",
        )
    except NativeHashUnavailable as exc:
        pytest.skip(str(exc))

    assert_workspace_hash_parity(
        python_report=python_report,
        rust_report=rust_report,
    )
    assert rust_report.paths == ("demo/root.aware", "empty.txt", "z-last.txt")
    assert rust_report.by_path["demo/root.aware"].sha256 == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    assert rust_report.cache_hits == 0
    assert rust_report.cache_misses == 3


def test_workspace_hash_parity_reports_digest_mismatch() -> None:
    python_report = WorkspaceHashReport(
        backend_kind="python",
        benchmark_version="aware.file_system.workspace_fs_benchmark.v1",
        operation="workspace_hashes",
        root_path="/tmp/python",
        entries=(
            WorkspaceHashEntry(
                path="demo/root.aware",
                sha256="a" * 64,
                size=3,
                bytes_read=3,
            ),
        ),
        cache_hits=0,
        cache_misses=1,
        bytes_read=3,
    )
    rust_report = WorkspaceHashReport(
        backend_kind="rust",
        benchmark_version="aware.file_system.workspace_fs_benchmark.v1",
        operation="workspace_hashes",
        root_path="/tmp/rust",
        entries=(
            WorkspaceHashEntry(
                path="demo/root.aware",
                sha256="b" * 64,
                size=3,
                bytes_read=3,
            ),
        ),
        cache_hits=0,
        cache_misses=1,
        bytes_read=3,
    )

    with pytest.raises(WorkspaceHashParityError, match="digest mismatch"):
        assert_workspace_hash_parity(
            python_report=python_report,
            rust_report=rust_report,
        )


def test_python_workspace_hashes_reject_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="within root"):
        collect_python_workspace_hashes(tmp_path, ("../outside.txt",))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
