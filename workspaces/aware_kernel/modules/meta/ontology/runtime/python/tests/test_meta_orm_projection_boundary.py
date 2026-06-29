from __future__ import annotations

import builtins
import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
META_ORM_PROJECTION_FILES = (
    REPO_ROOT
    / "modules"
    / "meta"
    / "runtime"
    / "aware_meta"
    / "graph"
    / "instance"
    / "orm_projector.py",
    REPO_ROOT
    / "modules"
    / "meta"
    / "runtime"
    / "aware_meta"
    / "graph"
    / "instance"
    / "orm_persistence.py",
)


def test_meta_orm_projection_sources_do_not_import_legacy_runtime() -> None:
    offenders = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in META_ORM_PROJECTION_FILES
        if "aware_runtime" in path.read_text(encoding="utf-8")
    )

    assert offenders == ()


def test_meta_orm_projection_imports_without_legacy_runtime(monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if str(name).split(".", 1)[0] == "aware_runtime":
            raise AssertionError(f"forbidden import attempted: {name}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    projector = importlib.import_module("aware_meta.graph.instance.orm_projector")
    persistence = importlib.import_module("aware_meta.graph.instance.orm_persistence")

    assert hasattr(projector, "stage_lane_projection_writes")
    assert hasattr(persistence, "stage_domain_persistence")
