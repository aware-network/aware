from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from aware_file_system.native_observation_service import NativeObservationService
from aware_file_system.native_snapshot import (
    WorkspaceSnapshot,
    WorkspaceSnapshotEntry,
    assert_workspace_snapshot_parity,
    collect_python_workspace_snapshot,
    workspace_snapshot_delta,
    workspace_snapshot_digest,
    workspace_snapshot_from_mapping,
)


class ObservationBackendMode(StrEnum):
    PYTHON_REFERENCE = "python_reference"
    RUST_SHADOW = "rust_shadow"
    RUST_PRIMARY = "rust_primary"


@dataclass(frozen=True, slots=True)
class BackendObservation:
    mode: ObservationBackendMode
    report: Mapping[str, Any]
    snapshot: WorkspaceSnapshot
    shadow_receipt: Mapping[str, Any] | None = None


class ObservationBackend(Protocol):
    @property
    def mode(self) -> ObservationBackendMode: ...

    def initialize(self, request_id: str) -> BackendObservation: ...

    def poll(self, request_id: str) -> BackendObservation: ...

    def close(self) -> None: ...


class PythonReferenceObservationBackend:
    def __init__(self, *, workspace_root: Path, cache_dir: Path) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        self.cache_dir = cache_dir.expanduser().resolve()
        self._snapshot: WorkspaceSnapshot | None = None

    @property
    def mode(self) -> ObservationBackendMode:
        return ObservationBackendMode.PYTHON_REFERENCE

    def initialize(self, request_id: str) -> BackendObservation:
        return self._observe(request_id)

    def poll(self, request_id: str) -> BackendObservation:
        return self._observe(request_id)

    def close(self) -> None:
        return None

    def _observe(self, request_id: str) -> BackendObservation:
        started = time.perf_counter()
        snapshot = collect_python_workspace_snapshot(
            self.workspace_root,
            cache_dir=self.cache_dir,
        )
        delta = (
            workspace_snapshot_delta(self._snapshot, snapshot)
            if self._snapshot is not None
            else None
        )
        self._snapshot = snapshot
        report: dict[str, Any] = {
            "schema": "aware.file_system.reference_observation.v1",
            "request_id": request_id,
            "backend_kind": "python",
            "status": "exact",
            "observation_mode": "full_reconciliation",
            "snapshot_digest": snapshot.inventory_digest,
            "snapshot_entry_count": len(snapshot.entries),
            "duration_s": time.perf_counter() - started,
            "added": list(delta.added) if delta is not None else list(snapshot.paths),
            "modified": list(delta.modified) if delta is not None else [],
            "deleted": list(delta.deleted) if delta is not None else [],
        }
        return BackendObservation(mode=self.mode, report=report, snapshot=snapshot)


class RustPrimaryObservationBackend:
    def __init__(self, service: NativeObservationService) -> None:
        self.service = service
        self._snapshot: WorkspaceSnapshot | None = None

    @property
    def mode(self) -> ObservationBackendMode:
        return ObservationBackendMode.RUST_PRIMARY

    def initialize(self, request_id: str) -> BackendObservation:
        self.service.ping()
        self._result(self.service.initialize_observation(request_id))
        return self._result(
            self.service.wait_for_watcher_ready(
                request_id=f"{request_id}-watcher-ready"
            )
        )

    def poll(self, request_id: str) -> BackendObservation:
        return self._result(self.service.poll(request_id))

    def close(self) -> None:
        self.service.close()

    def _result(self, report: Mapping[str, Any]) -> BackendObservation:
        snapshot = _snapshot_after_report(
            previous=self._snapshot,
            report=report,
            initial_snapshot=lambda: workspace_snapshot_from_mapping(
                self.service.snapshot()
            ),
        )
        self._snapshot = snapshot
        return BackendObservation(mode=self.mode, report=report, snapshot=snapshot)


class RustShadowObservationBackend:
    def __init__(
        self,
        *,
        service: NativeObservationService,
        python_cache_dir: Path,
        sample_every: int = 1,
    ) -> None:
        if sample_every < 1:
            raise ValueError("sample_every must be at least one")
        self.service = service
        self.python_cache_dir = python_cache_dir.expanduser().resolve()
        self.sample_every = sample_every
        self._poll_count = 0
        self._snapshot: WorkspaceSnapshot | None = None

    @property
    def mode(self) -> ObservationBackendMode:
        return ObservationBackendMode.RUST_SHADOW

    def initialize(self, request_id: str) -> BackendObservation:
        self.service.ping()
        return self._sample(request_id)

    def poll(self, request_id: str) -> BackendObservation:
        self._poll_count += 1
        if self._poll_count % self.sample_every == 0:
            return self._sample(request_id)
        report = self.service.poll(request_id)
        snapshot = _snapshot_after_report(
            previous=self._snapshot,
            report=report,
            initial_snapshot=lambda: workspace_snapshot_from_mapping(
                self.service.snapshot()
            ),
        )
        self._snapshot = snapshot
        return BackendObservation(
            mode=self.mode,
            report=report,
            snapshot=snapshot,
        )

    def close(self) -> None:
        self.service.close()

    def _sample(self, request_id: str) -> BackendObservation:
        native_started = time.perf_counter()
        report = self.service.observe(request_id)
        rust_snapshot = workspace_snapshot_from_mapping(self.service.snapshot())
        self._snapshot = rust_snapshot
        native_duration_s = time.perf_counter() - native_started
        python_started = time.perf_counter()
        python_snapshot = collect_python_workspace_snapshot(
            self.service.workspace_root,
            cache_dir=self.python_cache_dir,
        )
        python_duration_s = time.perf_counter() - python_started
        assert_workspace_snapshot_parity(
            python_snapshot=python_snapshot,
            rust_snapshot=rust_snapshot,
        )
        shadow_receipt = {
            "schema": "aware.file_system.observation_shadow.v1",
            "exact_parity": True,
            "snapshot_digest": rust_snapshot.inventory_digest,
            "entry_count": len(rust_snapshot.entries),
            "native_duration_s": native_duration_s,
            "python_reference_duration_s": python_duration_s,
            "second_watcher_started": False,
        }
        return BackendObservation(
            mode=self.mode,
            report=report,
            snapshot=rust_snapshot,
            shadow_receipt=shadow_receipt,
        )


def build_observation_backend(
    *,
    mode: ObservationBackendMode | str,
    workspace_root: Path,
    cache_path: Path,
    binary_path: Path | None = None,
    request_timeout_s: float = 5.0,
    reconciliation_interval_s: float = 30.0,
    shadow_sample_every: int = 1,
) -> ObservationBackend:
    try:
        selected = ObservationBackendMode(mode)
    except ValueError as error:
        allowed = ", ".join(item.value for item in ObservationBackendMode)
        raise ValueError(
            f"unsupported observation backend mode; choose {allowed}"
        ) from error
    if selected is ObservationBackendMode.PYTHON_REFERENCE:
        return PythonReferenceObservationBackend(
            workspace_root=workspace_root,
            cache_dir=cache_path,
        )
    if binary_path is None:
        raise ValueError(f"binary_path is required for {selected.value}")
    service = NativeObservationService(
        binary_path=binary_path,
        workspace_root=workspace_root,
        cache_path=cache_path,
        request_timeout_s=request_timeout_s,
        reconciliation_interval_s=reconciliation_interval_s,
    )
    if selected is ObservationBackendMode.RUST_PRIMARY:
        return RustPrimaryObservationBackend(service)
    return RustShadowObservationBackend(
        service=service,
        python_cache_dir=cache_path.parent / f"{cache_path.name}.python-shadow",
        sample_every=shadow_sample_every,
    )


def _snapshot_after_report(
    *,
    previous: WorkspaceSnapshot | None,
    report: Mapping[str, Any],
    initial_snapshot: Callable[[], WorkspaceSnapshot],
) -> WorkspaceSnapshot:
    if previous is None:
        snapshot = initial_snapshot()
        _assert_report_snapshot(snapshot, report)
        return snapshot
    if _report_preserves_snapshot(previous, report):
        return previous
    entries_by_path = previous.by_path
    for path in _string_list(report.get("deleted")):
        entries_by_path.pop(path, None)
    for raw_entry in [
        *_mapping_list(report.get("added_entries")),
        *_mapping_list(report.get("modified_entries")),
    ]:
        entry = WorkspaceSnapshotEntry(
            path=str(raw_entry["path"]),
            size=int(raw_entry["size"]),
            mtime_ns=int(raw_entry["mtime_ns"]),
            depth=int(raw_entry["depth"]),
        )
        entries_by_path[entry.path] = entry
    entries = tuple(sorted(entries_by_path.values(), key=lambda entry: entry.path))
    snapshot = WorkspaceSnapshot(
        backend_kind=previous.backend_kind,
        benchmark_version=previous.benchmark_version,
        operation=previous.operation,
        root_path=previous.root_path,
        entries=entries,
        semantics_engine=previous.semantics_engine,
        inventory_digest=workspace_snapshot_digest(entries),
        directories_scanned=previous.directories_scanned,
        files_seen=previous.files_seen,
        errors=(),
    )
    _assert_report_snapshot(snapshot, report)
    return snapshot


def _report_preserves_snapshot(
    previous: WorkspaceSnapshot,
    report: Mapping[str, Any],
) -> bool:
    return (
        previous.inventory_digest == str(report.get("snapshot_digest"))
        and len(previous.entries) == int(report.get("snapshot_entry_count", -1))
        and not _string_list(report.get("added"))
        and not _string_list(report.get("modified"))
        and not _string_list(report.get("deleted"))
        and not _mapping_list(report.get("added_entries"))
        and not _mapping_list(report.get("modified_entries"))
    )


def _assert_report_snapshot(
    snapshot: WorkspaceSnapshot,
    report: Mapping[str, Any],
) -> None:
    if snapshot.inventory_digest != str(report.get("snapshot_digest")):
        raise RuntimeError(
            "native observation delta does not reproduce snapshot digest"
        )
    if len(snapshot.entries) != int(report.get("snapshot_entry_count", -1)):
        raise RuntimeError(
            "native observation delta does not reproduce snapshot entry count"
        )


def _mapping_list(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)
