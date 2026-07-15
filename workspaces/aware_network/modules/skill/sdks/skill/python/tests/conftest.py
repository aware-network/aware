from __future__ import annotations

from pathlib import Path
import sys


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "aware.repo.toml").is_file():
            return candidate
    raise RuntimeError(f"Could not find aware.repo.toml from {start}")


def pytest_configure() -> None:
    repo_root = _find_repo_root(Path(__file__).resolve())
    skill_module_root = repo_root / "workspaces" / "aware_network" / "modules" / "skill"
    for path in (
        skill_module_root / "sdks" / "skill" / "python",
        skill_module_root / "apis" / "skill" / "python" / "aware_skill_service_dto",
    ):
        path_str = str(path.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
