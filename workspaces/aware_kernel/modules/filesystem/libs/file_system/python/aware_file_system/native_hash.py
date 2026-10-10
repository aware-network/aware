from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from aware_file_system.benchmark_receipt_contract import (
    WORKSPACE_FS_BENCHMARK_VERSION,
)
from aware_file_system.native_backend import (
    RUST_BACKEND_KIND,
    WORKSPACE_HASHES_OPERATION,
)


@dataclass(frozen=True, slots=True)
class WorkspaceHashEntry:
    path: str
    sha256: str
    size: int
    bytes_read: int


@dataclass(frozen=True, slots=True)
class WorkspaceHashReport:
    backend_kind: str
    benchmark_version: str
    operation: str
    root_path: str
    entries: tuple[WorkspaceHashEntry, ...]
    cache_hits: int
    cache_misses: int
    bytes_read: int

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(entry.path for entry in self.entries)

    @property
    def by_path(self) -> dict[str, WorkspaceHashEntry]:
        return {entry.path: entry for entry in self.entries}


class WorkspaceHashParityError(AssertionError):
    pass


class NativeHashUnavailable(RuntimeError):
    pass


def collect_python_workspace_hashes(
    root: Path,
    relative_paths: Sequence[str],
) -> WorkspaceHashReport:
    root_path = root.expanduser().resolve()
    entries: list[WorkspaceHashEntry] = []
    for relative_path in _normalized_relative_paths(relative_paths):
        absolute_path = (root_path / relative_path).resolve()
        _ensure_within_root(root_path=root_path, path=absolute_path)
        digest, bytes_read = _sha256_file(absolute_path)
        entries.append(
            WorkspaceHashEntry(
                path=relative_path,
                sha256=digest,
                size=absolute_path.stat().st_size,
                bytes_read=bytes_read,
            )
        )
    total_bytes = sum(entry.bytes_read for entry in entries)
    return WorkspaceHashReport(
        backend_kind="python",
        benchmark_version=WORKSPACE_FS_BENCHMARK_VERSION,
        operation=WORKSPACE_HASHES_OPERATION,
        root_path=root_path.as_posix(),
        entries=tuple(entries),
        cache_hits=0,
        cache_misses=len(entries),
        bytes_read=total_bytes,
    )


def collect_rust_workspace_hashes(
    root: Path,
    relative_paths: Sequence[str],
    *,
    cargo_path: Path | None = None,
    manifest_path: Path | None = None,
    target_dir: Path | None = None,
) -> WorkspaceHashReport:
    resolved_cargo = _resolve_cargo(cargo_path)
    resolved_manifest = manifest_path or _default_rust_manifest_path()
    command = [
        str(resolved_cargo),
        "run",
        "--quiet",
        "--manifest-path",
        str(resolved_manifest),
        "--bin",
        "aware-file-system-native-hash",
        "--",
        str(root.expanduser().resolve()),
        *_normalized_relative_paths(relative_paths),
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
        raise NativeHashUnavailable(
            "Rust workspace hash command failed: "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    return workspace_hash_report_from_mapping(json.loads(completed.stdout))


def workspace_hash_report_from_mapping(raw: Mapping[str, Any]) -> WorkspaceHashReport:
    entries = tuple(
        sorted(
            (
                WorkspaceHashEntry(
                    path=str(entry["path"]),
                    sha256=str(entry["sha256"]),
                    size=int(entry["size"]),
                    bytes_read=int(entry["bytes_read"]),
                )
                for entry in _list_value(raw.get("entries"))
            ),
            key=lambda entry: entry.path,
        )
    )
    return WorkspaceHashReport(
        backend_kind=str(raw.get("backend_kind", "")),
        benchmark_version=str(raw.get("benchmark_version", "")),
        operation=str(raw.get("operation", "")),
        root_path=str(raw.get("root_path", "")),
        entries=entries,
        cache_hits=int(raw.get("cache_hits", 0)),
        cache_misses=int(raw.get("cache_misses", 0)),
        bytes_read=int(raw.get("bytes_read", 0)),
    )


def assert_workspace_hash_parity(
    *,
    python_report: WorkspaceHashReport,
    rust_report: WorkspaceHashReport,
) -> None:
    if rust_report.backend_kind != RUST_BACKEND_KIND:
        raise WorkspaceHashParityError(
            f"Rust hash backend mismatch: {rust_report.backend_kind!r}"
        )
    if rust_report.benchmark_version != WORKSPACE_FS_BENCHMARK_VERSION:
        raise WorkspaceHashParityError(
            f"Rust hash benchmark mismatch: {rust_report.benchmark_version!r}"
        )
    if rust_report.operation != WORKSPACE_HASHES_OPERATION:
        raise WorkspaceHashParityError(
            f"Rust hash operation mismatch: {rust_report.operation!r}"
        )
    if python_report.paths != rust_report.paths:
        raise WorkspaceHashParityError(
            "Workspace hash path mismatch: "
            f"python={python_report.paths!r} rust={rust_report.paths!r}"
        )

    python_by_path = python_report.by_path
    rust_by_path = rust_report.by_path
    for relative_path, python_entry in python_by_path.items():
        rust_entry = rust_by_path[relative_path]
        if python_entry.sha256 != rust_entry.sha256:
            raise WorkspaceHashParityError(
                f"Workspace hash digest mismatch for {relative_path!r}"
            )
        if python_entry.size != rust_entry.size:
            raise WorkspaceHashParityError(
                f"Workspace hash size mismatch for {relative_path!r}"
            )
        if python_entry.bytes_read != rust_entry.bytes_read:
            raise WorkspaceHashParityError(
                f"Workspace hash bytes_read mismatch for {relative_path!r}"
            )

    if rust_report.cache_hits != 0:
        raise WorkspaceHashParityError("Rust hash v0 must not claim cache hits")
    if rust_report.cache_misses != len(rust_report.entries):
        raise WorkspaceHashParityError("Rust hash cache_misses must match entry count")
    if rust_report.bytes_read != python_report.bytes_read:
        raise WorkspaceHashParityError("Rust hash total bytes_read mismatch")


def _sha256_file(path: Path) -> tuple[str, int]:
    hasher = hashlib.sha256()
    bytes_read = 0
    with path.open("rb") as file:
        while True:
            chunk = file.read(131_072)
            if not chunk:
                break
            bytes_read += len(chunk)
            hasher.update(chunk)
    return hasher.hexdigest(), bytes_read


def _normalized_relative_paths(relative_paths: Sequence[str]) -> tuple[str, ...]:
    normalized = set()
    for relative_path in relative_paths:
        path = Path(relative_path.replace("\\", "/"))
        if not relative_path or path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Workspace hash path must stay within root: {relative_path}")
        normalized.add(path.as_posix())
    return tuple(sorted(normalized))


def _ensure_within_root(*, root_path: Path, path: Path) -> None:
    try:
        path.relative_to(root_path)
    except ValueError as exc:
        raise ValueError(f"Workspace hash path escapes root: {path}") from exc


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
    raise NativeHashUnavailable("cargo is not available on PATH")


def _list_value(value: object) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))
