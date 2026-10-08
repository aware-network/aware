from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from aware_file_system.config import (  # noqa: E402
    CanonicalSourceFilterConfig,
    Config,
    FileSystemConfig,
    FilterConfig,
)
from aware_file_system.index.incremental_scanner import IncrementalScanner  # noqa: E402
from aware_file_system.index.file_metadata_cached import (  # noqa: E402
    FileMetadataCached,
)


def _build_scanner(
    root: Path,
    *,
    filter_config: FilterConfig | None = None,
) -> IncrementalScanner:
    config = Config(
        file_system=FileSystemConfig(
            root_path=str(root), generate_tree=False, export_json=False
        ),
        filter=filter_config or FilterConfig(max_file_size=None),
    )
    return IncrementalScanner(config)


def test_detailed_timing_can_be_disabled_without_changing_scan_semantics(
    tmp_path: Path,
) -> None:
    target = tmp_path / "nested" / "sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('timing')\n", encoding="utf-8")
    config = Config(
        file_system=FileSystemConfig(
            root_path=str(tmp_path), generate_tree=False, export_json=False
        ),
        filter=FilterConfig(max_file_size=None),
    )

    scanner = IncrementalScanner(
        config,
        cache_dir=str(tmp_path / ".timing-cache"),
        collect_detailed_timings=False,
    )
    result = scanner.scan_incremental(use_session_cache=False)

    assert set(result.added) == {"nested/sample.py"}
    assert result.phase_timings_s["filter"] == 0.0
    assert result.phase_timings_s["stat"] == 0.0


def test_scan_incremental_skips_iterdir_for_unchanged_cached_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "nested" / "sample.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('ok')\n", encoding="utf-8")

    first_scanner = _build_scanner(tmp_path)
    first_result = first_scanner.scan_incremental(use_session_cache=False)
    assert first_result.total_changes == 1

    second_scanner = _build_scanner(tmp_path)
    original_iterdir = Path.iterdir
    root_path = tmp_path.resolve()

    def _guarded_iterdir(self: Path):  # type: ignore[no-untyped-def]
        if self.resolve() == root_path:
            raise AssertionError("unchanged cached root should not be enumerated")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", _guarded_iterdir)

    second_result = second_scanner.scan_incremental(use_session_cache=False)

    assert second_result.total_changes == 0


def test_process_restart_uses_exact_mtime_witness_for_unchanged_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "nested" / "sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('restart')\n", encoding="utf-8")
    cache_dir = tmp_path / ".aware" / "restart-cache"
    config = Config(
        file_system=FileSystemConfig(
            root_path=str(tmp_path), generate_tree=False, export_json=False
        ),
        filter=FilterConfig(max_file_size=None),
    )
    first = IncrementalScanner(config, cache_dir=str(cache_dir))
    first.scan_incremental(use_session_cache=False)
    restarted = IncrementalScanner(config, cache_dir=str(cache_dir))

    detailed_calls: list[str] = []
    original_from_file_fast = FileMetadataCached.from_file_fast

    def _tracked_detailed_metadata(*args, **kwargs):  # type: ignore[no-untyped-def]
        detailed_calls.append(str(args[0]))
        return original_from_file_fast(*args, **kwargs)

    monkeypatch.setattr(
        FileMetadataCached,
        "from_file_fast",
        _tracked_detailed_metadata,
    )
    result = restarted.scan_incremental(use_session_cache=False)

    assert result.total_changes == 0
    assert detailed_calls == []
    assert result.baseline_available
    assert result.baseline_observed_at is not None
    assert set(result.baseline_entries) == {"nested/sample.py"}


def test_restart_exposes_persisted_pre_scan_checkpoint_with_one_scan(
    tmp_path: Path,
) -> None:
    target = tmp_path / "nested" / "sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    cache_dir = tmp_path / ".aware" / "checkpoint-cache"
    config = Config(
        file_system=FileSystemConfig(
            root_path=str(tmp_path), generate_tree=False, export_json=False
        ),
        filter=FilterConfig(max_file_size=None),
    )
    first = IncrementalScanner(config, cache_dir=str(cache_dir))
    cold = first.scan_incremental(use_session_cache=False)
    assert not cold.baseline_available

    target.write_text("after with a different size\n", encoding="utf-8")
    restarted = IncrementalScanner(config, cache_dir=str(cache_dir))
    advanced = restarted.scan_incremental(use_session_cache=False)

    assert advanced.baseline_available
    assert advanced.baseline_observed_at is not None
    assert advanced.baseline_entries["nested/sample.py"].size == len("before\n")
    assert set(advanced.modified) == {"nested/sample.py"}


def test_discover_current_files_optimized_reuses_filtered_cache_for_unchanged_dirs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "nested" / "sample.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('ok')\n", encoding="utf-8")

    first_scanner = _build_scanner(tmp_path)
    first_scanner.scan_incremental(use_session_cache=False)

    second_scanner = _build_scanner(tmp_path)

    def _unexpected_should_include_cached(path: str) -> bool:
        raise AssertionError(f"unchanged cached file should not be re-filtered: {path}")

    monkeypatch.setattr(
        second_scanner, "_should_include_cached", _unexpected_should_include_cached
    )

    current_files = second_scanner._discover_current_files_optimized()

    assert current_files == {"nested/sample.py"}


def test_gitignore_resolution_is_lazy_and_follows_scanner_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".gitignore").write_text("root-ignored.aware\n", encoding="utf-8")
    (tmp_path / "root-ignored.aware").write_text("ignored\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".gitignore").write_text("nested-ignored.aware\n", encoding="utf-8")
    (nested / "nested-ignored.aware").write_text("ignored\n", encoding="utf-8")
    (nested / "visible.aware").write_text("visible\n", encoding="utf-8")

    scanner = _build_scanner(tmp_path)

    def _unexpected_listdir(_path: str) -> list[str]:
        raise AssertionError("GitIgnore setup must not discover repository directories")

    with monkeypatch.context() as setup_guard:
        setup_guard.setattr(os, "listdir", _unexpected_listdir)
        scanner.filter

    result = scanner.scan_incremental(use_session_cache=False)

    assert "root-ignored.aware" not in result.added
    assert "nested/nested-ignored.aware" not in result.added
    assert "nested/visible.aware" in result.added


def test_gitignore_preserves_nested_scope_ordered_negation_and_pruning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".gitignore").write_text(
        "*.env\n!/.env.example\nignored/\n", encoding="utf-8"
    )
    (tmp_path / ".env").write_text("secret\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("example\n", encoding="utf-8")
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "must-not-scan.txt").write_text("ignored\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".gitignore").write_text("*.tmp\n!keep.tmp\n", encoding="utf-8")
    (nested / "drop.tmp").write_text("drop\n", encoding="utf-8")
    (nested / "keep.tmp").write_text("keep\n", encoding="utf-8")

    original_scandir = os.scandir

    def _guarded_scandir(path: os.PathLike[str] | str):  # type: ignore[type-arg]
        if Path(path).resolve() == ignored.resolve():
            raise AssertionError("Git-ignored directory must be pruned")
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", _guarded_scandir)
    result = _build_scanner(tmp_path).scan_incremental(use_session_cache=False)

    assert ".env" not in result.added
    assert ".env.example" in result.added
    assert "ignored/must-not-scan.txt" not in result.added
    assert "nested/drop.tmp" not in result.added
    assert "nested/keep.tmp" in result.added


def test_nested_addition_is_detected_below_unchanged_root(tmp_path: Path) -> None:
    nested = tmp_path / "one" / "two"
    nested.mkdir(parents=True)
    (nested / "existing.py").write_text("existing\n", encoding="utf-8")
    scanner = _build_scanner(tmp_path)
    scanner.scan_incremental(use_session_cache=False)

    added = nested / "added.py"
    added.write_text("added\n", encoding="utf-8")
    result = scanner.scan_incremental(use_session_cache=False)

    assert set(result.added) == {"one/two/added.py"}


def test_gitignore_change_recomputes_affected_descendant_membership(
    tmp_path: Path,
) -> None:
    ignore = tmp_path / ".gitignore"
    ignore.write_text("*.tmp\n", encoding="utf-8")
    nested = tmp_path / "one" / "two"
    nested.mkdir(parents=True)
    (nested / "visible.py").write_text("visible\n", encoding="utf-8")
    (nested / "newly-visible.tmp").write_text("visible later\n", encoding="utf-8")
    scanner = _build_scanner(tmp_path)
    first = scanner.scan_incremental(use_session_cache=False)
    assert "one/two/newly-visible.tmp" not in first.added

    ignore.write_text("# tmp is authored now\n", encoding="utf-8")
    result = scanner.scan_incremental(use_session_cache=False)

    assert "one/two/newly-visible.tmp" in result.added


def test_gitignore_change_evicts_newly_ignored_cached_subtree(
    tmp_path: Path,
) -> None:
    ignore = tmp_path / ".gitignore"
    ignore.write_text("# all authored\n", encoding="utf-8")
    nested = tmp_path / "generated" / "nested"
    nested.mkdir(parents=True)
    target = nested / "stale.py"
    target.write_text("stale\n", encoding="utf-8")
    scanner = _build_scanner(tmp_path)
    first = scanner.scan_incremental(use_session_cache=False)
    assert "generated/nested/stale.py" in first.added

    ignore.write_text("generated/\n", encoding="utf-8")
    os.utime(ignore, None)
    result = scanner.scan_incremental(use_session_cache=False)

    assert "generated/nested/stale.py" in result.deleted
    assert "generated/nested/stale.py" not in scanner.storage.load_index()
    assert not any(
        path == "generated" or path.startswith(f"generated{os.sep}")
        for path in scanner._dir_cache.entries
    )


def test_canonical_source_filter_includes_semantic_user_paths(tmp_path: Path) -> None:
    expected_paths = {
        "demo/root.aware",
        "examples/tutorial.py",
        "docs/README.md",
        "migrations/001_init.sql",
        "assets/config.aware",
        "assets/semantic-map.png",
        "tests/test_root.py",
    }
    for relative_path in expected_paths:
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"source\n")

    ignored = tmp_path / ".aware" / "cache.json"
    ignored.parent.mkdir(parents=True)
    ignored.write_text("{}", encoding="utf-8")

    scanner = _build_scanner(
        tmp_path,
        filter_config=CanonicalSourceFilterConfig(),
    )

    result = scanner.scan_incremental(use_session_cache=False)

    assert result.total_changes == len(expected_paths)
    assert set(result.added) == expected_paths


def test_canonical_source_filter_prunes_infrastructure_before_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    infrastructure = tmp_path / ".local"
    infrastructure.mkdir()
    (infrastructure / "generated.js").write_text("generated\n", encoding="utf-8")
    authored = tmp_path / "docs" / "source.aware"
    authored.parent.mkdir()
    authored.write_text("source\n", encoding="utf-8")

    scanner = _build_scanner(
        tmp_path,
        filter_config=CanonicalSourceFilterConfig(),
    )
    original_iterdir = Path.iterdir

    def _guarded_iterdir(self: Path):  # type: ignore[no-untyped-def]
        if self.resolve() == infrastructure.resolve():
            raise AssertionError("infrastructure directory must be pruned")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", _guarded_iterdir)

    result = scanner.scan_incremental(use_session_cache=False)

    assert "docs/source.aware" in result.added
    assert ".local/generated.js" not in result.added


def test_canonical_source_filter_does_not_traverse_directory_symlinks(
    tmp_path: Path,
) -> None:
    real_file = tmp_path / "real" / "source.txt"
    real_file.parent.mkdir()
    real_file.write_text("source\n", encoding="utf-8")
    os.symlink(real_file.parent, tmp_path / "linked-directory")
    os.symlink(real_file, tmp_path / "linked-file.txt")
    os.symlink(tmp_path, real_file.parent / "cycle")

    scanner = _build_scanner(
        tmp_path,
        filter_config=CanonicalSourceFilterConfig(),
    )
    result = scanner.scan_incremental(use_session_cache=False)

    assert set(result.added) == {"linked-file.txt", "real/source.txt"}
    assert not any(path.startswith("linked-directory/") for path in result.added)
    assert not any("cycle" in path for path in result.added)


def test_incremental_scan_preserves_delete_delta_until_comparison(
    tmp_path: Path,
) -> None:
    target = tmp_path / "deleted.txt"
    target.write_text("present\n", encoding="utf-8")
    scanner = _build_scanner(tmp_path)
    assert set(scanner.scan_incremental(use_session_cache=False).added) == {
        "deleted.txt"
    }

    target.unlink()
    deleted = scanner.scan_incremental(use_session_cache=False)

    assert deleted.deleted == {"deleted.txt"}
    assert deleted.total_changes == 1
    assert scanner.storage.load_index() == {}


def test_removed_cached_directory_deletes_once_without_rewriting_idle_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "source"
    removed = root / "gone" / "deleted.py"
    removed.parent.mkdir(parents=True)
    removed.write_text("present\n", encoding="utf-8")
    kept = root / "kept.py"
    kept.write_text("kept\n", encoding="utf-8")
    config = Config(
        file_system=FileSystemConfig(
            root_path=str(root), generate_tree=False, export_json=False
        ),
        filter=FilterConfig(max_file_size=None),
    )
    cache_dir = tmp_path / "cache"
    scanner = IncrementalScanner(config, cache_dir=str(cache_dir))
    assert set(scanner.scan_incremental(use_session_cache=False).added) == {
        "gone/deleted.py", "kept.py"
    }
    saves: list[set[str]] = []
    storage_type = type(scanner.storage)
    original_save = storage_type.save_index

    def tracked_save(self, entries):  # type: ignore[no-untyped-def]
        saves.append(set(entries))
        return original_save(self, entries)

    monkeypatch.setattr(storage_type, "save_index", tracked_save)
    shutil.rmtree(removed.parent)
    first = scanner.scan_incremental(use_session_cache=False)
    assert first.deleted == {"gone/deleted.py"}
    assert "gone/deleted.py" in first.baseline_entries
    assert saves == [{"kept.py"}]

    for active in (
        scanner,
        scanner,
        IncrementalScanner(config, cache_dir=str(cache_dir)),
    ):
        idle = active.scan_incremental(use_session_cache=False)
        assert idle.deleted == set()
        assert idle.total_changes == 0
        assert "gone/deleted.py" not in idle.baseline_entries
        assert saves == [{"kept.py"}]

    kept.write_text("changed with a different size\n", encoding="utf-8")
    assert set(scanner.scan_incremental(use_session_cache=False).modified) == {
        "kept.py"
    }
    removed.parent.mkdir()
    removed.write_text("restored\n", encoding="utf-8")
    assert set(scanner.scan_incremental(use_session_cache=False).added) == {
        "gone/deleted.py"
    }
    shutil.rmtree(removed.parent)
    assert scanner.scan_incremental(use_session_cache=False).deleted == {
        "gone/deleted.py"
    }
    assert scanner.scan_incremental(use_session_cache=False).total_changes == 0
    assert len(saves) == 4


def test_missing_discovered_candidate_is_not_a_deletion_without_prior_membership(
    tmp_path: Path,
) -> None:
    scanner = _build_scanner(tmp_path)
    result = scanner._process_file_changes({}, {"never-indexed.py"})
    assert result.total_changes == 0
    assert result.deleted == set()


def test_indexed_file_disappearing_after_discovery_still_deletes_once(
    tmp_path: Path,
) -> None:
    target = tmp_path / "race.py"
    target.write_text("present\n", encoding="utf-8")
    scanner = _build_scanner(tmp_path)
    baseline = scanner.scan_incremental(use_session_cache=False).added
    target.unlink()
    result = scanner._process_file_changes(baseline, {"race.py"})
    assert result.deleted == {"race.py"}
    assert result.total_changes == 1
    assert scanner._process_file_changes({}, {"race.py"}).total_changes == 0
