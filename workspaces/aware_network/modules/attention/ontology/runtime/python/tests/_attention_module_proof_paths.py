from __future__ import annotations

from pathlib import Path


TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parents[7]
KERNEL_WORKSPACE_ROOT = REPO_ROOT / "workspaces" / "aware_kernel"
NETWORK_WORKSPACE_ROOT = REPO_ROOT / "workspaces" / "aware_network"
ATTENTION_RUNTIME_ROOT = TESTS_ROOT.parent
ATTENTION_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    NETWORK_WORKSPACE_ROOT / "modules/attention/ontology/structure/aware.toml",
)

