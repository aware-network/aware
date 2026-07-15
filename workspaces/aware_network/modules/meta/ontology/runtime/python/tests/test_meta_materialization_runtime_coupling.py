from __future__ import annotations

from _meta_runtime_test_paths import KERNEL_WORKSPACE_ROOT


def test_meta_materialization_production_imports_no_aware_runtime() -> None:
    root = (
        KERNEL_WORKSPACE_ROOT
        / "modules/meta/ontology/runtime/python/aware_meta/materialization"
    )
    offenders: list[str] = []
    for path in sorted(root.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if (
            "from aware_runtime" in source
            or "import aware_runtime" in source
            or "aware_runtime." in source
        ):
            offenders.append(path.as_posix())

    assert offenders == []


def test_meta_environment_reindex_service_rail_is_retired() -> None:
    assert not (
        KERNEL_WORKSPACE_ROOT
        / "modules/meta/services/environment/aware_meta_environment_service/reindex_db.py"
    ).exists()
    assert not (KERNEL_WORKSPACE_ROOT / "modules/meta/services/environment").exists()
