"""Codec proofs only: fixtures deliberately have no enrolled authority."""

import copy
import json

import pytest

from aware_goal_operational_runtime.identity import fingerprint
from aware_goal_operational_runtime.native_creation_claims import (
    ABSENCE_SCHEMA, CONTEXT_SCHEMA, EXCLUSION_SCHEMA, GRANT_SCHEMA, SOURCE_SCHEMA,
    GIT_PROFILE, make_native_creation_claim,
)
from aware_goal_operational_runtime.native_creation_plan import (
    NativeGoalCreationPlanClaimV1, NativeGoalCreationPlanError,
    decode_native_goal_creation_intent, decode_native_goal_creation_plan_claim,
    encode_native_goal_creation_intent, encode_native_goal_creation_plan_claim,
    make_native_goal_creation_intent, make_native_goal_creation_plan_claim,
)
from aware_goal_operational_runtime.native_creation_request import make_native_goal_creation_request
from aware_goal_operational_runtime.phase_contracts import GoalLanePhaseGate, GoalPhaseCoordinate
from aware_goal_operational_runtime.phase_document import (
    GoalLanePhaseDefinitionV1, _definition_wire,  # pyright: ignore[reportPrivateUsage]
)

GOAL = "goal/2026-10-04/customer-goal"
OWNER = "object:unverified-owner:1"


def fixture():
    gate = GoalLanePhaseGate(gate_key="review", promise="Publish independently reviewed proof.",
                            gate_contract_ref="contract:review-v1", evidence_schema_ref="evidence:review-v1")
    definitions = [_definition_wire(GoalLanePhaseDefinitionV1(
        coordinate=GoalPhaseCoordinate(goal_tag=GOAL, lane_key="runtime", phase_key=key),
        ordinal=i, title=key, intent="Explicit authored intent.", gate=gate,
    )) for i, key in enumerate(("first", "second"), start=1)]
    dependency = dict(owner_goal_tag=GOAL, dependency_key="second-requires-first",
                      dependent=definitions[1]["coordinate"], prerequisite=definitions[0]["coordinate"],
                      relation="requires_acceptance", required_gate_digest=gate.gate_digest,
                      reason="Authored, not evaluated.", evidence_refs=[])
    request = make_native_goal_creation_request(dict(
        idempotency_key="create-1", goal_tag=GOAL, title="Customer Goal", intent="Authored direction.",
        owner_ref=OWNER, definition_of_done_ref="object:done:1", priority="medium", locks_ref=None,
        lanes=[dict(lane_key="runtime", title="Runtime", role="implementation", owner_ref=OWNER)],
        definitions=definitions, dependencies=[dependency], unresolved_dependencies=[],
    ))
    common = dict(namespace_ref="object:namespace:1", namespace_revision_ref="object:revision:1",
                  target_locator_ref="object:target:1")
    grant = make_native_creation_claim(GRANT_SCHEMA, dict(
        common, creator_ref=OWNER, initial_owner_ref=OWNER, request_ref=request.request_ref,
        permission="create_proposed_goal", authority_profile=GIT_PROFILE,
        authority_source_ref="object:unverified-issue:1",
    ))
    source = make_native_creation_claim(SOURCE_SCHEMA, dict(
        common, provider_ref="object:provider:1", admission_profile="protocol-native-goal-fs-v1",
        admission_authority_ref="object:unverified-source:1",
    ))
    absence = make_native_creation_claim(ABSENCE_SCHEMA, dict(
        common, goal_tag=GOAL, target_disposition="absent", history_profile="goal-native-git-identity-census-v1",
        history_boundary_ref="object:unverified-history:1", history_inventory_ref="object:history:1",
        identity_inventory_ref="object:identity:1",
    ))
    guard = make_native_creation_claim(EXCLUSION_SCHEMA, dict(
        provider_ref="object:provider:1", namespace_ref=common["namespace_ref"],
        repository_binding_ref="object:repository:1", request_ref=request.request_ref, creator_ref=OWNER,
        enforcement_profile="goal-native-git-namespace-exclusion-v1", enforcement_authority_ref="object:unverified-enforcement:1",
        scope="complete_repository_ref_domain", fence_ref="object:unverified-fence:1",
        acquired_namespace_revision_ref=common["namespace_revision_ref"], acquired_at="2026-10-04T01:00:00Z",
    ))
    context = make_native_creation_claim(CONTEXT_SCHEMA, dict(
        common, provider_ref="object:provider:1", verifier_profile=GIT_PROFILE,
        request_ref=request.request_ref, creator_ref=OWNER, initial_owner_ref=OWNER,
        creation_grant_ref=grant.reference, source_admission_ref=source.reference,
        identity_absence_ref=absence.reference, namespace_exclusion_ref=guard.reference,
        verified_at="2026-10-04T01:00:01Z",
    ))
    return request, context, grant, source, absence, guard


def plan():
    return make_native_goal_creation_plan_claim(*fixture())


def redigest(body):
    body = copy.deepcopy(body)
    body["plan_ref"] = "goal-native-creation-plan:" + fingerprint({k:v for k,v in body.items() if k != "plan_ref"})
    return json.dumps(body)


def test_complete_round_trip_and_initial_state_are_non_authorizing():
    value = plan()
    restored = decode_native_goal_creation_plan_claim(encode_native_goal_creation_plan_claim(value))
    body = restored.to_wire()
    assert body == value.to_wire()
    state = body["initial_state"]
    assert state["status"] == "proposed" and state["hold"] == "clear"
    assert state["source_refs"] == [] and state["operational_bundle"]["phases"] == []
    assert state["definitions"] == body["request"]["definitions"]
    assert state["operational_bundle"]["dependencies"] == body["request"]["dependencies"]
    assert state["lanes"][0]["operational_state"] == "ready"
    assert state["lanes"][0]["current_issue_ref"] is None
    assert state["execution_authority"]["creation_intent_ref"] == body["intent"]["intent_ref"]
    for attr in ("require_verified", "verifier_token", "publish", "live_handle", "eligible"):
        assert not hasattr(restored, attr)
    body["initial_state"]["definitions"].clear()
    assert restored.to_wire()["initial_state"]["definitions"]


def test_intent_round_trip_and_schema_identity():
    body = plan().to_wire()
    value = make_native_goal_creation_intent(body["request"]["request_ref"], body["context"]["context_ref"])
    assert value.to_wire() == body["intent"]
    assert decode_native_goal_creation_intent(encode_native_goal_creation_intent(value)) == value
    invalid = dict(value.to_wire(), schema_id="foreign")
    invalid["intent_ref"] = "goal-native-creation-intent:" + fingerprint({k:v for k,v in invalid.items() if k != "intent_ref"})
    with pytest.raises(NativeGoalCreationPlanError):
        decode_native_goal_creation_intent(json.dumps(invalid))


@pytest.mark.parametrize("path,bad", [
    (["schema_id"], "foreign"), (["caller_current"], True),
    (["initial_state", "status"], "active"), (["initial_state", "hold"], "held"),
    (["initial_state", "owner_ref"], "object:foreign"), (["initial_state", "title"], "Other"),
    (["initial_state", "intent"], True), (["initial_state", "priority"], 2),
    (["initial_state", "source_refs"], ["object:invented:1"]),
    (["initial_state", "phase_operation_journal"], {"entries": []}),
    (["initial_state", "operational_bundle", "phases"], [dict(state="accepted")]),
    (["initial_state", "operational_bundle", "dependencies"], []),
    (["initial_state", "definitions"], []),
    (["initial_state", "definitions", 0, "ordinal"], True),
    (["initial_state", "lanes", 0, "operational_state"], "active"),
    (["initial_state", "lanes", 0, "current_issue_ref"], "issue:1"),
    (["initial_state", "lanes", 0, "current_work_association_ref"], "work:1"),
    (["initial_state", "lanes", 0, "hold_authority_refs"], ["hold:1"]),
    (["initial_state", "execution_authority", "legacy_execution_disposition"], "retired"),
    (["initial_state", "execution_authority", "creation_intent_ref"], "goal-native-creation-intent:sha256:" + "0"*64),
    (["intent", "context_ref"], "goal-native-creation-context:sha256:" + "0"*64),
    (["request", "owner_ref"], True), (["context", "verified_at"], True),
])
def test_redigested_substitution_refuses(path, bad):
    body = plan().to_wire()
    item = body
    for key in path[:-1]:
        item = item[key]
    item[path[-1]] = bad
    with pytest.raises(NativeGoalCreationPlanError):
        decode_native_goal_creation_plan_claim(redigest(body))


def replace_claim(body, field, **changes):
    claim = body[field]
    schema = claim["schema_id"]
    # Field name is explicit for the claims changed by these tests.
    ref_field = {"identity_absence":"absence_ref", "context":"context_ref", "grant":"grant_ref",
                 "namespace_exclusion":"exclusion_ref"}[field]
    fields = {k:v for k,v in claim.items() if k not in {"schema_id", ref_field}}
    body[field] = make_native_creation_claim(schema, dict(fields, **changes)).to_wire()


def test_canonical_foreign_absence_claim_refuses_even_with_rejoined_context():
    body = plan().to_wire()
    replace_claim(body, "identity_absence", goal_tag="goal/2026-10-04/foreign")
    replace_claim(body, "context", identity_absence_ref=body["identity_absence"]["absence_ref"])
    body["intent"] = make_native_goal_creation_intent(body["request"]["request_ref"], body["context"]["context_ref"]).to_wire()
    with pytest.raises(NativeGoalCreationPlanError, match="absence_goal_join"):
        decode_native_goal_creation_plan_claim(redigest(body))


def test_canonical_foreign_request_claims_refuse():
    body = plan().to_wire()
    foreign = "goal-native-creation-request:sha256:" + "0"*64
    replace_claim(body, "grant", request_ref=foreign)
    replace_claim(body, "namespace_exclusion", request_ref=foreign)
    replace_claim(body, "context", request_ref=foreign, creation_grant_ref=body["grant"]["grant_ref"],
                  namespace_exclusion_ref=body["namespace_exclusion"]["exclusion_ref"])
    with pytest.raises(NativeGoalCreationPlanError, match="request_context_join"):
        decode_native_goal_creation_plan_claim(redigest(body))


def test_actual_constructed_object_mutation_refuses_without_repair():
    value = plan()
    mutated = json.dumps(dict(value.to_wire(), plan_ref="goal-native-creation-plan:sha256:" + "0"*64))
    object.__setattr__(value, "canonical_body", mutated)
    with pytest.raises(NativeGoalCreationPlanError):
        encode_native_goal_creation_plan_claim(value)
    assert value.canonical_body == mutated


def test_full_claim_changes_bind_intent_and_plan_without_future_commit():
    values = list(fixture())
    context = values[1].to_wire()
    fields = {k:v for k,v in context.items() if k not in {"schema_id", "context_ref"}}
    values[1] = make_native_creation_claim(CONTEXT_SCHEMA, dict(fields, verified_at="2026-10-04T01:00:02Z"))
    altered = make_native_goal_creation_plan_claim(*values)
    original = plan()
    assert altered.plan_ref != original.plan_ref
    assert altered.to_wire()["intent"]["intent_ref"] != original.to_wire()["intent"]["intent_ref"]
    assert altered.to_wire()["initial_state"]["execution_authority"] != original.to_wire()["initial_state"]["execution_authority"]
    for field in ("repository_commit_ref", "publication_ref", "document_ref", "verifier_token"):
        assert field not in original.to_wire()


def test_existing_authored_external_edges_survive_without_qualification():
    values = list(fixture())
    request_body = values[0].to_wire()
    fields = {k:v for k,v in request_body.items() if k not in {"schema_id", "request_ref"}}
    fields["dependencies"][0]["prerequisite"]["goal_tag"] = "goal/2026-10-04/external"
    values[0] = make_native_goal_creation_request(fields)
    # Rebuild only consistency claims; this still issues no authority.
    body = plan().to_wire()
    replace_claim(body, "grant", request_ref=values[0].request_ref)
    replace_claim(body, "namespace_exclusion", request_ref=values[0].request_ref)
    replace_claim(body, "context", request_ref=values[0].request_ref,
                  creation_grant_ref=body["grant"]["grant_ref"], namespace_exclusion_ref=body["namespace_exclusion"]["exclusion_ref"])
    from aware_goal_operational_runtime.native_creation_claims import decode_native_creation_claim
    for index, field in ((1,"context"), (2,"grant"), (5,"namespace_exclusion")):
        values[index] = decode_native_creation_claim(json.dumps(body[field]))
    result = make_native_goal_creation_plan_claim(*values).to_wire()
    assert result["initial_state"]["operational_bundle"]["dependencies"] == fields["dependencies"]
    assert "dependency_observations" not in result["initial_state"]


@pytest.mark.parametrize("payload", [None, True, 3, [], "null", "[]", "{}", "{bad json}"])
def test_malformed_payload_refuses(payload):
    with pytest.raises(NativeGoalCreationPlanError):
        decode_native_goal_creation_plan_claim(payload)


def test_duplicates_unknown_nested_fields_and_constructor_refuse():
    payload = encode_native_goal_creation_plan_claim(plan())
    duplicated = payload.replace('"status":"proposed"', '"status":"proposed","status":"proposed"')
    with pytest.raises(NativeGoalCreationPlanError):
        decode_native_goal_creation_plan_claim(duplicated)
    with pytest.raises(NativeGoalCreationPlanError):
        NativeGoalCreationPlanClaimV1(duplicated)
    body = plan().to_wire()
    body["context"]["caller_current"] = True
    with pytest.raises(NativeGoalCreationPlanError):
        decode_native_goal_creation_plan_claim(redigest(body))
