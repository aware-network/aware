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
    SYNTHETIC_RUN_LABELS,
    assert_workspace_fs_benchmark_parity,
    validate_workspace_fs_benchmark_receipt,
    workspace_fs_benchmark_receipt_json_schema,
)
from aware_file_system.scripts.benchmark_workspace_fs import (  # noqa: E402
    WorkspaceFsBenchmarkConfig,
    run_workspace_fs_benchmark,
)


def test_contract_accepts_python_synthetic_receipt_and_exports_schema(
    tmp_path: Path,
) -> None:
    receipt = _synthetic_receipt(tmp_path)

    validated = validate_workspace_fs_benchmark_receipt(receipt)
    assert validated.backend_kind == "python"
    assert tuple(run.label for run in validated.runs) == SYNTHETIC_RUN_LABELS

    schema = workspace_fs_benchmark_receipt_json_schema()
    assert schema["properties"]["benchmark_version"]["const"] == (
        "aware.file_system.workspace_fs_benchmark.v1"
    )
    assert set(schema["properties"]) >= {
        "backend_kind",
        "mode",
        "iteration_count",
        "fixture",
        "runs",
    }


def test_contract_rejects_missing_synthetic_run_label(tmp_path: Path) -> None:
    receipt = _synthetic_receipt(tmp_path)
    receipt["runs"] = receipt["runs"][:-1]

    with pytest.raises(BenchmarkReceiptContractError, match="run labels"):
        validate_workspace_fs_benchmark_receipt(receipt)


def test_backend_parity_allows_backend_timings_to_differ(tmp_path: Path) -> None:
    reference = _synthetic_receipt(tmp_path)
    candidate = _rust_candidate(reference)
    for run in candidate["runs"]:
        run["duration_s"] += 100.0
        run["scanner_scan_time_s"] += 100.0
        run["hash_duration_s"] += 100.0
        for sample in run["samples"]:
            sample["duration_s"] += 100.0
            sample["scanner_scan_time_s"] += 100.0
            sample["hash_duration_s"] += 100.0

    report = assert_workspace_fs_benchmark_parity(
        reference=reference,
        candidate=candidate,
    )

    assert report.passed is True
    assert report.reference_backend_kind == "python"
    assert report.candidate_backend_kind == "rust"
    assert "runs.*.current_file_count" in report.checked_fields


def test_backend_parity_fails_on_semantic_mismatch(tmp_path: Path) -> None:
    reference = _synthetic_receipt(tmp_path)
    candidate = _rust_candidate(reference)
    candidate["runs"][0]["current_file_count"] += 1

    with pytest.raises(
        BenchmarkReceiptContractError,
        match="runs.cold_force_refresh.current_file_count",
    ):
        assert_workspace_fs_benchmark_parity(
            reference=reference,
            candidate=candidate,
        )


def test_backend_parity_fails_on_hash_mismatch(tmp_path: Path) -> None:
    reference = _synthetic_receipt(tmp_path)
    candidate = _rust_candidate(reference)
    first_hash_path = next(iter(candidate["runs"][0]["hashes"]))
    candidate["runs"][0]["hashes"][first_hash_path] = "0" * 64

    with pytest.raises(
        BenchmarkReceiptContractError,
        match="runs.cold_force_refresh.hashes",
    ):
        assert_workspace_fs_benchmark_parity(
            reference=reference,
            candidate=candidate,
        )


def _synthetic_receipt(tmp_path: Path) -> dict[str, object]:
    return run_workspace_fs_benchmark(
        WorkspaceFsBenchmarkConfig(
            packages=2,
            files_per_package=3,
            payload_bytes=96,
            iterations=2,
            fixture_root=tmp_path / "fixture",
            cache_dir=tmp_path / "cache",
        )
    )


def _rust_candidate(receipt: dict[str, object]) -> dict[str, object]:
    candidate = deepcopy(receipt)
    candidate["backend_kind"] = "rust"
    candidate["workspace_root"] = "/native/fixture/root"
    candidate["cache_dir"] = "/native/cache/root"
    return candidate
