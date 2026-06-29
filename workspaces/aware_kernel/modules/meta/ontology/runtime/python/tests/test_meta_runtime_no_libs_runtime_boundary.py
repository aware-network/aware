from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
META_HANDLER_IMPL_ROOT = (
    REPO_ROOT / "modules" / "meta" / "runtime" / "aware_meta" / "handlers" / "impl"
)
META_RUNTIME_FACADE_PATHS = (
    REPO_ROOT / "modules" / "meta" / "runtime" / "aware_meta" / "runtime" / "author.py",
    REPO_ROOT
    / "modules"
    / "meta"
    / "runtime"
    / "aware_meta"
    / "runtime"
    / "handler_context.py",
)
META_GENERATED_HANDLER_PATHS = tuple(
    path
    for root in (REPO_ROOT / "modules", REPO_ROOT / "workspaces")
    if root.exists()
    for pattern in (
        "handlers/_generated/handlers.py",
        "handlers/_generated/meta_handlers.py",
    )
    for path in sorted(root.rglob(pattern))
    if "aware_meta" in path.parts
)


def test_meta_handler_impls_do_not_import_libs_runtime_context() -> None:
    offenders = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted(META_HANDLER_IMPL_ROOT.rglob("*.py"))
        if "aware_runtime" in path.read_text(encoding="utf-8")
    )

    assert offenders == ()


def test_meta_runtime_context_facades_do_not_import_libs_runtime() -> None:
    offenders = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in META_RUNTIME_FACADE_PATHS
        if "aware_runtime" in path.read_text(encoding="utf-8")
    )

    assert offenders == ()


def test_generated_meta_handlers_do_not_import_libs_runtime() -> None:
    offenders = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in META_GENERATED_HANDLER_PATHS
        if "aware_runtime" in path.read_text(encoding="utf-8")
    )

    assert offenders == ()
