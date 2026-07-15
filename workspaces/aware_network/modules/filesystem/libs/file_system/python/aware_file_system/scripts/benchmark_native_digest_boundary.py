from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from aware_file_system.native_digest_library import (
    RustNativeDigestLibraryConfig,
    prepare_native_digest_library,
)


NATIVE_DIGEST_BOUNDARY_BENCHMARK_VERSION = (
    "aware.file_system.native_digest_boundary_benchmark.v1"
)
DEFAULT_PAYLOAD_BYTES = 1024 * 1024
DEFAULT_ITERATIONS = 200


@dataclass(frozen=True, slots=True)
class NativeDigestBoundaryBenchmarkConfig:
    fixture_root: Path
    payload_bytes: int = DEFAULT_PAYLOAD_BYTES
    iterations: int = DEFAULT_ITERATIONS
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    manifest_path: Path | None = None
    target_dir: Path | None = None
    prepared_library_path: Path | None = None
    release: bool = False
    build_timeout_s: float = 240.0
    write_receipt: bool = False
    receipt_dir: Path | None = None


def run_native_digest_boundary_benchmark(
    config: NativeDigestBoundaryBenchmarkConfig,
) -> dict[str, Any]:
    _validate_config(config)
    fixture_root = config.fixture_root.expanduser().resolve()
    fixture_root.mkdir(parents=True, exist_ok=True)
    prepared_library = prepare_native_digest_library(
        RustNativeDigestLibraryConfig(
            cargo_path=config.cargo_path,
            cargo_home=config.cargo_home,
            manifest_path=config.manifest_path,
            target_dir=config.target_dir,
            prepared_library_path=config.prepared_library_path,
            release=config.release,
            build_timeout_s=config.build_timeout_s,
        )
    )
    payload = deterministic_payload(config.payload_bytes)
    expected_digest = hashlib.sha256(payload).hexdigest()

    python_samples_ns: list[int] = []
    for _ in range(config.iterations):
        started = time.perf_counter_ns()
        digest = hashlib.sha256(payload).hexdigest()
        python_samples_ns.append(time.perf_counter_ns() - started)
        if digest != expected_digest:
            raise RuntimeError("Python hashlib produced inconsistent SHA-256 output")

    native_samples_ns: list[int] = []
    for _ in range(config.iterations):
        started = time.perf_counter_ns()
        digest = prepared_library.sha256_hex(payload)
        native_samples_ns.append(time.perf_counter_ns() - started)
        if digest != expected_digest:
            raise RuntimeError("Rust native digest library SHA-256 parity failed")

    bytes_hashed = config.payload_bytes * config.iterations
    python_summary = _duration_summary(
        samples_ns=python_samples_ns,
        payload_bytes=config.payload_bytes,
        bytes_hashed=bytes_hashed,
    )
    native_summary = _duration_summary(
        samples_ns=native_samples_ns,
        payload_bytes=config.payload_bytes,
        bytes_hashed=bytes_hashed,
    )
    ratio = _safe_ratio(native_summary["median_s"], python_summary["median_s"])
    receipt = {
        "receipt_schema": NATIVE_DIGEST_BOUNDARY_BENCHMARK_VERSION,
        "mode": "native_digest_boundary_benchmark",
        "algorithm": "sha256",
        "payload_boundary": "python_bytearray_ctypes_from_buffer_v1",
        "payload_bytes": config.payload_bytes,
        "iterations": config.iterations,
        "bytes_hashed": bytes_hashed,
        "digest": expected_digest,
        "parity_passed": True,
        "release": config.release,
        "fixture_root": fixture_root.as_posix(),
        "python_hashlib": python_summary,
        "rust_native_library": {
            **native_summary,
            "backend_kind": "rust",
            "digest_backend_kind": prepared_library.digest_backend_kind,
            "library_path": prepared_library.library_path.as_posix(),
            "invocation_kind": prepared_library.invocation_kind,
            "manifest_path": prepared_library.manifest_path.as_posix(),
            "target_dir": (
                prepared_library.target_dir.as_posix()
                if prepared_library.target_dir is not None
                else None
            ),
            "rust_build": prepared_library.rust_build,
        },
        "native_to_python_median_duration_ratio": ratio,
        "native_to_python_median_throughput_ratio": _safe_ratio(
            native_summary["median_bytes_per_second"],
            python_summary["median_bytes_per_second"],
        ),
    }
    if config.write_receipt:
        receipt_path = _write_receipt(
            receipt=receipt,
            fixture_root=fixture_root,
            receipt_dir=config.receipt_dir,
        )
        receipt["receipt_path"] = receipt_path.as_posix()
        receipt_path.write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return receipt


def deterministic_payload(payload_bytes: int) -> bytearray:
    return bytearray(
        ((index * 31 + 17) % 251) for index in range(payload_bytes)
    )


def _duration_summary(
    *,
    samples_ns: Sequence[int],
    payload_bytes: int,
    bytes_hashed: int,
) -> dict[str, Any]:
    ordered = sorted(samples_ns)
    total_ns = sum(samples_ns)
    median_ns = _median_ns(ordered)
    total_s = total_ns / 1_000_000_000.0
    median_s = median_ns / 1_000_000_000.0
    return {
        "sample_count": len(samples_ns),
        "samples_s": [sample / 1_000_000_000.0 for sample in samples_ns],
        "min_s": ordered[0] / 1_000_000_000.0,
        "median_s": median_s,
        "p95_s": _percentile_ns(ordered, 0.95) / 1_000_000_000.0,
        "max_s": ordered[-1] / 1_000_000_000.0,
        "total_s": total_s,
        "bytes_per_second": bytes_hashed / total_s if total_s > 0 else 0.0,
        "median_bytes_per_second": (
            payload_bytes / median_s if median_s > 0 else 0.0
        ),
    }


def _median_ns(ordered_samples_ns: Sequence[int]) -> float:
    midpoint = len(ordered_samples_ns) // 2
    if len(ordered_samples_ns) % 2:
        return float(ordered_samples_ns[midpoint])
    return (
        ordered_samples_ns[midpoint - 1] + ordered_samples_ns[midpoint]
    ) / 2.0


def _percentile_ns(ordered_samples_ns: Sequence[int], percentile: float) -> int:
    index = int(round((len(ordered_samples_ns) - 1) * percentile))
    return ordered_samples_ns[max(0, min(index, len(ordered_samples_ns) - 1))]


def _write_receipt(
    *,
    receipt: dict[str, Any],
    fixture_root: Path,
    receipt_dir: Path | None,
) -> Path:
    base_dir = (
        receipt_dir.expanduser().resolve()
        if receipt_dir is not None
        else fixture_root / ".aware" / "reports" / "file_system" / "performance"
    )
    base_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return base_dir / (
        f"{receipt['receipt_schema']}.{timestamp}.json"
    )


def _validate_config(config: NativeDigestBoundaryBenchmarkConfig) -> None:
    if config.payload_bytes <= 0:
        raise ValueError("payload_bytes must be greater than 0")
    if config.iterations <= 0:
        raise ValueError("iterations must be greater than 0")


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark Python hashlib against the Rust native digest library.",
    )
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--payload-bytes", type=int, default=DEFAULT_PAYLOAD_BYTES)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--cargo-path", type=Path)
    parser.add_argument("--cargo-home", type=Path)
    parser.add_argument("--manifest-path", type=Path)
    parser.add_argument("--target-dir", type=Path)
    parser.add_argument("--library-path", type=Path)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--build-timeout-s", type=float, default=240.0)
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--receipt-dir", type=Path)
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    receipt = run_native_digest_boundary_benchmark(
        NativeDigestBoundaryBenchmarkConfig(
            fixture_root=args.fixture_root,
            payload_bytes=args.payload_bytes,
            iterations=args.iterations,
            cargo_path=args.cargo_path,
            cargo_home=args.cargo_home,
            manifest_path=args.manifest_path,
            target_dir=args.target_dir,
            prepared_library_path=args.library_path,
            release=args.release,
            build_timeout_s=args.build_timeout_s,
            write_receipt=args.write_receipt,
            receipt_dir=args.receipt_dir,
        )
    )
    if args.compact:
        compact = {
            "receipt_schema": receipt["receipt_schema"],
            "payload_bytes": receipt["payload_bytes"],
            "iterations": receipt["iterations"],
            "digest_backend_kind": receipt["rust_native_library"][
                "digest_backend_kind"
            ],
            "python_median_s": receipt["python_hashlib"]["median_s"],
            "native_median_s": receipt["rust_native_library"]["median_s"],
            "native_to_python_median_duration_ratio": receipt[
                "native_to_python_median_duration_ratio"
            ],
            "receipt_path": receipt.get("receipt_path"),
        }
        print(json.dumps(compact, indent=2, sort_keys=True))
    else:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
