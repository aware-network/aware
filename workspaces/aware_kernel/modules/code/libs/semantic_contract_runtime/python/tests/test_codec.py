from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, cast

import pytest
from aware_code_semantic_contract_runtime import (
    ContractViolation,
    decode_invocation,
    decode_provider_declaration,
    decode_result,
    encode_invocation,
    encode_provider_declaration,
    encode_result,
)
from test_contracts import declaration, delta_result, digest, invocation


def test_declaration_invocation_and_contextual_result_round_trip() -> None:
    provider = declaration()
    call = invocation()
    result = delta_result(call)
    assert (
        decode_provider_declaration(encode_provider_declaration(provider)) == provider
    )
    assert decode_invocation(encode_invocation(call)) == call
    assert (
        decode_result(encode_result(result, provider, call), provider, call) == result
    )


def test_duplicate_unknown_and_noncanonical_wire_fail() -> None:
    payload = encode_provider_declaration(declaration())
    with pytest.raises(ContractViolation, match="duplicate"):
        decode_provider_declaration(
            payload[:-1] + ',"digest":"' + "sha256:" + "0" * 64 + '"}'
        )
    with pytest.raises(ContractViolation, match="field set"):
        root = json.loads(payload)
        root["unknown"] = 1
        decode_provider_declaration(
            json.dumps(root, sort_keys=True, separators=(",", ":"))
        )
    with pytest.raises(ContractViolation, match="field set"):
        root = json.loads(payload)
        del root["provider_contract"]
        decode_provider_declaration(
            json.dumps(root, sort_keys=True, separators=(",", ":"))
        )
    with pytest.raises(ContractViolation, match="canonical"):
        decode_provider_declaration(payload + "\n")


def test_true_integer_substitution_is_rejected_by_strict_wire_identity() -> None:
    payload = encode_provider_declaration(declaration())
    assert '"required":true' in payload
    with pytest.raises(TypeError):
        decode_provider_declaration(payload.replace('"required":true', '"required":1'))
    optional = replace(
        declaration(),
        consumed_roles=(replace(declaration().consumed_roles[0], required=False),),
    )
    optional_payload = encode_provider_declaration(optional)
    with pytest.raises(TypeError):
        decode_provider_declaration(
            optional_payload.replace('"required":false', '"required":0')
        )


def test_digest_restamp_and_context_substitution_fail() -> None:
    provider = declaration()
    call = invocation()
    result = delta_result(call)
    payload = encode_result(result, provider, call)
    root = json.loads(payload)
    root["digest"] = digest("9").value
    with pytest.raises(ContractViolation, match="digest differs"):
        decode_result(
            json.dumps(root, sort_keys=True, separators=(",", ":")), provider, call
        )
    other_call = replace(call, idempotency_key="other")
    with pytest.raises(ContractViolation, match="exact invocation"):
        decode_result(payload, provider, other_call)


def test_encoder_is_context_bound() -> None:
    provider = declaration()
    call = invocation()
    with pytest.raises(ContractViolation, match="exact invocation"):
        encode_result(
            delta_result(call), provider, replace(call, idempotency_key="other")
        )
    with pytest.raises(TypeError):
        encode_invocation(cast(Any, object()))
