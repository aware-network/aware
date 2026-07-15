from __future__ import annotations

from ._attention_module_proof_paths import ATTENTION_RUNTIME_ROOT


SOURCE = ATTENTION_RUNTIME_ROOT / "aware_attention" / "compile.py"


def test_attention_compile_uses_local_repo_root_helper() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    deprecated_runtime_root = "aware_" + "runtime"

    assert deprecated_runtime_root not in text
    assert "def _find_repo_root(" in text
    assert "aware.environment.toml" in text
