from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from aware_file_system.native_observation_service import (
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.observation_platform_contract import PLATFORM_RECEIPT_SCHEMA
from aware_file_system.scripts.benchmark_observation_resilience import (
    OBSERVATION_RESILIENCE_SCHEMA,
    run_cache_fault_recovery,
    run_crash_restart_soak,
    run_journal_tail_recovery,
    run_journal_checkpoint_recovery,
    run_linux_resilience_benchmark,
    run_multi_repository_capacity,
    run_portable_mutation_recovery,
    run_portable_resilience_benchmark,
    run_reconciliation_only_recovery,
)


@pytest.fixture(scope="module")
def observation_service_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(
            target_dir=tmp_path_factory.mktemp("resilience-target")
        )
    )


def test_multi_repository_capacity_preserves_independent_exact_deltas(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    receipt = run_multi_repository_capacity(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
        repository_count=2,
        directories_per_repository=3,
    )

    assert receipt["repository_count"] == 2
    assert receipt["exact_mutation_count"] == 2
    assert receipt["watched_directories"] >= 8
    assert receipt["orphan_process_ids"] == []
    assert all(health["state"] == "active" for health in receipt["watcher_health"])


def test_crash_restart_soak_preserves_digest_without_leaks(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    receipt = run_crash_restart_soak(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
        restart_iterations=3,
        fixture_file_count=4,
    )

    assert receipt["restart_sample_count"] == 3
    assert receipt["success_count"] == 3
    assert receipt["orphan_process_ids"] == []
    assert receipt["leaked_reader_threads"] == []


def test_portable_mutations_and_receipt_are_exact_but_do_not_self_authorize(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    mutations = run_portable_mutation_recovery(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
        burst_file_count=4,
    )
    assert mutations["passed"] is True
    assert [step["label"] for step in mutations["steps"]] == [
        "create",
        "update",
        "rename",
        "atomic_replace",
        "delete",
        "burst_create",
    ]

    binary_sha256 = hashlib.sha256(observation_service_binary.read_bytes()).hexdigest()
    package_manifest = tmp_path / "package.json"
    package_manifest.write_text(
        json.dumps(
            {
                "target_triple": "test-host",
                "binary_sha256": binary_sha256,
                "service_protocol": (
                    "aware.file_system.maintained_observation_service.v2"
                ),
                "runtime_verification": {"passed": True},
                "evidence_coordinate": {
                    "source_revision": "a" * 40,
                    "run_id": "test-run",
                },
            }
        ),
        encoding="utf-8",
    )
    receipt = run_portable_resilience_benchmark(
        binary_path=observation_service_binary,
        package_manifest_path=package_manifest,
        scratch_root=tmp_path,
        repository_count=2,
        directories_per_repository=2,
        restart_iterations=2,
        burst_file_count=4,
        source_revision="a" * 40,
        evidence_run_id="test-run",
    )
    assert receipt["schema"] == PLATFORM_RECEIPT_SCHEMA
    assert receipt["platform"]["architecture_class"] in {
        "x86_64",
        "arm64",
        "unsupported",
    }
    assert receipt["supported_platform_class"] is None
    assert receipt["portable_mutations"]["passed"] is True
    assert receipt["evidence_coordinate"] == {
        "source_revision": "a" * 40,
        "run_id": "test-run",
    }
    assert receipt["platform_gate"]["passed"] is False
    assert receipt["platform_gate"]["production_route_authorized"] is False
    assert receipt["production_gate_passed"] is False


def test_reconciliation_only_recovery_is_exact_without_watches(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    receipt = run_reconciliation_only_recovery(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
    )

    assert receipt["health"]["state"] == "reconciliation_only"
    assert receipt["health"]["watched_directory_count"] == 0
    assert receipt["unchanged_exact"] is True
    assert receipt["changed_exact"] is True


def test_cache_fault_recovery_removes_stale_temp_and_rebuilds_truncation(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    receipt = run_cache_fault_recovery(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
    )

    assert receipt["interrupted_temp"] == {
        "cache_start_state": "loaded",
        "stale_cache_temp_files_removed": 1,
        "temp_removed": True,
        "snapshot_digest_stable": True,
    }
    assert receipt["truncated_cache"] == {
        "cache_start_state": "corrupt",
        "cache_written": True,
        "snapshot_digest_stable": True,
    }


def test_journal_tail_recovery_restores_last_complete_generation(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    receipt = run_journal_tail_recovery(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
    )

    assert receipt["passed"] is True
    assert receipt["second_generation"] == receipt["first_generation"] + 1
    assert receipt["recovered_generation"] == receipt["first_generation"]
    assert receipt["recovered_journal_bytes"] == receipt["first_journal_bytes"]
    assert receipt["tail_bytes_removed"] == receipt["expected_tail_bytes_removed"]
    assert receipt["digest_stable"] is True


def test_journal_checkpoint_recovery_replaces_base_and_restarts_exactly(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    receipt = run_journal_checkpoint_recovery(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
    )

    assert receipt["passed"] is True
    assert receipt["mutation_sample_count"] == 128
    assert receipt["journal_append_count"] == 127
    assert receipt["checkpoint_count"] == 1
    assert receipt["checkpoint_sample_indices"] == [127]
    assert receipt["maximum_journal_frame_count"] == 127
    assert receipt["journal_bytes_after_checkpoint"] == 0
    assert receipt["recovered_generation"] == receipt["checkpoint_generation"]
    assert receipt["digest_stable"] is True


@pytest.mark.skipif(os.name == "nt", reason="Linux gate uses SIGKILL and /proc")
def test_linux_resilience_gate_requires_full_scale_distributions(
    tmp_path: Path,
    observation_service_binary: Path,
) -> None:
    receipt = run_linux_resilience_benchmark(
        binary_path=observation_service_binary,
        scratch_root=tmp_path,
        repository_count=2,
        directories_per_repository=2,
        restart_iterations=2,
    )

    assert receipt["schema"] == OBSERVATION_RESILIENCE_SCHEMA
    assert receipt["linux_resilience_gate"]["passed"] is False
    assert receipt["linux_resilience_gate"]["checks"]["four_distinct_roots"] is False
    assert receipt["production_gate_passed"] is False
