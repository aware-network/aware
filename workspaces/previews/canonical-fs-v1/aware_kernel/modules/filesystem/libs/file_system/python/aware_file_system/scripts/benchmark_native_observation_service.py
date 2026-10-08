from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from aware_file_system.native_observation_service import NativeObservationService


MAINTAINED_OBSERVATION_BENCHMARK_VERSION = (
    "aware.file_system.maintained_observation_benchmark.v1"
)


def run_maintained_observation_benchmark(
    *,
    workspace_root: Path,
    binary_path: Path,
    cache_path: Path,
    warm_iterations: int = 3,
    restart_iterations: int = 3,
) -> dict[str, Any]:
    if warm_iterations < 1 or restart_iterations < 1:
        raise ValueError("warm and restart iterations must be at least one")
    root = workspace_root.expanduser().resolve()
    binary = binary_path.expanduser().resolve()
    cache = cache_path.expanduser().resolve()
    if cache.exists():
        raise ValueError("benchmark cache path must not exist")

    cold_samples: list[dict[str, Any]] = []
    warm_samples: list[dict[str, Any]] = []
    restart_samples: list[dict[str, Any]] = []
    service, cold_activation_duration_s = _start_service(
        binary_path=binary,
        workspace_root=root,
        cache_path=cache,
    )
    try:
        cold_samples.append(
            _measure_observe(
                service,
                "cold-0",
                activation_duration_s=cold_activation_duration_s,
            )
        )
        for index in range(warm_iterations):
            warm_samples.append(_measure_observe(service, f"warm-{index}"))
    finally:
        service.close()

    for index in range(restart_iterations):
        service, activation_duration_s = _start_service(
            binary_path=binary,
            workspace_root=root,
            cache_path=cache,
        )
        try:
            restart_samples.append(
                _measure_observe(
                    service,
                    f"restart-{index}",
                    activation_duration_s=activation_duration_s,
                )
            )
        finally:
            service.close()

    scenarios = {
        "cold_missing_cache": _summarize(cold_samples),
        "warm_same_process": _summarize(warm_samples),
        "warm_process_restart": _summarize(restart_samples),
    }
    all_snapshot_digests = sorted(
        {
            sample["snapshot_digest"]
            for samples in (cold_samples, warm_samples, restart_samples)
            for sample in samples
        }
    )
    return {
        "benchmark_version": MAINTAINED_OBSERVATION_BENCHMARK_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "workspace_root": root.as_posix(),
        "binary_path": binary.as_posix(),
        "cache_path": cache.as_posix(),
        "cache_bytes": cache.stat().st_size,
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "all_snapshot_digests": all_snapshot_digests,
        "exact_digest_stable": len(all_snapshot_digests) == 1,
        "production_tail_eligible": False,
        "locks": [
            "prepared persistent process; build excluded from request latency",
            "candidate is explicit and unrouted",
            "no materialization, graph, ORM, or watcher",
            "fewer than 30 samples cannot claim production p99",
        ],
    }


def _measure_observe(
    service: NativeObservationService,
    request_id: str,
    *,
    activation_duration_s: float | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    report = service.observe(request_id)
    wall_duration_s = time.perf_counter() - started
    sample = {
        "request_id": request_id,
        "wall_duration_s": wall_duration_s,
        "engine_duration_s": int(report["total_ns"]) / 1_000_000_000,
        "scan_duration_s": int(report["scan_ns"]) / 1_000_000_000,
        "persistence_duration_s": int(report["persistence_ns"]) / 1_000_000_000,
        "cache_start_state": report["cache_start_state"],
        "cache_written": report["cache_written"],
        "from_generation": report["from_generation"],
        "to_generation": report["to_generation"],
        "snapshot_entry_count": report["snapshot_entry_count"],
        "snapshot_digest": report["snapshot_digest"],
        "delta_digest": report["delta_digest"],
        "added_count": len(report["added"]),
        "modified_count": len(report["modified"]),
        "deleted_count": len(report["deleted"]),
        "status": report["status"],
    }
    if activation_duration_s is not None:
        sample["activation_duration_s"] = activation_duration_s
        sample["ready_plus_observe_duration_s"] = (
            activation_duration_s + wall_duration_s
        )
    return sample


def _start_service(
    *,
    binary_path: Path,
    workspace_root: Path,
    cache_path: Path,
) -> tuple[NativeObservationService, float]:
    started = time.perf_counter()
    service = NativeObservationService(
        binary_path=binary_path,
        workspace_root=workspace_root,
        cache_path=cache_path,
    )
    try:
        service.ping()
    except BaseException:
        service.close()
        raise
    return service, time.perf_counter() - started


def _summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    durations = sorted(float(sample["wall_duration_s"]) for sample in samples)
    summary = {
        "sample_count": len(samples),
        "success_count": sum(sample["status"] == "exact" for sample in samples),
        "cache_write_count": sum(bool(sample["cache_written"]) for sample in samples),
        "snapshot_digests": sorted({sample["snapshot_digest"] for sample in samples}),
        "entry_counts": sorted({sample["snapshot_entry_count"] for sample in samples}),
        "wall_duration_s": {
            "p50": median(durations),
            "p95": _nearest_rank(durations, 0.95),
            "p99": _nearest_rank(durations, 0.99),
            "max": max(durations),
        },
        "samples": samples,
    }
    activation_durations = sorted(
        float(sample["activation_duration_s"])
        for sample in samples
        if "activation_duration_s" in sample
    )
    if activation_durations:
        summary["activation_duration_s"] = _duration_summary(activation_durations)
        summary["ready_plus_observe_duration_s"] = _duration_summary(
            sorted(float(sample["ready_plus_observe_duration_s"]) for sample in samples)
        )
    return summary


def _duration_summary(durations: list[float]) -> dict[str, float]:
    return {
        "p50": median(durations),
        "p95": _nearest_rank(durations, 0.95),
        "p99": _nearest_rank(durations, 0.99),
        "max": max(durations),
    }


def _nearest_rank(values: list[float], quantile: float) -> float:
    index = max(0, math.ceil(quantile * len(values)) - 1)
    return values[index]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark the persistent Rust FileSystem observation service."
    )
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--binary-path", type=Path, required=True)
    parser.add_argument("--cache-path", type=Path, required=True)
    parser.add_argument("--receipt-path", type=Path)
    parser.add_argument("--warm-iterations", type=int, default=3)
    parser.add_argument("--restart-iterations", type=int, default=3)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    receipt = run_maintained_observation_benchmark(
        workspace_root=args.workspace_root,
        binary_path=args.binary_path,
        cache_path=args.cache_path,
        warm_iterations=args.warm_iterations,
        restart_iterations=args.restart_iterations,
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
