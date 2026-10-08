from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Mapping

from aware_file_system.benchmark_receipt_contract import (
    WORKSPACE_FS_BENCHMARK_VERSION,
)


DEFAULT_NATIVE_MODULE = "aware_file_system_native"
PYTHON_BACKEND_KIND = "python"
RUST_BACKEND_KIND = "rust"
SCAFFOLD_OPERATION = "capability_report"
WORKSPACE_SNAPSHOT_OPERATION = "workspace_snapshot"
WORKSPACE_HASHES_OPERATION = "workspace_hashes"
WORKSPACE_APPLY_DELTAS_OPERATION = "workspace_apply_deltas"


@dataclass(frozen=True, slots=True)
class FileSystemBackendCapabilities:
    active_backend_kind: str
    native_backend_kind: str
    native_available: bool
    module_name: str
    backend_version: str | None
    benchmark_version: str
    supported_operations: tuple[str, ...]
    parity_required_before_performance: bool
    reason: str


def detect_native_backend(
    *,
    module_name: str = DEFAULT_NATIVE_MODULE,
) -> FileSystemBackendCapabilities:
    try:
        native_module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise
        return _python_fallback_capabilities(
            module_name=module_name,
            reason="native backend module is not installed",
        )

    return capabilities_from_native_module(
        native_module,
        module_name=module_name,
    )


def capabilities_from_native_module(
    native_module: ModuleType,
    *,
    module_name: str = DEFAULT_NATIVE_MODULE,
) -> FileSystemBackendCapabilities:
    raw_capabilities = _load_raw_capabilities(native_module)
    backend_kind = str(raw_capabilities.get("backend_kind", ""))
    benchmark_version = str(raw_capabilities.get("benchmark_version", ""))
    supported_operations = _string_tuple(raw_capabilities.get("supported_operations"))
    backend_version = raw_capabilities.get("backend_version")
    reason = str(raw_capabilities.get("reason", "native backend capability report loaded"))

    if backend_kind != RUST_BACKEND_KIND:
        return _python_fallback_capabilities(
            module_name=module_name,
            reason=f"native backend_kind must be {RUST_BACKEND_KIND!r}",
        )
    if benchmark_version != WORKSPACE_FS_BENCHMARK_VERSION:
        return _python_fallback_capabilities(
            module_name=module_name,
            reason="native benchmark contract version does not match Python",
        )
    if SCAFFOLD_OPERATION not in supported_operations:
        return _python_fallback_capabilities(
            module_name=module_name,
            reason=f"native backend must support {SCAFFOLD_OPERATION!r}",
        )

    return FileSystemBackendCapabilities(
        active_backend_kind=RUST_BACKEND_KIND,
        native_backend_kind=RUST_BACKEND_KIND,
        native_available=True,
        module_name=module_name,
        backend_version=str(backend_version) if backend_version is not None else None,
        benchmark_version=benchmark_version,
        supported_operations=supported_operations,
        parity_required_before_performance=True,
        reason=reason,
    )


def active_backend_capabilities(
    *,
    prefer_native: bool = True,
    module_name: str = DEFAULT_NATIVE_MODULE,
) -> FileSystemBackendCapabilities:
    if not prefer_native:
        return _python_fallback_capabilities(
            module_name=module_name,
            reason="native backend preference is disabled",
        )
    return detect_native_backend(module_name=module_name)


def supports_native_operation(
    capabilities: FileSystemBackendCapabilities,
    operation: str,
) -> bool:
    return capabilities.native_available and operation in capabilities.supported_operations


def _load_raw_capabilities(native_module: ModuleType) -> Mapping[str, Any]:
    capability_loader = getattr(native_module, "capabilities", None)
    if callable(capability_loader):
        raw_capabilities = capability_loader()
    else:
        raw_capabilities = getattr(native_module, "CAPABILITIES", None)
    if not isinstance(raw_capabilities, Mapping):
        return {}
    return raw_capabilities


def _python_fallback_capabilities(
    *,
    module_name: str,
    reason: str,
) -> FileSystemBackendCapabilities:
    return FileSystemBackendCapabilities(
        active_backend_kind=PYTHON_BACKEND_KIND,
        native_backend_kind=RUST_BACKEND_KIND,
        native_available=False,
        module_name=module_name,
        backend_version=None,
        benchmark_version=WORKSPACE_FS_BENCHMARK_VERSION,
        supported_operations=("python_fallback",),
        parity_required_before_performance=True,
        reason=reason,
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value)
