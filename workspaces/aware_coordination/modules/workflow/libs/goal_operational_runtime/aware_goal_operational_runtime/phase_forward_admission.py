"""Pure existing-definition admission. Plans are not publication authority.

Reuse native admission's Work identity law. Source/Issue authentication and
repository effects belong to bounded concrete provider entrances.
"""
# pyright: reportPrivateUsage=false
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import cast

from .identity import fingerprint, required_token
from .phase_contracts import (
    GoalLanePhase, GoalLanePhaseState, GoalLanePhaseWork,
    GoalLanePhaseWorkDisposition, GoalLanePhaseWorkRole, GoalPhaseCoordinate,
)
from .phase_document import (
    GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3,
    decode_goal_phase_native_document, encode_goal_phase_native_document,
)
from .phase_native_admission import _coordinate_wire, _derive_work_refs
from .phase_frontier import goal_phase_dependency_digest
from .phase_dependency_endpoint_context import (
    ABSENT_SCOPE_PROFILE, SCOPE_PROFILE, decode_dependency_endpoint_context, dependency_endpoint_scope_profile,
)
from .phase_migrated_definition_qualification import (
    decode_goal_phase_migrated_definition_qualification_publication_receipt,
    encode_goal_phase_migrated_definition_qualification_publication_receipt,
)

REQUEST_SCHEMA = "aware.goal.phase-operational-admission-request.v2"
PLAN_SCHEMA = "aware.goal.phase-operational-admission-plan.v2"
Document = GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_INSTANT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")


def _text(value: object, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} requires exact text")
    token = required_token(value, name)
    if token != value:
        raise ValueError(f"{name} requires canonical text")
    return token


def checked_forward_document(document: Document) -> Document:
    """Reconstruct nested invariants; do not trust frozen-object convention."""
    if type(document) not in {GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3}:
        raise ValueError("forward_admission_carrier_unsupported")
    restored = decode_goal_phase_native_document(encode_goal_phase_native_document(document))
    if restored != document:
        raise ValueError("forward_admission_document_not_canonical")
    return cast(Document, restored)


@dataclass(frozen=True, slots=True)
class GoalPhaseOperationalAdmissionRequestV2:
    coordinate: GoalPhaseCoordinate
    expected_document_ref: str
    expected_source_revision_ref: str
    expected_definition_ref: str
    expected_gate_digest: str
    initial_state: GoalLanePhaseState
    issue_ref: str
    work_role: GoalLanePhaseWorkRole
    admitted_at: str
    evidence_refs: tuple[str, ...]
    idempotency_key: str
    admission_profile: str = "existing_definition_v1"
    schema_id: str = REQUEST_SCHEMA
    request_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseOperationalAdmissionRequestV2:
            raise TypeError("forward request requires exact type")
        if self.schema_id != REQUEST_SCHEMA or self.admission_profile != "existing_definition_v1":
            raise ValueError("forward_admission_profile_unsupported")
        if type(self.coordinate) is not GoalPhaseCoordinate:
            raise TypeError("coordinate requires exact type")
        self.coordinate.__post_init__()
        for name, value in (("expected_document_ref", self.expected_document_ref),
            ("expected_source_revision_ref", self.expected_source_revision_ref),
            ("expected_definition_ref", self.expected_definition_ref),
            ("expected_gate_digest", self.expected_gate_digest), ("issue_ref", self.issue_ref),
            ("admitted_at", self.admitted_at), ("idempotency_key", self.idempotency_key)):
            _ = _text(value, name)
        for value, prefix in ((self.expected_document_ref, "goal-phase-document:"),
                             (self.expected_definition_ref, "goal-phase-definition:")):
            if not value.startswith(prefix) or not _SHA.fullmatch(value[len(prefix):]):
                raise ValueError("forward_admission_reference_invalid")
        if not _SHA.fullmatch(self.expected_gate_digest):
            raise ValueError("forward_admission_gate_digest_invalid")
        if type(self.initial_state) is not GoalLanePhaseState or self.initial_state not in {
            GoalLanePhaseState.PLANNED, GoalLanePhaseState.ACTIVE,
        }:
            raise ValueError("forward_admission_initial_state_unsupported")
        if type(self.work_role) is not GoalLanePhaseWorkRole:
            raise TypeError("work_role requires exact enum")
        if not _INSTANT.fullmatch(self.admitted_at):
            raise ValueError("forward_admission_time_invalid")
        try:
            _ = datetime.fromisoformat(self.admitted_at)
        except ValueError as error:
            raise ValueError("forward_admission_time_invalid") from error
        if type(self.evidence_refs) is not tuple or not self.evidence_refs:
            raise ValueError("forward_admission_evidence_required")
        if any(type(value) is not str for value in self.evidence_refs):
            raise TypeError("evidence requires exact text")
        if self.evidence_refs != tuple(sorted(set(self.evidence_refs))):
            raise ValueError("forward_admission_evidence_not_canonical")
        for value in self.evidence_refs:
            _ = _text(value, "evidence_ref")
        object.__setattr__(self, "request_ref", "goal-phase-operational-admission-request:" + fingerprint(self.to_wire(include_ref=False)))

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": self.schema_id, "admission_profile": self.admission_profile,
            "coordinate": _coordinate_wire(self.coordinate),
            "expected_document_ref": self.expected_document_ref,
            "expected_source_revision_ref": self.expected_source_revision_ref,
            "expected_definition_ref": self.expected_definition_ref,
            "expected_gate_digest": self.expected_gate_digest,
            "initial_state": self.initial_state.value, "issue_ref": self.issue_ref,
            "work_role": self.work_role.value, "admitted_at": self.admitted_at,
            "evidence_refs": list(self.evidence_refs), "idempotency_key": self.idempotency_key,
        }
        if include_ref:
            body["request_ref"] = self.request_ref
        return body


def decode_forward_admission_request(raw: object) -> GoalPhaseOperationalAdmissionRequestV2:
    if type(raw) is not dict:
        raise TypeError("request requires exact JSON object")
    values = cast(dict[str, object], raw)
    keys = {"schema_id", "admission_profile", "coordinate", "expected_document_ref",
            "expected_source_revision_ref", "expected_definition_ref", "expected_gate_digest",
            "initial_state", "issue_ref", "work_role", "admitted_at", "evidence_refs",
            "idempotency_key", "request_ref"}
    if set(values) != keys:
        raise ValueError("forward_admission_request_fields_invalid")
    coord = values["coordinate"]
    if type(coord) is not dict:
        raise ValueError("forward_admission_coordinate_invalid")
    coordinate = cast(dict[str, object], coord)
    if set(coordinate) != {"goal_tag", "lane_key", "phase_key"}:
        raise ValueError("forward_admission_coordinate_invalid")
    evidence = values["evidence_refs"]
    if type(evidence) is not list:
        raise TypeError("evidence requires exact JSON array")
    result = GoalPhaseOperationalAdmissionRequestV2(
        coordinate=GoalPhaseCoordinate(*(_text(coordinate[k], k) for k in ("goal_tag", "lane_key", "phase_key"))),
        expected_document_ref=_text(values["expected_document_ref"], "document"),
        expected_source_revision_ref=_text(values["expected_source_revision_ref"], "source"),
        expected_definition_ref=_text(values["expected_definition_ref"], "definition"),
        expected_gate_digest=_text(values["expected_gate_digest"], "gate"),
        initial_state=GoalLanePhaseState(_text(values["initial_state"], "state")),
        issue_ref=_text(values["issue_ref"], "issue"),
        work_role=GoalLanePhaseWorkRole(_text(values["work_role"], "role")),
        admitted_at=_text(values["admitted_at"], "time"),
        evidence_refs=tuple(_text(v, "evidence") for v in cast(list[object], evidence)),
        idempotency_key=_text(values["idempotency_key"], "idempotency"),
        admission_profile=_text(values["admission_profile"], "profile"),
        schema_id=_text(values["schema_id"], "schema"),
    )
    if result.to_wire() != values:
        raise ValueError("forward_admission_request_reference_invalid")
    return result


def _build(document: Document, request: GoalPhaseOperationalAdmissionRequestV2) -> tuple[Document, GoalLanePhase]:
    # Validate the existing identity before reconstruction. Re-running a
    # constructor hook on the issued request would repair a mutated ref and
    # erase the mutation before the provider's registered fingerprint check.
    if type(request) is not GoalPhaseOperationalAdmissionRequestV2:
        raise TypeError("forward request requires exact type")
    request = decode_forward_admission_request(request.to_wire())
    document = checked_forward_document(document)
    if document.document_ref != request.expected_document_ref or document.goal_tag != request.coordinate.goal_tag:
        raise ValueError("forward_admission_document_mismatch")
    definitions = tuple(d for d in document.definitions if d.coordinate == request.coordinate)
    if len(definitions) != 1:
        raise ValueError("forward_admission_definition_unavailable")
    definition = definitions[0]
    if definition.title is None or definition.intent is None:
        raise ValueError("definition_incomplete")
    if definition.definition_ref != request.expected_definition_ref or definition.gate.gate_digest != request.expected_gate_digest:
        raise ValueError("forward_admission_definition_mismatch")
    if any(p.coordinate == request.coordinate for p in document.operational_bundle.phases):
        raise ValueError("forward_admission_already_operational")
    if any(w.disposition is GoalLanePhaseWorkDisposition.CURRENT
           for p in document.operational_bundle.phases if p.coordinate.lane_key == request.coordinate.lane_key
           for w in p.work_associations):
        raise ValueError("forward_admission_lane_work_already_selected")
    association, receipt = _derive_work_refs(coordinate=request.coordinate,
        issue_ref=request.issue_ref, role=request.work_role, admitted_at=request.admitted_at,
        evidence_refs=request.evidence_refs)
    work = GoalLanePhaseWork(association_ref=association, receipt_ref=receipt,
        issue_ref=request.issue_ref, role=request.work_role,
        disposition=GoalLanePhaseWorkDisposition.CURRENT, admitted_at=request.admitted_at)
    phase = GoalLanePhase(coordinate=definition.coordinate, ordinal=definition.ordinal,
        title=definition.title, intent=definition.intent, state=request.initial_state,
        gate=definition.gate, work_associations=(work,))
    after = replace(document, operational_bundle=replace(document.operational_bundle,
        phases=document.operational_bundle.phases + (phase,)))
    return checked_forward_document(after), phase


@dataclass(frozen=True, slots=True)
class GoalPhaseOperationalAdmissionPlanV2:
    before_document: Document
    after_document: Document
    request: GoalPhaseOperationalAdmissionRequestV2
    phase: GoalLanePhase
    semantic_intent_ref: str = field(init=False)
    schema_id: str = PLAN_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseOperationalAdmissionPlanV2 or self.schema_id != PLAN_SCHEMA:
            raise ValueError("forward_admission_plan_profile_invalid")
        if type(self.request) is not GoalPhaseOperationalAdmissionRequestV2:
            raise TypeError("forward request requires exact type")
        after, phase = _build(self.before_document, self.request)
        if checked_forward_document(self.after_document) != after or self.phase != phase:
            raise ValueError("forward_admission_plan_not_canonical")
        object.__setattr__(self, "semantic_intent_ref", "goal-phase-operational-admission-plan:" + fingerprint({
            "schema_id": self.schema_id, "request": self.request.to_wire(),
            "before_document_ref": self.before_document.document_ref,
            "after_document_ref": self.after_document.document_ref,
        }))


def plan_existing_definition_admission(*, document: Document,
                                      request: GoalPhaseOperationalAdmissionRequestV2) -> GoalPhaseOperationalAdmissionPlanV2:
    if type(request) is not GoalPhaseOperationalAdmissionRequestV2:
        raise TypeError("forward request requires exact type")
    # Detach all caller-owned nested data before deriving a postimage.
    request = decode_forward_admission_request(request.to_wire())
    document = checked_forward_document(document)
    after, phase = _build(document, request)
    return GoalPhaseOperationalAdmissionPlanV2(document, after, request, phase)


def forward_plan_wire(plan: GoalPhaseOperationalAdmissionPlanV2) -> dict[str, object]:
    original = plan.semantic_intent_ref
    plan.__post_init__()
    if original != plan.semantic_intent_ref:
        raise ValueError("forward_admission_plan_mutated")
    return {"schema_id": plan.schema_id, "semantic_intent_ref": plan.semantic_intent_ref,
        "request": plan.request.to_wire(), "before_document_ref": plan.before_document.document_ref,
        "after_document_ref": plan.after_document.document_ref,
        "effect_profile": "plan_only_non_authorizing"}


def document_wire(document: Document) -> dict[str, object]:
    return cast(dict[str, object], json.loads(encode_goal_phase_native_document(checked_forward_document(document))))


PUBLICATION_SCHEMA = "aware.goal.phase-operational-admission-publication.v2"
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_VERIFICATION_FIELDS = {
    "schema_id", "plan", "goal_path", "publication_issue_path", "publication_issue",
    "selected_issue", "source_head", "observed_head", "before_sha256", "before_blob",
    "scope_profile", "dependency_contexts", "protected_paths", "goal_paths", "issue_paths",
    "protocol_sha256",
}
_PUBLICATION_FIELDS = {
    "schema_id", "provider_profile", "scope_profile", "source_verification",
    "before_document", "after_document", "before_phase", "after_phase", "semantic_intent_ref",
    "source_verification_ref", "after_sha256", "after_blob", "protocol_manifest_path",
    "repository_parent_ref", "repository_commit_ref", "repository_commit_receipt_ref",
    "repository_ref", "repository_request_fingerprint", "commit_message",
}


def canonical_repository_path(value: object) -> str:
    path = _text(value, "repository path")
    if ":" in path or "\\" in path or any(p in {"", ".", ".."} for p in path.split("/")):
        raise ValueError("forward_publication_path_invalid")
    return path


def _object(value: object, name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{name} requires exact JSON object")
    return cast(dict[str, object], value)


def _canonical_paths(value: object, name: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise TypeError(f"{name} requires exact JSON array")
    paths = tuple(canonical_repository_path(p) for p in cast(list[object], value))
    if not paths or paths != tuple(sorted(set(paths))):
        raise ValueError("forward_publication_path_set_invalid")
    return paths


def _receipt_issue(value: object) -> dict[str, object]:
    issue = _object(value, "Issue")
    if set(issue) != {"path", "tag", "blob_oid", "owner", "status", "scope", "scope_digest"}:
        raise ValueError("forward_publication_issue_fields_invalid")
    _ = canonical_repository_path(issue["path"])
    for key in ("tag", "blob_oid", "owner", "status", "scope_digest"):
        _ = _text(issue[key], key)
    if issue["status"] != "in_progress" or not _OID.fullmatch(cast(str, issue["blob_oid"])):
        raise ValueError("forward_publication_issue_authority_invalid")
    if type(issue["scope"]) is not list:
        raise TypeError("Issue scope requires exact JSON array")
    scope = tuple(canonical_repository_path(p) for p in cast(list[object], issue["scope"]))
    if not scope or len(set(scope)) != len(scope) or issue["scope_digest"] != fingerprint({"ownership_scope": list(scope)}):
        raise ValueError("forward_publication_issue_scope_invalid")
    return issue


def decode_pending_projection_authority(raw: object) -> dict[str, object]:
    """Strict integrity-only transport; committed M13 issuance is provider verified."""
    body = _object(raw, "pending projection authority")
    keys = {"schema_id", "profile", "goal_path", "publication_issue_path",
        "proposal_publication_path", "acceptance_publication_path", "publication_receipt",
        "before_goal_sha256", "after_goal_sha256", "authority_paths", "authority_issue_paths", "authority_ref"}
    if set(body) != keys or body["schema_id"] != "aware.goal.pending-projection-authority.v1" or body["profile"] != "migrated_definition_publication_v1":
        raise ValueError("forward_pending_projection_fields_invalid")
    for key in ("goal_path", "publication_issue_path", "proposal_publication_path", "acceptance_publication_path"):
        _ = canonical_repository_path(body[key])
    for key in ("before_goal_sha256", "after_goal_sha256"):
        if not _SHA.fullmatch(_text(body[key], key)):
            raise ValueError("forward_pending_projection_digest_invalid")
    protected = _canonical_paths(body["authority_paths"], "authority paths")
    issues = _canonical_paths(body["authority_issue_paths"], "authority Issue paths")
    if (not set(issues).issubset(protected) or body["publication_issue_path"] not in issues
        or not {cast(str, body["proposal_publication_path"]), cast(str, body["acceptance_publication_path"])}.issubset(protected)
        or body["goal_path"] in protected):
        raise ValueError("forward_pending_projection_protected_set_invalid")
    wire = _object(body["publication_receipt"], "M13 receipt")
    receipt = decode_goal_phase_migrated_definition_qualification_publication_receipt(
        json.dumps(wire, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    if (json.loads(encode_goal_phase_migrated_definition_qualification_publication_receipt(receipt)) != wire
        or receipt.changed_path != body["goal_path"]
        or receipt.repository_commit_receipt_ref != "repository-commit:" + receipt.repository_commit_ref
        or body["authority_ref"] != "goal-pending-projection-authority:" + fingerprint({k: v for k, v in body.items() if k != "authority_ref"})):
        raise ValueError("forward_pending_projection_binding_invalid")
    return cast(dict[str, object], json.loads(json.dumps(body)))


def forward_publication_intent(source_wire: dict[str, object],
    pending_projection_authority: dict[str, object] | None = None) -> str:
    """Stable source/effect binding; unrelated return HEAD is not intent."""
    if type(source_wire) is not dict or set(source_wire) != _VERIFICATION_FIELDS:
        raise ValueError("forward_publication_verification_fields_invalid")
    body: dict[str, object] = {
        "schema_id": PUBLICATION_SCHEMA,
        "source_verification": {k: v for k, v in source_wire.items() if k != "observed_head"},
    }
    if pending_projection_authority is not None:
        body["provider_profile"] = "git_repository_cas_pending_projection_v1"
        body["pending_projection_authority"] = decode_pending_projection_authority(pending_projection_authority)
    return "goal-phase-operational-admission-publication-intent:" + fingerprint(body)


def _validate_incident_records(before: Document, source: dict[str, object]) -> None:
    """Authority-free completeness/profile laws; actual sources are provider verified."""
    request = decode_forward_admission_request(_object(source["plan"], "plan")["request"])
    wire = document_wire(before)
    bundle = _object(wire["operational_bundle"], "bundle")
    declarations = {cast(str, d["dependency_key"]): d for d in cast(list[dict[str, object]], bundle["dependencies"])}
    expected: list[tuple[dict[str, object], str, bool]] = [
        (declarations[d.dependency_key], goal_phase_dependency_digest(d), False)
        for d in sorted(before.operational_bundle.dependencies, key=lambda value: value.dependency_key)
        if request.coordinate in (d.dependent, d.prerequisite)
    ]
    for declaration in cast(list[dict[str, object]], wire["unresolved_dependencies"]):
        if _coordinate_wire(request.coordinate) in (declaration["dependent"], declaration["prerequisite"]):
            expected.append((declaration, fingerprint(declaration), True))
    records = cast(list[object], source["dependency_contexts"])
    if len(records) != len(expected):
        raise ValueError("forward_publication_incident_set_incomplete")
    for raw, (declaration, digest, unresolved) in zip(records, expected):
        record = _object(raw, "dependency record")
        keys: set[str] = {"declaration", "declaration_digest", "evaluation_profile"}
        if not unresolved:
            keys.update({"dependent", "prerequisite"})
        if (set(record) != keys or record["declaration"] != declaration or record["declaration_digest"] != digest
            or record["evaluation_profile"] != ("unresolved_non_authorizing" if unresolved else "source_context_only_non_authorizing")):
            raise ValueError("forward_publication_incident_binding_invalid")
        if unresolved:
            continue
        for role in ("dependent", "prerequisite"):
            endpoint = _object(record[role], "endpoint")
            if set(endpoint) != {"context", "goal_path", "goal_sha256", "goal_blob_oid"}:
                raise ValueError("forward_publication_endpoint_fields_invalid")
            _ = canonical_repository_path(endpoint["goal_path"])
            if endpoint["goal_path"] not in cast(list[str], source["goal_paths"]):
                raise ValueError("forward_publication_endpoint_path_unprotected")
            if not _SHA.fullmatch(_text(endpoint["goal_sha256"], "Goal digest")) or not _OID.fullmatch(_text(endpoint["goal_blob_oid"], "Goal blob")):
                raise ValueError("forward_publication_endpoint_source_invalid")
            context = decode_dependency_endpoint_context(endpoint["context"])
            if (context["coordinate"] != declaration[role]
                or context["source_revision_ref"] != source["source_head"]):
                raise ValueError("forward_publication_endpoint_context_invalid")
            coordinate = _object(context["coordinate"], "endpoint coordinate")
            if (context["scope_profile"] == ABSENT_SCOPE_PROFILE
                and (coordinate["goal_tag"], coordinate["lane_key"]) == (request.coordinate.goal_tag, request.coordinate.lane_key)):
                raise ValueError("forward_publication_selected_lane_authority_absent")
            if {cast(str, issue["path"]) for issue in cast(list[dict[str, object]], context["lane_issue_context"])} - set(cast(list[str], source["issue_paths"])):
                raise ValueError("forward_publication_endpoint_issue_unprotected")
            definition = _object(context["definition"], "endpoint definition")
            if definition.get("coordinate") != declaration[role]:
                raise ValueError("forward_publication_endpoint_coordinate_invalid")
            if role == "prerequisite" and _object(definition.get("gate"), "Gate").get("gate_digest") != declaration["required_gate_digest"]:
                raise ValueError("forward_publication_endpoint_gate_invalid")
    if source["scope_profile"] != dependency_endpoint_scope_profile(tuple(cast(list[dict[str, object]], records))):
        raise ValueError("forward_publication_endpoint_scope_profile_invalid")


def _validate_publication_body(body: dict[str, object]) -> None:
    pending = body.get("provider_profile") == "git_repository_cas_pending_projection_v1" if type(body) is dict else False
    if type(body) is not dict or set(body) != _PUBLICATION_FIELDS | ({"pending_projection_authority"} if pending else set()):
        raise ValueError("forward_publication_receipt_fields_invalid")
    if (body["schema_id"] != PUBLICATION_SCHEMA or body["provider_profile"] not in {"git_repository_cas_v1", "git_repository_cas_pending_projection_v1"}
        or body["scope_profile"] not in {SCOPE_PROFILE, ABSENT_SCOPE_PROFILE}):
        raise ValueError("forward_publication_receipt_profile_invalid")
    source = _object(body["source_verification"], "source verification")
    if (set(source) != _VERIFICATION_FIELDS
        or source["schema_id"] != "aware.goal.git-forward-admission-verification.v2"
        or source["scope_profile"] != body["scope_profile"]):
        raise ValueError("forward_publication_verification_fields_invalid")
    raw_plan = _object(source["plan"], "plan")
    request = decode_forward_admission_request(raw_plan.get("request"))
    before_wire = _object(body["before_document"], "before document")
    after_wire = _object(body["after_document"], "after document")
    before = checked_forward_document(cast(Document, decode_goal_phase_native_document(json.dumps(before_wire).encode("utf-8"))))
    after = checked_forward_document(cast(Document, decode_goal_phase_native_document(json.dumps(after_wire).encode("utf-8"))))
    if document_wire(before) != before_wire or document_wire(after) != after_wire:
        raise ValueError("forward_publication_document_not_canonical")
    plan = plan_existing_definition_admission(document=before, request=request)
    if forward_plan_wire(plan) != raw_plan or after != plan.after_document:
        raise ValueError("forward_publication_delta_not_canonical")
    phases = cast(list[dict[str, object]], _object(after_wire["operational_bundle"], "bundle")["phases"])
    if body["before_phase"] is not None or body["after_phase"] != phases[-1]:
        raise ValueError("forward_publication_phase_binding_invalid")
    publication_issue = _receipt_issue(source["publication_issue"])
    selected_issue = _receipt_issue(source["selected_issue"])
    goal_path = canonical_repository_path(source["goal_path"])
    pending_authority = decode_pending_projection_authority(body["pending_projection_authority"]) if pending else None
    if pending_authority is not None:
        pending_receipt = _object(pending_authority["publication_receipt"], "M13 receipt")
        if (pending_authority["goal_path"] != goal_path
            or pending_authority["after_goal_sha256"] != source["before_sha256"]
            or pending_receipt["after_document_ref"] != before.document_ref):
            raise ValueError("forward_pending_projection_source_mismatch")
    manifest = canonical_repository_path(body["protocol_manifest_path"])
    if (publication_issue["path"] != source["publication_issue_path"]
        or goal_path not in cast(list[str], publication_issue["scope"])
        or selected_issue["path"] != request.issue_ref):
        raise ValueError("forward_publication_issue_binding_invalid")
    protected = _canonical_paths(source["protected_paths"], "protected paths")
    goals = _canonical_paths(source["goal_paths"], "Goal paths")
    issues = _canonical_paths(source["issue_paths"], "Issue paths")
    if (set(protected) != {manifest, *goals, *issues} or goal_path not in goals
        or {cast(str, publication_issue["path"]), request.issue_ref} - set(issues)):
        raise ValueError("forward_publication_protected_set_invalid")
    if type(source["dependency_contexts"]) is not list:
        raise TypeError("dependency contexts require exact JSON array")
    _validate_incident_records(before, source)
    for value in (source["source_head"], source["observed_head"], source["before_blob"],
                  body["after_blob"], body["repository_parent_ref"], body["repository_commit_ref"]):
        if not _OID.fullmatch(_text(value, "Git identity")):
            raise ValueError("forward_publication_git_identity_invalid")
    for value in (source["before_sha256"], source["protocol_sha256"], body["after_sha256"],
                  body["repository_request_fingerprint"]):
        if not _SHA.fullmatch(_text(value, "digest")):
            raise ValueError("forward_publication_digest_invalid")
    if (source["source_head"] != request.expected_source_revision_ref
        or source["observed_head"] != body["repository_parent_ref"]
        or body["repository_commit_receipt_ref"] != "repository-commit:" + cast(str, body["repository_commit_ref"])
        or body["semantic_intent_ref"] != forward_publication_intent(source, pending_authority)
        or body["source_verification_ref"] != "goal-phase-forward-admission-source:" + fingerprint(source)):
        raise ValueError("forward_publication_repository_binding_invalid")
    repository_ref = _text(body["repository_ref"], "repository ref")
    if not repository_ref.startswith("refs/heads/"):
        raise ValueError("forward_publication_repository_ref_invalid")
    message = body["commit_message"]
    if type(message) is not str or not message or message.strip() != message or any(ord(c) < 32 for c in message):
        raise ValueError("forward_publication_commit_message_invalid")


@dataclass(frozen=True, slots=True)
class GoalPhaseOperationalAdmissionPublicationV2:
    """Integrity-only receipt. Concrete committed-effect verification is required."""
    body: dict[str, object]
    receipt_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseOperationalAdmissionPublicationV2:
            raise TypeError("forward publication receipt requires exact type")
        _validate_publication_body(self.body)
        body = cast(dict[str, object], json.loads(json.dumps(self.body)))
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "receipt_ref", "goal-phase-operational-admission-publication:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        _validate_publication_body(self.body)
        if self.receipt_ref != "goal-phase-operational-admission-publication:" + fingerprint(self.body):
            raise ValueError("forward_publication_receipt_digest_invalid")
        return cast(dict[str, object], json.loads(json.dumps({**self.body, "receipt_ref": self.receipt_ref})))


def decode_forward_admission_publication(raw: object) -> GoalPhaseOperationalAdmissionPublicationV2:
    wire = _object(raw, "publication receipt")
    pending = wire.get("provider_profile") == "git_repository_cas_pending_projection_v1"
    if set(wire) != _PUBLICATION_FIELDS | {"receipt_ref"} | ({"pending_projection_authority"} if pending else set()):
        raise ValueError("forward_publication_receipt_fields_invalid")
    receipt = GoalPhaseOperationalAdmissionPublicationV2({k: v for k, v in wire.items() if k != "receipt_ref"})
    if receipt.to_wire() != wire:
        raise ValueError("forward_publication_receipt_digest_invalid")
    return receipt


_RECONCILIATION_FIELDS = {"schema_id", "effect_profile", "publication_receipt", "observed_head", "governance_issue",
    "index_blob_oid", "worktree_sha256", "disposition", "dry_run", "reason_codes"}


def _validate_reconciliation_body(body: dict[str, object]) -> None:
    if type(body) is not dict or set(body) != _RECONCILIATION_FIELDS:
        raise ValueError("forward_reconciliation_fields_invalid")
    if (body["schema_id"] != "aware.goal.phase-operational-admission-projection-reconciliation.v2"
        or body["effect_profile"] != "repository_only_no_projection_write_v1"):
        raise ValueError("forward_reconciliation_profile_invalid")
    receipt = decode_forward_admission_publication(body["publication_receipt"])
    issue = _receipt_issue(body["governance_issue"])
    source = _object(receipt.body["source_verification"], "source")
    preimages = {cast(str, source["before_sha256"])}
    if "pending_projection_authority" in receipt.body:
        pending = decode_pending_projection_authority(receipt.body["pending_projection_authority"])
        preimages.add(cast(str, pending["before_goal_sha256"]))
    if source["goal_path"] not in cast(list[str], issue["scope"]):
        raise ValueError("forward_reconciliation_issue_scope_invalid")
    for key in ("observed_head", "index_blob_oid"):
        if not _OID.fullmatch(_text(body[key], key)):
            raise ValueError("forward_reconciliation_git_identity_invalid")
    if not _SHA.fullmatch(_text(body["worktree_sha256"], "worktree digest")) or type(body["dry_run"]) is not bool:
        raise ValueError("forward_reconciliation_projection_invalid")
    if body["disposition"] not in {"current", "planned", "reconciliation_required"}:
        raise ValueError("forward_reconciliation_disposition_invalid")
    if type(body["reason_codes"]) is not list:
        raise TypeError("reconciliation reasons require exact JSON array")
    reasons = tuple(_text(v, "reason") for v in cast(list[object], body["reason_codes"]))
    if len(set(reasons)) != len(reasons):
        raise ValueError("forward_reconciliation_reasons_invalid")
    if body["index_blob_oid"] != receipt.body["after_blob"]:
        raise ValueError("forward_reconciliation_index_binding_invalid")
    if body["disposition"] == "current" and (reasons or body["worktree_sha256"] != receipt.body["after_sha256"]):
        raise ValueError("forward_reconciliation_current_binding_invalid")
    if body["disposition"] == "planned" and (not body["dry_run"] or reasons or body["worktree_sha256"] not in preimages):
        raise ValueError("forward_reconciliation_plan_binding_invalid")
    if body["disposition"] == "reconciliation_required" and (body["dry_run"]
        or reasons != ("forward_reconciliation_guarded_writer_unavailable",)
        or body["worktree_sha256"] not in preimages):
        raise ValueError("forward_reconciliation_required_binding_invalid")


@dataclass(frozen=True, slots=True)
class GoalPhaseForwardProjectionReconciliationV2:
    """Strict observation transport, not independently issued lasting authority."""
    body: dict[str, object]
    reconciliation_ref: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseForwardProjectionReconciliationV2:
            raise TypeError("forward reconciliation requires exact type")
        _validate_reconciliation_body(self.body)
        body = cast(dict[str, object], json.loads(json.dumps(self.body)))
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "reconciliation_ref", "goal-phase-forward-projection-reconciliation:" + fingerprint(body))

    def to_wire(self) -> dict[str, object]:
        _validate_reconciliation_body(self.body)
        if self.reconciliation_ref != "goal-phase-forward-projection-reconciliation:" + fingerprint(self.body):
            raise ValueError("forward_reconciliation_digest_invalid")
        return cast(dict[str, object], json.loads(json.dumps({**self.body, "reconciliation_ref": self.reconciliation_ref})))


def decode_forward_projection_reconciliation(raw: object) -> GoalPhaseForwardProjectionReconciliationV2:
    wire = _object(raw, "reconciliation receipt")
    if set(wire) != _RECONCILIATION_FIELDS | {"reconciliation_ref"}:
        raise ValueError("forward_reconciliation_fields_invalid")
    result = GoalPhaseForwardProjectionReconciliationV2({k: v for k, v in wire.items() if k != "reconciliation_ref"})
    if result.to_wire() != wire:
        raise ValueError("forward_reconciliation_digest_invalid")
    return result


def _unique_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("forward_receipt_duplicate_json_key")
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> object:
    raise ValueError("forward_receipt_json_constant_invalid")


def _receipt_bytes(wire: dict[str, object]) -> bytes:
    return json.dumps(wire, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def encode_forward_admission_publication(receipt: GoalPhaseOperationalAdmissionPublicationV2) -> bytes:
    if type(receipt) is not GoalPhaseOperationalAdmissionPublicationV2:
        raise TypeError("forward publication receipt requires exact type")
    return _receipt_bytes(receipt.to_wire())


def decode_forward_admission_publication_bytes(payload: bytes) -> GoalPhaseOperationalAdmissionPublicationV2:
    if type(payload) is not bytes:
        raise TypeError("forward receipt requires exact bytes")
    wire = cast(object, json.loads(payload, object_pairs_hook=_unique_json_pairs, parse_constant=_reject_json_constant))
    result = decode_forward_admission_publication(wire)
    if encode_forward_admission_publication(result) != payload:
        raise ValueError("forward_receipt_bytes_not_canonical")
    return result


def encode_forward_projection_reconciliation(receipt: GoalPhaseForwardProjectionReconciliationV2) -> bytes:
    if type(receipt) is not GoalPhaseForwardProjectionReconciliationV2:
        raise TypeError("forward reconciliation receipt requires exact type")
    return _receipt_bytes(receipt.to_wire())


def decode_forward_projection_reconciliation_bytes(payload: bytes) -> GoalPhaseForwardProjectionReconciliationV2:
    if type(payload) is not bytes:
        raise TypeError("forward receipt requires exact bytes")
    wire = cast(object, json.loads(payload, object_pairs_hook=_unique_json_pairs, parse_constant=_reject_json_constant))
    result = decode_forward_projection_reconciliation(wire)
    if encode_forward_projection_reconciliation(result) != payload:
        raise ValueError("forward_receipt_bytes_not_canonical")
    return result
