from __future__ import annotations

from pathlib import Path


def test_code_tests_do_not_import_legacy_repo_root_discovery() -> None:
    code_module_root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    banned_tokens = (
        "aware_utils." + "find_aware_root",
        "find_aware_" + "repo_root(",
    )

    for path in sorted(code_module_root.rglob("*.py")):
        if "tests" not in path.parts:
            continue
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for token in banned_tokens:
            if token in text:
                offenders.append(f"{path.relative_to(code_module_root).as_posix()}:{token}")

    assert offenders == []
