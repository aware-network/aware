from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.scripts.benchmark_workspace_fs_workload import (  # noqa: E402
    WorkspaceFsWorkloadConfig,
    run_workspace_fs_workload,
)


def test_synthetic_workload_proves_mutation_and_recovery_semantics(
    tmp_path: Path,
) -> None:
    receipt = run_workspace_fs_workload(
        WorkspaceFsWorkloadConfig(
            fixture_root=tmp_path / "fixture",
            cache_dir=tmp_path / "cache",
            iterations=2,
            packages=1,
            files_per_package=2,
            include_cpu_pressure=False,
            include_contention=False,
        )
    )
    scenarios = {scenario["label"]: scenario for scenario in receipt["scenarios"]}

    assert scenarios["create_path"]["samples"][0]["added_count"] == 1
    assert scenarios["update_path"]["samples"][0]["modified_count"] == 1
    assert scenarios["rename_path"]["samples"][0]["added_count"] == 1
    assert scenarios["rename_path"]["samples"][0]["deleted_count"] == 1
    assert scenarios["delete_path"]["samples"][0]["deleted_count"] == 1
    assert scenarios["ignore_policy_admit"]["samples"][0]["added_count"] == 1
    assert scenarios["ignore_policy_exclude"]["samples"][0]["deleted_count"] == 1
    recovery = scenarios["corrupt_cache_recovery"]
    assert recovery["failure_count"] == 0
    assert recovery["exact_inventory_stable"] is True
    assert recovery["tail_claim_eligible"] is False
    assert recovery["summary"]["duration_s"]["p99"] is not None


def test_real_workload_is_readonly_and_covers_tail_scenarios(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    source = root / "docs" / "source.aware"
    source.parent.mkdir(parents=True)
    source.write_text("class Source {}\n", encoding="utf-8")
    (root / "aware.workspace.toml").write_text("[workspace]\n", encoding="utf-8")
    before = _file_contents(root)

    receipt = run_workspace_fs_workload(
        WorkspaceFsWorkloadConfig(
            workspace_root=root,
            cache_dir=tmp_path / "cache",
            receipt_dir=tmp_path / "receipts",
            iterations=2,
            concurrency=2,
            include_cpu_pressure=False,
            write_receipt=True,
        )
    )
    scenarios = {scenario["label"]: scenario for scenario in receipt["scenarios"]}

    assert _file_contents(root) == before
    assert set(scenarios) == {
        "cold_clean",
        "warm_session_noop",
        "warm_process_restart",
        "cold_detailed_timings_off",
        "concurrent_cold_isolated_cache",
        "corrupt_cache_recovery",
    }
    assert scenarios["cold_clean"]["success_count"] == 2
    assert scenarios["concurrent_cold_isolated_cache"]["success_count"] == 4
    assert (
        scenarios["cold_detailed_timings_off"]["samples"][0]["phase_timings_s"][
            "filter"
        ]
        == 0.0
    )
    assert (
        scenarios["cold_detailed_timings_off"]["samples"][0]["phase_timings_s"]["stat"]
        == 0.0
    )
    assert Path(receipt["receipt_path"]).is_file()
    assert json.loads(Path(receipt["receipt_path"]).read_text()) == receipt


def _file_contents(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
