"""Contract specimens only: no authentic issuer, owner, provider or VM calls."""

import copy
import hashlib
import json
import inspect
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import pytest

import aware_ontology_object_facade_client as facade
from aware_ontology_object_facade_client import wire


def test_shared_engine_matches_frozen_v1_parent_bytes_refusals_and_signatures(tmp_path: Path) -> None:
    """Import the qualified parent codec normally in an isolated scratch cut."""
    root = Path(__file__).resolve().parents[1]
    package = root / "aware_ontology_object_facade_client"
    parent = subprocess.run(["git", "cat-file", "blob", "4908701c5d77ad0e5be60268423e063875f9c182"],
                            cwd=root, check=True, capture_output=True).stdout
    assert len(parent) == 33_710
    assert hashlib.sha256(parent).hexdigest() == "d6f8f3c9e28f635f6f2553d693a1de3dd2e2a2d057a3edc2ad2ee92c7d5301c5"
    shutil.copytree(package, tmp_path / package.name, ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / package.name / "codec.py").write_bytes(parent)
    # Keep this scratch predecessor coherent: P2 preparation requires the v4
    # profile and is absent from the historical codec proof closure.
    parent_init = tmp_path / package.name / "__init__.py"
    init = parent_init.read_text().replace("from .preparation import PreparationError, prepare_operation\n\n", "")
    init = init.replace('__all__ += ["PreparationError", "prepare_operation"]\n', "")
    parent_init.write_text(init)
    corpus = [("encode_request", specimen_request(kind)) for kind in wire.COMMANDS]
    corpus += [("encode_result", specimen_result(kind, label)) for kind in wire.COMMANDS for label in LABELS]
    for kind in wire.COMMANDS:
        changed = specimen_request(kind)
        changed["unexpected"] = 1
        corpus.append(("encode_request", changed))
    corpus += [("canonical_bytes", value) for value in ([0] * 4096, [0] * 4097, "é" * 32767, "é" * 32768,
        B("fixture.opaque.v1", {"lower_float": 1.5}))]
    corpus += [("encode_rejection", {"contract": wire.REJECTION_CONTRACT, "code": code}) for code in
               ("malformed", "unsupported_profile", "owner_unavailable", "unexpected")]
    expected = []
    for name, value in corpus:
        try:
            expected.append(["ok", getattr(facade, name)(value).hex()])
        except facade.WireError as error:
            expected.append(["error", error.code])
    script = """
import inspect
import json
import sys
sys.path[:0] = sys.argv[1:3]
import aware_ontology_object_facade_client as facade
from aware_ontology_object_facade_client import codec
results = []
for name, value in json.load(sys.stdin):
    try:
        results.append(['ok', getattr(facade, name)(value).hex()])
    except facade.WireError as error:
        results.append(['error', error.code])
signatures = {name: str(inspect.signature(value)) for name, value in vars(codec).items()
              if inspect.isfunction(value) and not name.startswith('_') and value.__module__ == codec.__name__}
print(json.dumps(dict(results=results, signatures=signatures), sort_keys=True))
"""
    proc = subprocess.run([sys.executable, "-I", "-B", "-c", script, str(tmp_path),
                           str(root.parents[3] / "meta/libs/type_schema/python")],
                          input=C(corpus).decode(), text=True, capture_output=True, check=True, timeout=15)
    assert proc.stderr == ""
    actual = json.loads(proc.stdout)
    assert actual["results"] == expected
    from aware_ontology_object_facade_client import codec
    signatures = {name: str(inspect.signature(value)) for name, value in vars(codec).items()
                  if inspect.isfunction(value) and not name.startswith("_") and value.__module__ == codec.__name__}
    assert actual["signatures"] == signatures


def C(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def H(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def D(domain: str, value: object) -> str:
    return H(domain.encode("utf-8") + b"\x00" + C(value))


def B(contract: str, value: object) -> dict[str, Any]:
    raw = C(value)
    return {"contract_ref": contract, "body_hex": raw.hex(), "body_hash": H(raw)}


ORIGIN = dict(owner_ref="service:specimen", owner_generation="generation:1",
    journal_namespace_ref="journal:specimen", invocation_ref="invocation:1",
    attempt_ref="attempt:1", principal_ref="actor:1", entry_kind="raw")
OPERATION = dict(ontology_ref="ontology:specimen", branch_ref="branch:1", actor_ref="actor:1",
    projection_ref="projection:1", operation_ref="operation:1", idempotency_key="idempotency:1",
    object_abi_digest="sha256:" + "0" * 64, provider_ref="provider:specimen",
    provider_generation="generation:1", expected_revision_ref=None,
    base_operational_digest="sha256:" + "1" * 64)
DIGEST = "sha256:" + "2" * 64


def lower(name: str) -> dict[str, Any]:
    return B("specimen." + name + ".v1", {"name": name})


def signed(contract: str, key: str, **fields: object) -> dict[str, Any]:
    obj = dict(contract=contract, **fields)
    obj[key] = D(contract, obj)
    return obj


def bundle() -> dict[str, Any]:
    origin = signed("aware.ontology.facade-origin.v1", "origin_digest", origin=ORIGIN,
        api_request=lower("api"), service_binding=lower("binding"),
        service_admission=lower("admission"), function_plan=lower("plan"),
        experience_admission=None)
    facts = signed("aware.ontology.facade-facts.v1", "facts_digest", facts_ref="facts:1",
        host_incarnation="host:1", origin=ORIGIN, operation=OPERATION,
        topology_body=lower("topology"), schema_body=lower("schema"),
        schema_slice_body=lower("slice"), object_abi_body=lower("abi"),
        application_authority_body=lower("authority"), selection_facts_body=lower("selection"),
        selection_profile_body=lower("selection-profile"), precontact_profile_body=lower("precontact"),
        lifetime_ms=30_000)
    return signed("aware.ontology.facade-bundle.v1", "bundle_digest",
        origin_body=B(origin["contract"], origin), facts_body=B(facts["contract"], facts),
        activation_preimage=lower("activation"), execution_preimage=lower("execution"),
        selection_admission_body=lower("selection-admission"), attempt_body=lower("attempt"),
        attempt_admission_body=lower("attempt-admission"), precontact_profile_body=lower("precontact"))


def specimen_request(kind: str = "object.acquire") -> dict[str, Any]:
    prepared = bundle()
    arguments = B("aware.ontology.facade-arguments.v1", dict(
        contract="aware.ontology.facade-arguments.v1", action_ref="action:1",
        binding_digest=DIGEST, arguments=[]))
    payloads = {
        "facts.read": dict(selection=OPERATION, origin_body=prepared["origin_body"]),
        "view.read": dict(selection=OPERATION, origin_body=prepared["origin_body"]),
        "owner.verify": dict(purpose="initial_activation", requesting_host_incarnation="host:1",
            bundle=B(prepared["contract"], prepared), owner_preparation_record_ref="record:1",
            owner_preparation_record_digest=DIGEST, owner_head_revision=1, owner_head_digest=DIGEST,
            contact_claim_body=None, challenge="3" * 64, challenge_budget_ms=5_000),
        "owner.command_verify": dict(purpose="scope_command", requesting_host_incarnation="host:1",
            bundle_digest=DIGEST, command_ordinal=1,
            command_intent=B(wire.INTENT_CONTRACT, {k: v for k, v in specimen_request().items()
                if k not in ("intent_digest", "delivery")}) if kind == "owner.command_verify" else lower("unused"),
            owner_head_revision=1, owner_head_digest=DIGEST, challenge="3" * 64, challenge_budget_ms=5_000),
        "operation.activate": dict(bundle=B(prepared["contract"], prepared),
            owner_preparation_record_ref="record:1", owner_preparation_record_digest=DIGEST,
            contact_claim_body=None),
        "object.acquire": dict(session_ref="session:1", type_ref="type:1", instance_ref="instance:1",
                               binding_digest=DIGEST),
        "object.invoke": dict(session_ref="session:1", object_ref="object:1", action_ref="action:1",
                              binding_digest=DIGEST, arguments=arguments),
        "object.construct": dict(session_ref="session:1", type_ref="type:1", action_ref="action:1",
            binding_digest=DIGEST, new_instance_ref="instance:2", arguments=arguments),
        "operation.complete": dict(session_ref="session:1", last_command_ordinal=0,
                                   command_prefix_digest=DIGEST),
        "operation.abort": dict(session_ref="session:1", reason="explicit_abort",
            last_command_ordinal=0, command_prefix_digest=DIGEST),
        "operation.inspect": dict(bundle_digest=DIGEST, lower_recovery_ref="recovery:1",
            original_preparation_record_ref="record:1", original_preparation_record_digest=DIGEST),
        "command.inspect": dict(command_ordinal=1, command_intent_digest=DIGEST),
    }
    obj = dict(contract=wire.REQUEST_CONTRACT, kind=kind, origin=copy.deepcopy(ORIGIN),
        operation=None if kind in ("facts.read", "view.read") else copy.deepcopy(OPERATION),
        ordinal=0 if kind == "operation.activate" else 1 if kind in wire.ACTIVE_COMMANDS else None,
        payload=payloads[kind], result_budget_bytes=16_384,
        delivery=dict(delivery_ref="delivery:current", recipient_incarnation="host:1", timeout_ms=30_000))
    obj["intent_digest"] = D(wire.INTENT_CONTRACT, {k: v for k, v in obj.items() if k != "delivery"})
    return obj


def specimen_value(kind: str) -> dict[str, Any]:
    prepared = bundle()
    return {
        "facts.read": dict(facts=prepared["facts_body"]),
        "view.read": dict(view=lower("view")),
        "owner.verify": dict(challenge="3" * 64, requesting_host_incarnation="host:1",
            bundle_digest=prepared["bundle_digest"], owner_profile_ref="profile:1", owner_generation="generation:1",
            preparation_record=lower("preparation-record"), owner_head=lower("head"),
            preparation_reread=lower("preparation-reread"), head_reread=lower("head-reread"),
            contact_claim=None, initial_contact_state="unclaimed"),
        "owner.command_verify": dict(challenge="3" * 64, requesting_host_incarnation="host:1",
            bundle_digest=DIGEST, command_ordinal=1, command_intent_digest=specimen_request()["intent_digest"],
            owner_profile_ref="profile:1", owner_generation="generation:1", owner_head=lower("head"),
            head_reread=lower("head-reread"), initial_contact_claim=None, command_phase="contact_claimed"),
        "operation.activate": dict(session_ref="session:1", host_incarnation="host:1",
                                   bundle_digest=prepared["bundle_digest"], remaining_ms=30_000),
        "object.acquire": dict(object_ref="object:1", snapshot=lower("snapshot")),
        "object.invoke": dict(action_digest=DIGEST, return_value=dict(tag="void"), snapshots=[]),
        "object.construct": dict(action_digest=DIGEST, return_value=dict(tag="object_target",
            value={"tag": "instance_ref", "type_ref": "type:1", "provider_key": "provider:specimen",
                   "provider_generation": "generation:1", "instance_ref": "instance:2"}), snapshots=[]),
        "operation.complete": dict(receipt=lower("receipt"), result_view=lower("view"),
            result_revision_ref="revision:2", result_operational_digest=DIGEST),
        "operation.abort": dict(abort_evidence=lower("abort")),
        "operation.inspect": dict(recovery_evidence=lower("recovery"), terminal_completion=None),
        "command.inspect": dict(command_phase="reserved", stored_result=None),
    }[kind]


EXPECTED_ROLES = {
    "facts.read": {"command_outcome", "facts_issuance"},
    "view.read": {"command_outcome", "view_observation"},
    "owner.verify": {"command_outcome", "owner_preparation", "owner_head", "owner_reread"},
    "owner.command_verify": {"command_outcome", "owner_head", "owner_reread"},
    "operation.activate": {"command_outcome", "provider_fence"},
    "object.acquire": {"command_outcome"}, "object.invoke": {"command_outcome"},
    "object.construct": {"command_outcome"},
    "operation.complete": {"command_outcome", "operation_completion"},
    "operation.abort": {"command_outcome", "operation_completion"},
    "operation.inspect": {"command_outcome", "historical_recovery"},
    "command.inspect": {"command_outcome", "owner_head", "owner_reread"},
}
VALUE_FIELDS = {"facts_issuance": "facts", "view_observation": "view",
    "owner_preparation": "preparation_record", "owner_head": "owner_head",
    "owner_reread": "head_reread", "historical_recovery": "recovery_evidence"}


def seal_result(obj: dict[str, Any]) -> dict[str, Any]:
    obj = copy.deepcopy(obj)
    projection = {k: v for k, v in obj.items() if k not in ("witnesses", "result_digest")}
    for witness in obj["witnesses"]:
        if witness["role"] != "command_outcome":
            continue
        observation = json.loads(bytes.fromhex(witness["body"]["body_hex"]))
        for field in ("origin", "operation", "ordinal", "intent_digest", "responder_incarnation"):
            observation[field] = obj[field]
        observation["outcome_hash"] = H(C(dict(contract=wire.PREIMAGE_CONTRACT, result=projection)))
        observation.pop("observation_digest", None)
        observation["observation_digest"] = D(wire.OBSERVATION_CONTRACT, observation)
        witness["body"] = B(wire.OBSERVATION_CONTRACT, observation)
    value = obj["outcome"].get("value", {})
    obj["witnesses"].sort(key=lambda x: (x["role"], x["issuer_ref"],
        (x["body"] if x["body"] is not None else value[x["value_field"]])["body_hash"]))
    obj.pop("result_digest", None)
    obj["result_digest"] = D(wire.RESULT_CONTRACT, obj)
    return obj


def specimen_result(kind: str = "object.acquire", label: str = "ok") -> dict[str, Any]:
    req = specimen_request(kind)
    obj = {k: copy.deepcopy(req[k]) for k in ("kind", "origin", "operation", "ordinal", "intent_digest")}
    obj.update(contract=wire.RESULT_CONTRACT, delivery_ref="delivery:current",
               responder_incarnation="host:1")
    if label == "ok":
        finality = ("observation" if kind in wire.COMMANDS[:4] else "historical" if kind in
            ("operation.inspect", "command.inspect") else "scope_complete" if kind in
            ("operation.complete", "operation.abort") else "provisional")
        outcome: dict[str, Any] = dict(tag="ok", value=specimen_value(kind), finality=finality)
        roles = EXPECTED_ROLES[kind]
    elif label.startswith("replay"):
        original = specimen_result(kind)
        original["delivery_ref"] = "delivery:original"
        original = seal_result(original)
        historical = label.endswith("historical")
        outcome = dict(tag="replay", mode="historical" if historical else "active",
            stored_result=B(wire.RESULT_CONTRACT, original),
            original_command_intent_digest=obj["intent_digest"],
            association=dict(contract=wire.ASSOCIATION_CONTRACT,
                original_result_digest=original["result_digest"], original_delivery_ref="delivery:original",
                original_responder_incarnation="host:1", original_session_ref="session:1",
                observing_host_incarnation="host:2" if historical else "host:1",
                current_session_ref=None if historical else "session:1"))
        roles = {"command_outcome", "owner_head", "owner_reread",
                 "historical_recovery" if historical else "provider_fence"}
        obj["responder_incarnation"] = "host:2" if historical else "host:1"
    else:
        outcome = dict(tag=label, code="indeterminate_contact" if label == "indeterminate" else
            "command_in_progress" if label == "pending" else "owner_unavailable",
            stage="execution", command_contact="possible", operation_contact="possible", recovery_ref=None)
        roles = {"command_outcome", "owner_head", "owner_reread"} if label == "pending" else {"command_outcome"}
    obj["outcome"] = outcome
    witnesses = []
    for role in roles:
        field = VALUE_FIELDS.get(role) if label == "ok" else None
        if field not in outcome.get("value", {}):
            field = None
        if role == "operation_completion":
            field = "receipt" if kind == "operation.complete" else "abort_evidence"
        if role == "command_outcome":
            observation = dict(contract=wire.OBSERVATION_CONTRACT, role="command_outcome",
                origin=obj["origin"], operation=obj["operation"], ordinal=obj["ordinal"],
                intent_digest=obj["intent_digest"], outcome_hash=DIGEST,
                responder_incarnation=obj["responder_incarnation"],
                session_ref=None if kind in wire.COMMANDS[:4] else "session:1",
                source_observation=lower("source"))
            observation["observation_digest"] = D(wire.OBSERVATION_CONTRACT, observation)
            body = B(wire.OBSERVATION_CONTRACT, observation)
        else:
            body = None if field else lower(role)
        witnesses.append(dict(role=role, issuer_ref="issuer:" + role,
            issuer_generation="generation:1", body=body, value_field=field))
    if label == "ok" and kind == "owner.verify":
        witnesses.append(dict(role="owner_reread", issuer_ref="issuer:owner_reread",
            issuer_generation="generation:1", body=None, value_field="preparation_reread"))
    obj["witnesses"] = witnesses
    return seal_result(obj)


LABELS = ("ok", "refused", "unavailable", "pending", "indeterminate", "replay.active", "replay.historical")
SUPPORTED = [(k, t) for k in wire.COMMANDS for t in LABELS if
    t in ("ok", "refused", "unavailable") or k in wire.ACTIVE_COMMANDS and
    (t != "replay.active" or k not in ("operation.complete", "operation.abort"))]
FORBIDDEN = [(k, t) for k in wire.COMMANDS for t in LABELS if (k, t) not in SUPPORTED]


def test_closed_matrix_cardinality() -> None:
    assert (len(SUPPORTED), len(FORBIDDEN)) == (58, 26)


@pytest.mark.parametrize("kind", wire.COMMANDS)
def test_every_request_round_trips(kind: str) -> None:
    value = specimen_request(kind)
    assert facade.encode_request(value) == C(value)
    assert facade.decode_request(C(value)) == value


@pytest.mark.parametrize("kind,label", SUPPORTED)
def test_every_supported_outcome_cell(kind: str, label: str) -> None:
    value = specimen_result(kind, label)
    raw = facade.encode_result(value)
    assert raw == C(value)
    assert facade.decode_result(raw) == value
    req = specimen_request(kind)
    req["delivery"]["recipient_incarnation"] = value["responder_incarnation"]
    facade.match_result(req, value)


@pytest.mark.parametrize("kind,label", FORBIDDEN)
def test_every_forbidden_outcome_cell(kind: str, label: str) -> None:
    value = specimen_result(kind, label)
    with pytest.raises(facade.WireError):
        facade.decode_result(C(value))


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a": 1}', b'{"a":1} ',
    b'{"b":1,"a":2}', b'"\\u0061"', b'"\\ud800"', b'NaN', b'Infinity', b'1.0',
    b'1e0', b'-0', b'01', b'{}{}', b'"\xff"', b'[]\x00'])
def test_noncanonical_or_invalid_bytes_refuse(raw: bytes) -> None:
    with pytest.raises(facade.WireError):
        facade.decode_canonical(raw)


@pytest.mark.parametrize("value", [1.0, float("nan"), {1: "value"}, (1,), b"bytes", "\ud800"])
def test_non_native_scalar_or_container_refuses(value: object) -> None:
    with pytest.raises(facade.WireError):
        facade.canonical_bytes(value)


def test_native_subclasses_and_cycles_refuse() -> None:
    class HostileDict(dict):
        def items(self):
            raise AssertionError("foreign body called")
    with pytest.raises(facade.WireError):
        facade.canonical_bytes(HostileDict(a=1))
    cycle: list[Any] = []
    cycle.append(cycle)
    with pytest.raises(facade.WireError):
        facade.canonical_bytes(cycle)


@pytest.mark.parametrize("location", ["root", "object", "array", "nested"])
def test_native_class_admission_never_calls_foreign_metaclass_equality(location: str) -> None:
    calls: list[object] = []

    class ForeignMeta(type):
        def __eq__(cls, other: object) -> bool:
            calls.append(other)
            return False

    class ForeignValue(metaclass=ForeignMeta):
        pass

    foreign = ForeignValue()
    values = {
        "root": foreign,
        "object": {"value": foreign},
        "array": [foreign],
        "nested": {"value": [True, None, {"nested": foreign}]},
    }
    with pytest.raises(facade.WireError, match="malformed"):
        facade.canonical_bytes(values[location])
    assert calls == []


@pytest.mark.parametrize("field", ["contract", "code"])
@pytest.mark.parametrize("shape", ["instance", "string_subclass", "nested_object", "nested_array"])
def test_rejection_exact_field_admission_precedes_foreign_comparison(field: str, shape: str) -> None:
    calls: list[object] = []

    class ForeignMeta(type):
        def __eq__(cls, other: object) -> bool:
            calls.append(other)
            return False

    class ForeignValue(metaclass=ForeignMeta):
        def __eq__(self, other: object) -> bool:
            calls.append(other)
            return False

        def __ne__(self, other: object) -> bool:
            calls.append(other)
            return True

    class ForeignString(str):
        def __eq__(self, other: object) -> bool:
            calls.append(other)
            return False

        def __ne__(self, other: object) -> bool:
            calls.append(other)
            return True

    foreign = ForeignValue()
    fields = {
        "instance": foreign,
        "string_subclass": ForeignString(wire.REJECTION_CONTRACT if field == "contract" else "malformed"),
        "nested_object": {"nested": foreign},
        "nested_array": [True, None, foreign],
    }
    obj: dict[str, Any] = dict(contract=wire.REJECTION_CONTRACT, code="malformed")
    obj[field] = fields[shape]
    with pytest.raises(facade.WireError, match="malformed"):
        facade.encode_rejection(obj)
    assert calls == []


def test_rejection_admits_both_field_types_before_contract_comparison() -> None:
    calls: list[object] = []

    class ForeignValue:
        def __eq__(self, other: object) -> bool:
            calls.append(other)
            return False

    with pytest.raises(facade.WireError, match="malformed"):
        facade.encode_rejection(dict(contract="unsupported:native-contract", code=ForeignValue()))
    assert calls == []


def test_digest_helpers_refuse_foreign_keys_before_equality_dispatch() -> None:
    calls = []
    class ForeignKey:
        def __hash__(self):
            return 1
        def __eq__(self, other):
            calls.append(other)
            return False
    value = {ForeignKey(): "untrusted"}
    for helper in (facade.request_intent_digest, facade.result_digest, facade.outcome_preimage):
        with pytest.raises(facade.WireError):
            helper(value)
    assert calls == []


@pytest.mark.parametrize("kind", wire.COMMANDS)
@pytest.mark.parametrize("location", ["envelope", "origin", "operation", "payload", "delivery"])
def test_unknown_request_members_refuse(kind: str, location: str) -> None:
    value = specimen_request(kind)
    if location == "operation" and value["operation"] is None:
        value["operation"] = dict(extra=1)
    else:
        target = value if location == "envelope" else value[location]
        target["extra"] = "unapproved"
    value["intent_digest"] = facade.request_intent_digest(value)
    with pytest.raises(facade.WireError):
        facade.encode_request(value)


@pytest.mark.parametrize("kind", wire.COMMANDS)
def test_cross_kind_payloads_refuse(kind: str) -> None:
    value = specimen_request(kind)
    other = "object.acquire" if kind != "object.acquire" else "operation.inspect"
    value["payload"] = specimen_request(other)["payload"]
    value["intent_digest"] = facade.request_intent_digest(value)
    with pytest.raises(facade.WireError):
        facade.encode_request(value)


@pytest.mark.parametrize("value", [True, -1, wire.MAX_COUNTER + 1, 1.0, "1", None])
def test_exact_counter_rule(value: object) -> None:
    req = specimen_request("owner.verify")
    req["payload"]["owner_head_revision"] = value
    with pytest.raises(facade.WireError):
        req["intent_digest"] = facade.request_intent_digest(req)
        facade.encode_request(req)


def test_delivery_not_in_intent_and_budget_is_in_intent() -> None:
    req = specimen_request()
    changed = copy.deepcopy(req)
    changed["delivery"] = dict(delivery_ref="delivery:retry", recipient_incarnation="host:2", timeout_ms=1)
    assert facade.encode_request(changed) != facade.encode_request(req)
    assert facade.request_intent_digest(changed) == req["intent_digest"]
    changed["result_budget_bytes"] -= 1
    with pytest.raises(facade.WireError):
        facade.encode_request(changed)


@pytest.mark.parametrize("field,value", [("kind", "object.invoke"), ("ordinal", 2),
    ("origin", dict(ORIGIN, principal_ref="actor:other")),
    ("operation", dict(OPERATION, branch_ref="branch:other")), ("delivery_ref", "delivery:other")])
def test_complete_response_correlation(field: str, value: object) -> None:
    result = specimen_result()
    if field == "kind":
        result = specimen_result("object.invoke")
    else:
        result[field] = value
        result = seal_result(result)
    with pytest.raises(facade.WireError):
        facade.match_result(specimen_request(), result)


@pytest.mark.parametrize("kind,label", SUPPORTED)
def test_missing_required_role_refuses(kind: str, label: str) -> None:
    result = specimen_result(kind, label)
    result["witnesses"] = [x for x in result["witnesses"] if x["role"] != "command_outcome"]
    result = seal_result(result)
    with pytest.raises(facade.WireError):
        facade.encode_result(result)


def test_witness_order_uniqueness_and_no_settlement_smuggling() -> None:
    result = specimen_result("owner.verify")
    for mutate in (lambda x: x["witnesses"].reverse(),
        lambda x: x["witnesses"].append(copy.deepcopy(x["witnesses"][0])),
        lambda x: x["witnesses"].append(dict(role="service_settlement", issuer_ref="issuer:1",
            issuer_generation="generation:1", body=lower("settlement"), value_field=None))):
        altered = copy.deepcopy(result)
        mutate(altered)
        altered["result_digest"] = facade.result_digest(altered)
        with pytest.raises(facade.WireError):
            facade.encode_result(altered)


def test_positive_owner_rereads_and_claim_structure() -> None:
    result = specimen_result("owner.verify")
    result["outcome"]["value"]["contact_claim"] = lower("claim")
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))
    result["witnesses"].append(dict(role="owner_contact_claim", issuer_ref="issuer:claim",
        issuer_generation="generation:1", body=None, value_field="contact_claim"))
    assert facade.decode_result(facade.encode_result(seal_result(result)))
    result["witnesses"] = [x for x in result["witnesses"] if x["value_field"] != "preparation_reread"]
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


@pytest.mark.parametrize("label", ["refused", "unavailable", "pending", "indeterminate", "replay.historical"])
def test_non_success_and_replay_cannot_use_value_fields(label: str) -> None:
    result = specimen_result(label=label)
    result["witnesses"][0].update(body=None, value_field="facts")
    result["result_digest"] = facade.result_digest(result)
    with pytest.raises(facade.WireError):
        facade.encode_result(result)


@pytest.mark.parametrize("label", ["refused", "unavailable", "indeterminate"])
def test_recovery_role_required_only_when_coordinate_present(label: str) -> None:
    result = specimen_result(label=label)
    result["outcome"]["recovery_ref"] = "recovery:1"
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))
    result["witnesses"].append(dict(role="historical_recovery", issuer_ref="issuer:recovery",
        issuer_generation="generation:1", body=lower("recovery"), value_field=None))
    assert facade.encode_result(seal_result(result))


def test_nested_replay_refuses_even_with_recomputed_data_hashes() -> None:
    result = specimen_result(label="replay.historical")
    nested = specimen_result(label="replay.active")
    result["outcome"]["stored_result"] = B(wire.RESULT_CONTRACT, nested)
    result["outcome"]["association"]["original_result_digest"] = nested["result_digest"]
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


@pytest.mark.parametrize("mode", ["active", "historical"])
@pytest.mark.parametrize("member", ["original_session_ref", "current_session_ref",
    "original_result_digest", "original_delivery_ref", "original_responder_incarnation",
    "observing_host_incarnation"])
def test_replay_association_substitutions_refuse(mode: str, member: str) -> None:
    result = specimen_result(label="replay." + mode)
    assoc = result["outcome"]["association"]
    assoc[member] = "sha256:" + "4" * 64 if member.endswith("digest") else "different:1"
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


def test_generic_limits_at_ceiling_and_one_beyond() -> None:
    assert len(facade.canonical_bytes("a" * (wire.MAX_MESSAGE_BYTES - 2))) == wire.MAX_MESSAGE_BYTES
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.canonical_bytes("a" * (wire.MAX_MESSAGE_BYTES - 1))
    assert facade.decode_canonical(C([0] * wire.MAX_ENTRIES)) == [0] * wire.MAX_ENTRIES
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.decode_canonical(C([0] * (wire.MAX_ENTRIES + 1)))
    at = b"[" * wire.MAX_DEPTH + b"0" + b"]" * wire.MAX_DEPTH
    assert facade.decode_canonical(at)
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.decode_canonical(b"[" + at + b"]")
    assert facade.make_body("owner:opaque", b"x" * wire.MAX_BODY_BYTES)
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.make_body("owner:opaque", b"x" * (wire.MAX_BODY_BYTES + 1))


def test_aggregate_budget_counts_repeated_decoded_bodies() -> None:
    body = B("specimen.array.v1", [0] * 4092)
    assert facade.canonical_bytes([body])
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.decode_canonical(C([body, body]))
    nested = B("specimen.depth.v1", [[0]])
    raw = b"[" * 31 + C(nested) + b"]" * 31
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.decode_canonical(raw)


def test_owner_bytes_preserved_without_semantic_codec_or_normalization() -> None:
    raw = b'{ "decimal": "1.00", "integer": "999999999999999999999999", "float": 1.5 }'
    body = facade.make_body("owner:fixed-contract", raw)
    assert bytes.fromhex(body["body_hex"]) == raw
    assert body["body_hash"] == H(raw)
    assert facade.make_body("owner:binary-contract", b"\xff\x00")["body_hex"] == "ff00"


@pytest.mark.parametrize("field,bad", [("contract_ref", ""), ("body_hex", "AA"),
    ("body_hex", "a"), ("body_hex", ""), ("body_hash", "sha256:" + "A" * 64)])
def test_body_closed_framing_refuses(field: str, bad: str) -> None:
    body = lower("body")
    body[field] = bad
    with pytest.raises(facade.WireError):
        facade.decode_canonical(C(body))


def test_rejection_has_no_caller_echo_or_business_witness() -> None:
    for code in ("malformed", "unsupported_contract", "limit_exceeded"):
        obj = dict(contract=wire.REJECTION_CONTRACT, code=code)
        assert facade.decode_rejection(facade.encode_rejection(obj)) == obj
    for obj in (dict(contract=wire.REJECTION_CONTRACT, code="unauthorized"),
                dict(contract=wire.REJECTION_CONTRACT, code="malformed", origin=ORIGIN)):
        with pytest.raises(facade.WireError):
            facade.encode_rejection(obj)


def test_command_prefix_only_closes_contiguous_delivery_order() -> None:
    entries = [dict(ordinal=i, intent_digest=DIGEST, result_digest=DIGEST) for i in range(63)]
    assert facade.command_prefix_digest(entries) == D(wire.PREFIX_CONTRACT, entries)
    with pytest.raises(facade.WireError):
        facade.command_prefix_digest(entries + [dict(ordinal=63, intent_digest=DIGEST, result_digest=DIGEST)])
    entries[1]["ordinal"] = 2
    with pytest.raises(facade.WireError):
        facade.command_prefix_digest(entries)


def frozen_vectors() -> dict[str, Any]:
    """Independent literal specimens from accepted F0.2 section 6.3."""
    def projection(outcome: object, delivery: str = "delivery:current", responder: str = "host:1"):
        return dict(contract=wire.RESULT_CONTRACT, kind="object.acquire", origin=ORIGIN,
            operation=OPERATION, ordinal=1, intent_digest=DIGEST, delivery_ref=delivery,
            responder_incarnation=responder, outcome=outcome)

    def preimage(value: object):
        return dict(contract=wire.PREIMAGE_CONTRACT, result=value)

    ok = dict(tag="ok", finality="provisional", value=dict(object_ref="object:1",
        snapshot=B("specimen.snapshot.v1", dict(contract="specimen.snapshot.v1", object_ref="object:1"))))
    original_projection = projection(ok, "delivery:original")
    observation = dict(contract=wire.OBSERVATION_CONTRACT, role="command_outcome", origin=ORIGIN,
        operation=OPERATION, ordinal=1, intent_digest=DIGEST,
        outcome_hash=H(C(preimage(original_projection))), responder_incarnation="host:1",
        session_ref="session:1", source_observation=None)
    observation["observation_digest"] = D(wire.OBSERVATION_CONTRACT, observation)
    original = dict(original_projection, witnesses=[dict(role="command_outcome", issuer_ref="ontology:specimen",
        issuer_generation="generation:1", body=B(wire.OBSERVATION_CONTRACT, observation), value_field=None)])
    original["result_digest"] = D(wire.RESULT_CONTRACT, original)

    def failure(tag: str, code: str, stage: str, command: str, operation: str):
        return dict(tag=tag, code=code, stage=stage, command_contact=command,
                    operation_contact=operation, recovery_ref=None)

    def replay(mode: str):
        return dict(tag="replay", mode=mode, stored_result=B(wire.RESULT_CONTRACT, original),
            original_command_intent_digest=DIGEST, association=dict(contract=wire.ASSOCIATION_CONTRACT,
                original_result_digest=original["result_digest"], original_delivery_ref="delivery:original",
                original_responder_incarnation="host:1", original_session_ref="session:1",
                observing_host_incarnation="host:1" if mode == "active" else "host:2",
                current_session_ref="session:1" if mode == "active" else None))

    outcomes = {
        "ok": ok,
        "refused": failure("refused", "binding_mismatch", "selection", "not_started", "observed"),
        "unavailable": failure("unavailable", "owner_unavailable", "owner_verification", "not_started", "observed"),
        "pending": failure("pending", "command_in_progress", "execution", "observed", "observed"),
        "indeterminate": failure("indeterminate", "indeterminate_contact", "execution", "possible", "possible"),
        "replay.active": replay("active"), "replay.historical": replay("historical"),
    }
    return {name: preimage(projection(outcome, responder="host:2" if name == "replay.historical" else "host:1"))
            for name, outcome in outcomes.items()}


FROZEN_PAIRS = {
    "ok": (1364, "ab99ce35e3d8dafe7cef49d382efe5a295bef20b09610c5face6de0bcb7ff10a"),
    "refused": (1170, "49726e22fc26e55837909b6b09291992829e51135c27d575d61b16afbd042e02"),
    "unavailable": (1184, "04b627f648eb99b919776c8bd0e185b147ab90fc686f5dd72ca0a880e829177b"),
    "pending": (1170, "2015fea4c7b2b879a6d4fd5041276afbf98a5c0995ad0cf6087a9bb516d58a9d"),
    "indeterminate": (1178, "7010dcd0b73663772749013c21d97e81706a4f44244f6e585baa58871225d02c"),
    "replay.active": (9723, "8322ce2f0eb43d70ca9249b66f9179b4c96bd812f984392ac953609bdbd733f4"),
    "replay.historical": (9720, "0aa49796caad65df3c017f517b32211d24636219d99d546d8c38e445cd640888"),
}


@pytest.mark.parametrize("name", FROZEN_PAIRS)
def test_seven_frozen_preimage_lengths_and_hashes(name: str) -> None:
    preimage = frozen_vectors()[name]
    raw = facade.canonical_bytes(facade.outcome_preimage(preimage["result"]))
    size, digest = FROZEN_PAIRS[name]
    assert raw == C(preimage)
    assert (len(raw), facade.outcome_hash(preimage["result"])) == (size, "sha256:" + digest)


def test_twenty_retained_preimage_substitutions() -> None:
    vectors = frozen_vectors()
    comparisons = 0
    for name, original in vectors.items():
        expected = "sha256:" + FROZEN_PAIRS[name][1]
        for variant in ("tag", "caller"):
            changed = copy.deepcopy(original)
            if variant == "tag":
                tag = changed["result"]["outcome"]["tag"]
                changed["result"]["outcome"]["tag"] = "refused" if tag != "refused" else "unavailable"
            else:
                changed["result"]["origin"]["principal_ref"] = "actor:other"
            assert facade.outcome_hash(changed["result"]) != expected
            comparisons += 1
    for name in ("replay.active", "replay.historical"):
        expected = "sha256:" + FROZEN_PAIRS[name][1]
        for variant in ("witness", "mode", "session"):
            changed = copy.deepcopy(vectors[name])
            replay = changed["result"]["outcome"]
            if variant == "witness":
                original = json.loads(bytes.fromhex(replay["stored_result"]["body_hex"]))
                original["witnesses"][0]["issuer_generation"] = "generation:other"
                original.pop("result_digest")
                original["result_digest"] = D(wire.RESULT_CONTRACT, original)
                replay["stored_result"] = B(wire.RESULT_CONTRACT, original)
                replay["association"]["original_result_digest"] = original["result_digest"]
            elif variant == "mode":
                replay["mode"] = "historical" if replay["mode"] == "active" else "active"
            else:
                replay["association"]["original_session_ref"] = "session:other"
            assert facade.outcome_hash(changed["result"]) != expected
            comparisons += 1
    assert comparisons == 20


@pytest.mark.parametrize("member", ["tag", "code", "stage", "command_contact", "operation_contact", "recovery_ref"])
def test_retained_failure_observation_rejects_each_changed_member(member: str) -> None:
    result = specimen_result(label="unavailable")
    replacements = dict(tag="refused", code="unauthorized", stage="selection", command_contact="observed",
                        operation_contact="observed", recovery_ref="recovery:other")
    result["outcome"][member] = replacements[member]
    result["result_digest"] = facade.result_digest(result)
    with pytest.raises(facade.WireError):
        facade.encode_result(result)


def test_session_evidence_matches_activation_value_and_replay() -> None:
    result = specimen_result("operation.activate")
    witness = next(x for x in result["witnesses"] if x["role"] == "command_outcome")
    observation = json.loads(bytes.fromhex(witness["body"]["body_hex"]))
    observation["session_ref"] = "session:other"
    observation.pop("observation_digest")
    observation["observation_digest"] = D(wire.OBSERVATION_CONTRACT, observation)
    witness["body"] = B(wire.OBSERVATION_CONTRACT, observation)
    result["result_digest"] = facade.result_digest(result)
    with pytest.raises(facade.WireError):
        facade.encode_result(result)


@pytest.mark.parametrize("count", [32, 33])
def test_snapshot_update_ceiling(count: int) -> None:
    result = specimen_result("object.invoke")
    result["outcome"]["value"]["snapshots"] = [dict(object_ref=f"object:{i:02}", snapshot=lower("snapshot"))
        for i in range(count)]
    result = seal_result(result)
    if count == 32:
        assert facade.encode_result(result)
    else:
        with pytest.raises(facade.WireError, match="limit_exceeded"):
            facade.encode_result(result)


@pytest.mark.parametrize("count", [16, 17])
def test_witness_entry_ceiling(count: int) -> None:
    result = specimen_result(label="pending")
    while len(result["witnesses"]) < count:
        n = len(result["witnesses"])
        result["witnesses"].append(dict(role="owner_reread", issuer_ref="issuer:owner_reread",
            issuer_generation="generation:1", body=lower(f"head-reread:{n}"), value_field=None))
    result = seal_result(result)
    if count == 16:
        assert facade.encode_result(result)
    else:
        with pytest.raises(facade.WireError, match="limit_exceeded"):
            facade.encode_result(result)


@pytest.mark.parametrize("size", [512, 513])
def test_ref_utf8_byte_ceiling(size: int) -> None:
    req = specimen_request()
    req["payload"]["instance_ref"] = "é" * (size // 2) + ("x" if size % 2 else "")
    req["intent_digest"] = facade.request_intent_digest(req)
    if size == 512:
        assert facade.encode_request(req)
    else:
        with pytest.raises(facade.WireError, match="limit_exceeded"):
            facade.encode_request(req)


@pytest.mark.parametrize("kind,member,ceiling", [("owner.verify", "challenge_budget_ms", 5_000),
    ("owner.verify", "owner_head_revision", wire.MAX_COUNTER)])
def test_request_numeric_ceiling(kind: str, member: str, ceiling: int) -> None:
    req = specimen_request(kind)
    req["payload"][member] = ceiling
    req["intent_digest"] = facade.request_intent_digest(req)
    assert facade.encode_request(req)
    req["payload"][member] = ceiling + 1
    req["intent_digest"] = facade.request_intent_digest(req)
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.encode_request(req)


def test_delivery_result_budget_and_last_ordinal_boundaries() -> None:
    req = specimen_request()
    req["delivery"]["timeout_ms"] = 30_001
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.encode_request(req)
    req = specimen_request()
    req["result_budget_bytes"] = 16_385
    req["intent_digest"] = facade.request_intent_digest(req)
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.encode_request(req)
    req = specimen_request()
    req["ordinal"] = 63
    req["intent_digest"] = facade.request_intent_digest(req)
    assert facade.encode_request(req)
    req["ordinal"] = 64
    req["intent_digest"] = facade.request_intent_digest(req)
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.encode_request(req)
    req = specimen_request("operation.complete")
    req["ordinal"] = 63
    req["payload"]["last_command_ordinal"] = 62
    req["intent_digest"] = facade.request_intent_digest(req)
    assert facade.encode_request(req)
    req["payload"]["last_command_ordinal"] = 63
    req["intent_digest"] = facade.request_intent_digest(req)
    with pytest.raises(facade.WireError):
        facade.encode_request(req)


@pytest.mark.parametrize("kind,label,role", [
    (kind, label, role)
    for kind, label in SUPPORTED
    for role in (EXPECTED_ROLES[kind] if label == "ok" else
        {"command_outcome", "owner_head", "owner_reread"} if label == "pending" else
        {"command_outcome", "owner_head", "owner_reread", "provider_fence"} if label == "replay.active" else
        {"command_outcome", "owner_head", "owner_reread", "historical_recovery"} if label == "replay.historical" else
        {"command_outcome"})
    if role != "command_outcome"
])
def test_each_other_required_role_cannot_be_omitted(kind: str, label: str, role: str) -> None:
    result = specimen_result(kind, label)
    result["witnesses"] = [x for x in result["witnesses"] if x["role"] != role]
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


@pytest.mark.parametrize("member", ["contract", "outcome", "origin", "operation", "witnesses"])
def test_extra_result_members_refuse(member: str) -> None:
    result = specimen_result()
    if member == "contract":
        result["extra"] = "undeclared"
    elif member == "witnesses":
        result["witnesses"][0]["extra"] = "undeclared"
    else:
        result[member]["extra"] = "undeclared"
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


@pytest.mark.parametrize("kind", wire.COMMANDS)
def test_exact_success_value_and_finality_are_command_specific(kind: str) -> None:
    result = specimen_result(kind)
    result["outcome"]["value"]["extra"] = 1
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))
    result = specimen_result(kind)
    result["outcome"]["finality"] = "observation" if result["outcome"]["finality"] != "observation" else "historical"
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


@pytest.mark.parametrize("variant", ["contract", "hash", "value_field", "source", "session"])
def test_observation_framing_and_inflight_provenance(variant: str) -> None:
    result = specimen_result(label="pending")
    witness = next(x for x in result["witnesses"] if x["role"] == "command_outcome")
    observation = json.loads(bytes.fromhex(witness["body"]["body_hex"]))
    if variant == "contract":
        witness["body"]["contract_ref"] = "specimen.not-outcome.v1"
    elif variant == "value_field":
        witness.update(body=None, value_field="owner_head")
    else:
        if variant == "hash":
            observation["outcome_hash"] = DIGEST
        elif variant == "source":
            observation["source_observation"] = None
        else:
            observation["session_ref"] = "\x00"
        observation.pop("observation_digest")
        observation["observation_digest"] = D(wire.OBSERVATION_CONTRACT, observation)
        witness["body"] = B(wire.OBSERVATION_CONTRACT, observation)
    result["result_digest"] = facade.result_digest(result)
    with pytest.raises(facade.WireError):
        facade.encode_result(result)


def test_lost_contact_stays_indeterminate_and_observed_needs_lower_body() -> None:
    result = specimen_result(label="indeterminate")
    result["outcome"]["command_contact"] = "not_started"
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))
    result = specimen_result(label="refused")
    result["outcome"]["operation_contact"] = "observed"
    witness = next(x for x in result["witnesses"] if x["role"] == "command_outcome")
    obs = json.loads(bytes.fromhex(witness["body"]["body_hex"]))
    obs["source_observation"] = None
    witness["body"] = B(wire.OBSERVATION_CONTRACT, obs)
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


def test_budget_correlation_owner_challenge_and_recipient_refuse() -> None:
    req = specimen_request()
    result = specimen_result()
    req["delivery"]["recipient_incarnation"] = "host:other"
    with pytest.raises(facade.WireError):
        facade.match_result(req, result)
    req = specimen_request()
    req["result_budget_bytes"] = 1
    req["intent_digest"] = facade.request_intent_digest(req)
    result["intent_digest"] = req["intent_digest"]
    with pytest.raises(facade.WireError, match="limit_exceeded"):
        facade.match_result(req, seal_result(result))
    result = specimen_result("owner.verify")
    result["outcome"]["value"]["challenge"] = "4" * 64
    with pytest.raises(facade.WireError):
        facade.match_result(specimen_request("owner.verify"), seal_result(result))


@pytest.mark.parametrize("text", ["", "ref withspace", "ref:\x00", "ref:\n", "ref:\u00a0", "ref:\ud800"])
def test_refs_are_scalar_opaque_nonempty_and_without_whitespace(text: str) -> None:
    req = specimen_request()
    req["payload"]["type_ref"] = text
    with pytest.raises(facade.WireError):
        req["intent_digest"] = facade.request_intent_digest(req)
        facade.encode_request(req)


def test_unicode_refs_are_not_normalized() -> None:
    req = specimen_request()
    req["payload"]["type_ref"] = "type:é"
    req["intent_digest"] = facade.request_intent_digest(req)
    raw = facade.encode_request(req)
    req["payload"]["type_ref"] = "type:e\u0301"
    req["intent_digest"] = facade.request_intent_digest(req)
    assert facade.encode_request(req) != raw


def test_actual_snapshot_order_and_uniqueness_refuse() -> None:
    result = specimen_result("object.invoke")
    updates = [dict(object_ref="object:2", snapshot=lower("snapshot")),
               dict(object_ref="object:1", snapshot=lower("snapshot"))]
    result["outcome"]["value"]["snapshots"] = updates
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))
    updates[1]["object_ref"] = "object:2"
    with pytest.raises(facade.WireError):
        facade.encode_result(seal_result(result))


def test_owned_argument_bytes_and_declared_sequence_are_preserved() -> None:
    req = specimen_request("object.invoke")
    data: dict[str, Any] = dict(contract="aware.ontology.facade-arguments.v1", action_ref="action:1",
        binding_digest=DIGEST, arguments=[
            dict(parameter_ref="parameter:z", value=dict(tag="runtime_value",
                runtime_value=dict(value_kind="string", value="e\u0301"))),
            dict(parameter_ref="parameter:a", value=dict(tag="object_target", object_target=dict(
                tag="instance_ref", type_ref="type:1", provider_key="provider:specimen",
                provider_generation="generation:1", instance_ref="instance:2"))),
        ])
    req["payload"]["arguments"] = B(data["contract"], data)
    req["intent_digest"] = facade.request_intent_digest(req)
    decoded = facade.decode_request(facade.encode_request(req))
    assert decoded["payload"]["arguments"] == req["payload"]["arguments"]
    body = decoded["payload"]["arguments"]
    assert isinstance(body, dict) and isinstance(body["body_hex"], str)
    assert json.loads(bytes.fromhex(body["body_hex"])) == data
    wrong = copy.deepcopy(req)
    data["action_ref"] = "action:other"
    wrong["payload"]["arguments"] = B(data["contract"], data)
    wrong["intent_digest"] = facade.request_intent_digest(wrong)
    with pytest.raises(facade.WireError):
        facade.encode_request(wrong)


def test_runtime_return_wrapper_preserves_owned_value_data() -> None:
    result = specimen_result("object.invoke")
    result["outcome"]["value"]["return_value"] = dict(tag="runtime_value",
        value=dict(value_kind="string", value="immutable specimen"))
    result = seal_result(result)
    assert facade.decode_result(facade.encode_result(result)) == result



def test_gow_preserves_historical_v1_pin_canonical_engine_and_default_policy() -> None:
    import ast
    import hashlib
    import inspect
    from pathlib import Path

    from aware_ontology_object_facade_client import codec as owner
    raw = Path(owner.__file__).read_bytes()
    parent = subprocess.run(["git", "cat-file", "blob", "4ab4c78120517c060ccd8b071b9d8b9c422de8fc"],
                            check=True, capture_output=True).stdout
    # Keep the accepted historical pin exact; the reviewed v4 successor shares
    # its canonical engine rather than requiring identical complete source.
    assert hashlib.sha256(parent).hexdigest() == "40454dafdd532833d72a6a5e7a18231765f90bc71ffd08b00b648e115f2722f2"
    def canonical_definitions(source):
        text = source.decode()
        return {node.name: ast.get_source_segment(text, node) for node in ast.parse(text).body
                if isinstance(node, ast.FunctionDef) and node.name in ("_tree", "_body", "make_body")}
    assert canonical_definitions(raw) == canonical_definitions(parent)
    assert owner._V1_POLICY == (65536, 16384, 4096, 32, None)
    for name in ("canonical_bytes", "decode_canonical", "encode_request", "decode_request", "encode_result", "decode_result", "encode_rejection", "decode_rejection"):
        assert len(inspect.signature(getattr(owner, name)).parameters) == 1


# Accepted docs-only successor corpus is independently frozen input, not runtime authority.
def _operation_successor_vectors():
    root = Path(__file__).resolve().parents[8]
    return json.loads((root / "docs/reports/ontology-facade-operation-wire-successor-vectors-20261004.json").read_text())


@pytest.mark.parametrize("row", _operation_successor_vectors()["owner_record_vectors"])
def test_operation_v4_owner_record_canonical_vectors_are_detached_framing_only(row):
    raw = bytes.fromhex(row["canonical_hex"])
    assert len(raw) == row["size_bytes"]
    assert facade.canonical_bytes(facade.decode_canonical(raw)) == raw
    assert H(raw) == row["body_hash"]


def test_operation_v4_oversized_head_is_not_positive_capacity_qualification():
    row = _operation_successor_vectors()["capacity_refusal_vectors"][0]
    raw = bytes.fromhex(row["canonical_hex"])
    assert len(raw) == row["size_bytes"] == 76_821
    assert H(raw) == row["body_hash"]
    assert len(raw) > wire.MAX_MESSAGE_BYTES == row["ceiling_bytes"]
    # This codec refuses framing. Original Service contact/activation and its
    # capacity_unavailable Result require their separately qualified owner.
    with pytest.raises(facade.WireError) as error:
        facade.decode_canonical(raw)
    assert error.value.code == "limit_exceeded"


@pytest.mark.parametrize("section,index", [("requests", i) for i in range(12)] +
                         [("supported_results", i) for i in range(58)] +
                         [("conditional_results", i) for i in range(6)])
def test_operation_v4_accepted_complete_frame_vectors(section, index):
    row = _operation_successor_vectors()[section][index]
    raw = bytes.fromhex(row["canonical_hex"])
    if section == "requests":
        value = facade.decode_request(raw)
        assert facade.encode_request(value) == raw
        assert value["intent_digest"] == facade.request_intent_digest(value)
    else:
        value = facade.decode_result(raw)
        assert facade.encode_result(value) == raw
        assert value["result_digest"] == facade.result_digest(value)
        observation = next(x for x in value["witnesses"] if x["role"] == "command_outcome")
        assert observation["body"] is not None
        observed = json.loads(bytes.fromhex(observation["body"]["body_hex"]))
        assert observed["outcome_hash"] == facade.outcome_hash(value)


@pytest.mark.parametrize("row", _operation_successor_vectors()["forbidden_outcomes"])
def test_operation_v4_forbidden_outcome_pairs_are_rejected(row):
    # Identical matrix governs both historical and successor framing.
    with pytest.raises(facade.WireError):
        facade.required_witness_roles(row["kind"], row["label"])


@pytest.mark.parametrize("section,index", [("requests", i) for i in range(12)] +
                         [("supported_results", i) for i in range(58)])
def test_operation_v4_outer_tag_substitution_rejects(section, index):
    row = _operation_successor_vectors()[section][index]
    value = json.loads(bytes.fromhex(row["canonical_hex"]))
    value["contract"] = "aware.ontology.facade-request.v999" if section == "requests" else "aware.ontology.facade-result.v999"
    with pytest.raises(facade.WireError):
        (facade.encode_request if section == "requests" else facade.encode_result)(value)



@pytest.mark.parametrize("row", _operation_successor_vectors()["supported_results"])
def test_operation_v4_every_tag_rejects_rebuilt_wrong_observation_preimage(row):
    value = json.loads(bytes.fromhex(row["canonical_hex"]))
    witness = next(x for x in value["witnesses"] if x["role"] == "command_outcome")
    observed = json.loads(bytes.fromhex(witness["body"]["body_hex"]))
    observed["outcome_hash"] = "sha256:" + "0" * 64
    observed["observation_digest"] = D(observed["contract"], {k:v for k,v in observed.items() if k != "observation_digest"})
    witness["body"] = B(observed["contract"], observed)
    value["result_digest"] = D(value["contract"], {k:v for k,v in value.items() if k != "result_digest"})
    # Complete enclosing digests were rebuilt; only the observation preimage is wrong.
    with pytest.raises(facade.WireError):
        facade.encode_result(value)
