from __future__ import annotations

from inspect import signature
from pathlib import Path

from aware_meta.runtime.oig_hydration import reify_meta_orm_root_from_oig_commit


REPO_ROOT = Path(__file__).resolve().parents[4]
META_RUNTIME_BOUNDARY_FILES = (
    REPO_ROOT
    / "modules"
    / "meta"
    / "runtime"
    / "aware_meta"
    / "runtime"
    / "oig_hydration.py",
    REPO_ROOT
    / "modules"
    / "meta"
    / "runtime"
    / "aware_meta"
    / "runtime"
    / "portal_context.py",
    REPO_ROOT
    / "modules"
    / "meta"
    / "runtime"
    / "aware_meta"
    / "runtime"
    / "portal_invocation.py",
)


def test_meta_oig_hydration_does_not_import_legacy_runtime() -> None:
    offenders = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in META_RUNTIME_BOUNDARY_FILES
        if "aware_runtime" in path.read_text(encoding="utf-8")
    )

    assert offenders == ()


def test_meta_oig_root_reifier_has_no_portal_hydration_flag() -> None:
    assert (
        "hydrate_portal_targets"
        not in signature(reify_meta_orm_root_from_oig_commit).parameters
    )
