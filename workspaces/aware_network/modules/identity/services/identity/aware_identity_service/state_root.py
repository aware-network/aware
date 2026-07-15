from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def isolated_identity_service_state(
    *,
    state_root_path: Path,
    persistence_backend: str = "fs",
) -> Iterator[Path]:
    root = state_root_path.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / ".aware").mkdir(parents=True, exist_ok=True)
    previous = {
        "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
        "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
    }
    os.environ["AWARE_ROOT"] = str(root)
    os.environ["AWARE_PERSISTENCE_BACKEND"] = persistence_backend
    os.environ.pop("DATABASE_URL", None)
    try:
        yield root
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
