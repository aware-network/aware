from __future__ import annotations

from aware_meta.materialization.deltas import coercion, constants, contracts
from aware_meta.materialization.deltas.contracts import (
    MetaProviderDeltaResultEnvelope,
    MetaProviderDeltaTypedOperation,
)


def test_provider_delta_contract_constants_are_focused_and_reexported() -> None:
    assert constants.META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION == (
        contracts.META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION
    )
    assert constants.META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION == (
        contracts.META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
    )
    assert constants.META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION == (
        contracts.META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION
    )

    operation = MetaProviderDeltaTypedOperation(
        operation_kind="meta_ocg_provider_delta_typed_operation",
        operation_key="op:update:attribute",
        operation_family="update",
        provider_operation_type="meta_ocg.attribute.update",
        semantic_key="home.Device/name",
        ontology_subject_kind="attribute",
    )

    assert operation.contract_version == (
        constants.META_PROVIDER_DELTA_TYPED_OPERATION_CONTRACT_VERSION
    )


def test_provider_delta_coercion_helpers_are_focused_and_reexported() -> None:
    assert contracts.mapping_value is coercion.mapping_value
    assert contracts.mapping_or_none is coercion.mapping_or_none
    assert contracts.tuple_mappings is coercion.tuple_mappings
    assert contracts.optional_text is coercion.optional_text
    assert contracts.string_value is coercion.string_value
    assert contracts.tuple_text is coercion.tuple_text
    assert contracts.int_value is coercion.int_value
    assert contracts.int_mapping_value is coercion.int_mapping_value

    assert coercion.mapping_value({"answer": 42}) == {"answer": 42}
    assert coercion.mapping_or_none(None) is None
    assert coercion.mapping_or_none({"answer": 42}) == {"answer": 42}
    assert coercion.tuple_mappings([{"a": 1}, "skip", {"b": 2}]) == (
        {"a": 1},
        {"b": 2},
    )
    assert coercion.optional_text("  value  ") == "value"
    assert coercion.optional_text("   ") is None
    assert coercion.string_value(None) == ""
    assert coercion.tuple_text([" one ", None, "two"]) == ("one", "two")
    assert coercion.int_value("7") == 7
    assert coercion.int_value(True) == 0
    assert coercion.int_mapping_value({"a": "3", "b": object()}) == {
        "a": 3,
        "b": 0,
    }


def test_result_envelope_keeps_contract_constant_reexport() -> None:
    envelope = MetaProviderDeltaResultEnvelope.from_payload(
        {
            "status": "fallback_required",
            "contract_version": constants.META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION,
            "details": {},
            "commit_ref_contract": {
                "contract_version": (
                    constants.META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION
                ),
            },
        }
    )

    assert envelope.contract_version == (
        contracts.META_PROVIDER_DELTA_RESULT_CONTRACT_VERSION
    )
    assert envelope.commit_ref_contract.contract_version == (
        contracts.META_PROVIDER_DELTA_COMMIT_REF_CONTRACT_VERSION
    )
