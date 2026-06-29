from __future__ import annotations

from pathlib import Path


def test_meta_materialization_production_imports_no_aware_runtime() -> None:
    root = Path("workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/materialization")
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


def test_meta_environment_reindex_imports_no_aware_runtime() -> None:
    path = Path(
        "modules/meta/services/environment/aware_meta_environment_service/reindex_db.py"
    )
    source = path.read_text(encoding="utf-8")

    assert "from aware_runtime" not in source
    assert "import aware_runtime" not in source
    assert "aware_runtime." not in source
