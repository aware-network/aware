from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from aware_file_system.benchmark_receipt_contract import (
    WORKSPACE_FS_BENCHMARK_VERSION,
)
from aware_file_system.native_backend import (
    RUST_BACKEND_KIND,
    WORKSPACE_APPLY_DELTAS_OPERATION,
)


@dataclass(frozen=True, slots=True)
class WorkspaceApplyDelta:
    operation: str
    path: str
    content_text: str | None = None
    expected_sha256: str | None = None
    content_bytes: bytes | None = None


@dataclass(frozen=True, slots=True)
class WorkspaceApplyEntry:
    path: str
    operation: str
    before_exists: bool
    after_exists: bool
    before_sha256: str | None
    after_sha256: str | None
    expected_sha256: str | None
    bytes_written: int
    bytes_deleted: int
    digest_verified: bool


@dataclass(frozen=True, slots=True)
class WorkspaceApplyReport:
    backend_kind: str
    benchmark_version: str
    operation: str
    root_path: str
    entries: tuple[WorkspaceApplyEntry, ...]
    applied_path_count: int
    bytes_written: int
    bytes_deleted: int
    digest_verified_count: int
    materialized_artifact_count: int
    stored_artifact_count: int
    digest_backend_kind: str | None = None
    content_engine: Mapping[str, Any] | None = None
    phase_timings: Mapping[str, Any] | None = None

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(entry.path for entry in self.entries)

    @property
    def by_path(self) -> dict[str, WorkspaceApplyEntry]:
        return {entry.path: entry for entry in self.entries}


class WorkspaceApplyParityError(AssertionError):
    pass


class NativeApplyUnavailable(RuntimeError):
    pass


def collect_python_workspace_apply(
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
) -> WorkspaceApplyReport:
    root_path = root.expanduser().resolve()
    if not root_path.is_dir():
        raise ValueError("Workspace apply root must be a directory.")

    entries = tuple(_apply_python_delta(root_path, delta) for delta in deltas)
    return WorkspaceApplyReport(
        backend_kind="python",
        benchmark_version=WORKSPACE_FS_BENCHMARK_VERSION,
        operation=WORKSPACE_APPLY_DELTAS_OPERATION,
        root_path=root_path.as_posix(),
        entries=entries,
        applied_path_count=len(entries),
        bytes_written=sum(entry.bytes_written for entry in entries),
        bytes_deleted=sum(entry.bytes_deleted for entry in entries),
        digest_verified_count=sum(1 for entry in entries if entry.digest_verified),
        materialized_artifact_count=0,
        stored_artifact_count=0,
        digest_backend_kind=None,
        content_engine=None,
    )


def collect_rust_workspace_apply(
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    *,
    cargo_path: Path | None = None,
    cargo_home: Path | None = None,
    manifest_path: Path | None = None,
    target_dir: Path | None = None,
    prepared_binary_path: Path | None = None,
    release: bool = False,
    build_timeout_s: float = 240.0,
) -> WorkspaceApplyReport:
    from aware_file_system.native_apply_executor import (
        RustWorkspaceApplyExecutorConfig,
        collect_prepared_rust_workspace_apply,
        prepare_rust_workspace_apply_executor,
    )

    executor = prepare_rust_workspace_apply_executor(
        RustWorkspaceApplyExecutorConfig(
            cargo_path=cargo_path,
            cargo_home=cargo_home,
            manifest_path=manifest_path,
            target_dir=target_dir,
            prepared_binary_path=prepared_binary_path,
            release=release,
            build_timeout_s=build_timeout_s,
        )
    )
    return collect_prepared_rust_workspace_apply(root, deltas, executor=executor)


def workspace_apply_report_from_mapping(raw: Mapping[str, Any]) -> WorkspaceApplyReport:
    entries = tuple(
        WorkspaceApplyEntry(
            path=str(entry["path"]),
            operation=str(entry["operation"]),
            before_exists=bool(entry["before_exists"]),
            after_exists=bool(entry["after_exists"]),
            before_sha256=_optional_string(entry.get("before_sha256")),
            after_sha256=_optional_string(entry.get("after_sha256")),
            expected_sha256=_optional_string(entry.get("expected_sha256")),
            bytes_written=int(entry["bytes_written"]),
            bytes_deleted=int(entry["bytes_deleted"]),
            digest_verified=bool(entry["digest_verified"]),
        )
        for entry in _list_value(raw.get("entries"))
    )
    return WorkspaceApplyReport(
        backend_kind=str(raw.get("backend_kind", "")),
        benchmark_version=str(raw.get("benchmark_version", "")),
        operation=str(raw.get("operation", "")),
        root_path=str(raw.get("root_path", "")),
        entries=entries,
        applied_path_count=int(raw.get("applied_path_count", 0)),
        bytes_written=int(raw.get("bytes_written", 0)),
        bytes_deleted=int(raw.get("bytes_deleted", 0)),
        digest_verified_count=int(raw.get("digest_verified_count", 0)),
        materialized_artifact_count=int(raw.get("materialized_artifact_count", 0)),
        stored_artifact_count=int(raw.get("stored_artifact_count", 0)),
        digest_backend_kind=_optional_string(raw.get("digest_backend_kind")),
        content_engine=_mapping_value(raw.get("content_engine")),
        phase_timings=_mapping_value(raw.get("phase_timings")),
    )


def assert_workspace_apply_parity(
    *,
    python_report: WorkspaceApplyReport,
    rust_report: WorkspaceApplyReport,
) -> None:
    if rust_report.backend_kind != RUST_BACKEND_KIND:
        raise WorkspaceApplyParityError(
            f"Rust apply backend mismatch: {rust_report.backend_kind!r}"
        )
    if rust_report.benchmark_version != WORKSPACE_FS_BENCHMARK_VERSION:
        raise WorkspaceApplyParityError(
            f"Rust apply benchmark mismatch: {rust_report.benchmark_version!r}"
        )
    if rust_report.operation != WORKSPACE_APPLY_DELTAS_OPERATION:
        raise WorkspaceApplyParityError(
            f"Rust apply operation mismatch: {rust_report.operation!r}"
        )
    if python_report.entries != rust_report.entries:
        raise WorkspaceApplyParityError(
            "Workspace apply entry mismatch: "
            f"python={python_report.entries!r} rust={rust_report.entries!r}"
        )
    if python_report.bytes_written != rust_report.bytes_written:
        raise WorkspaceApplyParityError("Workspace apply bytes_written mismatch")
    if python_report.bytes_deleted != rust_report.bytes_deleted:
        raise WorkspaceApplyParityError("Workspace apply bytes_deleted mismatch")
    if python_report.digest_verified_count != rust_report.digest_verified_count:
        raise WorkspaceApplyParityError("Workspace apply digest count mismatch")
    if rust_report.stored_artifact_count != 0:
        raise WorkspaceApplyParityError("Rust apply v0 must not store artifacts")


def _apply_python_delta(root_path: Path, delta: WorkspaceApplyDelta) -> WorkspaceApplyEntry:
    relative_path = _normalize_relative_path(delta.path)
    target = root_path / relative_path
    before_exists = target.exists()
    if before_exists:
        _ensure_within_root(root_path=root_path, path=target.resolve())
    before_sha256 = _file_sha256(target) if target.is_file() else None
    bytes_written = 0
    bytes_deleted = 0
    after_sha256: str | None = None
    expected_sha256 = _normalize_sha256_digest(delta.expected_sha256)

    if delta.operation == "delete":
        if target.exists():
            if not target.is_file():
                raise ValueError(f"Workspace apply delete target is not a file: {delta.path}")
            bytes_deleted = target.stat().st_size
            target.unlink()
        after_exists = False
        digest_verified = False
    elif delta.operation in {"create", "update"}:
        content_bytes = workspace_apply_delta_content_bytes(delta)
        if content_bytes is None:
            raise ValueError(
                f"Workspace apply upsert requires content payload: {delta.path}"
            )
        if target.exists() and not target.is_file():
            raise ValueError(f"Workspace apply upsert target is not a file: {delta.path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        _ensure_within_root(root_path=root_path, path=target.parent.resolve())
        target.write_bytes(content_bytes)
        after_exists = True
        bytes_written = len(content_bytes)
        after_sha256 = _file_sha256(target)
        digest_verified = expected_sha256 is not None
        if expected_sha256 is not None and after_sha256 != expected_sha256:
            raise ValueError(
                "Workspace apply digest mismatch for "
                f"{delta.path}: expected {expected_sha256}, got {after_sha256}"
            )
    else:
        raise ValueError(f"Unsupported workspace apply operation: {delta.operation}")

    return WorkspaceApplyEntry(
        path=relative_path,
        operation=delta.operation,
        before_exists=before_exists,
        after_exists=after_exists,
        before_sha256=before_sha256,
        after_sha256=after_sha256,
        expected_sha256=expected_sha256,
        bytes_written=bytes_written,
        bytes_deleted=bytes_deleted,
        digest_verified=digest_verified,
    )


def _normalize_relative_path(raw_path: str) -> str:
    path = Path(raw_path.replace("\\", "/"))
    if not raw_path or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Workspace apply path must stay within root: {raw_path}")
    normalized = path.as_posix().strip("/")
    if not normalized or normalized == ".":
        raise ValueError("Workspace apply path must target a file.")
    return normalized


def _normalize_sha256_digest(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if not text or text == "-":
        return None
    if text.startswith("sha256:"):
        text = text.split(":", 1)[1]
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"Workspace apply expected_sha256 is invalid: {value}")
    return text


def workspace_apply_delta_content_bytes(delta: WorkspaceApplyDelta) -> bytes | None:
    if delta.content_bytes is not None and delta.content_text is not None:
        raise ValueError(
            "Workspace apply delta must provide either content_text or content_bytes, "
            "not both."
        )
    if delta.content_bytes is not None:
        return bytes(delta.content_bytes)
    if delta.content_text is not None:
        return delta.content_text.encode("utf-8")
    return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_within_root(*, root_path: Path, path: Path) -> None:
    try:
        path.relative_to(root_path)
    except ValueError as exc:
        raise ValueError(f"Workspace apply path escapes root: {path}") from exc


def _list_value(value: object) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _mapping_value(value: object) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return dict(value)
