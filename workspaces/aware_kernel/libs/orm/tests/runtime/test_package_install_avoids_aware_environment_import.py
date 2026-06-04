from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path
from uuid import uuid4

import msgpack

from aware_orm.runtime.package_artifacts import (
    ORM_GRAPH_BINDING_FILENAME,
    PYTHON_MODELS_MANIFEST_FILENAME,
)
from aware_orm.runtime.package_install import install_package_runtime_artifacts


def _unimport(prefix: str) -> None:
    for name in list(sys.modules.keys()):
        if name == prefix or name.startswith(prefix + "."):
            sys.modules.pop(name, None)


def test_install_package_runtime_artifacts_does_not_import_aware_environment(
    tmp_path: Path,
) -> None:
    """
    Regression: the canonical package rail must not import `aware_environment`.

    Why:
    - Generated ontology packages call `install_package_runtime_artifacts(...)` at import time.
    - Importing `aware_environment.models_manifest` executes heavy `aware_environment/__init__.py`
      re-exports (docs + runtime), which can reorder ontology imports during bootstrap and
      break Pydantic forward-ref rebuilds (`undefined-annotation`).
    """

    pkg_root = tmp_path / "pkgs"
    pkg_root.mkdir(parents=True, exist_ok=True)

    pkg_name = f"aware_tmp_{uuid4().hex[:8]}"
    pkg_dir = pkg_root / pkg_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "__init__.py").write_text("", encoding="utf-8")

    artifacts = pkg_dir / "_aware"
    artifacts.mkdir(parents=True, exist_ok=True)

    # Minimal artifacts so install succeeds with strict=True.
    (artifacts / PYTHON_MODELS_MANIFEST_FILENAME).write_text(
        '{"language":"python","classes":[],"enums":[]}\n',
        encoding="utf-8",
    )
    snapshot_bytes = msgpack.packb(
        {"version": "v1", "entities": []},
        use_bin_type=True,
    )
    (artifacts / ORM_GRAPH_BINDING_FILENAME).write_bytes(snapshot_bytes)

    sys_path_snapshot = list(sys.path)
    orig_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "aware_environment" or name.startswith("aware_environment."):
            raise AssertionError(f"Unexpected import during package install: {name}")
        return orig_import(name, globals, locals, fromlist, level)

    try:
        builtins.__import__ = guarded_import
        sys.path.insert(0, str(pkg_root))
        importlib.invalidate_caches()
        _unimport(pkg_name)

        importlib.import_module(pkg_name)
        install_package_runtime_artifacts(package_prefix=pkg_name, strict=True)
    finally:
        builtins.__import__ = orig_import
        sys.path[:] = sys_path_snapshot
        _unimport(pkg_name)
