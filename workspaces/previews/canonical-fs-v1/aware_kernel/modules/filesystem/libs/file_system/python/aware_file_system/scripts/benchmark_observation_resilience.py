from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import threading
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from typing import Any

from aware_file_system.native_observation_service import (
    NativeObservationService,
    NativeObservationServiceError,
    ObservationWatchMode,
)
from aware_file_system.observation_platform_contract import (
    PLATFORM_RECEIPT_SCHEMA,
    architecture_class,
    resolve_supported_platform_class,
)

OBSERVATION_RESILIENCE_SCHEMA = "aware.file_system.observation_resilience.v1"


def run_multi_repository_capacity(
    *,
    binary_path: Path,
    scratch_root: Path,
    repository_count: int = 4,
    directories_per_repository: int = 4096,
    request_timeout_s: float = 5.0,
) -> dict[str, Any]:
    if repository_count < 2:
        raise ValueError("repository_count must be at least two")
    if directories_per_repository < 1:
        raise ValueError("directories_per_repository must be at least one")
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="aware-fs-multi-root-", dir=scratch) as raw_root:
        fixture_root = Path(raw_root)
        roots = [
            fixture_root / f"repository-{index}" for index in range(repository_count)
        ]
        for root in roots:
            _build_directory_fixture(root, directories_per_repository)
        services: list[NativeObservationService] = []
        process_ids: list[int] = []
        processes: list[Any] = []
        try:
            activation_started = time.perf_counter()
            for index, root in enumerate(roots):
                service = NativeObservationService(
                    binary_path=binary_path,
                    workspace_root=root,
                    cache_path=fixture_root / f"repository-{index}.cache",
                    request_timeout_s=request_timeout_s,
                    reconciliation_interval_s=3600.0,
                )
                service.ping()
                service.initialize_observation(f"repository-{index}-startup")
                service.wait_for_watcher_ready(
                    request_id=f"repository-{index}-watcher-ready"
                )
                services.append(service)
                process_ids.append(service.process_id)
                processes.append(service._process)
            activation_duration_s = time.perf_counter() - activation_started
            watcher_health = [service.health()["watcher"] for service in services]
            mutation_started = time.perf_counter()
            for index, root in enumerate(roots):
                (root / "probe.txt").write_text(
                    f"changed-repository-{index}-with-new-size\n",
                    encoding="utf-8",
                )
            with ThreadPoolExecutor(max_workers=repository_count) as executor:
                mutation_reports = list(
                    executor.map(
                        _poll_repository_mutation,
                        services,
                        range(repository_count),
                    )
                )
            mutation_duration_s = time.perf_counter() - mutation_started
        finally:
            for service in services:
                service.close()
        _wait_for_process_exit(processes)

    max_user_watches = _linux_inotify_max_user_watches()
    watched_directories = sum(
        int(health["watched_directory_count"]) for health in watcher_health
    )
    watch_ratio = (
        watched_directories / max_user_watches
        if max_user_watches is not None and max_user_watches > 0
        else None
    )
    return {
        "repository_count": repository_count,
        "directories_per_repository": directories_per_repository,
        "activation_duration_s": activation_duration_s,
        "mutation_duration_s": mutation_duration_s,
        "watched_directories": watched_directories,
        "max_user_watches": max_user_watches,
        "watch_ratio": watch_ratio,
        "watcher_health": watcher_health,
        "exact_mutation_count": sum(
            report["modified"] == ["probe.txt"]
            and report["reconciliation_cause"] == "event_hints"
            for report in mutation_reports
        ),
        "orphan_process_ids": [
            pid
            for pid, process in zip(process_ids, processes, strict=True)
            if process.poll() is None
        ],
        "mutation_reports": mutation_reports,
    }


def run_crash_restart_soak(
    *,
    binary_path: Path,
    scratch_root: Path,
    restart_iterations: int = 30,
    fixture_file_count: int = 64,
    request_timeout_s: float = 5.0,
) -> dict[str, Any]:
    if restart_iterations < 1:
        raise ValueError("restart_iterations must be at least one")
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    baseline_threads = _observation_reader_threads()
    with TemporaryDirectory(prefix="aware-fs-restart-soak-", dir=scratch) as raw_root:
        fixture_root = Path(raw_root)
        root = fixture_root / "workspace"
        _build_flat_file_fixture(root, fixture_file_count)
        cache = fixture_root / "state.cache"
        service = NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
            request_timeout_s=request_timeout_s,
        )
        process_ids: list[int] = []
        processes: list[Any] = []
        samples: list[dict[str, Any]] = []
        try:
            service.initialize_observation("seed")
            service.wait_for_watcher_ready(request_id="seed-watcher-ready")
            expected_snapshot = dict(service.snapshot())
            expected_digest = str(expected_snapshot["inventory_digest"])
            expected_generation = int(service.poll("seed-idle")["to_generation"])
            for index in range(restart_iterations):
                killed_pid = service.process_id
                process_ids.append(killed_pid)
                processes.append(service._process)
                service.terminate_immediately()
                service.close()
                started = time.perf_counter()
                service = NativeObservationService(
                    binary_path=binary_path,
                    workspace_root=root,
                    cache_path=cache,
                    request_timeout_s=request_timeout_s,
                )
                service.ping()
                restarted = dict(service.initialize_observation(f"restart-{index}"))
                service.wait_for_watcher_ready(
                    request_id=f"restart-{index}-watcher-ready"
                )
                duration_s = time.perf_counter() - started
                samples.append(
                    {
                        "index": index,
                        "duration_s": duration_s,
                        "cache_start_state": restarted["cache_start_state"],
                        "snapshot_digest_stable": restarted["snapshot_digest"]
                        == expected_digest,
                        "generation_stable": int(restarted["to_generation"])
                        == expected_generation,
                        "watcher_active": service.health()["watcher"]["state"]
                        == "active",
                    }
                )
            process_ids.append(service.process_id)
            processes.append(service._process)
        finally:
            service.close()
        _wait_for_process_exit(processes)
    time.sleep(0.05)
    durations = sorted(float(sample["duration_s"]) for sample in samples)
    return {
        "restart_sample_count": len(samples),
        "success_count": sum(
            sample["cache_start_state"] == "loaded"
            and sample["snapshot_digest_stable"]
            and sample["generation_stable"]
            and sample["watcher_active"]
            for sample in samples
        ),
        "duration_s": _duration_summary(durations),
        "orphan_process_ids": [
            pid
            for pid, process in zip(process_ids, processes, strict=True)
            if process.poll() is None
        ],
        "leaked_reader_threads": sorted(
            _observation_reader_threads().difference(baseline_threads)
        ),
        "samples": samples,
    }


def run_reconciliation_only_recovery(
    *,
    binary_path: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix="aware-fs-reconciliation-only-", dir=scratch
    ) as raw_root:
        fixture_root = Path(raw_root)
        root = fixture_root / "workspace"
        root.mkdir()
        source = root / "source.txt"
        source.write_text("before\n", encoding="utf-8")
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=fixture_root / "state.cache",
            reconciliation_interval_s=3600.0,
            watch_mode=ObservationWatchMode.RECONCILIATION_ONLY,
        ) as service:
            service.initialize_observation("startup")
            health = dict(service.health()["watcher"])
            unchanged = dict(service.poll("unchanged"))
            source.write_text("after-with-new-size\n", encoding="utf-8")
            changed = dict(service.poll("changed"))
    return {
        "health": health,
        "unchanged_exact": unchanged["status"] == "exact"
        and unchanged["reconciliation_cause"] == "watch_unavailable"
        and int(unchanged["scan_ns"]) > 0,
        "changed_exact": changed["modified"] == ["source.txt"]
        and changed["reconciliation_cause"] == "watch_unavailable",
    }


def run_cache_fault_recovery(
    *,
    binary_path: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="aware-fs-cache-fault-", dir=scratch) as raw_root:
        fixture_root = Path(raw_root)
        root = fixture_root / "workspace"
        root.mkdir()
        (root / "source.txt").write_text("source\n", encoding="utf-8")
        cache = fixture_root / "state.cache"
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
            watch_mode=ObservationWatchMode.RECONCILIATION_ONLY,
        ) as service:
            seed = dict(service.observe("seed"))
        stale_temp = cache.with_name(f".{cache.name}.999999.123456.tmp")
        stale_temp.write_bytes(b"interrupted replacement")
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
            watch_mode=ObservationWatchMode.RECONCILIATION_ONLY,
        ) as service:
            interrupted = dict(service.observe("interrupted-temp"))
        raw_cache = cache.read_bytes()
        cache.write_bytes(raw_cache[:16])
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
            watch_mode=ObservationWatchMode.RECONCILIATION_ONLY,
        ) as service:
            truncated = dict(service.observe("truncated-cache"))
    return {
        "interrupted_temp": {
            "cache_start_state": interrupted["cache_start_state"],
            "stale_cache_temp_files_removed": interrupted[
                "stale_cache_temp_files_removed"
            ],
            "temp_removed": not stale_temp.exists(),
            "snapshot_digest_stable": interrupted["snapshot_digest"]
            == seed["snapshot_digest"],
        },
        "truncated_cache": {
            "cache_start_state": truncated["cache_start_state"],
            "cache_written": truncated["cache_written"],
            "snapshot_digest_stable": truncated["snapshot_digest"]
            == seed["snapshot_digest"],
        },
    }


def run_journal_tail_recovery(
    *,
    binary_path: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="aware-fs-journal-tail-", dir=scratch) as raw_root:
        fixture_root = Path(raw_root)
        root = fixture_root / "workspace"
        root.mkdir()
        source = root / "source.txt"
        source.write_text("base\n", encoding="utf-8")
        cache = fixture_root / "state.cache"
        journal = Path(f"{cache}.journal")
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
            reconciliation_interval_s=3600.0,
        ) as service:
            service.initialize_observation("journal-tail-startup")
            service.wait_for_watcher_ready(request_id="journal-tail-watcher-ready")
            source.write_text("first-acknowledged-state\n", encoding="utf-8")
            first = _poll_repository_mutation(service, 0)
            first_stat = source.stat()
            first_journal_size = journal.stat().st_size
            source.write_text(
                "second-acknowledged-state-with-new-size\n", encoding="utf-8"
            )
            second = _poll_repository_mutation(service, 1)
            complete_journal_size = journal.stat().st_size

        torn_journal_size = complete_journal_size - 7
        with journal.open("r+b") as stream:
            stream.truncate(torn_journal_size)
        source.write_text("first-acknowledged-state\n", encoding="utf-8")
        os.utime(source, ns=(first_stat.st_atime_ns, first_stat.st_mtime_ns))

        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
        ) as restarted:
            recovered = dict(restarted.observe("journal-tail-recovery"))
            watcher = dict(restarted.health()["watcher"])

        expected_removed_bytes = torn_journal_size - first_journal_size
        passed = (
            first["persistence_mode"] == "journal_append"
            and int(first["journal_frame_count"]) == 1
            and second["persistence_mode"] == "journal_append"
            and int(second["journal_frame_count"]) == 2
            and recovered["cache_start_state"] == "loaded"
            and recovered["cache_written"] is False
            and int(recovered["from_generation"]) == int(first["to_generation"])
            and int(recovered["to_generation"]) == int(first["to_generation"])
            and int(recovered["journal_frame_count"]) == 1
            and int(recovered["journal_tail_bytes_removed"]) == expected_removed_bytes
            and recovered["snapshot_digest"] == first["snapshot_digest"]
            and journal.stat().st_size == first_journal_size
        )
        return {
            "passed": passed,
            "first_generation": int(first["to_generation"]),
            "second_generation": int(second["to_generation"]),
            "recovered_generation": int(recovered["to_generation"]),
            "first_journal_bytes": first_journal_size,
            "complete_journal_bytes": complete_journal_size,
            "torn_journal_bytes": torn_journal_size,
            "recovered_journal_bytes": journal.stat().st_size,
            "tail_bytes_removed": int(recovered["journal_tail_bytes_removed"]),
            "expected_tail_bytes_removed": expected_removed_bytes,
            "digest_stable": recovered["snapshot_digest"] == first["snapshot_digest"],
            "digest_backend_kind": recovered["digest_backend_kind"],
            "watcher": watcher,
        }


def run_journal_checkpoint_recovery(
    *,
    binary_path: Path,
    scratch_root: Path,
) -> dict[str, Any]:
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="aware-fs-journal-checkpoint-", dir=scratch) as raw:
        fixture_root = Path(raw)
        root = fixture_root / "workspace"
        root.mkdir()
        source = root / "source.txt"
        source.write_text("base\n", encoding="utf-8")
        cache = fixture_root / "state.cache"
        journal = Path(f"{cache}.journal")
        samples: list[dict[str, Any]] = []
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
            reconciliation_interval_s=3600.0,
        ) as service:
            service.initialize_observation("journal-checkpoint-startup")
            service.wait_for_watcher_ready(
                request_id="journal-checkpoint-watcher-ready"
            )
            for index in range(128):
                started = time.perf_counter()
                source.write_text(
                    f"checkpoint-{index}-{'x' * (index + 1)}\n",
                    encoding="utf-8",
                )
                report = _poll_repository_mutation(service, 1000 + index)
                samples.append(
                    {
                        "index": index,
                        "duration_s": time.perf_counter() - started,
                        "persistence_mode": report["persistence_mode"],
                        "checkpoint_written": bool(report["checkpoint_written"]),
                        "journal_frame_count": int(report["journal_frame_count"]),
                        "journal_bytes": int(report["journal_bytes"]),
                        "generation": int(report["to_generation"]),
                        "snapshot_digest": report["snapshot_digest"],
                        "modified_exact": report["modified"] == ["source.txt"],
                    }
                )
            watcher = dict(service.health()["watcher"])
        final = samples[-1]
        journal_bytes_after_checkpoint = journal.stat().st_size

        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=cache,
        ) as restarted:
            recovered = dict(restarted.observe("journal-checkpoint-restart"))

        durations = sorted(float(sample["duration_s"]) for sample in samples)
        append_count = sum(
            sample["persistence_mode"] == "journal_append"
            and sample["checkpoint_written"] is False
            for sample in samples
        )
        checkpoint_samples = [
            sample for sample in samples if sample["checkpoint_written"]
        ]
        passed = (
            len(samples) == 128
            and all(sample["modified_exact"] for sample in samples)
            and append_count == 127
            and len(checkpoint_samples) == 1
            and checkpoint_samples[0]["index"] == 127
            and checkpoint_samples[0]["persistence_mode"] == "journal_checkpoint"
            and final["journal_frame_count"] == 0
            and final["journal_bytes"] == 0
            and journal_bytes_after_checkpoint == 0
            and recovered["cache_start_state"] == "loaded"
            and recovered["cache_written"] is False
            and int(recovered["from_generation"]) == final["generation"]
            and int(recovered["to_generation"]) == final["generation"]
            and recovered["snapshot_digest"] == final["snapshot_digest"]
            and int(recovered["journal_frame_count"]) == 0
            and int(recovered["journal_bytes"]) == 0
            and watcher["state"] == "active"
        )
        return {
            "passed": passed,
            "mutation_sample_count": len(samples),
            "journal_append_count": append_count,
            "checkpoint_count": len(checkpoint_samples),
            "checkpoint_sample_indices": [
                int(sample["index"]) for sample in checkpoint_samples
            ],
            "duration_s": _duration_summary(durations),
            "maximum_journal_frame_count": max(
                int(sample["journal_frame_count"]) for sample in samples
            ),
            "maximum_journal_bytes": max(
                int(sample["journal_bytes"]) for sample in samples
            ),
            "journal_bytes_after_checkpoint": journal_bytes_after_checkpoint,
            "checkpoint_generation": int(final["generation"]),
            "recovered_generation": int(recovered["to_generation"]),
            "digest_stable": recovered["snapshot_digest"] == final["snapshot_digest"],
            "digest_backend_kind": recovered["digest_backend_kind"],
            "watcher": watcher,
        }


def run_portable_mutation_recovery(
    *,
    binary_path: Path,
    scratch_root: Path,
    burst_file_count: int = 64,
) -> dict[str, Any]:
    if burst_file_count < 1:
        raise ValueError("burst_file_count must be at least one")
    scratch = scratch_root.expanduser().resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="aware-fs-portable-mutations-", dir=scratch) as raw:
        fixture_root = Path(raw)
        root = fixture_root / "workspace"
        root.mkdir()
        source = root / "source.txt"
        source.write_text("before\n", encoding="utf-8")
        with NativeObservationService(
            binary_path=binary_path,
            workspace_root=root,
            cache_path=fixture_root / "state.cache",
            reconciliation_interval_s=3600.0,
        ) as service:
            service.initialize_observation("portable-startup")
            service.wait_for_watcher_ready(request_id="portable-watcher-ready")
            steps: list[dict[str, Any]] = []

            created = root / "created.txt"
            created.write_text("created\n", encoding="utf-8")
            steps.append(
                _await_exact_paths(
                    service,
                    label="create",
                    expected_paths={"created.txt", "source.txt"},
                    expected_added={"created.txt"},
                )
            )

            source.write_text("updated-with-new-size\n", encoding="utf-8")
            steps.append(
                _await_exact_paths(
                    service,
                    label="update",
                    expected_paths={"created.txt", "source.txt"},
                    expected_modified={"source.txt"},
                )
            )

            renamed = root / "renamed.txt"
            source.rename(renamed)
            steps.append(
                _await_exact_paths(
                    service,
                    label="rename",
                    expected_paths={"created.txt", "renamed.txt"},
                    expected_added={"renamed.txt"},
                    expected_deleted={"source.txt"},
                )
            )

            replacement = root / "replacement.tmp"
            replacement.write_text(
                "atomic-replacement-with-new-size\n", encoding="utf-8"
            )
            os.replace(replacement, renamed)
            steps.append(
                _await_exact_paths(
                    service,
                    label="atomic_replace",
                    expected_paths={"created.txt", "renamed.txt"},
                    expected_modified={"renamed.txt"},
                )
            )

            created.unlink()
            steps.append(
                _await_exact_paths(
                    service,
                    label="delete",
                    expected_paths={"renamed.txt"},
                    expected_deleted={"created.txt"},
                )
            )

            burst_paths = {
                f"burst-{index:04d}.txt" for index in range(burst_file_count)
            }
            for path in burst_paths:
                (root / path).write_text(f"{path}\n", encoding="utf-8")
            steps.append(
                _await_exact_paths(
                    service,
                    label="burst_create",
                    expected_paths={"renamed.txt", *burst_paths},
                    expected_added=burst_paths,
                )
            )
            watcher = dict(service.health()["watcher"])
    return {
        "burst_file_count": burst_file_count,
        "watcher": watcher,
        "steps": steps,
        "passed": all(step["passed"] for step in steps)
        and watcher["state"] == "active",
    }


def run_portable_resilience_benchmark(
    *,
    binary_path: Path,
    package_manifest_path: Path,
    scratch_root: Path,
    repository_count: int = 4,
    directories_per_repository: int = 256,
    restart_iterations: int = 30,
    burst_file_count: int = 64,
    source_revision: str,
    evidence_run_id: str,
) -> dict[str, Any]:
    evidence_coordinate = _require_evidence_coordinate(
        source_revision=source_revision,
        evidence_run_id=evidence_run_id,
    )
    package_manifest = json.loads(
        package_manifest_path.expanduser().resolve().read_text(encoding="utf-8")
    )
    if not isinstance(package_manifest, dict):
        raise NativeObservationServiceError("Native package manifest must be an object")
    binary = binary_path.expanduser().resolve()
    binary_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    multi_repository = run_multi_repository_capacity(
        binary_path=binary,
        scratch_root=scratch_root,
        repository_count=repository_count,
        directories_per_repository=directories_per_repository,
    )
    mutations = run_portable_mutation_recovery(
        binary_path=binary,
        scratch_root=scratch_root,
        burst_file_count=burst_file_count,
    )
    crash_restart = run_crash_restart_soak(
        binary_path=binary,
        scratch_root=scratch_root,
        restart_iterations=restart_iterations,
    )
    reconciliation_only = run_reconciliation_only_recovery(
        binary_path=binary,
        scratch_root=scratch_root,
    )
    cache_faults = run_cache_fault_recovery(
        binary_path=binary,
        scratch_root=scratch_root,
    )
    journal_tail = run_journal_tail_recovery(
        binary_path=binary,
        scratch_root=scratch_root,
    )
    journal_checkpoint = run_journal_checkpoint_recovery(
        binary_path=binary,
        scratch_root=scratch_root,
    )
    platform_key = _platform_key()
    machine = platform.machine()
    target_triple = str(package_manifest.get("target_triple") or "")
    supported_platform_class = resolve_supported_platform_class(
        platform_key=platform_key,
        sys_platform=sys.platform,
        os_name=os.name,
        machine=machine,
        target_triple=target_triple,
    )
    linux_watch_budget = (
        multi_repository["watch_ratio"] is not None
        and multi_repository["watch_ratio"] <= 0.30
        if platform_key == "linux"
        else True
    )
    checks = {
        "supported_platform": supported_platform_class is not None,
        "package_coordinate": package_manifest.get("binary_sha256") == binary_sha256
        and package_manifest.get("runtime_verification", {}).get("passed") is True,
        "evidence_coordinate": package_manifest.get("evidence_coordinate")
        == evidence_coordinate,
        "four_distinct_roots": multi_repository["repository_count"] >= 4,
        "multi_root_exact": multi_repository["exact_mutation_count"]
        == multi_repository["repository_count"],
        "multi_root_watchers_active": all(
            health["state"] == "active" for health in multi_repository["watcher_health"]
        ),
        "platform_watch_budget": linux_watch_budget,
        "multi_root_no_orphans": not multi_repository["orphan_process_ids"],
        "portable_mutations_exact": mutations["passed"],
        "restart_distribution": crash_restart["restart_sample_count"] >= 30,
        "restart_exact": crash_restart["success_count"]
        == crash_restart["restart_sample_count"],
        "restart_p99": crash_restart["duration_s"]["p99"] <= 2.0,
        "restart_no_orphans": not crash_restart["orphan_process_ids"],
        "restart_no_reader_leaks": not crash_restart["leaked_reader_threads"],
        "reconciliation_only_exact": reconciliation_only["unchanged_exact"]
        and reconciliation_only["changed_exact"]
        and reconciliation_only["health"]["state"] == "reconciliation_only",
        "interrupted_cache_recovered": cache_faults["interrupted_temp"][
            "cache_start_state"
        ]
        == "loaded"
        and cache_faults["interrupted_temp"]["temp_removed"]
        and cache_faults["interrupted_temp"]["snapshot_digest_stable"],
        "truncated_cache_rebuilt": cache_faults["truncated_cache"]["cache_start_state"]
        == "corrupt"
        and cache_faults["truncated_cache"]["cache_written"]
        and cache_faults["truncated_cache"]["snapshot_digest_stable"],
        "journal_torn_tail_recovered": journal_tail["passed"],
        "journal_checkpoint_recovered": journal_checkpoint["passed"],
    }
    return {
        "schema": PLATFORM_RECEIPT_SCHEMA,
        "created_at": datetime.now(UTC).isoformat(),
        "platform": {
            "key": platform_key,
            "sys_platform": sys.platform,
            "os_name": os.name,
            "machine": machine,
            "architecture_class": architecture_class(machine),
            "python": platform.python_version(),
        },
        "supported_platform_class": (
            supported_platform_class.as_receipt()
            if supported_platform_class is not None
            else None
        ),
        "artifact": {
            "target_triple": target_triple,
            "binary_name": binary.name,
            "binary_sha256": binary_sha256,
            "binary_bytes": binary.stat().st_size,
            "service_protocol": package_manifest.get("service_protocol"),
        },
        "evidence_coordinate": evidence_coordinate,
        "watcher_backend": mutations["watcher"].get("backend"),
        "multi_repository": multi_repository,
        "portable_mutations": mutations,
        "crash_restart": crash_restart,
        "reconciliation_only": reconciliation_only,
        "cache_faults": cache_faults,
        "journal_tail": journal_tail,
        "journal_checkpoint": journal_checkpoint,
        "platform_gate": {
            "checks": checks,
            "passed": all(checks.values()),
            "production_route_authorized": False,
            "platforms_authorized": [],
        },
        "production_gate_passed": False,
    }


def run_linux_resilience_benchmark(
    *,
    binary_path: Path,
    scratch_root: Path,
    repository_count: int = 4,
    directories_per_repository: int = 4096,
    restart_iterations: int = 30,
) -> dict[str, Any]:
    multi_repository = run_multi_repository_capacity(
        binary_path=binary_path,
        scratch_root=scratch_root,
        repository_count=repository_count,
        directories_per_repository=directories_per_repository,
    )
    crash_restart = run_crash_restart_soak(
        binary_path=binary_path,
        scratch_root=scratch_root,
        restart_iterations=restart_iterations,
    )
    reconciliation_only = run_reconciliation_only_recovery(
        binary_path=binary_path,
        scratch_root=scratch_root,
    )
    cache_faults = run_cache_fault_recovery(
        binary_path=binary_path,
        scratch_root=scratch_root,
    )
    journal_tail = run_journal_tail_recovery(
        binary_path=binary_path,
        scratch_root=scratch_root,
    )
    journal_checkpoint = run_journal_checkpoint_recovery(
        binary_path=binary_path,
        scratch_root=scratch_root,
    )
    checks = {
        "linux_host": os.name == "posix" and Path("/proc").is_dir(),
        "four_distinct_roots": multi_repository["repository_count"] >= 4,
        "multi_root_exact": multi_repository["exact_mutation_count"]
        == multi_repository["repository_count"],
        "watch_budget": multi_repository["watch_ratio"] is not None
        and multi_repository["watch_ratio"] <= 0.30,
        "multi_root_no_orphans": not multi_repository["orphan_process_ids"],
        "restart_distribution": crash_restart["restart_sample_count"] >= 30,
        "restart_exact": crash_restart["success_count"]
        == crash_restart["restart_sample_count"],
        "restart_p99": crash_restart["duration_s"]["p99"] <= 1.0,
        "restart_no_orphans": not crash_restart["orphan_process_ids"],
        "restart_no_reader_leaks": not crash_restart["leaked_reader_threads"],
        "reconciliation_only_exact": reconciliation_only["unchanged_exact"]
        and reconciliation_only["changed_exact"]
        and reconciliation_only["health"]["state"] == "reconciliation_only"
        and reconciliation_only["health"]["watched_directory_count"] == 0,
        "interrupted_cache_recovered": cache_faults["interrupted_temp"][
            "cache_start_state"
        ]
        == "loaded"
        and cache_faults["interrupted_temp"]["stale_cache_temp_files_removed"] == 1
        and cache_faults["interrupted_temp"]["temp_removed"]
        and cache_faults["interrupted_temp"]["snapshot_digest_stable"],
        "truncated_cache_rebuilt": cache_faults["truncated_cache"]["cache_start_state"]
        == "corrupt"
        and cache_faults["truncated_cache"]["cache_written"]
        and cache_faults["truncated_cache"]["snapshot_digest_stable"],
        "journal_torn_tail_recovered": journal_tail["passed"],
        "journal_checkpoint_recovered": journal_checkpoint["passed"],
    }
    return {
        "schema": OBSERVATION_RESILIENCE_SCHEMA,
        "created_at": datetime.now(UTC).isoformat(),
        "binary_path": binary_path.expanduser().resolve().as_posix(),
        "multi_repository": multi_repository,
        "crash_restart": crash_restart,
        "reconciliation_only": reconciliation_only,
        "cache_faults": cache_faults,
        "journal_tail": journal_tail,
        "journal_checkpoint": journal_checkpoint,
        "linux_resilience_gate": {
            "checks": checks,
            "passed": all(checks.values()),
            "production_route_authorized": False,
            "platforms_authorized": ["linux_shadow"] if all(checks.values()) else [],
        },
        "production_gate_passed": False,
    }


def _await_exact_paths(
    service: NativeObservationService,
    *,
    label: str,
    expected_paths: set[str],
    expected_added: set[str] | None = None,
    expected_modified: set[str] | None = None,
    expected_deleted: set[str] | None = None,
) -> dict[str, Any]:
    expected_added = expected_added or set()
    expected_modified = expected_modified or set()
    expected_deleted = expected_deleted or set()
    observed_added: set[str] = set()
    observed_modified: set[str] = set()
    observed_deleted: set[str] = set()
    event_reconciliations = 0
    attempts = 0
    started = time.perf_counter()
    deadline = time.monotonic() + service.request_timeout_s
    while True:
        report = dict(service.poll(f"portable-{label}-{attempts}"))
        cause = report["reconciliation_cause"]
        if str(cause).startswith("event_hints"):
            event_reconciliations += 1
            observed_added.update(str(path) for path in report["added"])
            observed_modified.update(str(path) for path in report["modified"])
            observed_deleted.update(str(path) for path in report["deleted"])
            snapshot = service.snapshot()
            raw_entries = snapshot.get("entries")
            if not isinstance(raw_entries, list):
                raise NativeObservationServiceError(
                    "Native snapshot entries are unavailable during mutation recovery"
                )
            observed_paths = {
                str(entry["path"])
                for entry in raw_entries
                if isinstance(entry, dict) and "path" in entry
            }
            if observed_paths == expected_paths:
                break
        elif report["observation_mode"] != "maintained_no_hint":
            raise NativeObservationServiceError(
                f"Portable mutation {label} returned unexpected cause {cause}"
            )
        if time.monotonic() >= deadline:
            raise NativeObservationServiceError(
                f"Portable mutation {label} did not converge before its deadline"
            )
        attempts += 1
        time.sleep(0.005)
    passed = (
        expected_added <= observed_added
        and expected_modified <= observed_modified
        and expected_deleted <= observed_deleted
    )
    return {
        "label": label,
        "passed": passed,
        "duration_s": time.perf_counter() - started,
        "attempts": attempts + 1,
        "event_reconciliations": event_reconciliations,
        "expected_paths": sorted(expected_paths),
        "observed_added": sorted(observed_added),
        "observed_modified": sorted(observed_modified),
        "observed_deleted": sorted(observed_deleted),
    }


def _platform_key() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform in {"win32", "cygwin"}:
        return "windows"
    return "unsupported"


def _require_evidence_coordinate(
    *,
    source_revision: str,
    evidence_run_id: str,
) -> dict[str, str]:
    revision = source_revision.strip().lower()
    run_id = evidence_run_id.strip()
    if len(revision) not in {40, 64} or any(
        character not in "0123456789abcdef" for character in revision
    ):
        raise ValueError("source_revision must be a 40- or 64-character hex digest")
    if (
        not run_id
        or len(run_id.encode("utf-8")) > 128
        or any(character in run_id for character in "\r\n")
    ):
        raise ValueError("evidence_run_id must contain 1..128 bytes without newlines")
    return {"source_revision": revision, "run_id": run_id}


def _build_directory_fixture(root: Path, count: int) -> None:
    root.mkdir(parents=True)
    (root / "probe.txt").write_text("before\n", encoding="utf-8")
    for index in range(count):
        directory = root / "tree" / f"{index // 256:04d}" / f"{index % 256:04d}"
        directory.mkdir(parents=True)
        (directory / "source.txt").write_text(f"source-{index}\n", encoding="utf-8")


def _build_flat_file_fixture(root: Path, count: int) -> None:
    root.mkdir(parents=True)
    for index in range(count):
        (root / f"source-{index:04d}.txt").write_text(
            f"source-{index}\n", encoding="utf-8"
        )


def _poll_repository_mutation(
    service: NativeObservationService,
    index: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + service.request_timeout_s
    attempt = 0
    while True:
        report = dict(service.poll(f"repository-{index}-mutation-{attempt}"))
        if report["reconciliation_cause"] == "event_hints":
            return report
        if report["observation_mode"] != "maintained_no_hint":
            raise RuntimeError(
                f"repository {index} returned unexpected cause "
                f"{report['reconciliation_cause']}"
            )
        if time.monotonic() >= deadline:
            raise RuntimeError(f"repository {index} mutation hint timed out")
        attempt += 1
        time.sleep(0.001)


def _observation_reader_threads() -> set[str]:
    return {
        thread.name
        for thread in threading.enumerate()
        if thread.name.startswith("aware-fs-observation-")
    }


def _wait_for_process_exit(processes: list[Any]) -> None:
    deadline = time.monotonic() + 3.0
    while any(process.poll() is None for process in processes):
        if time.monotonic() >= deadline:
            return
        time.sleep(0.01)


def _linux_inotify_max_user_watches() -> int | None:
    try:
        return int(
            Path("/proc/sys/fs/inotify/max_user_watches")
            .read_text(encoding="utf-8")
            .strip()
        )
    except (OSError, ValueError):
        return None


def _duration_summary(values: list[float]) -> dict[str, float]:
    return {
        "p50": median(values),
        "p95": _nearest_rank(values, 0.95),
        "p99": _nearest_rank(values, 0.99),
        "max": max(values),
    }


def _nearest_rank(values: list[float], quantile: float) -> float:
    return values[max(0, math.ceil(quantile * len(values)) - 1)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark native observation resilience on one host platform."
    )
    parser.add_argument("--binary-path", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--repository-count", type=int, default=4)
    parser.add_argument("--directories-per-repository", type=int, default=4096)
    parser.add_argument("--restart-iterations", type=int, default=30)
    parser.add_argument("--burst-file-count", type=int, default=64)
    parser.add_argument("--gate", choices=("linux", "portable"), default="linux")
    parser.add_argument("--package-manifest", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--evidence-run-id")
    parser.add_argument("--receipt-path", type=Path)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    if args.gate == "portable":
        if args.package_manifest is None:
            parser.error("--package-manifest is required for --gate=portable")
        if args.source_revision is None or args.evidence_run_id is None:
            parser.error(
                "--source-revision and --evidence-run-id are required "
                "for --gate=portable"
            )
        receipt = run_portable_resilience_benchmark(
            binary_path=args.binary_path,
            package_manifest_path=args.package_manifest,
            scratch_root=args.scratch_root,
            repository_count=args.repository_count,
            directories_per_repository=args.directories_per_repository,
            restart_iterations=args.restart_iterations,
            burst_file_count=args.burst_file_count,
            source_revision=args.source_revision,
            evidence_run_id=args.evidence_run_id,
        )
    else:
        receipt = run_linux_resilience_benchmark(
            binary_path=args.binary_path,
            scratch_root=args.scratch_root,
            repository_count=args.repository_count,
            directories_per_repository=args.directories_per_repository,
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
