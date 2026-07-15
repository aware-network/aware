from __future__ import annotations

from aware_code.section.projection.builder import (
    _normalize_projection_target,
    _projection_identity,
)


def test_projection_identity_preserves_authored_symbol_without_implicit_lowering() -> (
    None
):
    projection_name, label, is_branchable = _projection_identity(
        projection_symbol="FocusScope",
        options=[],
    )

    assert projection_name == "FocusScope"
    assert label is None
    assert is_branchable is False


def test_projection_target_preserves_unqualified_authored_token() -> None:
    assert _normalize_projection_target("FocusScope") == "FocusScope"
    assert (
        _normalize_projection_target("aware_attention.FocusScope")
        == "aware_attention.FocusScope"
    )
