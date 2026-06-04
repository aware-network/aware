"""SSOT: canonical runtime artifact names and helpers.

Goal: stop scattering magic filenames/paths across the codebase.

These artifacts are used by the **canonical package rail** (Option A: package resources)
and can also be reused by other distribution rails.
"""

from __future__ import annotations

from importlib import import_module
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Tuple


DEFAULT_ARTIFACTS_DIR = "_aware"

# Canonical Python package rail artifacts (embedded as package resources)
PYTHON_MODELS_MANIFEST_FILENAME = "python.models.json"
ORM_GRAPH_BINDING_FILENAME = "orm.graph.binding.msgpack"
# Optional fallback when raw msgpack cannot be shipped by registry filters.
ORM_GRAPH_BINDING_B64_FILENAME = "orm.graph.binding.msgpack.b64"
# Canonical Python package bootstrap manifest (embedded as a package resource)
PYTHON_BOOTSTRAP_MANIFEST_FILENAME = "python.bootstrap.json"


def get_package_artifact_paths(
    *,
    package_prefix: str,
    artifacts_dir: str = DEFAULT_ARTIFACTS_DIR,
) -> Tuple[Traversable, Traversable]:
    """Resolve canonical artifact paths from package resources."""

    pkg = import_module(package_prefix)
    root = files(pkg)
    models_path = root.joinpath(artifacts_dir, PYTHON_MODELS_MANIFEST_FILENAME)
    binding_path = root.joinpath(artifacts_dir, ORM_GRAPH_BINDING_FILENAME)
    return models_path, binding_path
