"""Opt-in, forward-looking V2 proof/review Gate contracts and pure reduction.

Constructing/decoding an authored artifact never issues authority. The reducer
consumes a concrete-provider witness, not resolver callbacks or caller states.
No repository, Issue, Phase, event or dispatch effect occurs here.
"""
from __future__ import annotations

import hashlib
import json
import re
import weakref
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Protocol, cast

from .phase_contracts import (
    GoalPhaseCoordinate, GoalLanePhaseWorkDisposition, GoalLanePhaseWorkRole,
    _utc_instant,  # pyright: ignore[reportPrivateUsage]
)
from .phase_native_lane_hold import exact_hold_wire
from .phase_document import GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4, encode_goal_phase_native_document
from .phase_native_scope_advancement import GoalGlobalDirectionAuthorityV1, GoalLaneDirectionAuthorityV1

class _DependencyScopeSource(Protocol):
    """Read-only projection interface, NOT a verifier or authority entrance.

    The concrete source verifier still constructs/qualifies exact dependency
    records. Pure scope projection must not depend on its consuming lane seal.
    """

    @property
    def document(self) -> GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4: ...

    @property
    def global_authority(self) -> GoalGlobalDirectionAuthorityV1: ...

    @property
    def lane_authorities(self) -> tuple[GoalLaneDirectionAuthorityV1, ...]: ...

PROFILE = "aware.goal.phase-gate-evaluator/runtime-checks-review-v2"
GATE_CONTRACT = "aware.goal.phase-gate.profile/runtime-checks-review-v2"
EVIDENCE_SCHEMA = "aware.goal.phase-gate-evidence/runtime-checks-review-v2"
INVARIANTS = tuple("invariant:aware.goal.runtime-checks-review." + k + "-v2" for k in
    ("package-tests", "runtime-canary", "static-checks"))
REQUEST = "aware.goal.runtime-checks-review-request.v2"
PROOF = "aware.goal.runtime-checks-proof.v2"
REVIEW = "aware.goal.runtime-checks-independent-verdict.v2"
PUBLICATION = "aware.goal.runtime-checks-authority-publication.v2"
VERIFICATION = "aware.goal.runtime-checks-source-verification.v2"
EVALUATION = "aware.goal.runtime-checks-evaluation.v2"
_REFS = {REQUEST: ("request_ref", "goal-runtime-checks-review-request:"),
    PROOF: ("proof_ref", "goal-runtime-checks-proof:"),
    REVIEW: ("review_ref", "goal-runtime-checks-independent-verdict:"),
    PUBLICATION: ("publication_ref", "goal-runtime-checks-authority-publication:")}
_FIELDS = {
    REQUEST: {"goal_path", "goal_tag", "coordinate", "source_document_ref", "source_revision_ref",
        "definition_ref", "gate_digest", "evaluator_profile", "implementation_publication", "source_scope",
        "source_scope_ref", "incoming_declarations", "requested_by_execution_id", "issued_at"},
    PROOF: {"request_ref", "request_publication_ref", "coordinate", "definition_ref", "gate_digest",
        "evaluator_profile", "source_scope_ref", "publisher_execution_id", "checks", "issued_at"},
    REVIEW: {"request_ref", "request_publication_ref", "proof_ref", "proof_publication_ref", "coordinate",
        "definition_ref", "gate_digest", "evaluator_profile", "source_scope_ref", "reviewed_changed_paths_ref",
        "reviewer_execution_id", "verdict", "issued_at"},
    PUBLICATION: {"artifact_schema_id", "artifact_ref", "artifact_path", "artifact_blob_ref",
        "repository_revision_ref", "repository_commit_receipt_ref", "governing_issue_path",
        "governing_issue_blob_ref", "owner_execution_id", "status", "scope", "scope_digest"},
}


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def strict_json(data: str | bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError("runtime_checks_duplicate_json_field")
            result[key] = value
        return result
    return cast(object, json.loads(data, object_pairs_hook=pairs))


def obj(value: object, names: set[str]) -> dict[str, object]:
    if type(value) is not dict or set(cast(dict[str, object], value)) != names:
        raise ValueError("runtime_checks_wire_fields")
    return cast(dict[str, object], value)


def text(value: object) -> str:
    if type(value) is not str or not value or value.strip() != value or any(c.isspace() for c in value) or "|" in value:
        raise ValueError("runtime_checks_wire_text")
    return value


def path(value: object) -> str:
    if type(value) is not str:
        raise ValueError("runtime_checks_wire_path")
    result = value
    if any(p in {"", ".", ".."} for p in result.split("/")) or ":" in result or "\\" in result or any(ord(c) < 32 for c in result):
        raise ValueError("runtime_checks_wire_path")
    return result


def sha(value: object) -> str:
    result = text(value)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", result):
        raise ValueError("runtime_checks_wire_sha256")
    return result


def strings(value: object, *, paths: bool = False, ordered: bool = True) -> list[str]:
    if type(value) is not list:
        raise ValueError("runtime_checks_wire_array")
    result = [(path(v) if paths else text(v)) for v in cast(list[object], value)]
    if ordered and result != sorted(set(result)):
        raise ValueError("runtime_checks_wire_order")
    return result


def coordinate(value: object) -> GoalPhaseCoordinate:
    v = obj(value, {"goal_tag", "lane_key", "phase_key"})
    return GoalPhaseCoordinate(*(text(v[k]) for k in ("goal_tag", "lane_key", "phase_key")))


def _file(value: object) -> None:
    v = obj(value, {"path", "blob_ref", "sha256"})
    _ = path(v["path"]), text(v["blob_ref"]), sha(v["sha256"])


def _count(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("runtime_checks_wire_integer")
    return value


def _body(value: dict[str, object]) -> None:
    schema = text(value.get("schema_id"))
    if schema not in _REFS:
        raise ValueError("runtime_checks_schema_unsupported")
    field, domain = _REFS[schema]
    _ = obj(value, _FIELDS[schema] | {"schema_id", field})
    body = {k: v for k, v in value.items() if k != field}
    if value[field] != domain + digest(body):
        raise ValueError("runtime_checks_artifact_digest")
    if schema == PUBLICATION:
        if value["artifact_schema_id"] not in {REQUEST, PROOF, REVIEW}:
            raise ValueError("runtime_checks_artifact_profile_unsupported")
        for k in _FIELDS[schema] - {"scope", "artifact_path", "governing_issue_path"}:
            _ = text(value[k])
        for k in ("artifact_path", "governing_issue_path"):
            _ = path(value[k])
        scope = strings(value["scope"], paths=True, ordered=False)
        if not scope or len(set(scope)) != len(scope) or value["scope_digest"] != digest({"ownership_scope": scope}):
            raise ValueError("runtime_checks_issue_scope")
        if value["status"] != "in_progress":
            raise ValueError("runtime_checks_issue_status")
        if value["repository_commit_receipt_ref"] != "repository-commit:" + text(value["repository_revision_ref"]):
            raise ValueError("runtime_checks_repository_receipt_binding")
        return
    _ = coordinate(value["coordinate"])
    _ = _utc_instant(text(value["issued_at"]), "issued_at")
    for k in _FIELDS[schema] - {"coordinate", "implementation_publication", "source_scope", "incoming_declarations", "checks", "goal_path"}:
        _ = text(value[k])
    _ = sha(value["gate_digest"])
    if value["evaluator_profile"] != PROFILE:
        raise ValueError("gate_evaluator_profile_unsupported")
    if schema == REQUEST:
        if coordinate(value["coordinate"]).goal_tag != value["goal_tag"]:
            raise ValueError("runtime_checks_goal_coordinate")
        _ = path(value["goal_path"])
        pub = obj(value["implementation_publication"], {"repository_revision_ref", "repository_parent_ref",
            "repository_commit_receipt_ref", "selected_work_binding", "governing_issue_path", "governing_issue_tag",
            "governing_issue_blob_ref", "owner_execution_id", "status", "scope", "scope_digest",
            "changed_paths", "changed_paths_ref"})
        for k in set(pub) - {"selected_work_binding", "scope", "changed_paths", "governing_issue_path"}:
            _ = text(pub[k])
        _ = path(pub["governing_issue_path"])
        if pub["repository_commit_receipt_ref"] != "repository-commit:" + text(pub["repository_revision_ref"]):
            raise ValueError("runtime_checks_repository_receipt_binding")
        work = obj(pub["selected_work_binding"], {"coordinate", "association_ref", "receipt_ref", "issue_ref", "role", "disposition"})
        _ = coordinate(work["coordinate"])
        for k in set(work) - {"coordinate"}:
            _ = text(work[k])
        if work["role"] != "implementation" or work["disposition"] != "current" or work["coordinate"] != value["coordinate"]:
            raise ValueError("implementation_work_issue_mismatch")
        paths = strings(pub["changed_paths"], paths=True)
        scope = strings(pub["scope"], paths=True, ordered=False)
        if not paths or not scope or len(set(scope)) != len(scope) or pub["status"] != "in_progress":
            raise ValueError("runtime_checks_issue_scope")
        if pub["changed_paths_ref"] != "goal-runtime-checks-changed-paths:" + digest(paths) or pub["scope_digest"] != digest({"ownership_scope": scope}):
            raise ValueError("runtime_checks_scope_digest")
        if type(value["source_scope"]) is not list or not value["source_scope"]:
            raise ValueError("runtime_checks_source_scope_absent")
        source = cast(list[object], value["source_scope"])
        for entry in source:
            _file(entry)
        names = [cast(dict[str, object], x)["path"] for x in source]
        if names != sorted(set(cast(list[str], names))) or value["source_scope_ref"] != "goal-runtime-checks-source-scope:" + digest(source):
            raise ValueError("runtime_checks_source_scope_digest")
        if type(value["incoming_declarations"]) is not list:
            raise ValueError("runtime_checks_wire_array")
        keys: list[str] = []
        for raw in cast(list[object], value["incoming_declarations"]):
            dep = obj(raw, {"dependency_key", "declaration_digest"})
            keys.append(text(dep["dependency_key"]))
            _ = sha(dep["declaration_digest"])
        if keys != sorted(set(keys)):
            raise ValueError("runtime_checks_dependency_order")
    elif schema == PROOF:
        if type(value["checks"]) is not list:
            raise ValueError("runtime_checks_wire_array")
        keys = []
        outputs: list[str] = []
        for raw in cast(list[object], value["checks"]):
            if type(raw) is not dict:
                raise ValueError("runtime_checks_wire_fields")
            key = text(cast(dict[str, object], raw).get("key"))
            extras = {"package-tests": {"passed_count", "failed_count", "skipped_count"},
                "runtime-canary": {"result"}, "static-checks": {"error_count", "warning_count"}}.get(key)
            if extras is None:
                raise ValueError("runtime_checks_check_unsupported")
            check = obj(cast(dict[str, object], raw), {"key", "source_scope_ref", "command_argv", "output", "exit_code"} | extras)
            _ = text(check["source_scope_ref"]), _count(check["exit_code"])
            argv = check["command_argv"]
            if type(argv) is not list or not argv or any(type(a) is not str or not a or "\x00" in a for a in cast(list[object], argv)):
                raise ValueError("runtime_checks_command_absent")
            _file(check["output"])
            outputs.append(path(cast(dict[str, object], check["output"])["path"]))
            for k in extras - {"result"}:
                _ = _count(check[k])
            if key == "runtime-canary" and check["result"] not in {"passed", "failed", "unavailable"}:
                raise ValueError("runtime_checks_canary_result")
            keys.append(key)
        if keys != ["package-tests", "runtime-canary", "static-checks"] or len(set(outputs)) != 3:
            raise ValueError("runtime_checks_check_set")
    elif value["verdict"] not in {"accepted", "rejected", "unavailable"}:
        raise ValueError("runtime_checks_review_verdict")


@dataclass(frozen=True, slots=True)
class RuntimeChecksArtifactV2:
    canonical_body: str

    def __post_init__(self) -> None:
        if type(self) is not RuntimeChecksArtifactV2 or type(self.canonical_body) is not str:
            raise ValueError("runtime_checks_artifact_type")
        value = strict_json(self.canonical_body)
        if type(value) is not dict or canonical_json(cast(dict[str, object], value)) != self.canonical_body:
            raise ValueError("runtime_checks_artifact_encoding")
        _body(cast(dict[str, object], value))

    def to_wire(self) -> dict[str, object]:
        return cast(dict[str, object], strict_json(self.canonical_body))


def decode_runtime_checks_artifact(payload: object) -> RuntimeChecksArtifactV2:
    if type(payload) is not dict:
        raise ValueError("runtime_checks_artifact_object")
    return RuntimeChecksArtifactV2(canonical_json(cast(dict[str, object], payload)))


def make_runtime_checks_artifact(schema: str, body: dict[str, object]) -> RuntimeChecksArtifactV2:
    if schema not in _REFS:
        raise ValueError("runtime_checks_schema_unsupported")
    field, domain = _REFS[schema]
    value = {"schema_id": schema, **body}
    return decode_runtime_checks_artifact({**value, field: domain + digest(value)})


class RuntimeChecksSourceIssuerV2:
    def require_input(self, _value: RuntimeChecksVerifiedInputV2) -> None:
        raise NotImplementedError


_ISSUERS: set[type[RuntimeChecksSourceIssuerV2]] = set()


def _register_runtime_checks_issuer(kind: type[RuntimeChecksSourceIssuerV2]) -> None:  # pyright: ignore[reportUnusedFunction]
    _ISSUERS.add(kind)


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class RuntimeChecksVerifiedInputV2:
    canonical_body: str
    source_evidence: RuntimeChecksSourceIssuerV2

    def to_wire(self) -> dict[str, object]:
        return cast(dict[str, object], strict_json(self.canonical_body))


def require_runtime_checks_input(value: RuntimeChecksVerifiedInputV2) -> RuntimeChecksVerifiedInputV2:
    if type(value) is not RuntimeChecksVerifiedInputV2 or not hasattr(value, "source_evidence") or type(value.source_evidence) not in _ISSUERS:
        raise ValueError("runtime_checks_input_unissued_or_mutated")
    value.source_evidence.require_input(value)
    return value


def runtime_checks_selected_work(document: GoalPhaseNativeDocumentV4, request: dict[str, object]) -> dict[str, object]:
    """Shared pure profile/selection law, NOT an authority issuer or decision.

    Providers independently restore the document and the returned Issue identity.
    This same structural law is available to a future non-filesystem provider.
    """
    if type(document) is not GoalPhaseNativeDocumentV4:
        raise ValueError("runtime_checks_requires_v4")
    document.__post_init__()
    request = decode_runtime_checks_artifact(request).to_wire()
    c = coordinate(request["coordinate"])
    definition = next((d for d in document.definitions if d.coordinate == c), None)
    phase = next((p for p in document.operational_bundle.phases if p.coordinate == c), None)
    lane = next((l for l in document.native_lane_authorities if l.lane_key == c.lane_key), None)
    if definition is None or phase is None or lane is None or document.goal_tag != request["goal_tag"]:
        raise ValueError("runtime_checks_coordinate_unavailable")
    gate = definition.gate
    if gate.gate_contract_ref != GATE_CONTRACT or gate.evidence_schema_ref != EVIDENCE_SCHEMA or sorted(gate.invariant_refs) != sorted(INVARIANTS):
        raise ValueError("gate_evaluator_profile_unsupported")
    if definition.definition_ref != request["definition_ref"] or gate.gate_digest != request["gate_digest"] or phase.gate != gate:
        raise ValueError("runtime_checks_definition_gate_mismatch")
    current = [w for w in phase.work_associations if w.disposition is GoalLanePhaseWorkDisposition.CURRENT]
    if len(current) != 1 or current[0].role is not GoalLanePhaseWorkRole.IMPLEMENTATION or lane.current_work_association_ref != current[0].association_ref:
        raise ValueError("implementation_work_issue_mismatch")
    work = current[0]
    binding: dict[str, object] = {"coordinate": endpoints_coord(c), "association_ref": work.association_ref,
        "receipt_ref": work.receipt_ref, "issue_ref": work.issue_ref, "role": work.role.value,
        "disposition": work.disposition.value}
    if binding != cast(dict[str, object], request["implementation_publication"])["selected_work_binding"]:
        raise ValueError("implementation_work_issue_mismatch")
    return binding


def require_runtime_checks_dependency_profile(document: GoalPhaseNativeDocumentV4, request: dict[str, object]) -> None:
    """No caller inventory can omit an incoming declaration in the first profile."""
    document.__post_init__()
    c = coordinate(request["coordinate"])
    if (any(d.dependent == c for d in document.operational_bundle.dependencies)
        or any(d.dependent == c for d in document.unresolved_dependencies) or request["incoming_declarations"]):
        raise ValueError("gate_evaluator_dependency_profile_unsupported")


def _scoped_operation_journal(
    wire: dict[str, object], goal_tag: str, lane_key: str, phase_key: str | None = None,
) -> dict[str, object]:
    """Bind canonical profile and full scoped entries, not the aggregate digest.

    V3 implies profile v1; V4 names it explicitly. Filtering preserves entry
    order and all decision/causal fields, including each content-derived ref.
    An unrelated entry must not invalidate this closure through journal_ref.
    """
    journal = wire.get("phase_operation_journal")
    profile = wire.get("operation_journal_profile", "v1" if journal is not None else "none")
    scoped = None
    if journal is not None:
        body = cast(dict[str, object], journal)
        entries: list[dict[str, object]] = []
        for entry in cast(list[dict[str, object]], body["entries"]):
            c = cast(dict[str, object], entry["coordinate"])
            if (c["goal_tag"] == goal_tag and c["lane_key"] == lane_key
                and (phase_key is None or c["phase_key"] == phase_key)):
                entries.append(entry)
        scoped = {"schema_id": body["schema_id"], "entries": entries}
    return {"operation_journal_profile": profile, "phase_operation_journal": scoped}


def runtime_checks_semantic_scope(
    document: GoalPhaseNativeDocumentV4, global_authority: GoalGlobalDirectionAuthorityV1,
    lane_key: str, dependency_sources: Mapping[str, _DependencyScopeSource],
    lane_authorities: tuple[GoalLaneDirectionAuthorityV1, ...],
) -> dict[str, object]:
    """Pure closure projection, not a currentness or eligibility authority.

    Work Issues are independently protected in the source inventory. Their
    exact permitted publication effects are not erased into this projection.
    """
    document.__post_init__()
    global_authority.__post_init__()
    body = cast(dict[str, object], strict_json(encode_goal_phase_native_document(document)))
    def member(raw: dict[str, object], lane: str) -> bool:
        return cast(dict[str, object], raw["coordinate"])["lane_key"] == lane
    bundle = cast(dict[str, object], body["operational_bundle"])
    incident = [d for d in document.operational_bundle.dependencies if any(
        c.goal_tag == document.goal_tag and c.lane_key == lane_key for c in (d.dependent, d.prerequisite))]
    coordinates = {c for d in incident for c in (d.dependent, d.prerequisite)}
    endpoints: list[dict[str, object]] = []
    for c in sorted(coordinates, key=lambda c: (c.goal_tag, c.lane_key, c.phase_key)):
        source = document if c.goal_tag == document.goal_tag else dependency_sources[c.goal_tag].document
        source.__post_init__()
        wire = cast(dict[str, object], strict_json(encode_goal_phase_native_document(source)))
        other = None if c.goal_tag == document.goal_tag else dependency_sources[c.goal_tag]
        endpoints.append({"coordinate": {"goal_tag": c.goal_tag, "lane_key": c.lane_key, "phase_key": c.phase_key},
            "global": global_authority.semantic_wire() if other is None else other.global_authority.semantic_wire(),
            "lane": [r for r in cast(list[dict[str, object]], wire.get("native_lane_authorities", [])) if r["lane_key"] == c.lane_key]
                or [a.semantic_wire() for a in (lane_authorities if other is None else other.lane_authorities) if a.lane_key == c.lane_key],
            "definitions": [r for r in cast(list[dict[str, object]], wire["definitions"]) if r["coordinate"] == endpoints_coord(c)],
            "phases": [r for r in cast(list[dict[str, object]], cast(dict[str, object], wire["operational_bundle"])["phases"])
                if r["coordinate"] == endpoints_coord(c)],
            "execution_authority": wire.get("execution_authority"), "source_refs": wire["source_refs"],
            **_scoped_operation_journal(wire, c.goal_tag, c.lane_key, c.phase_key)})
    return {"global": global_authority.semantic_wire(), "execution_authority": body["execution_authority"],
        "lane": [r for r in cast(list[dict[str, object]], body["native_lane_authorities"]) if r["lane_key"] == lane_key],
        "definitions": [r for r in cast(list[dict[str, object]], body["definitions"]) if member(r, lane_key)],
        "phases": [r for r in cast(list[dict[str, object]], bundle["phases"]) if member(r, lane_key)],
        "incident": [r for r in cast(list[dict[str, object]], bundle["dependencies"]) if any(
            cast(dict[str, object], r[k])["goal_tag"] == document.goal_tag and
            cast(dict[str, object], r[k])["lane_key"] == lane_key for k in ("dependent", "prerequisite"))],
        "unresolved": [r for r in cast(list[dict[str, object]], body["unresolved_dependencies"]) if any(
            cast(dict[str, object], r[k])["goal_tag"] == document.goal_tag and
            cast(dict[str, object], r[k])["lane_key"] == lane_key for k in ("dependent", "prerequisite"))],
        "endpoints": endpoints, "source_refs": body["source_refs"],
        **_scoped_operation_journal(body, document.goal_tag, lane_key)}


def endpoints_coord(c: GoalPhaseCoordinate) -> dict[str, str]:
    return {"goal_tag": c.goal_tag, "lane_key": c.lane_key, "phase_key": c.phase_key}


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class RuntimeChecksEvaluationV2:
    canonical_body: str

    def to_wire(self) -> dict[str, object]:
        return cast(dict[str, object], strict_json(self.canonical_body))


_EVALUATIONS: weakref.WeakKeyDictionary[RuntimeChecksEvaluationV2, str] = weakref.WeakKeyDictionary()


def require_runtime_checks_evaluation(value: RuntimeChecksEvaluationV2) -> RuntimeChecksEvaluationV2:
    """An authored/constructed result is transport, not an issued evaluation."""
    if type(value) is not RuntimeChecksEvaluationV2 or _EVALUATIONS.get(value) != digest(value.to_wire()):
        raise ValueError("runtime_checks_evaluation_unissued_or_mutated")
    return value


def evaluate_runtime_checks_review_v2(qualified: RuntimeChecksVerifiedInputV2) -> RuntimeChecksEvaluationV2:
    value = require_runtime_checks_input(qualified).to_wire()
    request = decode_runtime_checks_artifact(value["request"]).to_wire()
    proof = decode_runtime_checks_artifact(value["proof"]).to_wire()
    review = decode_runtime_checks_artifact(value["review"]).to_wire()
    verification = cast(dict[str, object], value["source_verification"])
    for entry in (proof, review):
        for name in ("coordinate", "definition_ref", "gate_digest", "evaluator_profile", "source_scope_ref"):
            if entry[name] != request[name]:
                raise ValueError("runtime_checks_cross_role_mismatch")
        if entry["request_ref"] != request["request_ref"]:
            raise ValueError("runtime_checks_cross_role_mismatch")
    if review["proof_ref"] != proof["proof_ref"]:
        raise ValueError("runtime_checks_cross_role_mismatch")
    reasons: set[str] = set()
    for c in cast(list[dict[str, object]], proof["checks"]):
        if c["source_scope_ref"] != request["source_scope_ref"]:
            raise ValueError("runtime_checks_cross_role_mismatch")
        key = c["key"]
        if key == "package-tests":
            if c["exit_code"] != 0 or c["failed_count"] != 0:
                reasons.add("package_tests_failed")
            if c["passed_count"] == 0 or c["skipped_count"] != 0:
                reasons.add("package_tests_incomplete")
        elif key == "static-checks":
            if c["exit_code"] != 0 or c["error_count"] != 0 or c["warning_count"] != 0:
                reasons.add("static_checks_failed")
        elif c["exit_code"] != 0 or c["result"] == "failed":
            reasons.add("runtime_canary_failed")
        elif c["result"] == "unavailable":
            reasons.add("runtime_canary_unavailable")
    if review["verdict"] != "accepted":
        reasons.add("independent_review_" + text(review["verdict"]))
    inventory = cast(list[dict[str, object]], verification["authority_inventory"])
    for event in cast(list[dict[str, object]], verification["history_effects"]):
        if event["permitted_publication_ref"] is not None:
            continue
        changed = cast(list[str], event["changed_paths"])
        for item in inventory:
            if item["path"] not in changed:
                continue
            role = text(item["role"])
            if role.startswith("proof"):
                reasons.add("proof_publication_stale")
            elif role.startswith("review"):
                reasons.add("independent_review_stale")
            else:
                reasons.add("source_scope_stale")
    rejected = {"independent_review_rejected", "package_tests_failed", "static_checks_failed", "runtime_canary_failed"}
    stale = {"source_scope_stale", "proof_publication_stale", "independent_review_stale"}
    result = "rejected" if reasons & rejected else "stale" if reasons & stale else "unavailable" if reasons else "satisfied"
    evaluator = "goal-runtime-checks-evaluator:" + digest(value)
    currentness = "goal-runtime-checks-currentness:" + digest(verification)
    observed = text(verification["observed_source_revision_ref"])
    at = _utc_instant(text(value["evaluated_at"]), "evaluated_at")
    pubs = cast(list[dict[str, object]], verification["authority_publications"])
    evidence = sorted([text(request["request_ref"]), text(proof["proof_ref"]), text(review["review_ref"]),
        *(text(p["publication_ref"]) for p in pubs)])
    gate = {"gate_digest": request["gate_digest"], "outcome": {"unavailable": "unresolved"}.get(result, result),
        "evaluator_ref": evaluator, "evidence_refs": evidence, "source_revision_refs": [observed],
        "evaluated_at": at, "currentness_ref": currentness}
    observation = {**gate, "observation_ref": "goal-phase-gate-observation:" + digest(gate)}
    body = {"schema_id": EVALUATION, "coordinate": request["coordinate"], "definition_ref": request["definition_ref"],
        "gate_digest": request["gate_digest"], "evaluator_profile": PROFILE, "request_ref": request["request_ref"],
        "proof_ref": proof["proof_ref"], "review_ref": review["review_ref"], "authority_publications": pubs,
        "source_verification": verification, "result": result, "reasons": sorted(reasons), "source_revision_ref": observed,
        "evaluated_at": at, "evaluator_ref": evaluator, "currentness_ref": currentness, "gate_observation": observation,
        "effect_profile": "read_only_non_authorizing", "event_effect": "none", "dispatch_effect": "none"}
    result_object = RuntimeChecksEvaluationV2(canonical_json({**body, "evaluation_ref": "goal-runtime-checks-evaluation:" + digest(body)}))
    _EVALUATIONS[result_object] = digest(result_object.to_wire())
    return result_object


def decode_runtime_checks_evaluation(payload: object, *, qualified: RuntimeChecksVerifiedInputV2) -> RuntimeChecksEvaluationV2:
    expected = evaluate_runtime_checks_review_v2(qualified)
    if not exact_hold_wire(payload, expected.to_wire()):
        raise ValueError("runtime_checks_evaluation_differs_from_authority")
    return expected
