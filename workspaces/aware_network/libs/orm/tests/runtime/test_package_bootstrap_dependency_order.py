from __future__ import annotations

import json
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import msgpack

from aware_orm.registry import ORMModelRegistry
from aware_orm.runtime.package_artifacts import (
    ORM_GRAPH_BINDING_FILENAME,
    PYTHON_MODELS_MANIFEST_FILENAME,
)
from aware_orm.runtime import package_install
from python_grammar.package_templates import render_root_init


def _unimport(prefix: str) -> None:
    for name in list(sys.modules.keys()):
        if name == prefix or name.startswith(prefix + "."):
            sys.modules.pop(name, None)


def test_root_init_bootstraps_dependency_packages_for_forward_refs(
    tmp_path: Path,
) -> None:
    """
    Regression: importing a generated ORM package must not depend on manual import order.

    In particular, cross-package relationships are commonly emitted with TYPE_CHECKING imports
    (to avoid runtime package import cycles). If the root package bootstraps before its declared
    dependencies are imported, Pydantic forward refs can remain unresolved in the process.
    """

    dep_root = f"aware_dep_{uuid4().hex[:8]}"
    main_root = f"aware_main_{uuid4().hex[:8]}"

    pkg_root = tmp_path / "pkgs"
    dep_pkg = pkg_root / dep_root
    main_pkg = pkg_root / main_root
    dep_pkg.mkdir(parents=True, exist_ok=True)
    main_pkg.mkdir(parents=True, exist_ok=True)

    # Minimal artifacts so `install_package_runtime_artifacts(..., strict=True)` succeeds.
    empty_manifest = '{"language":"python","classes":[],"enums":[]}\n'
    empty_snapshot = {"version": "v1", "entities": []}
    snapshot_bytes = msgpack.packb(empty_snapshot, use_bin_type=True)

    for pkg in (dep_pkg, main_pkg):
        artifacts = pkg / "_aware"
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / PYTHON_MODELS_MANIFEST_FILENAME).write_text(empty_manifest, encoding="utf-8")
        (artifacts / ORM_GRAPH_BINDING_FILENAME).write_bytes(snapshot_bytes)

    # Deterministic bootstrap manifests (replace giant __init__ lists).
    (dep_pkg / "_aware" / "python.bootstrap.json").write_text(
        json.dumps(
            {
                "version": "v1",
                "package_prefix": dep_root,
                "dependency_import_roots": [],
                "modules": [f"{dep_root}.models"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (main_pkg / "_aware" / "python.bootstrap.json").write_text(
        json.dumps(
            {
                "version": "v1",
                "package_prefix": main_root,
                "dependency_import_roots": [dep_root],
                "modules": [f"{main_root}.models"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    (dep_pkg / "models.py").write_text(
        """
from __future__ import annotations

from uuid import UUID

from aware_orm.models.orm_model import ORMModel


class Identity(ORMModel):
    id: UUID
""".lstrip(),
        encoding="utf-8",
    )

    (main_pkg / "models.py").write_text(
        f"""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import Field

from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from {dep_root}.models import Identity


class Tool(ORMModel):
    identity: Identity | None = Field(default=None, exclude=True)
    identity_id: UUID | None = Field(default=None)
""".lstrip(),
        encoding="utf-8",
    )

    (dep_pkg / "__init__.py").write_text(
        render_root_init(
            module_names=[f"{dep_root}.models"],
            dependency_import_roots=[],
            install_runtime_artifacts=True,
        ),
        encoding="utf-8",
    )
    (main_pkg / "__init__.py").write_text(
        render_root_init(
            module_names=[f"{main_root}.models"],
            dependency_import_roots=[dep_root],
            install_runtime_artifacts=True,
        ),
        encoding="utf-8",
    )

    registry_snapshot = ORMModelRegistry.snapshot_state()
    sys_path_snapshot = list(sys.path)
    try:
        ORMModelRegistry.clear_registry()
        ORMModelRegistry._initialized = False  # test-local reset
        _unimport(dep_root)
        _unimport(main_root)

        sys.path.insert(0, str(pkg_root))
        importlib.invalidate_caches()

        # Import the main package only: it must bootstrap the dependency first.
        importlib.import_module(main_root)

        tool_mod = importlib.import_module(f"{main_root}.models")
        Tool = getattr(tool_mod, "Tool")
        Identity = getattr(importlib.import_module(f"{dep_root}.models"), "Identity")

        # If forward refs were not rebuilt with dependency types present, this instantiation
        # would raise `pydantic.errors.PydanticUserError: Tool is not fully defined ...`.
        instance = Tool(identity=Identity(id=uuid4()), identity_id=uuid4())
        assert instance is not None

        tool_fqn = f"{main_root}.models.Tool"
        identity_fqn = f"{dep_root}.models.Identity"
        assert ORMModelRegistry.get_class_by_fqn(tool_fqn) is Tool
        assert ORMModelRegistry.get_class_by_fqn(identity_fqn) is Identity

        # Import-cache isolation may remove package modules while registry state
        # survives. The generated package bootstrap must install the new class
        # objects and rebuild their forward refs without consumer-local
        # `model_rebuild` calls.
        _unimport(dep_root)
        _unimport(main_root)
        importlib.invalidate_caches()
        importlib.import_module(main_root)

        reloaded_tool_mod = importlib.import_module(f"{main_root}.models")
        ReloadedTool = getattr(reloaded_tool_mod, "Tool")
        ReloadedIdentity = getattr(
            importlib.import_module(f"{dep_root}.models"),
            "Identity",
        )

        assert ReloadedTool is not Tool
        assert ReloadedIdentity is not Identity
        assert ORMModelRegistry.get_class_by_fqn(tool_fqn) is ReloadedTool
        assert ORMModelRegistry.get_class_by_fqn(identity_fqn) is ReloadedIdentity

        reloaded_instance = ReloadedTool(
            identity=ReloadedIdentity(id=uuid4()),
            identity_id=uuid4(),
        )
        assert reloaded_instance is not None
    finally:
        sys.path[:] = sys_path_snapshot
        _unimport(dep_root)
        _unimport(main_root)
        ORMModelRegistry.restore_state(registry_snapshot)


def test_package_install_cache_detects_stale_class_config_bindings(
    tmp_path: Path,
) -> None:
    package_root = f"aware_install_{uuid4().hex[:8]}"
    class_config_id = uuid4()
    pkg_root = tmp_path / "pkgs"
    package_dir = pkg_root / package_root
    package_dir.mkdir(parents=True, exist_ok=True)
    artifacts = package_dir / "_aware"
    artifacts.mkdir(parents=True, exist_ok=True)

    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "models.py").write_text(
        """
from __future__ import annotations

from aware_orm.models.orm_model import ORMModel


class Thing(ORMModel):
    name: str
""".lstrip(),
        encoding="utf-8",
    )
    (artifacts / PYTHON_MODELS_MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "language": "python",
                "classes": [
                    {
                        "class_config_id": str(class_config_id),
                        "module": f"{package_root}.models",
                        "name": "Thing",
                    }
                ],
                "enums": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    registry_snapshot = ORMModelRegistry.snapshot_state()
    sys_path_snapshot = list(sys.path)
    try:
        ORMModelRegistry.clear_registry()
        sys.path.insert(0, str(pkg_root))
        importlib.invalidate_caches()

        Thing = getattr(importlib.import_module(f"{package_root}.models"), "Thing")
        fqn = f"{package_root}.models.Thing"
        ORMModelRegistry.register_class_stub(Thing)
        class_config = SimpleNamespace(id=class_config_id, name="Thing")
        Thing.bind_class_config(class_config)
        assert ORMModelRegistry.attach_class_config(fqn, class_config)

        assert package_install._installed_package_is_current(
            package_prefix=package_root,
            artifacts_dir="_aware",
        )

        _unimport(package_root)
        importlib.invalidate_caches()
        ReloadedThing = getattr(
            importlib.import_module(f"{package_root}.models"),
            "Thing",
        )

        assert ReloadedThing is not Thing
        assert not package_install._installed_package_is_current(
            package_prefix=package_root,
            artifacts_dir="_aware",
        )

        ORMModelRegistry.register_class_stub(ReloadedThing)
        assert not package_install._installed_package_is_current(
            package_prefix=package_root,
            artifacts_dir="_aware",
        )

        ReloadedThing.bind_class_config(class_config)
        assert ORMModelRegistry.attach_class_config(fqn, class_config)
        assert package_install._installed_package_is_current(
            package_prefix=package_root,
            artifacts_dir="_aware",
        )
    finally:
        sys.path[:] = sys_path_snapshot
        _unimport(package_root)
        ORMModelRegistry.restore_state(registry_snapshot)
