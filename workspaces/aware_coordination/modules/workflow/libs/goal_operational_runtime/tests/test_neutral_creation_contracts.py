"""Detached structural claims; no fixture provider is an admitted issuer."""

import copy
import hashlib
import json
import subprocess
import sys
import types

import pytest

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.native_creation_plan import make_native_goal_creation_plan_claim, encode_native_goal_creation_plan_claim
from aware_goal_operational_runtime.native_creation_request import make_native_goal_creation_request
from aware_goal_operational_runtime.neutral_creation_contracts import (
    AUTHORITY_SCHEMA, STATE_SCHEMA, INTENT_SCHEMA, DECISION_SCHEMA,
    NeutralCreationContractError, NeutralGoalCreationClaim,
    decode_neutral_goal_creation_claim, encode_neutral_goal_creation_claim,
    make_goal_creation_authority_input_claim, make_goal_creation_semantic_state,
    make_goal_creation_intent_claim, make_goal_creation_decision_claim,
)
from test_native_creation_plan import fixture as git_fixture


def authority(request=None, provider="git-fixture"):
    request = request or git_fixture()[0]
    owner = request.to_wire()["owner_ref"]
    return make_goal_creation_authority_input_claim(dict(
        request_ref=request.request_ref, provider_ref="object:" + provider,
        provider_generation_ref="object:" + provider + ":generation:1",
        authority_profile_ref="object:unadmitted-profile:" + provider,
        namespace_ref="object:namespace:1", namespace_revision_ref="object:revision:1",
        target_locator_ref="object:target:1", creator_ref=owner, initial_owner_ref=owner,
        source_binding_ref="object:unverified-source:" + provider,
        permission_ref="object:unverified-permission:" + provider,
        identity_absence_ref="object:unverified-absence:" + provider,
        publication_concurrency_ref="object:unverified-concurrency:" + provider,
        verified_at="2026-10-05T01:00:00Z",
    ))


def decision(provider="git-fixture"):
    request = git_fixture()[0]
    return make_goal_creation_decision_claim(request, authority(request, provider))


def redigest(body):
    body = copy.deepcopy(body)
    field, domain = {
        AUTHORITY_SCHEMA: ("authority_input_ref", "goal-creation-authority-input:"),
        STATE_SCHEMA: ("semantic_state_ref", "goal-creation-semantic-state:"),
        INTENT_SCHEMA: ("intent_ref", "goal-native-creation-intent:"),
        DECISION_SCHEMA: ("decision_ref", "goal-creation-decision:"),
    }[body["schema_id"]]
    body[field] = domain + fingerprint({k:v for k,v in body.items() if k != field})
    return json.dumps(body)


@pytest.mark.parametrize("schema", [AUTHORITY_SCHEMA, STATE_SCHEMA, INTENT_SCHEMA, DECISION_SCHEMA])
def test_round_trip_is_detached_non_authorizing_data(schema):
    all_values = decision().to_wire()
    body = {AUTHORITY_SCHEMA:all_values["authority_input"], STATE_SCHEMA:all_values["semantic_state"],
            INTENT_SCHEMA:all_values["intent"], DECISION_SCHEMA:all_values}[schema]
    value = decode_neutral_goal_creation_claim(json.dumps(body), expected_schema=schema)
    assert decode_neutral_goal_creation_claim(encode_neutral_goal_creation_claim(value)) == value
    detached = value.to_wire()
    detached["schema_id"] = "foreign"
    assert value.to_wire()["schema_id"] == schema
    for attr in ("require_verified", "verifier_token", "publish", "live_handle", "dispatch", "eligible"):
        assert not hasattr(value, attr)


def test_same_semantic_state_distinct_fixture_provenance_and_genesis():
    git = decision("git-fixture").to_wire()
    obj = decision("object-fixture").to_wire()
    assert git["semantic_state"] == obj["semantic_state"]
    for field in ("authority_input", "intent", "genesis", "decision_ref"):
        assert git[field] != obj[field]
    assert "execution_authority" not in git["semantic_state"]
    assert "provider_ref" not in git["semantic_state"]
    assert git["genesis"]["creation_intent_ref"] == git["intent"]["intent_ref"]


def test_existing_initial_plan_bytes_match_pinned_prechange_reader():
    # Load the exact committed source pin into memory only. No checkout writes.
    source = subprocess.run(["git", "cat-file", "blob", "3b428be46a1c261ab3315fbb68d0e1e4d7c0ba4e"],
                            check=True, capture_output=True).stdout
    assert hashlib.sha256(source).hexdigest() == "ec3325012119b4a48512bdc3b627080388cf3ece70324b59008b45412c7668ef"
    name = "aware_goal_operational_runtime._prechange_creation_plan_test"
    module = types.ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(source, "<pinned-prechange-plan>", "exec"), module.__dict__)
        original = module.encode_native_goal_creation_plan_claim(module.make_native_goal_creation_plan_claim(*git_fixture()))
        current = encode_native_goal_creation_plan_claim(make_native_goal_creation_plan_claim(*git_fixture()))
        assert original == current
        old_state = json.loads(original)["initial_state"]
        state = decision().to_wire()["semantic_state"]
        assert {k:v for k,v in old_state.items() if k not in {"schema_id", "execution_authority"}} == {
            k:v for k,v in state.items() if k not in {"schema_id", "semantic_state_ref"}
        }
    finally:
        del sys.modules[name]


@pytest.mark.parametrize("field", [
    "provider_ref", "provider_generation_ref", "authority_profile_ref", "namespace_ref",
    "namespace_revision_ref", "target_locator_ref", "creator_ref", "initial_owner_ref",
    "source_binding_ref", "permission_ref", "identity_absence_ref", "publication_concurrency_ref", "verified_at",
])
@pytest.mark.parametrize("bad", [True, 2, None, [], {}, "", " spaced ", "\ud800"])
def test_authority_input_requires_exact_text(field, bad):
    body = authority().to_wire()
    body[field] = bad
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(redigest(body))


@pytest.mark.parametrize("field,bad", [
    ("creator_ref", "object:foreign"), ("request_ref", "request:fake"),
    ("verified_at", "2026-02-30T01:00:00Z"), ("verified_at", "2026-10-05T01:00:00+00:00"),
    ("caller_current", True), ("verifier_token", "token"),
])
def test_authority_input_malformed_join_time_and_extra_fields_refuse(field,bad):
    body = authority().to_wire()
    body[field] = bad
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(redigest(body))


@pytest.mark.parametrize("path,bad", [
    (["status"], "active"), (["hold"], "held"), (["source_refs"], ["object:prior"]),
    (["execution_authority"], {}), (["phase_operation_journal"], {}),
    (["operational_bundle", "phases"], [dict(state="accepted")]),
    (["operational_bundle", "schema_id"], "foreign"),
    (["operational_bundle", "observations"], []), (["lanes",0,"operational_state"], "active"),
    (["lanes",0,"current_issue_ref"], "issue:1"), (["lanes",0,"blocker_ref"], "blocker:1"),
    (["lanes",0,"current_work_association_ref"], "work:1"),
    (["lanes",0,"hold_authority_refs"], ["hold:1"]),
    (["definitions",0,"ordinal"], True), (["definitions",0,"ordinal"], 0),
    (["definitions",0,"gate","satisfied"], True), (["definitions",0,"title"], None),
    (["unresolved_dependencies"], "absent"), (["lanes"], "ready"),
])
def test_semantic_state_operational_injection_refuses_even_redigested(path,bad):
    body = make_goal_creation_semantic_state(git_fixture()[0]).to_wire()
    target = body
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = bad
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(redigest(body))


@pytest.mark.parametrize("field", ["request_ref", "authority_input_ref", "semantic_state_ref"])
@pytest.mark.parametrize("bad", [True, 1, None, "object:untyped"])
def test_intent_reference_domains_are_closed(field,bad):
    body = decision().to_wire()["intent"]
    body[field] = bad
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(redigest(body))


@pytest.mark.parametrize("field", ["authority_input", "semantic_state", "intent", "genesis"])
def test_decision_canonical_foreign_nested_body_refuses(field):
    body = decision().to_wire()
    # Another internally valid request/decision, not a malformed nested digest.
    original = git_fixture()[0].to_wire()
    fields = {k:v for k,v in original.items() if k not in {"schema_id","request_ref"}}
    fields["title"] = "Foreign authored Goal"
    other_request = make_native_goal_creation_request(fields)
    other = make_goal_creation_decision_claim(other_request, authority(other_request)).to_wire()
    body[field] = other[field]
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(redigest(body))


def test_same_state_different_idempotency_still_binds_exact_request():
    request = git_fixture()[0]
    original = request.to_wire()
    fields = {k:v for k,v in original.items() if k not in {"schema_id","request_ref"}}
    fields["idempotency_key"] = "other-request"
    other = make_native_goal_creation_request(fields)
    assert make_goal_creation_semantic_state(request) == make_goal_creation_semantic_state(other)
    with pytest.raises(NeutralCreationContractError, match="request_authority_join"):
        make_goal_creation_decision_claim(other, authority(request))


def test_omitted_dependency_refuses_even_with_all_nested_identities_recomputed():
    body = decision().to_wire()
    body["semantic_state"]["operational_bundle"]["dependencies"] = []
    body["semantic_state"] = json.loads(redigest(body["semantic_state"]))
    # The changed state is structurally valid, but not this complete request.
    decode_neutral_goal_creation_claim(json.dumps(body["semantic_state"]), expected_schema=STATE_SCHEMA)
    body["intent"] = make_goal_creation_intent_claim(body["request"]["request_ref"],
        body["authority_input"]["authority_input_ref"], body["semantic_state"]["semantic_state_ref"]).to_wire()
    from aware_goal_operational_runtime.native_creation_execution_authority import GoalPhaseExecutionAuthorityV2
    body["genesis"] = GoalPhaseExecutionAuthorityV2(creation_intent_ref=body["intent"]["intent_ref"]).to_wire()
    with pytest.raises(NeutralCreationContractError, match="request_state_join"):
        decode_neutral_goal_creation_claim(redigest(body))


@pytest.mark.parametrize("schema", [AUTHORITY_SCHEMA, STATE_SCHEMA, INTENT_SCHEMA, DECISION_SCHEMA])
def test_actual_record_mutation_never_repairs(schema):
    body = decision().to_wire()
    body = {AUTHORITY_SCHEMA:body["authority_input"], STATE_SCHEMA:body["semantic_state"],
            INTENT_SCHEMA:body["intent"], DECISION_SCHEMA:body}[schema]
    value = decode_neutral_goal_creation_claim(json.dumps(body))
    ref_field = {AUTHORITY_SCHEMA:"authority_input_ref", STATE_SCHEMA:"semantic_state_ref",
                 INTENT_SCHEMA:"intent_ref", DECISION_SCHEMA:"decision_ref"}[schema]
    body[ref_field] = "bad"
    raw = json.dumps(body)
    object.__setattr__(value, "canonical_body", raw)
    with pytest.raises(NeutralCreationContractError):
        encode_neutral_goal_creation_claim(value)
    assert value.canonical_body == raw


def test_duplicates_wrong_profile_and_missing_fields_refuse():
    raw = encode_neutral_goal_creation_claim(decision())
    raw = raw.replace('"status":"proposed"', '"status":"proposed","status":"proposed"')
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(raw)
    with pytest.raises(NeutralCreationContractError):
        NeutralGoalCreationClaim(raw)
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(encode_neutral_goal_creation_claim(authority()), expected_schema=STATE_SCHEMA)
    body = decision().to_wire()
    del body["authority_input"]["permission_ref"]
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(redigest(body))


@pytest.mark.parametrize("payload", [None, True, 1, [], "null", "[]", "{}", "{bad json}"])
def test_invalid_payload_refuses(payload):
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(payload)


def test_intent_factory_matches_decision_and_old_profile_not_relabelled():
    body = decision().to_wire()
    intent = make_goal_creation_intent_claim(body["request"]["request_ref"],
        body["authority_input"]["authority_input_ref"], body["semantic_state"]["semantic_state_ref"])
    assert intent.to_wire() == body["intent"]
    old = make_native_goal_creation_plan_claim(*git_fixture()).to_wire()
    assert old["intent"]["schema_id"] != intent.to_wire()["schema_id"]
    assert old["intent"]["intent_ref"] != intent.reference
    with pytest.raises(NeutralCreationContractError):
        decode_neutral_goal_creation_claim(json.dumps(old))
