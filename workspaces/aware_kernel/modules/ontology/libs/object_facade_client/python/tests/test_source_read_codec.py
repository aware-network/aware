"""Generic framing proofs. Fixture Bodies establish no original-owner authority."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from aware_ontology_object_facade_client import source_read_codec as read
from aware_ontology_object_facade_client import source_read_wire as w

ARTIFACT = Path(__file__).resolve().parents[8] / "docs/reports/ontology-generic-object-observation-wire-successor-vectors-20261003.json"
EVIDENCE = json.loads(ARTIFACT.read_text())
VECTORS = {row["name"]: row for row in EVIDENCE["vectors"]}
PORTS = {
    w.REQUEST_CONTRACT: "request", w.RESULT_CONTRACT: "result", w.REJECTION_CONTRACT: "rejection",
    w.ORIGIN_CONTRACT: "origin", w.MODEL_CONTRACT: "model_binding",
    w.BINDING_CONTRACT: "provider_binding", w.ROOT_CONTRACT: "typed_root",
    w.READING_CONTRACT: "provider_reading", w.TARGET_CONTRACT: "target",
    w.OBSERVATION_CONTRACT: "observation", w.FOCUS_CONTRACT: "focus_admission",
}
SIGNED = {"origin": "origin_digest", "model": "model_digest", "provider_binding": "binding_digest",
          "reading": "reading_digest", "target": "target_digest", "observation": "observation_digest",
          "focus": "admission_digest"}


def C(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def H(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def D(domain: str, value: object) -> str:
    return H(domain.encode() + b"\x00" + C(value))


def fixture(name: str) -> dict[str, Any]:
    return copy.deepcopy(VECTORS[name]["value"])


def seal(value: dict[str, Any], field: str) -> None:
    value[field] = D(value["contract"], {k: v for k, v in value.items() if k != field})


def B(contract: str, value: object) -> dict[str, str]:
    raw = C(value)
    return {"contract_ref": contract, "body_hex": raw.hex(), "body_hash": H(raw)}


def negative(tag: str, code: str, stage: str = "owner_verification", contact: str = "not_started") -> dict[str, Any]:
    return {"tag": tag, "code": code, "stage": stage, "command_contact": contact,
            "operation_contact": "not_started", "recovery_ref": None}


def response(req: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
    # Witnesses are detached fixture data, not issued host verification.
    result = {"contract": w.RESULT_CONTRACT, "profile_ref": w.PROFILE, "kind": "view.read",
              "origin": req["origin"], "operation": None, "ordinal": None,
              "intent_digest": req["intent_digest"], "delivery_ref": req["delivery"]["delivery_ref"],
              "responder_incarnation": req["delivery"]["recipient_incarnation"], "outcome": outcome}
    observed = {"contract": w.OUTCOME_OBSERVATION_CONTRACT, "request_intent_digest": req["intent_digest"],
                "outcome_hash": H(C({"contract": w.PREIMAGE_CONTRACT, "result": result})),
                "issuer_ref": "fixture:host-owner", "issuer_generation": result["responder_incarnation"],
                "verification_ref": "fixture:verification", "owner_observation_body": B("fixture.verification.v1", {"fixture_only": True})}
    seal(observed, "observation_digest")
    first = {"role": "command_outcome", "issuer_ref": observed["issuer_ref"],
             "issuer_generation": observed["issuer_generation"], "body": B(w.OUTCOME_OBSERVATION_CONTRACT, observed),
             "value_field": None}
    result["witnesses"] = [first]
    if outcome["tag"] == "ok":
        result["witnesses"].append({"role": "view_observation", "issuer_ref": first["issuer_ref"],
                                    "issuer_generation": first["issuer_generation"], "body": None, "value_field": "view"})
    result["result_digest"] = D(w.RESULT_DIGEST_DOMAIN, result)
    return result


@pytest.mark.parametrize("name", list(VECTORS))
def test_all_accepted_vectors_preserve_exact_bytes_and_roundtrip(name: str) -> None:
    vector = VECTORS[name]
    value = fixture(name)
    port = PORTS[value["contract"]]
    raw = getattr(read, "encode_" + port)(value)
    assert raw == C(value)
    assert len(raw) == vector["canonical_bytes"] and H(raw) == vector["sha256"]
    assert getattr(read, "decode_" + port)(raw) == value
    assert EVIDENCE["qualification"] == "synthetic_framing_only_no_issuer_or_nested_owner_conformance"


@pytest.mark.parametrize("label", ["A", "B"])
def test_distinct_provider_owned_models_use_identical_framing(label: str) -> None:
    req, res = fixture("request_" + label), fixture("positive_" + label)
    assert read.match_result(req, res) == res
    assert read.fit_response(req, res) == C(res)


@pytest.mark.parametrize("name", list(PORTS.values()))
@pytest.mark.parametrize("defect", ["missing", "extra", "contract", "foreign_string"])
def test_closed_envelope_keys_and_contracts(name: str, defect: str) -> None:
    vector = next(v for v in VECTORS.values() if PORTS[v["value"]["contract"]] == name)
    value = copy.deepcopy(vector["value"])
    if defect == "missing":
        value.pop("contract")
    elif defect == "extra":
        value["extra"] = None
    elif defect == "contract":
        value["contract"] = "fixture.other.v1"
    else:
        class ForeignString(str):
            pass
        value["contract"] = ForeignString(value["contract"])
    with pytest.raises(read.WireError):
        getattr(read, "encode_" + name)(value)
    if defect != "foreign_string":
        with pytest.raises(read.WireError):
            getattr(read, "decode_" + name)(C(value))


@pytest.mark.parametrize("name", list(SIGNED))
def test_enclosing_digest_is_complete(name: str) -> None:
    value = fixture(name)
    value[SIGNED[name]] = H(b"different")
    with pytest.raises(read.WireError):
        getattr(read, "encode_" + PORTS[value["contract"]])(value)


@pytest.mark.parametrize("comparison", EVIDENCE["substitution_comparisons"], ids=lambda x: x["name"])
def test_frozen_substitution_preimages_and_actual_refusal(comparison: dict[str, Any]) -> None:
    base = fixture(comparison["base_vector"])
    changed = copy.deepcopy(base)
    cursor = changed
    for part in comparison["path"][:-1]:
        cursor = cursor[part]
    cursor[comparison["path"][-1]] = comparison["replacement"]
    def digest(value: dict[str, Any]) -> str:
        rule = comparison["rule"]
        if rule == "request_intent":
            return D(w.INTENT_CONTRACT, {k: v for k, v in value.items() if k not in ("delivery", "intent_digest")})
        if rule == "outcome_preimage":
            return H(C({"contract": w.PREIMAGE_CONTRACT, "result": {k: v for k, v in value.items() if k not in ("witnesses", "result_digest")}}))
        field = comparison["digest_field"]
        return D(value["contract"], {k: v for k, v in value.items() if k != field})
    assert digest(base) == comparison["expected"]
    assert digest(changed) == comparison["substituted"] != comparison["expected"]
    with pytest.raises(read.WireError):
        getattr(read, "encode_" + PORTS[base["contract"]])(changed)


@pytest.mark.parametrize("tag,code", [(tag, code) for tag, codes in (("refused", w.REFUSED_CODES), ("unavailable", w.UNAVAILABLE_CODES)) for code in sorted(codes)])
def test_every_negative_has_complete_preimage_and_required_witness(tag: str, code: str) -> None:
    req = fixture("request_A")
    value = response(req, negative(tag, code))
    assert read.match_result(req, value) == value
    assert read.required_witness_roles(tag) == ("command_outcome",)
    assert read.outcome_preimage(value) == {"contract": w.PREIMAGE_CONTRACT, "result": {k: v for k, v in value.items() if k not in ("witnesses", "result_digest")}}
    value["outcome"]["code"] = "other"
    with pytest.raises(read.WireError):
        read.encode_result(value)


@pytest.mark.parametrize("stage", sorted(w.FAILURE_STAGES))
@pytest.mark.parametrize("contact", sorted(w.CONTACT_STATES))
def test_negative_contact_law(stage: str, contact: str) -> None:
    value = response(fixture("request_A"), negative("unavailable", "owner_unavailable", stage, contact))
    lawful = contact == "not_started" if stage in ("decode", "selection", "owner_verification") else contact != "not_started"
    if lawful:
        assert read.decode_result(read.encode_result(value)) == value
    else:
        with pytest.raises(read.WireError):
            read.encode_result(value)


@pytest.mark.parametrize("field,value", [("role", "operation_completion"), ("issuer_generation", "fixture:wrong"),
                                         ("issuer_ref", "fixture:wrong"), ("body", None), ("value_field", "view")])
def test_witness_associations_reject(field: str, value: object) -> None:
    result = fixture("positive_A")
    result["witnesses"][0][field] = value
    with pytest.raises(read.WireError):
        read.encode_result(result)


@pytest.mark.parametrize("defect", ["empty", "extra", "reverse", "positive_body", "positive_field", "positive_issuer"])
def test_witness_count_order_and_positive_role(defect: str) -> None:
    result = fixture("positive_A")
    witnesses = result["witnesses"]
    if defect == "empty": witnesses.clear()
    elif defect == "extra": witnesses.append(copy.deepcopy(witnesses[0]))
    elif defect == "reverse": witnesses.reverse()
    elif defect == "positive_body": witnesses[1]["body"] = witnesses[0]["body"]
    elif defect == "positive_field": witnesses[1]["value_field"] = "other"
    else: witnesses[1]["issuer_ref"] = "fixture:other"
    with pytest.raises(read.WireError):
        read.encode_result(result)


@pytest.mark.parametrize("tag", ["pending", "replay", "indeterminate", "ok_mutation", "ok_commit"])
def test_read_cannot_manufacture_execution_or_continuation(tag: str) -> None:
    value = fixture("positive_A")
    value["outcome"]["tag"] = tag
    with pytest.raises(read.WireError):
        read.encode_result(value)


@pytest.mark.parametrize("field", ["ontology_ref", "namespace_ref", "context_ref", "branch_ref", "object_ref",
                                  "root_type_ref", "observable_ref", "projection_ref", "model_digest"])
def test_resealed_observation_scope_mismatch_rejects(field: str) -> None:
    value = fixture("observation")
    value["scope"][field] = H(b"other") if field == "model_digest" else "fixture:other"
    seal(value, "observation_digest")
    with pytest.raises(read.WireError):
        read.encode_observation(value)


@pytest.mark.parametrize("record,field", [("model_binding", "root_type_ref"), ("model_binding", "projection_ref"),
                                          ("provider_binding", "provider_ref"), ("provider_binding", "provider_generation"),
                                          ("provider_reading", "provider_binding_digest"), ("provider_reading", "revision_ref")])
def test_resealed_lower_records_cannot_replace_wrapper_joins(record: str, field: str) -> None:
    obs = fixture("observation")
    body = obs[record]
    value = json.loads(bytes.fromhex(body["body_hex"]))
    value[field] = H(b"other") if field.endswith("digest") else "fixture:other"
    seal(value, {"model_binding": "model_digest", "provider_binding": "binding_digest", "provider_reading": "reading_digest"}[record])
    obs[record] = B(body["contract_ref"], value)
    seal(obs, "observation_digest")
    if record == "provider_reading" and field == "revision_ref":
        # Null expected revision allows a new reading; a pinned Request refuses it.
        req = fixture("request_A")
        req["payload"]["selection"]["expected_revision_ref"] = "fixture:revision:A"
        req["intent_digest"] = read.request_intent_digest(req)
        result = response(req, {"tag": "ok", "value": {"view": B(w.OBSERVATION_CONTRACT, obs)}, "finality": "observation"})
        with pytest.raises(read.WireError, match="source_stale"):
            read.match_result(req, result)
    else:
        with pytest.raises(read.WireError):
            read.encode_observation(obs)


@pytest.mark.parametrize("entry", ["view", "raw", "client"])
def test_original_entry_provenance_is_preserved(entry: str) -> None:
    req = fixture("request_A")
    origin = json.loads(bytes.fromhex(req["payload"]["origin_body"]["body_hex"]))
    req["origin"]["entry_kind"] = origin["origin"]["entry_kind"] = entry
    origin["experience_admission"] = B("fixture.experience.v1", {"fixture_only": True}) if entry == "view" else None
    seal(origin, "origin_digest")
    req["payload"]["origin_body"] = B(w.ORIGIN_CONTRACT, origin)
    req["intent_digest"] = read.request_intent_digest(req)
    assert read.decode_request(read.encode_request(req)) == req
    origin["experience_admission"] = None if entry == "view" else B("fixture.experience.v1", {"fixture_only": True})
    seal(origin, "origin_digest")
    req["payload"]["origin_body"] = B(w.ORIGIN_CONTRACT, origin)
    req["intent_digest"] = read.request_intent_digest(req)
    with pytest.raises(read.WireError):
        read.encode_request(req)


@pytest.mark.parametrize("field", ["target_kind", "authority_grade", "target_ref", "reading_ref"])
def test_target_authority_and_reading_join(field: str) -> None:
    obs = fixture("observation")
    obs["target"][field] = {"target_kind": "constructor", "authority_grade": "canonical", "target_ref": "fixture:other", "reading_ref": "fixture:other"}[field]
    seal(obs["target"], "target_digest")
    seal(obs, "observation_digest")
    with pytest.raises(read.WireError):
        read.encode_observation(obs)


@pytest.mark.parametrize("port", list(PORTS.values()) + ["outcome_observation"])
@pytest.mark.parametrize("nested", [False, True])
def test_foreign_values_never_execute_on_rejection(port: str, nested: bool) -> None:
    calls: list[str] = []
    class ProbeMeta(type):
        def __eq__(cls, other: object) -> bool:
            calls.append("metaclass equality")
            return False
    class Probe(metaclass=ProbeMeta):
        def __eq__(self, other: object) -> bool:
            calls.append("equality")
            return False
        def __str__(self) -> str:
            calls.append("conversion")
            return "probe"
    if port == "outcome_observation":
        result = fixture("positive_A")
        value = json.loads(bytes.fromhex(result["witnesses"][0]["body"]["body_hex"]))
    else:
        value = copy.deepcopy(next(v["value"] for v in VECTORS.values() if PORTS[v["value"]["contract"]] == port))
    if nested:
        value["extra"] = [{"nested": Probe()}]
    else:
        value["contract"] = Probe()
    with pytest.raises(read.WireError):
        getattr(read, "encode_" + port)(value)
    assert calls == []


@pytest.mark.parametrize("name", ["request_A", "positive_A", "rejection"])
@pytest.mark.parametrize("field,retired", [("contract", "aware.ontology.facade-request.v2"), ("profile_ref", "aware.ontology.source-read.v1")])
def test_retired_profile_has_no_live_fallback(name: str, field: str, retired: str) -> None:
    value = fixture(name)
    value[field] = retired
    with pytest.raises(read.WireError):
        getattr(read, "encode_" + PORTS[VECTORS[name]["value"]["contract"]])(value)
    with pytest.raises(read.WireError):
        getattr(read, "decode_" + PORTS[VECTORS[name]["value"]["contract"]])(C(value))


def test_retired_domain_helpers_and_discriminators_are_absent() -> None:
    for name in ("Subject", "NamespaceBinding", "SourceReading", "Mapping", "NAMESPACE_CONTRACT", "SOURCE_CONTRACT", "MAPPING_CONTRACT"):
        assert not hasattr(w, name)
    for name in ("encode_namespace", "decode_namespace", "encode_source", "decode_source", "encode_mapping", "decode_mapping"):
        assert not hasattr(read, name)
    value = fixture("request_A")
    value["payload"]["selection"]["subject_kind"] = "unrelated"
    value["intent_digest"] = read.request_intent_digest(value)
    with pytest.raises(read.WireError):
        read.encode_request(value)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{ "a":1}', b'{"a":1.0}', b'NaN', b'"\\ud800"', b'{"b":1,"a":2}'])
def test_noncanonical_outer_data_refuses(raw: bytes) -> None:
    with pytest.raises(read.WireError):
        read.decode_canonical(raw)


@pytest.mark.parametrize("field,ceiling", [("binding_revision", w.MAX_COUNTER), ("mount_activation_epoch", w.MAX_COUNTER), ("remaining_lifetime_ms", w.MAX_LIFETIME_MS)])
@pytest.mark.parametrize("variant", ["maximum", "overflow", "bool", "negative"])
def test_focus_counters_and_lifetime(field: str, ceiling: int, variant: str) -> None:
    value = fixture("focus")
    value[field] = {"maximum": ceiling, "overflow": ceiling + 1, "bool": True, "negative": -1}[variant]
    seal(value, "admission_digest")
    if variant == "maximum":
        assert read.decode_focus_admission(read.encode_focus_admission(value)) == value
    else:
        with pytest.raises(read.WireError):
            read.encode_focus_admission(value)


@pytest.mark.parametrize("defect", ["decimal_float", "nested_float", "unknown_tag", "unsorted_fields", "extra_value_key"])
def test_typed_root_uses_existing_scalar_owner(defect: str) -> None:
    value = fixture("typed_root_decimal")
    item = value["object"]["fields"][0]
    if defect == "decimal_float": item["value"]["value"] = 1.25
    elif defect == "nested_float": item["value"] = {"value_kind": "json", "value": {"nested": [1.25]}}
    elif defect == "unknown_tag": item["value"]["value_kind"] = "float"
    elif defect == "extra_value_key": item["value"]["extra"] = None
    else:
        second = copy.deepcopy(item)
        second["field_ref"] = "fixture:field:aaa"
        value["object"]["fields"].append(second)
    with pytest.raises(read.WireError):
        read.encode_typed_root(value)
    with pytest.raises(read.WireError):
        read.decode_typed_root(C(value))


def test_typed_root_body_numeric_float_refuses_in_reading() -> None:
    value = fixture("reading")
    root = fixture("typed_root_decimal")
    root["object"]["fields"][0]["value"]["value"] = 1.25
    value["typed_state"] = B(w.ROOT_CONTRACT, root)
    seal(value, "reading_digest")
    with pytest.raises(read.WireError):
        read.encode_provider_reading(value)


@pytest.mark.parametrize("kind,value", [("string", "é"), ("integer", -7), ("boolean", False),
                                       ("decimal", "1.25"), ("datetime", "2026-10-03T00:00:00Z"),
                                       ("reference", "fixture:ref"), ("json", {"nested": [None, True, 1]})])
def test_all_existing_runtime_value_tags_preserve_owner_bytes(kind: str, value: object) -> None:
    root = fixture("typed_root_decimal")
    root["object"]["fields"][0]["value"] = {"value_kind": kind, "value": value}
    assert read.decode_typed_root(read.encode_typed_root(root)) == root


def test_request_byte_limit_is_inclusive_before_any_original_owner_work() -> None:
    req = fixture("request_A")
    origin = json.loads(bytes.fromhex(req["payload"]["origin_body"]["body_hex"]))
    def prepared(size: int) -> dict[str, Any]:
        local = copy.deepcopy(origin)
        local["api_request"] = B("fixture.api.v1", {"padding": "x" * size})
        seal(local, "origin_digest")
        value = copy.deepcopy(req)
        value["payload"]["origin_body"] = B(w.ORIGIN_CONTRACT, local)
        value["intent_digest"] = D(w.INTENT_CONTRACT, {k: v for k, v in value.items() if k not in ("intent_digest", "delivery")})
        return value
    zero = prepared(0)
    at = prepared((w.MAX_REQUEST_BYTES - len(C(zero))) // 4)
    remaining = w.MAX_REQUEST_BYTES - len(C(at))
    assert 0 <= remaining < 4
    at["delivery"]["delivery_ref"] += "x" * remaining
    assert len(read.encode_request(at)) == w.MAX_REQUEST_BYTES
    at["delivery"]["delivery_ref"] += "x"
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.encode_request(at)
    with pytest.raises(read.WireError, match="limit_exceeded"):
        read.decode_request(C(at))


@pytest.mark.parametrize("field,value", [("timeout_ms", 0), ("timeout_ms", 5001), ("timeout_ms", True),
                                         ("recipient_incarnation", ""), ("delivery_ref", "has space")])
def test_delivery_limits_and_refs(field: str, value: object) -> None:
    req = fixture("request_A")
    req["delivery"][field] = value
    with pytest.raises(read.WireError):
        read.encode_request(req)


@pytest.mark.parametrize("field,value", [("operation", {}), ("ordinal", 0), ("result_budget_bytes", True),
                                         ("result_budget_bytes", 0), ("result_budget_bytes", w.MAX_RESULT_BYTES + 1)])
def test_request_cannot_introduce_operation_or_ill_typed_budget(field: str, value: object) -> None:
    req = fixture("request_A")
    req[field] = value
    req["intent_digest"] = read.request_intent_digest(req)
    with pytest.raises(read.WireError):
        read.encode_request(req)
