from __future__ import annotations

import ast
from pathlib import Path


WRITER_SOURCE = (
    Path(__file__).resolve().parents[1] / "aware_reactivity" / "evidence" / "writer.py"
)


def test_evidence_writer_has_no_direct_deprecated_runtime_imports() -> None:
    source = WRITER_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[tuple[str, tuple[str, ...]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, tuple(alias.name for alias in node.names)))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, (alias.name,)))

    assert (
        "aware_meta.runtime.author",
        ("SYSTEM_ACTOR_ID",),
    ) in imports
    assert all(
        module.split(".", 1)[0] != "aware_" + "runtime" for module, _names in imports
    )
    assert "aware_" + "runtime" not in source
