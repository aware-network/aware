from __future__ import annotations

from pathlib import Path

from aware_meta.runtime.graph_context import (
    resolve_meta_runtime_package_manifest_closure_for_package_names,
)


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "aware.repo.toml").is_file():
            return candidate
    raise RuntimeError(f"Unable to resolve aware repo root from {start}")


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
ENVIRONMENT_ONTOLOGY_ROOT = (
    REPO_ROOT / "workspaces/aware_network/modules/environment/ontology"
)
ENVIRONMENT_STRUCTURE_ROOT = ENVIRONMENT_ONTOLOGY_ROOT / "structure"
ENVIRONMENT_AWARE_TOML = ENVIRONMENT_STRUCTURE_ROOT / "aware.toml"
ENVIRONMENT_AWARE = ENVIRONMENT_STRUCTURE_ROOT / "aware"
ENVIRONMENT_SQL_ROOTS = (
    ENVIRONMENT_STRUCTURE_ROOT / "sql/schema",
    ENVIRONMENT_STRUCTURE_ROOT / "sql/sqlite",
)
ENVIRONMENT_RUNTIME_ROOT = ENVIRONMENT_ONTOLOGY_ROOT / "runtime/python"


def environment_package_manifest_paths(
    repo_root: Path,
    package_names: tuple[str, ...] = ("environment-ontology",),
) -> tuple[Path, ...]:
    return resolve_meta_runtime_package_manifest_closure_for_package_names(
        repo_root=repo_root,
        package_names=package_names,
    )
