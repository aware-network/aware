import json

import pytest
from aware_code_semantic_contract_runtime import canonical_json_bytes
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    decode_dependency_product_input,
    dependency_product_input_body,
    encode_dependency_product_input,
)
from test_dependency_inputs import product_input


def test_roundtrip_retains_full_intent_and_product_bytes():
    value = product_input()
    body = dependency_product_input_body(value)
    assert decode_dependency_product_input(body.canonical_body) == value
    assert body.canonical_body == encode_dependency_product_input(value)


@pytest.mark.parametrize(
    "change", ["extra", "bytes", "intent", "missing", "duplicate", "base64"]
)
def test_wire_rejects_invalid_closure(change):
    wire = json.loads(encode_dependency_product_input(product_input()))
    if change == "extra":
        wire["authority"] = "invented"
    elif change == "bytes":
        wire["products"][0]["body_base64"] = "eA=="
    elif change == "intent":
        wire["intent"]["operation_kind"] = "other"
    elif change == "missing":
        wire["products"] = []
    elif change == "duplicate":
        wire["products"] *= 2
    else:
        wire["products"][0]["body_base64"] = "!"
    with pytest.raises(ValueError):
        decode_dependency_product_input(canonical_json_bytes(wire))


@pytest.mark.parametrize("suffix", [b" ", b',"products":[]}'])
def test_noncanonical_or_duplicate_fields_rejected(suffix):
    wire = encode_dependency_product_input(product_input())
    changed = wire + suffix if suffix == b" " else wire[:-1] + suffix
    with pytest.raises(ValueError):
        decode_dependency_product_input(changed)
