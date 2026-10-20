"""Structural fixture claims only; no accepted Goal or actor authority."""

import hashlib
import json
from dataclasses import replace

import pytest

from aware_goal_operational_runtime.phase_document_v5 import (
    DOCUMENT_V5, PROVENANCE_PROFILE, GoalPhaseDocumentV5Error, GoalPhaseNativeDocumentV5,
    decode_goal_phase_native_document_v5, encode_goal_phase_native_document_v5,
)
from aware_goal_operational_runtime.phase_acceptance_provenance import (
    OWNER_PROFILE, LEGACY_PROFILE, QUALIFICATION_SCHEMA, POLICY_SCHEMA, BASELINE_POLICY,
    make_acceptance_provenance_claim_v2,
)
from aware_goal_operational_runtime.phase_document import (
    GoalPhaseNativeDocumentV2, GoalPhaseExecutionAuthorityV1, GoalLanePhaseDefinitionV1,
    GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4, GoalNativeLaneAuthorityV1,
    GoalPhaseOperationJournalV1, GoalPhaseOperationJournalEntryV1,
    decode_goal_phase_native_document, encode_goal_phase_native_document,
)
from aware_goal_operational_runtime.phase_contracts import (
    GoalPhaseCoordinate, GoalLanePhaseGate, GoalLanePhase, GoalLanePhaseState,
    GoalPhaseContractBundleV1, GoalLanePhaseGateObservation, GoalLanePhaseGateOutcome, GoalPhaseDependency,
)
from aware_goal_operational_runtime.dependencies import GoalDependencyRelation
from aware_goal_operational_runtime.phase_frontier import goal_phase_dependency_digest


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return "sha256:" + hashlib.sha256(wire(value).encode()).hexdigest()


def ref(domain, value):
    return domain + digest(value)


def coord(phase="portal"):
    return GoalPhaseCoordinate("goal/2026-10-03/example", "runtime", phase)


def coordinate(value):
    return {"goal_tag": value.goal_tag, "lane_key": value.lane_key, "phase_key": value.phase_key}


def base(*, accepted=False, observed=False, dependencies=False):
    gate = GoalLanePhaseGate("review", "Meet the unchanged promise.", "contract:portal", "evidence:portal", ())
    definition = GoalLanePhaseDefinitionV1(coordinate=coord(), ordinal=1, title="Portal", intent="Establish portal.", gate=gate)
    observation = GoalLanePhaseGateObservation(
        "object:observation:1", gate.gate_digest, GoalLanePhaseGateOutcome.SATISFIED,
        OWNER_PROFILE, ("object:evidence:1",), ("object:revision:original",),
        "2026-10-03T00:00:00Z", "object:currentness:claim",
    )
    phase = GoalLanePhase(coord(), "Portal", 1, "Establish portal.",
                          GoalLanePhaseState.ACCEPTED if accepted else GoalLanePhaseState.ACTIVE, gate,
                          gate_observations=(observation,) if observed or accepted else (),
                          last_receipt_ref=ref("goal-phase-acceptance:", "accepted") if accepted else None)
    edges = (GoalPhaseDependency(
        coord().goal_tag, "requires_portal", coord(),
        GoalPhaseCoordinate("goal/2026-10-03/other", "runtime", "prerequisite"), gate.gate_digest,
        GoalDependencyRelation.REQUIRES_ACCEPTANCE, "Requires prerequisite.",
    ),) if dependencies else ()
    return GoalPhaseNativeDocumentV2(
        goal_tag=coord().goal_tag, compatibility_projection_sha256=digest("compatibility"),
        compatibility_projection_byte_count=42, definitions=(definition,),
        operational_bundle=GoalPhaseContractBundleV1((phase,), edges), unresolved_dependencies=(),
        source_refs=("object:source:1",), execution_authority=GoalPhaseExecutionAuthorityV1(
            source_execution_authority_profile="hybrid_legacy_row_phase_native_v1",
            parity_ref=ref("goal-phase-native-compatibility-parity:", "parity"),
            proposal_aggregate_ref=ref("goal-phase-native-operational-bootstrap-proposal:", "proposal"),
            coordinator_acceptance_ref=ref("goal-phase-native-operational-bootstrap-coordinator-acceptance:", "acceptance"),
        ),
    )


def qualification(document, kind, evidence_ref, *, mode="owner_attested"):
    return make_acceptance_provenance_claim_v2(QUALIFICATION_SCHEMA, {
        "coordinate": coordinate(coord()), "definition_ref": document.definitions[0].definition_ref,
        "gate_digest": document.definitions[0].gate.gate_digest, "evidence_kind": kind,
        "evidence_ref": evidence_ref,
        "evidence_source_epoch": {"provider_binding_ref": "object:repository:1", "source_revision": "object:revision:original",
                                  "document_ref": document.document_ref, "goal_sha256": digest("source")},
        "mode": mode, "profile": OWNER_PROFILE if mode == "owner_attested" else LEGACY_PROFILE,
        "authority_refs": ["object:authority:1"] if mode == "owner_attested" else [],
        "evidence_refs": ["object:evidence:1"] if mode == "owner_attested" else [],
        "decision_ref": ref("goal-owner-phase-acceptance-decision:", "decision") if mode == "owner_attested" else None,
        "profile_authorization_ref": ref("goal-owner-phase-acceptance-authorization:", "authorization") if mode == "owner_attested" else None,
    }).to_wire()


def redigest(body):
    body["document_ref"] = ref("goal-phase-document:", {k: v for k, v in body.items() if k != "document_ref"})
    return wire(body).encode()


def document_wire(document):
    body = json.loads(encode_goal_phase_native_document(document))
    body["schema_id"] = DOCUMENT_V5
    body.setdefault("native_lane_authorities", [])
    body.setdefault("operation_journal_profile", "v1" if "phase_operation_journal" in body else "none")
    body["acceptance_provenance_profile"] = PROVENANCE_PROFILE
    body["acceptance_qualifications"] = []
    for phase in document.operational_bundle.phases:
        if phase.state is GoalLanePhaseState.ACCEPTED:
            body["acceptance_qualifications"].append(qualification(document, "acceptance", phase.last_receipt_ref))
        for observation in phase.gate_observations:
            if observation.outcome is GoalLanePhaseGateOutcome.SATISFIED:
                body["acceptance_qualifications"].append(qualification(document, "gate_observation", observation.observation_ref))
    body["acceptance_dependency_policies"] = []
    declarations = body["operational_bundle"]["dependencies"]
    for dependency, declaration in zip(document.operational_bundle.dependencies, declarations, strict=True):
        body["acceptance_dependency_policies"].append(make_acceptance_provenance_claim_v2(POLICY_SCHEMA, {
            "declaration": declaration, "declaration_digest": goal_phase_dependency_digest(dependency),
            "required_modes": ["evaluator_proven"], "authority_profile": "versioned_baseline",
            "policy_authority_ref": BASELINE_POLICY,
        }).to_wire())
    redigest(body)
    return body


@pytest.mark.parametrize("accepted,observed,dependencies", [(False, False, False), (False, True, False),
                                                           (True, True, False), (True, True, True)])
def test_v5_round_trip_preserves_complete_provenance_and_cannot_issue_authority(accepted, observed, dependencies):
    original = base(accepted=accepted, observed=observed, dependencies=dependencies)
    body = document_wire(original)
    doc = decode_goal_phase_native_document_v5(redigest(body))
    assert doc.to_wire() == body
    assert encode_goal_phase_native_document_v5(doc) == redigest(body)
    assert not hasattr(doc, "verifier_token")
    assert not hasattr(doc, "accepted")
    assert not hasattr(doc, "base_document")
    for field in ("definitions", "operational_bundle", "source_refs", "execution_authority"):
        assert body[field] == json.loads(encode_goal_phase_native_document(original))[field]
    with pytest.raises(ValueError):
        decode_goal_phase_native_document(redigest(body))


@pytest.mark.parametrize("kind", ["journal", "lane", "lane-journal"])
def test_v5_preserves_existing_journal_and_lane_components(kind):
    original = base()
    fields = {name: getattr(original, name) for name in (
        "goal_tag", "compatibility_projection_sha256", "compatibility_projection_byte_count", "definitions",
        "operational_bundle", "unresolved_dependencies", "source_refs", "execution_authority",
    )}
    entry = GoalPhaseOperationJournalEntryV1(
        operation_kind="approve_pursuit", decision="approve", coordinate=coord(),
        gate_digest=original.definitions[0].gate.gate_digest, source_preimage_ref=original.document_ref,
        actor_ref="identity:actor-one", action_occurrence_ref=ref("actor-action-occurrence:", "action"),
        policy_ref=ref("goal-phase-approval-policy:", "policy"), policy_digest=digest("policy"),
        idempotency_key="approval-1", delta_ref=ref("goal-phase-delta:", "delta"),
        event_ref=ref("goal-phase-event:", "event"), approval_entry_ref=None,
        agent_run_request_ref=None, assignment_ref=None, execution_ref=None,
    )
    journal = GoalPhaseOperationJournalV1(entries=(entry,))
    if kind == "journal":
        source = GoalPhaseNativeDocumentV3(**fields, phase_operation_journal=journal)
    else:
        lane = GoalNativeLaneAuthorityV1(
            goal_tag=original.goal_tag, lane_key="runtime", role="foundation", owner_profile="provider_execution_v1",
            owner_ref="codex-source", operational_state="ready", state_detail=None,
            current_work_association_ref=None, hold_authority_refs=(),
        )
        # This fixture has no Work; state is independent of Work presence.
        source = GoalPhaseNativeDocumentV4(**fields, native_lane_authorities=(lane,),
                                            operation_journal_profile="v1" if kind == "lane-journal" else "none",
                                            phase_operation_journal=journal if kind == "lane-journal" else None)
    body = document_wire(source)
    assert decode_goal_phase_native_document_v5(redigest(body)).to_wire() == body


@pytest.mark.parametrize("mode", ["missing", "extra", "duplicate", "order", "wrong-gate", "wrong-definition", "wrong-epoch", "stripped-mode", "missing-policy", "foreign-policy"])
def test_redigested_coverage_and_pair_substitutions_refuse(mode):
    source = base(accepted=True, dependencies=True)
    body = document_wire(source)
    records = body["acceptance_qualifications"]
    if mode == "missing": records.pop()
    elif mode == "extra": records.append(dict(records[0], evidence_ref=ref("goal-phase-acceptance:", "foreign")))
    elif mode == "duplicate": records.append(records[0])
    elif mode == "order": records.reverse()
    elif mode in ("wrong-gate", "wrong-definition", "wrong-epoch"):
        fields = {k: v for k, v in records[1].items() if k not in ("schema_id", "qualification_ref")}
        if mode == "wrong-gate": fields["gate_digest"] = digest("foreign")
        elif mode == "wrong-definition": fields["definition_ref"] = ref("goal-phase-definition:", "foreign")
        else: fields["evidence_source_epoch"] = dict(fields["evidence_source_epoch"], source_revision="object:revision:foreign")
        records[1] = make_acceptance_provenance_claim_v2(QUALIFICATION_SCHEMA, fields).to_wire()
    elif mode == "stripped-mode": records[1] = qualification(source, "gate_observation", "object:observation:1", mode="legacy_unqualified")
    elif mode == "missing-policy": body["acceptance_dependency_policies"] = []
    elif mode == "foreign-policy":
        policy = body["acceptance_dependency_policies"][0]
        fields = {k: v for k, v in policy.items() if k not in ("schema_id", "policy_ref")}
        fields["declaration"] = dict(fields["declaration"], reason="Foreign reason.")
        declaration = fields["declaration"]
        fields["declaration_digest"] = goal_phase_dependency_digest(GoalPhaseDependency(
            declaration["owner_goal_tag"], declaration["dependency_key"],
            GoalPhaseCoordinate(**declaration["dependent"]), GoalPhaseCoordinate(**declaration["prerequisite"]),
            declaration["required_gate_digest"], GoalDependencyRelation.REQUIRES_ACCEPTANCE,
            declaration["reason"], tuple(declaration["evidence_refs"]),
        ))
        body["acceptance_dependency_policies"][0] = make_acceptance_provenance_claim_v2(POLICY_SCHEMA, fields).to_wire()
    with pytest.raises(GoalPhaseDocumentV5Error):
        decode_goal_phase_native_document_v5(redigest(body))


@pytest.mark.parametrize("field,value", [("acceptance_provenance_profile", "unknown"), ("operation_journal_profile", "unknown"),
                                        ("native_lane_authorities", True), ("authority_profile", "foreign"),
                                        ("acceptance_qualifications", "stripped"), ("acceptance_dependency_policies", {}),
                                        ("extra", True)])
def test_unknown_profiles_and_shapes_refuse(field, value):
    body = document_wire(base())
    body[field] = value
    with pytest.raises(GoalPhaseDocumentV5Error):
        decode_goal_phase_native_document_v5(redigest(body))


def test_mutated_canonical_storage_and_detached_wire():
    body = document_wire(base())
    doc = decode_goal_phase_native_document_v5(redigest(body))
    detached = doc.to_wire()
    detached["source_refs"].append("object:foreign")
    assert doc.to_wire() == body
    object.__setattr__(doc, "canonical_body", wire(dict(body, document_ref=ref("goal-phase-document:", "foreign"))))
    with pytest.raises(GoalPhaseDocumentV5Error):
        encode_goal_phase_native_document_v5(doc)
    with pytest.raises(GoalPhaseDocumentV5Error, match="canonical"):
        GoalPhaseNativeDocumentV5(json.dumps(body, indent=2))


@pytest.mark.parametrize("data", [b"\xff", b"[]", b'{"schema_id":"a","schema_id":"b"}', b'{"a":NaN}'])
def test_malformed_payload_refuses(data):
    with pytest.raises(GoalPhaseDocumentV5Error):
        decode_goal_phase_native_document_v5(data)


def test_historical_gate_observation_is_preserved_only_as_legacy_unqualified():
    source = base(observed=True)
    phase = source.operational_bundle.phases[0]
    observation = replace(phase.gate_observations[0], evaluator_ref="historical:unknown")
    source = replace(source, operational_bundle=GoalPhaseContractBundleV1(
        (replace(phase, gate_observations=(observation,)),), (),
    ))
    body = document_wire(source)
    record = qualification(source, "gate_observation", observation.observation_ref, mode="legacy_unqualified")
    fields = {k: v for k, v in record.items() if k not in ("schema_id", "qualification_ref")}
    fields["gate_digest"] = observation.gate_digest
    fields["definition_ref"] = ref("goal-phase-definition:", "original-historical-definition")
    body["acceptance_qualifications"] = [make_acceptance_provenance_claim_v2(QUALIFICATION_SCHEMA, fields).to_wire()]
    restored = decode_goal_phase_native_document_v5(redigest(body))
    assert restored.to_wire()["operational_bundle"] == body["operational_bundle"]
    assert restored.to_wire()["acceptance_qualifications"][0]["mode"] == "legacy_unqualified"
