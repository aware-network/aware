from __future__ import annotations

from ._paths import IDENTITY_RUNTIME_SOURCE_ROOT


def test_identity_handler_materialization_context_uses_meta_boundary() -> None:
    source = (
        IDENTITY_RUNTIME_SOURCE_ROOT / "handlers" / "impl" / "identity" / "identity.py"
    ).read_text(encoding="utf-8")

    assert (
        "from aware_runtime.materialization import MaterializationRuntimeContext"
        not in source
    )
    assert "MaterializationRuntimeContext" not in source
