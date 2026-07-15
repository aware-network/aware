from __future__ import annotations

import ast
from pathlib import Path


SERVICE_PATH = (
    Path(__file__).resolve().parents[1]
    / "aware_environment"
    / "materialization"
    / "service.py"
)


def _import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def test_environment_materialization_uses_meta_portal_facade() -> None:
    source = SERVICE_PATH.read_text(encoding="utf-8")
    imports = _import_modules(SERVICE_PATH)

    assert "aware_meta.graph.projection.branching" not in imports
    assert "aware_meta.runtime.oigb_relationship_lane" not in imports
    assert "stable_portal_target_branch_id" not in source
    assert "attach_oigb_relationship" not in source
    assert "aware_meta.runtime.portal_lane_resolution" in imports
    assert "resolve_portal_target_branch_ref_for_object" in source
    assert "attach_portal_target_branch_relationship_for_object" in source
