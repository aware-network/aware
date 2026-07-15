from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Mapping


def api_service_protocol_dependency_roots(repo_root: Path) -> tuple[Path, ...]:
    return tuple(
        dict.fromkeys(
            (
                repo_root.resolve(),
                *declared_workspace_dependency_roots(workspace_root=repo_root),
            )
        )
    )


def declared_workspace_dependency_roots(*, workspace_root: Path) -> tuple[Path, ...]:
    workspace_toml = (workspace_root / "aware.workspace.toml").resolve()
    if not workspace_toml.is_file():
        return ()
    try:
        payload = tomllib.loads(workspace_toml.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return ()
    workspace_payload = payload.get("workspace")
    if not isinstance(workspace_payload, dict):
        return ()
    raw_dependencies = workspace_payload.get("dependencies")
    if not isinstance(raw_dependencies, list):
        return ()
    roots: list[Path] = []
    for raw_dependency in raw_dependencies:
        if not isinstance(raw_dependency, dict):
            continue
        root = _declared_local_workspace_dependency_root(
            workspace_root=workspace_root,
            dependency=raw_dependency,
        )
        if root is not None:
            roots.append(root)
    return tuple(dict.fromkeys(roots))


def _declared_local_workspace_dependency_root(
    *,
    workspace_root: Path,
    dependency: Mapping[str, object],
) -> Path | None:
    if str(dependency.get("kind") or "").strip() != "workspace":
        return None
    source = str(dependency.get("source") or "").strip()
    if not source.startswith("workspace://"):
        return None
    handle = source.removeprefix("workspace://").strip().strip("/")
    if not handle:
        return None
    sibling = workspace_root.parent / handle
    if (sibling / "aware.workspace.toml").is_file():
        return sibling.resolve()
    nested = workspace_root / "workspaces" / handle
    if (nested / "aware.workspace.toml").is_file():
        return nested.resolve()
    for parent in workspace_root.parents:
        candidate = parent / "workspaces" / handle
        if (candidate / "aware.workspace.toml").is_file():
            return candidate.resolve()
    return None
