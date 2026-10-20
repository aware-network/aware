"""Planning is authored intention, never an empty-set eligibility shortcut."""

import copy
import json

import pytest
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.native_creation_request import (
    decode_native_goal_creation_request,
    make_native_goal_creation_request,
)
from aware_goal_operational_runtime.planning_creation_request import (
    GRAPH_FIELDS,
    REQUEST_DOMAIN,
    decode_planning_goal_creation_request,
    encode_planning_goal_creation_request,
    make_planning_goal_creation_request,
)


def inputs():
    return {
        "idempotency_key": "first-goal",
        "goal_tag": "goal/2026-10-17/customer-intent",
        "title": "Our first Goal",
        "intent": "Make useful progress without inventing a Phase.",
        "owner_ref": "codex-customer-example",
        "definition_of_done_ref": None,
        "priority": "medium",
        "locks_ref": None,
        "lanes": [],
        "definitions": [],
        "dependencies": [],
        "unresolved_dependencies": [],
    }


def redigest(body):
    body = copy.deepcopy(body)
    body["request_ref"] = (
        REQUEST_DOMAIN
        + ":"
        + fingerprint(
            {key: value for key, value in body.items() if key != "request_ref"}
        )
    )
    return json.dumps(body)


def test_actual_minimal_planning_request_round_trip_is_detached_and_non_authorizing():
    authored = inputs()
    request = make_planning_goal_creation_request(authored)
    payload = encode_planning_goal_creation_request(request)
    assert decode_planning_goal_creation_request(payload) == request
    assert request.request_ref.startswith("goal-planning-creation-request:sha256:")
    assert set(request.to_wire()) == set(authored) | {"schema_id", "request_ref"}
    authored["lanes"].append({"invented": "lane"})
    detached = request.to_wire()
    detached["definitions"].append({"invented": "phase"})
    assert all(request.to_wire()[key] == [] for key in GRAPH_FIELDS)
    for field in (
        "admission",
        "verified",
        "publish",
        "eligibility",
        "operational_bundle",
    ):
        assert not hasattr(request, field)


@pytest.mark.parametrize(
    "field", ["idempotency_key", "goal_tag", "owner_ref", "priority", "title", "intent"]
)
@pytest.mark.parametrize(
    "invalid", [None, True, 3, [], {}, "", " padded ", "bad\x00text", "\ud800"]
)
def test_existing_metadata_types_and_strings_remain_strict(field, invalid):
    body = make_planning_goal_creation_request(inputs()).to_wire()
    body[field] = invalid
    with pytest.raises(ValueError):
        decode_planning_goal_creation_request(redigest(body))


@pytest.mark.parametrize("field", ["definition_of_done_ref", "locks_ref"])
@pytest.mark.parametrize("value", [None, "object:authored-reference"])
def test_optional_reference_contract_is_preserved(field, value):
    fields = inputs()
    fields[field] = value
    assert make_planning_goal_creation_request(fields).to_wire()[field] == value


@pytest.mark.parametrize("field", ["definition_of_done_ref", "locks_ref"])
@pytest.mark.parametrize("value", [True, 1, {}, [], "inline body"])
def test_inline_metadata_and_coercions_refuse(field, value):
    body = make_planning_goal_creation_request(inputs()).to_wire()
    body[field] = value
    with pytest.raises(ValueError):
        decode_planning_goal_creation_request(redigest(body))


@pytest.mark.parametrize("field", sorted(GRAPH_FIELDS))
@pytest.mark.parametrize("value", [[{"placeholder": "entity"}], None, {}, (), True])
def test_planning_arrays_cannot_supply_graph_or_evidence(field, value):
    fields = inputs()
    fields[field] = value
    with pytest.raises(ValueError):
        make_planning_goal_creation_request(fields)


@pytest.mark.parametrize(
    "field",
    [
        "operational_bundle",
        "execution_authority",
        "status",
        "creator_binding",
        "phase_operation_journal",
        "gate_observations",
        "work",
        "acceptance",
        "verified",
    ],
)
def test_even_redigested_extra_authority_fields_refuse(field):
    body = make_planning_goal_creation_request(inputs()).to_wire()
    body[field] = {}
    with pytest.raises(ValueError):
        decode_planning_goal_creation_request(redigest(body))


def test_v1_and_planning_v2_are_not_interchangeable_or_automatically_migrated():
    request = make_planning_goal_creation_request(inputs())
    with pytest.raises(ValueError):
        make_native_goal_creation_request(inputs())
    with pytest.raises(ValueError):
        decode_native_goal_creation_request(
            encode_planning_goal_creation_request(request)
        )
    body = request.to_wire()
    body["schema_id"] = "aware.goal.native-creation-request.v1"
    with pytest.raises(ValueError):
        decode_planning_goal_creation_request(redigest(body))
    body = request.to_wire()
    body["request_ref"] = "goal-native-creation-request:" + fingerprint(
        {key: value for key, value in body.items() if key != "request_ref"}
    )
    with pytest.raises(ValueError):
        decode_planning_goal_creation_request(json.dumps(body))


def test_consumption_revalidates_without_repairing_mutated_request():
    request = make_planning_goal_creation_request(inputs())
    body = request.to_wire()
    body["request_ref"] = "foreign"
    altered = json.dumps(body)
    object.__setattr__(request, "canonical_body", altered)
    for _ in range(2):
        with pytest.raises(ValueError):
            encode_planning_goal_creation_request(request)
    assert request.canonical_body == altered


@pytest.mark.parametrize("payload", ["null", "[]", "{", '{"x":1,"x":2}', True, b"{}"])
def test_bad_payload_and_duplicate_fields_refuse(payload):
    with pytest.raises(ValueError):
        decode_planning_goal_creation_request(payload)
