from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import platform
import sys
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from aware_file_system.native_observation_service import (
    MAINTAINED_OBSERVATION_SERVICE_PROTOCOL,
    NativeObservationService,
)
from aware_file_system.native_snapshot import (
    assert_workspace_snapshot_parity,
    collect_python_workspace_snapshot,
    workspace_snapshot_from_mapping,
)
from aware_file_system.observation_workload_receipt_contract import (
    OBSERVATION_PRODUCTION_WORKLOAD_SCHEMA,
    REQUIRED_SCENARIOS,
    duration_summary,
    evaluate_observation_workload_receipt,
    validate_observation_workload_receipt,
)
from aware_file_system.scripts.benchmark_observation_resilience import (
    run_cache_fault_recovery,
    run_crash_restart_soak,
    run_journal_tail_recovery,
    run_reconciliation_only_recovery,
)


def run_observation_production_workload(
    *,
    binary_path: Path,
    scratch_root: Path,
    file_count: int = 34_000,
    samples: int = 30,
    burst_size: int = 16,
    periodic_interval_s: float = 0.75,
    recovery_restarts: int = 5,
) -> dict[str, Any]:
    if file_count < 128:
        raise ValueError("file_count must be at least 128")
    if samples < 1 or burst_size < 1 or recovery_restarts < 1:
        raise ValueError("samples, burst_size, and recovery_restarts must be positive")
    binary = binary_path.expanduser().resolve()
    if not binary.is_file():
        raise ValueError(f"prepared native binary is missing: {binary}")
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    baseline_threads = _reader_threads()
    all_processes: list[Any] = []
    resources = _ResourceAccumulator()

    with TemporaryDirectory(prefix="aware-fs-production-workload-", dir=scratch) as raw:
        fixture = Path(raw)
        root = fixture / "workspace"
        targets = _build_fixture(root, file_count=file_count, samples=samples)
        scenarios: list[dict[str, Any]] = []

        cold_samples: list[dict[str, Any]] = []
        for index in range(samples):
            service = NativeObservationService(
                binary_path=binary,
                workspace_root=root,
                cache_path=fixture / "cold" / f"{index}.cache",
                request_timeout_s=5.0,
                reconciliation_interval_s=3600.0,
            )
            all_processes.append(service._process)
            before = _process_resources(service.process_id)
            started = time.perf_counter()
            init_started = time.perf_counter()
            service.initialize_observation(f"cold-{index}-initialize")
            init_wall = time.perf_counter() - init_started
            ready_started = time.perf_counter()
            report = dict(
                service.wait_for_watcher_ready(
                    request_id=f"cold-{index}-watcher-ready"
                )
            )
            request_wall = init_wall + (time.perf_counter() - ready_started)
            wall = time.perf_counter() - started
            after = _process_resources(service.process_id)
            cold_samples.append(
                _sample(
                    index=index,
                    wall_s=wall,
                    request_wall_s=request_wall,
                    report=report,
                    before=before,
                    after=after,
                    exact=_is_exact(report),
                )
            )
            resources.add(before, after)
            service.close()
        scenarios.append(_scenario("cold_initialize", cold_samples))

        warm_cache = fixture / "warm.cache"
        with NativeObservationService(
            binary_path=binary,
            workspace_root=root,
            cache_path=warm_cache,
            reconciliation_interval_s=3600.0,
        ) as seed:
            all_processes.append(seed._process)
            seed.initialize_observation("warm-seed")
            seed.wait_for_watcher_ready(request_id="warm-seed-ready")
        warm_samples: list[dict[str, Any]] = []
        for index in range(samples):
            started = time.perf_counter()
            service = NativeObservationService(
                binary_path=binary,
                workspace_root=root,
                cache_path=warm_cache,
                request_timeout_s=5.0,
                reconciliation_interval_s=3600.0,
            )
            all_processes.append(service._process)
            before = _process_resources(service.process_id)
            request_started = time.perf_counter()
            initialized = dict(service.initialize_observation(f"warm-{index}"))
            report = dict(
                service.wait_for_watcher_ready(
                    request_id=f"warm-{index}-watcher-ready"
                )
            )
            request_wall = time.perf_counter() - request_started
            wall = time.perf_counter() - started
            after = _process_resources(service.process_id)
            warm_samples.append(
                _sample(
                    index=index,
                    wall_s=wall,
                    request_wall_s=request_wall,
                    report=report,
                    before=before,
                    after=after,
                    exact=_is_exact(report)
                    and initialized["cache_start_state"] == "loaded",
                )
            )
            resources.add(before, after)
            service.close()
        scenarios.append(_scenario("warm_restart", warm_samples))

        main_cache = fixture / "main.cache"
        service = NativeObservationService(
            binary_path=binary,
            workspace_root=root,
            cache_path=main_cache,
            request_timeout_s=5.0,
            reconciliation_interval_s=3600.0,
        )
        all_processes.append(service._process)
        service.initialize_observation("main-startup")
        service.wait_for_watcher_ready(request_id="main-watcher-ready")
        try:
            idle = [
                _measure_call(
                    index=index,
                    service=service,
                    call=lambda index=index: service.poll(f"idle-{index}"),
                    exact=lambda report: _is_exact(report)
                    and _delta_count(report) == 0,
                    resources=resources,
                )
                for index in range(samples)
            ]
            scenarios.append(_scenario("idle_poll", idle))

            mutation_specs: list[
                tuple[
                    str,
                    Callable[[int], None],
                    Callable[[set[str], set[str], set[str], int], bool],
                ]
            ] = [
                (
                    "create",
                    lambda index: (root / f"dynamic/create-{index:04d}.aware").write_text(
                        f"created-{index}\n", encoding="utf-8"
                    ),
                    lambda added, _modified, _deleted, index: (
                        f"dynamic/create-{index:04d}.aware" in added
                    ),
                ),
                (
                    "update",
                    lambda index: targets["update"][index].write_text(
                        f"updated-{index}-with-a-new-size\n", encoding="utf-8"
                    ),
                    lambda _added, modified, _deleted, index: (
                        _relative(root, targets["update"][index]) in modified
                    ),
                ),
                (
                    "rename",
                    lambda index: targets["rename"][index].rename(
                        targets["rename"][index].with_name(
                            f"renamed-{index:04d}.aware"
                        )
                    ),
                    lambda added, _modified, deleted, index: (
                        _relative(
                            root,
                            targets["rename"][index].with_name(
                                f"renamed-{index:04d}.aware"
                            ),
                        )
                        in added
                        and _relative(root, targets["rename"][index]) in deleted
                    ),
                ),
                (
                    "delete",
                    lambda index: targets["delete"][index].unlink(),
                    lambda _added, _modified, deleted, index: (
                        _relative(root, targets["delete"][index]) in deleted
                    ),
                ),
                (
                    "atomic_replace",
                    lambda index: _atomic_replace(targets["replace"][index], index),
                    lambda _added, modified, _deleted, index: (
                        _relative(root, targets["replace"][index]) in modified
                    ),
                ),
            ]
            for name, mutate, predicate in mutation_specs:
                scenario_samples = []
                for index in range(samples):
                    before = _process_resources(service.process_id)
                    started = time.perf_counter()
                    mutate(index)
                    report, request_wall, delta_count = _wait_for_delta(
                        service=service,
                        request_prefix=f"{name}-{index}",
                        predicate=lambda added, modified, deleted, index=index: predicate(
                            added, modified, deleted, index
                        ),
                    )
                    wall = time.perf_counter() - started
                    after = _process_resources(service.process_id)
                    scenario_samples.append(
                        _sample(
                            index=index,
                            wall_s=wall,
                            request_wall_s=request_wall,
                            report=report,
                            before=before,
                            after=after,
                            exact=_is_exact(report),
                            delta_count=delta_count,
                        )
                    )
                    resources.add(before, after)
                scenarios.append(_scenario(name, scenario_samples))

            ignore_file = root / ".gitignore"
            ignore_samples: list[dict[str, Any]] = []
            for index in range(samples):
                ignored_path = targets["ignore"][index]
                before = _process_resources(service.process_id)
                started = time.perf_counter()
                with ignore_file.open("a", encoding="utf-8") as stream:
                    stream.write(_relative(root, ignored_path) + "\n")
                report, request_wall, delta_count = _wait_for_delta(
                    service=service,
                    request_prefix=f"ignore-policy-{index}",
                    predicate=lambda _added, _modified, deleted, ignored_path=ignored_path: (
                        _relative(root, ignored_path) in deleted
                    ),
                )
                wall = time.perf_counter() - started
                after = _process_resources(service.process_id)
                ignore_samples.append(
                    _sample(
                        index=index,
                        wall_s=wall,
                        request_wall_s=request_wall,
                        report=report,
                        before=before,
                        after=after,
                        exact=_is_exact(report),
                        delta_count=delta_count,
                    )
                )
                resources.add(before, after)
            scenarios.append(_scenario("ignore_policy_change", ignore_samples))

            burst_samples: list[dict[str, Any]] = []
            for index in range(samples):
                expected = {
                    f"dynamic/burst-{index:04d}-{item:03d}.aware"
                    for item in range(burst_size)
                }
                before = _process_resources(service.process_id)
                started = time.perf_counter()
                for relative in expected:
                    (root / relative).write_text(f"{relative}\n", encoding="utf-8")
                report, request_wall, delta_count = _wait_for_delta(
                    service=service,
                    request_prefix=f"burst-{index}",
                    predicate=lambda added, _modified, _deleted, expected=expected: (
                        expected.issubset(added)
                    ),
                )
                wall = time.perf_counter() - started
                after = _process_resources(service.process_id)
                burst_samples.append(
                    _sample(
                        index=index,
                        wall_s=wall,
                        request_wall_s=request_wall,
                        report=report,
                        before=before,
                        after=after,
                        exact=_is_exact(report),
                        delta_count=delta_count,
                    )
                )
                resources.add(before, after)
            scenarios.append(_scenario("bounded_burst", burst_samples))

            process_context = multiprocessing.get_context("spawn")
            pressure_stop = process_context.Event()
            pressure = process_context.Process(
                target=_cpu_pressure_worker,
                args=(pressure_stop,),
                name="aware-fs-production-pressure",
            )
            pressure.start()
            try:
                pressure_samples = [
                    _measure_call(
                        index=index,
                        service=service,
                        call=lambda index=index: service.observe(f"pressure-{index}"),
                        exact=_is_exact,
                        resources=resources,
                    )
                    for index in range(samples)
                ]
            finally:
                pressure_stop.set()
                pressure.join(timeout=5.0)
                if pressure.is_alive():
                    pressure.terminate()
                    pressure.join(timeout=5.0)
            scenarios.append(
                _scenario("pressure_full_reconcile", pressure_samples)
            )

            io_context = multiprocessing.get_context("spawn")
            io_stop = io_context.Event()
            io_pressure = io_context.Process(
                target=_io_pressure_worker,
                args=(io_stop, fixture / "io-pressure.bin"),
                name="aware-fs-production-io-pressure",
            )
            io_pressure.start()
            try:
                io_pressure_samples = [
                    _measure_call(
                        index=index,
                        service=service,
                        call=lambda index=index: service.observe(
                            f"io-pressure-{index}"
                        ),
                        exact=_is_exact,
                        resources=resources,
                    )
                    for index in range(samples)
                ]
            finally:
                io_stop.set()
                io_pressure.join(timeout=5.0)
                if io_pressure.is_alive():
                    io_pressure.terminate()
                    io_pressure.join(timeout=5.0)
            scenarios.append(
                _scenario("io_pressure_full_reconcile", io_pressure_samples)
            )
        finally:
            service.close()

        periodic = NativeObservationService(
            binary_path=binary,
            workspace_root=root,
            cache_path=main_cache,
            request_timeout_s=5.0,
            reconciliation_interval_s=periodic_interval_s,
        )
        all_processes.append(periodic._process)
        periodic.initialize_observation("periodic-startup")
        periodic.wait_for_watcher_ready(request_id="periodic-watcher-ready")
        try:
            audit_samples = [
                _wait_for_periodic_audit(
                    service=periodic,
                    index=index,
                    resources=resources,
                    interval_s=periodic_interval_s,
                )
                for index in range(samples)
            ]
            scenarios.append(_scenario("periodic_audit_poll", audit_samples))
            rust_snapshot = workspace_snapshot_from_mapping(periodic.snapshot())
            python_snapshot = collect_python_workspace_snapshot(
                root,
                cache_dir=fixture / "python-parity-cache",
            )
            assert_workspace_snapshot_parity(
                python_snapshot=python_snapshot,
                rust_snapshot=rust_snapshot,
            )
            final_report = dict(periodic.poll("final-identity"))
        finally:
            periodic.close()

        concurrent_samples = _run_concurrent_distinct_roots(
            binary_path=binary,
            fixture_root=fixture / "concurrent",
            total_file_count=file_count,
            samples=samples,
            all_processes=all_processes,
            resources=resources,
        )
        scenarios.append(_scenario("concurrent_distinct_roots", concurrent_samples))

        recovery_scratch = fixture / "recovery"
        restart = run_crash_restart_soak(
            binary_path=binary,
            scratch_root=recovery_scratch,
            restart_iterations=recovery_restarts,
        )
        cache_recovery = run_cache_fault_recovery(
            binary_path=binary,
            scratch_root=recovery_scratch,
        )
        journal_recovery = run_journal_tail_recovery(
            binary_path=binary,
            scratch_root=recovery_scratch,
        )
        reconciliation = run_reconciliation_only_recovery(
            binary_path=binary,
            scratch_root=recovery_scratch,
        )

        time.sleep(0.05)
        orphan_process_ids = [
            process.pid for process in all_processes if process.poll() is None
        ]
        leaked_threads = sorted(_reader_threads().difference(baseline_threads))
        recovery_checks = {
            "forced_restart_exact": (
                restart["success_count"] == recovery_restarts
                and restart["orphan_process_ids"] == []
                and restart["leaked_reader_threads"] == []
            ),
            "truncated_cache_rebuilt": (
                cache_recovery["truncated_cache"]["cache_start_state"]
                == "corrupt"
                and cache_recovery["truncated_cache"]["cache_written"] is True
                and cache_recovery["truncated_cache"]["snapshot_digest_stable"]
                is True
            ),
            "torn_journal_tail_recovered": journal_recovery["passed"] is True,
            "reconciliation_only_exact": (
                reconciliation["unchanged_exact"] is True
                and reconciliation["changed_exact"] is True
            ),
            "no_orphan_process": orphan_process_ids == [],
            "no_reader_thread_leak": leaked_threads == [],
        }

        receipt: dict[str, Any] = {
            "schema": OBSERVATION_PRODUCTION_WORKLOAD_SCHEMA,
            "created_at": datetime.now(UTC).isoformat(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python": platform.python_version(),
            },
            "binary": {
                "path": binary.as_posix(),
                "sha256": _sha256(binary),
                "bytes": binary.stat().st_size,
            },
            "protocol": MAINTAINED_OBSERVATION_SERVICE_PROTOCOL,
            "fixture": {
                "root": root.as_posix(),
                "file_count": file_count,
                "canonical_filter_profile": "canonical_source_v1",
                "initial_inventory_digest": cold_samples[0]["snapshot_digest"],
                "burst_size": burst_size,
                "periodic_interval_ms": round(periodic_interval_s * 1000),
            },
            "scenarios": scenarios,
            "recovery_checks": recovery_checks,
            "resources": {
                "process_cpu_s": resources.cpu_s,
                "rss_peak_bytes": resources.rss_peak_bytes,
                "io_read_bytes": resources.io_read_bytes,
                "io_write_bytes": resources.io_write_bytes,
            },
            "final": {
                "python_parity": True,
                "digest": rust_snapshot.inventory_digest,
                "generation": int(final_report["to_generation"]),
                "orphan_process_ids": orphan_process_ids,
                "leaked_reader_threads": leaked_threads,
            },
            "locks": [
                "one observer and one maintained snapshot per admitted root",
                "watch notifications remain invalidation hints",
                "prepared Rust runtime contains no build work in request latency",
                "no materialization, graph, ORM, or consumer-local observation",
                "host-native macOS and Windows evidence is not inferred",
            ],
        }
        validate_observation_workload_receipt(receipt)
        return {
            "bundle_schema": "aware.file_system.observation_production_admission.v1",
            "evidence": receipt,
            "admission": evaluate_observation_workload_receipt(receipt),
        }


class _ResourceAccumulator:
    def __init__(self) -> None:
        self.cpu_s = 0.0
        self.rss_peak_bytes = 0
        self.io_read_bytes = 0
        self.io_write_bytes = 0

    def add(
        self,
        before: Mapping[str, float | int | None],
        after: Mapping[str, float | int | None],
    ) -> None:
        self.cpu_s += _delta(before.get("cpu_s"), after.get("cpu_s")) or 0.0
        rss = after.get("rss_bytes")
        if isinstance(rss, int):
            self.rss_peak_bytes = max(self.rss_peak_bytes, rss)
        self.io_read_bytes += int(
            _delta(before.get("io_read_bytes"), after.get("io_read_bytes")) or 0
        )
        self.io_write_bytes += int(
            _delta(before.get("io_write_bytes"), after.get("io_write_bytes")) or 0
        )


def _scenario(name: str, samples: list[dict[str, Any]]) -> dict[str, Any]:
    workload_class, budget = REQUIRED_SCENARIOS[name]
    return {
        "name": name,
        "workload_class": workload_class,
        "budget": budget.model_dump(),
        "samples": samples,
        "failures": [],
        "wall_s": duration_summary([float(sample["wall_s"]) for sample in samples]),
        "request_wall_s": duration_summary(
            [float(sample["request_wall_s"]) for sample in samples]
        ),
    }


def _measure_call(
    *,
    index: int,
    service: NativeObservationService,
    call: Callable[[], Mapping[str, Any]],
    exact: Callable[[Mapping[str, Any]], bool],
    resources: _ResourceAccumulator,
) -> dict[str, Any]:
    before = _process_resources(service.process_id)
    started = time.perf_counter()
    report = dict(call())
    wall = time.perf_counter() - started
    after = _process_resources(service.process_id)
    resources.add(before, after)
    return _sample(
        index=index,
        wall_s=wall,
        request_wall_s=wall,
        report=report,
        before=before,
        after=after,
        exact=exact(report),
    )


def _wait_for_delta(
    *,
    service: NativeObservationService,
    request_prefix: str,
    predicate: Callable[[set[str], set[str], set[str]], bool],
) -> tuple[dict[str, Any], float, int]:
    deadline = time.monotonic() + service.request_timeout_s
    added: set[str] = set()
    modified: set[str] = set()
    deleted: set[str] = set()
    request_wall = 0.0
    attempt = 0
    first_generation: int | None = None
    while True:
        started = time.perf_counter()
        report = dict(service.poll(f"{request_prefix}-{attempt}"))
        request_wall += time.perf_counter() - started
        if first_generation is None:
            first_generation = int(report["from_generation"])
        added.update(str(path) for path in report["added"])
        modified.update(str(path) for path in report["modified"])
        deleted.update(str(path) for path in report["deleted"])
        if predicate(added, modified, deleted):
            report["from_generation"] = first_generation
            return report, request_wall, len(added) + len(modified) + len(deleted)
        if report["status"] not in {"exact", "maintained"}:
            raise RuntimeError(f"{request_prefix} returned non-exact state: {report}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"{request_prefix} did not converge before deadline")
        attempt += 1
        time.sleep(0.002)


def _wait_for_periodic_audit(
    *,
    service: NativeObservationService,
    index: int,
    resources: _ResourceAccumulator,
    interval_s: float,
) -> dict[str, Any]:
    before = _process_resources(service.process_id)
    started = time.perf_counter()
    attempt = 0
    while True:
        poll_started = time.perf_counter()
        report = dict(service.poll(f"periodic-{index}-{attempt}"))
        current_request_wall = time.perf_counter() - poll_started
        if report["observation_mode"] == "periodic_audit_rebased":
            after = _process_resources(service.process_id)
            resources.add(before, after)
            return _sample(
                index=index,
                wall_s=time.perf_counter() - started,
                request_wall_s=current_request_wall,
                report=report,
                before=before,
                after=after,
                exact=_is_exact(report) and _delta_count(report) == 0,
            )
        if report["status"] == "degraded":
            raise RuntimeError(f"periodic audit degraded: {report}")
        if time.perf_counter() - started > interval_s * 3 + 5:
            raise TimeoutError("periodic audit did not complete")
        attempt += 1
        time.sleep(0.005)


def _run_concurrent_distinct_roots(
    *,
    binary_path: Path,
    fixture_root: Path,
    total_file_count: int,
    samples: int,
    all_processes: list[Any],
    resources: _ResourceAccumulator,
) -> list[dict[str, Any]]:
    root_a = fixture_root / "a"
    root_b = fixture_root / "b"
    per_root = max(64, total_file_count // 2)
    _build_flat_fixture(root_a, per_root)
    _build_flat_fixture(root_b, per_root)
    service_a = NativeObservationService(
        binary_path=binary_path,
        workspace_root=root_a,
        cache_path=fixture_root / "a.cache",
        reconciliation_interval_s=3600.0,
    )
    service_b = NativeObservationService(
        binary_path=binary_path,
        workspace_root=root_b,
        cache_path=fixture_root / "b.cache",
        reconciliation_interval_s=3600.0,
    )
    all_processes.extend([service_a._process, service_b._process])
    services = (service_a, service_b)
    for position, service in enumerate(services):
        service.initialize_observation(f"concurrent-{position}-startup")
        service.wait_for_watcher_ready(
            request_id=f"concurrent-{position}-watcher-ready"
        )
    result: list[dict[str, Any]] = []
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            for index in range(samples):
                paths = (
                    root_a / f"source-{index % per_root:06d}.aware",
                    root_b / f"source-{index % per_root:06d}.aware",
                )
                before_a = _process_resources(service_a.process_id)
                before_b = _process_resources(service_b.process_id)
                started = time.perf_counter()
                for position, path in enumerate(paths):
                    path.write_text(
                        f"concurrent-{index}-{position}-new-size\n",
                        encoding="utf-8",
                    )
                futures = [
                    executor.submit(
                        _wait_for_delta,
                        service=service,
                        request_prefix=f"concurrent-{index}-{position}",
                        predicate=lambda _added, modified, _deleted, path=path, root=root: (
                            _relative(root, path) in modified
                        ),
                    )
                    for position, (service, path, root) in enumerate(
                        zip(services, paths, (root_a, root_b), strict=True)
                    )
                ]
                reports = [future.result() for future in futures]
                wall = time.perf_counter() - started
                after_a = _process_resources(service_a.process_id)
                after_b = _process_resources(service_b.process_id)
                resources.add(before_a, after_a)
                resources.add(before_b, after_b)
                report = reports[0][0]
                result.append(
                    _sample(
                        index=index,
                        wall_s=wall,
                        request_wall_s=max(item[1] for item in reports),
                        report=report,
                        before=before_a,
                        after=after_a,
                        exact=all(_is_exact(item[0]) for item in reports),
                        delta_count=sum(item[2] for item in reports),
                    )
                )
    finally:
        service_a.close()
        service_b.close()
    return result


def _sample(
    *,
    index: int,
    wall_s: float,
    request_wall_s: float,
    report: Mapping[str, Any],
    before: Mapping[str, float | int | None],
    after: Mapping[str, float | int | None],
    exact: bool,
    delta_count: int | None = None,
) -> dict[str, Any]:
    return {
        "index": index,
        "wall_s": wall_s,
        "request_wall_s": request_wall_s,
        "engine_s": int(report.get("total_ns", 0)) / 1_000_000_000,
        "scan_s": int(report.get("scan_ns", 0)) / 1_000_000_000,
        "merge_s": int(report.get("merge_ns", 0)) / 1_000_000_000,
        "cpu_s_delta": _delta(before.get("cpu_s"), after.get("cpu_s")),
        "rss_bytes": after.get("rss_bytes"),
        "io_read_bytes_delta": _delta(
            before.get("io_read_bytes"), after.get("io_read_bytes")
        ),
        "io_write_bytes_delta": _delta(
            before.get("io_write_bytes"), after.get("io_write_bytes")
        ),
        "from_generation": int(report.get("from_generation", 0)),
        "to_generation": int(report.get("to_generation", 0)),
        "snapshot_digest": str(report["snapshot_digest"]),
        "status": str(report.get("status", "unknown")),
        "observation_mode": str(report.get("observation_mode", "unknown")),
        "reconciliation_cause": str(report.get("reconciliation_cause", "none")),
        "delta_count": _delta_count(report) if delta_count is None else delta_count,
        "exact": exact,
    }


def _build_fixture(
    root: Path,
    *,
    file_count: int,
    samples: int,
) -> dict[str, list[Path]]:
    root.mkdir(parents=True)
    dynamic = root / "dynamic"
    dynamic.mkdir()
    targets = {
        name: [dynamic / f"{name}-{index:04d}.aware" for index in range(samples)]
        for name in ("update", "rename", "delete", "replace", "ignore")
    }
    target_count = sum(len(paths) for paths in targets.values())
    if target_count >= file_count:
        raise ValueError("file_count must exceed reserved mutation targets")
    for name, paths in targets.items():
        for index, path in enumerate(paths):
            path.write_text(f"{name}-{index}\n", encoding="utf-8")
    remaining = file_count - target_count
    partitions = [root / "source" / f"{index:04d}" for index in range(256)]
    for partition in partitions:
        partition.mkdir(parents=True)
    for index in range(remaining):
        (partitions[index % len(partitions)] / f"source-{index:06d}.aware").write_text(
            f"source-{index}\n",
            encoding="utf-8",
        )
    return targets


def _build_flat_fixture(root: Path, count: int) -> None:
    root.mkdir(parents=True)
    for index in range(count):
        (root / f"source-{index:06d}.aware").write_text(
            f"source-{index}\n", encoding="utf-8"
        )


def _atomic_replace(target: Path, index: int) -> None:
    replacement = target.with_name(f".replacement-{index:04d}.tmp")
    replacement.write_text(
        f"atomic-replacement-{index}-with-new-size\n", encoding="utf-8"
    )
    os.replace(replacement, target)


def _cpu_pressure_worker(stop: Any) -> None:
    payload = b"aware-file-system-pressure" * 32_768
    while not stop.is_set():
        hashlib.sha256(payload).digest()


def _io_pressure_worker(stop: Any, path: Path) -> None:
    payload = b"aware-file-system-io-pressure" * 131_072
    with path.open("w+b", buffering=0) as stream:
        while not stop.is_set():
            stream.seek(0)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())


def _process_resources(process_id: int) -> dict[str, float | int | None]:
    result: dict[str, float | int | None] = {
        "cpu_s": None,
        "rss_bytes": None,
        "io_read_bytes": None,
        "io_write_bytes": None,
    }
    if not sys.platform.startswith("linux"):
        return result
    try:
        fields = Path(f"/proc/{process_id}/stat").read_text(encoding="utf-8").split()
        ticks = int(fields[13]) + int(fields[14])
        result["cpu_s"] = ticks / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError):
        pass
    try:
        for line in Path(f"/proc/{process_id}/status").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.startswith("VmRSS:"):
                result["rss_bytes"] = int(line.split()[1]) * 1024
                break
    except (OSError, ValueError, IndexError):
        pass
    try:
        for line in Path(f"/proc/{process_id}/io").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.startswith("read_bytes:"):
                result["io_read_bytes"] = int(line.split()[1])
            elif line.startswith("write_bytes:"):
                result["io_write_bytes"] = int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return result


def _delta(
    before: float | int | None,
    after: float | int | None,
) -> float | int | None:
    if before is None or after is None:
        return None
    return max(0, after - before)


def _is_exact(report: Mapping[str, Any]) -> bool:
    return report.get("status") in {"exact", "maintained"} and len(
        str(report.get("snapshot_digest"))
    ) == 64


def _delta_count(report: Mapping[str, Any]) -> int:
    return sum(len(report.get(key, [])) for key in ("added", "modified", "deleted"))


def _reader_threads() -> set[str]:
    return {
        thread.name
        for thread in threading.enumerate()
        if thread.name.startswith("aware-fs-observation-")
    }


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the fail-closed native FileSystem production workload."
    )
    parser.add_argument("--binary-path", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--receipt-path", type=Path, required=True)
    parser.add_argument("--file-count", type=int, default=34_000)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--burst-size", type=int, default=16)
    parser.add_argument("--periodic-interval-s", type=float, default=0.75)
    parser.add_argument("--recovery-restarts", type=int, default=5)
    args = parser.parse_args(argv)
    receipt = run_observation_production_workload(
        binary_path=args.binary_path,
        scratch_root=args.scratch_root,
        file_count=args.file_count,
        samples=args.samples,
        burst_size=args.burst_size,
        periodic_interval_s=args.periodic_interval_s,
        recovery_restarts=args.recovery_restarts,
    )
    receipt_path = args.receipt_path.expanduser().resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt["receipt_path"] = receipt_path.as_posix()
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt["admission"], indent=2, sort_keys=True))
    return 0 if receipt["admission"]["admitted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
