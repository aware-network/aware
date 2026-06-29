"""Small support helpers kept local to the public ORM package."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger()


class AwareRootError(RuntimeError):
    pass


def require_aware_root(*, purpose: str, env_var: str = "AWARE_ROOT") -> Path:
    raw = os.environ.get(env_var)
    if raw is None or not raw.strip():
        raise AwareRootError(f"{purpose}: {env_var} is required for runtime persistence")

    root = Path(raw).expanduser().resolve()
    if not root.exists():
        raise AwareRootError(f"{purpose}: {env_var} directory does not exist: {root}")
    if not root.is_dir():
        raise AwareRootError(f"{purpose}: {env_var} must be a directory: {root}")
    return root


def to_snake_case(name: str) -> str:
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s2 = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1)
    return s2.lower()
