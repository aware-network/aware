from __future__ import annotations

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


def _build_scanner(
    root: Path,
    *,
    filter_config: FilterConfig | None = None,
) -> IncrementalScanner:
    config = Config(
        file_system=FileSystemConfig(root_path=str(root), generate_tree=False, export_json=False),
        filter=filter_config or FilterConfig(max_file_size=None),
    )
    return IncrementalScanner(config)


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

    monkeypatch.setattr(second_scanner, "_should_include_cached", _unexpected_should_include_cached)

    current_files = second_scanner._discover_current_files_optimized()

    assert current_files == {"nested/sample.py"}


def test_canonical_source_filter_includes_semantic_user_paths(tmp_path: Path) -> None:
    expected_paths = {
        "demo/root.aware",
        "examples/tutorial.py",
        "docs/README.md",
        "migrations/001_init.sql",
        "assets/config.aware",
        "tests/test_root.py",
    }
    for relative_path in expected_paths:
        target = tmp_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("source\n", encoding="utf-8")

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
