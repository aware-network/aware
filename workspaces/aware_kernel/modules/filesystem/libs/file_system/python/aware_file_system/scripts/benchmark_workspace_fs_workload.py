from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aware_file_system.scripts.benchmark_workspace_fs import (
    _benchmark_environment,
    _ensure_empty_or_missing,
    _file_system_index,
    _measure_scan,
    _resource_stats,
    _stats,
    _write_workspace_fixture,
)
from aware_file_system.workload_receipt_contract import (
    PRODUCTION_TAIL_MIN_SAMPLES,
    WORKSPACE_FS_WORKLOAD_VERSION,
    WORKLOAD_SUMMARY_KEYS,
    validate_workspace_fs_workload_receipt,
)


@dataclass(frozen=True, slots=True)
class WorkspaceFsWorkloadConfig:
    workspace_root: Path | None = None
    fixture_root: Path | None = None
    cache_dir: Path | None = None
    iterations: int = 5
    concurrency: int = 2
    packages: int = 4
    files_per_package: int = 32
    payload_bytes: int = 512
    include_cpu_pressure: bool = True
    include_contention: bool = True
    include_recovery: bool = True
    include_diagnostic_comparison: bool = True
    write_receipt: bool = False
    receipt_dir: Path | None = None


def run_workspace_fs_workload(
    config: WorkspaceFsWorkloadConfig | None = None,
) -> dict[str, Any]:
    resolved = config or WorkspaceFsWorkloadConfig()
    if resolved.iterations < 1:
        raise ValueError("Workload iterations must be at least 1.")
    if resolved.concurrency < 1:
        raise ValueError("Workload concurrency must be at least 1.")
    if resolved.workspace_root is not None and resolved.fixture_root is not None:
        raise ValueError("Use either workspace_root or fixture_root, not both.")
    if resolved.workspace_root is not None:
        return _run_real_workload(resolved)
    return _run_synthetic_workload(resolved)


def _run_real_workload(config: WorkspaceFsWorkloadConfig) -> dict[str, Any]:
    if config.workspace_root is None:
        raise ValueError("workspace_root is required for real workload mode")
    root = config.workspace_root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Workspace root is not a directory: {root}")
    if config.cache_dir is not None:
        cache_dir = config.cache_dir.expanduser().resolve()
        cache_dir.mkdir(parents=True, exist_ok=True)
        receipt = _run_real_workload_with_cache(config, root, cache_dir)
        return _maybe_write_receipt(receipt, config, cache_dir)
    with tempfile.TemporaryDirectory(prefix="aware-fs-workload-") as raw_cache:
        cache_dir = Path(raw_cache)
        receipt = _run_real_workload_with_cache(config, root, cache_dir)
        if config.write_receipt and config.receipt_dir is None:
            raise ValueError("write_receipt requires cache_dir or receipt_dir")
        return _maybe_write_receipt(receipt, config, cache_dir)


def _run_real_workload_with_cache(
    config: WorkspaceFsWorkloadConfig,
    root: Path,
    cache_dir: Path,
) -> dict[str, Any]:
    cold: list[dict[str, Any]] = []
    warm_session: list[dict[str, Any]] = []
    warm_restart: list[dict[str, Any]] = []
    for iteration in range(config.iterations):
        iteration_cache = cache_dir / "baseline" / f"iteration_{iteration}"
        _require_empty(iteration_cache)
        index = _file_system_index(root=root, cache_dir=iteration_cache)
        cold.append(
            _measure_scan(
                index=index,
                root=root,
                label="cold_clean",
                force_refresh=True,
                hash_changed_paths=False,
                iteration_index=iteration,
                cache_empty_before=True,
            )
        )
        warm_session.append(
            _measure_scan(
                index=index,
                root=root,
                label="warm_session_noop",
                force_refresh=False,
                hash_changed_paths=False,
                iteration_index=iteration,
                cache_empty_before=False,
            )
        )
        restart_index = _file_system_index(root=root, cache_dir=iteration_cache)
        warm_restart.append(
            _measure_scan(
                index=restart_index,
                root=root,
                label="warm_process_restart",
                force_refresh=False,
                hash_changed_paths=False,
                iteration_index=iteration,
                cache_empty_before=False,
            )
        )

    scenarios = [
        _scenario(
            label="cold_clean",
            workload_class="cold",
            source_mutation=False,
            cache_state="empty",
            samples=cold,
            setup={"detailed_timings": True, "independent_cache_per_sample": True},
        ),
        _scenario(
            label="warm_session_noop",
            workload_class="warm_session",
            source_mutation=False,
            cache_state="warm",
            samples=warm_session,
            setup={"same_index_generation": True},
        ),
        _scenario(
            label="warm_process_restart",
            workload_class="warm_restart",
            source_mutation=False,
            cache_state="warm",
            samples=warm_restart,
            setup={"new_index_generation": True, "persisted_cache_reused": True},
        ),
    ]

    if config.include_diagnostic_comparison:
        diagnostic_off = _independent_cold_samples(
            root=root,
            cache_root=cache_dir / "diagnostic_off",
            iterations=config.iterations,
            label="cold_detailed_timings_off",
            collect_detailed_timings=False,
        )
        scenarios.append(
            _scenario(
                label="cold_detailed_timings_off",
                workload_class="diagnostic_comparison",
                source_mutation=False,
                cache_state="empty",
                samples=diagnostic_off,
                setup={
                    "detailed_timings": False,
                    "comparison_scenario": "cold_clean",
                },
            )
        )

    if config.include_contention:
        samples, failures = _concurrent_cold_samples(
            root=root,
            cache_root=cache_dir / "contention",
            iterations=config.iterations,
            concurrency=config.concurrency,
        )
        scenarios.append(
            _scenario(
                label="concurrent_cold_isolated_cache",
                workload_class="contention",
                source_mutation=False,
                cache_state="empty",
                samples=samples,
                failures=failures,
                concurrency=config.concurrency,
                setup={
                    "benchmark_only_multiple_indices": True,
                    "production_authority_allowed": False,
                    "isolated_cache_per_worker": True,
                },
            )
        )

    if config.include_cpu_pressure:
        pressure_samples, pressure_failures = _cpu_pressure_samples(
            root=root,
            cache_root=cache_dir / "cpu_pressure",
            iterations=config.iterations,
        )
        scenarios.append(
            _scenario(
                label="cold_cpu_pressure",
                workload_class="cpu_pressure",
                source_mutation=False,
                cache_state="empty",
                samples=pressure_samples,
                failures=pressure_failures,
                setup={"pressure_workers": 1, "worker_kind": "sha256_loop"},
            )
        )

    if config.include_recovery:
        recovery_samples, recovery_failures = _corrupt_cache_recovery_samples(
            root=root,
            cache_root=cache_dir / "corrupt_recovery",
            iterations=config.iterations,
        )
        scenarios.append(
            _scenario(
                label="corrupt_cache_recovery",
                workload_class="recovery",
                source_mutation=False,
                cache_state="corrupt",
                samples=recovery_samples,
                failures=recovery_failures,
                setup={
                    "corrupted_files": ["file_index.json", "directory_cache.msgpack"],
                    "expected_action": "observable_rebuild",
                },
            )
        )

    return _receipt(
        mode="real_workspace_readonly",
        root=root,
        cache_dir=cache_dir,
        scenarios=scenarios,
        source_mutation=False,
    )


def _run_synthetic_workload(config: WorkspaceFsWorkloadConfig) -> dict[str, Any]:
    if config.fixture_root is not None:
        root = config.fixture_root.expanduser().resolve()
        _ensure_empty_or_missing(root)
        root.mkdir(parents=True, exist_ok=True)
        cache_dir = (
            config.cache_dir.expanduser().resolve()
            if config.cache_dir is not None
            else root.parent / f"{root.name}-cache"
        )
        receipt = _run_synthetic_mutation_sequence(config, root, cache_dir)
        return _maybe_write_receipt(receipt, config, cache_dir)
    with tempfile.TemporaryDirectory(prefix="aware-fs-workload-fixture-") as raw_root:
        root = Path(raw_root)
        with tempfile.TemporaryDirectory(
            prefix="aware-fs-workload-cache-"
        ) as raw_cache:
            cache_dir = Path(raw_cache)
            receipt = _run_synthetic_mutation_sequence(config, root, cache_dir)
            if config.write_receipt and config.receipt_dir is None:
                raise ValueError("write_receipt requires cache_dir or receipt_dir")
            return _maybe_write_receipt(receipt, config, cache_dir)


def _run_synthetic_mutation_sequence(
    config: WorkspaceFsWorkloadConfig,
    root: Path,
    cache_dir: Path,
) -> dict[str, Any]:
    fixture = _write_workspace_fixture(
        root=root,
        packages=config.packages,
        files_per_package=config.files_per_package,
        payload_bytes=config.payload_bytes,
    )
    nested = root / "nested_policy"
    nested.mkdir(parents=True, exist_ok=True)
    ignore_path = nested / ".gitignore"
    ignored_path = nested / "candidate.tmp"
    ignore_path.write_text("*.tmp\n", encoding="utf-8")
    ignored_path.write_text("candidate\n", encoding="utf-8")

    index = _file_system_index(root=root, cache_dir=cache_dir / "mutation")
    index.scan_relative_metadata(force_refresh=True)
    scenarios: list[dict[str, Any]] = []
    created = root / "docs" / "workload-created.aware"
    created.parent.mkdir(parents=True, exist_ok=True)
    created.write_text("created\n", encoding="utf-8")
    scenarios.append(_mutation_scenario(index, root, "create_path", 0))

    edit_target = root / str(fixture["edit_target"])
    edit_target.write_text("updated workload payload\n", encoding="utf-8")
    os.utime(edit_target, None)
    scenarios.append(_mutation_scenario(index, root, "update_path", 0))

    renamed = created.with_name("workload-renamed.aware")
    created.rename(renamed)
    scenarios.append(_mutation_scenario(index, root, "rename_path", 0))

    renamed.unlink()
    scenarios.append(_mutation_scenario(index, root, "delete_path", 0))

    ignore_path.write_text("# admitted now\n", encoding="utf-8")
    os.utime(ignore_path, None)
    scenarios.append(_mutation_scenario(index, root, "ignore_policy_admit", 0))

    ignore_path.write_text("*.tmp\n", encoding="utf-8")
    os.utime(ignore_path, None)
    scenarios.append(_mutation_scenario(index, root, "ignore_policy_exclude", 0))

    if config.include_recovery:
        recovery_samples, recovery_failures = _corrupt_cache_recovery_samples(
            root=root,
            cache_root=cache_dir / "synthetic_recovery",
            iterations=max(1, min(config.iterations, 3)),
        )
        scenarios.append(
            _scenario(
                label="corrupt_cache_recovery",
                workload_class="recovery",
                source_mutation=False,
                cache_state="corrupt",
                samples=recovery_samples,
                failures=recovery_failures,
                setup={"expected_action": "observable_rebuild"},
            )
        )

    receipt = _receipt(
        mode="synthetic_mutating",
        root=root,
        cache_dir=cache_dir,
        scenarios=scenarios,
        source_mutation=True,
    )
    return receipt


def _mutation_scenario(
    index: Any,
    root: Path,
    label: str,
    iteration_index: int,
) -> dict[str, Any]:
    index.invalidate_cache()
    sample = _measure_scan(
        index=index,
        root=root,
        label=label,
        force_refresh=False,
        hash_changed_paths=True,
        iteration_index=iteration_index,
        cache_empty_before=False,
    )
    return _scenario(
        label=label,
        workload_class="mutation",
        source_mutation=True,
        cache_state="warm",
        samples=[sample],
        setup={"operation": label},
    )


def _independent_cold_samples(
    *,
    root: Path,
    cache_root: Path,
    iterations: int,
    label: str,
    collect_detailed_timings: bool,
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for iteration in range(iterations):
        sample_cache = cache_root / f"iteration_{iteration}"
        _require_empty(sample_cache)
        index = _file_system_index(
            root=root,
            cache_dir=sample_cache,
            collect_detailed_timings=collect_detailed_timings,
        )
        samples.append(
            _measure_scan(
                index=index,
                root=root,
                label=label,
                force_refresh=True,
                hash_changed_paths=False,
                iteration_index=iteration,
                cache_empty_before=True,
            )
        )
    return samples


def _concurrent_cold_samples(
    *,
    root: Path,
    cache_root: Path,
    iterations: int,
    concurrency: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    samples: list[dict[str, Any]] = []
    failures: list[str] = []
    jobs = iterations * concurrency

    def run_one(job_index: int) -> dict[str, Any]:
        sample_cache = cache_root / f"job_{job_index}"
        _require_empty(sample_cache)
        index = _file_system_index(root=root, cache_dir=sample_cache)
        return _measure_scan(
            index=index,
            root=root,
            label="concurrent_cold_isolated_cache",
            force_refresh=True,
            hash_changed_paths=False,
            iteration_index=job_index,
            cache_empty_before=True,
        )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(run_one, index): index for index in range(jobs)}
        for future in as_completed(futures):
            try:
                samples.append(future.result())
            except Exception as exc:
                failures.append(f"job {futures[future]}: {type(exc).__name__}: {exc}")
    samples.sort(key=lambda sample: sample["iteration_index"])
    for index, sample in enumerate(samples):
        sample["iteration_index"] = index
    return samples, failures


def _cpu_pressure_samples(
    *,
    root: Path,
    cache_root: Path,
    iterations: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    samples: list[dict[str, Any]] = []
    failures: list[str] = []
    for iteration in range(iterations):
        stop_event = multiprocessing.Event()
        process = multiprocessing.Process(
            target=_cpu_pressure_worker,
            args=(stop_event,),
            daemon=True,
        )
        process.start()
        try:
            sample_cache = cache_root / f"iteration_{iteration}"
            _require_empty(sample_cache)
            index = _file_system_index(root=root, cache_dir=sample_cache)
            samples.append(
                _measure_scan(
                    index=index,
                    root=root,
                    label="cold_cpu_pressure",
                    force_refresh=True,
                    hash_changed_paths=False,
                    iteration_index=iteration,
                    cache_empty_before=True,
                )
            )
        except Exception as exc:
            failures.append(f"iteration {iteration}: {type(exc).__name__}: {exc}")
        finally:
            stop_event.set()
            process.join(timeout=5)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
    return samples, failures


def _cpu_pressure_worker(stop_event: Any) -> None:
    payload = b"aware-file-system-cpu-pressure" * 4096
    while not stop_event.is_set():
        payload = hashlib.sha256(payload).digest() * 4096


def _corrupt_cache_recovery_samples(
    *,
    root: Path,
    cache_root: Path,
    iterations: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    samples: list[dict[str, Any]] = []
    failures: list[str] = []
    for iteration in range(iterations):
        sample_cache = cache_root / f"iteration_{iteration}"
        _require_empty(sample_cache)
        seed = _file_system_index(root=root, cache_dir=sample_cache)
        seed.scan_relative_metadata(force_refresh=True)
        (sample_cache / "file_index.json").write_text("{broken", encoding="utf-8")
        (sample_cache / "directory_cache.msgpack").write_bytes(b"broken-msgpack")
        try:
            recovered = _file_system_index(root=root, cache_dir=sample_cache)
            samples.append(
                _measure_scan(
                    index=recovered,
                    root=root,
                    label="corrupt_cache_recovery",
                    force_refresh=False,
                    hash_changed_paths=False,
                    iteration_index=iteration,
                    cache_empty_before=False,
                )
            )
        except Exception as exc:
            failures.append(f"iteration {iteration}: {type(exc).__name__}: {exc}")
    return samples, failures


def _scenario(
    *,
    label: str,
    workload_class: str,
    source_mutation: bool,
    cache_state: str,
    samples: list[dict[str, Any]],
    setup: dict[str, Any],
    failures: list[str] | None = None,
    concurrency: int = 1,
) -> dict[str, Any]:
    actual_failures = failures or []
    inventory_digests = sorted({sample["inventory_digest"] for sample in samples})
    return {
        "label": label,
        "workload_class": workload_class,
        "source_mutation": source_mutation,
        "cache_state": cache_state,
        "concurrency": concurrency,
        "setup": setup,
        "sample_count": len(samples) + len(actual_failures),
        "success_count": len(samples),
        "failure_count": len(actual_failures),
        "failures": actual_failures,
        "inventory_digests": inventory_digests,
        "exact_inventory_stable": bool(inventory_digests)
        and len(inventory_digests) == 1,
        "tail_claim_min_samples": PRODUCTION_TAIL_MIN_SAMPLES,
        "tail_claim_eligible": len(samples) >= PRODUCTION_TAIL_MIN_SAMPLES
        and not actual_failures
        and len(inventory_digests) == 1,
        "summary": {key: _scenario_stat(samples, key) for key in WORKLOAD_SUMMARY_KEYS},
        "samples": samples,
    }


def _scenario_stat(samples: list[dict[str, Any]], key: str) -> dict[str, Any]:
    if key in {"duration_s", "scanner_scan_time_s"}:
        return _stats(samples, key)
    return _resource_stats(samples, key)


def _receipt(
    *,
    mode: str,
    root: Path,
    cache_dir: Path,
    scenarios: list[dict[str, Any]],
    source_mutation: bool,
) -> dict[str, Any]:
    receipt = {
        "workload_version": WORKSPACE_FS_WORKLOAD_VERSION,
        "baseline_contract_version": "aware.file_system.workspace_fs_benchmark.v1",
        "backend_kind": "python",
        "mode": mode,
        "workspace_root": root.as_posix(),
        "cache_dir": cache_dir.as_posix(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "environment": _benchmark_environment(),
        "canonical_filter_profile": "CanonicalSourceFilterConfig",
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "production_invariants": [
            "one production observer authority",
            "exact inventory and delta semantics",
            "watch events remain invalidation hints",
            "no materialization graph or ORM prerequisite",
            "timeout widening is not a performance proof",
        ],
        "source_mutation": source_mutation,
        "receipt_path": None,
    }
    validate_workspace_fs_workload_receipt(receipt)
    return receipt


def _maybe_write_receipt(
    receipt: dict[str, Any],
    config: WorkspaceFsWorkloadConfig,
    cache_dir: Path,
) -> dict[str, Any]:
    if not config.write_receipt:
        return receipt
    receipt_dir = (
        config.receipt_dir.expanduser().resolve()
        if config.receipt_dir is not None
        else cache_dir / "receipts"
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = receipt_dir / f"{WORKSPACE_FS_WORKLOAD_VERSION}.{timestamp}.json"
    with_path = {**receipt, "receipt_path": receipt_path.as_posix()}
    validate_workspace_fs_workload_receipt(with_path)
    receipt_path.write_text(
        json.dumps(with_path, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return with_path


def _require_empty(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Workload cache directory must be empty: {path}")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the generic aware-file-system production workload profile."
    )
    parser.add_argument("--workspace-root", default=None)
    parser.add_argument("--fixture-root", default=None)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--receipt-dir", default=None)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--packages", type=int, default=4)
    parser.add_argument("--files-per-package", type=int, default=32)
    parser.add_argument("--payload-bytes", type=int, default=512)
    parser.add_argument("--no-cpu-pressure", action="store_true")
    parser.add_argument("--no-contention", action="store_true")
    parser.add_argument("--no-recovery", action="store_true")
    parser.add_argument("--no-diagnostic-comparison", action="store_true")
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--compact", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    receipt = run_workspace_fs_workload(
        WorkspaceFsWorkloadConfig(
            workspace_root=Path(args.workspace_root) if args.workspace_root else None,
            fixture_root=Path(args.fixture_root) if args.fixture_root else None,
            cache_dir=Path(args.cache_dir) if args.cache_dir else None,
            receipt_dir=Path(args.receipt_dir) if args.receipt_dir else None,
            iterations=args.iterations,
            concurrency=args.concurrency,
            packages=args.packages,
            files_per_package=args.files_per_package,
            payload_bytes=args.payload_bytes,
            include_cpu_pressure=not args.no_cpu_pressure,
            include_contention=not args.no_contention,
            include_recovery=not args.no_recovery,
            include_diagnostic_comparison=not args.no_diagnostic_comparison,
            write_receipt=args.write_receipt,
        )
    )
    print(json.dumps(receipt, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
