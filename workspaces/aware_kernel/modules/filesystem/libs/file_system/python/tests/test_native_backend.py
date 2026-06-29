from __future__ import annotations

import sys
from types import ModuleType
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.benchmark_receipt_contract import (  # noqa: E402
    WORKSPACE_FS_BENCHMARK_VERSION,
)
from aware_file_system.native_backend import (  # noqa: E402
    WORKSPACE_HASHES_OPERATION,
    WORKSPACE_SNAPSHOT_OPERATION,
    active_backend_capabilities,
    capabilities_from_native_module,
    detect_native_backend,
    supports_native_operation,
)


def test_missing_native_backend_uses_python_fallback() -> None:
    capabilities = detect_native_backend(module_name="_aware_missing_native_backend")

    assert capabilities.active_backend_kind == "python"
    assert capabilities.native_backend_kind == "rust"
    assert capabilities.native_available is False
    assert capabilities.benchmark_version == WORKSPACE_FS_BENCHMARK_VERSION
    assert capabilities.supported_operations == ("python_fallback",)
    assert capabilities.parity_required_before_performance is True


def test_active_backend_can_disable_native_preference() -> None:
    capabilities = active_backend_capabilities(
        prefer_native=False,
        module_name="_aware_missing_native_backend",
    )

    assert capabilities.active_backend_kind == "python"
    assert capabilities.native_available is False
    assert capabilities.reason == "native backend preference is disabled"


def test_native_backend_capability_report_can_activate_rust() -> None:
    native_module = ModuleType("aware_file_system_native")

    def capabilities() -> dict[str, object]:
        return {
            "backend_kind": "rust",
            "backend_version": "0.1.0",
            "benchmark_version": WORKSPACE_FS_BENCHMARK_VERSION,
            "supported_operations": [
                "capability_report",
                "workspace_snapshot",
                "workspace_hashes",
            ],
            "reason": "scaffold loaded",
        }

    native_module.capabilities = capabilities  # type: ignore[attr-defined]

    report = capabilities_from_native_module(native_module)

    assert report.active_backend_kind == "rust"
    assert report.native_available is True
    assert report.backend_version == "0.1.0"
    assert report.supported_operations == (
        "capability_report",
        "workspace_snapshot",
        "workspace_hashes",
    )
    assert supports_native_operation(report, WORKSPACE_SNAPSHOT_OPERATION)
    assert supports_native_operation(report, WORKSPACE_HASHES_OPERATION)


def test_native_backend_contract_mismatch_falls_back_to_python() -> None:
    native_module = ModuleType("aware_file_system_native")
    native_module.CAPABILITIES = {
        "backend_kind": "rust",
        "backend_version": "0.1.0",
        "benchmark_version": "wrong",
        "supported_operations": ["capability_report"],
    }

    report = capabilities_from_native_module(native_module)

    assert report.active_backend_kind == "python"
    assert report.native_available is False
    assert report.reason == "native benchmark contract version does not match Python"
