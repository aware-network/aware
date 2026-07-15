from __future__ import annotations

from pathlib import Path

from aware_meta.runtime.graph_context import (
    resolve_meta_runtime_package_manifest_closure_for_package_names,
)

TESTS_ROOT = Path(__file__).resolve().parent
ECONOMY_RUNTIME_PYTHON_ROOT = TESTS_ROOT.parent
ECONOMY_RUNTIME_ROOT = ECONOMY_RUNTIME_PYTHON_ROOT.parent
ECONOMY_ONTOLOGY_ROOT = ECONOMY_RUNTIME_ROOT.parent
ECONOMY_MODULE_ROOT = ECONOMY_ONTOLOGY_ROOT.parent
AWARE_NETWORK_WORKSPACE_ROOT = ECONOMY_MODULE_ROOT.parent.parent
REPO_ROOT = AWARE_NETWORK_WORKSPACE_ROOT.parent.parent
KERNEL_WORKSPACE_ROOT = REPO_ROOT / "workspaces" / "aware_kernel"


def economy_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return resolve_meta_runtime_package_manifest_closure_for_package_names(
        repo_root=repo_root,
        package_names=("economy-ontology",),
    )
