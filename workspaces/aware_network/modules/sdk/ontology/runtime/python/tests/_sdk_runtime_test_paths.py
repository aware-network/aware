from __future__ import annotations

from pathlib import Path

SDK_TESTS_ROOT = Path(__file__).resolve().parent
SDK_RUNTIME_ROOT = SDK_TESTS_ROOT.parent
SDK_ONTOLOGY_ROOT = SDK_TESTS_ROOT.parents[2]
SDK_MODULE_ROOT = SDK_TESTS_ROOT.parents[3]
REPO_ROOT = SDK_TESTS_ROOT.parents[7]
KERNEL_WORKSPACE_ROOT = SDK_TESTS_ROOT.parents[5]
API_ONTOLOGY_ROOT = KERNEL_WORKSPACE_ROOT / "modules/api/ontology"

SDK_RAW_PYTHON_ROOT = SDK_MODULE_ROOT / "libs/sdk/python"

SDK_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    API_ONTOLOGY_ROOT / "structure/aware.toml",
    SDK_ONTOLOGY_ROOT / "structure/aware.toml",
)
