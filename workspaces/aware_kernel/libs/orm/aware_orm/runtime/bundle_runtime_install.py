"""Compatibility entrypoints for Structure environment bundle installation.

The implementation lives in `aware_structure.environment_config.orm_runtime_install`.
Base `aware-orm` only owns artifact payload sinks; it must not import Structure at
module import time.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from aware_orm._support import find_aware_root

CANONICAL_ONLY_ENV = "AWARE_ORM_CANONICAL_ONLY"
ENVIRONMENT_MANIFEST_ENV = "AWARE_ENVIRONMENT_MANIFEST"
ENVIRONMENT_ROOT = Path(".aware") / "environment"
DEFAULT_MANIFEST_PATH = ENVIRONMENT_ROOT / "runtime" / "environment.manifest.json"


def _structure_installer() -> Any:
    try:
        from aware_structure.environment_config import orm_runtime_install
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Structure environment bundle installation requires the Structure adapter "
            "(`aware-structure`). Base `aware-orm` only installs package-local runtime artifacts."
        ) from exc
    return orm_runtime_install


def canonical_only_enabled(default: bool = False) -> bool:
    raw = os.getenv(CANONICAL_ONLY_ENV)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def resolve_environment_manifest_path(manifest_override: Optional[str] = None) -> Path:
    candidate = manifest_override or os.getenv(ENVIRONMENT_MANIFEST_ENV)
    if candidate:
        path = Path(candidate)
        if not path.is_absolute():
            path = find_aware_root() / path
    else:
        path = find_aware_root() / DEFAULT_MANIFEST_PATH
    return path


def install_environment_bundle(
    manifest_path: Path,
    *,
    canonical_only: Optional[bool] = None,
    strict: bool = True,
    load_graph_artifacts: bool = True,
):
    return _structure_installer().install_environment_bundle(
        manifest_path=manifest_path,
        canonical_only=canonical_only,
        strict=strict,
        load_graph_artifacts=load_graph_artifacts,
    )


def install_default_environment_bundle(*, canonical_only: Optional[bool] = None, strict: bool = True):
    return _structure_installer().install_default_environment_bundle(
        canonical_only=canonical_only,
        strict=strict,
    )
