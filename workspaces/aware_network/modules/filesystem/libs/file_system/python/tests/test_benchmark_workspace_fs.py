from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.scripts.benchmark_workspace_fs import (  # noqa: E402
    BENCHMARK_VERSION,
    WorkspaceFsBenchmarkConfig,
    run_workspace_fs_benchmark,
)


def test_workspace_fs_benchmark_emits_python_baseline_receipt(tmp_path: Path) -> None:
    receipt = run_workspace_fs_benchmark(
        WorkspaceFsBenchmarkConfig(
            packages=2,
            files_per_package=3,
            payload_bytes=96,
            iterations=3,
            fixture_root=tmp_path / "fixture",
            cache_dir=tmp_path / "cache",
        )
    )

    assert receipt["benchmark_version"] == BENCHMARK_VERSION
    assert receipt["backend_kind"] == "python"
    assert receipt["mode"] == "synthetic_fixture"
    assert receipt["iteration_count"] == 3
    assert receipt["fixture"]["expected_tracked_file_count"] == 9
    runs = {run["label"]: run for run in receipt["runs"]}
    assert set(runs) == {
        "cold_force_refresh",
        "warm_noop_session_cache",
        "one_file_edit_metadata_hash",
    }

    cold = runs["cold_force_refresh"]
    assert cold["iteration_count"] == 3
    assert cold["current_file_count"] == 9
    assert cold["total_changes"] == 9
    assert cold["hashed_path_count"] == 9
    assert cold["summary"]["duration_s"]["count"] == 3
    assert [sample["iteration_index"] for sample in cold["samples"]] == [0, 1, 2]

    warm = runs["warm_noop_session_cache"]
    assert warm["iteration_count"] == 3
    assert warm["current_file_count"] == 9
    assert warm["total_changes"] == 0
    assert warm["hashed_path_count"] == 0
    assert warm["summary"]["cache_hit_ratio"]["count"] == 3

    edit = runs["one_file_edit_metadata_hash"]
    assert edit["iteration_count"] == 3
    assert edit["current_file_count"] == 9
    assert edit["total_changes"] == 1
    assert edit["modified_count"] == 1
    assert edit["hashed_path_count"] == 1
    assert edit["summary"]["hash_duration_s"]["count"] == 3
    assert receipt["fixture"]["edit_target"] in edit["hashes"]


def test_workspace_fs_benchmark_writes_receipt_file(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture"
    receipt = run_workspace_fs_benchmark(
        WorkspaceFsBenchmarkConfig(
            packages=1,
            files_per_package=1,
            payload_bytes=96,
            iterations=2,
            fixture_root=fixture_root,
            cache_dir=tmp_path / "cache",
            write_receipt=True,
        )
    )

    receipt_path = Path(receipt["receipt_path"])
    assert receipt_path.parent == (
        fixture_root / ".aware" / "reports" / "file_system" / "performance"
    )
    assert receipt_path.is_file()
    stored = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert stored == receipt


def test_workspace_fs_benchmark_real_workspace_mode_is_readonly(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    source_file = (
        workspace_root
        / "modules"
        / "bench"
        / "structure"
        / "ontology"
        / "aware"
        / "bench"
        / "item.aware"
    )
    source_file.parent.mkdir(parents=True)
    (workspace_root / "aware.workspace.toml").write_text(
        "[workspace]\nname = \"real-fs-benchmark\"\n",
        encoding="utf-8",
    )
    package_toml = (
        workspace_root / "modules" / "bench" / "structure" / "ontology" / "aware.toml"
    )
    package_toml.write_text(
        "[package]\npackage_name = \"bench\"\nkind = \"ontology\"\n",
        encoding="utf-8",
    )
    source_file.write_text("class Item {\n    name String\n}\n", encoding="utf-8")
    before = _workspace_file_contents(workspace_root)

    receipt = run_workspace_fs_benchmark(
        WorkspaceFsBenchmarkConfig(
            iterations=2,
            workspace_root=workspace_root,
            cache_dir=tmp_path / "real-cache",
        )
    )

    assert _workspace_file_contents(workspace_root) == before
    assert receipt["mode"] == "real_workspace_readonly"
    assert receipt["iteration_count"] == 2
    assert receipt["fixture"]["source_mutation"] is False
    runs = {run["label"]: run for run in receipt["runs"]}
    assert set(runs) == {"cold_force_refresh", "warm_noop_session_cache"}
    assert runs["cold_force_refresh"]["iteration_count"] == 2
    assert runs["cold_force_refresh"]["current_file_count"] == 3
    assert runs["cold_force_refresh"]["hashed_path_count"] == 0
    assert runs["warm_noop_session_cache"]["total_changes"] == 0


def test_workspace_fs_benchmark_rejects_non_empty_fixture_root(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixture"
    fixture_root.mkdir()
    (fixture_root / "existing.txt").write_text("do not overwrite\n", encoding="utf-8")

    try:
        run_workspace_fs_benchmark(
            WorkspaceFsBenchmarkConfig(
                packages=1,
                files_per_package=1,
                fixture_root=fixture_root,
            )
        )
    except ValueError as exc:
        assert "must be empty" in str(exc)
    else:
        raise AssertionError("expected non-empty fixture root to be rejected")


def _workspace_file_contents(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
