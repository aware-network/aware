"""Strict native-lane introduction facts; a receipt is not issuer authentication.

The repository provider must independently verify the named commit, Issue,
Goal owner, and protected history before using this receipt for eligibility.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from .identity import fingerprint
from .phase_document import (
    GoalNativeLaneAuthorityV1,
    GoalPhaseNativeDocumentV2,
    GoalPhaseNativeDocumentV3,
    GoalPhaseNativeDocumentV4,
    encode_goal_phase_native_document,
)
from .phase_contracts import GoalLanePhaseWorkDisposition, GoalPhaseCoordinate
from .phase_frontier import goal_phase_dependency_digest
from .phase_native_lane_evidence import (
    GoalNativeLaneEvidenceSnapshotV2, require_native_lane_evidence_for_document,
    require_native_lane_gate_scope, native_lane_gate_issue_scope,
)
from .phase_native_scope_advancement import (
    GoalGlobalDirectionAuthorityV1, GoalLaneDirectionAuthorityV1,
)

RECEIPT_SCHEMA = "aware.goal.native-lane-introduction-publication-receipt.v1"
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_DOCUMENT = re.compile(r"goal-phase-document:sha256:[0-9a-f]{64}\Z")
_LANE = re.compile(r"goal-native-lane-authority:sha256:[0-9a-f]{64}\Z")


class GoalNativeLaneDirectionEvidenceV1:
    """Source adapter proof, not a callable accepting caller-authored mappings.

    An accepted adapter installs its exact verifier implementation at bootstrap.
    Input data cannot install providers. Concrete implementations must require
    an actually issued instance bound to the complete direction snapshot.
    """

    def require_direction(self, _value: GoalNativeLaneDirectionAuthorityV1) -> None:
        raise NotImplementedError("native lane evidence requires an admitted concrete verifier")


_DIRECTION_EVIDENCE_TYPES: set[type[GoalNativeLaneDirectionEvidenceV1]] = set()


def _register_goal_native_lane_evidence_type(  # pyright: ignore[reportUnusedFunction]
    evidence_type: object,
) -> None:
    """Internal adapter-code admission; never an authored/wire input entrance."""
    if not isinstance(evidence_type, type) or not issubclass(evidence_type, GoalNativeLaneDirectionEvidenceV1):
        raise TypeError("native lane evidence implementation must be a concrete verifier type")
    _DIRECTION_EVIDENCE_TYPES.add(evidence_type)


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False)
class GoalNativeLaneDirectionAuthorityV1:
    """Qualified source snapshot, issued by a concrete provider after verification.

    Construction/decoding and a content-derived reference alone never qualify
    this type. The bounded provider entrance issues it only after authenticating
    publication, complete scope history and terminal source currentness.
    """

    document: GoalPhaseNativeDocumentV4
    global_authority: GoalGlobalDirectionAuthorityV1
    lane_key: str
    issue_authorities: Mapping[str, Mapping[str, object]]
    dependency_sources: Mapping[str, GoalNativeLaneDependencySourceV1]
    source_blob_ref: str
    goal_sha256: str
    publication_ref: str
    scope_currentness_ref: str
    semantic_closure_ref: str
    projector_ref: str
    source_evidence: GoalNativeLaneDirectionEvidenceV1
    evidence_snapshot: GoalNativeLaneEvidenceSnapshotV2 | None = None

    def _body(self) -> dict[str, object]:
        lane = next(r for r in self.document.native_lane_authorities if r.lane_key == self.lane_key)
        body: dict[str, object] = {
            "schema_id": ("aware.goal.native-lane-direction-authority.v1" if self.evidence_snapshot is None
                else "aware.goal.native-lane-direction-authority.v2"),
            "goal_tag": self.document.goal_tag, "lane_key": self.lane_key,
            "role": lane.role, "owner_profile": lane.owner_profile,
            "owner_ref": lane.owner_ref, "operational_state": lane.operational_state,
            "state_detail": lane.state_detail, "hold_authority_refs": list(lane.hold_authority_refs),
            "current_work_association_ref": lane.current_work_association_ref,
            "current_issue_authorities": [
                {**dict(self.issue_authorities[k]), "scope": list(cast(tuple[str, ...], self.issue_authorities[k]["scope"]))}
                for k in sorted(self.issue_authorities)
            ],
            "native_lane_authority_ref": lane.lane_authority_ref,
            "document_ref": self.document.document_ref,
            "source_revision_ref": self.global_authority.source_revision_ref,
            "source_blob_ref": self.source_blob_ref, "goal_sha256": self.goal_sha256,
            "publication_ref": self.publication_ref,
            "scope_currentness_ref": self.scope_currentness_ref,
            "semantic_closure_ref": self.semantic_closure_ref,
            "projector_ref": self.projector_ref,
        }
        if self.evidence_snapshot is not None:
            body["evidence_snapshot"] = self.evidence_snapshot.to_wire()
        return body

    @property
    def authority_ref(self) -> str:
        return "goal-native-lane-direction:" + fingerprint(self._body())

    def to_wire(self) -> dict[str, object]:
        return {**self._body(), "authority_ref": self.authority_ref}


def _direction_fingerprint(value: GoalNativeLaneDirectionAuthorityV1) -> str:  # pyright: ignore[reportUnusedFunction]
    # Include complete nested semantics, not just observation/document refs.
    return fingerprint({
        "authority": value.to_wire(),
        "document": json.loads(encode_goal_phase_native_document(value.document)),
        "goal_global": value.global_authority.to_wire(),
        "issues": {k: dict(v) for k, v in value.issue_authorities.items()},
        "dependency_sources": {tag: {
            "document": json.loads(encode_goal_phase_native_document(source.document)),
            "global_authority": source.global_authority.to_wire(),
            "lane_authorities": [lane.to_wire() for lane in source.lane_authorities],
            "issue_authorities": {k: dict(v) for k, v in source.issue_authorities.items()},
            "source_revision_ref": source.source_revision_ref,
        } for tag, source in value.dependency_sources.items()},
    })


def require_qualified_goal_native_lane_direction(
    value: GoalNativeLaneDirectionAuthorityV1,
) -> GoalNativeLaneDirectionAuthorityV1:
    if type(value) is not GoalNativeLaneDirectionAuthorityV1 or not hasattr(value, "source_evidence"):
        raise GoalNativeLanePublicationError("native_lane_direction_unissued_or_mutated")
    if type(value.source_evidence) not in _DIRECTION_EVIDENCE_TYPES:
        raise GoalNativeLanePublicationError("native_lane_direction_unissued_or_mutated")
    value.source_evidence.require_direction(value)
    _validate_goal_native_lane_direction(value)
    return value


def decode_goal_native_lane_direction_authority(
    payload: Mapping[str, object], *, qualified: GoalNativeLaneDirectionAuthorityV1,
) -> GoalNativeLaneDirectionAuthorityV1:
    """Validate transport against freshly provider-qualified inputs, not itself.

    Decoding never issues a proof. Even a fully re-digested wire value cannot
    substitute another source/Issue/publication for the independently verified
    snapshot. The exact provider output must be independently restored first.
    """
    qualified = require_qualified_goal_native_lane_direction(qualified)
    if type(payload) is not dict or not _exact_direction_wire(cast(dict[str, object], payload), qualified.to_wire()):
        raise GoalNativeLanePublicationError("native_lane_direction_wire_differs_from_authority")
    return qualified


def _exact_direction_wire(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        a, b = cast(dict[str, object], left), cast(dict[str, object], right)
        return a.keys() == b.keys() and all(_exact_direction_wire(a[k], b[k]) for k in a)
    if type(left) is list:
        a_list, b_list = cast(list[object], left), cast(list[object], right)
        return len(a_list) == len(b_list) and all(_exact_direction_wire(a, b) for a, b in zip(a_list, b_list))
    return left == right


def _validate_goal_native_lane_direction(value: GoalNativeLaneDirectionAuthorityV1) -> None:
    """Pure consistency only: this function never registers or issues authority."""
    closure = derive_goal_native_lane_semantic_closure(
        document=value.document, lane_key=value.lane_key, global_authority=value.global_authority,
        issue_authorities=value.issue_authorities, dependency_sources=value.dependency_sources,
        evidence_snapshot=value.evidence_snapshot,
    )
    if value.evidence_snapshot is not None and value.evidence_snapshot.source_revision_ref != value.global_authority.source_revision_ref:
        raise GoalNativeLanePublicationError("native_lane_evidence_epoch_mismatch")
    if value.evidence_snapshot is not None and value.evidence_snapshot.source_binding_ref != "goal-native-lane-source:" + fingerprint({
        "document_ref": value.document.document_ref, "source_revision_ref": value.global_authority.source_revision_ref,
        "source_blob_ref": value.source_blob_ref, "goal_sha256": value.goal_sha256,
    }):
        raise GoalNativeLanePublicationError("native_lane_evidence_source_binding_mismatch")
    if value.semantic_closure_ref != "goal-native-lane-semantic-closure:" + fingerprint(closure):
        raise GoalNativeLanePublicationError("native_lane_direction_closure_mismatch")
    for source in value.dependency_sources.values():
        if source.source_revision_ref != value.global_authority.source_revision_ref:
            raise GoalNativeLanePublicationError("native_lane_direction_source_mismatch")
    for name, token in (
        ("source_blob_ref", value.source_blob_ref), ("publication_ref", value.publication_ref),
        ("scope_currentness_ref", value.scope_currentness_ref), ("projector_ref", value.projector_ref),
    ):
        _ = _text(token, name)
    _ = _match(value.goal_sha256, "goal_sha256", _SHA)


class GoalNativeLanePublicationError(ValueError):
    """The claimed single-carrier lane introduction is not canonical."""


@dataclass(frozen=True, slots=True)
class GoalNativeLaneDependencySourceV1:
    """Source facts, not an authority seal or a dependency outcome.

    A concrete provider must restore these from the named committed source.
    No caller-supplied observations or satisfaction enter this bounded intake.
    """

    document: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4
    global_authority: GoalGlobalDirectionAuthorityV1
    lane_authorities: tuple[GoalLaneDirectionAuthorityV1, ...]
    issue_authorities: Mapping[str, Mapping[str, object]]
    source_revision_ref: str

    def __post_init__(self) -> None:
        if type(self.document) not in {
            GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3, GoalPhaseNativeDocumentV4,
        }:
            raise TypeError("dependency source requires exact native document")
        self.document.__post_init__()
        if type(self.global_authority) is not GoalGlobalDirectionAuthorityV1:
            raise TypeError("dependency Goal authority must be exact")
        self.global_authority.__post_init__()
        _ = _text(self.source_revision_ref, "dependency_source_revision")
        if (
            self.global_authority.goal_tag != self.document.goal_tag
            or self.global_authority.source_revision_ref != self.source_revision_ref
        ):
            raise GoalNativeLanePublicationError("dependency_source_authority_mismatch")
        if type(self.lane_authorities) is not tuple:
            raise TypeError("dependency lane authorities must be an exact tuple")
        seen: set[str] = set()
        for lane in self.lane_authorities:
            if type(lane) is not GoalLaneDirectionAuthorityV1:
                raise TypeError("dependency lane authority must be exact")
            lane.__post_init__()
            if (
                lane.goal_tag != self.document.goal_tag
                or lane.source_revision_ref != self.source_revision_ref
                or lane.lane_key in seen
            ):
                raise GoalNativeLanePublicationError("dependency_lane_source_mismatch")
            seen.add(lane.lane_key)


def derive_goal_native_lane_dependency_scope(
    *, document: GoalPhaseNativeDocumentV4, lane_key: str,
    sources: Mapping[str, GoalNativeLaneDependencySourceV1],
    evidence_snapshot: GoalNativeLaneEvidenceSnapshotV2 | None = None,
) -> list[dict[str, object]]:
    """Derive a complete incident inventory, including explicit absent evidence.

    Epoch identities stay in the provider's audit binding, not the semantic
    digest: a different HEAD alone is not a change to an incident Phase. Every
    endpoint and containing-lane authority is nevertheless independently read
    at that HEAD by the provider, including external Goals.
    """
    if type(document) is not GoalPhaseNativeDocumentV4:
        raise TypeError("dependency scope requires exact V4 document")
    document.__post_init__()
    if len(tuple(r for r in document.native_lane_authorities if r.lane_key == lane_key)) != 1:
        raise GoalNativeLanePublicationError("native_lane_authority_absent")
    sources = dict(sources)
    incident = tuple(d for d in document.operational_bundle.dependencies if any(
        c.goal_tag == document.goal_tag and c.lane_key == lane_key
        for c in (d.dependent, d.prerequisite)
    ))
    required = {c.goal_tag for d in incident for c in (d.dependent, d.prerequisite)}
    if set(sources) != required:
        raise GoalNativeLanePublicationError("incident_dependency_source_set_mismatch")
    for tag, source in sources.items():
        if type(source) is not GoalNativeLaneDependencySourceV1:
            raise TypeError("dependency source facts must be exact")
        source.__post_init__()
        if source.document.goal_tag != tag or (
            tag == document.goal_tag and source.document.document_ref != document.document_ref
        ):
            raise GoalNativeLanePublicationError("incident_dependency_document_mismatch")
        endpoint_lanes = {c.lane_key for d in incident for c in (d.dependent, d.prerequisite) if c.goal_tag == tag}
        required_issues = {w.issue_ref for p in source.document.operational_bundle.phases
            if p.coordinate.lane_key in endpoint_lanes for w in p.work_associations
            if w.disposition is GoalLanePhaseWorkDisposition.CURRENT}
        if set(source.issue_authorities) != required_issues:
            raise GoalNativeLanePublicationError("incident_dependency_issue_set_mismatch")
    wire = cast(dict[str, object], json.loads(encode_goal_phase_native_document(document)))
    declarations = cast(list[dict[str, object]], cast(dict[str, object], wire["operational_bundle"])["dependencies"])
    records: list[dict[str, object]] = []
    for dependency in sorted(incident, key=lambda d: d.dependency_key):
        declaration = next(d for d in declarations if d["dependency_key"] == dependency.dependency_key)
        dependent = _dependency_endpoint_scope(sources[dependency.dependent.goal_tag], dependency.dependent, document, lane_key, evidence_snapshot)
        prerequisite = _dependency_endpoint_scope(sources[dependency.prerequisite.goal_tag], dependency.prerequisite, document, lane_key, evidence_snapshot)
        definition = cast(dict[str, object], prerequisite["definition"])
        if cast(dict[str, object], definition["gate"])["gate_digest"] != dependency.required_gate_digest:
            raise GoalNativeLanePublicationError("incident_dependency_required_gate_mismatch")
        records.append({
            "declaration": declaration,
            "dependency_digest": goal_phase_dependency_digest(dependency),
            "dependent": dependent, "prerequisite": prerequisite,
            "observation_profile": "not_evaluated", "observation": None,
        })
    unresolved = cast(list[dict[str, object]], wire["unresolved_dependencies"])
    records.extend({
        "declaration": d, "dependency_digest": fingerprint(d),
        "observation_profile": "unresolved", "observation": None,
    } for d in unresolved if any(
        cast(dict[str, object], d[name])["goal_tag"] == document.goal_tag
        and cast(dict[str, object], d[name])["lane_key"] == lane_key
        for name in ("dependent", "prerequisite")
    ))
    return sorted(records, key=lambda r: cast(str, cast(dict[str, object], r["declaration"])["dependency_key"]))


def _dependency_endpoint_scope(
    source: GoalNativeLaneDependencySourceV1, coordinate: GoalPhaseCoordinate,
    document: GoalPhaseNativeDocumentV4, lane_key: str,
    evidence_snapshot: GoalNativeLaneEvidenceSnapshotV2 | None,
) -> dict[str, object]:
    body = cast(dict[str, object], json.loads(encode_goal_phase_native_document(source.document)))
    coord = {"goal_tag": coordinate.goal_tag, "lane_key": coordinate.lane_key, "phase_key": coordinate.phase_key}
    definitions = [d for d in cast(list[dict[str, object]], body["definitions"]) if d["coordinate"] == coord]
    if len(definitions) != 1:
        raise GoalNativeLanePublicationError("incident_dependency_definition_unavailable")
    phases = tuple(p for p in source.document.operational_bundle.phases if p.coordinate == coordinate)
    if any(p.gate_observations for p in phases):
        raise GoalNativeLanePublicationError("incident_dependency_gate_authority_unavailable")
    current = tuple(w.issue_ref for p in source.document.operational_bundle.phases
        if p.coordinate.lane_key == coordinate.lane_key for w in p.work_associations
        if w.disposition is GoalLanePhaseWorkDisposition.CURRENT)
    if coordinate.goal_tag == document.goal_tag and coordinate.lane_key == lane_key:
        lane = next(r for r in document.native_lane_authorities if r.lane_key == lane_key)
        lane_body = next(r for r in cast(list[dict[str, object]], body["native_lane_authorities"]) if r["lane_key"] == lane_key)
        owner = lane.owner_ref
        holds = lane.hold_authority_refs
    else:
        lanes = tuple(a for a in source.lane_authorities if a.lane_key == coordinate.lane_key)
        if len(lanes) != 1 or lanes[0].qualification != "qualified":
            raise GoalNativeLanePublicationError("incident_dependency_lane_authority_unavailable")
        authority = lanes[0]
        expected = authority.current_issue_ref
        if current != (() if expected is None or expected.startswith("TBD:") else (expected,)):
            raise GoalNativeLanePublicationError("incident_dependency_lane_work_disagreement")
        lane_body, owner, holds = authority.semantic_wire(), authority.owner_ref, authority.blocker_authority_refs
    if holds:
        if coordinate.goal_tag == document.goal_tag and coordinate.lane_key == lane_key and evidence_snapshot is not None:
            _ = require_native_lane_evidence_for_document(evidence_snapshot, document=document, lane_key=lane_key)
        else:
            raise GoalNativeLanePublicationError("incident_dependency_hold_authority_unavailable")
    if source.global_authority.hold_state != "clear":
        raise GoalNativeLanePublicationError("incident_dependency_hold_authority_unavailable")
    issues: list[dict[str, object]] = []
    for issue_ref in current:
        if issue_ref not in source.issue_authorities:
            raise GoalNativeLanePublicationError("incident_dependency_current_issue_unavailable")
        issue = _validated_current_issue(source.issue_authorities[issue_ref], owner)
        if evidence_snapshot is not None and evidence_snapshot.gate_observations and (
            coordinate.goal_tag == document.goal_tag and coordinate.lane_key == lane_key
        ):
            issue = native_lane_gate_issue_scope(evidence_snapshot, issue)
        issue["scope"] = list(cast(tuple[str, ...], issue["scope"]))
        issues.append(issue)
    bundle = cast(dict[str, object], body["operational_bundle"])
    phase_wires = [p for p in cast(list[dict[str, object]], bundle["phases"]) if p["coordinate"] == coord]
    return {"goal_global": source.global_authority.semantic_wire(), "lane": lane_body,
        "definition": definitions[0], "phase": phase_wires[0] if phase_wires else None,
        "issues": issues, **_scoped_operation_journal(body, coordinate=coord)}


def _scoped_operation_journal(
    body: dict[str, object], *, lane_key: str | None = None,
    coordinate: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Bind the canonical profile and only this scope's complete entry wires.

    The containing document has already passed its exact codec invariants.
    A journal binding is not actor-action/policy authentication. Do not bind
    the aggregate journal ref: an unrelated entry must not change this scope.
    """
    journal = body.get("phase_operation_journal")
    profile = body.get("operation_journal_profile", "none" if journal is None else "v1")
    entries = [] if journal is None else cast(list[dict[str, object]],
        cast(dict[str, object], journal)["entries"])
    scoped = [entry for entry in entries if (
        entry["coordinate"] == coordinate if coordinate is not None
        else cast(dict[str, object], entry["coordinate"])["lane_key"] == lane_key
    )]
    return {"operation_journal_profile": profile, "operation_journal": scoped}


def _validated_current_issue(value: Mapping[str, object], owner: str) -> dict[str, object]:
    authority = dict(value)
    if set(authority) != {"path", "blob_oid", "tag", "owner", "status", "scope", "scope_digest"}:
        raise GoalNativeLanePublicationError("native_lane_issue_authority_fields")
    _ = _path(authority["path"], "current_issue_path")
    _ = _match(authority["blob_oid"], "current_issue_blob_oid", _OID)
    _ = _text(authority["tag"], "current_issue_tag")
    _ = _text(authority["owner"], "current_issue_owner")
    scope = authority["scope"]
    if type(scope) is not tuple or not scope:
        raise GoalNativeLanePublicationError("native_lane_issue_scope_invalid")
    if any(type(p) is not str for p in cast(tuple[object, ...], scope)):
        raise GoalNativeLanePublicationError("native_lane_issue_scope_invalid")
    scope = cast(tuple[str, ...], scope)
    if len(set(scope)) != len(scope):
        raise GoalNativeLanePublicationError("native_lane_issue_scope_invalid")
    for path in scope:
        _ = _path(path, "current_issue_scope_path")
    if authority["scope_digest"] != fingerprint({"ownership_scope": list(scope)}):
        raise GoalNativeLanePublicationError("native_lane_issue_scope_digest_mismatch")
    if authority["status"] != "in_progress" or authority["owner"] != owner:
        raise GoalNativeLanePublicationError("native_lane_current_work_issue_disagreement")
    return authority


def derive_goal_native_lane_semantic_closure(
    *,
    document: GoalPhaseNativeDocumentV4,
    lane_key: str,
    global_authority: GoalGlobalDirectionAuthorityV1,
    issue_authorities: Mapping[str, Mapping[str, object]],
    dependency_sources: Mapping[str, GoalNativeLaneDependencySourceV1] | None = None,
    evidence_snapshot: GoalNativeLaneEvidenceSnapshotV2 | None = None,
    gate_history_evidence: GoalNativeLaneEvidenceSnapshotV2 | None = None,
) -> dict[str, object]:
    """Pure canonical scope derivation; source authentication is external.

    Incident declarations and absent observations are complete and explicit.
    Holds and supplied Gate observations still require their qualified intake.
    It is not a constructor of qualified authority or an eligibility verdict.
    """

    if type(document) is not GoalPhaseNativeDocumentV4:
        raise TypeError("closure requires exact V4 document")
    document.__post_init__()
    if type(global_authority) is not GoalGlobalDirectionAuthorityV1:
        raise TypeError("closure requires exact Goal-global authority")
    global_authority.__post_init__()
    if document.goal_tag != global_authority.goal_tag:
        raise GoalNativeLanePublicationError("closure_goal_authority_mismatch")
    records = tuple(x for x in document.native_lane_authorities if x.lane_key == lane_key)
    if len(records) != 1:
        raise GoalNativeLanePublicationError("native_lane_authority_absent")
    record = records[0]
    if gate_history_evidence is not None:
        if evidence_snapshot is not None:
            raise GoalNativeLanePublicationError("native_lane_evidence_must_not_be_substituted")
        _ = require_native_lane_gate_scope(gate_history_evidence, document=document, lane_key=lane_key)
    if evidence_snapshot is not None:
        _ = require_native_lane_evidence_for_document(evidence_snapshot, document=document, lane_key=lane_key)
    elif record.hold_authority_refs:
        raise GoalNativeLanePublicationError("native_lane_hold_authority_unavailable")
    dependency_scope = derive_goal_native_lane_dependency_scope(
        document=document, lane_key=lane_key,
        sources={} if dependency_sources is None else dependency_sources,
        evidence_snapshot=evidence_snapshot if gate_history_evidence is None else gate_history_evidence,
    )
    body = cast(dict[str, object], json.loads(encode_goal_phase_native_document(document)))
    record_wire = next(
        x for x in cast(list[dict[str, object]], body["native_lane_authorities"])
        if x["lane_key"] == lane_key
    )
    definitions = [
        d for d in cast(list[dict[str, object]], body["definitions"])
        if cast(dict[str, object], d["coordinate"])["lane_key"] == lane_key
    ]
    bundle = cast(dict[str, object], body["operational_bundle"])
    phases = [
        p for p in cast(list[dict[str, object]], bundle["phases"])
        if cast(dict[str, object], p["coordinate"])["lane_key"] == lane_key
    ]
    required: list[str] = []
    issues: list[dict[str, object]] = []
    for phase in document.operational_bundle.phases:
        if phase.coordinate.lane_key != lane_key:
            continue
        if phase.gate_observations:
            # Immutable observation bytes alone do not prove that their
            # evaluator/evidence source epochs remain current. That intake is
            # an explicit remaining gate, not a scope-currentness shortcut.
            raise GoalNativeLanePublicationError("native_lane_gate_authority_unavailable")
        for work in phase.work_associations:
            if work.disposition is not GoalLanePhaseWorkDisposition.CURRENT:
                continue
            required.append(work.issue_ref)
            if work.issue_ref not in issue_authorities:
                raise GoalNativeLanePublicationError("native_lane_current_issue_unavailable")
            authority = _validated_current_issue(issue_authorities[work.issue_ref], record.owner_ref)
            scope_evidence = evidence_snapshot if gate_history_evidence is None else gate_history_evidence
            if scope_evidence is not None and scope_evidence.gate_observations:
                authority = native_lane_gate_issue_scope(scope_evidence, authority)
            if work.association_ref != record.current_work_association_ref:
                raise GoalNativeLanePublicationError("native_lane_current_work_issue_disagreement")
            authority["scope"] = list(cast(tuple[str, ...], authority["scope"]))
            issues.append(authority)
    if set(issue_authorities) != set(required):
        raise GoalNativeLanePublicationError("native_lane_issue_set_mismatch")
    closure: dict[str, object] = {
        "goal_global": global_authority.semantic_wire(), "native_lane": record_wire,
        "definitions": definitions, "phases": phases,
        "incident_dependencies": dependency_scope, "issues": issues,
        "source_refs": list(document.source_refs),
        **_scoped_operation_journal(body, lane_key=lane_key),
    }
    scope_evidence = evidence_snapshot if gate_history_evidence is None else gate_history_evidence
    if scope_evidence is not None:
        # Admission/currentness bindings stay outside the semantic digest.
        # The complete immutable decision remains inside semantic authority.
        closure["qualified_holds"] = [hold.decision.to_wire() for hold in scope_evidence.holds]
    return closure


def reduce_goal_native_lane_scope_history(
    *,
    lineage: str,
    origin_closure_ref: str,
    current_closure_ref: str,
    effect_closure_pairs: tuple[tuple[str, str], ...],
    compatibility_relations: tuple[str, ...],
) -> tuple[str, str, str, tuple[str, ...]]:
    """One neutral currentness law over independently verified provider facts.

    Like the receipt/closure, plain reducer inputs are not qualified source
    evidence. The concrete provider verifies and registers the joined result.
    """
    if lineage not in {"equal", "descendant", "unproven"}:
        raise GoalNativeLanePublicationError("unsupported lane lineage")
    if type(effect_closure_pairs) is not tuple or type(compatibility_relations) is not tuple:
        raise TypeError("lane history facts must be exact tuples")
    if len(effect_closure_pairs) != len(compatibility_relations):
        raise GoalNativeLanePublicationError("lane history completeness mismatch")
    for ref in (origin_closure_ref, current_closure_ref):
        _ = _match(ref, "closure_ref", re.compile(r"goal-native-lane-semantic-closure:sha256:[0-9a-f]{64}\Z"))
    for pair in effect_closure_pairs:
        if type(pair) is not tuple or len(pair) != 2:
            raise GoalNativeLanePublicationError("lane history pair invalid")
        for ref in pair:
            _ = _match(ref, "effect_closure_ref", re.compile(r"goal-native-lane-semantic-closure:sha256:[0-9a-f]{64}\Z"))
    if any(r not in {"exact", "allowlisted_append", "decoded_authority_change", "unknown"} for r in compatibility_relations):
        raise GoalNativeLanePublicationError("lane compatibility relation invalid")
    if lineage == "unproven":
        return "ambiguous", "unproven", "refuse", ("repository_lineage_unproven",)
    if lineage == "equal" and (effect_closure_pairs or origin_closure_ref != current_closure_ref):
        raise GoalNativeLanePublicationError("equal lane lineage has effects")
    if lineage == "descendant" and not effect_closure_pairs:
        raise GoalNativeLanePublicationError("descendant lane lineage lacks effects")
    projection = "exact" if lineage == "equal" else "advanced"
    reasons: set[str] = set()
    if origin_closure_ref != current_closure_ref or any(a != b for a, b in effect_closure_pairs):
        reasons.add("lane_scope_changed")
    if "unknown" in compatibility_relations:
        reasons.add("compatibility_unknown")
        return "ambiguous", projection, "refuse", tuple(sorted(reasons))
    if reasons:
        return "stale", projection, "admitted_delta_required", tuple(sorted(reasons))
    return "current", projection, "exact" if lineage == "equal" else "reobserved_unchanged", ()


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise GoalNativeLanePublicationError(f"{name} must be exact nonempty text")
    return value


def _match(value: object, name: str, pattern: re.Pattern[str]) -> str:
    result = _text(value, name)
    if pattern.fullmatch(result) is None:
        raise GoalNativeLanePublicationError(f"{name} has invalid identity")
    return result


def _path(value: object, name: str) -> str:
    """Validate repository coordinates; roots/templates belong to the provider."""

    path = _text(value, name)
    if (
        any(part in {"", ".", ".."} for part in path.split("/"))
        or any(char in path for char in ("\\", ":"))
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
    ):
        raise GoalNativeLanePublicationError(f"{name} is not a canonical path")
    return path


@dataclass(frozen=True, slots=True)
class GoalNativeLaneIntroductionPublicationReceiptV1:
    """Exact claimed effect coordinates, requiring independent provider proof."""

    goal_tag: str
    lane_key: str
    lane_authority_ref: str
    goal_path: str
    before_document_ref: str
    after_document_ref: str
    before_goal_sha256: str
    after_goal_sha256: str
    before_goal_blob_oid: str
    after_goal_blob_oid: str
    repository_parent_ref: str
    repository_commit_ref: str
    repository_commit_receipt_ref: str
    publication_issue_path: str
    publication_issue_blob_oid: str
    publication_issue_owner_execution_id: str
    publication_issue_status: str
    publication_issue_scope_digest: str
    receipt_ref: str = field(init=False)
    schema_id: str = RECEIPT_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalNativeLaneIntroductionPublicationReceiptV1:
            raise TypeError("receipt type must be exact")
        if self.schema_id != RECEIPT_SCHEMA:
            raise GoalNativeLanePublicationError("unsupported receipt schema")
        _ = _text(self.goal_tag, "goal_tag")
        _ = _text(self.lane_key, "lane_key")
        _ = _match(self.lane_authority_ref, "lane_authority_ref", _LANE)
        _ = _path(self.goal_path, "goal_path")
        _ = _match(self.before_document_ref, "before_document_ref", _DOCUMENT)
        _ = _match(self.after_document_ref, "after_document_ref", _DOCUMENT)
        _ = _match(self.before_goal_sha256, "before_goal_sha256", _SHA)
        _ = _match(self.after_goal_sha256, "after_goal_sha256", _SHA)
        for name in (
            "before_goal_blob_oid", "after_goal_blob_oid", "repository_parent_ref",
            "repository_commit_ref", "publication_issue_blob_oid",
        ):
            _ = _match(cast(object, getattr(self, name)), name, _OID)
        if self.repository_parent_ref == self.repository_commit_ref:
            raise GoalNativeLanePublicationError("publication commit must advance parent")
        if self.repository_commit_receipt_ref != (
            "repository-commit:" + self.repository_commit_ref
        ):
            raise GoalNativeLanePublicationError("repository receipt/commit mismatch")
        _ = _path(self.publication_issue_path, "publication_issue_path")
        _ = _text(self.publication_issue_owner_execution_id, "publication_issue_owner_execution_id")
        if self.publication_issue_status != "in_progress":
            raise GoalNativeLanePublicationError("publication Issue must be in progress")
        _ = _match(self.publication_issue_scope_digest, "publication_issue_scope_digest", _SHA)
        object.__setattr__(
            self, "receipt_ref", "goal-native-lane-introduction-publication:"
            + fingerprint(self.to_wire(include_ref=False)),
        )

    def to_wire(self, *, include_ref: bool = True) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_id": self.schema_id,
            "goal_tag": self.goal_tag,
            "lane_key": self.lane_key,
            "lane_authority_ref": self.lane_authority_ref,
            "goal_path": self.goal_path,
            "before_document_ref": self.before_document_ref,
            "after_document_ref": self.after_document_ref,
            "before_goal_sha256": self.before_goal_sha256,
            "after_goal_sha256": self.after_goal_sha256,
            "before_goal_blob_oid": self.before_goal_blob_oid,
            "after_goal_blob_oid": self.after_goal_blob_oid,
            "repository_parent_ref": self.repository_parent_ref,
            "repository_commit_ref": self.repository_commit_ref,
            "repository_commit_receipt_ref": self.repository_commit_receipt_ref,
            "publication_issue_path": self.publication_issue_path,
            "publication_issue_blob_oid": self.publication_issue_blob_oid,
            "publication_issue_owner_execution_id": self.publication_issue_owner_execution_id,
            "publication_issue_status": self.publication_issue_status,
            "publication_issue_scope_digest": self.publication_issue_scope_digest,
        }
        if include_ref:
            body["receipt_ref"] = self.receipt_ref
        return body


def decode_goal_native_lane_introduction_receipt(
    payload: Mapping[str, object],
) -> GoalNativeLaneIntroductionPublicationReceiptV1:
    """Reject unknown fields, type substitution, and re-digested false shape."""

    if type(payload) is not dict:
        raise TypeError("receipt payload must be an exact object")
    wire = cast(dict[str, object], payload)
    required = {
        "schema_id", "goal_tag", "lane_key", "lane_authority_ref", "goal_path",
        "before_document_ref", "after_document_ref", "before_goal_sha256",
        "after_goal_sha256", "before_goal_blob_oid", "after_goal_blob_oid",
        "repository_parent_ref", "repository_commit_ref",
        "repository_commit_receipt_ref", "publication_issue_path",
        "publication_issue_blob_oid", "publication_issue_owner_execution_id",
        "publication_issue_status", "publication_issue_scope_digest",
    }
    if set(wire) != required | {"receipt_ref"}:
        raise GoalNativeLanePublicationError("receipt fields differ from canonical schema")
    values: dict[str, object] = {
        name: wire[name] for name in required if name != "schema_id"
    }
    if any(type(value) is not str for value in values.values()):
        raise GoalNativeLanePublicationError("receipt fields require exact JSON strings")
    receipt = GoalNativeLaneIntroductionPublicationReceiptV1(
        **cast(dict[str, str], values),
        schema_id=cast(str, wire["schema_id"]),
    )
    if wire != receipt.to_wire():
        raise GoalNativeLanePublicationError("receipt digest or body differs")
    return receipt


def require_exact_native_lane_introduction(
    *,
    before: GoalPhaseNativeDocumentV2 | GoalPhaseNativeDocumentV3 | GoalPhaseNativeDocumentV4,
    after: GoalPhaseNativeDocumentV4,
    receipt: GoalNativeLaneIntroductionPublicationReceiptV1,
) -> GoalNativeLaneAuthorityV1:
    """Check carrier semantics only; repository/Issue proof is provider-owned."""

    if type(before) not in {
        GoalPhaseNativeDocumentV2, GoalPhaseNativeDocumentV3,
        GoalPhaseNativeDocumentV4,
    } or type(after) is not GoalPhaseNativeDocumentV4:
        raise TypeError("introduction requires exact V2/V3/V4 to V4 documents")
    if type(receipt) is not GoalNativeLaneIntroductionPublicationReceiptV1:
        raise TypeError("receipt type must be exact")
    before.__post_init__()
    after.__post_init__()
    receipt.__post_init__()
    if (
        receipt.goal_tag != before.goal_tag
        or after.goal_tag != before.goal_tag
        or receipt.before_document_ref != before.document_ref
        or receipt.after_document_ref != after.document_ref
        or before.document_ref == after.document_ref
    ):
        raise GoalNativeLanePublicationError("document/receipt identity mismatch")
    for name in (
        "compatibility_projection_sha256", "compatibility_projection_byte_count",
        "definitions", "operational_bundle", "unresolved_dependencies",
        "source_refs", "execution_authority",
    ):
        if getattr(before, name) != getattr(after, name):
            raise GoalNativeLanePublicationError(f"introduction changed {name}")
    if isinstance(before, GoalPhaseNativeDocumentV2):
        expected_profile = "none"
        expected_journal = None
        prior_lanes: tuple[GoalNativeLaneAuthorityV1, ...] = ()
    elif isinstance(before, GoalPhaseNativeDocumentV3):
        expected_profile = "v1"
        expected_journal = before.phase_operation_journal
        prior_lanes = ()
    else:
        expected_profile = before.operation_journal_profile
        expected_journal = before.phase_operation_journal
        prior_lanes = before.native_lane_authorities
    if (
        after.operation_journal_profile != expected_profile
        or after.phase_operation_journal != expected_journal
    ):
        raise GoalNativeLanePublicationError("introduction changed journal authority")
    previous_keys = {item.lane_key for item in prior_lanes}
    additions = tuple(
        item for item in after.native_lane_authorities
        if item.lane_key not in previous_keys
    )
    retained = tuple(
        item for item in after.native_lane_authorities
        if item.lane_key in previous_keys
    )
    if retained != prior_lanes or len(additions) != 1:
        raise GoalNativeLanePublicationError("introduction changed other lane authority")
    lane = additions[0]
    if (
        lane.lane_key != receipt.lane_key
        or lane.lane_authority_ref != receipt.lane_authority_ref
    ):
        raise GoalNativeLanePublicationError("introduced lane differs from receipt")
    return lane
