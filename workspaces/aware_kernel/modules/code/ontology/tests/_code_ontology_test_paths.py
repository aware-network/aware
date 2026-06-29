from __future__ import annotations

from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent

CODE_ONTOLOGY_ROOT = _TESTS_ROOT.parents[0]
KERNEL_WORKSPACE_ROOT = _TESTS_ROOT.parents[3]
REPO_ROOT = _TESTS_ROOT.parents[5]


def source_text(repo_relative_path: str | Path) -> str:
    return (REPO_ROOT / repo_relative_path).read_text(encoding="utf-8")
