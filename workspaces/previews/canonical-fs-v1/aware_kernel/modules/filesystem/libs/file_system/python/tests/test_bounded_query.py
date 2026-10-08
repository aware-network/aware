from __future__ import annotations

from pathlib import Path

import pytest

from aware_file_system.bounded_query import BoundedPathQuery, query_bounded_paths


def _query(**overrides: object) -> BoundedPathQuery:
    values: dict[str, object] = {
        "prefixes": ("docs/issues",),
        "maximum_depth": 4,
        "maximum_entries": 32,
        "maximum_examined": 64,
        "suffixes": (".md",),
    }
    values.update(overrides)
    return BoundedPathQuery(**values)  # type: ignore[arg-type]


def test_query_is_prefix_depth_suffix_and_metadata_bounded(tmp_path: Path) -> None:
    issue = tmp_path / "docs/issues/2026/08/21/issue.md"
    issue.parent.mkdir(parents=True)
    issue.write_text("issue")
    (issue.parent / "ignored.txt").write_text("ignored")
    too_deep = issue.parent / "deeper/ignored.md"
    too_deep.parent.mkdir()
    too_deep.write_text("ignored")
    sibling = tmp_path / "huge/unrelated.md"
    sibling.parent.mkdir()
    sibling.write_text("unrelated")

    result = query_bounded_paths(root_path=tmp_path, query=_query())

    assert [entry.path for entry in result.entries] == [
        "docs/issues/2026/08/21/issue.md"
    ]
    assert result.entries[0].size_bytes == 5
    assert not result.truncated
    assert result.examined_count < 10


def test_query_never_follows_symlinks(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "escape.md").write_text("escape")
    prefix = tmp_path / "docs/issues"
    prefix.mkdir(parents=True)
    (prefix / "linked").symlink_to(outside, target_is_directory=True)
    (prefix / "file.md").symlink_to(outside / "escape.md")

    result = query_bounded_paths(root_path=tmp_path, query=_query())

    assert result.entries == ()


def test_query_reports_hard_budget_truncation(tmp_path: Path) -> None:
    prefix = tmp_path / "docs/issues"
    prefix.mkdir(parents=True)
    for index in range(10):
        (prefix / f"{index}.md").write_text(str(index))

    result = query_bounded_paths(
        root_path=tmp_path,
        query=_query(maximum_depth=1, maximum_entries=3, maximum_examined=4),
    )

    assert len(result.entries) == 3
    assert result.truncated


@pytest.mark.parametrize("prefix", ("", "/tmp", "../escape", "docs/../escape"))
def test_query_rejects_unconfined_prefixes(prefix: str) -> None:
    with pytest.raises(ValueError, match="prefix must be relative"):
        _query(prefixes=(prefix,))
