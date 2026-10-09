from __future__ import annotations

from copy import deepcopy
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.benchmark_receipt_contract import (  # noqa: E402
    BenchmarkReceiptContractError,
)
from aware_file_system.scripts.benchmark_workspace_fs_workload import (  # noqa: E402
    WorkspaceFsWorkloadConfig,
    run_workspace_fs_workload,
)
from aware_file_system.workload_receipt_contract import (  # noqa: E402
    WORKSPACE_FS_WORKLOAD_VERSION,
    validate_workspace_fs_workload_receipt,
    workspace_fs_workload_receipt_json_schema,
)


def test_workload_contract_accepts_synthetic_receipt_and_exports_schema(
    tmp_path: Path,
) -> None:
    receipt = _receipt(tmp_path)

    validated = validate_workspace_fs_workload_receipt(receipt)
    schema = workspace_fs_workload_receipt_json_schema()

    assert validated.workload_version == WORKSPACE_FS_WORKLOAD_VERSION
    assert validated.mode == "synthetic_mutating"
    assert schema["properties"]["workload_version"]["const"] == (
        WORKSPACE_FS_WORKLOAD_VERSION
    )


def test_workload_contract_rejects_false_inventory_stability(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path)
    broken = deepcopy(receipt)
    broken["scenarios"][0]["exact_inventory_stable"] = False

    with pytest.raises(BenchmarkReceiptContractError, match="disagrees"):
        validate_workspace_fs_workload_receipt(broken)


def test_workload_contract_rejects_real_source_mutation(tmp_path: Path) -> None:
    receipt = _receipt(tmp_path)
    broken = deepcopy(receipt)
    broken["mode"] = "real_workspace_readonly"
    broken["source_mutation"] = True

    with pytest.raises(BenchmarkReceiptContractError, match="cannot mutate source"):
        validate_workspace_fs_workload_receipt(broken)


def _receipt(tmp_path: Path) -> dict[str, object]:
    return run_workspace_fs_workload(
        WorkspaceFsWorkloadConfig(
            fixture_root=tmp_path / "fixture",
            cache_dir=tmp_path / "cache",
            iterations=1,
            packages=1,
            files_per_package=1,
            include_cpu_pressure=False,
            include_contention=False,
        )
    )
