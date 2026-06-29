from __future__ import annotations

import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.native_snapshot import (  # noqa: E402
    NativeSnapshotUnavailable,
    WorkspaceSnapshot,
    WorkspaceSnapshotEntry,
    WorkspaceSnapshotParityError,
    assert_workspace_snapshot_parity,
    collect_python_workspace_snapshot,
    collect_rust_workspace_snapshot,
)


def test_rust_workspace_snapshot_matches_python_canonical_snapshot(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    _write_snapshot_fixture(root)

    python_snapshot = collect_python_workspace_snapshot(
        root,
        cache_dir=tmp_path / "python-cache",
    )
    try:
        rust_snapshot = collect_rust_workspace_snapshot(
            root,
            target_dir=tmp_path / "cargo-target",
        )
    except NativeSnapshotUnavailable as exc:
        pytest.skip(str(exc))

    assert_workspace_snapshot_parity(
        python_snapshot=python_snapshot,
        rust_snapshot=rust_snapshot,
    )
    assert set(python_snapshot.paths) == {
        ".gitignore",
        "assets/config.aware",
        "aware.workspace.toml",
        "demo/root.aware",
        "docs/README.md",
        "migrations/001_init.sql",
        "tests/test_root.py",
    }
    assert rust_snapshot.files_seen is not None
    assert rust_snapshot.files_seen > len(rust_snapshot.entries)


def test_workspace_snapshot_parity_reports_metadata_mismatch() -> None:
    python_snapshot = WorkspaceSnapshot(
        backend_kind="python",
        benchmark_version="aware.file_system.workspace_fs_benchmark.v1",
        operation="workspace_snapshot",
        root_path="/tmp/python",
        entries=(
            WorkspaceSnapshotEntry(
                path="demo/root.aware",
                size=6,
                mtime_ns=1,
                depth=1,
            ),
        ),
    )
    rust_snapshot = WorkspaceSnapshot(
        backend_kind="rust",
        benchmark_version="aware.file_system.workspace_fs_benchmark.v1",
        operation="workspace_snapshot",
        root_path="/tmp/rust",
        entries=(
            WorkspaceSnapshotEntry(
                path="demo/root.aware",
                size=7,
                mtime_ns=1,
                depth=1,
            ),
        ),
    )

    with pytest.raises(WorkspaceSnapshotParityError, match="size mismatch"):
        assert_workspace_snapshot_parity(
            python_snapshot=python_snapshot,
            rust_snapshot=rust_snapshot,
        )


def _write_snapshot_fixture(root: Path) -> None:
    _write(root / "aware.workspace.toml", "[workspace]\nname = \"native-snapshot\"\n")
    _write(root / ".gitignore", "*.skip\n")
    _write(root / "demo" / "root.aware", "source\n")
    _write(root / "docs" / "README.md", "source\n")
    _write(root / "migrations" / "001_init.sql", "source\n")
    _write(root / "assets" / "config.aware", "source\n")
    _write(root / "tests" / "test_root.py", "source\n")
    _write(root / ".aware" / "cache.json", "{}\n")
    _write(root / "_aware" / "cache.json", "{}\n")
    _write(root / "node_modules" / "pkg" / "ignored.js", "ignored\n")
    _write(root / "build" / "generated" / "ignored.py", "ignored\n")
    _write(root / "target" / "debug" / "ignored", "ignored\n")
    _write(root / "ignored_by_gitignore.skip", "ignored\n")
    _write(root / "compiled.pyc", "ignored\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
