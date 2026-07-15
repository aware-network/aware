from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from statistics import median
from typing import Any

from aware_file_system.native_apply_executor import (
    RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
    RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaRequest,
)
from aware_file_system_service_dto.file_system.service_operation import (
    ApplyFileSystemDeltaResponse,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemApplyPolicy,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemBackendKind,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemContentDigest,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaEntry,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaOperation,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaSet,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDeltaTotals,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemDigestAlgorithm,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemRelativePath,
)
from aware_file_system_service_dto.file_system.types import (
    FileSystemRootRef,
)

SERVICE_APPLY_ROUTE_PROFILE_MATRIX_VERSION = (
    "aware.file_system.service_apply_route_profile_matrix.v1"
)


@dataclass(frozen=True, slots=True)
class ServiceApplyRouteProfileCase:
    name: str
    create_file_count: int
    update_file_count: int
    delete_file_count: int
    payload_bytes: int
    verify_digests: bool = True

    @property
    def operation_count(self) -> int:
        return (
            self.create_file_count
            + self.update_file_count
            + self.delete_file_count
        )


@dataclass(frozen=True, slots=True)
class ServiceApplyRouteProfileConfig:
    fixture_root: Path
    iterations: int = 3
    cases: tuple[ServiceApplyRouteProfileCase, ...] = ()
    case_names: tuple[str, ...] = ()
    warm_rust_route: bool = True
    write_receipt: bool = False
    receipt_dir: Path | None = None


def default_service_apply_route_profile_cases() -> tuple[
    ServiceApplyRouteProfileCase,
    ...,
]:
    return (
        ServiceApplyRouteProfileCase(
            name="many_small_files",
            create_file_count=64,
            update_file_count=64,
            delete_file_count=16,
            payload_bytes=128,
            verify_digests=True,
        ),
        ServiceApplyRouteProfileCase(
            name="large_payloads",
            create_file_count=8,
            update_file_count=8,
            delete_file_count=2,
            payload_bytes=32 * 1024,
            verify_digests=True,
        ),
    )


async def run_service_apply_route_profile_matrix(
    config: ServiceApplyRouteProfileConfig,
    *,
    api_client: Any | None = None,
    close_client: Callable[[], None] | None = None,
) -> dict[str, Any]:
    _validate_config(config)
    fixture_root = config.fixture_root.expanduser().resolve()
    _ensure_empty_or_missing(fixture_root)
    fixture_root.mkdir(parents=True, exist_ok=True)

    owns_client = api_client is None
    if api_client is None:
        from aware_file_system_service.api_service_protocol import (
            build_aware_file_system_service_protocol_handler,
        )
        from aware_file_system_service.local_api_client import (
            build_local_file_system_service_api_client,
        )

        handler = build_aware_file_system_service_protocol_handler()
        api_client = build_local_file_system_service_api_client(handler=handler)
        close_client = getattr(handler, "close", None)

    cases = _selected_cases(config)
    rust_route_warmup = None
    case_receipts: list[dict[str, Any]] = []
    try:
        if config.warm_rust_route:
            rust_route_warmup = await _warm_rust_route(
                api_client=api_client,
                fixture_root=fixture_root,
            )
        for case in cases:
            case_receipts.append(
                await _run_case(
                    api_client=api_client,
                    fixture_root=fixture_root,
                    case=case,
                    iterations=config.iterations,
                )
            )
    finally:
        if owns_client and close_client is not None:
            close_client()

    receipt = {
        "receipt_schema": SERVICE_APPLY_ROUTE_PROFILE_MATRIX_VERSION,
        "mode": "service_apply_route_profile_matrix",
        "fixture_root": fixture_root.as_posix(),
        "iteration_count": config.iterations,
        "case_count": len(case_receipts),
        "generated_api_client_route": True,
        "backend_routes": ["python", "rust"],
        "rust_route_warmup": rust_route_warmup,
        "rust_route_contract": {
            "payload_protocol": RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
            "response_protocol": RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
            "timing_protocol": RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
        },
        "cases": case_receipts,
        "analysis": _analysis(case_receipts),
    }
    return _maybe_write_receipt(
        receipt=receipt,
        fixture_root=fixture_root,
        config=config,
    )


def run_service_apply_route_profile_matrix_sync(
    config: ServiceApplyRouteProfileConfig,
) -> dict[str, Any]:
    return asyncio.run(run_service_apply_route_profile_matrix(config))


async def _warm_rust_route(
    *,
    api_client: Any,
    fixture_root: Path,
) -> dict[str, Any]:
    warmup_root = fixture_root / "warmup" / "rust"
    entries = _write_fixture(
        root=warmup_root,
        case=ServiceApplyRouteProfileCase(
            name="rust_route_warmup",
            create_file_count=1,
            update_file_count=0,
            delete_file_count=0,
            payload_bytes=16,
            verify_digests=True,
        ),
        iteration_index=0,
    )
    return await _measure_apply_route(
        api_client=api_client,
        root_path=warmup_root,
        entries=entries,
        backend_kind=FileSystemBackendKind.rust,
        iteration_index=0,
        verify_digests=True,
    )


async def _run_case(
    *,
    api_client: Any,
    fixture_root: Path,
    case: ServiceApplyRouteProfileCase,
    iterations: int,
) -> dict[str, Any]:
    python_samples: list[dict[str, Any]] = []
    rust_samples: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for iteration_index in range(iterations):
        iteration_root = fixture_root / "cases" / case.name / f"iteration_{iteration_index}"
        base_root = iteration_root / "base"
        python_root = iteration_root / "python"
        rust_root = iteration_root / "rust"
        entries = _write_fixture(
            root=base_root,
            case=case,
            iteration_index=iteration_index,
        )
        shutil.copytree(base_root, python_root)
        shutil.copytree(base_root, rust_root)

        python_sample = await _measure_apply_route(
            api_client=api_client,
            root_path=python_root,
            entries=entries,
            backend_kind=FileSystemBackendKind.python,
            iteration_index=iteration_index,
            verify_digests=case.verify_digests,
        )
        rust_sample = await _measure_apply_route(
            api_client=api_client,
            root_path=rust_root,
            entries=entries,
            backend_kind=FileSystemBackendKind.rust,
            iteration_index=iteration_index,
            verify_digests=case.verify_digests,
        )
        python_samples.append(python_sample)
        rust_samples.append(rust_sample)
        mismatches.extend(
            _parity_mismatches(
                iteration_index=iteration_index,
                python_root=python_root,
                rust_root=rust_root,
                python_sample=python_sample,
                rust_sample=rust_sample,
            )
        )

    return {
        "case_name": case.name,
        "fixture": {
            "create_file_count": case.create_file_count,
            "update_file_count": case.update_file_count,
            "delete_file_count": case.delete_file_count,
            "operation_count": case.operation_count,
            "payload_bytes": case.payload_bytes,
            "verify_digests": case.verify_digests,
        },
        "python_route": {
            "backend_kind": "python",
            "samples": python_samples,
            "summary": _backend_summary(python_samples),
        },
        "rust_route": {
            "backend_kind": "rust",
            "samples": rust_samples,
            "summary": _backend_summary(rust_samples),
        },
        "parity": {
            "passed": not mismatches,
            "sample_count": iterations,
            "checked_fields": [
                "tree_sha256",
                "created_count",
                "updated_count",
                "deleted_count",
                "bytes_written",
                "bytes_deleted",
                "digest_verified_count",
            ],
            "mismatches": mismatches,
        },
        "rust_to_python_duration_ratio": _ratio(
            _summary_median(rust_samples, "duration_s"),
            _summary_median(python_samples, "duration_s"),
        ),
    }


async def _measure_apply_route(
    *,
    api_client: Any,
    root_path: Path,
    entries: Sequence[FileSystemDeltaEntry],
    backend_kind: FileSystemBackendKind,
    iteration_index: int,
    verify_digests: bool,
) -> dict[str, Any]:
    root = FileSystemRootRef(root_path=root_path.as_posix())
    request = ApplyFileSystemDeltaRequest(
        root=root,
        backend_kind=backend_kind,
        delta_set=FileSystemDeltaSet(
            root=root,
            entries=list(entries),
            totals=_delta_totals(entries),
        ),
        policy=FileSystemApplyPolicy(verify_digests=verify_digests),
    )
    started = time.perf_counter()
    response = await api_client.filesystem.delta.apply(request)
    duration_s = time.perf_counter() - started
    return _sample_from_response(
        response=response,
        backend_kind=backend_kind,
        iteration_index=iteration_index,
        duration_s=duration_s,
        root_path=root_path,
    )


def _sample_from_response(
    *,
    response: ApplyFileSystemDeltaResponse,
    backend_kind: FileSystemBackendKind,
    iteration_index: int,
    duration_s: float,
    root_path: Path,
) -> dict[str, Any]:
    if not response.success or response.receipt is None:
        raise RuntimeError(response.error or f"{backend_kind.value} apply failed")
    backend_receipt = response.backend_receipt or response.receipt.backend_receipt
    if backend_receipt is None:
        raise ValueError(f"{backend_kind.value} apply response missing backend receipt")
    if backend_receipt.backend_kind is not backend_kind:
        raise ValueError(
            f"{backend_kind.value} route returned backend "
            f"{backend_receipt.backend_kind.value}"
        )
    metadata = dict(backend_receipt.metadata)
    if backend_kind is FileSystemBackendKind.rust:
        _validate_rust_route_metadata(metadata)
        if backend_receipt.implementation_language != "rust":
            raise ValueError("Rust route receipt must report implementation_language=rust")
        if not backend_receipt.native_accelerated:
            raise ValueError("Rust route receipt must report native_accelerated=true")
    receipt = response.receipt
    service_duration = backend_receipt.timings.get("duration_s")
    return {
        "iteration_index": iteration_index,
        "duration_s": duration_s,
        "service_duration_s": service_duration,
        "success": response.success,
        "created_count": receipt.created_count,
        "updated_count": receipt.updated_count,
        "deleted_count": receipt.deleted_count,
        "bytes_written": receipt.bytes_written,
        "bytes_deleted": receipt.bytes_deleted,
        "digest_verified_count": receipt.digest_verified_count,
        "backend_kind": backend_receipt.backend_kind.value,
        "backend_name": backend_receipt.backend_name,
        "implementation_language": backend_receipt.implementation_language,
        "native_accelerated": backend_receipt.native_accelerated,
        "digest_backend_kind": metadata.get("digest_backend_kind"),
        "service_payload_protocol": metadata.get("service_payload_protocol"),
        "service_response_protocol": metadata.get("service_response_protocol"),
        "service_timing_protocol": metadata.get("service_timing_protocol"),
        "service_stream_chunk_bytes": metadata.get("service_stream_chunk_bytes"),
        "service_invocation_kind": metadata.get("service_invocation_kind"),
        "service_client_timings_s": metadata.get("service_client_timings_s"),
        "service_client_counters": metadata.get("service_client_counters"),
        "service_server_timings_s": metadata.get("service_server_timings_s"),
        "service_server_flags": metadata.get("service_server_flags"),
        "service_content_engine": metadata.get("service_content_engine"),
        "tree_sha256": _tree_sha256(root_path),
    }


def _validate_rust_route_metadata(metadata: dict[str, Any]) -> None:
    expected = {
        "service_payload_protocol": RUST_WORKSPACE_APPLY_SERVICE_DIRECT_STREAMING_PAYLOAD_PROTOCOL,
        "service_response_protocol": RUST_WORKSPACE_APPLY_SERVICE_COMPACT_RESPONSE_PROTOCOL,
        "service_timing_protocol": RUST_WORKSPACE_APPLY_SERVICE_TIMING_TRAILER_PROTOCOL,
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(
                f"Rust route metadata {key} must be {value!r}, "
                f"got {metadata.get(key)!r}"
            )


def _write_fixture(
    *,
    root: Path,
    case: ServiceApplyRouteProfileCase,
    iteration_index: int,
) -> tuple[FileSystemDeltaEntry, ...]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "aware.workspace.toml").write_text(
        "[workspace]\nname = \"service-apply-route-profile\"\n",
        encoding="utf-8",
    )
    entries: list[FileSystemDeltaEntry] = []
    for index in range(case.create_file_count):
        content = _payload(
            seed=f"create-{iteration_index}-{index}",
            payload_bytes=case.payload_bytes,
        )
        entries.append(
            _write_entry(
                operation=FileSystemDeltaOperation.create,
                relative_path=f"generated/new/item_{index}.py",
                content=content,
                verify_digests=case.verify_digests,
            )
        )

    for index in range(case.update_file_count):
        relative_path = f"generated/existing/item_{index}.py"
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            _payload(
                seed=f"old-{iteration_index}-{index}",
                payload_bytes=case.payload_bytes,
            ),
            encoding="utf-8",
        )
        content = _payload(
            seed=f"update-{iteration_index}-{index}",
            payload_bytes=case.payload_bytes,
        )
        entries.append(
            _write_entry(
                operation=FileSystemDeltaOperation.update,
                relative_path=relative_path,
                content=content,
                verify_digests=case.verify_digests,
            )
        )

    for index in range(case.delete_file_count):
        relative_path = f"generated/delete/item_{index}.txt"
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            _payload(
                seed=f"delete-{iteration_index}-{index}",
                payload_bytes=case.payload_bytes,
            ),
            encoding="utf-8",
        )
        entries.append(
            FileSystemDeltaEntry(
                operation=FileSystemDeltaOperation.delete,
                path=FileSystemRelativePath(relative_path=relative_path),
            )
        )
    return tuple(entries)


def _write_entry(
    *,
    operation: FileSystemDeltaOperation,
    relative_path: str,
    content: str,
    verify_digests: bool,
) -> FileSystemDeltaEntry:
    content_bytes = content.encode("utf-8")
    digest = (
        FileSystemContentDigest(
            algorithm=FileSystemDigestAlgorithm.sha256,
            hex=sha256(content_bytes).hexdigest(),
            byte_length=len(content_bytes),
        )
        if verify_digests
        else None
    )
    return FileSystemDeltaEntry(
        operation=operation,
        path=FileSystemRelativePath(relative_path=relative_path),
        content_text=content,
        after_digest=digest,
    )


def _delta_totals(entries: Sequence[FileSystemDeltaEntry]) -> FileSystemDeltaTotals:
    return FileSystemDeltaTotals(
        create_count=sum(
            1 for entry in entries if entry.operation is FileSystemDeltaOperation.create
        ),
        update_count=sum(
            1 for entry in entries if entry.operation is FileSystemDeltaOperation.update
        ),
        delete_count=sum(
            1 for entry in entries if entry.operation is FileSystemDeltaOperation.delete
        ),
        byte_count=sum(len((entry.content_text or "").encode("utf-8")) for entry in entries),
        digest_count=sum(1 for entry in entries if entry.after_digest is not None),
    )


def _parity_mismatches(
    *,
    iteration_index: int,
    python_root: Path,
    rust_root: Path,
    python_sample: dict[str, Any],
    rust_sample: dict[str, Any],
) -> list[str]:
    mismatches: list[str] = []
    if _tree_sha256(python_root) != _tree_sha256(rust_root):
        mismatches.append(f"iteration {iteration_index}: tree_sha256 mismatch")
    for key in (
        "created_count",
        "updated_count",
        "deleted_count",
        "bytes_written",
        "bytes_deleted",
        "digest_verified_count",
    ):
        if python_sample[key] != rust_sample[key]:
            mismatches.append(
                f"iteration {iteration_index}: {key} mismatch "
                f"{python_sample[key]!r} != {rust_sample[key]!r}"
            )
    return mismatches


def _backend_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "duration_s": _stats(samples, "duration_s"),
        "service_duration_s": _stats(samples, "service_duration_s"),
        "bytes_written_per_second": _stats(
            [
                {
                    "bytes_written_per_second": _rate(
                        int(sample["bytes_written"]),
                        float(sample["duration_s"]),
                    )
                }
                for sample in samples
            ],
            "bytes_written_per_second",
        ),
    }


def _stats(samples: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [
        float(sample[key])
        for sample in samples
        if isinstance(sample.get(key), int | float)
    ]
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": len(values),
        "min": min(values),
        "median": median(values),
        "max": max(values),
    }


def _analysis(cases: list[dict[str, Any]]) -> dict[str, Any]:
    ratios = [
        {
            "case_name": case["case_name"],
            "rust_to_python_duration_ratio": case["rust_to_python_duration_ratio"],
        }
        for case in cases
        if case["rust_to_python_duration_ratio"] is not None
    ]
    slowest_rust = max(
        cases,
        key=lambda case: _summary_median(case["rust_route"]["samples"], "duration_s") or 0.0,
        default=None,
    )
    return {
        "all_parity_passed": all(case["parity"]["passed"] for case in cases),
        "rust_route_contract_checked": True,
        "rust_to_python_duration_ratios": ratios,
        "slowest_rust_route_case": (
            {
                "case_name": slowest_rust["case_name"],
                "median_s": _summary_median(
                    slowest_rust["rust_route"]["samples"],
                    "duration_s",
                ),
            }
            if slowest_rust is not None
            else None
        ),
    }


def _summary_median(samples: list[dict[str, Any]], key: str) -> float | None:
    return _stats(samples, key)["median"]


def _rate(value: int, duration_s: float) -> float | None:
    if duration_s <= 0:
        return None
    return value / duration_s


def _ratio(candidate: float | None, reference: float | None) -> float | None:
    if candidate is None or reference is None or reference <= 0:
        return None
    return candidate / reference


def _tree_sha256(root: Path) -> str:
    digest = sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative_path = path.relative_to(root).as_posix()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _payload(*, seed: str, payload_bytes: int) -> str:
    if payload_bytes <= 0:
        return ""
    base = (f"# {seed}\nprint({seed!r})\n").encode("utf-8")
    repeats = (payload_bytes // len(base)) + 1
    return (base * repeats)[:payload_bytes].decode("utf-8", errors="ignore")


def _selected_cases(
    config: ServiceApplyRouteProfileConfig,
) -> tuple[ServiceApplyRouteProfileCase, ...]:
    cases = config.cases or default_service_apply_route_profile_cases()
    if not config.case_names:
        return cases
    by_name = {case.name: case for case in cases}
    missing = sorted(set(config.case_names) - set(by_name))
    if missing:
        raise ValueError(f"Unknown service apply route profile case(s): {missing}")
    return tuple(by_name[name] for name in config.case_names)


def _validate_config(config: ServiceApplyRouteProfileConfig) -> None:
    if config.iterations < 1:
        raise ValueError("iterations must be >= 1")
    for case in config.cases or default_service_apply_route_profile_cases():
        if case.operation_count < 1:
            raise ValueError(f"{case.name} must include at least one operation")
        if case.payload_bytes < 0:
            raise ValueError(f"{case.name} payload_bytes must be >= 0")


def _ensure_empty_or_missing(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def _maybe_write_receipt(
    *,
    receipt: dict[str, Any],
    fixture_root: Path,
    config: ServiceApplyRouteProfileConfig,
) -> dict[str, Any]:
    if not config.write_receipt:
        return receipt
    receipt_dir = (
        config.receipt_dir.expanduser().resolve()
        if config.receipt_dir is not None
        else fixture_root / ".aware" / "reports" / "file_system" / "performance"
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = (
        receipt_dir
        / f"aware.file_system.service_apply_route_profile_matrix.v1.{timestamp}.json"
    )
    receipt_with_path = dict(receipt)
    receipt_with_path["receipt_path"] = receipt_path.as_posix()
    receipt_path.write_text(
        json.dumps(receipt_with_path, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt_with_path


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit FileSystem Service API apply route performance receipts.",
    )
    parser.add_argument("--fixture-root", required=True, type=Path)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--skip-rust-warmup", action="store_true")
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--receipt-dir", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    receipt = run_service_apply_route_profile_matrix_sync(
        ServiceApplyRouteProfileConfig(
            fixture_root=args.fixture_root,
            iterations=args.iterations,
            case_names=tuple(args.case),
            warm_rust_route=not args.skip_rust_warmup,
            write_receipt=args.write_receipt,
            receipt_dir=args.receipt_dir,
        )
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
