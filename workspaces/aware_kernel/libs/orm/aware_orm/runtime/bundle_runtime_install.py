"""Retired Environment bundle install entrypoints.

`aware-orm` installs generated package/runtime artifacts from package-owned
`_aware` resources. It must not import Structure or load composed
`.aware/environment/runtime/environment.manifest.json` bundles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .errors import BundleInstallError

CANONICAL_ONLY_ENV = "AWARE_ORM_CANONICAL_ONLY"
ENVIRONMENT_MANIFEST_ENV = "AWARE_ENVIRONMENT_MANIFEST"
ENVIRONMENT_ROOT = Path(".aware") / "environment"
DEFAULT_MANIFEST_PATH = ENVIRONMENT_ROOT / "runtime" / "environment.manifest.json"
_RETIRED_MESSAGE = (
    "Environment bundle installation is retired. Install ORM runtime state from "
    "package-owned ontology artifacts via install_package_runtime_artifacts(), "
    "embedded _aware resources, db_schema_registry refs, and ORM graph binding "
    "snapshots instead of Structure Environment bundles."
)


def canonical_only_enabled(default: bool = False) -> bool:
    return default


def resolve_environment_manifest_path(manifest_override: Optional[str] = None) -> Path:
    raise BundleInstallError(_RETIRED_MESSAGE)


def install_environment_bundle(
    manifest_path: Path,
    *,
    canonical_only: Optional[bool] = None,
    strict: bool = True,
    load_graph_artifacts: bool = True,
):
    raise BundleInstallError(_RETIRED_MESSAGE)


def install_default_environment_bundle(
    *, canonical_only: Optional[bool] = None, strict: bool = True
):
    raise BundleInstallError(_RETIRED_MESSAGE)
