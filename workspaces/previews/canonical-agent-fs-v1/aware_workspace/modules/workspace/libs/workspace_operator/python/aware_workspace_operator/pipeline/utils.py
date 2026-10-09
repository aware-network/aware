"""Pipeline utility helpers for workspace bootstrap."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

WORKSPACE_OPERATOR_REPO_ROOT_ENV_VARS = (
    "AWARE_WORKSPACE_OPERATOR_REPO_ROOT",
    "AWARE_WORKSPACE_REPO_ROOT",
    "AWARE_REPO_ROOT",
    "AWARE_REPOSITORY_ROOT",
)


def _normalize_env_token(name: str) -> str | None:
    raw = str(os.environ.get(name) or "").strip()
    return raw or None


def resolve_repo_root(
    *, raw_repo_root: str | None, create_if_missing: bool = True
) -> Path:
    """Resolve an explicit workspace root, creating it when requested."""

    raw = (raw_repo_root or "").strip()
    if not raw:
        for env_name in WORKSPACE_OPERATOR_REPO_ROOT_ENV_VARS:
            raw = _normalize_env_token(env_name) or ""
            if raw:
                break
    if not raw:
        try:
            return _resolve_aware_repo_root(start=Path.cwd())
        except RuntimeError as exc:
            raise RuntimeError(
                "Workspace Operator repo root is required. Pass --repo-root, "
                "set one of "
                f"{', '.join(WORKSPACE_OPERATOR_REPO_ROOT_ENV_VARS)}, "
                "or run from an Aware source checkout with aware.repo.toml."
            ) from exc

    root = Path(raw).expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(f"--repo-root must be a directory: {root}")
    if not root.exists() and create_if_missing:
        root.mkdir(parents=True, exist_ok=True)
    if not root.exists():
        raise FileNotFoundError(f"--repo-root does not exist: {root}")
    return root


def _resolve_aware_repo_root(*, start: Path) -> Path:
    current = start.expanduser().resolve()
    candidates = (current, *current.parents)
    for candidate in candidates:
        marker = candidate / "aware.repo.toml"
        if marker.is_file():
            return candidate
    raise RuntimeError(
        f"Could not resolve Aware repo root from {start}; aware.repo.toml not found."
    )


@contextmanager
def temporary_repo_root_env(*, repo_root: Path):
    """Set `AWARE_REPO_ROOT` and cwd temporarily for workspace-scoped ops."""

    key = "AWARE_REPO_ROOT"
    previous = os.environ.get(key)
    previous_cwd = Path.cwd()
    os.environ[key] = str(repo_root)
    os.chdir(repo_root)
    try:
        yield
    finally:
        os.chdir(previous_cwd)
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


__all__ = [
    "WORKSPACE_OPERATOR_REPO_ROOT_ENV_VARS",
    "resolve_repo_root",
    "temporary_repo_root_env",
]
