from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.native_snapshot import (  # noqa: E402
    WorkspaceSnapshot,
    WorkspaceSnapshotEntry,
    WorkspaceSnapshotParityError,
    assert_workspace_snapshot_parity,
    collect_python_workspace_snapshot,
    collect_rust_workspace_snapshot,
    workspace_snapshot_delta,
    workspace_snapshot_delta_digest,
    workspace_snapshot_digest,
)


def test_rust_workspace_snapshot_matches_python_canonical_snapshot(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    _write_snapshot_fixture(root)

    python_snapshot = collect_python_workspace_snapshot(
        root,
        cache_dir=tmp_path / "python-cache",
    )
    rust_snapshot = collect_rust_workspace_snapshot(
        root,
        target_dir=tmp_path / "cargo-target",
    )

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
    assert rust_snapshot.semantics_engine == "ignore-0.4.33-root-gitignore-only"
    assert rust_snapshot.inventory_digest == workspace_snapshot_digest(
        rust_snapshot.entries
    )
    assert rust_snapshot.errors == ()


def test_rust_workspace_snapshot_matches_adversarial_gitignore_and_symlinks(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    _write_adversarial_snapshot_fixture(root)
    external = tmp_path / "outside.txt"
    external.write_text("must-not-enter\n", encoding="utf-8")
    os.symlink(root / "authored.txt", root / "internal-file-link.txt")
    os.symlink(external, root / "external-file-link.txt")
    os.symlink(root / "missing.txt", root / "broken-file-link.txt")

    python_snapshot = collect_python_workspace_snapshot(
        root,
        cache_dir=tmp_path / "python-cache",
    )
    rust_snapshot = collect_rust_workspace_snapshot(
        root,
        target_dir=tmp_path / "cargo-target",
    )

    assert_workspace_snapshot_parity(
        python_snapshot=python_snapshot,
        rust_snapshot=rust_snapshot,
    )
    assert set(python_snapshot.paths) == {
        "!literal",
        "#literal",
        ".cache/authored.txt",
        ".gitignore",
        ".github/workflows/check.yml",
        "authored.txt",
        "internal-file-link.txt",
        "keep.tmp",
        "nested/.gitignore",
        "nested/deep/keep.txt",
        "nested/keep.log",
        "nested/root-only.txt",
    }


def test_python_and_rust_snapshot_deltas_match_mutations(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    _write(root / ".gitignore", "*.blocked\n")
    _write(root / "update.txt", "before\n")
    _write(root / "delete.txt", "delete\n")
    _write(root / "rename-before.txt", "rename\n")
    _write(root / "ignore-change.blocked", "ignored\n")
    cargo_target = tmp_path / "cargo-target"

    python_before = collect_python_workspace_snapshot(
        root,
        cache_dir=tmp_path / "python-before-cache",
    )
    rust_before = collect_rust_workspace_snapshot(root, target_dir=cargo_target)
    assert_workspace_snapshot_parity(
        python_snapshot=python_before,
        rust_snapshot=rust_before,
    )

    _write(root / "create.txt", "created\n")
    _write(root / "update.txt", "after-with-new-size\n")
    (root / "delete.txt").unlink()
    (root / "rename-before.txt").rename(root / "rename-after.txt")
    _write(root / ".gitignore", "# now admitted\n")

    python_after = collect_python_workspace_snapshot(
        root,
        cache_dir=tmp_path / "python-after-cache",
    )
    rust_after = collect_rust_workspace_snapshot(root, target_dir=cargo_target)
    assert_workspace_snapshot_parity(
        python_snapshot=python_after,
        rust_snapshot=rust_after,
    )

    python_delta = workspace_snapshot_delta(python_before, python_after)
    rust_delta = workspace_snapshot_delta(rust_before, rust_after)
    assert python_delta == rust_delta
    assert workspace_snapshot_delta_digest(
        python_delta
    ) == workspace_snapshot_delta_digest(rust_delta)
    assert python_delta.added == (
        "create.txt",
        "ignore-change.blocked",
        "rename-after.txt",
    )
    assert python_delta.modified == (".gitignore", "update.txt")
    assert python_delta.deleted == ("delete.txt", "rename-before.txt")


def test_rust_workspace_snapshot_matches_internal_directory_symlink_policy(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    _write(root / "real" / "source.txt", "source\n")
    os.symlink(root / "real", root / "linked")
    os.symlink(root, root / "real" / "cycle")

    python_snapshot = collect_python_workspace_snapshot(
        root,
        cache_dir=tmp_path / "python-cache",
    )
    rust_snapshot = collect_rust_workspace_snapshot(
        root,
        target_dir=tmp_path / "cargo-target",
    )

    assert_workspace_snapshot_parity(
        python_snapshot=python_snapshot,
        rust_snapshot=rust_snapshot,
    )


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
    _write(root / "aware.workspace.toml", '[workspace]\nname = "native-snapshot"\n')
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


def _write_adversarial_snapshot_fixture(root: Path) -> None:
    _write(
        root / ".gitignore",
        "\n".join(
            (
                "*.tmp",
                "!keep.tmp",
                "/root-only.txt",
                "logs/**/debug.log",
                "ignored/",
                "!ignored/cannot-reinclude.txt",
                r"\#ignored-literal",
                r"\!ignored-literal",
                "trailing-space.txt   ",
                "*.log",
                "",
            )
        ),
    )
    _write(root / "authored.txt", "source\n")
    _write(root / "keep.tmp", "source\n")
    _write(root / "drop.tmp", "ignored\n")
    _write(root / "root-only.txt", "ignored\n")
    _write(root / "nested" / "root-only.txt", "source\n")
    _write(root / "logs" / "a" / "b" / "debug.log", "ignored\n")
    _write(root / "ignored" / "cannot-reinclude.txt", "ignored\n")
    _write(root / "#ignored-literal", "ignored\n")
    _write(root / "!ignored-literal", "ignored\n")
    _write(root / "trailing-space.txt", "ignored\n")
    _write(root / "#literal", "source\n")
    _write(root / "!literal", "source\n")
    _write(root / "nested" / ".gitignore", "!keep.log\n**/drop.txt\n")
    _write(root / "nested" / "keep.log", "source\n")
    _write(root / "nested" / "drop.log", "ignored\n")
    _write(root / "nested" / "deep" / "keep.txt", "source\n")
    _write(root / "nested" / "deep" / "drop.txt", "ignored\n")
    _write(root / ".github" / "workflows" / "check.yml", "source\n")
    _write(root / ".cache" / "authored.txt", "source\n")
    _write(root / ".local" / "ignored.txt", "ignored\n")
    _write(root / ".uv_cache" / "ignored.txt", "ignored\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
