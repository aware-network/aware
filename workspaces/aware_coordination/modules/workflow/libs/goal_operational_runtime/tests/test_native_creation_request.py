"""Authored requests, never issued authority, accepted Gates or created Goals."""

import copy
import json

import pytest

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.native_creation_request import (
    NativeGoalCreationRequestError, decode_native_goal_creation_request,
    encode_native_goal_creation_request, make_native_goal_creation_request,
)
from aware_goal_operational_runtime.phase_contracts import GoalLanePhaseGate, GoalPhaseCoordinate
from aware_goal_operational_runtime.phase_document import (
    GoalLanePhaseDefinitionV1, _definition_wire,  # pyright: ignore[reportPrivateUsage]
)

GOAL = "goal/2026-10-04/customer-goal"


def definition(key="first", ordinal=1, lane="runtime", goal=GOAL):
    return _definition_wire(GoalLanePhaseDefinitionV1(
        coordinate=GoalPhaseCoordinate(goal_tag=goal, lane_key=lane, phase_key=key),
        ordinal=ordinal, title="Authored phase " + key, intent="An explicit authored direction.",
        gate=GoalLanePhaseGate(gate_key="review", promise="Retain the reviewed proof.",
                              gate_contract_ref="contract:review-v1", evidence_schema_ref="evidence:review-v1"),
    ))


def inputs():
    return dict(idempotency_key="customer-create-1", goal_tag=GOAL, title="Customer Goal",
                intent="Create an honestly Proposed Goal.", owner_ref="object:owner:1",
                definition_of_done_ref=None, priority="medium", locks_ref=None,
                lanes=[dict(lane_key="runtime", title="Runtime", role="implementation", owner_ref="object:owner:1")],
                definitions=[definition()], dependencies=[], unresolved_dependencies=[])


def dependency(key="second-requires-first", *, external=False):
    return dict(owner_goal_tag=GOAL, dependency_key=key,
                dependent=definition("second", 2)["coordinate"],
                prerequisite=definition(goal="goal/2026-10-04/external" if external else GOAL)["coordinate"],
                relation="requires_acceptance", required_gate_digest=definition()["gate"]["gate_digest"],
                reason="Authored prerequisite, not an evaluation.", evidence_refs=[])


def graph():
    value=inputs()
    value["definitions"].append(definition("second", 2))
    value["dependencies"]=[dependency()]
    return value


def redigest(body):
    body=copy.deepcopy(body)
    body["request_ref"]="goal-native-creation-request:" + fingerprint({k:v for k,v in body.items() if k!="request_ref"})
    return json.dumps(body)


def changed(path, value):
    body=make_native_goal_creation_request(graph()).to_wire()
    nested=body
    for key in path[:-1]: nested=nested[key]
    nested[path[-1]]=value
    return redigest(body)


@pytest.mark.parametrize("value", [inputs(), graph()])
def test_round_trip_retains_authored_graph_without_operational_authority(value):
    request=make_native_goal_creation_request(value)
    decoded=decode_native_goal_creation_request(encode_native_goal_creation_request(request))
    assert decoded.to_wire()==request.to_wire()
    assert decoded.to_wire()["definitions"]==value["definitions"]
    for field in ("status", "document_ref", "outcome", "verifier_token", "publish", "operational_bundle"):
        assert not hasattr(decoded,field)
        assert field not in decoded.to_wire()
    value["definitions"].clear()
    assert request.to_wire()["definitions"]


@pytest.mark.parametrize("field", ["idempotency_key", "goal_tag", "title", "intent", "owner_ref", "priority"])
@pytest.mark.parametrize("invalid", [True, 17, None, [], {}, "", " padded ", "bad\x00text"])
def test_text_is_exact_not_coerced(field,invalid):
    with pytest.raises(NativeGoalCreationRequestError):
        decode_native_goal_creation_request(changed([field],invalid))


@pytest.mark.parametrize("field", ["definition_of_done_ref","locks_ref"])
@pytest.mark.parametrize("value", [None, "object:metadata:1"])
def test_metadata_uses_existing_optional_reference_contract(field,value):
    data=inputs()
    data[field]=value
    assert make_native_goal_creation_request(data).to_wire()[field]==value


@pytest.mark.parametrize("field", ["definition_of_done_ref","locks_ref"])
@pytest.mark.parametrize("value", [True, 2, {"body":"text"}, ["ref"], "with space"])
def test_inline_metadata_bodies_and_nonreferences_refuse(field,value):
    with pytest.raises(NativeGoalCreationRequestError):
        decode_native_goal_creation_request(changed([field],value))


@pytest.mark.parametrize("path,value", [
    (["schema_id"], "foreign"), (["definitions"], []), (["lanes"], []),
    (["definitions"], "not-array"), (["dependencies"], {}),
    (["lanes",0,"owner_ref"], "object:foreign"), (["lanes",0,"current_issue_ref"], "issue:1"),
    (["definitions",0,"title"], None), (["definitions",0,"intent"], None),
    (["definitions",0,"ordinal"], True), (["definitions",0,"ordinal"], 1.0),
    (["definitions",0,"coordinate","goal_tag"], "goal/2026-10-04/foreign"),
    (["definitions",0,"gate","unknown"], True),
    (["definitions",0,"gate","promise"], "bad\x00promise"),
    (["definitions",0,"intent"], "\ud800"),
    (["definitions",0,"gate","promise"], " Changed promise. "),
    (["dependencies",0,"required_gate_digest"], "sha256:"+"0"*64),
    (["dependencies",0,"relation"], "satisfied"),
    (["dependencies",0,"dependent","phase_key"], "missing"),
    (["dependencies",0,"prerequisite","phase_key"], "missing"),
    (["operational_bundle"], {}), (["phase_operation_journal"], []), (["status"], "active"),
])
def test_redigested_malformed_graph_and_operational_claims_refuse(path,value):
    with pytest.raises(NativeGoalCreationRequestError):
        decode_native_goal_creation_request(changed(path,value))


def test_duplicates_lane_partition_order_and_cycles_refuse():
    for field in ("lanes","definitions","dependencies"):
        data=graph()
        data[field].append(copy.deepcopy(data[field][0]))
        with pytest.raises(NativeGoalCreationRequestError): make_native_goal_creation_request(data)
    data=graph()
    data["definitions"].reverse()
    with pytest.raises(NativeGoalCreationRequestError): make_native_goal_creation_request(data)
    data=graph()
    data["lanes"][0]["lane_key"]="foreign"
    with pytest.raises(NativeGoalCreationRequestError): make_native_goal_creation_request(data)
    data=graph()
    edge=dependency("first-requires-second")
    edge["dependent"],edge["prerequisite"]=edge["prerequisite"],edge["dependent"]
    data["dependencies"].insert(0,edge)
    with pytest.raises(NativeGoalCreationRequestError): make_native_goal_creation_request(data)


def test_zero_ordinal_refuses_creation_without_changing_definition_codec():
    zero_definition = definition(ordinal=0)
    assert zero_definition["ordinal"] == 0  # Still permitted by the shared legacy codec.
    data = inputs()
    data["definitions"] = [zero_definition]
    with pytest.raises(NativeGoalCreationRequestError, match="creation_request_definition_ordinal"):
        make_native_goal_creation_request(data)
    body = make_native_goal_creation_request(inputs()).to_wire()
    body["definitions"] = [zero_definition]  # Exact nested ref, not merely a stale ref substitution.
    with pytest.raises(NativeGoalCreationRequestError, match="creation_request_definition_ordinal"):
        decode_native_goal_creation_request(redigest(body))


def test_cross_goal_and_unresolved_declarations_do_not_create_observations():
    data=graph()
    data["dependencies"]=[dependency(external=True)]
    request=make_native_goal_creation_request(data)
    assert request.to_wire()["dependencies"]==data["dependencies"]
    unresolved=dependency("unresolved",external=True)
    unresolved.pop("required_gate_digest")
    unresolved.update(resolution_state="required_gate_digest_unresolved",eligibility_effect="none")
    data["unresolved_dependencies"]=[unresolved]
    request=make_native_goal_creation_request(data)
    assert request.to_wire()["unresolved_dependencies"]==[unresolved]
    unresolved["eligibility_effect"]="satisfied"
    with pytest.raises(NativeGoalCreationRequestError): make_native_goal_creation_request(data)


def test_unresolved_key_overlap_duplicate_and_local_resolved_target_refuse():
    for case in ("overlap", "duplicate", "local"):
        data=graph()
        edge=dependency("second-requires-first" if case=="overlap" else "unresolved",external=case!="local")
        edge.pop("required_gate_digest")
        edge.update(resolution_state="required_gate_digest_unresolved",eligibility_effect="none")
        data["unresolved_dependencies"]=[edge,copy.deepcopy(edge)] if case=="duplicate" else [edge]
        with pytest.raises(NativeGoalCreationRequestError): make_native_goal_creation_request(data)


def test_consume_revalidates_mutation_and_does_not_repair_identity():
    request=make_native_goal_creation_request(inputs())
    body=request.to_wire()
    body["request_ref"]="foreign"
    object.__setattr__(request,"canonical_body",json.dumps(body))
    with pytest.raises(NativeGoalCreationRequestError): encode_native_goal_creation_request(request)
    assert "foreign" in request.canonical_body


@pytest.mark.parametrize("payload", ['null','[]','{','{"schema_id":"x","schema_id":"x"}'])
def test_invalid_payloads_and_duplicate_keys_refuse(payload):
    with pytest.raises(NativeGoalCreationRequestError): decode_native_goal_creation_request(payload)
