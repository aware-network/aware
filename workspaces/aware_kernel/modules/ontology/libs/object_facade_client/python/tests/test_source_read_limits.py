"""Read resource ceilings and isolation from the accepted v1 policy."""

import hashlib
import json
from typing import Any

import pytest
from aware_ontology_object_facade_client import codec as v1
from aware_ontology_object_facade_client import source_read_codec as read
from aware_ontology_object_facade_client import source_read_wire as w


def body(raw: bytes) -> dict[str, str]:
    return {"contract_ref": "fixture.opaque.v1", "body_hex": raw.hex(),
                "body_hash": "sha256:" + hashlib.sha256(raw).hexdigest()}


def raw(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def test_result_byte_ceiling_inclusive_and_v1_not_widened() -> None:
    at = "a" * (w.MAX_RESULT_BYTES - 2)
    assert len(read.canonical_bytes(at)) == w.MAX_RESULT_BYTES
    assert read.decode_canonical(raw(at)) == at
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.canonical_bytes(at + "a")
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.decode_canonical(raw(at + "a"))
    with pytest.raises(v1.WireError, match="limit_exceeded"):
        v1.canonical_bytes(at)


def test_each_body_ceiling_and_shared_v1_isolation() -> None:
    at = b"x" * w.MAX_BODY_BYTES
    assert read.make_body("fixture.opaque.v1", at) == body(at)
    assert read.decode_canonical(read.canonical_bytes(body(at))) == body(at)
    for encode in (read.make_body, v1.make_body):
        with pytest.raises(read.WireError, match="limit_exceeded"):
            encode("fixture.opaque.v1", at + b"x")
    with pytest.raises(v1.WireError, match="limit_exceeded"):
        v1.make_body("fixture.opaque.v1", at)


def test_aggregate_decoded_body_ceiling_counts_nested_and_repeated_occurrences() -> None:
    leaf = body(b"x" * 80_000)
    nested_raw = raw(leaf)
    nested = body(nested_raw)
    base = [nested] * 4
    remaining = w.MAX_AGGREGATE_BODY_BYTES - 4 * (len(nested_raw) + 80_000)
    assert 0 < remaining < w.MAX_BODY_BYTES
    at = [*base, body(b"x" * remaining)]
    assert read.decode_canonical(read.canonical_bytes(at)) == at
    over = [*base, body(b"x" * (remaining + 1))]
    assert len(raw(over)) < w.MAX_RESULT_BYTES
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.canonical_bytes(over)
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.decode_canonical(raw(over))


def test_depth_ceiling_includes_decoded_body_structure() -> None:
    at = b"[" * w.MAX_DEPTH + b"0" + b"]" * w.MAX_DEPTH
    assert read.decode_canonical(at)
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.decode_canonical(b"[" + at + b"]")
    owner = b"[" * (w.MAX_DEPTH - 1) + b"0" + b"]" * (w.MAX_DEPTH - 1)
    assert read.canonical_bytes(body(owner))
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.canonical_bytes(body(at))


def test_entry_ceiling_includes_owner_body_entries() -> None:
    assert read.decode_canonical(raw([0] * w.MAX_ENTRIES)) == [0] * w.MAX_ENTRIES
    for value in ([0] * (w.MAX_ENTRIES + 1), body(raw([0] * (w.MAX_ENTRIES - 2)))):
        with pytest.raises(read.WireError, match="limit_exceeded"):
            read.canonical_bytes(value)
    with pytest.raises(v1.WireError, match="limit_exceeded"):
        v1.decode_canonical(raw([0] * 4097))


@pytest.mark.parametrize("value", [b"[" * 33 + b"0" + b"]" * 33, raw([0] * 32_769)])
def test_parser_allocation_is_refused_before_json_loading(value: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("parser allocated before structural preflight")
    monkeypatch.setattr(json, "loads", unexpected)
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.decode_canonical(value)


def test_cycles_refuse_and_opaque_owner_float_meaning_is_preserved() -> None:
    cyclic: list[Any] = []
    cyclic.append(cyclic)
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.canonical_bytes(cyclic)
    owner = raw({"measurement": 1.5})
    assert read.make_body("fixture.owner-float.v1", owner)["body_hex"] == owner.hex()
    with pytest.raises(read.WireError):
        read.canonical_bytes({"measurement": 1.5})


@pytest.mark.parametrize("defect", ["uppercase", "odd", "empty", "hash", "extra", "tag"])
def test_invalid_body_framing(defect: str) -> None:
    obj: dict[str, Any] = body(b"test")
    if defect == "uppercase": obj["body_hex"] = "AB"
    elif defect == "odd": obj["body_hex"] = "a"
    elif defect == "empty": obj["body_hex"] = ""
    elif defect == "hash": obj["body_hash"] = "sha256:" + "0" * 64
    elif defect == "extra": obj["extra"] = 1
    else: obj["contract_ref"] = True
    # Body-aware primitive checks exactly shaped records. The dedicated Body
    # port must additionally reject a record whose shape has an extra field.
    with pytest.raises(read.WireError):
        read._body(obj)


def test_ref_scalar_and_counter_limits() -> None:
    for value in ("", "x y", "x\x00y", "\ud800", True):
        with pytest.raises(read.WireError):
            read.make_body(value, b"test")  # type: ignore[arg-type]
    assert read.make_body("é" * 256, b"test")
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.make_body("é" * 257, b"test")


@pytest.mark.parametrize("name,budget", [("request_budget_1", 1), ("request_budget_65535", 65535), ("request_budget_65536", 65536)])
def test_budget_admission_is_separate_from_syntactic_request_range(name: str, budget: int) -> None:
    from pathlib import Path
    evidence = json.loads((Path(__file__).resolve().parents[8] / "docs/reports/ontology-generic-object-observation-wire-successor-vectors-20261003.json").read_text())
    values = {v["name"]: v["value"] for v in evidence["vectors"]}
    request = values[name]
    assert read.decode_request(read.encode_request(request))["result_budget_bytes"] == budget
    if budget < w.MIN_RESULT_BUDGET_BYTES:
        with pytest.raises(read.WireError, match="limit_exceeded"):
            read.admit_result_budget(request)
        # No candidate behavior runs at this pre-contact data decision.
        class Candidate:
            def __getattribute__(self, name: str) -> object:
                raise AssertionError("candidate inspected before budget admission")
        assert read.decode_rejection(read.fit_response(request, Candidate())) == values["rejection_budget"]
    else:
        assert read.admit_result_budget(request) == budget


@pytest.mark.parametrize("budget", [74534, 74535, 74536])
def test_complete_negative_result_exact_final_fit_or_detached_refusal(budget: int) -> None:
    from pathlib import Path
    evidence = json.loads((Path(__file__).resolve().parents[8] / "docs/reports/ontology-generic-object-observation-wire-successor-vectors-20261003.json").read_text())
    values = {v["name"]: v["value"] for v in evidence["vectors"]}
    request = values[f"request_final_budget_{budget}"]
    result = values[f"unavailable_final_budget_{budget}"]
    full = read.encode_result(result)
    assert len(full) == 74535
    selected = read.fit_response(request, result)
    if budget < len(full):
        assert selected == read.encode_rejection(values["rejection_budget"])
        assert len(selected) == 147
        with pytest.raises(read.WireError, match="limit_exceeded"):
            read.match_result(request, result)
    else:
        assert selected == full
        assert read.match_result(request, result) == result


def test_budget_fallback_does_not_disguise_invalid_correlation() -> None:
    from pathlib import Path
    evidence = json.loads((Path(__file__).resolve().parents[8] / "docs/reports/ontology-generic-object-observation-wire-successor-vectors-20261003.json").read_text())
    values = {v["name"]: v["value"] for v in evidence["vectors"]}
    with pytest.raises(read.WireError, match="result_invalid"):
        read.fit_response(values["request_A"], values["positive_B"])
