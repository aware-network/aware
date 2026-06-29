from __future__ import annotations

from pathlib import Path

from aware_meta.runtime import oigb_relationship_lane


REPO_ROOT = Path(__file__).resolve().parents[4]


def test_meta_oigb_relationship_lane_avoids_deprecated_runtime_imports() -> None:
    source = (
        REPO_ROOT / "workspaces/aware_kernel/modules/meta/ontology/runtime/python/aware_meta/runtime/oigb_relationship_lane.py"
    ).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "RuntimeInvocationProvider" not in source
    assert "execute_function" not in source


def test_meta_oigb_relationship_lane_exports_meta_owned_helper() -> None:
    assert callable(oigb_relationship_lane.attach_oigb_relationship)
    assert (
        oigb_relationship_lane.attach_oigb_relationship.__module__
        == "aware_meta.runtime.oigb_relationship_lane"
    )
