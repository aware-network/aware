from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from typing import Any, Sequence

from aware_file_system.native_observation_service import NativeObservationService
from aware_file_system.native_snapshot import (
    collect_python_workspace_snapshot,
    workspace_snapshot_digest,
)


EVENT_HINT_BENCHMARK_VERSION = "aware.file_system.observation_event_hints.v1"
LINUX_SHADOW_GATE_VERSION = "aware.file_system.linux_observation_shadow_gate.v1"
DIRTY_PATH_BENCHMARK_VERSION = "aware.file_system.dirty_path_reconciliation.v1"
LINUX_SHADOW_THRESHOLDS = {
    "minimum_samples": 30,
    "activation_max_s": 0.05,
    "startup_max_s": 1.5,
    "watcher_activation_max_s": 2.0,
    "idle_p99_max_s": 0.01,
    "synthetic_mutation_p99_max_s": 0.05,
    "pressure_event_to_exact_p99_max_s": 1.5,
    "pressure_event_to_exact_max_s": 2.5,
    "watch_ratio_max": 0.25,
}
_PRESSURE_WORKER = """
import hashlib
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
paths = tuple(path for path in root.rglob("*") if path.is_file())
payload = b"aware-file-system-pressure" * 131072
while True:
    hashlib.sha256(payload).digest()
    for path in paths[::17]:
        try:
            with path.open("rb") as stream:
                stream.read(4096)
        except OSError:
            pass
"""


def run_event_hint_idle_benchmark(
    *,
    workspace_root: Path,
    binary_path: Path,
    cache_path: Path,
    idle_iterations: int = 30,
    request_timeout_s: float = 5.0,
) -> dict[str, Any]:
    if idle_iterations < 1:
        raise ValueError("idle_iterations must be at least one")
    root = workspace_root.expanduser().resolve()
    binary = binary_path.expanduser().resolve()
    cache = cache_path.expanduser().resolve()
    if cache.exists():
        raise ValueError("benchmark cache path must not exist")

    activation_started = time.perf_counter()
    service = NativeObservationService(
        binary_path=binary,
        workspace_root=root,
        cache_path=cache,
        request_timeout_s=request_timeout_s,
        reconciliation_interval_s=3600.0,
    )
    try:
        service.ping()
        activation_duration_s = time.perf_counter() - activation_started
        startup = _measure_initialize(service, "startup")
        watcher_activation_started = time.perf_counter()
        watcher_ready_report = dict(service.wait_for_watcher_ready())
        watcher_activation_duration_s = time.perf_counter() - watcher_activation_started
        samples = [
            _measure_poll(service, f"idle-{index}") for index in range(idle_iterations)
        ]
        health = service.health()
    finally:
        service.close()

    durations = sorted(float(sample["wall_duration_s"]) for sample in samples)
    exact_digest_stable = len({sample["snapshot_digest"] for sample in samples}) == 1
    traversal_free = all(
        sample["observation_mode"] == "maintained_no_hint"
        and sample["scan_ns"] == 0
        and sample["cache_written"] is False
        for sample in samples
    )
    return {
        "benchmark_version": EVENT_HINT_BENCHMARK_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "workspace_root": root.as_posix(),
        "binary_path": binary.as_posix(),
        "cache_path": cache.as_posix(),
        "activation_duration_s": activation_duration_s,
        "watcher_activation_duration_s": watcher_activation_duration_s,
        "startup": startup,
        "watcher_ready_reconciliation": {
            "status": watcher_ready_report["status"],
            "cause": watcher_ready_report["reconciliation_cause"],
            "scan_duration_s": int(watcher_ready_report["scan_ns"]) / 1_000_000_000,
        },
        "idle": {
            "sample_count": len(samples),
            "traversal_free_count": sum(sample["scan_ns"] == 0 for sample in samples),
            "cache_write_count": sum(
                bool(sample["cache_written"]) for sample in samples
            ),
            "wall_duration_s": _duration_summary(durations),
            "response_bytes": _integer_summary(
                sorted(int(sample["response_bytes"]) for sample in samples)
            ),
            "samples": samples,
        },
        "watcher_health": health["watcher"],
        "exact_digest_stable": exact_digest_stable,
        "traversal_free": traversal_free,
        "distribution_sample_eligible": idle_iterations >= 30,
        "production_gate_passed": False,
        "locks": [
            "idle distribution only; mutation, pressure, loss, and recovery remain",
            "watch events are invalidation hints, never delta truth",
            "no snapshot transfer occurs on idle poll",
            "no materialization, graph, ORM, or consumer watcher",
        ],
    }


def run_event_hint_mutation_benchmark(
    *,
    binary_path: Path,
    scratch_root: Path,
    mutation_iterations: int = 30,
    request_timeout_s: float = 5.0,
) -> dict[str, Any]:
    if mutation_iterations < 1:
        raise ValueError("mutation_iterations must be at least one")
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="aware-fs-event-mutation-", dir=scratch) as raw_root:
        root = Path(raw_root)
        source = root / "probe.txt"
        source.write_text("seed\n", encoding="utf-8")
        service = NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=root.parent / f"{root.name}.cache",
            request_timeout_s=request_timeout_s,
            reconciliation_interval_s=3600.0,
        )
        try:
            service.ping()
            service.initialize_observation("startup")
            service.wait_for_watcher_ready()
            samples: list[dict[str, Any]] = []
            for index in range(mutation_iterations):
                _settle_hint_queue(service, index)
                started = time.perf_counter()
                source.write_text(f"mutation-{index}-{'x' * index}\n", encoding="utf-8")
                polls_before_hint = 0
                deadline = time.monotonic() + request_timeout_s
                while True:
                    report = dict(service.poll(f"mutation-{index}-{polls_before_hint}"))
                    if report["reconciliation_cause"] == "event_hints":
                        break
                    if report["observation_mode"] != "maintained_no_hint":
                        raise RuntimeError(
                            "mutation probe received unexpected reconciliation cause: "
                            f"{report['reconciliation_cause']}"
                        )
                    if time.monotonic() >= deadline:
                        raise RuntimeError(
                            "mutation event hint did not arrive before deadline"
                        )
                    polls_before_hint += 1
                    time.sleep(0.001)
                samples.append(
                    {
                        "index": index,
                        "event_to_exact_duration_s": time.perf_counter() - started,
                        "polls_before_hint": polls_before_hint,
                        "hint_event_count": int(report["hint_event_count"]),
                        "scan_duration_s": int(report["scan_ns"]) / 1_000_000_000,
                        "cache_written": bool(report["cache_written"]),
                        "modified": list(report["modified"]),
                        "status": report["status"],
                    }
                )
            health = service.health()["watcher"]
        finally:
            service.close()
            cache = root.parent / f"{root.name}.cache"
            cache.unlink(missing_ok=True)

    durations = sorted(float(sample["event_to_exact_duration_s"]) for sample in samples)
    return {
        "sample_count": len(samples),
        "success_count": sum(
            sample["status"] == "exact"
            and sample["modified"] == ["probe.txt"]
            and sample["cache_written"]
            for sample in samples
        ),
        "event_to_exact_duration_s": _duration_summary(durations),
        "polls_before_hint": _integer_summary(
            sorted(int(sample["polls_before_hint"]) for sample in samples)
        ),
        "watcher_health": health,
        "distribution_sample_eligible": mutation_iterations >= 30,
        "samples": samples,
    }


def run_event_hint_canonical_file_set_pressure_benchmark(
    *,
    source_workspace_root: Path,
    binary_path: Path,
    scratch_root: Path,
    mutation_iterations: int = 30,
    churn_width: int = 64,
    pressure_workers: int = 2,
    request_timeout_s: float = 5.0,
) -> dict[str, Any]:
    if mutation_iterations < 1:
        raise ValueError("mutation_iterations must be at least one")
    if churn_width < 1:
        raise ValueError("churn_width must be at least one")
    if pressure_workers < 1:
        raise ValueError("pressure_workers must be at least one")
    source_root = source_workspace_root.expanduser().resolve()
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    binary = binary_path.expanduser().resolve()

    with TemporaryDirectory(
        prefix="aware-fs-canonical-file-set-", dir=scratch
    ) as raw_root:
        mirror_root = Path(raw_root) / "workspace"
        mirror_root.mkdir()
        source_cache = Path(raw_root) / "source.cache"
        source_service = NativeObservationService(
            binary_path=binary,
            workspace_root=source_root,
            cache_path=source_cache,
            request_timeout_s=request_timeout_s,
            reconciliation_interval_s=3600.0,
        )
        try:
            source_report = dict(
                source_service.initialize_observation("source-topology")
            )
            source_snapshot = dict(source_service.snapshot())
        finally:
            source_service.close()
        source_cache.unlink(missing_ok=True)
        mirror_started = time.perf_counter()
        _materialize_metadata_mirror(
            source_root=source_root,
            mirror_root=mirror_root,
            entries=list(source_snapshot["entries"]),
        )
        mirror_duration_s = time.perf_counter() - mirror_started

        probe = mirror_root / "pressure-probe.txt"
        probe.write_text("seed\n", encoding="utf-8")
        churn = mirror_root / "pressure-churn"
        churn.mkdir()
        service = NativeObservationService(
            binary_path=binary,
            workspace_root=mirror_root,
            cache_path=Path(raw_root) / "mirror.cache",
            request_timeout_s=request_timeout_s,
            reconciliation_interval_s=3600.0,
        )
        workers: list[subprocess.Popen[bytes]] = []
        try:
            service.initialize_observation("startup")
            service.wait_for_watcher_ready()
            workers = _start_pressure_workers(mirror_root, pressure_workers)
            time.sleep(0.1)
            samples: list[dict[str, Any]] = []
            churn_present = False
            for index in range(mutation_iterations):
                _settle_hint_queue(service, index)
                replacement = mirror_root / ".pressure-probe.atomic"
                replacement.write_text(
                    f"pressure-{index}-{'x' * (index + 1)}\n",
                    encoding="utf-8",
                )
                replacement.replace(probe)
                expected_added: list[str] = []
                expected_deleted: list[str] = []
                if churn_present:
                    for item_index in range(churn_width):
                        path = churn / f"item-{item_index:04d}.txt"
                        path.unlink()
                        expected_deleted.append(
                            f"pressure-churn/item-{item_index:04d}.txt"
                        )
                else:
                    for item_index in range(churn_width):
                        path = churn / f"item-{item_index:04d}.txt"
                        path.write_text(
                            f"iteration-{index}-item-{item_index}\n",
                            encoding="utf-8",
                        )
                        expected_added.append(
                            f"pressure-churn/item-{item_index:04d}.txt"
                        )
                churn_present = not churn_present
                started = time.perf_counter()
                report, polls_before_hint = _poll_until_event_reconciliation(
                    service=service,
                    request_prefix=f"pressure-{index}",
                    request_timeout_s=request_timeout_s,
                )
                samples.append(
                    {
                        "index": index,
                        "event_to_exact_duration_s": time.perf_counter() - started,
                        "polls_before_hint": polls_before_hint,
                        "scan_duration_s": int(report["scan_ns"]) / 1_000_000_000,
                        "hint_event_count": int(report["hint_event_count"]),
                        "hint_path_count": len(report["hint_paths"]),
                        "hint_paths_truncated": bool(report["hint_paths_truncated"]),
                        "cache_written": bool(report["cache_written"]),
                        "modified_exact": report["modified"] == ["pressure-probe.txt"],
                        "added_exact": report["added"] == expected_added,
                        "deleted_exact": report["deleted"] == expected_deleted,
                        "workers_alive": all(
                            worker.poll() is None for worker in workers
                        ),
                    }
                )
            health = service.health()["watcher"]
        finally:
            _stop_pressure_workers(workers)
            service.close()

    durations = sorted(float(sample["event_to_exact_duration_s"]) for sample in samples)
    scans = sorted(float(sample["scan_duration_s"]) for sample in samples)
    return {
        "schema": "aware.file_system.observation_pressure.v1",
        "source_workspace_root": source_root.as_posix(),
        "source_snapshot_entry_count": int(source_report["snapshot_entry_count"]),
        "mirror_kind": "canonical_file_path_size_mtime_sparse_v1",
        "mirror_duration_s": mirror_duration_s,
        "mutation_sample_count": len(samples),
        "success_count": sum(
            sample["modified_exact"]
            and sample["added_exact"]
            and sample["deleted_exact"]
            and sample["workers_alive"]
            for sample in samples
        ),
        "churn_width": churn_width,
        "pressure_worker_count": pressure_workers,
        "event_to_exact_duration_s": _duration_summary(durations),
        "scan_duration_s": _duration_summary(scans),
        "watcher_health": health,
        "distribution_sample_eligible": mutation_iterations >= 30,
        "production_gate_passed": False,
        "samples": samples,
        "locks": [
            "canonical-file-set sparse mirror; empty-directory topology is not claimed",
            "shared source repository is read-only",
            "pressure workers contend CPU and filesystem reads but own no watcher",
            "watch hints schedule exact full reconciliation and never define deltas",
        ],
    }


def run_dirty_path_canonical_file_set_benchmark(
    *,
    source_workspace_root: Path,
    binary_path: Path,
    scratch_root: Path,
    probe_relative_path: str = "AGENTS.md",
    mutation_iterations: int = 30,
    pressure_workers: int = 2,
    request_timeout_s: float = 5.0,
) -> dict[str, Any]:
    if mutation_iterations < 1:
        raise ValueError("mutation_iterations must be at least one")
    if pressure_workers < 0:
        raise ValueError("pressure_workers must not be negative")
    probe_relative = Path(probe_relative_path)
    if (
        probe_relative_path == ""
        or probe_relative.is_absolute()
        or ".." in probe_relative.parts
    ):
        raise ValueError("probe_relative_path must be a confined nonempty path")
    source_root = source_workspace_root.expanduser().resolve()
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    binary = binary_path.expanduser().resolve()

    with TemporaryDirectory(prefix="aware-fs-dirty-path-", dir=scratch) as raw_root:
        run_root = Path(raw_root)
        mirror_root = run_root / "workspace"
        mirror_root.mkdir()
        source_service = NativeObservationService(
            binary_path=binary,
            workspace_root=source_root,
            cache_path=run_root / "source.cache",
            request_timeout_s=request_timeout_s,
            reconciliation_interval_s=3600.0,
        )
        try:
            source_report = dict(source_service.initialize_observation("source-topology"))
            source_snapshot = dict(source_service.snapshot())
        finally:
            source_service.close()
        _materialize_metadata_mirror(
            source_root=source_root,
            mirror_root=mirror_root,
            entries=list(source_snapshot["entries"]),
        )
        probe = mirror_root / probe_relative
        if not probe.is_file():
            raise ValueError(
                "probe_relative_path must select a canonical source file in the mirror"
            )

        service = NativeObservationService(
            binary_path=binary,
            workspace_root=mirror_root,
            cache_path=run_root / "mirror.cache",
            request_timeout_s=request_timeout_s,
            reconciliation_interval_s=3600.0,
        )
        workers: list[subprocess.Popen[bytes]] = []
        try:
            service.initialize_observation("startup")
            service.wait_for_watcher_ready()
            workers = _start_pressure_workers(mirror_root, pressure_workers)
            if workers:
                time.sleep(0.1)
            samples: list[dict[str, Any]] = []
            for index in range(mutation_iterations):
                _settle_hint_queue(service, index)
                started = time.perf_counter()
                probe.write_text(
                    f"dirty-path-{index}-{'x' * (index + 1)}\n",
                    encoding="utf-8",
                )
                report, polls_before_hint = _poll_until_event_reconciliation(
                    service=service,
                    request_prefix=f"dirty-path-{index}",
                    request_timeout_s=request_timeout_s,
                )
                event_to_exact_duration_s = time.perf_counter() - started
                samples.append(
                    {
                        "index": index,
                        "event_to_exact_duration_s": event_to_exact_duration_s,
                        "polls_before_hint": polls_before_hint,
                        "observation_mode": report["observation_mode"],
                        "reconciled_scope_count": int(
                            report["reconciled_scope_count"]
                        ),
                        "directories_scanned": int(report["directories_scanned"]),
                        "files_seen": int(report["files_seen"]),
                        "scan_duration_s": int(report["scan_ns"]) / 1_000_000_000,
                        "merge_duration_s": int(report["merge_ns"])
                        / 1_000_000_000,
                        "delta_duration_s": int(report["delta_ns"]) / 1_000_000_000,
                        "persistence_duration_s": int(report["persistence_ns"])
                        / 1_000_000_000,
                        "service_total_duration_s": int(report["total_ns"])
                        / 1_000_000_000,
                        "hint_event_count": int(report["hint_event_count"]),
                        "digest_backend_kind": str(report["digest_backend_kind"]),
                        "cache_written": bool(report["cache_written"]),
                        "persistence_mode": report["persistence_mode"],
                        "checkpoint_written": bool(report["checkpoint_written"]),
                        "journal_bytes": int(report["journal_bytes"]),
                        "journal_frame_count": int(report["journal_frame_count"]),
                        "modified": list(report["modified"]),
                        "snapshot_digest": report["snapshot_digest"],
                        "workers_alive": all(
                            worker.poll() is None for worker in workers
                        ),
                    }
                )
            final_snapshot = dict(service.snapshot())
            _stop_pressure_workers(workers)
            workers = []
            oracle = collect_python_workspace_snapshot(mirror_root)
            oracle_digest = workspace_snapshot_digest(oracle.entries)
            final_digest_exact = final_snapshot["inventory_digest"] == oracle_digest
            health = service.health()["watcher"]
        finally:
            _stop_pressure_workers(workers)
            service.close()

    def durations(field: str) -> dict[str, float]:
        return _duration_summary(sorted(float(sample[field]) for sample in samples))

    def timing_distribution(selected: list[dict[str, Any]]) -> dict[str, Any]:
        def selected_durations(field: str) -> dict[str, float] | None:
            if not selected:
                return None
            return _duration_summary(
                sorted(float(sample[field]) for sample in selected)
            )

        return {
            "sample_count": len(selected),
            "event_to_exact_duration_s": selected_durations(
                "event_to_exact_duration_s"
            ),
            "merge_duration_s": selected_durations("merge_duration_s"),
            "persistence_duration_s": selected_durations("persistence_duration_s"),
            "service_total_duration_s": selected_durations(
                "service_total_duration_s"
            ),
        }

    ordinary_journal_samples = [
        sample
        for sample in samples
        if sample["persistence_mode"] == "journal_append"
        and not sample["checkpoint_written"]
    ]
    checkpoint_samples = [sample for sample in samples if sample["checkpoint_written"]]

    return {
        "schema": DIRTY_PATH_BENCHMARK_VERSION,
        "source_workspace_root": source_root.as_posix(),
        "source_snapshot_entry_count": int(source_report["snapshot_entry_count"]),
        "mirror_kind": "canonical_file_path_size_mtime_sparse_v1",
        "probe_relative_path": probe_relative.as_posix(),
        "mutation_sample_count": len(samples),
        "success_count": (
            sum(
                sample["observation_mode"] == "dirty_path_reconciliation"
                and sample["reconciled_scope_count"] == 1
                and sample["modified"] == [probe_relative.as_posix()]
                and (
                    (
                        sample["persistence_mode"] == "journal_append"
                        and not sample["checkpoint_written"]
                    )
                    or (
                        sample["persistence_mode"] == "journal_checkpoint"
                        and sample["checkpoint_written"]
                    )
                )
                and sample["workers_alive"]
                for sample in samples
            )
            if final_digest_exact
            else 0
        ),
        "final_snapshot_digest": final_snapshot["inventory_digest"],
        "final_oracle_digest": oracle_digest,
        "final_digest_exact": final_digest_exact,
        "pressure_worker_count": pressure_workers,
        "event_to_exact_duration_s": durations("event_to_exact_duration_s"),
        "scan_duration_s": durations("scan_duration_s"),
        "merge_duration_s": durations("merge_duration_s"),
        "delta_duration_s": durations("delta_duration_s"),
        "persistence_duration_s": durations("persistence_duration_s"),
        "service_total_duration_s": durations("service_total_duration_s"),
        "directories_scanned": _integer_summary(
            sorted(int(sample["directories_scanned"]) for sample in samples)
        ),
        "files_seen": _integer_summary(
            sorted(int(sample["files_seen"]) for sample in samples)
        ),
        "journal_bytes": _integer_summary(
            sorted(int(sample["journal_bytes"]) for sample in samples)
        ),
        "journal_frame_count": _integer_summary(
            sorted(int(sample["journal_frame_count"]) for sample in samples)
        ),
        "journal_append_count": sum(
            sample["persistence_mode"] == "journal_append" for sample in samples
        ),
        "checkpoint_count": sum(sample["checkpoint_written"] for sample in samples),
        "ordinary_journal_append": timing_distribution(ordinary_journal_samples),
        "checkpoint": {
            **timing_distribution(checkpoint_samples),
            "sample_indices": [int(sample["index"]) for sample in checkpoint_samples],
        },
        "digest_backend_kinds": sorted(
            {str(sample["digest_backend_kind"]) for sample in samples}
        ),
        "watcher_health": health,
        "distribution_sample_eligible": mutation_iterations >= 30,
        "production_gate_passed": False,
        "samples": samples,
        "locks": [
            "canonical-file-set sparse mirror; shared source repository is read-only",
            "each measured mutation changes one existing canonical file",
            "each measured exact change durably appends one journal frame",
            "one independent full Python oracle verifies the final accumulated digest",
            "watch events remain invalidation hints and never define deltas",
        ],
    }


def _materialize_metadata_mirror(
    *,
    source_root: Path,
    mirror_root: Path,
    entries: list[dict[str, Any]],
) -> None:
    for raw_entry in entries:
        relative = Path(str(raw_entry["path"]))
        destination = mirror_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = source_root / relative
        if relative.name == ".gitignore":
            destination.write_bytes(source.read_bytes())
        else:
            destination.touch()
            os.truncate(destination, int(raw_entry["size"]))
        mtime_ns = int(raw_entry["mtime_ns"])
        os.utime(destination, ns=(mtime_ns, mtime_ns))


def _start_pressure_workers(
    root: Path,
    worker_count: int,
) -> list[subprocess.Popen[bytes]]:
    return [
        subprocess.Popen(
            [sys.executable, "-c", _PRESSURE_WORKER, str(root)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(worker_count)
    ]


def _stop_pressure_workers(workers: list[subprocess.Popen[bytes]]) -> None:
    for worker in workers:
        if worker.poll() is None:
            worker.terminate()
    for worker in workers:
        try:
            worker.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=3.0)


def _poll_until_event_reconciliation(
    *,
    service: NativeObservationService,
    request_prefix: str,
    request_timeout_s: float,
) -> tuple[dict[str, Any], int]:
    deadline = time.monotonic() + request_timeout_s
    polls_before_hint = 0
    while True:
        report = dict(service.poll(f"{request_prefix}-{polls_before_hint}"))
        if str(report["reconciliation_cause"]).startswith("event_hints"):
            return report, polls_before_hint
        if report["observation_mode"] != "maintained_no_hint":
            raise RuntimeError(
                "pressure mutation received unexpected reconciliation cause: "
                f"{report['reconciliation_cause']}"
            )
        if time.monotonic() >= deadline:
            raise RuntimeError("pressure mutation hint did not arrive before deadline")
        polls_before_hint += 1
        time.sleep(0.001)


def evaluate_linux_shadow_gate(receipt: dict[str, Any]) -> dict[str, Any]:
    pressure = receipt.get("canonical_file_set_pressure")
    mutation = receipt.get("mutation_fixture")
    max_user_watches = _linux_inotify_max_user_watches()
    watched_directories = int(receipt["watcher_health"]["watched_directory_count"])
    watch_ratio = (
        watched_directories / max_user_watches
        if max_user_watches is not None and max_user_watches > 0
        else None
    )
    checks = {
        "linux_host": sys.platform.startswith("linux"),
        "idle_sample_count": int(receipt["idle"]["sample_count"])
        >= LINUX_SHADOW_THRESHOLDS["minimum_samples"],
        "mutation_sample_count": mutation is not None
        and int(mutation["sample_count"]) >= LINUX_SHADOW_THRESHOLDS["minimum_samples"],
        "pressure_sample_count": pressure is not None
        and int(pressure["mutation_sample_count"])
        >= LINUX_SHADOW_THRESHOLDS["minimum_samples"],
        "activation": float(receipt["activation_duration_s"])
        <= LINUX_SHADOW_THRESHOLDS["activation_max_s"],
        "startup": float(receipt["startup"]["wall_duration_s"])
        <= LINUX_SHADOW_THRESHOLDS["startup_max_s"],
        "watcher_activation": float(receipt["watcher_activation_duration_s"])
        <= LINUX_SHADOW_THRESHOLDS["watcher_activation_max_s"],
        "idle_p99": float(receipt["idle"]["wall_duration_s"]["p99"])
        <= LINUX_SHADOW_THRESHOLDS["idle_p99_max_s"],
        "synthetic_mutation_p99": mutation is not None
        and float(mutation["event_to_exact_duration_s"]["p99"])
        <= LINUX_SHADOW_THRESHOLDS["synthetic_mutation_p99_max_s"],
        "pressure_event_to_exact_p99": pressure is not None
        and float(pressure["event_to_exact_duration_s"]["p99"])
        <= LINUX_SHADOW_THRESHOLDS["pressure_event_to_exact_p99_max_s"],
        "pressure_event_to_exact_max": pressure is not None
        and float(pressure["event_to_exact_duration_s"]["max"])
        <= LINUX_SHADOW_THRESHOLDS["pressure_event_to_exact_max_s"],
        "exact_mutations": mutation is not None
        and int(mutation["success_count"]) == int(mutation["sample_count"]),
        "exact_pressure_mutations": pressure is not None
        and int(pressure["success_count"]) == int(pressure["mutation_sample_count"]),
        "zero_watcher_errors": int(receipt["watcher_health"]["total_error_count"]) == 0
        and pressure is not None
        and int(pressure["watcher_health"]["total_error_count"]) == 0,
        "watch_budget": watch_ratio is not None
        and watch_ratio <= LINUX_SHADOW_THRESHOLDS["watch_ratio_max"],
    }
    return {
        "schema": LINUX_SHADOW_GATE_VERSION,
        "thresholds": dict(LINUX_SHADOW_THRESHOLDS),
        "checks": checks,
        "max_user_watches": max_user_watches,
        "watched_directories": watched_directories,
        "watch_ratio": watch_ratio,
        "passed": all(checks.values()),
        "scope": "linux_single_repository_shadow_candidate",
        "production_route_authorized": False,
    }


def _linux_inotify_max_user_watches() -> int | None:
    if not sys.platform.startswith("linux"):
        return None
    try:
        return int(
            Path("/proc/sys/fs/inotify/max_user_watches")
            .read_text(encoding="utf-8")
            .strip()
        )
    except (OSError, ValueError):
        return None


def _settle_hint_queue(service: NativeObservationService, index: int) -> None:
    for attempt in range(20):
        report = service.poll(f"settle-{index}-{attempt}")
        if report["observation_mode"] == "maintained_no_hint":
            return
    raise RuntimeError("watcher hint queue did not settle after 20 reconciliations")


def _measure_poll(
    service: NativeObservationService,
    request_id: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    report = dict(service.poll(request_id))
    wall_duration_s = time.perf_counter() - started
    return {
        "request_id": request_id,
        "status": report["status"],
        "observation_mode": report["observation_mode"],
        "reconciliation_cause": report["reconciliation_cause"],
        "wall_duration_s": wall_duration_s,
        "engine_duration_s": int(report["total_ns"]) / 1_000_000_000,
        "scan_ns": int(report["scan_ns"]),
        "cache_written": bool(report["cache_written"]),
        "snapshot_entry_count": int(report["snapshot_entry_count"]),
        "snapshot_digest": str(report["snapshot_digest"]),
        "hint_event_count": int(report["hint_event_count"]),
        "hint_error_count": int(report["hint_error_count"]),
        "response_bytes": len(
            json.dumps(report, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ),
    }


def _measure_initialize(
    service: NativeObservationService,
    request_id: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    report = dict(service.initialize_observation(request_id))
    wall_duration_s = time.perf_counter() - started
    return {
        "request_id": request_id,
        "status": report["status"],
        "observation_mode": report["observation_mode"],
        "reconciliation_cause": report["reconciliation_cause"],
        "wall_duration_s": wall_duration_s,
        "engine_duration_s": int(report["total_ns"]) / 1_000_000_000,
        "scan_ns": int(report["scan_ns"]),
        "cache_written": bool(report["cache_written"]),
        "snapshot_entry_count": int(report["snapshot_entry_count"]),
        "snapshot_digest": str(report["snapshot_digest"]),
        "hint_event_count": int(report["hint_event_count"]),
        "hint_error_count": int(report["hint_error_count"]),
        "delta_omitted": bool(report["delta_omitted"]),
        "response_bytes": len(
            json.dumps(report, separators=(",", ":"), sort_keys=True).encode("utf-8")
        ),
    }


def _duration_summary(values: list[float]) -> dict[str, float]:
    return {
        "p50": median(values),
        "p95": _nearest_rank(values, 0.95),
        "p99": _nearest_rank(values, 0.99),
        "max": max(values),
    }


def _integer_summary(values: list[int]) -> dict[str, int | float]:
    return {
        "p50": median(values),
        "p95": _nearest_rank(values, 0.95),
        "p99": _nearest_rank(values, 0.99),
        "max": max(values),
    }


def _nearest_rank(values: list[Any], quantile: float) -> Any:
    return values[max(0, math.ceil(quantile * len(values)) - 1)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark traversal-free native FileSystem idle polling."
    )
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--binary-path", type=Path, required=True)
    parser.add_argument("--cache-path", type=Path, required=True)
    parser.add_argument("--receipt-path", type=Path)
    parser.add_argument("--idle-iterations", type=int, default=30)
    parser.add_argument("--request-timeout-s", type=float, default=5.0)
    parser.add_argument("--mutation-scratch-root", type=Path)
    parser.add_argument("--mutation-iterations", type=int, default=30)
    parser.add_argument("--pressure-scratch-root", type=Path)
    parser.add_argument("--pressure-iterations", type=int, default=30)
    parser.add_argument("--pressure-churn-width", type=int, default=64)
    parser.add_argument("--pressure-workers", type=int, default=2)
    parser.add_argument("--dirty-path-scratch-root", type=Path)
    parser.add_argument("--dirty-path-probe", default="AGENTS.md")
    parser.add_argument("--dirty-path-iterations", type=int, default=30)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    receipt = run_event_hint_idle_benchmark(
        workspace_root=args.workspace_root,
        binary_path=args.binary_path,
        cache_path=args.cache_path,
        idle_iterations=args.idle_iterations,
        request_timeout_s=args.request_timeout_s,
    )
    if args.mutation_scratch_root is not None:
        receipt["mutation_fixture"] = run_event_hint_mutation_benchmark(
            binary_path=args.binary_path,
            scratch_root=args.mutation_scratch_root,
            mutation_iterations=args.mutation_iterations,
            request_timeout_s=args.request_timeout_s,
        )
    if args.pressure_scratch_root is not None:
        receipt["canonical_file_set_pressure"] = (
            run_event_hint_canonical_file_set_pressure_benchmark(
                source_workspace_root=args.workspace_root,
                binary_path=args.binary_path,
                scratch_root=args.pressure_scratch_root,
                mutation_iterations=args.pressure_iterations,
                churn_width=args.pressure_churn_width,
                pressure_workers=args.pressure_workers,
                request_timeout_s=args.request_timeout_s,
            )
        )
        receipt["linux_shadow_gate"] = evaluate_linux_shadow_gate(receipt)
    if args.dirty_path_scratch_root is not None:
        receipt["dirty_path_canonical_file_set"] = (
            run_dirty_path_canonical_file_set_benchmark(
                source_workspace_root=args.workspace_root,
                binary_path=args.binary_path,
                scratch_root=args.dirty_path_scratch_root,
                probe_relative_path=args.dirty_path_probe,
                mutation_iterations=args.dirty_path_iterations,
                pressure_workers=args.pressure_workers,
                request_timeout_s=args.request_timeout_s,
            )
        )
    if args.receipt_path is not None:
        receipt_path = args.receipt_path.expanduser().resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt["receipt_path"] = receipt_path.as_posix()
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(receipt, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
