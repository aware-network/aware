from __future__ import annotations

from pathlib import Path


def test_operational_core_has_no_runtime_dependencies() -> None:
    root = Path(__file__).parents[1]
    pyproject = (root / "pyproject.toml").read_text()
    assert "dependencies = []" in pyproject
    production = "\n".join(
        path.read_text()
        for path in (root / "aware_issue_operational_runtime").glob("*.py")
    )
    assert "aware_local_service" not in production
    assert "aware_issue_runtime" not in production
    assert "aware_meta" not in production
    assert "sqlalchemy" not in production
    assert "tree_sitter" not in production
