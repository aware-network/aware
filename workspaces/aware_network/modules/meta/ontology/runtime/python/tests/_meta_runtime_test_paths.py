from __future__ import annotations

from pathlib import Path

META_TESTS_ROOT = Path(__file__).resolve().parent
META_RUNTIME_ROOT = META_TESTS_ROOT.parent
META_ONTOLOGY_ROOT = META_TESTS_ROOT.parents[2]
META_MODULE_ROOT = META_TESTS_ROOT.parents[3]
KERNEL_WORKSPACE_ROOT = META_TESTS_ROOT.parents[5]
REPO_ROOT = META_TESTS_ROOT.parents[7]

CODE_RUNTIME_ROOT = KERNEL_WORKSPACE_ROOT / "modules/code/ontology/runtime/python"
META_FIXTURES_ROOT = META_TESTS_ROOT / "fixtures"

META_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
)


def source_text(repo_relative_path: str | Path) -> str:
    return (REPO_ROOT / repo_relative_path).read_text(encoding="utf-8")
