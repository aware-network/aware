from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from aware_file_system.benchmark_receipt_contract import (
    WORKSPACE_FS_BENCHMARK_VERSION,
)
from aware_file_system.native_apply import (
    NativeApplyUnavailable,
    WorkspaceApplyDelta,
    WorkspaceApplyReport,
    collect_python_workspace_apply,
    collect_rust_workspace_apply,
)
from aware_file_system.native_apply_benchmark import (
    NATIVE_APPLY_BENCHMARK_VERSION,
    NativeApplyBenchmarkReceipt,
    validate_native_apply_benchmark_receipt,
)
from aware_file_system.native_backend import (
    DEFAULT_NATIVE_MODULE,
    PYTHON_BACKEND_KIND,
    RUST_BACKEND_KIND,
    WORKSPACE_APPLY_DELTAS_OPERATION,
    FileSystemBackendCapabilities,
    active_backend_capabilities,
    supports_native_operation,
)


REQUIRED_NATIVE_APPLY_PARITY_FIELDS = (
    "entries",
    "bytes_written",
    "bytes_deleted",
    "digest_verified_count",
    "stored_artifact_count",
)


@dataclass(frozen=True, slots=True)
class NativeApplySelectorOptions:
    prefer_native: bool = False
    benchmark_receipt_path: Path | None = None
    require_benchmark_receipt: bool = True
    allow_python_fallback: bool = True
    module_name: str = DEFAULT_NATIVE_MODULE
    cargo_path: Path | None = None
    cargo_home: Path | None = None
    manifest_path: Path | None = None
    target_dir: Path | None = None
    prepared_binary_path: Path | None = None
    release: bool = False
    build_timeout_s: float = 240.0


@dataclass(frozen=True, slots=True)
class NativeApplySelectionResult:
    backend_kind: str
    report: WorkspaceApplyReport
    reason: str
    native_attempted: bool
    native_gate_passed: bool
    benchmark_receipt_path: str | None
    native_capabilities: FileSystemBackendCapabilities


class NativeApplySelectionError(RuntimeError):
    pass


def apply_workspace_deltas(
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    *,
    options: NativeApplySelectorOptions | None = None,
) -> NativeApplySelectionResult:
    resolved = options or NativeApplySelectorOptions()
    capabilities = active_backend_capabilities(
        prefer_native=resolved.prefer_native,
        module_name=resolved.module_name,
    )

    if not resolved.prefer_native:
        return _apply_python(
            root=root,
            deltas=deltas,
            capabilities=capabilities,
            reason="native apply preference is disabled; using Python apply",
            native_attempted=False,
            native_gate_passed=False,
            benchmark_receipt_path=None,
        )

    if not supports_native_operation(capabilities, WORKSPACE_APPLY_DELTAS_OPERATION):
        return _python_or_raise(
            root=root,
            deltas=deltas,
            options=resolved,
            capabilities=capabilities,
            reason=(
                "native apply capability gate failed: "
                f"{WORKSPACE_APPLY_DELTAS_OPERATION!r} is not supported "
                f"({capabilities.reason})"
            ),
            native_attempted=False,
            native_gate_passed=False,
            benchmark_receipt_path=None,
        )

    receipt: NativeApplyBenchmarkReceipt | None = None
    if resolved.require_benchmark_receipt:
        try:
            receipt = validate_native_apply_benchmark_receipt_path(
                resolved.benchmark_receipt_path
            )
        except NativeApplySelectionError as exc:
            return _python_or_raise(
                root=root,
                deltas=deltas,
                options=resolved,
                capabilities=capabilities,
                reason=f"native apply benchmark receipt gate failed: {exc}",
                native_attempted=False,
                native_gate_passed=False,
                benchmark_receipt_path=_optional_path_string(
                    resolved.benchmark_receipt_path
                ),
            )

    try:
        report = collect_rust_workspace_apply(
            root,
            deltas,
            cargo_path=resolved.cargo_path,
            cargo_home=resolved.cargo_home,
            manifest_path=resolved.manifest_path,
            target_dir=resolved.target_dir,
            prepared_binary_path=resolved.prepared_binary_path,
            release=resolved.release,
            build_timeout_s=resolved.build_timeout_s,
        )
        _validate_native_apply_report(report)
    except (NativeApplyUnavailable, NativeApplySelectionError) as exc:
        return _python_or_raise(
            root=root,
            deltas=deltas,
            options=resolved,
            capabilities=capabilities,
            reason=f"native apply failed after gate passed: {exc}",
            native_attempted=True,
            native_gate_passed=True,
            benchmark_receipt_path=_receipt_path(receipt, resolved),
        )

    return NativeApplySelectionResult(
        backend_kind=RUST_BACKEND_KIND,
        report=report,
        reason="native apply selected after capability and benchmark receipt gates",
        native_attempted=True,
        native_gate_passed=True,
        benchmark_receipt_path=_receipt_path(receipt, resolved),
        native_capabilities=capabilities,
    )


def validate_native_apply_benchmark_receipt_path(
    receipt_path: Path | None,
) -> NativeApplyBenchmarkReceipt:
    if receipt_path is None:
        raise NativeApplySelectionError(
            "benchmark_receipt_path is required for native apply selection"
        )
    resolved = receipt_path.expanduser().resolve()
    if not resolved.is_file():
        raise NativeApplySelectionError(
            f"benchmark receipt does not exist: {resolved.as_posix()}"
        )
    try:
        raw_receipt = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NativeApplySelectionError(
            f"benchmark receipt is not valid JSON: {resolved.as_posix()}"
        ) from exc
    if not isinstance(raw_receipt, Mapping):
        raise NativeApplySelectionError("benchmark receipt must be a JSON object")

    try:
        receipt = validate_native_apply_benchmark_receipt(raw_receipt)
    except ValueError as exc:
        raise NativeApplySelectionError(str(exc)) from exc

    if receipt.receipt_schema != NATIVE_APPLY_BENCHMARK_VERSION:
        raise NativeApplySelectionError(
            f"benchmark receipt schema mismatch: {receipt.receipt_schema!r}"
        )
    if receipt.rust_backend.backend_kind != RUST_BACKEND_KIND:
        raise NativeApplySelectionError("benchmark receipt must include Rust samples")
    if receipt.python_backend.backend_kind != PYTHON_BACKEND_KIND:
        raise NativeApplySelectionError("benchmark receipt must include Python samples")
    missing_fields = set(REQUIRED_NATIVE_APPLY_PARITY_FIELDS).difference(
        receipt.parity.checked_fields
    )
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise NativeApplySelectionError(
            f"benchmark receipt parity did not check required fields: {missing}"
        )
    return receipt


def _validate_native_apply_report(report: WorkspaceApplyReport) -> None:
    if report.backend_kind != RUST_BACKEND_KIND:
        raise NativeApplySelectionError(
            f"native apply report backend_kind mismatch: {report.backend_kind!r}"
        )
    if report.benchmark_version != WORKSPACE_FS_BENCHMARK_VERSION:
        raise NativeApplySelectionError(
            "native apply report benchmark version mismatch: "
            f"{report.benchmark_version!r}"
        )
    if report.operation != WORKSPACE_APPLY_DELTAS_OPERATION:
        raise NativeApplySelectionError(
            f"native apply report operation mismatch: {report.operation!r}"
        )
    if report.stored_artifact_count != 0:
        raise NativeApplySelectionError(
            "native apply selector v0 requires zero stored artifacts"
        )


def _apply_python(
    *,
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    capabilities: FileSystemBackendCapabilities,
    reason: str,
    native_attempted: bool,
    native_gate_passed: bool,
    benchmark_receipt_path: str | None,
) -> NativeApplySelectionResult:
    report = collect_python_workspace_apply(root, deltas)
    return NativeApplySelectionResult(
        backend_kind=PYTHON_BACKEND_KIND,
        report=report,
        reason=reason,
        native_attempted=native_attempted,
        native_gate_passed=native_gate_passed,
        benchmark_receipt_path=benchmark_receipt_path,
        native_capabilities=capabilities,
    )


def _python_or_raise(
    *,
    root: Path,
    deltas: Sequence[WorkspaceApplyDelta],
    options: NativeApplySelectorOptions,
    capabilities: FileSystemBackendCapabilities,
    reason: str,
    native_attempted: bool,
    native_gate_passed: bool,
    benchmark_receipt_path: str | None,
) -> NativeApplySelectionResult:
    if not options.allow_python_fallback:
        raise NativeApplySelectionError(reason)
    return _apply_python(
        root=root,
        deltas=deltas,
        capabilities=capabilities,
        reason=reason + "; using Python fallback",
        native_attempted=native_attempted,
        native_gate_passed=native_gate_passed,
        benchmark_receipt_path=benchmark_receipt_path,
    )


def _receipt_path(
    receipt: NativeApplyBenchmarkReceipt | None,
    options: NativeApplySelectorOptions,
) -> str | None:
    requested_path = _optional_path_string(options.benchmark_receipt_path)
    if requested_path is not None:
        return requested_path
    if receipt is not None and receipt.receipt_path is not None:
        return receipt.receipt_path
    return None


def _optional_path_string(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.expanduser().resolve().as_posix()
