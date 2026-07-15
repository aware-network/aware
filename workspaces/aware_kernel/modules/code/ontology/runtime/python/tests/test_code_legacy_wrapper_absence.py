from __future__ import annotations

from pathlib import Path


def test_code_legacy_wrapper_modules_are_removed() -> None:
    aware_code_root = Path(__file__).resolve().parents[1] / "aware_code"
    retired_paths = (aware_code_root / "segment" / "renderer.py",)

    assert [
        path.relative_to(aware_code_root) for path in retired_paths if path.exists()
    ] == []
