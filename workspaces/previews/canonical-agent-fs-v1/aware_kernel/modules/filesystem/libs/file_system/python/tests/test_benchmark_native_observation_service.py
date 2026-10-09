from __future__ import annotations

from pathlib import Path

from aware_file_system.native_observation_service import (
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.scripts.benchmark_native_observation_service import (
    MAINTAINED_OBSERVATION_BENCHMARK_VERSION,
    run_maintained_observation_benchmark,
)


def test_maintained_observation_benchmark_records_noop_and_restart(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    target = tmp_path / "cargo-target"
    binary = prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=target)
    )

    receipt = run_maintained_observation_benchmark(
        workspace_root=root,
        binary_path=binary,
        cache_path=tmp_path / "state" / "observation.cache",
        warm_iterations=1,
        restart_iterations=1,
    )

    assert receipt["benchmark_version"] == MAINTAINED_OBSERVATION_BENCHMARK_VERSION
    assert receipt["exact_digest_stable"] is True
    assert len(receipt["all_snapshot_digests"]) == 1
    assert receipt["production_tail_eligible"] is False
    assert receipt["scenarios"]["cold_missing_cache"]["cache_write_count"] == 1
    assert receipt["scenarios"]["warm_same_process"]["cache_write_count"] == 0
    assert receipt["scenarios"]["warm_process_restart"]["cache_write_count"] == 0
    assert (
        receipt["scenarios"]["warm_process_restart"]["activation_duration_s"]["max"] > 0
    )
    assert (
        receipt["scenarios"]["warm_process_restart"]["ready_plus_observe_duration_s"][
            "max"
        ]
        >= receipt["scenarios"]["warm_process_restart"]["wall_duration_s"]["max"]
    )
    assert (
        receipt["scenarios"]["warm_process_restart"]["samples"][0]["cache_start_state"]
        == "loaded"
    )
