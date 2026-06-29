from __future__ import annotations

import os
import tempfile
from pathlib import Path


class AwareRootError(RuntimeError):
    pass


def require_aware_root(*, purpose: str, env_var: str = "AWARE_ROOT") -> Path:
    """Resolve and validate the configured Aware root directory.

    This is intentionally strict: production services must not silently fall back to
    repo-relative `.aware` directories when durability is required.
    """

    raw = os.environ.get(env_var)
    if raw is None or not raw.strip():
        raise AwareRootError(
            f"{purpose}: {env_var} is required (set to a persistent volume mount, e.g. /var/lib/aware)."
        )

    aware_root = Path(raw).expanduser().resolve()
    if not aware_root.exists():
        raise AwareRootError(f"{purpose}: {env_var} directory does not exist: {aware_root}")
    if not aware_root.is_dir():
        raise AwareRootError(f"{purpose}: {env_var} must be a directory: {aware_root}")
    return aware_root


def ensure_aware_state_dir(*, aware_root: Path, require_writable: bool = True) -> Path:
    """Ensure `<AWARE_ROOT>/.aware` exists and is writable."""

    aware_dir = aware_root / ".aware"
    try:
        aware_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise AwareRootError(f"Unable to create Aware state directory: {aware_dir}") from exc

    if require_writable:
        try:
            with tempfile.NamedTemporaryFile(dir=str(aware_dir), prefix=".write_probe.", delete=True) as handle:
                handle.write(b"aware")
                handle.flush()
                os.fsync(handle.fileno())
        except Exception as exc:
            raise AwareRootError(f"Aware state directory is not writable: {aware_dir}") from exc

    return aware_dir


def ensure_aware_oig_dir(*, aware_root: Path, require_writable: bool = True) -> Path:
    """Ensure `<AWARE_ROOT>/.aware/oig` exists and is writable."""

    oig_dir = ensure_aware_state_dir(aware_root=aware_root, require_writable=require_writable) / "oig"
    try:
        oig_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise AwareRootError(f"Unable to create OIG commit store directory: {oig_dir}") from exc

    if require_writable:
        try:
            with tempfile.NamedTemporaryFile(dir=str(oig_dir), prefix=".write_probe.", delete=True) as handle:
                handle.write(b"oig")
                handle.flush()
                os.fsync(handle.fileno())
        except Exception as exc:
            raise AwareRootError(f"OIG commit store directory is not writable: {oig_dir}") from exc

    return oig_dir


__all__ = [
    "AwareRootError",
    "ensure_aware_oig_dir",
    "ensure_aware_state_dir",
    "require_aware_root",
]
