from __future__ import annotations

from pathlib import Path

from aware_file_system.native_observation_service import (
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.scripts.benchmark_observation_service_workload import (
    PERIODIC_AUDIT_WORKLOAD_SCHEMA,
    run_periodic_audit_workload,
)


def test_periodic_audit_workload_separates_background_scan_from_poll_tail(
    tmp_path: Path,
) -> None:
    binary = prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=tmp_path / "target")
    )
    receipt = run_periodic_audit_workload(
        binary_path=binary,
        scratch_root=tmp_path,
        file_count=64,
        audit_samples=3,
        baseline_samples=2,
        reconciliation_interval_s=0.1,
        poll_interval_s=0.001,
    )

    assert receipt["schema"] == PERIODIC_AUDIT_WORKLOAD_SCHEMA
    assert receipt["periodic_background"]["exact_completion_count"] == 3
    assert receipt["periodic_background"]["deadline_met"] is True
    assert receipt["final"]["python_parity"] is True
    assert receipt["final"]["orphan_process"] is False
    assert receipt["production_gate_passed"] is False
