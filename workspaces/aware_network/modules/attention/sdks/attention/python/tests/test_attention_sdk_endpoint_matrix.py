from __future__ import annotations

from aware_attention_service_api._bindings import ENDPOINT_REF_BY_NAME

from attention_endpoint_matrix import ATTENTION_ENDPOINT_MATRIX


def test_attention_endpoint_matrix_accounts_for_generated_sdk_surface() -> None:
    generated_endpoint_refs = set(ENDPOINT_REF_BY_NAME.values())
    matrix_endpoint_refs = {row.endpoint_ref for row in ATTENTION_ENDPOINT_MATRIX}
    assert matrix_endpoint_refs == generated_endpoint_refs
    assert len(ATTENTION_ENDPOINT_MATRIX) == 14
    assert {row.status for row in ATTENTION_ENDPOINT_MATRIX} == {"green"}
