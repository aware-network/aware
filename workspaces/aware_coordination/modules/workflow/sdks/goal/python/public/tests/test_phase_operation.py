"""Portable identity and error boundary for native read-only eligibility."""

from __future__ import annotations

import pytest
import hashlib
import json
from copy import deepcopy

from aware_goal_sdk.phase_operation import (
    GoalPhaseObserveEligibilityError,
    GoalPhaseObserveEligibilityRequestV1,
    GoalPhaseOperationClient,
    GoalPhaseObserveEligibilityRequestV2,
    decode_goal_phase_observe_eligibility_request_v2,
    decode_goal_phase_observe_eligibility_result_v2,
    issue_goal_phase_operation_result_ref_v2,
)


class _UnavailableProvider:
    def observe_eligibility(
        self, request: GoalPhaseObserveEligibilityRequestV1
    ) -> dict[str, object]:
        raise ValueError("qualified source unavailable")


def test_sdk_operation_reports_provider_refusal_without_inventing_a_result() -> None:
    request = GoalPhaseObserveEligibilityRequestV1(
        source_locator_ref="repository-path:customer/goals/sample.md",
        goal_tag="goal/2026-09-27/sample",
        lane_key="runtime",
        phase_key="candidate",
        expected_goal_sha256="sha256:" + "a" * 64,
        expected_native_document_ref="goal-phase-document:sha256:" + "b" * 64,
        expected_gate_digest="sha256:" + "c" * 64,
    )

    with pytest.raises(GoalPhaseObserveEligibilityError, match="qualified source unavailable"):
        GoalPhaseOperationClient(_UnavailableProvider()).observe_eligibility(request)


def _object_transport():
    # Structural transport fixture only: not an object authority issuer, and
    # no test uses it to authorize an effect or bypass the neutral verifier.
    request = GoalPhaseObserveEligibilityRequestV2(
        source_locator_ref="object:goal:sample", goal_tag="goal/2026-09-27/sample",
        lane_key="runtime", phase_key="candidate", expected_goal_sha256="sha256:" + "a" * 64,
        expected_native_document_ref="goal-phase-document:sha256:" + "b" * 64,
        expected_gate_digest="sha256:" + "c" * 64, lane_authority_locator_ref="object:lane-publication:sample",
    )
    coordinate = {"goal_tag": request.goal_tag, "lane_key": request.lane_key, "phase_key": request.phase_key}
    decision = {
        "schema_id": "aware.goal.phase-eligibility-decision.v2", "coordinate": coordinate,
        "lane_authority_profile": "native_carrier_v1", "source_revision_ref": "object-revision:sample",
        "source_binding_ref": "object-source:sample", "scope_currentness_ref": "object-currentness:sample",
        "effect_profile": "read_only_non_authorizing", "event_effect": "none", "dispatch_effect": "none",
        "native_document_ref": request.expected_native_document_ref, "gate_digest": request.expected_gate_digest,
        "goal_authority_ref": "goal-authority:sample", "lane_authority_ref": "lane-authority:sample",
        "observation_coverage": "none", "phase_state": "active", "projection_health": "clean",
        "dependency_gate": {"state": "satisfied", "incoming_count": 0, "dependency_keys": [],
            "satisfied": [], "pending": [], "not_evaluated": [], "stale": [], "unresolved": [], "rejected": []},
        "unresolved_dependency_keys": [], "eligibility": "eligible", "reasons": [],
    }
    decision["decision_ref"] = "goal-phase-eligibility-decision:sha256:" + hashlib.sha256(
        json.dumps(decision, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    wire = {"schema_id": "aware.goal.phase-operation-result.v2", "operation_kind": "observe_eligibility",
        "status": "observed", "effect_profile": "read_only_non_authorizing", "event_effect": "none", "dispatch_effect": "none",
        "source_locator_ref": request.source_locator_ref, "lane_authority_locator_ref": request.lane_authority_locator_ref,
        "gate_authority_locator_ref": None, "coordinate": coordinate, "source_revision_ref": "object-revision:sample",
        "goal_sha256": request.expected_goal_sha256, "decision": decision, "reasons": []}
    wire["result_ref"] = issue_goal_phase_operation_result_ref_v2(wire)
    return request, wire


def test_v2_transport_carries_object_locators_without_git_or_markdown_interpretation():
    request, payload = _object_transport()
    assert decode_goal_phase_observe_eligibility_request_v2(request.to_wire()) == request
    class TransportOnlyProvider:
        def observe_eligibility_v2(self, request):
            return payload
    actual = GoalPhaseOperationClient(TransportOnlyProvider()).observe_eligibility_v2(request)
    assert actual == payload
    # Copy ownership is transport ergonomics, not an authority seal.
    actual["decision"]["reasons"].append("changed")
    assert payload["decision"]["reasons"] == []


@pytest.mark.parametrize("field,value", [("schema_id", "aware.goal.phase-operation-request.v1"),
    ("lane_authority_locator_ref", True), ("gate_authority_locator_ref", []), ("expected_goal_sha256", "a" * 64)])
def test_v2_request_refuses_type_and_profile_substitution(field, value):
    request, _ = _object_transport()
    wire = request.to_wire()
    wire[field] = value
    with pytest.raises((TypeError, ValueError)):
        decode_goal_phase_observe_eligibility_request_v2(wire)


@pytest.mark.parametrize("fault", ["unknown", "dispatch", "coordinate", "source", "gate", "integrity", "decision_unknown", "count", "duplicate_partition", "bool_count"])
def test_v2_transport_refuses_schema_binding_and_integrity_tampering(fault):
    request, payload = _object_transport()
    bad = deepcopy(payload)
    if fault == "unknown": bad["unexpected"] = True
    elif fault == "dispatch": bad["dispatch_effect"] = "agent.run"
    elif fault == "coordinate": bad["coordinate"]["phase_key"] = "foreign"
    elif fault == "source": bad["decision"]["source_revision_ref"] = "object-revision:foreign"
    elif fault == "gate": bad["decision"]["gate_digest"] = "sha256:" + "f" * 64
    elif fault == "integrity": bad["result_ref"] = "goal-phase-operation-result:sha256:" + "f" * 64
    elif fault == "decision_unknown": bad["decision"]["unexpected"] = True
    elif fault == "count": bad["decision"]["dependency_gate"]["incoming_count"] = 1
    elif fault == "bool_count": bad["decision"]["dependency_gate"]["incoming_count"] = False
    else:
        gate = bad["decision"]["dependency_gate"]
        gate.update(incoming_count=1, dependency_keys=["one"], satisfied=["one"], pending=["one"])
    with pytest.raises((TypeError, ValueError)):
        decode_goal_phase_observe_eligibility_result_v2(bad, request=request)


def _redigest(payload):
    decision = payload["decision"]
    body = {key: value for key, value in decision.items() if key != "decision_ref"}
    decision["decision_ref"] = "goal-phase-eligibility-decision:sha256:" + hashlib.sha256(
        json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    payload["result_ref"] = issue_goal_phase_operation_result_ref_v2(
        {key: value for key, value in payload.items() if key != "result_ref"})


@pytest.mark.parametrize("field,value", [
    ("lane_authority_profile", "unknown"), ("eligibility", "running"),
    ("observation_coverage", "unknown"), ("phase_state", "running"),
    ("projection_health", "consistent"), ("reasons", ["unknown"]),
    ("projection_health", "ambiguous"), ("phase_state", "held"),
    ("unresolved_dependency_keys", ["external"]),
    ("eligibility", "held"), ("reasons", ["frontier_ineligible"]),
    ("observation_coverage", "complete"),
])
def test_v2_transport_rejects_redigested_invalid_or_contradictory_decision(field, value):
    request, payload = _object_transport()
    payload["decision"][field] = value
    if field == "reasons":
        payload["reasons"] = value
    _redigest(payload)

    class FakeProvider:
        def observe_eligibility_v2(self, request):
            return payload

    with pytest.raises(GoalPhaseObserveEligibilityError):
        GoalPhaseOperationClient(FakeProvider()).observe_eligibility_v2(request)


@pytest.mark.parametrize("fault", ["unknown_state", "false_aggregate", "eligible_stale", "false_coverage"])
def test_v2_transport_rejects_redigested_dependency_contradictions(fault):
    request, payload = _object_transport()
    d = payload["decision"]
    gate = d["dependency_gate"]
    if fault == "unknown_state":
        gate["state"] = "open"
    else:
        gate.update(state="stale", incoming_count=1, dependency_keys=["one"], stale=["one"])
        d["observation_coverage"] = "complete"
        if fault == "false_aggregate":
            gate["state"] = "satisfied"
        elif fault == "false_coverage":
            d.update(eligibility="held", reasons=["frontier_ineligible"], observation_coverage="none")
            payload["reasons"] = d["reasons"]
    _redigest(payload)
    with pytest.raises(ValueError):
        decode_goal_phase_observe_eligibility_result_v2(payload, request=request)


@pytest.mark.parametrize("phase_state", ["accepted", "withdrawn"])
def test_v2_transport_preserves_terminal_non_authorizing_decisions(phase_state):
    request, payload = _object_transport()
    d = payload["decision"]
    d.update(phase_state=phase_state, eligibility="held", reasons=["frontier_ineligible", "phase_not_pursuable"])
    d["dependency_gate"].update(state="not_applicable", incoming_count=1, dependency_keys=["historical"])
    payload["reasons"] = d["reasons"]
    _redigest(payload)
    assert decode_goal_phase_observe_eligibility_result_v2(payload, request=request) == payload
