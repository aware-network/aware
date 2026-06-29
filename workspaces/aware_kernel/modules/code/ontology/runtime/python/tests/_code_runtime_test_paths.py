from __future__ import annotations

from pathlib import Path

_TESTS_ROOT = Path(__file__).resolve().parent

CODE_ONTOLOGY_ROOT = _TESTS_ROOT.parents[2]
KERNEL_WORKSPACE_ROOT = _TESTS_ROOT.parents[5]
REPO_ROOT = _TESTS_ROOT.parents[7]

CODE_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/ontology/ontology/structure/aware.toml",
)


def source_text(repo_relative_path: str | Path) -> str:
    return (REPO_ROOT / repo_relative_path).read_text(encoding="utf-8")
