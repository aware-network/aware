from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
import sys
from typing import Protocol, cast


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "aware.repo.toml").is_file():
            return candidate
    raise RuntimeError(f"Could not resolve aware repo root from {start}")


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
SKILL_MODULE_ROOT = REPO_ROOT / "workspaces/aware_network/modules/skill"


class _SyspathPrepend(Protocol):
    def syspath_prepend(self, path: str) -> None: ...


def prepend_repo_paths(
    monkeypatch: _SyspathPrepend,
    relpaths: Iterable[str],
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for relpath in relpaths:
        path = REPO_ROOT / relpath
        if path.exists():
            syspath_prepend(str(path))


def install_repo_paths(relpaths: Iterable[str]) -> None:
    for relpath in reversed(tuple(relpaths)):
        path = REPO_ROOT / relpath
        if path.exists():
            path_text = str(path)
            if path_text not in sys.path:
                sys.path.insert(0, path_text)


SKILL_DEPENDENCY_RELPATHS: tuple[str, ...] = (
    "workspaces/aware_network/modules/skill/ontology/runtime/python",
    "workspaces/aware_network/modules/skill/ontology/structure/python/orm_runtime",
    "workspaces/aware_kernel/modules/api/ontology/runtime/python",
    "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_runtime",
    "workspaces/aware_kernel/modules/code/ontology/runtime/python",
    "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_runtime",
    "workspaces/aware_network/modules/experience/ontology/runtime/python",
    "workspaces/aware_network/modules/experience/ontology/structure/python/orm_runtime",
)


def install_skill_dependency_paths() -> None:
    install_repo_paths(SKILL_DEPENDENCY_RELPATHS)


def register_skill_module_plugins(registry: object) -> None:
    getattr(registry, "ensure_module_plugins_registered_from_module_roots")(
        module_roots=(SKILL_MODULE_ROOT,),
    )


def prepend_skill_dependency_paths(monkeypatch: _SyspathPrepend) -> None:
    prepend_repo_paths(
        monkeypatch,
        SKILL_DEPENDENCY_RELPATHS,
    )
