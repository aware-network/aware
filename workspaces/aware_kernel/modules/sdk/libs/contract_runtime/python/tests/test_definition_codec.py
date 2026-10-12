from __future__ import annotations

import json

import pytest
from aware_sdk_contract_runtime import (
    SdkDefinitionDecodeError,
    decode_sdk_definition_state,
    decode_sdk_definition_transition,
    decode_sdk_prepared_definition_effect,
    derive_sdk_definition_transition,
    encode_sdk_definition_state,
    encode_sdk_definition_transition,
    encode_sdk_prepared_definition_effect,
    prepare_sdk_definition_effect,
)

from test_definition_transition import _state


def test_definition_state_transition_and_effect_round_trip() -> None:
    before = _state(legacy_mode="sync")
    after = _state(legacy_mode="async")
    transition = derive_sdk_definition_transition(before, after)
    effect = prepare_sdk_definition_effect(before, after)

    assert decode_sdk_definition_state(encode_sdk_definition_state(after)) == after
    assert (
        decode_sdk_definition_transition(
            encode_sdk_definition_transition(
                transition, predecessor=before, result=after
            ),
            predecessor=before,
            result=after,
        )
        == transition
    )
    assert (
        decode_sdk_prepared_definition_effect(
            encode_sdk_prepared_definition_effect(
                effect, predecessor=before, result=after
            ),
            predecessor=before,
            result=after,
        )
        == effect
    )


@pytest.mark.parametrize(
    ("needle", "replacement"),
    ((b'"has_default":true', b'"has_default":1'), (b'"default_value":false', b'"default_value":0')),
)
def test_state_decoder_rejects_canonical_bool_integer_substitution(
    needle: bytes, replacement: bytes
) -> None:
    state = _state()
    payload = encode_sdk_definition_state(state)
    assert needle in payload
    poison = payload.replace(needle, replacement, 1)
    json.loads(poison)
    with pytest.raises(SdkDefinitionDecodeError):
        decode_sdk_definition_state(poison)


def test_state_decoder_rejects_noncanonical_and_duplicate_wire() -> None:
    state = _state()
    payload = encode_sdk_definition_state(state)
    with pytest.raises(SdkDefinitionDecodeError):
        decode_sdk_definition_state(payload + b"\n")
    duplicate = payload.replace(b'{"contract":', b'{"contract":"duplicate","contract":', 1)
    with pytest.raises(SdkDefinitionDecodeError, match="duplicate JSON key"):
        decode_sdk_definition_state(duplicate)


def test_context_bound_transition_encoder_rejects_restamped_value() -> None:
    before = _state(legacy_mode="sync")
    after = _state(legacy_mode="async")
    transition = derive_sdk_definition_transition(before, after)
    object.__setattr__(transition, "result_definition_digest", "sha256:" + "9" * 64)
    object.__setattr__(transition, "transition_digest", "sha256:" + "8" * 64)
    with pytest.raises(ValueError, match="fresh supplied-state derivation"):
        encode_sdk_definition_transition(transition, predecessor=before, result=after)


def test_transition_decoder_rejects_context_substitution() -> None:
    before = _state(legacy_mode="sync")
    after = _state(legacy_mode="async")
    payload = encode_sdk_definition_transition(
        derive_sdk_definition_transition(before, after),
        predecessor=before,
        result=after,
    )
    with pytest.raises(SdkDefinitionDecodeError, match="fresh supplied-state"):
        decode_sdk_definition_transition(
            payload,
            predecessor=None,
            result=after,
        )


def test_effect_encoder_rejects_restamped_embedded_state() -> None:
    before = _state(legacy_mode="sync")
    after = _state(legacy_mode="async")
    effect = prepare_sdk_definition_effect(before, after)
    object.__setattr__(effect, "effect_digest", "sha256:" + "7" * 64)
    with pytest.raises(ValueError, match="fresh supplied-state derivation"):
        encode_sdk_prepared_definition_effect(effect, predecessor=before, result=after)
