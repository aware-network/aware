from __future__ import annotations

import argparse
import json
import math
import os
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from typing import Any

from aware_file_system.native_observation_service import NativeObservationService
from aware_file_system.native_snapshot import (
    assert_workspace_snapshot_parity,
    collect_python_workspace_snapshot,
    workspace_snapshot_from_mapping,
)


PERIODIC_AUDIT_WORKLOAD_SCHEMA = "aware.file_system.periodic_audit_workload.v1"


def run_periodic_audit_workload(
    *,
    binary_path: Path,
    scratch_root: Path,
    file_count: int = 34_000,
    audit_samples: int = 30,
    baseline_samples: int = 5,
    reconciliation_interval_s: float = 2.0,
    poll_interval_s: float = 0.005,
    request_timeout_s: float = 5.0,
) -> dict[str, Any]:
    if file_count < 1:
        raise ValueError("file_count must be at least one")
    if audit_samples < 1 or baseline_samples < 1:
        raise ValueError("audit and baseline samples must be at least one")
    if reconciliation_interval_s <= 0 or poll_interval_s <= 0:
        raise ValueError("reconciliation and poll intervals must be positive")

    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    baseline: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    all_poll_durations: list[float] = []
    rss_samples: list[int] = []
    with TemporaryDirectory(prefix="aware-fs-periodic-audit-", dir=scratch) as raw:
        fixture = Path(raw)
        workspace = fixture / "workspace"
        cache = fixture / "state.cache"
        _build_real_sized_fixture(workspace, file_count)
        service = NativeObservationService(
            binary_path=binary_path,
            workspace_root=workspace,
            cache_path=cache,
            request_timeout_s=request_timeout_s,
            reconciliation_interval_s=reconciliation_interval_s,
        )
        process = service._process
        process_id = service.process_id
        cpu_before = _process_cpu_seconds(process_id)
        try:
            startup = dict(service.initialize_observation("periodic-workload-startup"))
            service.wait_for_watcher_ready(
                request_id="periodic-workload-watcher-ready"
            )
            watcher = dict(service.health()["watcher"])
            for index in range(baseline_samples):
                started = time.perf_counter()
                report = dict(service.observe(f"periodic-baseline-{index}"))
                wall_s = time.perf_counter() - started
                baseline.append(_full_sample(report, wall_s))

            for index in range(audit_samples):
                cycle_started = time.perf_counter()
                launch_sample: dict[str, Any] | None = None
                completion_sample: dict[str, Any] | None = None
                cycle_poll_count = 0
                while completion_sample is None:
                    poll_started = time.perf_counter()
                    report = dict(service.poll(f"periodic-audit-{index}-{cycle_poll_count}"))
                    wall_s = time.perf_counter() - poll_started
                    all_poll_durations.append(wall_s)
                    cycle_poll_count += 1
                    rss = _process_rss_bytes(process_id)
                    if rss is not None:
                        rss_samples.append(rss)
                    mode = str(report["observation_mode"])
                    if mode == "periodic_audit_running" and launch_sample is None:
                        launch_sample = _poll_sample(report, wall_s)
                    elif mode == "periodic_audit_rebased":
                        completion_sample = _poll_sample(report, wall_s)
                    elif report.get("reconciliation_cause") in {
                        "periodic",
                        "periodic_audit_overdue",
                        "periodic_audit_failed",
                    }:
                        completion_sample = _poll_sample(report, wall_s)
                    if time.perf_counter() - cycle_started > reconciliation_interval_s * 2 + 5:
                        raise TimeoutError("periodic audit workload cycle did not complete")
                    time.sleep(poll_interval_s)
                audit.append(
                    {
                        "index": index,
                        "cycle_duration_s": time.perf_counter() - cycle_started,
                        "poll_count": cycle_poll_count,
                        "launch": launch_sample,
                        "completion": completion_sample,
                    }
                )

            rust_snapshot = workspace_snapshot_from_mapping(service.snapshot())
            python_snapshot = collect_python_workspace_snapshot(
                workspace,
                cache_dir=fixture / "python-cache",
            )
            assert_workspace_snapshot_parity(
                python_snapshot=python_snapshot,
                rust_snapshot=rust_snapshot,
            )
            final_generation = int(service.poll("periodic-workload-final")["to_generation"])
            final_digest = rust_snapshot.inventory_digest
            cpu_after = _process_cpu_seconds(process_id)
        finally:
            service.close()
        orphan_process = process.poll() is None

    baseline_wall = [float(sample["wall_s"]) for sample in baseline]
    baseline_scan = [float(sample["scan_s"]) for sample in baseline]
    launch_wall = [
        float(sample["launch"]["wall_s"])
        for sample in audit
        if sample["launch"] is not None
    ]
    completion_wall = [float(sample["completion"]["wall_s"]) for sample in audit]
    completion_engine = [
        float(sample["completion"]["engine_s"]) for sample in audit
    ]
    background_scan = [
        float(sample["completion"]["scan_s"]) for sample in audit
    ]
    cycle_durations = [float(sample["cycle_duration_s"]) for sample in audit]
    exact_completions = sum(
        sample["completion"]["observation_mode"] == "periodic_audit_rebased"
        and sample["completion"]["status"] == "exact"
        and sample["completion"]["delta_count"] == 0
        for sample in audit
    )
    deadline_met = all(
        duration <= reconciliation_interval_s for duration in cycle_durations
    )
    production_gate_passed = (
        file_count >= 33_000
        and audit_samples >= 30
        and exact_completions == audit_samples
        and len(launch_wall) == audit_samples
        and _nearest_rank(completion_wall, 0.99) <= 0.100
        and deadline_met
        and not orphan_process
    )
    return {
        "schema": PERIODIC_AUDIT_WORKLOAD_SCHEMA,
        "created_at": datetime.now(UTC).isoformat(),
        "binary_path": binary_path.expanduser().resolve().as_posix(),
        "file_count": file_count,
        "audit_sample_count": audit_samples,
        "baseline_sample_count": baseline_samples,
        "reconciliation_interval_s": reconciliation_interval_s,
        "poll_interval_s": poll_interval_s,
        "startup": startup,
        "watcher": watcher,
        "baseline_synchronous_full": {
            "wall_s": _duration_summary(baseline_wall),
            "scan_s": _duration_summary(baseline_scan),
            "samples": baseline,
        },
        "periodic_background": {
            "exact_completion_count": exact_completions,
            "launch_wall_s": _duration_summary(launch_wall),
            "completion_wall_s": _duration_summary(completion_wall),
            "completion_engine_s": _duration_summary(completion_engine),
            "background_scan_s": _duration_summary(background_scan),
            "cycle_duration_s": _duration_summary(cycle_durations),
            "all_poll_wall_s": _duration_summary(all_poll_durations),
            "deadline_met": deadline_met,
            "samples": audit,
        },
        "resources": {
            "process_cpu_s": (
                cpu_after - cpu_before
                if cpu_before is not None and cpu_after is not None
                else None
            ),
            "rss_peak_bytes": max(rss_samples) if rss_samples else None,
        },
        "final": {
            "generation": final_generation,
            "digest": final_digest,
            "python_parity": True,
            "orphan_process": orphan_process,
        },
        "production_gate_passed": production_gate_passed,
        "locks": [
            "one native watcher and one maintained snapshot",
            "periodic candidate has no cache, journal, cursor, or generation authority",
            "30-second production recovery deadline is not widened",
            "no materialization, graph, ORM, or consumer-local observation",
        ],
    }


def _build_real_sized_fixture(root: Path, file_count: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    directory_count = min(256, max(1, math.ceil(file_count / 128)))
    directories = [root / f"partition-{index:04d}" for index in range(directory_count)]
    for directory in directories:
        directory.mkdir()
    for index in range(file_count):
        directory = directories[index % directory_count]
        (directory / f"source-{index:06d}.aware").write_text(
            f"source-{index}\n",
            encoding="utf-8",
        )


def _full_sample(report: dict[str, Any], wall_s: float) -> dict[str, Any]:
    return {
        "wall_s": wall_s,
        "engine_s": int(report["total_ns"]) / 1_000_000_000,
        "scan_s": int(report["scan_ns"]) / 1_000_000_000,
        "status": report["status"],
        "observation_mode": report["observation_mode"],
        "snapshot_digest": report["snapshot_digest"],
    }


def _poll_sample(report: dict[str, Any], wall_s: float) -> dict[str, Any]:
    return {
        "wall_s": wall_s,
        "engine_s": int(report["total_ns"]) / 1_000_000_000,
        "scan_s": int(report["scan_ns"]) / 1_000_000_000,
        "merge_s": int(report["merge_ns"]) / 1_000_000_000,
        "status": str(report["status"]),
        "observation_mode": str(report["observation_mode"]),
        "reconciliation_cause": str(report["reconciliation_cause"]),
        "delta_count": (
            int(report["added_count"])
            + int(report["modified_count"])
            + int(report["deleted_count"])
        ),
        "from_generation": int(report["from_generation"]),
        "to_generation": int(report["to_generation"]),
    }


def _duration_summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    ordered = sorted(values)
    return {
        "p50": median(ordered),
        "p95": _nearest_rank(ordered, 0.95),
        "p99": _nearest_rank(ordered, 0.99),
        "max": max(ordered),
    }


def _nearest_rank(values: list[float], quantile: float) -> float:
    if not values:
        return math.inf
    return values[max(0, math.ceil(quantile * len(values)) - 1)]


def _process_cpu_seconds(process_id: int) -> float | None:
    stat = Path(f"/proc/{process_id}/stat")
    if not stat.is_file():
        return None
    fields = stat.read_text(encoding="utf-8").split()
    ticks = int(fields[13]) + int(fields[14])
    return ticks / os.sysconf("SC_CLK_TCK")


def _process_rss_bytes(process_id: int) -> int | None:
    status = Path(f"/proc/{process_id}/status")
    if not status.is_file():
        return None
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) * 1024
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Characterize synchronous and background periodic FileSystem audits."
    )
    parser.add_argument("--binary-path", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--receipt-path", type=Path, required=True)
    parser.add_argument("--file-count", type=int, default=34_000)
    parser.add_argument("--audit-samples", type=int, default=30)
    parser.add_argument("--baseline-samples", type=int, default=5)
    parser.add_argument("--reconciliation-interval-s", type=float, default=2.0)
    parser.add_argument("--poll-interval-s", type=float, default=0.005)
    args = parser.parse_args(argv)
    receipt = run_periodic_audit_workload(
        binary_path=args.binary_path,
        scratch_root=args.scratch_root,
        file_count=args.file_count,
        audit_samples=args.audit_samples,
        baseline_samples=args.baseline_samples,
        reconciliation_interval_s=args.reconciliation_interval_s,
        poll_interval_s=args.poll_interval_s,
    )
    receipt_path = args.receipt_path.expanduser().resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt["receipt_path"] = receipt_path.as_posix()
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["production_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
