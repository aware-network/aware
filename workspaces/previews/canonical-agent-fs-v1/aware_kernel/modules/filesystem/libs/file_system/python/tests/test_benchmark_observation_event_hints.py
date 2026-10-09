from __future__ import annotations

from pathlib import Path

from aware_file_system.native_observation_service import (
    RustObservationServiceBuildConfig,
    prepare_rust_observation_service_binary,
)
from aware_file_system.scripts.benchmark_observation_event_hints import (
    DIRTY_PATH_BENCHMARK_VERSION,
    EVENT_HINT_BENCHMARK_VERSION,
    LINUX_SHADOW_GATE_VERSION,
    evaluate_linux_shadow_gate,
    run_dirty_path_canonical_file_set_benchmark,
    run_event_hint_canonical_file_set_pressure_benchmark,
    run_event_hint_idle_benchmark,
    run_event_hint_mutation_benchmark,
)


def test_event_hint_idle_benchmark_proves_traversal_free_polling(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    binary = prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=tmp_path / "target")
    )
    receipt = run_event_hint_idle_benchmark(
        workspace_root=root,
        binary_path=binary,
        cache_path=tmp_path / "state.cache",
        idle_iterations=3,
    )

    assert receipt["benchmark_version"] == EVENT_HINT_BENCHMARK_VERSION
    assert receipt["traversal_free"] is True
    assert receipt["exact_digest_stable"] is True
    assert receipt["distribution_sample_eligible"] is False
    assert receipt["idle"]["traversal_free_count"] == 3
    assert receipt["idle"]["cache_write_count"] == 0
    assert receipt["watcher_health"]["state"] == "active"


def test_linux_shadow_gate_requires_full_distributions() -> None:
    receipt = {
        "activation_duration_s": 0.001,
        "startup": {"wall_duration_s": 0.5},
        "watcher_activation_duration_s": 0.6,
        "watcher_health": {
            "watched_directory_count": 1,
            "total_error_count": 0,
        },
        "idle": {
            "sample_count": 3,
            "wall_duration_s": {"p99": 0.001},
        },
        "mutation_fixture": {
            "sample_count": 3,
            "success_count": 3,
            "event_to_exact_duration_s": {"p99": 0.003},
        },
        "canonical_file_set_pressure": {
            "mutation_sample_count": 3,
            "success_count": 3,
            "event_to_exact_duration_s": {"p99": 0.7, "max": 0.8},
            "watcher_health": {"total_error_count": 0},
        },
    }

    gate = evaluate_linux_shadow_gate(receipt)

    assert gate["schema"] == LINUX_SHADOW_GATE_VERSION
    assert gate["passed"] is False
    assert gate["checks"]["idle_sample_count"] is False
    assert gate["production_route_authorized"] is False


def test_event_hint_mutation_benchmark_converges_exactly(tmp_path: Path) -> None:
    binary = prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=tmp_path / "target")
    )
    receipt = run_event_hint_mutation_benchmark(
        binary_path=binary,
        scratch_root=tmp_path / "scratch",
        mutation_iterations=3,
    )

    assert receipt["sample_count"] == 3
    assert receipt["success_count"] == 3
    assert receipt["distribution_sample_eligible"] is False
    assert receipt["watcher_health"]["state"] == "active"


def test_canonical_file_set_pressure_benchmark_preserves_exact_deltas(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    (root / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    binary = prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=tmp_path / "target")
    )

    receipt = run_event_hint_canonical_file_set_pressure_benchmark(
        source_workspace_root=root,
        binary_path=binary,
        scratch_root=tmp_path / "scratch",
        mutation_iterations=3,
        churn_width=4,
        pressure_workers=1,
    )

    assert receipt["source_snapshot_entry_count"] == 2
    assert receipt["mutation_sample_count"] == 3
    assert receipt["success_count"] == 3
    assert receipt["distribution_sample_eligible"] is False
    assert receipt["watcher_health"]["state"] == "active"


def test_dirty_path_canonical_file_set_benchmark_proves_scoped_oracle_parity(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "source.txt").write_text("source\n", encoding="utf-8")
    (root / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
    binary = prepare_rust_observation_service_binary(
        RustObservationServiceBuildConfig(target_dir=tmp_path / "target")
    )

    receipt = run_dirty_path_canonical_file_set_benchmark(
        source_workspace_root=root,
        binary_path=binary,
        scratch_root=tmp_path / "scratch",
        probe_relative_path="source.txt",
        mutation_iterations=3,
        pressure_workers=0,
    )

    assert receipt["schema"] == DIRTY_PATH_BENCHMARK_VERSION
    assert receipt["mutation_sample_count"] == 3
    assert receipt["success_count"] == 3
    assert receipt["directories_scanned"]["max"] == 0
    assert receipt["files_seen"]["max"] == 1
    assert receipt["final_digest_exact"] is True
    assert receipt["journal_append_count"] == 3
    assert receipt["checkpoint_count"] == 0
    assert receipt["ordinary_journal_append"]["sample_count"] == 3
    assert receipt["checkpoint"]["sample_count"] == 0
    assert receipt["checkpoint"]["sample_indices"] == []
    assert receipt["journal_frame_count"]["max"] == 3
    assert receipt["digest_backend_kinds"] == ["rustcrypto_sha2_asm_optimized"]
    assert receipt["watcher_health"]["state"] == "active"
