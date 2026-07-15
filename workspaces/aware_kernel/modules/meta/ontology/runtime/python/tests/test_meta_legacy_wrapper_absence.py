from __future__ import annotations

from pathlib import Path


def test_meta_legacy_wrapper_modules_are_removed() -> None:
    aware_meta_root = Path(__file__).resolve().parents[1] / "aware_meta"
    retired_paths = (
        aware_meta_root / "function" / "invocation_plan_builder.py",
        aware_meta_root / "handlers" / "declarative.py",
        aware_meta_root / "graph" / "config" / "render" / "stable_ids_codegen.py",
        aware_meta_root / "graph" / "instance" / "seed.py",
    )

    assert [
        path.relative_to(aware_meta_root) for path in retired_paths if path.exists()
    ] == []
