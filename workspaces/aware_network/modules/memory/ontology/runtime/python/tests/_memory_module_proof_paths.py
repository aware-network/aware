from __future__ import annotations

from pathlib import Path
import sys


TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parents[7]
KERNEL_WORKSPACE_ROOT = REPO_ROOT / "workspaces" / "aware_kernel"
NETWORK_WORKSPACE_ROOT = REPO_ROOT / "workspaces" / "aware_network"
MEMORY_RUNTIME_ROOT = TESTS_ROOT.parent
MEMORY_STRUCTURE_ROOT = NETWORK_WORKSPACE_ROOT / "modules/memory/ontology/structure"
MEMORY_PACKAGE_MANIFEST_PATHS = (
    KERNEL_WORKSPACE_ROOT / "modules/storage/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/api/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/aware.toml",
    KERNEL_WORKSPACE_ROOT / "modules/reactivity/ontology/structure/aware.toml",
    NETWORK_WORKSPACE_ROOT / "modules/identity/ontology/structure/aware.toml",
    NETWORK_WORKSPACE_ROOT / "modules/attention/ontology/structure/aware.toml",
    NETWORK_WORKSPACE_ROOT / "modules/memory/ontology/structure/aware.toml",
)


def extend_sys_path_for_memory_tests() -> None:
    paths = (
        MEMORY_RUNTIME_ROOT,
        MEMORY_STRUCTURE_ROOT / "python/orm_runtime",
        NETWORK_WORKSPACE_ROOT / "modules/attention/ontology/runtime/python",
        NETWORK_WORKSPACE_ROOT / "modules/attention/ontology/structure/python/orm_runtime",
        NETWORK_WORKSPACE_ROOT / "modules/identity/ontology/structure/python/orm_runtime",
        KERNEL_WORKSPACE_ROOT / "modules/meta/ontology/structure/python/orm_runtime",
        KERNEL_WORKSPACE_ROOT / "modules/content/ontology/structure/python/orm_runtime",
        KERNEL_WORKSPACE_ROOT / "modules/code/ontology/structure/python/orm_runtime",
        KERNEL_WORKSPACE_ROOT / "modules/history/ontology/structure/python/orm_runtime",
        KERNEL_WORKSPACE_ROOT / "modules/api/ontology/structure/python/orm_runtime",
        KERNEL_WORKSPACE_ROOT / "modules/reactivity/ontology/structure/python/orm_runtime",
    )
    for path in paths:
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)
