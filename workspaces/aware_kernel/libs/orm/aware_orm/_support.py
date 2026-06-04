"""Small support helpers kept local to the public ORM package."""

from __future__ import annotations

import logging
import os
import re
import tomllib
from pathlib import Path

logger = logging.getLogger()

_REPO_ROOT_MARKERS = ("aware.environment.toml", "aware.workspace.toml")


def _has_repo_root_marker(path: Path) -> bool:
    return any((path / marker).exists() for marker in _REPO_ROOT_MARKERS)


def _validate_repo_candidate(path: Path | None) -> Path | None:
    if path is None:
        return None
    if _has_repo_root_marker(path):
        return path
    if (path / "libs").exists() and (path / "apps").exists():
        return path
    if (path / "libs").exists() and (path / "modules").exists():
        return path
    return None


def _walk_for_persistence_marker(start: Path) -> Path | None:
    current = start.resolve()
    while current.parent != current:
        if (current / ".aware").exists():
            return current
        current = current.parent
    if (current / ".aware").exists():
        return current
    return None


def _walk_for_repo_marker(start: Path) -> Path | None:
    current = start.resolve()
    while current.parent != current:
        if _has_repo_root_marker(current):
            return current
        current = current.parent
    if _has_repo_root_marker(current):
        return current
    return None


def _legacy_repo_lookup(start: Path) -> Path | None:
    current = start.resolve()
    while current.parent != current:
        pyproject_file = current / "pyproject.toml"
        if pyproject_file.exists():
            try:
                with pyproject_file.open("rb") as handle:
                    data = tomllib.load(handle)
                if data.get("tool", {}).get("poetry", {}).get("name") == "aware":
                    return current
            except Exception:
                pass
        if (current / "libs").exists() and (current / "apps").exists():
            return current
        current = current.parent
    return None


def find_aware_root() -> Path:
    for key in ("AWARE_ROOT", "AWARE_REPO_ROOT", "AWARE_HOME"):
        raw = os.environ.get(key)
        if raw is not None and raw.strip():
            return Path(raw).expanduser().resolve()

    marker_root = _walk_for_persistence_marker(Path.cwd())
    if marker_root:
        return marker_root

    repo_root = _walk_for_repo_marker(Path.cwd())
    if repo_root:
        return repo_root

    legacy_root = _legacy_repo_lookup(Path.cwd())
    if legacy_root:
        return legacy_root

    fallback = Path.cwd().resolve()
    while fallback.parent != fallback:
        candidate = _validate_repo_candidate(fallback)
        if candidate:
            return candidate
        fallback = fallback.parent
    return fallback


def find_aware_repo_root() -> Path:
    raw = os.environ.get("AWARE_REPO_ROOT")
    if raw is not None and raw.strip():
        candidate = _validate_repo_candidate(Path(raw).expanduser().resolve())
        if candidate is not None:
            return candidate

    marker_root = _walk_for_repo_marker(Path.cwd())
    if marker_root:
        return marker_root

    legacy_root = _legacy_repo_lookup(Path.cwd())
    if legacy_root:
        return legacy_root

    start = Path.cwd().resolve()
    fallback = start
    while fallback.parent != fallback:
        candidate = _validate_repo_candidate(fallback)
        if candidate:
            return candidate
        fallback = fallback.parent
    return start


def to_snake_case(name: str) -> str:
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s2 = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1)
    return s2.lower()
