from __future__ import annotations

import sys
from pathlib import Path


def _extend_sys_path_for_monorepo() -> None:
    """Ensure monorepo packages (libs/* + materialized ontologies) are importable in tests."""

    repo_root = Path(__file__).resolve().parents[3]
    candidates: list[Path] = [repo_root]

    libs_root = repo_root / "libs"
    if libs_root.exists():
        candidates.extend([p for p in libs_root.iterdir() if p.is_dir()])

    modules_root = repo_root / "modules"
    if modules_root.exists():
        for module in modules_root.iterdir():
            structure_root = module / "structure"
            if not structure_root.exists():
                continue
            python_pkg_root = structure_root / "python"
            if python_pkg_root.exists():
                candidates.append(python_pkg_root)
            api_pkg_root = structure_root / "api" / "python"
            if api_pkg_root.exists():
                candidates.append(api_pkg_root)

    env_root = repo_root / "environments"
    if env_root.exists():
        for env in env_root.iterdir():
            python_pkg_root = env / "ontology" / "python"
            if python_pkg_root.exists():
                candidates.append(python_pkg_root)

    for path in candidates:
        location = str(path)
        if location not in sys.path:
            sys.path.insert(0, location)


_extend_sys_path_for_monorepo()
