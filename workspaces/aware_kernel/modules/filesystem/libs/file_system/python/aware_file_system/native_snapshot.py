from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence

from aware_file_system.benchmark_receipt_contract import (
    WORKSPACE_FS_BENCHMARK_VERSION,
)
from aware_file_system.config import CanonicalSourceFilterConfig, Config, FileSystemConfig
from aware_file_system.index.file_system_index import FileSystemIndex
from aware_file_system.native_backend import (
    RUST_BACKEND_KIND,
    WORKSPACE_SNAPSHOT_OPERATION,
)


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshotEntry:
    path: str
    size: int
    mtime_ns: int
    depth: int


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshot:
    backend_kind: str
    benchmark_version: str
    operation: str
    root_path: str
    entries: tuple[WorkspaceSnapshotEntry, ...]
    directories_scanned: int | None = None
    files_seen: int | None = None

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(entry.path for entry in self.entries)

    @property
    def by_path(self) -> dict[str, WorkspaceSnapshotEntry]:
        return {entry.path: entry for entry in self.entries}


class WorkspaceSnapshotParityError(AssertionError):
    pass


class NativeSnapshotUnavailable(RuntimeError):
    pass


def collect_python_workspace_snapshot(
    root: Path,
    *,
    cache_dir: Path | None = None,
) -> WorkspaceSnapshot:
    root_path = root.expanduser().resolve()
    if cache_dir is not None:
        return _collect_python_workspace_snapshot_with_cache(
            root_path=root_path,
            cache_dir=cache_dir.expanduser().resolve(),
        )
    with TemporaryDirectory(prefix="aware-fs-python-snapshot-") as raw_cache_dir:
        return _collect_python_workspace_snapshot_with_cache(
            root_path=root_path,
            cache_dir=Path(raw_cache_dir),
        )


def collect_rust_workspace_snapshot(
    root: Path,
    *,
    cargo_path: Path | None = None,
    manifest_path: Path | None = None,
    target_dir: Path | None = None,
) -> WorkspaceSnapshot:
    resolved_cargo = _resolve_cargo(cargo_path)
    resolved_manifest = manifest_path or _default_rust_manifest_path()
    command = [
        str(resolved_cargo),
        "run",
        "--quiet",
        "--manifest-path",
        str(resolved_manifest),
        "--bin",
        "aware-file-system-native-snapshot",
        "--",
        str(root.expanduser().resolve()),
    ]
    env = os.environ.copy()
    if target_dir is not None:
        env["CARGO_TARGET_DIR"] = str(target_dir.expanduser().resolve())

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        raise NativeSnapshotUnavailable(
            "Rust workspace snapshot command failed: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    return workspace_snapshot_from_mapping(json.loads(completed.stdout))


def workspace_snapshot_from_mapping(raw: Mapping[str, Any]) -> WorkspaceSnapshot:
    entries = tuple(
        sorted(
            (
                WorkspaceSnapshotEntry(
                    path=str(entry["path"]),
                    size=int(entry["size"]),
                    mtime_ns=int(entry["mtime_ns"]),
                    depth=int(entry["depth"]),
                )
                for entry in _list_value(raw.get("entries"))
            ),
            key=lambda entry: entry.path,
        )
    )
    return WorkspaceSnapshot(
        backend_kind=str(raw.get("backend_kind", "")),
        benchmark_version=str(raw.get("benchmark_version", "")),
        operation=str(raw.get("operation", "")),
        root_path=str(raw.get("root_path", "")),
        entries=entries,
        directories_scanned=_optional_int(raw.get("directories_scanned")),
        files_seen=_optional_int(raw.get("files_seen")),
    )


def assert_workspace_snapshot_parity(
    *,
    python_snapshot: WorkspaceSnapshot,
    rust_snapshot: WorkspaceSnapshot,
) -> None:
    if rust_snapshot.backend_kind != RUST_BACKEND_KIND:
        raise WorkspaceSnapshotParityError(
            f"Rust snapshot backend mismatch: {rust_snapshot.backend_kind!r}"
        )
    if rust_snapshot.benchmark_version != WORKSPACE_FS_BENCHMARK_VERSION:
        raise WorkspaceSnapshotParityError(
            "Rust snapshot benchmark contract mismatch: "
            f"{rust_snapshot.benchmark_version!r}"
        )
    if rust_snapshot.operation != WORKSPACE_SNAPSHOT_OPERATION:
        raise WorkspaceSnapshotParityError(
            f"Rust snapshot operation mismatch: {rust_snapshot.operation!r}"
        )
    if python_snapshot.paths != rust_snapshot.paths:
        raise WorkspaceSnapshotParityError(
            "Workspace snapshot path mismatch: "
            f"python={python_snapshot.paths!r} rust={rust_snapshot.paths!r}"
        )

    python_by_path = python_snapshot.by_path
    rust_by_path = rust_snapshot.by_path
    for relative_path, python_entry in python_by_path.items():
        rust_entry = rust_by_path[relative_path]
        if python_entry.size != rust_entry.size:
            raise WorkspaceSnapshotParityError(
                f"Workspace snapshot size mismatch for {relative_path!r}: "
                f"python={python_entry.size} rust={rust_entry.size}"
            )
        if python_entry.depth != rust_entry.depth:
            raise WorkspaceSnapshotParityError(
                f"Workspace snapshot depth mismatch for {relative_path!r}: "
                f"python={python_entry.depth} rust={rust_entry.depth}"
            )
        if python_entry.mtime_ns != rust_entry.mtime_ns:
            raise WorkspaceSnapshotParityError(
                f"Workspace snapshot mtime_ns mismatch for {relative_path!r}: "
                f"python={python_entry.mtime_ns} rust={rust_entry.mtime_ns}"
            )


def _collect_python_workspace_snapshot_with_cache(
    *,
    root_path: Path,
    cache_dir: Path,
) -> WorkspaceSnapshot:
    index = FileSystemIndex(
        Config(
            file_system=FileSystemConfig(
                root_path=root_path.as_posix(),
                generate_tree=False,
                export_json=False,
            ),
            filter=CanonicalSourceFilterConfig(),
        ),
        cache_dir=cache_dir.as_posix(),
    )
    _scan_result, current_files = index.scan_relative_metadata(force_refresh=True)
    entries = tuple(
        sorted(
            (
                WorkspaceSnapshotEntry(
                    path=relative_path,
                    size=metadata.size,
                    mtime_ns=metadata.mtime_ns,
                    depth=metadata.depth,
                )
                for relative_path, metadata in current_files.items()
            ),
            key=lambda entry: entry.path,
        )
    )
    return WorkspaceSnapshot(
        backend_kind="python",
        benchmark_version=WORKSPACE_FS_BENCHMARK_VERSION,
        operation=WORKSPACE_SNAPSHOT_OPERATION,
        root_path=root_path.as_posix(),
        entries=entries,
    )


def _default_rust_manifest_path() -> Path:
    file_system_root = Path(__file__).resolve().parents[2]
    return file_system_root / "rust" / "aware_file_system_native" / "Cargo.toml"


def _resolve_cargo(cargo_path: Path | None) -> Path:
    if cargo_path is not None:
        return cargo_path.expanduser().resolve()
    discovered = shutil.which("cargo")
    if discovered:
        return Path(discovered)
    home_cargo = Path.home() / ".cargo" / "bin" / "cargo"
    if home_cargo.exists():
        return home_cargo
    raise NativeSnapshotUnavailable("cargo is not available on PATH")


def _list_value(value: object) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float | str):
        return int(value)
    return None
