"""Exact acyclic planning claims do not authenticate creation permission."""

import copy
import json

import pytest
import test_planning_intent_document as fixtures
from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.phase_document import (
    extract_goal_phase_native_carrier,
)
from aware_goal_operational_runtime.planning_initial_plan import (
    ORIGIN_DOMAIN,
    PLAN_DOMAIN,
    GoalPlanningInitialPlanV1,
    decode_goal_planning_initial_plan,
    decode_goal_planning_origin_intent,
    encode_goal_planning_initial_plan,
    make_goal_planning_initial_plan,
)
from aware_goal_operational_runtime.planning_intent_document import (
    extract_goal_planning_markdown,
)

SOURCE = "workspace-initial-goal-source-context:sha256:" + "c" * 64
PERMISSION = "workspace-initial-goal-intent-permission:sha256:" + "d" * 64


def plan(**overrides):
    return make_goal_planning_initial_plan(
        fixtures.request(**overrides),
        creator_binding=fixtures.creator(),
        source_context_ref=SOURCE,
        intent_permission_ref=PERMISSION,
    )


def redigest(body):
    result = copy.deepcopy(body)
    result["plan_ref"] = (
        PLAN_DOMAIN
        + ":"
        + fingerprint({k: v for k, v in result.items() if k != "plan_ref"})
    )
    return json.dumps(result).encode()


def test_deterministic_complete_plan_and_acyclic_origin_reuse_original_carrier():
    value = plan()
    assert type(value) is GoalPlanningInitialPlanV1
    wire = value.to_wire()
    assert plan() == value
    assert (
        decode_goal_planning_initial_plan(encode_goal_planning_initial_plan(value))
        == value
    )
    assert json.loads(value.canonical_body) == wire
    origin = decode_goal_planning_origin_intent(
        json.dumps(wire["origin_intent"]).encode()
    )
    assert origin.to_wire() == wire["origin_intent"]
    assert origin.origin_intent_ref == wire["document"]["origin_intent_ref"]
    assert origin.to_wire()["request_ref"] == fixtures.request().request_ref
    assert origin.to_wire()["source_context_ref"] == SOURCE
    assert origin.to_wire()["intent_permission_ref"] == PERMISSION
    assert wire["publication_admission"] == "not_issued"
    assert extract_goal_planning_markdown(value.carrier_bytes) == value.document
    assert value.document.planning_status == "not_yet_decomposed"
    assert value.document.to_wire()["lifecycle_status"] == "proposed"
    assert value.plan_ref == wire["plan_ref"]
    assert not (
        {
            "carrier_sha256",
            "plan_ref",
            "document_ref",
            "commit",
            "blob_oid",
            "verified",
            "currentness",
            "publication_receipt",
        }
        & origin.to_wire().keys()
    )
    with pytest.raises(ValueError):
        extract_goal_phase_native_carrier(value.carrier_bytes)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_id", "aware.goal.native-creation-plan.v1"),
        ("publication_admission", "issued"),
        ("publication_admission", True),
        ("carrier_utf8", "substituted"),
        ("carrier_utf8", True),
        ("carrier_sha256", "sha256:" + "0" * 64),
        ("carrier_sha256", None),
        ("plan_ref", PLAN_DOMAIN + ":sha256:" + "a" * 64),
    ],
)
def test_outer_redigestion_cannot_legitimize_derived_substitution(field, value):
    body = plan().to_wire()
    body[field] = value
    payload = json.dumps(body).encode() if field == "plan_ref" else redigest(body)
    with pytest.raises(ValueError):
        decode_goal_planning_initial_plan(payload)


@pytest.mark.parametrize("scope", ["plan", "origin", "request", "creator", "document"])
def test_unknown_fields_refuse_at_every_nested_level(scope):
    body = plan().to_wire()
    target = {
        "plan": body,
        "origin": body["origin_intent"],
        "request": body["request"],
        "creator": body["origin_intent"]["creator_binding"],
        "document": body["document"],
    }[scope]
    target["verified"] = True
    with pytest.raises(ValueError):
        decode_goal_planning_initial_plan(redigest(body))


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_context_ref", True),
        ("source_context_ref", "sha256:" + "c" * 64),
        (
            "intent_permission_ref",
            "workspace-initial-goal-intent-permission:sha256:" + "F" * 64,
        ),
        (
            "intent_permission_ref",
            "workspace-initial-goal-source-context:sha256:" + "d" * 64,
        ),
        ("request_ref", "goal-planning-creation-request:sha256:" + "e" * 64),
        ("origin_profile", "goal-native-genesis-repository-issue-v1"),
        ("schema_id", "aware.goal.native-creation-intent.v1"),
    ],
)
def test_wrong_origin_binding_refuses_even_with_recomputed_origin_and_plan_digests(
    field, value
):
    body = plan().to_wire()
    body["origin_intent"][field] = value
    body["origin_intent"]["origin_intent_ref"] = (
        ORIGIN_DOMAIN
        + ":"
        + fingerprint(
            {k: v for k, v in body["origin_intent"].items() if k != "origin_intent_ref"}
        )
    )
    with pytest.raises(ValueError):
        decode_goal_planning_initial_plan(redigest(body))


@pytest.mark.parametrize(
    "field,value",
    [
        ("lifecycle_status", "accepted"),
        ("lanes", [{"lane_key": "placeholder"}]),
        ("owner_ref", "codex-foreign"),
        ("origin_intent_ref", ORIGIN_DOMAIN + ":sha256:" + "e" * 64),
    ],
)
def test_document_substitution_cannot_become_canonical_initial_state(field, value):
    body = plan().to_wire()
    body["document"][field] = value
    body["document"]["document_ref"] = "goal-intent-document:" + fingerprint(
        {k: v for k, v in body["document"].items() if k != "document_ref"}
    )
    with pytest.raises(ValueError):
        decode_goal_planning_initial_plan(redigest(body))


@pytest.mark.parametrize(
    "field", ["plan_ref", "carrier_sha256", "document_ref", "commit", "blob_oid"]
)
def test_origin_cannot_bind_its_future_enclosing_effect(field):
    body = plan().to_wire()["origin_intent"]
    body[field] = "future"
    body["origin_intent_ref"] = (
        ORIGIN_DOMAIN
        + ":"
        + fingerprint({k: v for k, v in body.items() if k != "origin_intent_ref"})
    )
    with pytest.raises(ValueError):
        decode_goal_planning_origin_intent(json.dumps(body).encode())


@pytest.mark.parametrize(
    "payload", [b"[]", b"{}", b'{"schema_id":1,"schema_id":2}', b"\xff", "{}", True]
)
def test_malformed_or_nonbytes_wire_refuses(payload):
    for decoder in (
        decode_goal_planning_initial_plan,
        decode_goal_planning_origin_intent,
    ):
        with pytest.raises(ValueError):
            decoder(payload)


def test_marker_bearing_unicode_authored_intent_round_trips_exactly():
    marker = "VAMOS · intención\n<!-- aware.goal.intent.document.v1:end -->\n```"
    value = plan(title=marker, intent=marker + "\nA meaningful intended outcome")
    assert extract_goal_planning_markdown(value.carrier_bytes) == value.document
    assert value.document.to_wire()["title"] == marker
    assert (
        decode_goal_planning_initial_plan(encode_goal_planning_initial_plan(value))
        == value
    )


def test_postconstruction_mutation_is_not_repaired_on_consumption():
    value = plan()
    broken = value.to_wire()
    broken["carrier_utf8"] = "forged"
    changed = redigest(broken).decode()
    object.__setattr__(value, "canonical_body", changed)
    for _ in range(2):
        with pytest.raises(ValueError):
            encode_goal_planning_initial_plan(value)
    assert value.canonical_body == changed


def test_complete_coherent_caller_claims_are_data_not_qualified_permission():
    # No live source or permission is supplied here. The pure codec is allowed
    # to describe coherent claims; a provider must authenticate them separately.
    value = plan()
    other = make_goal_planning_initial_plan(
        fixtures.request(title="another coherent claim"),
        creator_binding=fixtures.creator(),
        source_context_ref=SOURCE,
        intent_permission_ref=PERMISSION,
    )
    assert other != value
    assert (
        decode_goal_planning_initial_plan(encode_goal_planning_initial_plan(other))
        == other
    )
    assert other.to_wire()["publication_admission"] == "not_issued"
    assert not hasattr(other, "require_current")
    assert not hasattr(other, "publish")
