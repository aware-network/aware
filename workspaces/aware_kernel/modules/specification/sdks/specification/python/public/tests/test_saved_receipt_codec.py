"""Strict complete saved transports and lossless wire values, not live receipts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace

import pytest
from aware_specification_sdk import (
    SpecificationSavedReceiptErrorEvidence,
    SpecificationSavedReceiptReadCleanup,
    SpecificationSavedReceiptRequest,
    SpecificationSavedReceiptValueError,
    decode_saved_draft_capture,
    decode_specification_saved_receipt_value,
    decode_specification_value,
    encode_specification_saved_receipt_value,
    encode_specification_value,
    present_saved_draft_capture,
)
from aware_specification_sdk import saved_receipt as owner


def body():
    return b'{"effect":"none","consumer_completion_verified":false,"retained_capability_exported":false,"error":"governed_draft_integration_unavailable","detail":"ImportError"}\n'


def request():
    return SpecificationSavedReceiptRequest(
        "/explicit/root", "receipt.json", "sha256:" + hashlib.sha256(body()).hexdigest()
    )


def result(view="summary"):
    return present_saved_draft_capture(
        replace(request(), view=view),
        body(),
        provider_ref="original:reader",
        provider_distribution="fixture",
        provider_version="0",
        cleanup=SpecificationSavedReceiptReadCleanup("closed", 1, 1, 1),
    )


@pytest.mark.parametrize(
    "value",
    [
        request(),
        result(),
        result("full"),
        result().source,
        SpecificationSavedReceiptReadCleanup("closed", 1, 1, 1),
        SpecificationSavedReceiptReadCleanup("unknown", None, 1, None, ("uncertain",)),
        SpecificationSavedReceiptErrorEvidence("invalid", "Local request refused."),
        SpecificationSavedReceiptErrorEvidence(
            "foreign",
            "Unvalidated provider bytes.",
            request=request(),
            provider_invoked=True,
            cleanup="unknown",
            effect="unknown",
            reported_result={"raw": [1, False, "captured"]},
            reported_result_type="foreign.Report",
            evidence_grade="unvalidated_provider_report",
        ),
    ],
)
def test_all_outer_values_roundtrip_through_dedicated_and_common_codecs(value):
    encoded = encode_specification_saved_receipt_value(value)
    restored = decode_specification_saved_receipt_value(encoded)
    assert restored == value and restored is not value
    assert encode_specification_saved_receipt_value(restored) == encoded
    assert encode_specification_value(value) == encoded
    assert decode_specification_value(encoded) == value


@pytest.mark.parametrize(
    "raw",
    [
        b"[]",
        b"{}",
        b"null",
        b"{} {}",
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":-Infinity}',
        b'{"a":"\xff"}',
        b'{"a":"\\ud800"}',
        b'{"effect":"none","effect":"unknown"}',
        b'{"outer":{"duplicate":1,"duplicate":2}}',
        b'{"integer":9223372036854775808}',
        b'{"integer":-9223372036854775809}',
        b'{"a":' + b"[" * 33 + b"0" + b"]" * 33 + b"}",
    ],
)
def test_strict_saved_capture_refuses_invalid_or_non_profile_json(raw):
    with pytest.raises(SpecificationSavedReceiptValueError):
        decode_saved_draft_capture(raw)


@pytest.mark.parametrize(
    "profile", ["", "guess", "specification.cli041-draft-transport.v1", None]
)
def test_profile_never_guesses_producer_version(profile):
    with pytest.raises(SpecificationSavedReceiptValueError):
        decode_saved_draft_capture(body(), input_profile=profile)


@pytest.mark.parametrize(
    "field,value",
    [
        ("effect", "unknown"),
        ("consumer_completion_verified", True),
        ("retained_capability_exported", 0),
        ("error", "other"),
        ("detail", "ValueError"),
        ("unexpected", None),
    ],
)
def test_supplier_unavailable_variant_is_closed(field, value):
    packet = json.loads(body())
    packet[field] = value
    with pytest.raises(SpecificationSavedReceiptValueError):
        decode_saved_draft_capture(json.dumps(packet).encode())


@pytest.mark.parametrize("boundary", ["source", "nodes", "string", "depth"])
def test_receiving_limits_refuse_without_truncation(monkeypatch, boundary):
    if boundary == "source":
        monkeypatch.setattr(
            owner, "SPECIFICATION_SAVED_RECEIPT_SOURCE_LIMIT", len(body()) - 1
        )
        raw = body()
    elif boundary == "nodes":
        raw = json.dumps({"a": [0] * 262144}).encode()
    elif boundary == "string":
        raw = json.dumps({"a": "x" * (1024**2 + 1)}).encode()
    else:
        raw = b'{"a":' + b"[" * 32 + b"0" + b"]" * 32 + b"}"
    with pytest.raises(SpecificationSavedReceiptValueError, match="limit"):
        decode_saved_draft_capture(raw)


@pytest.mark.parametrize(
    "changes",
    [
        {"contract": "wrong"},
        {"type_ref": "foreign.Type"},
        {"extra": None},
    ],
)
def test_outer_wire_allowlist_and_exact_fields(changes):
    raw = json.loads(encode_specification_saved_receipt_value(request()))
    raw.update(changes)
    with pytest.raises(SpecificationSavedReceiptValueError):
        decode_specification_saved_receipt_value(owner._json_body(raw))


@pytest.mark.parametrize(
    "raw",
    [
        b'{"contract":"x","contract":"y"}',
        b"{}{}",
        b"[]",
        b'{"value":"\\ud800"}',
        b"[" * 100 + b"0" + b"]" * 100,
    ],
)
def test_outer_wire_rejects_duplicate_unicode_and_excessive_nesting(raw):
    with pytest.raises(SpecificationSavedReceiptValueError):
        decode_specification_saved_receipt_value(raw)


@pytest.mark.parametrize("target", ["result", "record", "source", "cleanup"])
def test_outer_wire_unknown_fields_cannot_hide_in_nested_records(target):
    raw = json.loads(encode_specification_saved_receipt_value(result()))
    slot = raw["value"]
    if target == "record":
        slot = slot["record"]
    elif target == "source":
        slot = slot["source"]
    elif target == "cleanup":
        slot = slot["source"]["cleanup"]
    slot["unexpected"] = "not omitted"
    with pytest.raises(SpecificationSavedReceiptValueError):
        decode_specification_saved_receipt_value(owner._json_body(raw))


@pytest.mark.parametrize("hex_body", ["FF", "0", "00 00", "\ud800"])
def test_full_hex_is_canonical_bounded_and_utf8_errors_stay_typed(hex_body):
    raw = json.loads(encode_specification_saved_receipt_value(result()))
    raw["value"]["full_body_hex"] = hex_body
    with pytest.raises(SpecificationSavedReceiptValueError):
        decode_specification_saved_receipt_value(owner._json_body(raw))


@pytest.mark.parametrize("location", ["message", "report_key", "report_value"])
def test_direct_error_evidence_unicode_validation_preserves_encoding_cause(location):
    if location == "message":
        values = {"message": "\ud800"}
    else:
        report = {"\ud800": "x"} if location == "report_key" else {"x": "\ud800"}
        values = {
            "provider_invoked": True,
            "cleanup": "unknown",
            "effect": "unknown",
            "evidence_grade": "unvalidated_provider_report",
            "reported_result": report,
        }
    with pytest.raises(SpecificationSavedReceiptValueError) as failure:
        replace(
            SpecificationSavedReceiptErrorEvidence("invalid", "Original cause."),
            **values,
        )
    assert isinstance(failure.value.__cause__, UnicodeEncodeError)


def test_full_return_revalidates_record_after_provider_mutation():
    value = result()
    original = asdict(value)
    value.record["detail"] = "invented producer report"
    with pytest.raises(SpecificationSavedReceiptValueError):
        encode_specification_saved_receipt_value(value)
    assert original["record"]["detail"] == "ImportError"


def test_valid_utf8_capture_whitespace_is_preserved_not_reencoded():
    content = body() + b"  \n"
    req = replace(
        request(),
        expected_source_sha256="sha256:" + hashlib.sha256(content).hexdigest(),
        view="full",
    )
    value = present_saved_draft_capture(
        req,
        content,
        provider_ref="fixture",
        provider_distribution="fixture",
        provider_version="0",
        cleanup=SpecificationSavedReceiptReadCleanup("closed", 1, 1, 1),
    )
    assert (
        bytes.fromhex(
            decode_specification_saved_receipt_value(
                encode_specification_saved_receipt_value(value)
            ).full_body_hex
        )
        == content
    )


def test_wire_requests_have_their_smaller_explicit_limit(monkeypatch):
    encoded = encode_specification_saved_receipt_value(request())
    monkeypatch.setattr(
        owner, "SPECIFICATION_SAVED_RECEIPT_REQUEST_LIMIT", len(encoded) - 1
    )
    with pytest.raises(SpecificationSavedReceiptValueError, match="limit"):
        decode_specification_saved_receipt_value(encoded)
    with pytest.raises(SpecificationSavedReceiptValueError, match="limit"):
        encode_specification_saved_receipt_value(request())
