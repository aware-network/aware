from __future__ import annotations

from pathlib import Path

import pytest

from aware_file_system.native_observation_service import (
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.observation_workload_receipt_contract import (
    REQUIRED_RECOVERY_CHECKS,
    REQUIRED_SCENARIOS,
    evaluate_observation_workload_receipt,
    validate_observation_workload_receipt,
)
from aware_file_system.scripts.benchmark_observation_production_workload import (
    run_observation_production_workload,
)


@pytest.fixture(scope="module")
def production_workload_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(
            target_dir=tmp_path_factory.mktemp("production-workload-target")
        )
    )


def test_small_workload_exercises_complete_fail_closed_scenario_set(
    tmp_path: Path,
    production_workload_binary: Path,
) -> None:
    bundle = run_observation_production_workload(
        binary_path=production_workload_binary,
        scratch_root=tmp_path,
        file_count=128,
        samples=1,
        burst_size=2,
        periodic_interval_s=0.1,
        recovery_restarts=1,
    )
    evidence = bundle["evidence"]
    parsed = validate_observation_workload_receipt(evidence)
    decision = evaluate_observation_workload_receipt(evidence)

    assert bundle["bundle_schema"].endswith("production_admission.v1")
    assert {scenario.name for scenario in parsed.scenarios} == set(
        REQUIRED_SCENARIOS
    )
    assert all(
        sample.exact for scenario in parsed.scenarios for sample in scenario.samples
    )
    assert parsed.recovery_checks.keys() == REQUIRED_RECOVERY_CHECKS
    assert all(parsed.recovery_checks.values())
    assert parsed.final.python_parity is True
    assert parsed.final.orphan_process_ids == []
    assert parsed.final.leaked_reader_threads == []
    assert decision == bundle["admission"]
    assert decision["admitted"] is False
    assert any("fixture has 128 files" in failure for failure in decision["failures"])
    assert any(
        "insufficient successful samples" in failure
        for failure in decision["failures"]
    )


def test_workload_rejects_invalid_inputs(
    tmp_path: Path,
    production_workload_binary: Path,
) -> None:
    with pytest.raises(ValueError, match="file_count"):
        run_observation_production_workload(
            binary_path=production_workload_binary,
            scratch_root=tmp_path,
            file_count=127,
        )
