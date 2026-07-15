from __future__ import annotations

from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "aware.repo.toml").is_file():
            return candidate
    raise RuntimeError(f"Unable to resolve aware repo root from {start}")


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
SERVICE_ONTOLOGY_ROOT = REPO_ROOT / "workspaces/aware_network/modules/service/ontology"
SERVICE_STRUCTURE_ROOT = SERVICE_ONTOLOGY_ROOT / "structure"
SERVICE_AWARE_TOML = SERVICE_STRUCTURE_ROOT / "aware.toml"
