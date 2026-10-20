"""Provider-neutral, authority-bound supplied-evidence snapshot.

This intake supports issued introduction holds and the opted-in V2 evaluator. A codec, digest or
constructed snapshot is not authority; qualification requires a concrete source
verifier. Carrier Gate claims and hold advancement/release remain unsupported.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

from .identity import fingerprint
from .phase_contracts import GoalPhaseCoordinate, GoalLanePhase, GoalLanePhaseGateObservation, GoalLanePhaseGateOutcome
from .phase_document import GoalPhaseNativeDocumentV4, encode_goal_phase_native_document
from .phase_frontier import goal_phase_dependency_digest
from .phase_native_lane_hold import (
    GoalNativeLaneHoldDecisionV1, decode_goal_native_lane_hold_decision, exact_hold_wire,
)

if TYPE_CHECKING:
    from .phase_runtime_checks_review import RuntimeChecksEvaluationV2, RuntimeChecksVerifiedInputV2


class GoalNativeLaneEvidenceIssuerV2:
    """Code-admitted verifier implementation, never an authored callback."""

    def require_snapshot(self, _value: GoalNativeLaneEvidenceSnapshotV2) -> None:
        raise NotImplementedError("native lane evidence needs a concrete issuer")


_ISSUER_TYPES: set[type[GoalNativeLaneEvidenceIssuerV2]] = set()


def _register_native_lane_evidence_issuer(value: object) -> None:  # pyright: ignore[reportUnusedFunction]
    if not isinstance(value, type) or not issubclass(value, GoalNativeLaneEvidenceIssuerV2):
        raise TypeError("evidence issuer must be a concrete implementation")
    _ISSUER_TYPES.add(value)


@dataclass(frozen=True, slots=True)
class GoalNativeLaneQualifiedHoldV2:
    decision: GoalNativeLaneHoldDecisionV1
    verifier_profile: str
    issuance_authority: Mapping[str, object]
    evidence_source_revision_ref: str
    observed_source_revision_ref: str
    currentness_ref: str

    def __post_init__(self) -> None:
        if type(self) is not GoalNativeLaneQualifiedHoldV2 or type(self.decision) is not GoalNativeLaneHoldDecisionV1:
            raise TypeError("hold record must be exact")
        _ = decode_goal_native_lane_hold_decision(self.decision.to_wire())
        for name, token in (("verifier_profile", self.verifier_profile),
            ("evidence_source_revision_ref", self.evidence_source_revision_ref),
            ("observed_source_revision_ref", self.observed_source_revision_ref), ("currentness_ref", self.currentness_ref)):
            _ = _text(token, name)
        if self.evidence_source_revision_ref != self.decision.source_revision_ref:
            raise ValueError("native_lane_hold_evidence_source_mismatch")
        _json_object(self.issuance_authority)
        if not self.issuance_authority:
            raise ValueError("native_lane_hold_issuance_authority_absent")

    def to_wire(self) -> dict[str, object]:
        body = {
            "schema_id": "aware.goal.native-lane-qualified-hold.v2",
            "decision": self.decision.to_wire(), "verifier_profile": self.verifier_profile,
            "issuance_authority": dict(self.issuance_authority),
            "evidence_source_revision_ref": self.evidence_source_revision_ref,
            "observed_source_revision_ref": self.observed_source_revision_ref,
            "currentness_ref": self.currentness_ref,
        }
        return {**body, "authority_binding_ref": "goal-native-lane-qualified-hold:" + fingerprint(body)}


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GoalNativeLaneQualifiedGateV2:
    """A joined issued input/output graph, not a carrier observation claim."""

    evaluator_input: RuntimeChecksVerifiedInputV2
    evaluation: RuntimeChecksEvaluationV2

    def __post_init__(self) -> None:
        from .phase_runtime_checks_review import (
            decode_runtime_checks_evaluation, require_runtime_checks_evaluation, require_runtime_checks_input,
        )
        if type(self) is not GoalNativeLaneQualifiedGateV2:
            raise TypeError("qualified Gate must be exact")
        _ = require_runtime_checks_input(self.evaluator_input)
        _ = require_runtime_checks_evaluation(self.evaluation)
        # Issued results from another valid evaluation cannot be interchanged.
        _ = decode_runtime_checks_evaluation(self.evaluation.to_wire(), qualified=self.evaluator_input)

    def to_wire(self) -> dict[str, object]:
        evaluation = self.evaluation.to_wire()
        return {"coordinate": evaluation["coordinate"], "evaluator_profile": evaluation["evaluator_profile"],
            "evaluation": evaluation, "gate_observation": evaluation["gate_observation"]}


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GoalNativeLaneEvidenceSnapshotV2:
    goal_tag: str
    lane_key: str
    document_ref: str
    source_revision_ref: str
    source_binding_ref: str
    incident_declarations: tuple[tuple[str, str], ...]
    gate_observations: tuple[GoalNativeLaneQualifiedGateV2, ...]
    holds: tuple[GoalNativeLaneQualifiedHoldV2, ...]
    authority_inventory: tuple[Mapping[str, object], ...]
    source_evidence: GoalNativeLaneEvidenceIssuerV2

    def __post_init__(self) -> None:
        if type(self) is not GoalNativeLaneEvidenceSnapshotV2:
            raise TypeError("snapshot must be exact")
        for name, token in (("goal_tag", self.goal_tag), ("lane_key", self.lane_key),
            ("document_ref", self.document_ref), ("source_revision_ref", self.source_revision_ref),
            ("source_binding_ref", self.source_binding_ref)):
            _ = _text(token, name)
        _ = GoalPhaseCoordinate(self.goal_tag, self.lane_key, "lane-evidence")
        if not re.fullmatch(r"goal-phase-document:sha256:[0-9a-f]{64}", self.document_ref):
            raise ValueError("snapshot document_ref must be exact")
        if type(self.incident_declarations) is not tuple:
            raise TypeError("incident declarations must be an exact tuple")
        keys: list[str] = []
        for pair in self.incident_declarations:
            if type(pair) is not tuple or len(pair) != 2:
                raise TypeError("incident declaration must preserve its key/digest pair")
            keys.append(_text(pair[0], "dependency_key"))
            _ = _text(pair[1], "dependency_digest")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", pair[1]):
                raise ValueError("dependency digest must be exact")
        if keys != sorted(set(keys)):
            raise ValueError("incident declarations must be sorted and unique")
        if type(self.gate_observations) is not tuple:
            raise ValueError("native_lane_gate_authority_unavailable")
        coordinates: list[tuple[str, str, str]] = []
        for gate in self.gate_observations:
            if type(gate) is not GoalNativeLaneQualifiedGateV2:
                raise ValueError("native_lane_gate_authority_unavailable")
            gate.__post_init__()
            evaluation = gate.evaluation.to_wire()
            coordinate = cast(dict[str, str], evaluation["coordinate"])
            if (coordinate["goal_tag"], coordinate["lane_key"]) != (self.goal_tag, self.lane_key):
                raise ValueError("native_lane_gate_snapshot_coordinate_mismatch")
            verification = cast(dict[str, object], evaluation["source_verification"])
            if (evaluation["source_revision_ref"] != self.source_revision_ref
                or verification["observed_source_revision_ref"] != self.source_revision_ref
                or verification["observed_document_ref"] != self.document_ref):
                raise ValueError("native_lane_gate_snapshot_epoch_mismatch")
            coordinates.append((coordinate["goal_tag"], coordinate["lane_key"], coordinate["phase_key"]))
        if coordinates != sorted(set(coordinates)):
            raise ValueError("snapshot Gates must be sorted and unique")
        if type(self.holds) is not tuple or type(self.authority_inventory) is not tuple:
            raise TypeError("snapshot records must be exact tuples")
        refs: list[str] = []
        for hold in self.holds:
            if type(hold) is not GoalNativeLaneQualifiedHoldV2:
                raise TypeError("qualified hold must be exact")
            hold.__post_init__()
            if (hold.decision.goal_tag, hold.decision.lane_key) != (self.goal_tag, self.lane_key):
                raise ValueError("native_lane_hold_snapshot_coordinate_mismatch")
            if hold.observed_source_revision_ref != self.source_revision_ref:
                raise ValueError("native_lane_hold_snapshot_epoch_mismatch")
            refs.append(hold.decision.decision_ref)
        if refs != sorted(set(refs)):
            raise ValueError("snapshot holds must be sorted and unique")
        if not self.authority_inventory:
            raise ValueError("native_lane_evidence_inventory_absent")
        for item in self.authority_inventory:
            _json_object(item)

    def to_wire(self) -> dict[str, object]:
        if any(type(record) is not GoalNativeLaneQualifiedGateV2 for record in self.gate_observations):
            raise ValueError("native_lane_gate_authority_unavailable")
        body = {
            "schema_id": "aware.goal.native-lane-evidence-snapshot.v2",
            "goal_tag": self.goal_tag, "lane_key": self.lane_key,
            "document_ref": self.document_ref, "source_revision_ref": self.source_revision_ref,
            "source_binding_ref": self.source_binding_ref,
            "incident_declarations": [list(pair) for pair in self.incident_declarations],
            "gate_observations": [record.to_wire() for record in self.gate_observations],
            "holds": [hold.to_wire() for hold in self.holds],
            "authority_inventory": [dict(record) for record in self.authority_inventory],
            "effect_profile": "read_only_non_authorizing", "event_effect": "none", "dispatch_effect": "none",
        }
        return {**body, "snapshot_ref": "goal-native-lane-evidence:" + fingerprint(body)}


def require_qualified_native_lane_evidence(value: GoalNativeLaneEvidenceSnapshotV2) -> GoalNativeLaneEvidenceSnapshotV2:
    if type(value) is not GoalNativeLaneEvidenceSnapshotV2 or not hasattr(value, "source_evidence"):
        raise ValueError("native_lane_evidence_unissued_or_mutated")
    if type(value.source_evidence) not in _ISSUER_TYPES:
        raise ValueError("native_lane_evidence_unissued_or_mutated")
    value.source_evidence.require_snapshot(value)
    value.__post_init__()
    return value


def decode_goal_native_lane_evidence_snapshot(
    payload: object, *, qualified: GoalNativeLaneEvidenceSnapshotV2,
) -> GoalNativeLaneEvidenceSnapshotV2:
    qualified = require_qualified_native_lane_evidence(qualified)
    if not exact_hold_wire(payload, qualified.to_wire()):
        raise ValueError("native_lane_evidence_transport_differs_from_authority")
    return qualified


def native_lane_incident_declarations(document: GoalPhaseNativeDocumentV4, lane_key: str) -> tuple[tuple[str, str], ...]:
    """Canonical complete key/digest pairs, including typed unresolved edges."""
    document.__post_init__()
    records = [(d.dependency_key, goal_phase_dependency_digest(d)) for d in document.operational_bundle.dependencies
        if any(c.goal_tag == document.goal_tag and c.lane_key == lane_key for c in (d.dependent, d.prerequisite))]
    body = cast(dict[str, object], json.loads(encode_goal_phase_native_document(document)))
    for raw in cast(list[dict[str, object]], body["unresolved_dependencies"]):
        if any(cast(dict[str, object], raw[name])["goal_tag"] == document.goal_tag
            and cast(dict[str, object], raw[name])["lane_key"] == lane_key for name in ("dependent", "prerequisite")):
            records.append((cast(str, raw["dependency_key"]), fingerprint(raw)))
    return tuple(sorted(records))


def require_native_lane_evidence_for_document(
    value: GoalNativeLaneEvidenceSnapshotV2, *, document: GoalPhaseNativeDocumentV4, lane_key: str,
) -> GoalNativeLaneEvidenceSnapshotV2:
    value = require_qualified_native_lane_evidence(value)
    document.__post_init__()
    if (value.goal_tag, value.lane_key, value.document_ref) != (document.goal_tag, lane_key, document.document_ref):
        raise ValueError("native_lane_evidence_document_mismatch")
    if value.incident_declarations != native_lane_incident_declarations(document, lane_key):
        raise ValueError("native_lane_evidence_incident_set_mismatch")
    if value.gate_observations:
        from .phase_runtime_checks_review import (
            require_runtime_checks_dependency_profile, runtime_checks_selected_work,
        )
        for gate in value.gate_observations:
            request = cast(dict[str, object], gate.evaluator_input.to_wire()["request"])
            _ = runtime_checks_selected_work(document, request)
            require_runtime_checks_dependency_profile(document, request)
    # This fresh evaluator entrance is not a historical carrier-claim verifier.
    if any(p.gate_observations for p in document.operational_bundle.phases if p.coordinate.lane_key == lane_key):
        raise ValueError("native_lane_gate_authority_unavailable")
    lane = next(r for r in document.native_lane_authorities if r.lane_key == lane_key)
    if tuple(hold.decision.decision_ref for hold in value.holds) != lane.hold_authority_refs:
        raise ValueError("native_lane_evidence_hold_set_mismatch")
    for hold in value.holds:
        decision = hold.decision
        if (decision.owner_profile, decision.owner_ref, decision.target_state, decision.state_detail,
            decision.current_work_association_ref) != (lane.owner_profile, lane.owner_ref, lane.operational_state,
                lane.state_detail, lane.current_work_association_ref):
            raise ValueError("native_lane_evidence_hold_carrier_mismatch")
    return value


def require_native_lane_gate_scope(
    value: GoalNativeLaneEvidenceSnapshotV2, *, document: GoalPhaseNativeDocumentV4, lane_key: str,
) -> GoalNativeLaneEvidenceSnapshotV2:
    """Pure historical scope check, not issuance or whole-document currentness.

    The provider proves every repository edge. Only unrelated aggregate bytes
    may differ here; exact selected definition/Gate/Work and incident identities
    must remain unchanged. The current entrance still requires exact document.
    """
    from .phase_runtime_checks_review import require_runtime_checks_dependency_profile, runtime_checks_selected_work
    value = require_qualified_native_lane_evidence(value)
    document.__post_init__()
    if (value.goal_tag, value.lane_key) != (document.goal_tag, lane_key) or not value.gate_observations or value.holds:
        raise ValueError("native_lane_gate_scope_profile_unsupported")
    if value.incident_declarations != native_lane_incident_declarations(document, lane_key):
        raise ValueError("native_lane_evidence_incident_set_mismatch")
    for gate in value.gate_observations:
        request = cast(dict[str, object], gate.evaluator_input.to_wire()["request"])
        _ = runtime_checks_selected_work(document, request)
        require_runtime_checks_dependency_profile(document, request)
    return value


def native_lane_gate_issue_scope(
    value: GoalNativeLaneEvidenceSnapshotV2, authority: Mapping[str, object],
) -> dict[str, object]:
    """Account for exact issued initial effects; never erase unknown touches.

    Blob/currentness identities remain in the full provider/direction binding.
    Only after the provider verifies every exact Issue effect across the full
    introduction→HEAD graph may these versions use the preimplementation blob
    anchor for semantic comparison. Blob membership alone never issues proof.
    """
    value = require_qualified_native_lane_evidence(value)
    result = dict(authority)
    for gate in value.gate_observations:
        body = gate.evaluator_input.to_wire()
        request = cast(dict[str, object], body["request"])
        pub = cast(dict[str, object], request["implementation_publication"])
        if authority["path"] != pub["governing_issue_path"]:
            continue
        if (authority["tag"] != pub["governing_issue_tag"] or authority["owner"] != pub["owner_execution_id"]
            or authority["status"] != pub["status"] or authority["scope_digest"] != pub["scope_digest"]
            or list(cast(tuple[str, ...], authority["scope"])) != pub["scope"]):
            raise ValueError("native_lane_gate_issue_authority_mismatch")
        verification = cast(dict[str, object], body["source_verification"])
        for event in cast(list[dict[str, object]], verification["history_effects"]):
            if authority["path"] in cast(list[str], event["changed_paths"]) and event["permitted_publication_ref"] is None:
                raise ValueError("native_lane_gate_issue_history_unqualified")
        blobs = {pub["governing_issue_blob_ref"]}
        blobs.update(item["blob_ref"] for item in cast(list[dict[str, object]], verification["authority_inventory"])
            if item["path"] == authority["path"] and item["role"] == "implementation-source-issue")
        blobs.update(p["governing_issue_blob_ref"] for p in
            cast(list[dict[str, object]], verification["authority_publications"])
            if p["governing_issue_path"] == authority["path"])
        if authority["blob_oid"] not in blobs:
            raise ValueError("native_lane_gate_issue_version_unqualified")
        result["blob_oid"] = pub["governing_issue_blob_ref"]
    return result


def require_native_lane_gate_issue_effect(
    value: GoalNativeLaneEvidenceSnapshotV2, *, issue_path: str,
    parent_ref: str, commit_ref: str, before_blob_ref: str, after_blob_ref: str,
) -> str:
    """Qualify one actual repository edge, never a content-only occurrence.

    The concrete provider enumerates the complete introduction→HEAD graph and
    restores each edge. Issued evaluator records authorize only their exact
    publication commit/parent and pre/post Issue bindings. Identical content
    occurring at an earlier or later ungoverned edge is not authorized.
    """
    value = require_qualified_native_lane_evidence(value)
    for gate in value.gate_observations:
        body = gate.evaluator_input.to_wire()
        request = cast(dict[str, object], body["request"])
        impl = cast(dict[str, object], request["implementation_publication"])
        if issue_path != impl["governing_issue_path"]:
            continue
        verified = cast(dict[str, object], body["source_verification"])
        inventory = cast(list[dict[str, object]], verified["authority_inventory"])
        if (parent_ref, commit_ref) == (impl["repository_parent_ref"], impl["repository_revision_ref"]):
            after = next(item for item in inventory if item["path"] == issue_path and item["role"] == "implementation-source-issue")
            if (issue_path in cast(list[str], impl["changed_paths"])
                and before_blob_ref == impl["governing_issue_blob_ref"] and after_blob_ref == after["blob_ref"]):
                return cast(str, impl["repository_commit_receipt_ref"])
        for pub in cast(list[dict[str, object]], verified["authority_publications"]):
            if pub["governing_issue_path"] != issue_path or pub["repository_revision_ref"] != commit_ref:
                continue
            post = next(item for item in inventory if item["path"] == issue_path
                and item["source_revision_ref"] == commit_ref and item["role"] in {"request-issue", "proof-issue", "review-issue"})
            role = cast(str, post["role"]).removesuffix("-issue")
            before = next(item for item in inventory if item["path"] == issue_path and item["role"] == role + "-parent-issue")
            if (parent_ref == before["source_revision_ref"] and before_blob_ref == before["blob_ref"]
                and after_blob_ref == post["blob_ref"] == pub["governing_issue_blob_ref"]):
                return cast(str, pub["publication_ref"])
    raise ValueError("native_lane_gate_issue_effect_unqualified")


def observe_native_lane_gate_phases(
    *, document: GoalPhaseNativeDocumentV4, evidence: GoalNativeLaneEvidenceSnapshotV2,
    lane_key: str, source_revision_ref: str,
) -> dict[GoalPhaseCoordinate, GoalLanePhase]:
    """Neutral observed views; no authored carrier or lifecycle is rewritten."""
    evidence = require_native_lane_evidence_for_document(evidence, document=document, lane_key=lane_key)
    if evidence.source_revision_ref != source_revision_ref:
        raise ValueError("native_lane_evidence_epoch_mismatch")
    views: dict[GoalPhaseCoordinate, GoalLanePhase] = {}
    for record in evidence.gate_observations:
        evaluation = record.evaluation.to_wire()
        raw_coordinate = cast(dict[str, str], evaluation["coordinate"])
        c = GoalPhaseCoordinate(**raw_coordinate)
        phase = next(p for p in document.operational_bundle.phases if p.coordinate == c)
        raw = cast(dict[str, object], evaluation["gate_observation"])
        observation = GoalLanePhaseGateObservation(
            observation_ref=cast(str, raw["observation_ref"]), gate_digest=cast(str, raw["gate_digest"]),
            outcome=GoalLanePhaseGateOutcome(cast(str, raw["outcome"])), evaluator_ref=cast(str, raw["evaluator_ref"]),
            evidence_refs=tuple(cast(list[str], raw["evidence_refs"])),
            source_revision_refs=tuple(cast(list[str], raw["source_revision_refs"])),
            evaluated_at=cast(str, raw["evaluated_at"]), currentness_ref=cast(str, raw["currentness_ref"]),
        )
        views[c] = replace(phase, gate_observations=(observation,))
    return views


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be exact nonempty text")
    return value


def _json_object(value: object) -> None:
    if type(value) is not dict:
        raise TypeError("authority binding must be an exact JSON object")
    def visit(item: object) -> None:
        if type(item) is dict:
            for key, child in cast(dict[object, object], item).items():
                if type(key) is not str:
                    raise TypeError("authority field must be text")
                visit(child)
        elif type(item) is list:
            for child in cast(list[object], item):
                visit(child)
        elif item is not None and type(item) not in {str, bool, int}:
            raise TypeError("authority value must be canonical JSON")
    visit(cast(dict[str, object], value))
