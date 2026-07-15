from __future__ import annotations

import ast
from pathlib import Path

from _sdk_runtime_test_paths import SDK_TESTS_ROOT


def test_sdk_runtime_tests_do_not_import_legacy_root_discovery() -> None:
    offenders: list[str] = []
    for path in sorted(SDK_TESTS_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "aware_utils.find_aware_root"
            ):
                offenders.append(_location(path, node.lineno, "legacy import"))
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "find_aware_repo_root"
            ):
                offenders.append(_location(path, node.lineno, "legacy root call"))

    assert offenders == []


def _location(path: Path, lineno: int, reason: str) -> str:
    return f"{path.relative_to(SDK_TESTS_ROOT).as_posix()}:{lineno}:{reason}"
