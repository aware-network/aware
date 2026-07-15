from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

from aware_file_system.benchmark_receipt_contract import (
    WORKSPACE_FS_BENCHMARK_VERSION,
    validate_workspace_fs_benchmark_receipt,
)
from aware_file_system.config import CanonicalSourceFilterConfig, Config, FileSystemConfig
from aware_file_system.index.file_metadata_cached import FileMetadataCached
from aware_file_system.index.file_system_index import FileSystemIndex
from aware_file_system.index.incremental_scanner import ScanResult


BENCHMARK_VERSION = WORKSPACE_FS_BENCHMARK_VERSION
BACKEND_KIND = "python"


@dataclass(frozen=True, slots=True)
class WorkspaceFsBenchmarkConfig:
    packages: int = 8
    files_per_package: int = 64
    payload_bytes: int = 512
    iterations: int = 3
    fixture_root: Path | None = None
    workspace_root: Path | None = None
    cache_dir: Path | None = None
    write_receipt: bool = False
    receipt_dir: Path | None = None


def run_workspace_fs_benchmark(
    config: WorkspaceFsBenchmarkConfig | None = None,
) -> dict[str, Any]:
    resolved = config or WorkspaceFsBenchmarkConfig()
    if resolved.iterations < 1:
        raise ValueError("Benchmark iterations must be at least 1.")
    if resolved.fixture_root is not None and resolved.workspace_root is not None:
        raise ValueError("Use either fixture_root or workspace_root, not both.")
    if resolved.workspace_root is not None:
        return _run_real_workspace_benchmark(config=resolved)
    if resolved.fixture_root is None:
        with tempfile.TemporaryDirectory(prefix="aware-fs-benchmark-") as raw_tmp:
            return _run_workspace_fs_benchmark_with_root(
                config=resolved,
                fixture_root=Path(raw_tmp),
            )
    return _run_workspace_fs_benchmark_with_root(
        config=resolved,
        fixture_root=resolved.fixture_root,
    )


def _run_workspace_fs_benchmark_with_root(
    *,
    config: WorkspaceFsBenchmarkConfig,
    fixture_root: Path,
) -> dict[str, Any]:
    root = fixture_root.expanduser().resolve()
    _ensure_empty_or_missing(root)
    root.mkdir(parents=True, exist_ok=True)
    fixture = _write_workspace_fixture(
        root=root,
        packages=config.packages,
        files_per_package=config.files_per_package,
        payload_bytes=config.payload_bytes,
    )
    cache_dir = (
        config.cache_dir.expanduser().resolve()
        if config.cache_dir is not None
        else root / ".aware" / "benchmarks" / "file_system_index"
    )

    cold_samples: list[dict[str, Any]] = []
    warm_samples: list[dict[str, Any]] = []
    edit_samples: list[dict[str, Any]] = []
    edit_path = root / fixture["edit_target"]
    for iteration_index in range(config.iterations):
        iteration_cache_dir = cache_dir / f"iteration_{iteration_index}"
        cold_warm_index = _file_system_index(
            root=root,
            cache_dir=iteration_cache_dir / "cold_warm",
        )
        cold_samples.append(
            _measure_scan(
                index=cold_warm_index,
                root=root,
                label="cold_force_refresh",
                force_refresh=True,
                hash_changed_paths=True,
                iteration_index=iteration_index,
            )
        )
        warm_samples.append(
            _measure_scan(
                index=cold_warm_index,
                root=root,
                label="warm_noop_session_cache",
                force_refresh=False,
                hash_changed_paths=False,
                iteration_index=iteration_index,
            )
        )
        edit_index = _file_system_index(
            root=root,
            cache_dir=iteration_cache_dir / "edit",
        )
        edit_index.scan_relative_metadata(force_refresh=True)
        edit_path.write_text(
            _payload(
                seed=f"edited-small-change-{iteration_index}",
                payload_bytes=config.payload_bytes + 17,
            ),
            encoding="utf-8",
        )
        os.utime(edit_path, None)
        edit_index.invalidate_cache()
        edit_samples.append(
            _measure_scan(
                index=edit_index,
                root=root,
                label="one_file_edit_metadata_hash",
                force_refresh=False,
                hash_changed_paths=True,
                iteration_index=iteration_index,
            )
        )

    receipt = _benchmark_receipt(
        root=root,
        cache_dir=cache_dir,
        mode="synthetic_fixture",
        config=config,
        fixture={
            "packages": config.packages,
            "files_per_package": config.files_per_package,
            "payload_bytes": config.payload_bytes,
            "expected_tracked_file_count": fixture["expected_tracked_file_count"],
            "edit_target": fixture["edit_target"],
        },
        runs=[
            _aggregate_samples("cold_force_refresh", cold_samples),
            _aggregate_samples("warm_noop_session_cache", warm_samples),
            _aggregate_samples("one_file_edit_metadata_hash", edit_samples),
        ],
    )
    return _maybe_write_receipt(
        receipt=receipt,
        root=root,
        config=config,
    )


def _run_real_workspace_benchmark(
    *,
    config: WorkspaceFsBenchmarkConfig,
) -> dict[str, Any]:
    if config.workspace_root is None:
        raise ValueError("workspace_root is required for real-workspace benchmark mode.")
    root = config.workspace_root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Workspace root is not a directory: {root}")

    if config.cache_dir is not None:
        cache_dir = config.cache_dir.expanduser().resolve()
        receipt = _run_real_workspace_benchmark_with_index(
            config=config,
            root=root,
            cache_dir=cache_dir,
        )
        return _maybe_write_receipt(receipt=receipt, root=root, config=config)

    with tempfile.TemporaryDirectory(prefix="aware-fs-real-cache-") as raw_cache:
        cache_dir = Path(raw_cache)
        receipt = _run_real_workspace_benchmark_with_index(
            config=config,
            root=root,
            cache_dir=cache_dir,
        )
        return _maybe_write_receipt(receipt=receipt, root=root, config=config)


def _run_real_workspace_benchmark_with_index(
    *,
    config: WorkspaceFsBenchmarkConfig,
    root: Path,
    cache_dir: Path,
) -> dict[str, Any]:
    cold_samples: list[dict[str, Any]] = []
    warm_samples: list[dict[str, Any]] = []
    for iteration_index in range(config.iterations):
        index = _file_system_index(
            root=root,
            cache_dir=cache_dir / f"iteration_{iteration_index}",
        )
        cold_samples.append(
            _measure_scan(
                index=index,
                root=root,
                label="cold_force_refresh",
                force_refresh=True,
                hash_changed_paths=False,
                iteration_index=iteration_index,
            )
        )
        warm_samples.append(
            _measure_scan(
                index=index,
                root=root,
                label="warm_noop_session_cache",
                force_refresh=False,
                hash_changed_paths=False,
                iteration_index=iteration_index,
            )
        )
    return _benchmark_receipt(
        root=root,
        cache_dir=cache_dir,
        mode="real_workspace_readonly",
        config=config,
        fixture={
            "workspace_root": root.as_posix(),
            "source_mutation": False,
        },
        runs=[
            _aggregate_samples("cold_force_refresh", cold_samples),
            _aggregate_samples("warm_noop_session_cache", warm_samples),
        ],
    )


def _benchmark_receipt(
    *,
    root: Path,
    cache_dir: Path,
    mode: str,
    config: WorkspaceFsBenchmarkConfig,
    fixture: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    receipt = {
        "benchmark_version": BENCHMARK_VERSION,
        "backend_kind": BACKEND_KIND,
        "mode": mode,
        "iteration_count": config.iterations,
        "workspace_root": root.as_posix(),
        "cache_dir": cache_dir.as_posix(),
        "fixture": fixture,
        "runs": runs,
        "recommendation": {
            "rust_must_preserve": [
                "canonical source filter semantics",
                "workspace-relative path output",
                "cold/warm/edit run labels and receipt fields",
                "SHA-256 digest equality for changed paths",
            ],
            "rust_should_improve": [
                "cold_force_refresh duration",
                "one_file_edit_metadata_hash duration",
                "changed-path hash duration",
            ],
        },
    }
    validate_workspace_fs_benchmark_receipt(receipt)
    return receipt


def _measure_scan(
    *,
    index: FileSystemIndex,
    root: Path,
    label: str,
    force_refresh: bool,
    hash_changed_paths: bool,
    iteration_index: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    scan_result, current_files = index.scan_relative_metadata(
        force_refresh=force_refresh,
    )
    duration_s = time.perf_counter() - started
    hash_stats = (
        _hash_changed_metadata(
            root=root,
            scan_result=scan_result,
        )
        if hash_changed_paths
        else {
            "hashed_path_count": 0,
            "hash_duration_s": 0.0,
            "hashes": {},
        }
    )
    performance = index.get_performance_stats()
    cache_stats = performance.get("cache", {})
    directory_cache = _mapping(cache_stats.get("directory_cache", {}))
    persistent_cache = _mapping(cache_stats.get("persistent_cache", {}))
    return {
        "label": label,
        "iteration_index": iteration_index,
        "duration_s": duration_s,
        "scanner_scan_time_s": scan_result.scan_time,
        "total_changes": scan_result.total_changes,
        "current_file_count": len(current_files),
        "added_count": len(scan_result.added),
        "modified_count": len(scan_result.modified),
        "deleted_count": len(scan_result.deleted),
        "files_processed": scan_result.files_processed,
        "files_content_read": scan_result.files_content_read,
        "cache_hit_ratio": scan_result.cache_hit_ratio,
        "directory_cache": {
            "total_directories": directory_cache.get("total_directories"),
            "total_files_tracked": directory_cache.get("total_files_tracked"),
            "changed_directories": directory_cache.get("changed_directories"),
        },
        "persistent_cache": {
            "entry_count": persistent_cache.get("entry_count"),
            "file_size": persistent_cache.get("file_size"),
        },
        **hash_stats,
    }


def _aggregate_samples(
    label: str,
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    if not samples:
        raise ValueError(f"Benchmark run {label!r} requires at least one sample.")
    representative = samples[-1]
    return {
        "label": label,
        "iteration_count": len(samples),
        "duration_s": _median_number(samples, "duration_s"),
        "scanner_scan_time_s": _median_number(samples, "scanner_scan_time_s"),
        "hash_duration_s": _median_number(samples, "hash_duration_s"),
        "total_changes": representative["total_changes"],
        "current_file_count": representative["current_file_count"],
        "added_count": representative["added_count"],
        "modified_count": representative["modified_count"],
        "deleted_count": representative["deleted_count"],
        "files_processed": representative["files_processed"],
        "files_content_read": representative["files_content_read"],
        "cache_hit_ratio": _median_number(samples, "cache_hit_ratio"),
        "hashed_path_count": representative["hashed_path_count"],
        "hashes": representative["hashes"],
        "directory_cache": representative["directory_cache"],
        "persistent_cache": representative["persistent_cache"],
        "summary": {
            "duration_s": _stats(samples, "duration_s"),
            "scanner_scan_time_s": _stats(samples, "scanner_scan_time_s"),
            "hash_duration_s": _stats(samples, "hash_duration_s"),
            "cache_hit_ratio": _stats(samples, "cache_hit_ratio"),
        },
        "samples": samples,
    }


def _median_number(samples: list[dict[str, Any]], key: str) -> float:
    values = _number_values(samples, key)
    return float(median(values)) if values else 0.0


def _stats(samples: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = sorted(_number_values(samples, key))
    if not values:
        return {
            "count": 0,
            "min": None,
            "median": None,
            "p95": None,
            "max": None,
        }
    return {
        "count": len(values),
        "min": values[0],
        "median": float(median(values)),
        "p95": _percentile_nearest_rank(values, 0.95),
        "max": values[-1],
    }


def _number_values(samples: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for sample in samples:
        value = sample.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            values.append(float(value))
    return values


def _percentile_nearest_rank(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    rank = max(1, int(len(values) * percentile + 0.999999))
    return values[min(rank, len(values)) - 1]


def _hash_changed_metadata(
    *,
    root: Path,
    scan_result: ScanResult,
) -> dict[str, Any]:
    changed: dict[str, FileMetadataCached] = {
        **scan_result.added,
        **scan_result.modified,
    }
    started = time.perf_counter()
    hashes = {
        relative_path: metadata.compute_hash_if_needed(str(root / relative_path))
        for relative_path, metadata in sorted(changed.items())
    }
    duration_s = time.perf_counter() - started
    return {
        "hashed_path_count": len(hashes),
        "hash_duration_s": duration_s,
        "hashes": hashes,
    }


def _file_system_index(
    *,
    root: Path,
    cache_dir: Path,
) -> FileSystemIndex:
    return FileSystemIndex(
        Config(
            file_system=FileSystemConfig(
                root_path=root.as_posix(),
                generate_tree=False,
                export_json=False,
            ),
            filter=CanonicalSourceFilterConfig(),
        ),
        cache_dir=cache_dir.as_posix(),
    )


def _write_workspace_fixture(
    *,
    root: Path,
    packages: int,
    files_per_package: int,
    payload_bytes: int,
) -> dict[str, Any]:
    (root / "aware.workspace.toml").write_text(
        "[workspace]\nname = \"fs-benchmark\"\n",
        encoding="utf-8",
    )
    tracked_count = 1
    edit_target: str | None = None
    for package_index in range(packages):
        package_root = root / "modules" / f"bench_{package_index}" / "structure" / "ontology"
        source_root = package_root / "aware" / f"bench_{package_index}"
        source_root.mkdir(parents=True, exist_ok=True)
        (package_root / "aware.toml").write_text(
            "[package]\n"
            + f"package_name = \"bench-{package_index}\"\n"
            + "kind = \"ontology\"\n",
            encoding="utf-8",
        )
        tracked_count += 1
        for file_index in range(files_per_package):
            relative_path = (
                Path("modules")
                / f"bench_{package_index}"
                / "structure"
                / "ontology"
                / "aware"
                / f"bench_{package_index}"
                / f"item_{file_index}.aware"
            )
            target = root / relative_path
            target.write_text(
                _payload(
                    seed=f"bench-{package_index}-{file_index}",
                    payload_bytes=payload_bytes,
                ),
                encoding="utf-8",
            )
            tracked_count += 1
            if edit_target is None:
                edit_target = relative_path.as_posix()

    _write_ignored_noise(root)
    if edit_target is None:
        raise ValueError("Benchmark fixture requires at least one source file.")
    return {
        "expected_tracked_file_count": tracked_count,
        "edit_target": edit_target,
    }


def _payload(
    *,
    seed: str,
    payload_bytes: int,
) -> str:
    base = f"class {seed.replace('-', '_')} {{\n    name String\n}}\n"
    if len(base.encode("utf-8")) >= payload_bytes:
        return base
    padding = "x" * max(payload_bytes - len(base.encode("utf-8")), 0)
    return base + "// " + padding + "\n"


def _write_ignored_noise(root: Path) -> None:
    for relative_path in (
        ".aware/cache/ignored.json",
        "_aware/cache/ignored.json",
        "node_modules/pkg/ignored.js",
        "build/generated/ignored.py",
        ".venv/lib/ignored.py",
    ):
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ignored\n", encoding="utf-8")


def _ensure_empty_or_missing(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise ValueError(
            "Benchmark fixture root must be empty so the receipt is reproducible: "
            f"{path}"
        )


def _maybe_write_receipt(
    *,
    receipt: dict[str, Any],
    root: Path,
    config: WorkspaceFsBenchmarkConfig,
) -> dict[str, Any]:
    if not config.write_receipt:
        return receipt
    receipt_dir = (
        config.receipt_dir.expanduser().resolve()
        if config.receipt_dir is not None
        else root / ".aware" / "reports" / "file_system" / "performance"
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = (
        f"{BENCHMARK_VERSION}.{receipt['backend_kind']}.{receipt['mode']}."
        f"{timestamp}.json"
    )
    receipt_path = receipt_dir / filename
    receipt_with_path = {
        **receipt,
        "receipt_path": receipt_path.as_posix(),
    }
    validate_workspace_fs_benchmark_receipt(receipt_with_path)
    receipt_path.write_text(
        json.dumps(receipt_with_path, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_with_path


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit an aware-file-system Workspace-style benchmark receipt.",
    )
    parser.add_argument("--fixture-root", default=None)
    parser.add_argument("--workspace-root", default=None)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--packages", type=int, default=8)
    parser.add_argument("--files-per-package", type=int, default=64)
    parser.add_argument("--payload-bytes", type=int, default=512)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--receipt-dir", default=None)
    parser.add_argument("--compact", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    receipt = run_workspace_fs_benchmark(
        WorkspaceFsBenchmarkConfig(
            packages=args.packages,
            files_per_package=args.files_per_package,
            payload_bytes=args.payload_bytes,
            iterations=args.iterations,
            fixture_root=Path(args.fixture_root) if args.fixture_root else None,
            workspace_root=Path(args.workspace_root) if args.workspace_root else None,
            cache_dir=Path(args.cache_dir) if args.cache_dir else None,
            write_receipt=args.write_receipt,
            receipt_dir=Path(args.receipt_dir) if args.receipt_dir else None,
        )
    )
    indent = None if args.compact else 2
    print(json.dumps(receipt, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
